"""
维护任务模块

本模块实现系统维护相关的 Celery 任务，包括：
- 代理池健康检查
- 节点健康检查
- 用户权限过期检查
- 分享页访问统计

任务特点：
    - 定时执行（Celery Beat 调度）
    - 低优先级（不影响核心业务）
    - 异步执行（不阻塞主流程）
    - 错误容忍（失败不影响系统运行）

调度配置：
    - check_proxy_health: 每5分钟执行一次
    - check_node_health: 每1分钟执行一次
    - check_permission_expiry: 每10分钟执行一次

使用方式：
    这些任务由 Celery Beat 自动调度，无需手动调用
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List

import httpx
from celery import Task
from sqlalchemy import select, and_, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.celery_app import celery_app
from app.db.database import async_session_maker
from app.models.proxy import Proxy
from app.models.node import Node
from app.models.user import User
from app.models.permission import UserPermission

logger = logging.getLogger(__name__)


# ========================================
# 任务基类
# ========================================

class MaintenanceTask(Task):
    """
    维护任务基类

    提供数据库会话管理和错误处理
    """
    _db_session = None

    @property
    def db_session(self) -> AsyncSession:
        """获取数据库会话（懒加载）"""
        if self._db_session is None:
            self._db_session = async_session_maker()
        return self._db_session

    def after_return(self, *args, **kwargs):
        """任务返回后清理资源"""
        if self._db_session is not None:
            asyncio.create_task(self._db_session.close())
            self._db_session = None


# ========================================
# 代理池健康检查
# ========================================

@celery_app.task(
    bind=True,
    base=MaintenanceTask,
    name="app.tasks.maintenance_tasks.check_proxy_health"
)
def check_proxy_health(self) -> Dict[str, Any]:
    """
    检查代理池健康状态（每5分钟执行）

    业务流程：
        1. 查询所有 is_active=True 的代理
        2. 为每个代理发送测试请求
        3. 更新代理状态和统计信息：
           - 成功：更新 last_success_at, success_count, avg_response_time
           - 失败：更新 failure_count, last_error
           - 连续失败3次：设置 status='failed'
           - 连续失败5次：设置 is_active=False
        4. 返回统计结果

    测试方法：
        - 目标 URL: https://httpbin.org/ip
        - 超时时间: 10秒
        - 验证内容: 响应包含 "origin" 字段

    Returns:
        Dict[str, Any]: 检查结果
            {
                "total": 50,
                "success": 45,
                "failed": 5,
                "deactivated": 2,
                "duration": 12.5,
                "timestamp": "2025-11-20T12:00:00"
            }

    TODO (优先级 P1):
        - [ ] 支持多个测试 URL（避免单点失败）
        - [ ] 添加 IP 地理位置检测
        - [ ] 支持代理匿名度检测
        - [ ] 添加代理速度排名
        - [ ] 支持自定义测试间隔
    """
    return asyncio.run(_check_proxy_health_async(self))


async def _check_proxy_health_async(task: Task) -> Dict[str, Any]:
    """
    异步检查代理池健康（内部实现）
    """
    db = async_session_maker()
    start_time = datetime.utcnow()

    try:
        # 1. 查询所有启用的代理
        query = select(Proxy).where(Proxy.is_active == True)
        result = await db.execute(query)
        proxies = result.scalars().all()

        total = len(proxies)
        success = 0
        failed = 0
        deactivated = 0

        logger.info(f"开始代理池健康检查: 共 {total} 个代理")

        # 2. 测试每个代理
        for proxy in proxies:
            try:
                # 构建代理 URL
                if proxy.username and proxy.password:
                    proxy_url = f"{proxy.proxy_type}://{proxy.username}:{proxy.password}@{proxy.host}:{proxy.port}"
                else:
                    proxy_url = f"{proxy.proxy_type}://{proxy.host}:{proxy.port}"

                # 发送测试请求
                test_result = await _test_proxy(proxy_url)

                if test_result["success"]:
                    # 测试成功
                    proxy.status = "active"
                    proxy.last_success_at = datetime.utcnow()
                    proxy.last_checked_at = datetime.utcnow()
                    proxy.success_count += 1
                    proxy.avg_response_time = test_result["response_time"]
                    proxy.last_error = None

                    success += 1
                    logger.debug(f"代理 {proxy.host}:{proxy.port} 测试成功 ({test_result['response_time']}ms)")

                else:
                    # 测试失败
                    proxy.status = "failed"
                    proxy.last_checked_at = datetime.utcnow()
                    proxy.failure_count += 1
                    proxy.last_error = test_result["error"]

                    failed += 1
                    logger.warning(f"代理 {proxy.host}:{proxy.port} 测试失败: {test_result['error']}")

                    # 连续失败5次，禁用代理
                    consecutive_failures = proxy.failure_count - proxy.success_count
                    if consecutive_failures >= 5:
                        proxy.is_active = False
                        deactivated += 1
                        logger.error(f"代理 {proxy.host}:{proxy.port} 连续失败{consecutive_failures}次，已禁用")

            except Exception as e:
                logger.error(f"检查代理 {proxy.host}:{proxy.port} 时出错: {str(e)}")
                failed += 1

        # 3. 提交数据库更新
        await db.commit()

        duration = (datetime.utcnow() - start_time).total_seconds()

        result = {
            "total": total,
            "success": success,
            "failed": failed,
            "deactivated": deactivated,
            "duration": round(duration, 2),
            "timestamp": datetime.utcnow().isoformat()
        }

        logger.info(f"代理池健康检查完成: {result}")

        return result

    except Exception as e:
        logger.error(f"代理池健康检查失败: {str(e)}", exc_info=True)
        raise
    finally:
        await db.close()


async def _test_proxy(proxy_url: str, timeout: int = 10) -> Dict[str, Any]:
    """
    测试单个代理

    Args:
        proxy_url: 代理 URL
        timeout: 超时时间（秒）

    Returns:
        Dict[str, Any]: 测试结果
            {
                "success": True,
                "response_time": 234,  # 毫秒
                "ip": "1.2.3.4",
                "error": None
            }
    """
    test_url = "https://httpbin.org/ip"
    start_time = datetime.utcnow()

    try:
        # 配置代理
        proxies = {
            "http://": proxy_url,
            "https://": proxy_url,
        }

        # 发送请求
        async with httpx.AsyncClient(proxies=proxies, timeout=timeout, verify=False) as client:
            response = await client.get(test_url)

        # 计算响应时间
        response_time = int((datetime.utcnow() - start_time).total_seconds() * 1000)

        # 检查响应
        if response.status_code == 200:
            data = response.json()
            return {
                "success": True,
                "response_time": response_time,
                "ip": data.get("origin", "unknown"),
                "error": None
            }
        else:
            return {
                "success": False,
                "response_time": response_time,
                "ip": None,
                "error": f"HTTP {response.status_code}"
            }

    except httpx.TimeoutException:
        return {
            "success": False,
            "response_time": timeout * 1000,
            "ip": None,
            "error": "连接超时"
        }
    except Exception as e:
        return {
            "success": False,
            "response_time": 0,
            "ip": None,
            "error": str(e)
        }


# ========================================
# 节点健康检查
# ========================================

@celery_app.task(
    bind=True,
    base=MaintenanceTask,
    name="app.tasks.maintenance_tasks.check_node_health"
)
def check_node_health(self) -> Dict[str, Any]:
    """
    检查节点健康状态（每1分钟执行）

    业务流程：
        1. 查询所有节点
        2. 检查每个节点的心跳时间：
           - 心跳时间在3分钟内：online
           - 心跳时间超过3分钟：offline
           - 从未有心跳：offline
        3. 更新节点状态
        4. 返回统计结果

    节点健康标准：
        - online: 最后心跳时间 <= 3分钟
        - offline: 最后心跳时间 > 3分钟
        - error: 节点报告错误状态

    Returns:
        Dict[str, Any]: 检查结果
            {
                "total": 10,
                "online": 8,
                "offline": 2,
                "error": 0,
                "timestamp": "2025-11-20T12:00:00"
            }

    TODO (优先级 P1):
        - [ ] 添加节点性能监控（CPU、内存、磁盘）
        - [ ] 支持节点主动健康检查（ping/http）
        - [ ] 添加节点告警（离线时发送通知）
        - [ ] 支持节点自动重启
        - [ ] 添加节点负载均衡策略
    """
    return asyncio.run(_check_node_health_async(self))


async def _check_node_health_async(task: Task) -> Dict[str, Any]:
    """
    异步检查节点健康（内部实现）
    """
    db = async_session_maker()

    try:
        # 1. 查询所有节点
        query = select(Node)
        result = await db.execute(query)
        nodes = result.scalars().all()

        total = len(nodes)
        online = 0
        offline = 0
        error = 0

        logger.info(f"开始节点健康检查: 共 {total} 个节点")

        # 2. 检查每个节点的心跳时间
        threshold = datetime.utcnow() - timedelta(seconds=180)  # 3分钟阈值

        for node in nodes:
            try:
                # 检查心跳时间
                if node.last_heartbeat_at and node.last_heartbeat_at > threshold:
                    # 在线
                    if node.status != "online":
                        node.status = "online"
                        logger.info(f"节点 {node.node_name} 状态更新: offline → online")
                    online += 1

                else:
                    # 离线
                    if node.status != "offline":
                        node.status = "offline"
                        logger.warning(f"节点 {node.node_name} 状态更新: online → offline")
                    offline += 1

            except Exception as e:
                logger.error(f"检查节点 {node.node_name} 时出错: {str(e)}")
                node.status = "error"
                node.last_error = str(e)
                error += 1

        # 3. 提交数据库更新
        await db.commit()

        result = {
            "total": total,
            "online": online,
            "offline": offline,
            "error": error,
            "timestamp": datetime.utcnow().isoformat()
        }

        logger.info(f"节点健康检查完成: {result}")

        return result

    except Exception as e:
        logger.error(f"节点健康检查失败: {str(e)}", exc_info=True)
        raise
    finally:
        await db.close()


# ========================================
# 权限过期检查
# ========================================

@celery_app.task(
    bind=True,
    base=MaintenanceTask,
    name="app.tasks.maintenance_tasks.check_permission_expiry"
)
def check_permission_expiry(self) -> Dict[str, Any]:
    """
    检查用户权限过期（每10分钟执行）

    业务流程：
        1. 查询所有有 expires_at 的权限
        2. 检查是否已过期（expires_at < 当前时间）
        3. 对于过期的权限：
           - 禁用用户账户（is_active = False）
           - 记录过期时间
           - 发送过期通知（TODO）
        4. 返回统计结果

    处理策略：
        - 过期前3天：发送提醒通知（TODO）
        - 过期后：禁用账户，停止所有自动化任务
        - 过期30天后：清理数据（TODO）

    Returns:
        Dict[str, Any]: 检查结果
            {
                "total_checked": 100,
                "expired": 5,
                "expiring_soon": 8,
                "deactivated_users": 5,
                "timestamp": "2025-11-20T12:00:00"
            }

    TODO (优先级 P1):
        - [ ] 添加过期前提醒通知（邮件/站内信）
        - [ ] 添加宽限期（过期后3天再禁用）
        - [ ] 支持自动续费（对接支付系统）
        - [ ] 添加过期数据清理策略
        - [ ] 支持权限降级（过期后降级到免费套餐）
    """
    return asyncio.run(_check_permission_expiry_async(self))


async def _check_permission_expiry_async(task: Task) -> Dict[str, Any]:
    """
    异步检查权限过期（内部实现）
    """
    db = async_session_maker()

    try:
        # 1. 查询所有有过期时间的权限
        query = select(UserPermission).where(
            UserPermission.expires_at.isnot(None)
        )
        result = await db.execute(query)
        permissions = result.scalars().all()

        total_checked = len(permissions)
        expired = 0
        expiring_soon = 0
        deactivated_users = 0

        now = datetime.utcnow()
        three_days_later = now + timedelta(days=3)

        logger.info(f"开始权限过期检查: 共 {total_checked} 个权限")

        # 2. 检查每个权限
        for permission in permissions:
            try:
                # 检查是否已过期
                if permission.expires_at < now:
                    # 已过期
                    expired += 1

                    # 获取关联用户
                    user_query = select(User).where(User.id == permission.user_id)
                    user_result = await db.execute(user_query)
                    user = user_result.scalars().first()

                    if user and user.is_active:
                        # 禁用用户
                        user.is_active = False
                        deactivated_users += 1

                        logger.warning(
                            f"用户 {user.username} 权限已过期 (过期时间: {permission.expires_at})，账户已禁用"
                        )

                        # TODO: 发送过期通知
                        # await send_expiry_notification(user, permission)

                # 检查是否即将过期（3天内）
                elif permission.expires_at < three_days_later:
                    expiring_soon += 1
                    logger.info(
                        f"用户 ID {permission.user_id} 的权限即将过期 (过期时间: {permission.expires_at})"
                    )

                    # TODO: 发送即将过期提醒
                    # await send_expiry_reminder(user, permission)

            except Exception as e:
                logger.error(f"检查权限 {permission.id} 时出错: {str(e)}")

        # 3. 提交数据库更新
        await db.commit()

        result = {
            "total_checked": total_checked,
            "expired": expired,
            "expiring_soon": expiring_soon,
            "deactivated_users": deactivated_users,
            "timestamp": datetime.utcnow().isoformat()
        }

        logger.info(f"权限过期检查完成: {result}")

        return result

    except Exception as e:
        logger.error(f"权限过期检查失败: {str(e)}", exc_info=True)
        raise
    finally:
        await db.close()


# ========================================
# 导出任务
# ========================================

__all__ = [
    "check_proxy_health",
    "check_node_health",
    "check_permission_expiry",
]
