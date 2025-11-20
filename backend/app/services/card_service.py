"""
卡密服务
"""
from datetime import datetime, timedelta
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func
import secrets

from app.models.card import Card, CardLog
from app.models.package import Package
from app.models.permission import UserPermission
from app.models.user import User
from app.core.security import generate_card_code


class CardService:
    """卡密服务类"""

    @staticmethod
    async def generate_cards(
        db: AsyncSession,
        admin_id: int,
        card_type: str,
        package_id: int,
        quantity: int,
        duration_days: Optional[int] = None,
        usage_count: Optional[int] = None,
        batch_id: Optional[str] = None,
        note: Optional[str] = None
    ) -> List[str]:
        """
        批量生成卡密

        Args:
            db: 数据库会话
            admin_id: 管理员 ID
            card_type: 卡密类型（time/usage/permanent）
            package_id: 套餐 ID
            quantity: 生成数量
            duration_days: 有效天数（time 类型）
            usage_count: 使用次数（usage 类型）
            batch_id: 批次 ID
            note: 备注

        Returns:
            List[str]: 生成的卡密代码列表
        """
        # 验证套餐是否存在
        result = await db.execute(select(Package).where(Package.id == package_id))
        package = result.scalar_one_or_none()
        if not package:
            raise ValueError("套餐不存在")

        # 验证参数
        if card_type == "time" and not duration_days:
            raise ValueError("time 类型卡密必须指定有效天数")
        if card_type == "usage" and not usage_count:
            raise ValueError("usage 类型卡密必须指定使用次数")

        # 生成批次 ID
        if not batch_id:
            batch_id = f"BATCH_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"

        # 批量生成卡密
        card_codes = []
        cards = []

        for _ in range(quantity):
            # 生成唯一卡密代码
            while True:
                card_code = generate_card_code()
                # 检查是否已存在
                result = await db.execute(select(Card).where(Card.card_code == card_code))
                if not result.scalar_one_or_none():
                    break

            card = Card(
                card_code=card_code,
                card_type=card_type,
                package_id=package_id,
                duration_days=duration_days if card_type == "time" else None,
                usage_count=usage_count if card_type == "usage" else None,
                status="unused",
                batch_id=batch_id,
                note=note,
                created_by=admin_id,
            )
            cards.append(card)
            card_codes.append(card_code)

        # 批量插入
        db.add_all(cards)
        await db.commit()

        return card_codes

    @staticmethod
    async def activate_card(
        db: AsyncSession,
        user_id: int,
        card_code: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> dict:
        """
        激活卡密

        Args:
            db: 数据库会话
            user_id: 用户 ID
            card_code: 卡密代码
            ip_address: IP 地址
            user_agent: User Agent

        Returns:
            dict: 激活结果信息
        """
        # 查询卡密
        result = await db.execute(
            select(Card).where(Card.card_code == card_code)
        )
        card = result.scalar_one_or_none()

        if not card:
            raise ValueError("卡密不存在")

        if card.status != "unused":
            if card.status == "used":
                raise ValueError("卡密已被使用")
            elif card.status == "expired":
                raise ValueError("卡密已过期")
            elif card.status == "revoked":
                raise ValueError("卡密已被作废")

        # 获取套餐信息
        result = await db.execute(select(Package).where(Package.id == card.package_id))
        package = result.scalar_one_or_none()

        if not package:
            raise ValueError("套餐不存在")

        # 计算到期时间
        expires_at = None
        if card.card_type == "time":
            expires_at = datetime.utcnow() + timedelta(days=card.duration_days)
        elif card.card_type == "permanent":
            expires_at = None  # 永久有效

        # 更新卡密状态
        card.status = "used"
        card.activated_by = user_id
        card.activated_at = datetime.utcnow()
        card.activated_ip = ip_address
        card.expires_at = expires_at

        # 查询或创建用户权限
        result = await db.execute(
            select(UserPermission).where(UserPermission.user_id == user_id)
        )
        permission = result.scalar_one_or_none()

        if not permission:
            # 创建新权限
            permission = UserPermission(
                user_id=user_id,
                package_id=package.id,
            )
            db.add(permission)
        else:
            # 更新现有权限
            permission.package_id = package.id

        # 应用套餐权限
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
        permission.authorized_at = datetime.utcnow()
        permission.expires_at = expires_at

        # 记录激活日志
        log = CardLog(
            card_id=card.id,
            user_id=user_id,
            action="activate",
            details={
                "package_name": package.name,
                "card_type": card.card_type,
                "duration_days": card.duration_days,
                "expires_at": expires_at.isoformat() if expires_at else None,
            },
            ip_address=ip_address,
            user_agent=user_agent,
        )
        db.add(log)

        await db.commit()

        return {
            "card_type": card.card_type,
            "duration_days": card.duration_days,
            "usage_count": card.usage_count,
            "package": {
                "id": package.id,
                "name": package.name,
                "max_accounts": package.max_accounts,
                "max_share_pages": package.max_share_pages,
            },
            "expires_at": expires_at,
        }

    @staticmethod
    async def get_card_status(
        db: AsyncSession,
        user_id: int
    ) -> dict:
        """
        获取用户卡密状态

        Args:
            db: 数据库会话
            user_id: 用户 ID

        Returns:
            dict: 卡密状态信息
        """
        # 查询用户权限
        result = await db.execute(
            select(UserPermission).where(UserPermission.user_id == user_id)
        )
        permission = result.scalar_one_or_none()

        if not permission:
            return {
                "is_activated": False,
                "card_type": None,
                "package_name": None,
                "activated_at": None,
                "expires_at": None,
                "days_remaining": None,
            }

        # 查询套餐信息
        package = None
        if permission.package_id:
            result = await db.execute(
                select(Package).where(Package.id == permission.package_id)
            )
            package = result.scalar_one_or_none()

        # 查询用户激活的卡密
        result = await db.execute(
            select(Card).where(
                and_(
                    Card.activated_by == user_id,
                    Card.status == "used"
                )
            ).order_by(Card.activated_at.desc())
        )
        card = result.scalars().first()

        days_remaining = None
        if permission.expires_at:
            delta = permission.expires_at - datetime.utcnow()
            days_remaining = max(0, delta.days)

        return {
            "is_activated": True,
            "card_type": card.card_type if card else None,
            "package_name": package.name if package else None,
            "activated_at": permission.authorized_at,
            "expires_at": permission.expires_at,
            "days_remaining": days_remaining,
            "usage_count": card.usage_count if card and card.card_type == "usage" else None,
            "used_count": card.used_count if card and card.card_type == "usage" else None,
        }

    @staticmethod
    async def revoke_card(
        db: AsyncSession,
        card_id: int,
        admin_id: int,
        reason: str
    ) -> bool:
        """
        作废卡密

        Args:
            db: 数据库会话
            card_id: 卡密 ID
            admin_id: 管理员 ID
            reason: 作废原因

        Returns:
            bool: 是否成功
        """
        result = await db.execute(select(Card).where(Card.id == card_id))
        card = result.scalar_one_or_none()

        if not card:
            raise ValueError("卡密不存在")

        card.status = "revoked"

        # 记录日志
        log = CardLog(
            card_id=card.id,
            user_id=admin_id,
            action="revoke",
            details={"reason": reason},
        )
        db.add(log)

        await db.commit()
        return True

    @staticmethod
    async def extend_card(
        db: AsyncSession,
        card_id: int,
        admin_id: int,
        extend_days: int,
        reason: Optional[str] = None
    ) -> bool:
        """
        延期卡密

        Args:
            db: 数据库会话
            card_id: 卡密 ID
            admin_id: 管理员 ID
            extend_days: 延长天数
            reason: 延期原因

        Returns:
            bool: 是否成功
        """
        result = await db.execute(select(Card).where(Card.id == card_id))
        card = result.scalar_one_or_none()

        if not card:
            raise ValueError("卡密不存在")

        if card.card_type != "time":
            raise ValueError("只能延期 time 类型的卡密")

        if not card.expires_at:
            raise ValueError("卡密没有到期时间")

        # 延长到期时间
        old_expires_at = card.expires_at
        card.expires_at = card.expires_at + timedelta(days=extend_days)

        # 如果卡密已激活，同时更新用户权限
        if card.activated_by:
            result = await db.execute(
                select(UserPermission).where(UserPermission.user_id == card.activated_by)
            )
            permission = result.scalar_one_or_none()
            if permission and permission.expires_at:
                permission.expires_at = permission.expires_at + timedelta(days=extend_days)

        # 记录日志
        log = CardLog(
            card_id=card.id,
            user_id=admin_id,
            action="extend",
            details={
                "extend_days": extend_days,
                "old_expires_at": old_expires_at.isoformat(),
                "new_expires_at": card.expires_at.isoformat(),
                "reason": reason,
            },
        )
        db.add(log)

        await db.commit()
        return True

    @staticmethod
    async def get_card_list(
        db: AsyncSession,
        page: int = 1,
        per_page: int = 20,
        status: Optional[str] = None,
        card_type: Optional[str] = None,
        batch_id: Optional[str] = None,
        search: Optional[str] = None
    ) -> tuple[List[Card], int]:
        """
        获取卡密列表

        Args:
            db: 数据库会话
            page: 页码
            per_page: 每页数量
            status: 状态过滤
            card_type: 类型过滤
            batch_id: 批次过滤
            search: 搜索关键词

        Returns:
            tuple: (卡密列表, 总数)
        """
        query = select(Card)

        # 应用过滤
        filters = []
        if status:
            filters.append(Card.status == status)
        if card_type:
            filters.append(Card.card_type == card_type)
        if batch_id:
            filters.append(Card.batch_id == batch_id)
        if search:
            filters.append(Card.card_code.ilike(f"%{search}%"))

        if filters:
            query = query.where(and_(*filters))

        # 获取总数
        count_query = select(func.count()).select_from(Card)
        if filters:
            count_query = count_query.where(and_(*filters))
        result = await db.execute(count_query)
        total = result.scalar()

        # 分页
        query = query.order_by(Card.created_at.desc())
        query = query.offset((page - 1) * per_page).limit(per_page)

        result = await db.execute(query)
        cards = result.scalars().all()

        return list(cards), total

    @staticmethod
    async def export_cards(
        db: AsyncSession,
        batch_id: Optional[str] = None,
        status: str = "unused"
    ) -> List[str]:
        """
        导出卡密

        Args:
            db: 数据库会话
            batch_id: 批次 ID
            status: 状态过滤

        Returns:
            List[str]: 卡密代码列表
        """
        query = select(Card.card_code).where(Card.status == status)

        if batch_id:
            query = query.where(Card.batch_id == batch_id)

        result = await db.execute(query)
        cards = result.scalars().all()

        return list(cards)
