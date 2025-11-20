"""
账号相关 Celery 任务模块

本模块实现账号的自动化操作任务，包括：
- 账号状态检测（单个/批量）
- 账号自动解锁
- 2FA 关闭
- 密码修改
- 设备删除

任务执行流程：
    1. 从数据库获取任务记录和账号信息
    2. 更新任务状态为 processing
    3. 选择代理和节点
    4. 调用自动化脚本（Playwright/Selenium/API）
    5. 更新任务结果和账号状态
    6. 记录日志和统计

错误处理：
    - 网络错误：自动重试（指数退避）
    - 账号错误：标记失败，不重试
    - 验证码：标记失败，等待人工处理
    - 其他错误：记录日志，重试

依赖关系：
    - Celery: 任务队列
    - PostgreSQL: 数据存储
    - Redis: 分布式锁
    - Playwright/Selenium: 浏览器自动化
    - 代理池: 网络请求
    - 节点池: 分布式执行
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List

from celery import Task
from celery.exceptions import SoftTimeLimitExceeded
from sqlalchemy import select, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.celery_app import celery_app
from app.db.database import async_session_maker
from app.models.apple_account import AppleAccount
from app.models.task import UnlockTask
from app.models.proxy import Proxy
from app.models.node import Node
from app.utils.encryption import decrypt_data

logger = logging.getLogger(__name__)


# ========================================
# 任务基类
# ========================================

class DatabaseTask(Task):
    """
    数据库任务基类

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
# 辅助函数
# ========================================

async def get_available_proxy(db: AsyncSession) -> Optional[Proxy]:
    """
    获取可用的代理

    选择策略：
        1. 状态为 active
        2. 成功率 > 80%
        3. 最后使用时间最早（轮询）

    Returns:
        Optional[Proxy]: 可用的代理，如果没有则返回 None
    """
    query = select(Proxy).where(
        and_(
            Proxy.is_active == True,
            Proxy.success_rate >= 80.0
        )
    ).order_by(Proxy.last_used_at.asc()).limit(1)

    result = await db.execute(query)
    proxy = result.scalars().first()

    if proxy:
        # 更新最后使用时间
        proxy.last_used_at = datetime.utcnow()
        await db.commit()

    return proxy


async def get_available_node(db: AsyncSession) -> Optional[Node]:
    """
    获取可用的执行节点

    选择策略：
        1. 状态为 online
        2. 负载最低（current_load / max_load）
        3. 最后心跳时间在3分钟内

    Returns:
        Optional[Node]: 可用的节点，如果没有则返回 None
    """
    three_minutes_ago = datetime.utcnow() - timedelta(minutes=3)

    query = select(Node).where(
        and_(
            Node.status == "online",
            Node.last_heartbeat >= three_minutes_ago
        )
    ).order_by((Node.current_load / Node.max_load).asc()).limit(1)

    result = await db.execute(query)
    node = result.scalars().first()

    return node


async def update_task_status(
    db: AsyncSession,
    task_id: int,
    status: str,
    result: Optional[Dict[str, Any]] = None,
    error_message: Optional[str] = None
) -> None:
    """
    更新任务状态

    Args:
        db: 数据库会话
        task_id: 任务 ID
        status: 新状态
        result: 任务结果
        error_message: 错误信息
    """
    query = select(UnlockTask).where(UnlockTask.id == task_id)
    result_db = await db.execute(query)
    task = result_db.scalars().first()

    if task:
        task.status = status
        if result:
            task.result = result
        if error_message:
            task.error_message = error_message

        if status == "processing":
            task.started_at = datetime.utcnow()
        elif status in ["success", "failed", "cancelled"]:
            task.completed_at = datetime.utcnow()

        await db.commit()


# ========================================
# 账号检测任务
# ========================================

@celery_app.task(
    bind=True,
    base=DatabaseTask,
    max_retries=3,
    default_retry_delay=60,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_backoff_max=600,
    retry_jitter=True,
    name="app.tasks.account_tasks.check_account"
)
def check_account(self, account_id: int) -> Dict[str, Any]:
    """
    检测单个账号状态

    业务流程：
        1. 从数据库获取账号信息
        2. 解密账号密码
        3. 选择代理和节点
        4. 调用 Apple 登录接口检测账号状态
        5. 更新账号状态（normal/locked）
        6. 如果账号被锁定且启用了 auto_unlock，创建解锁任务
        7. 更新 last_checked_at 和 next_check_at

    Args:
        account_id: 账号 ID

    Returns:
        Dict[str, Any]: 检测结果
            {
                "account_id": 1,
                "apple_id": "example@icloud.com",
                "status": "locked",
                "locked": True,
                "two_factor_enabled": True,
                "error": None
            }

    Raises:
        Exception: 数据库错误、网络错误等

    TODO (优先级 P0):
        - [ ] 集成 Apple 登录接口（appleid.apple.com）
        - [ ] 实现账号状态检测逻辑（正常/锁定/异常）
        - [ ] 实现 2FA 状态检测
        - [ ] 实现代理切换和重试机制
        - [ ] 添加验证码识别（OCR/打码平台）
    """
    return asyncio.run(_check_account_async(self, account_id))


async def _check_account_async(task: Task, account_id: int) -> Dict[str, Any]:
    """
    异步检测账号状态（内部实现）
    """
    db = async_session_maker()

    try:
        # 1. 获取账号信息
        query = select(AppleAccount).where(AppleAccount.id == account_id)
        result = await db.execute(query)
        account = result.scalars().first()

        if not account:
            raise ValueError(f"账号 {account_id} 不存在")

        logger.info(f"开始检测账号: {account.apple_id} (ID: {account_id})")

        # 2. 解密密码
        if account.current_password:
            password = decrypt_data(account.current_password)
        else:
            raise ValueError(f"账号 {account.apple_id} 没有密码")

        # 3. 选择代理
        proxy = await get_available_proxy(db)
        proxy_url = f"{proxy.protocol}://{proxy.host}:{proxy.port}" if proxy else None

        # 4. 选择节点
        node = await get_available_node(db)

        # ========== TODO: 调用 Apple 登录接口检测状态 ==========
        # 这里需要实现实际的账号检测逻辑
        # 可以使用 Playwright/Selenium 模拟登录，或调用 Apple API

        # 示例伪代码：
        # from app.automation.apple_checker import check_apple_account
        # check_result = await check_apple_account(
        #     apple_id=account.apple_id,
        #     password=password,
        #     proxy=proxy_url
        # )

        # 模拟检测结果（实际应该从真实检测中获取）
        check_result = {
            "success": True,
            "locked": False,  # TODO: 从实际检测中获取
            "two_factor_enabled": False,  # TODO: 从实际检测中获取
            "status": "normal",  # normal/locked/error
            "error": None,
            "duration": 5.2,  # 检测耗时（秒）
        }

        # 5. 更新账号状态
        account.status = check_result["status"]
        account.lock_status = check_result["locked"]
        account.two_factor_enabled = check_result.get("two_factor_enabled", False)
        account.last_checked_at = datetime.utcnow()
        account.next_check_at = datetime.utcnow() + timedelta(seconds=account.check_interval)

        if check_result["success"]:
            # 清除错误计数
            account.error_count = 0
            account.last_error = None
        else:
            # 增加错误计数
            account.error_count += 1
            account.last_error = check_result.get("error", "Unknown error")

        await db.commit()

        # 6. 如果账号被锁定且启用了自动解锁，创建解锁任务
        if check_result["locked"] and account.auto_unlock:
            logger.info(f"账号 {account.apple_id} 被锁定，创建自动解锁任务")

            unlock_task = UnlockTask(
                account_id=account_id,
                user_id=account.user_id,
                task_type="unlock",
                status="pending",
                priority=5,  # 自动解锁优先级为5
                max_retries=3
            )
            db.add(unlock_task)
            await db.commit()
            await db.refresh(unlock_task)

            # 调度解锁任务
            unlock_account.apply_async(
                args=[unlock_task.id],
                queue="high_priority",
                priority=5
            )

        logger.info(f"账号 {account.apple_id} 检测完成: {check_result}")

        return {
            "account_id": account_id,
            "apple_id": account.apple_id,
            "status": check_result["status"],
            "locked": check_result["locked"],
            "two_factor_enabled": check_result.get("two_factor_enabled", False),
            "error": check_result.get("error"),
            "duration": check_result.get("duration", 0),
            "proxy_used": proxy_url,
            "node_used": node.name if node else None,
        }

    except SoftTimeLimitExceeded:
        logger.error(f"账号 {account_id} 检测超时")
        raise
    except Exception as e:
        logger.error(f"账号 {account_id} 检测失败: {str(e)}", exc_info=True)
        raise
    finally:
        await db.close()


@celery_app.task(
    bind=True,
    name="app.tasks.account_tasks.batch_check_accounts"
)
def batch_check_accounts(self) -> Dict[str, Any]:
    """
    批量检测账号状态（定时任务）

    业务流程：
        1. 从数据库查询需要检测的账号：
           - next_check_at <= 当前时间
           - status != 'error'
           - user 权限未过期
        2. 为每个账号创建检测任务
        3. 调度到 Celery 队列

    Returns:
        Dict[str, Any]: 批量检测结果
            {
                "total": 50,
                "queued": 48,
                "skipped": 2,
                "timestamp": "2025-11-20T12:00:00"
            }

    TODO (优先级 P1):
        - [ ] 添加批量检测限流（避免同时检测过多账号）
        - [ ] 支持按标签/分类批量检测
        - [ ] 添加检测优先级（VIP 用户优先）
    """
    return asyncio.run(_batch_check_accounts_async(self))


async def _batch_check_accounts_async(task: Task) -> Dict[str, Any]:
    """
    异步批量检测账号（内部实现）
    """
    db = async_session_maker()

    try:
        # 1. 查询需要检测的账号
        now = datetime.utcnow()

        query = select(AppleAccount).where(
            and_(
                or_(
                    AppleAccount.next_check_at <= now,
                    AppleAccount.next_check_at.is_(None)
                ),
                AppleAccount.status != "error"
            )
        ).limit(100)  # 每次最多检测100个账号

        result = await db.execute(query)
        accounts = result.scalars().all()

        total = len(accounts)
        queued = 0
        skipped = 0

        logger.info(f"批量检测: 找到 {total} 个待检测账号")

        # 2. 为每个账号创建检测任务
        for account in accounts:
            try:
                # TODO: 检查用户权限是否过期
                # if user.permission_expired:
                #     skipped += 1
                #     continue

                # 调度检测任务
                check_account.apply_async(
                    args=[account.id],
                    queue="default",
                    priority=3
                )
                queued += 1

            except Exception as e:
                logger.error(f"调度账号 {account.id} 检测失败: {str(e)}")
                skipped += 1

        logger.info(f"批量检测调度完成: 总数={total}, 已调度={queued}, 跳过={skipped}")

        return {
            "total": total,
            "queued": queued,
            "skipped": skipped,
            "timestamp": datetime.utcnow().isoformat()
        }

    except Exception as e:
        logger.error(f"批量检测失败: {str(e)}", exc_info=True)
        raise
    finally:
        await db.close()


# ========================================
# 账号解锁任务
# ========================================

@celery_app.task(
    bind=True,
    base=DatabaseTask,
    max_retries=3,
    default_retry_delay=120,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_backoff_max=1200,
    retry_jitter=True,
    name="app.tasks.account_tasks.unlock_account"
)
def unlock_account(self, task_id: int) -> Dict[str, Any]:
    """
    解锁账号任务

    业务流程：
        1. 从数据库获取任务和账号信息
        2. 更新任务状态为 processing
        3. 解密账号密码和密保问题
        4. 选择代理和节点
        5. 调用解锁自动化脚本（iforgot 流程）
        6. 更新任务结果和账号状态
        7. 记录解锁日志

    解锁方法：
        - iforgot: 通过 iforgot.apple.com 密保问题解锁
        - account_recovery: 通过账号恢复流程
        - contact_support: 联系 Apple 客服（人工）

    Args:
        task_id: 任务 ID

    Returns:
        Dict[str, Any]: 解锁结果
            {
                "success": True,
                "method": "iforgot",
                "duration": 45.2,
                "error": None
            }

    TODO (优先级 P0):
        - [ ] 集成 iforgot.apple.com 解锁流程
        - [ ] 实现密保问题回答逻辑
        - [ ] 实现账号恢复流程
        - [ ] 添加短信/邮件验证码处理
        - [ ] 添加人工介入机制（验证码识别失败）
    """
    return asyncio.run(_unlock_account_async(self, task_id))


async def _unlock_account_async(task_obj: Task, task_id: int) -> Dict[str, Any]:
    """
    异步解锁账号（内部实现）
    """
    db = async_session_maker()

    try:
        # 1. 获取任务和账号信息
        query = select(UnlockTask).where(UnlockTask.id == task_id)
        result = await db.execute(query)
        task = result.scalars().first()

        if not task:
            raise ValueError(f"任务 {task_id} 不存在")

        # 获取关联的账号
        account_query = select(AppleAccount).where(AppleAccount.id == task.account_id)
        account_result = await db.execute(account_query)
        account = account_result.scalars().first()

        if not account:
            raise ValueError(f"账号 {task.account_id} 不存在")

        logger.info(f"开始解锁账号: {account.apple_id} (任务ID: {task_id})")

        # 2. 更新任务状态
        await update_task_status(db, task_id, "processing")

        # 3. 解密密码和密保问题
        password = decrypt_data(account.current_password) if account.current_password else None
        security_questions = account.security_questions or {}

        if not password:
            raise ValueError(f"账号 {account.apple_id} 没有密码")

        # 4. 选择代理和节点
        proxy = await get_available_proxy(db)
        proxy_url = f"{proxy.protocol}://{proxy.host}:{proxy.port}" if proxy else None

        node = await get_available_node(db)

        # 更新任务的代理和节点
        if proxy:
            task.proxy_id = proxy.id
        if node:
            task.node_id = node.id
        await db.commit()

        # ========== TODO: 调用解锁自动化脚本 ==========
        # 这里需要实现实际的解锁逻辑
        # 可以使用 Playwright/Selenium 模拟 iforgot 流程

        # 示例伪代码：
        # from app.automation.apple_unlocker import unlock_apple_account
        # unlock_result = await unlock_apple_account(
        #     apple_id=account.apple_id,
        #     password=password,
        #     security_questions=security_questions,
        #     proxy=proxy_url
        # )

        # 模拟解锁结果（实际应该从真实解锁中获取）
        unlock_result = {
            "success": True,  # TODO: 从实际解锁中获取
            "method": "iforgot",
            "duration": 45.2,
            "steps": [
                "访问 iforgot.apple.com",
                "输入 Apple ID",
                "回答密保问题 1",
                "回答密保问题 2",
                "解锁成功"
            ],
            "error": None
        }

        # 5. 更新账号状态
        if unlock_result["success"]:
            account.status = "normal"
            account.lock_status = False
            account.last_unlocked_at = datetime.utcnow()
            account.unlock_count += 1
            account.error_count = 0
            account.last_error = None

            # 更新任务状态为成功
            await update_task_status(
                db, task_id, "success",
                result=unlock_result
            )

            logger.info(f"账号 {account.apple_id} 解锁成功")

        else:
            # 解锁失败
            task.retry_count += 1

            if task.retry_count >= task.max_retries:
                # 达到最大重试次数，标记为失败
                account.status = "error"
                await update_task_status(
                    db, task_id, "failed",
                    error_message=unlock_result.get("error", "解锁失败")
                )
                logger.error(f"账号 {account.apple_id} 解锁失败（达到最大重试次数）")
            else:
                # 重试
                await update_task_status(
                    db, task_id, "pending",
                    error_message=f"解锁失败，将在60秒后重试（第{task.retry_count}次）"
                )
                logger.warning(f"账号 {account.apple_id} 解锁失败，将重试")

        await db.commit()

        return unlock_result

    except SoftTimeLimitExceeded:
        logger.error(f"任务 {task_id} 解锁超时")
        await update_task_status(db, task_id, "failed", error_message="解锁超时")
        await db.commit()
        raise
    except Exception as e:
        logger.error(f"任务 {task_id} 解锁失败: {str(e)}", exc_info=True)
        await update_task_status(db, task_id, "failed", error_message=str(e))
        await db.commit()
        raise
    finally:
        await db.close()


# ========================================
# 关闭 2FA 任务
# ========================================

@celery_app.task(
    bind=True,
    base=DatabaseTask,
    max_retries=3,
    name="app.tasks.account_tasks.disable_2fa"
)
def disable_2fa(self, task_id: int) -> Dict[str, Any]:
    """
    关闭账号 2FA 任务

    业务流程：
        1. 从数据库获取任务和账号信息
        2. 登录 Apple ID 账户
        3. 进入安全设置
        4. 关闭两步验证
        5. 更新账号状态

    Args:
        task_id: 任务 ID

    Returns:
        Dict[str, Any]: 关闭结果

    TODO (优先级 P1):
        - [ ] 实现 2FA 关闭流程（appleid.apple.com）
        - [ ] 处理 2FA 验证码（短信/设备推送）
        - [ ] 添加关闭失败处理
    """
    return asyncio.run(_disable_2fa_async(self, task_id))


async def _disable_2fa_async(task_obj: Task, task_id: int) -> Dict[str, Any]:
    """
    异步关闭 2FA（内部实现）
    """
    db = async_session_maker()

    try:
        # TODO: 实现 2FA 关闭逻辑
        logger.info(f"关闭 2FA 任务 {task_id}（功能待实现）")

        # 模拟结果
        return {
            "success": False,
            "error": "功能待实现",
            "message": "2FA 关闭功能正在开发中"
        }

    finally:
        await db.close()


# ========================================
# 修改密码任务
# ========================================

@celery_app.task(
    bind=True,
    base=DatabaseTask,
    max_retries=3,
    name="app.tasks.account_tasks.change_password"
)
def change_password(self, task_id: int, new_password: str) -> Dict[str, Any]:
    """
    修改账号密码任务

    业务流程：
        1. 登录账号
        2. 进入密码设置
        3. 修改密码
        4. 更新数据库中的密码
        5. 创建密码历史记录

    Args:
        task_id: 任务 ID
        new_password: 新密码

    Returns:
        Dict[str, Any]: 修改结果

    TODO (优先级 P1):
        - [ ] 实现密码修改流程
        - [ ] 添加密码强度检查
        - [ ] 处理密码修改验证（2FA/邮件/短信）
    """
    return asyncio.run(_change_password_async(self, task_id, new_password))


async def _change_password_async(task_obj: Task, task_id: int, new_password: str) -> Dict[str, Any]:
    """
    异步修改密码（内部实现）
    """
    db = async_session_maker()

    try:
        # TODO: 实现密码修改逻辑
        logger.info(f"修改密码任务 {task_id}（功能待实现）")

        # 模拟结果
        return {
            "success": False,
            "error": "功能待实现",
            "message": "密码修改功能正在开发中"
        }

    finally:
        await db.close()


# ========================================
# 导出任务
# ========================================

__all__ = [
    "check_account",
    "batch_check_accounts",
    "unlock_account",
    "disable_2fa",
    "change_password",
]
