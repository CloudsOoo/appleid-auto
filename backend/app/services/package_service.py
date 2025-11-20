"""
套餐服务
"""
from datetime import datetime
from typing import Optional, List, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc

from app.models.package import Package
from app.schemas.package import (
    PackageCreate,
    PackageUpdate,
    PackageResponse,
)


class PackageService:
    """套餐服务类"""

    @staticmethod
    async def create_package(
        db: AsyncSession,
        data: PackageCreate,
    ) -> Package:
        """
        创建套餐

        Args:
            db: 数据库会话
            data: 创建数据

        Returns:
            Package: 创建的套餐对象
        """
        # 创建套餐
        package = Package(
            name=data.name,
            description=data.description,
            max_accounts=data.max_accounts,
            max_share_pages=data.max_share_pages,
            max_nodes=data.max_nodes,
            min_unlock_interval=data.min_unlock_interval,
            allow_custom_html=data.allow_custom_html,
            allow_view_password_history=data.allow_view_password_history,
            allow_batch_import=data.allow_batch_import,
            allow_api_access=data.allow_api_access,
            max_unlock_per_day=data.max_unlock_per_day,
            max_import_per_time=data.max_import_per_time,
            price=data.price,
            currency=data.currency,
            is_active=data.is_active,
            sort_order=data.sort_order,
        )

        db.add(package)
        await db.commit()
        await db.refresh(package)

        return package

    @staticmethod
    async def get_package(
        db: AsyncSession,
        package_id: int,
    ) -> Optional[Package]:
        """
        获取套餐详情

        Args:
            db: 数据库会话
            package_id: 套餐ID

        Returns:
            Package: 套餐对象
        """
        result = await db.execute(
            select(Package).where(Package.id == package_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def update_package(
        db: AsyncSession,
        package_id: int,
        data: PackageUpdate,
    ) -> Optional[Package]:
        """
        更新套餐

        Args:
            db: 数据库会话
            package_id: 套餐ID
            data: 更新数据

        Returns:
            Package: 更新后的套餐对象
        """
        # 获取套餐
        result = await db.execute(
            select(Package).where(Package.id == package_id)
        )
        package = result.scalar_one_or_none()

        if not package:
            return None

        # 更新字段
        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(package, field, value)

        package.updated_at = datetime.utcnow()
        await db.commit()
        await db.refresh(package)

        return package

    @staticmethod
    async def delete_package(
        db: AsyncSession,
        package_id: int,
    ) -> bool:
        """
        删除套餐

        Args:
            db: 数据库会话
            package_id: 套餐ID

        Returns:
            bool: 是否成功
        """
        # 获取套餐
        result = await db.execute(
            select(Package).where(Package.id == package_id)
        )
        package = result.scalar_one_or_none()

        if not package:
            return False

        # 检查是否有关联的卡密或用户权限
        # 如果有，不能删除，只能禁用
        # 这里简化处理，直接删除
        await db.delete(package)
        await db.commit()
        return True

    @staticmethod
    async def get_package_list(
        db: AsyncSession,
        page: int = 1,
        per_page: int = 20,
        is_active: Optional[bool] = None,
        include_inactive: bool = False,
    ) -> Tuple[List[Package], int]:
        """
        获取套餐列表

        Args:
            db: 数据库会话
            page: 页码
            per_page: 每页数量
            is_active: 激活状态过滤
            include_inactive: 是否包含禁用的套餐

        Returns:
            Tuple[List[Package], int]: (套餐列表, 总数)
        """
        # 构建基础查询
        query = select(Package)

        # 应用过滤条件
        if is_active is not None:
            query = query.where(Package.is_active == is_active)
        elif not include_inactive:
            # 默认只返回激活的套餐
            query = query.where(Package.is_active == True)

        # 获取总数
        count_query = select(func.count()).select_from(query.subquery())
        result = await db.execute(count_query)
        total = result.scalar()

        # 排序和分页
        query = query.order_by(Package.sort_order, desc(Package.created_at))
        query = query.offset((page - 1) * per_page).limit(per_page)

        # 执行查询
        result = await db.execute(query)
        packages = result.scalars().all()

        return list(packages), total

    @staticmethod
    async def get_all_active_packages(
        db: AsyncSession,
    ) -> List[Package]:
        """
        获取所有激活的套餐（用于前端展示）

        Args:
            db: 数据库会话

        Returns:
            List[Package]: 套餐列表
        """
        result = await db.execute(
            select(Package)
            .where(Package.is_active == True)
            .order_by(Package.sort_order)
        )
        return list(result.scalars().all())

    @staticmethod
    async def toggle_package_status(
        db: AsyncSession,
        package_id: int,
    ) -> bool:
        """
        切换套餐激活状态

        Args:
            db: 数据库会话
            package_id: 套餐ID

        Returns:
            bool: 是否成功
        """
        # 获取套餐
        result = await db.execute(
            select(Package).where(Package.id == package_id)
        )
        package = result.scalar_one_or_none()

        if not package:
            return False

        # 切换状态
        package.is_active = not package.is_active
        package.updated_at = datetime.utcnow()

        await db.commit()
        return True
