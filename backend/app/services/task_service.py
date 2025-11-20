"""
任务服务
"""
from datetime import datetime
from typing import Optional, List, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, desc
import uuid

from app.models.task import UnlockTask
from app.models.apple_account import AppleAccount
from app.models.permission import UserPermission
from app.schemas.task import (
    UnlockTaskCreate,
    UnlockTaskResponse,
    TaskStatsResponse,
)


class TaskService:
    """任务服务类"""

    @staticmethod
    async def create_tasks(
        db: AsyncSession,
        user_id: int,
        data: UnlockTaskCreate,
    ) -> List[UnlockTask]:
        """
        创建任务

        Args:
            db: 数据库会话
            user_id: 用户ID
            data: 创建数据

        Returns:
            List[UnlockTask]: 创建的任务列表
        """
        # 验证账号是否属于用户
        result = await db.execute(
            select(AppleAccount).where(
                and_(
                    AppleAccount.id.in_(data.account_ids),
                    AppleAccount.user_id == user_id
                )
            )
        )
        accounts = result.scalars().all()

        if len(accounts) != len(data.account_ids):
            raise ValueError("部分账号不存在或不属于您")

        # 检查权限（每日解锁次数）
        if data.task_type == "unlock":
            result = await db.execute(
                select(UserPermission).where(UserPermission.user_id == user_id)
            )
            permission = result.scalar_one_or_none()

            if not permission:
                raise ValueError("用户权限不存在")

            if permission.is_expired():
                raise ValueError("用户权限已过期")

            # 重置每日计数（如果需要）
            permission.reset_daily_counters()

            # 检查每日配额
            needed_count = len(data.account_ids)
            if permission.unlock_count_today + needed_count > permission.max_unlock_per_day:
                remaining = permission.max_unlock_per_day - permission.unlock_count_today
                raise ValueError(f"每日解锁次数不足，剩余：{remaining}")

            # 更新每日计数
            permission.unlock_count_today += needed_count

        # 创建任务
        tasks = []
        for account in accounts:
            # 生成唯一任务 ID
            task_id = f"{data.task_type}_{uuid.uuid4().hex[:16]}"

            task = UnlockTask(
                account_id=account.id,
                user_id=user_id,
                task_type=data.task_type,
                task_id=task_id,
                status="pending",
                priority=data.priority,
            )
            db.add(task)
            tasks.append(task)

        await db.commit()

        # 刷新任务
        for task in tasks:
            await db.refresh(task)

        # TODO: 发送任务到 Celery 队列
        # for task in tasks:
        #     send_task_to_celery(task)

        return tasks

    @staticmethod
    async def get_task(
        db: AsyncSession,
        task_id: int,
        user_id: int,
    ) -> Optional[UnlockTask]:
        """
        获取任务详情

        Args:
            db: 数据库会话
            task_id: 任务ID
            user_id: 用户ID

        Returns:
            UnlockTask: 任务对象
        """
        result = await db.execute(
            select(UnlockTask).where(
                and_(
                    UnlockTask.id == task_id,
                    UnlockTask.user_id == user_id
                )
            )
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_task_list(
        db: AsyncSession,
        user_id: int,
        page: int = 1,
        per_page: int = 20,
        status: Optional[str] = None,
        task_type: Optional[str] = None,
        account_id: Optional[int] = None,
    ) -> Tuple[List[UnlockTask], int]:
        """
        获取任务列表

        Args:
            db: 数据库会话
            user_id: 用户ID
            page: 页码
            per_page: 每页数量
            status: 状态过滤
            task_type: 类型过滤
            account_id: 账号ID过滤

        Returns:
            Tuple[List[UnlockTask], int]: (任务列表, 总数)
        """
        # 构建基础查询
        query = select(UnlockTask).where(UnlockTask.user_id == user_id)

        # 应用过滤条件
        if status:
            query = query.where(UnlockTask.status == status)

        if task_type:
            query = query.where(UnlockTask.task_type == task_type)

        if account_id:
            query = query.where(UnlockTask.account_id == account_id)

        # 获取总数
        count_query = select(func.count()).select_from(query.subquery())
        result = await db.execute(count_query)
        total = result.scalar()

        # 排序和分页
        query = query.order_by(desc(UnlockTask.created_at))
        query = query.offset((page - 1) * per_page).limit(per_page)

        # 执行查询
        result = await db.execute(query)
        tasks = result.scalars().all()

        return list(tasks), total

    @staticmethod
    async def cancel_task(
        db: AsyncSession,
        task_id: int,
        user_id: int,
    ) -> bool:
        """
        取消任务

        Args:
            db: 数据库会话
            task_id: 任务ID
            user_id: 用户ID

        Returns:
            bool: 是否成功
        """
        # 获取任务
        result = await db.execute(
            select(UnlockTask).where(
                and_(
                    UnlockTask.id == task_id,
                    UnlockTask.user_id == user_id
                )
            )
        )
        task = result.scalar_one_or_none()

        if not task:
            return False

        # 只能取消 pending 或 processing 状态的任务
        if task.status not in ["pending", "processing"]:
            raise ValueError(f"任务状态为 {task.status}，无法取消")

        # 更新状态
        task.status = "cancelled"
        task.completed_at = datetime.utcnow()

        # TODO: 如果任务正在执行，需要通知 Celery 取消
        # if task.task_id:
        #     revoke_celery_task(task.task_id)

        await db.commit()
        return True

    @staticmethod
    async def update_task_status(
        db: AsyncSession,
        task_id: int,
        status: str,
        result: Optional[dict] = None,
        error_message: Optional[str] = None,
        node_id: Optional[int] = None,
        proxy_id: Optional[int] = None,
    ) -> bool:
        """
        更新任务状态（内部使用，由 Celery 任务调用）

        Args:
            db: 数据库会话
            task_id: 任务ID（Celery task ID）
            status: 状态
            result: 结果
            error_message: 错误信息
            node_id: 节点ID
            proxy_id: 代理ID

        Returns:
            bool: 是否成功
        """
        result_obj = await db.execute(
            select(UnlockTask).where(UnlockTask.task_id == task_id)
        )
        task = result_obj.scalar_one_or_none()

        if not task:
            return False

        # 更新状态
        task.status = status

        if status == "processing":
            task.started_at = datetime.utcnow()

        if status in ["success", "failed", "cancelled"]:
            task.completed_at = datetime.utcnow()

        # 更新结果
        if result is not None:
            task.result = result

        # 更新错误信息
        if error_message:
            task.error_message = error_message

        # 更新执行信息
        if node_id is not None:
            task.node_id = node_id

        if proxy_id is not None:
            task.proxy_id = proxy_id

        await db.commit()
        return True

    @staticmethod
    async def retry_task(
        db: AsyncSession,
        task_id: int,
        user_id: int,
    ) -> bool:
        """
        重试任务

        Args:
            db: 数据库会话
            task_id: 任务ID
            user_id: 用户ID

        Returns:
            bool: 是否成功
        """
        # 获取任务
        result = await db.execute(
            select(UnlockTask).where(
                and_(
                    UnlockTask.id == task_id,
                    UnlockTask.user_id == user_id
                )
            )
        )
        task = result.scalar_one_or_none()

        if not task:
            return False

        # 只能重试 failed 状态的任务
        if task.status != "failed":
            raise ValueError("只能重试失败的任务")

        # 检查重试次数
        if task.retry_count >= task.max_retries:
            raise ValueError("已达最大重试次数")

        # 更新状态和重试次数
        task.status = "pending"
        task.retry_count += 1
        task.error_message = None
        task.started_at = None
        task.completed_at = None

        # TODO: 重新发送任务到 Celery
        # send_task_to_celery(task)

        await db.commit()
        return True

    @staticmethod
    async def get_task_stats(
        db: AsyncSession,
        user_id: int,
    ) -> TaskStatsResponse:
        """
        获取任务统计

        Args:
            db: 数据库会话
            user_id: 用户ID

        Returns:
            TaskStatsResponse: 统计信息
        """
        # 总数
        result = await db.execute(
            select(func.count(UnlockTask.id)).where(UnlockTask.user_id == user_id)
        )
        total = result.scalar() or 0

        # 各状态数量
        result = await db.execute(
            select(UnlockTask.status, func.count(UnlockTask.id))
            .where(UnlockTask.user_id == user_id)
            .group_by(UnlockTask.status)
        )
        status_counts = dict(result.all())

        pending = status_counts.get("pending", 0)
        processing = status_counts.get("processing", 0)
        success = status_counts.get("success", 0)
        failed = status_counts.get("failed", 0)
        cancelled = status_counts.get("cancelled", 0)

        # 成功率
        completed = success + failed
        success_rate = (success / completed * 100) if completed > 0 else 0.0

        return TaskStatsResponse(
            total=total,
            pending=pending,
            processing=processing,
            success=success,
            failed=failed,
            cancelled=cancelled,
            success_rate=round(success_rate, 2),
        )

    @staticmethod
    async def get_pending_tasks(
        db: AsyncSession,
        limit: int = 10,
    ) -> List[UnlockTask]:
        """
        获取待处理任务（内部使用，由 Celery 任务调度器调用）

        Args:
            db: 数据库会话
            limit: 返回数量

        Returns:
            List[UnlockTask]: 任务列表
        """
        # 按优先级和创建时间排序
        result = await db.execute(
            select(UnlockTask)
            .where(UnlockTask.status == "pending")
            .order_by(desc(UnlockTask.priority), UnlockTask.created_at)
            .limit(limit)
        )
        return list(result.scalars().all())
