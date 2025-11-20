"""
权限服务
"""
from datetime import datetime
from typing import Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.permission import UserPermission
from app.models.package import Package


class PermissionService:
    """权限服务类"""

    @staticmethod
    async def get_permission(
        db: AsyncSession,
        user_id: int,
    ) -> Optional[UserPermission]:
        """
        获取用户权限

        Args:
            db: 数据库会话
            user_id: 用户ID

        Returns:
            UserPermission: 用户权限对象
        """
        result = await db.execute(
            select(UserPermission).where(UserPermission.user_id == user_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def check_permission(
        db: AsyncSession,
        user_id: int,
        permission_name: str,
    ) -> bool:
        """
        检查用户是否有某项权限

        Args:
            db: 数据库会话
            user_id: 用户ID
            permission_name: 权限名称（如 allow_custom_html, allow_api_access）

        Returns:
            bool: 是否有权限
        """
        permission = await PermissionService.get_permission(db, user_id)

        if not permission:
            return False

        # 检查是否过期
        if permission.is_expired():
            return False

        # 检查具体权限
        return getattr(permission, permission_name, False)

    @staticmethod
    async def check_quota(
        db: AsyncSession,
        user_id: int,
        quota_name: str,
        required: int = 1,
    ) -> Tuple[bool, str]:
        """
        检查用户配额

        Args:
            db: 数据库会话
            user_id: 用户ID
            quota_name: 配额名称（如 max_accounts, max_unlock_per_day）
            required: 需要的配额数量

        Returns:
            Tuple[bool, str]: (是否有配额, 错误信息)
        """
        permission = await PermissionService.get_permission(db, user_id)

        if not permission:
            return False, "用户权限不存在"

        # 检查是否过期
        if permission.is_expired():
            return False, "用户权限已过期"

        # 重置每日计数（如果需要）
        if quota_name.endswith("_per_day"):
            permission.reset_daily_counters()

        # 检查具体配额
        max_value = getattr(permission, quota_name, 0)

        # 对于每日配额，需要检查当前使用量
        if quota_name == "max_unlock_per_day":
            current_value = permission.unlock_count_today
            remaining = max_value - current_value
            if required > remaining:
                return False, f"{quota_name} 配额不足，剩余：{remaining}"

        return True, ""

    @staticmethod
    async def apply_package(
        db: AsyncSession,
        user_id: int,
        package_id: int,
        duration_days: Optional[int] = None,
    ) -> bool:
        """
        应用套餐到用户权限

        Args:
            db: 数据库会话
            user_id: 用户ID
            package_id: 套餐ID
            duration_days: 有效期天数

        Returns:
            bool: 是否成功
        """
        # 获取套餐
        result = await db.execute(
            select(Package).where(Package.id == package_id)
        )
        package = result.scalar_one_or_none()

        if not package:
            raise ValueError("套餐不存在")

        if not package.is_active:
            raise ValueError("套餐已禁用")

        # 获取或创建用户权限
        permission = await PermissionService.get_permission(db, user_id)

        if not permission:
            permission = UserPermission(user_id=user_id)
            db.add(permission)

        # 应用套餐权限
        permission.package_id = package_id
        permission.max_accounts = package.max_accounts
        permission.max_share_pages = package.max_share_pages
        permission.max_nodes = package.max_nodes
        permission.min_unlock_interval = package.min_unlock_interval
        permission.allow_custom_html = package.allow_custom_html
        permission.allow_view_password_history = package.allow_view_password_history
        permission.allow_batch_import = package.allow_batch_import
        permission.allow_api_access = package.allow_api_access
        permission.max_unlock_per_day = package.max_unlock_per_day
        permission.max_import_per_time = package.max_import_per_time

        # 更新授权时间
        permission.authorized_at = datetime.utcnow()

        # 设置过期时间
        if duration_days:
            from datetime import timedelta
            permission.expires_at = datetime.utcnow() + timedelta(days=duration_days)

        await db.commit()
        return True

    @staticmethod
    async def update_permission(
        db: AsyncSession,
        user_id: int,
        **kwargs,
    ) -> bool:
        """
        更新用户权限（管理员使用）

        Args:
            db: 数据库会话
            user_id: 用户ID
            **kwargs: 要更新的字段

        Returns:
            bool: 是否成功
        """
        permission = await PermissionService.get_permission(db, user_id)

        if not permission:
            raise ValueError("用户权限不存在")

        # 更新字段
        for field, value in kwargs.items():
            if hasattr(permission, field):
                setattr(permission, field, value)

        permission.updated_at = datetime.utcnow()
        await db.commit()
        return True

    @staticmethod
    async def extend_expiration(
        db: AsyncSession,
        user_id: int,
        extend_days: int,
    ) -> bool:
        """
        延长权限有效期

        Args:
            db: 数据库会话
            user_id: 用户ID
            extend_days: 延长天数

        Returns:
            bool: 是否成功
        """
        from datetime import timedelta

        permission = await PermissionService.get_permission(db, user_id)

        if not permission:
            raise ValueError("用户权限不存在")

        # 如果已有过期时间，从过期时间延长；否则从当前时间延长
        if permission.expires_at:
            permission.expires_at += timedelta(days=extend_days)
        else:
            permission.expires_at = datetime.utcnow() + timedelta(days=extend_days)

        await db.commit()
        return True

    @staticmethod
    async def check_expired_permissions(
        db: AsyncSession,
    ) -> dict:
        """
        检查过期的权限（内部使用，由定时任务调用）

        Args:
            db: 数据库会话

        Returns:
            dict: 检查结果
        """
        # 获取所有有过期时间的权限
        result = await db.execute(
            select(UserPermission).where(UserPermission.expires_at.isnot(None))
        )
        permissions = result.scalars().all()

        total = len(permissions)
        expired = 0
        active = 0

        for permission in permissions:
            if permission.is_expired():
                expired += 1
                # 可以在这里添加过期处理逻辑，如发送通知
            else:
                active += 1

        return {
            "total": total,
            "expired": expired,
            "active": active,
            "message": f"权限检查完成，已过期：{expired}，有效：{active}"
        }
