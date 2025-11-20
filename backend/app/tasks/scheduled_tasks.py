"""
定时任务模块

本模块实现系统定时任务，包括：
- 每日计数重置
- 每日统计生成
- 数据清理
- 报表生成

任务特点：
    - 按固定时间调度（Celery Beat crontab）
    - 在系统负载低时执行（凌晨）
    - 幂等性（可重复执行不会产生副作用）
    - 错误容忍（失败不影响系统运行）

调度配置：
    - reset_daily_counts: 每天 00:00 执行
    - generate_daily_stats: 每天 01:00 执行

使用方式：
    这些任务由 Celery Beat 自动调度，无需手动调用
"""

import asyncio
import logging
from datetime import datetime, date, timedelta
from typing import Dict, Any, List

from celery import Task
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.celery_app import celery_app
from app.db.database import async_session_maker
from app.models.user import User
from app.models.permission import UserPermission
from app.models.apple_account import AppleAccount
from app.models.task import UnlockTask
from app.models.share_page import SharePage

logger = logging.getLogger(__name__)


# ========================================
# 任务基类
# ========================================

class ScheduledTask(Task):
    """
    定时任务基类

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
# 每日计数重置
# ========================================

@celery_app.task(
    bind=True,
    base=ScheduledTask,
    name="app.tasks.scheduled_tasks.reset_daily_counts"
)
def reset_daily_counts(self) -> Dict[str, Any]:
    """
    重置每日计数（每天 00:00 执行）

    业务流程：
        1. 查询所有用户权限
        2. 重置每日解锁次数计数器：
           - unlock_count_today = 0
           - last_reset_date = today
        3. 记录重置日志
        4. 返回统计结果

    重置项目：
        - unlock_count_today: 每日解锁次数
        - （可扩展）每日 API 调用次数
        - （可扩展）每日导入次数

    Returns:
        Dict[str, Any]: 重置结果
            {
                "total_users": 100,
                "reset_count": 95,
                "skipped": 5,
                "timestamp": "2025-11-20T00:00:00"
            }

    TODO (优先级 P2):
        - [ ] 添加每日 API 调用次数重置
        - [ ] 添加每日导入次数重置
        - [ ] 支持按时区重置（不同地区用户）
        - [ ] 添加重置日志记录表
        - [ ] 支持重置失败重试
    """
    return asyncio.run(_reset_daily_counts_async(self))


async def _reset_daily_counts_async(task: Task) -> Dict[str, Any]:
    """
    异步重置每日计数（内部实现）
    """
    db = async_session_maker()

    try:
        logger.info("开始每日计数重置")

        # 1. 查询所有用户权限
        query = select(UserPermission)
        result = await db.execute(query)
        permissions = result.scalars().all()

        total_users = len(permissions)
        reset_count = 0
        skipped = 0

        today = date.today()

        # 2. 重置每个用户的计数器
        for permission in permissions:
            try:
                # 检查是否已重置
                if permission.last_reset_date and permission.last_reset_date >= today:
                    skipped += 1
                    logger.debug(f"用户 {permission.user_id} 今日已重置，跳过")
                    continue

                # 重置计数器
                permission.unlock_count_today = 0
                permission.last_reset_date = today

                reset_count += 1
                logger.debug(f"用户 {permission.user_id} 每日计数已重置")

            except Exception as e:
                logger.error(f"重置用户 {permission.user_id} 计数失败: {str(e)}")
                skipped += 1

        # 3. 提交数据库更新
        await db.commit()

        result = {
            "total_users": total_users,
            "reset_count": reset_count,
            "skipped": skipped,
            "timestamp": datetime.utcnow().isoformat()
        }

        logger.info(f"每日计数重置完成: {result}")

        return result

    except Exception as e:
        logger.error(f"每日计数重置失败: {str(e)}", exc_info=True)
        raise
    finally:
        await db.close()


# ========================================
# 每日统计生成
# ========================================

@celery_app.task(
    bind=True,
    base=ScheduledTask,
    name="app.tasks.scheduled_tasks.generate_daily_stats"
)
def generate_daily_stats(self) -> Dict[str, Any]:
    """
    生成每日统计（每天 01:00 执行）

    业务流程：
        1. 统计前一天的数据：
           - 新增用户数
           - 新增账号数
           - 任务执行统计（总数、成功、失败）
           - 分享页访问统计（总访问、独立访客）
           - 系统健康度（代理成功率、节点在线率）
        2. 保存统计数据到数据库（TODO: 需要统计表）
        3. 生成日报（TODO: 邮件/站内信）
        4. 返回统计结果

    统计维度：
        - 用户维度：新增、活跃、权限过期
        - 账号维度：新增、检测、解锁、错误
        - 任务维度：创建、成功、失败、取消
        - 分享页维度：访问量、独立访客、热门页面
        - 系统维度：代理成功率、节点在线率、平均响应时间

    Returns:
        Dict[str, Any]: 统计结果
            {
                "date": "2025-11-19",
                "users": {
                    "total": 100,
                    "new": 5,
                    "active": 80,
                    "expired": 3
                },
                "accounts": {
                    "total": 500,
                    "new": 20,
                    "checked": 450,
                    "unlocked": 10
                },
                "tasks": {
                    "total": 1000,
                    "success": 950,
                    "failed": 50,
                    "success_rate": 95.0
                },
                "share_pages": {
                    "total_views": 5000,
                    "unique_visitors": 2000
                },
                "system": {
                    "proxy_success_rate": 92.5,
                    "node_online_rate": 100.0
                },
                "timestamp": "2025-11-20T01:00:00"
            }

    TODO (优先级 P1):
        - [ ] 创建统计数据表（daily_stats）
        - [ ] 实现统计数据持久化
        - [ ] 生成每日报表（PDF/HTML）
        - [ ] 发送每日报表（邮件/站内信）
        - [ ] 添加每周/每月统计报表
        - [ ] 支持自定义统计维度
        - [ ] 添加数据可视化（图表）
    """
    return asyncio.run(_generate_daily_stats_async(self))


async def _generate_daily_stats_async(task: Task) -> Dict[str, Any]:
    """
    异步生成每日统计（内部实现）
    """
    db = async_session_maker()

    try:
        logger.info("开始生成每日统计")

        # 统计日期：前一天
        yesterday = date.today() - timedelta(days=1)
        start_time = datetime.combine(yesterday, datetime.min.time())
        end_time = datetime.combine(yesterday, datetime.max.time())

        # ========== 用户统计 ==========
        # 总用户数
        total_users_query = select(func.count(User.id))
        total_users_result = await db.execute(total_users_query)
        total_users = total_users_result.scalar()

        # 新增用户数（前一天注册）
        new_users_query = select(func.count(User.id)).where(
            and_(
                User.created_at >= start_time,
                User.created_at <= end_time
            )
        )
        new_users_result = await db.execute(new_users_query)
        new_users = new_users_result.scalar()

        # 活跃用户数（前一天登录）
        active_users_query = select(func.count(User.id)).where(
            and_(
                User.last_login_at >= start_time,
                User.last_login_at <= end_time
            )
        )
        active_users_result = await db.execute(active_users_query)
        active_users = active_users_result.scalar()

        # ========== 账号统计 ==========
        # 总账号数
        total_accounts_query = select(func.count(AppleAccount.id))
        total_accounts_result = await db.execute(total_accounts_query)
        total_accounts = total_accounts_result.scalar()

        # 新增账号数
        new_accounts_query = select(func.count(AppleAccount.id)).where(
            and_(
                AppleAccount.created_at >= start_time,
                AppleAccount.created_at <= end_time
            )
        )
        new_accounts_result = await db.execute(new_accounts_query)
        new_accounts = new_accounts_result.scalar()

        # 检测账号数
        checked_accounts_query = select(func.count(AppleAccount.id)).where(
            and_(
                AppleAccount.last_checked_at >= start_time,
                AppleAccount.last_checked_at <= end_time
            )
        )
        checked_accounts_result = await db.execute(checked_accounts_query)
        checked_accounts = checked_accounts_result.scalar()

        # 解锁账号数
        unlocked_accounts_query = select(func.count(AppleAccount.id)).where(
            and_(
                AppleAccount.last_unlocked_at >= start_time,
                AppleAccount.last_unlocked_at <= end_time
            )
        )
        unlocked_accounts_result = await db.execute(unlocked_accounts_query)
        unlocked_accounts = unlocked_accounts_result.scalar()

        # ========== 任务统计 ==========
        # 总任务数
        total_tasks_query = select(func.count(UnlockTask.id)).where(
            and_(
                UnlockTask.created_at >= start_time,
                UnlockTask.created_at <= end_time
            )
        )
        total_tasks_result = await db.execute(total_tasks_query)
        total_tasks = total_tasks_result.scalar()

        # 成功任务数
        success_tasks_query = select(func.count(UnlockTask.id)).where(
            and_(
                UnlockTask.created_at >= start_time,
                UnlockTask.created_at <= end_time,
                UnlockTask.status == "success"
            )
        )
        success_tasks_result = await db.execute(success_tasks_query)
        success_tasks = success_tasks_result.scalar()

        # 失败任务数
        failed_tasks_query = select(func.count(UnlockTask.id)).where(
            and_(
                UnlockTask.created_at >= start_time,
                UnlockTask.created_at <= end_time,
                UnlockTask.status == "failed"
            )
        )
        failed_tasks_result = await db.execute(failed_tasks_query)
        failed_tasks = failed_tasks_result.scalar()

        # 计算成功率
        if total_tasks > 0:
            success_rate = (success_tasks / total_tasks) * 100
        else:
            success_rate = 0.0

        # ========== 分享页统计 ==========
        # TODO: 需要分享页访问日志表来统计

        # ========== 系统统计 ==========
        # TODO: 从代理和节点统计数据中计算

        # 构建统计结果
        stats = {
            "date": str(yesterday),
            "users": {
                "total": total_users or 0,
                "new": new_users or 0,
                "active": active_users or 0,
                "expired": 0  # TODO: 需要从权限表统计
            },
            "accounts": {
                "total": total_accounts or 0,
                "new": new_accounts or 0,
                "checked": checked_accounts or 0,
                "unlocked": unlocked_accounts or 0
            },
            "tasks": {
                "total": total_tasks or 0,
                "success": success_tasks or 0,
                "failed": failed_tasks or 0,
                "success_rate": round(success_rate, 2)
            },
            "share_pages": {
                "total_views": 0,  # TODO: 实现
                "unique_visitors": 0  # TODO: 实现
            },
            "system": {
                "proxy_success_rate": 0.0,  # TODO: 实现
                "node_online_rate": 0.0  # TODO: 实现
            },
            "timestamp": datetime.utcnow().isoformat()
        }

        logger.info(f"每日统计生成完成: {stats}")

        # TODO: 保存统计数据到数据库
        # TODO: 发送每日报表

        return stats

    except Exception as e:
        logger.error(f"每日统计生成失败: {str(e)}", exc_info=True)
        raise
    finally:
        await db.close()


# ========================================
# 导出任务
# ========================================

__all__ = [
    "reset_daily_counts",
    "generate_daily_stats",
]
