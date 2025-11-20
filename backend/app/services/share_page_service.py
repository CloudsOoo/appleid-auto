"""
分享页服务
"""
from datetime import datetime
from typing import Optional, List, Tuple, Dict
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_, and_, desc
import random

from app.models.share_page import SharePage, SharePageLog
from app.models.apple_account import AppleAccount
from app.models.permission import UserPermission
from app.core.security import get_password_hash, verify_password, decrypt_sensitive_data
from app.utils.html_filter import html_filter, validate_custom_html
from app.schemas.share_page import (
    SharePageCreate,
    SharePageUpdate,
    SharePageResponse,
    SharePagePublicResponse,
    SharePageLogResponse,
    SharePageStatsResponse,
)


class SharePageService:
    """分享页服务类"""

    @staticmethod
    async def check_share_page_quota(
        db: AsyncSession,
        user_id: int
    ) -> Tuple[bool, str]:
        """
        检查分享页配额

        Args:
            db: 数据库会话
            user_id: 用户ID

        Returns:
            Tuple[bool, str]: (是否有配额, 错误信息)
        """
        # 获取用户权限
        result = await db.execute(
            select(UserPermission).where(UserPermission.user_id == user_id)
        )
        permission = result.scalar_one_or_none()

        if not permission:
            return False, "用户权限不存在"

        # 检查是否过期
        if permission.is_expired():
            return False, "用户权限已过期"

        # 检查分享页数量配额
        result = await db.execute(
            select(func.count(SharePage.id)).where(SharePage.user_id == user_id)
        )
        current_count = result.scalar() or 0

        if current_count >= permission.max_share_pages:
            return False, f"分享页数量已达上限（{permission.max_share_pages}）"

        return True, ""

    @staticmethod
    async def check_custom_html_permission(
        db: AsyncSession,
        user_id: int
    ) -> bool:
        """
        检查自定义 HTML 权限

        Args:
            db: 数据库会话
            user_id: 用户ID

        Returns:
            bool: 是否有权限
        """
        result = await db.execute(
            select(UserPermission).where(UserPermission.user_id == user_id)
        )
        permission = result.scalar_one_or_none()

        if not permission:
            return False

        return permission.allow_custom_html

    @staticmethod
    async def create_share_page(
        db: AsyncSession,
        user_id: int,
        data: SharePageCreate,
        base_url: str = "https://example.com"
    ) -> SharePage:
        """
        创建分享页

        Args:
            db: 数据库会话
            user_id: 用户ID
            data: 创建数据
            base_url: 基础 URL

        Returns:
            SharePage: 创建的分享页对象
        """
        # 检查配额
        has_quota, error_msg = await SharePageService.check_share_page_quota(db, user_id)
        if not has_quota:
            raise ValueError(error_msg)

        # 检查 slug 是否已存在
        result = await db.execute(
            select(SharePage).where(SharePage.slug == data.slug)
        )
        if result.scalar_one_or_none():
            raise ValueError("该 URL 别名已存在")

        # 检查账号是否属于用户
        result = await db.execute(
            select(func.count(AppleAccount.id)).where(
                and_(
                    AppleAccount.id.in_(data.account_ids),
                    AppleAccount.user_id == user_id
                )
            )
        )
        valid_count = result.scalar() or 0

        if valid_count != len(data.account_ids):
            raise ValueError("部分账号不存在或不属于您")

        # 处理自定义 HTML
        cleaned_html_header = None
        cleaned_html_body = None
        cleaned_html_footer = None

        if data.custom_html_header or data.custom_html_body or data.custom_html_footer:
            # 检查自定义 HTML 权限
            has_permission = await SharePageService.check_custom_html_permission(db, user_id)
            if not has_permission:
                raise ValueError("您没有使用自定义 HTML 的权限")

            # 验证自定义 HTML
            is_valid, error_msg = validate_custom_html(
                data.custom_html_header,
                data.custom_html_body,
                data.custom_html_footer
            )
            if not is_valid:
                raise ValueError(error_msg)

            # 过滤自定义 HTML
            cleaned_html = html_filter.clean_custom_html(
                data.custom_html_header,
                data.custom_html_body,
                data.custom_html_footer
            )
            cleaned_html_header = cleaned_html.get("header")
            cleaned_html_body = cleaned_html.get("body")
            cleaned_html_footer = cleaned_html.get("footer")

        # 加密密码（如果有）
        password_hash = None
        if data.password:
            password_hash = get_password_hash(data.password)

        # 创建分享页
        share_page = SharePage(
            user_id=user_id,
            title=data.title,
            slug=data.slug,
            description=data.description,
            password_hash=password_hash,
            access_limit=data.access_limit,
            expires_at=data.expires_at,
            allowed_domains=data.allowed_domains,
            display_mode=data.display_mode,
            template=data.template,
            account_ids=data.account_ids,
            custom_html_header=cleaned_html_header,
            custom_html_body=cleaned_html_body,
            custom_html_footer=cleaned_html_footer,
            is_active=data.is_active,
        )

        db.add(share_page)
        await db.flush()

        # 更新用户权限计数
        result = await db.execute(
            select(UserPermission).where(UserPermission.user_id == user_id)
        )
        permission = result.scalar_one()
        permission.share_pages_count += 1

        await db.commit()
        await db.refresh(share_page)

        return share_page

    @staticmethod
    async def get_share_page(
        db: AsyncSession,
        page_id: int,
        user_id: int,
    ) -> Optional[SharePage]:
        """
        获取分享页详情

        Args:
            db: 数据库会话
            page_id: 分享页ID
            user_id: 用户ID

        Returns:
            SharePage: 分享页对象
        """
        result = await db.execute(
            select(SharePage).where(
                and_(
                    SharePage.id == page_id,
                    SharePage.user_id == user_id
                )
            )
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_share_page_by_slug(
        db: AsyncSession,
        slug: str,
    ) -> Optional[SharePage]:
        """
        通过 slug 获取分享页（公开访问）

        Args:
            db: 数据库会话
            slug: URL 别名

        Returns:
            SharePage: 分享页对象
        """
        result = await db.execute(
            select(SharePage).where(SharePage.slug == slug)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def update_share_page(
        db: AsyncSession,
        page_id: int,
        user_id: int,
        data: SharePageUpdate,
    ) -> Optional[SharePage]:
        """
        更新分享页

        Args:
            db: 数据库会话
            page_id: 分享页ID
            user_id: 用户ID
            data: 更新数据

        Returns:
            SharePage: 更新后的分享页对象
        """
        # 获取分享页
        result = await db.execute(
            select(SharePage).where(
                and_(
                    SharePage.id == page_id,
                    SharePage.user_id == user_id
                )
            )
        )
        share_page = result.scalar_one_or_none()

        if not share_page:
            return None

        # 更新字段
        update_data = data.model_dump(exclude_unset=True)

        # 如果更新密码，需要加密
        if "password" in update_data:
            password = update_data.pop("password")
            if password:
                share_page.password_hash = get_password_hash(password)
            else:
                share_page.password_hash = None

        # 如果更新账号列表，需要验证
        if "account_ids" in update_data:
            account_ids = update_data["account_ids"]
            result = await db.execute(
                select(func.count(AppleAccount.id)).where(
                    and_(
                        AppleAccount.id.in_(account_ids),
                        AppleAccount.user_id == user_id
                    )
                )
            )
            valid_count = result.scalar() or 0

            if valid_count != len(account_ids):
                raise ValueError("部分账号不存在或不属于您")

        # 如果更新自定义 HTML，需要过滤
        if any(key in update_data for key in ["custom_html_header", "custom_html_body", "custom_html_footer"]):
            # 检查权限
            has_permission = await SharePageService.check_custom_html_permission(db, user_id)
            if not has_permission:
                raise ValueError("您没有使用自定义 HTML 的权限")

            # 获取要清理的 HTML
            header = update_data.get("custom_html_header", share_page.custom_html_header)
            body = update_data.get("custom_html_body", share_page.custom_html_body)
            footer = update_data.get("custom_html_footer", share_page.custom_html_footer)

            # 验证
            is_valid, error_msg = validate_custom_html(header, body, footer)
            if not is_valid:
                raise ValueError(error_msg)

            # 过滤
            cleaned_html = html_filter.clean_custom_html(header, body, footer)

            if "custom_html_header" in update_data:
                update_data["custom_html_header"] = cleaned_html.get("header")
            if "custom_html_body" in update_data:
                update_data["custom_html_body"] = cleaned_html.get("body")
            if "custom_html_footer" in update_data:
                update_data["custom_html_footer"] = cleaned_html.get("footer")

        # 更新其他字段
        for field, value in update_data.items():
            setattr(share_page, field, value)

        share_page.updated_at = datetime.utcnow()
        await db.commit()
        await db.refresh(share_page)

        return share_page

    @staticmethod
    async def delete_share_page(
        db: AsyncSession,
        page_id: int,
        user_id: int,
    ) -> bool:
        """
        删除分享页

        Args:
            db: 数据库会话
            page_id: 分享页ID
            user_id: 用户ID

        Returns:
            bool: 是否成功
        """
        # 获取分享页
        result = await db.execute(
            select(SharePage).where(
                and_(
                    SharePage.id == page_id,
                    SharePage.user_id == user_id
                )
            )
        )
        share_page = result.scalar_one_or_none()

        if not share_page:
            return False

        # 删除分享页（级联删除日志）
        await db.delete(share_page)

        # 更新用户权限计数
        result = await db.execute(
            select(UserPermission).where(UserPermission.user_id == user_id)
        )
        permission = result.scalar_one_or_none()
        if permission and permission.share_pages_count > 0:
            permission.share_pages_count -= 1

        await db.commit()
        return True

    @staticmethod
    async def get_share_page_list(
        db: AsyncSession,
        user_id: int,
        page: int = 1,
        per_page: int = 20,
        is_active: Optional[bool] = None,
        search: Optional[str] = None,
    ) -> Tuple[List[SharePage], int]:
        """
        获取分享页列表

        Args:
            db: 数据库会话
            user_id: 用户ID
            page: 页码
            per_page: 每页数量
            is_active: 激活状态过滤
            search: 搜索关键词

        Returns:
            Tuple[List[SharePage], int]: (分享页列表, 总数)
        """
        # 构建基础查询
        query = select(SharePage).where(SharePage.user_id == user_id)

        # 应用过滤条件
        if is_active is not None:
            query = query.where(SharePage.is_active == is_active)

        if search:
            # 搜索标题、slug、描述
            search_pattern = f"%{search}%"
            query = query.where(
                or_(
                    SharePage.title.ilike(search_pattern),
                    SharePage.slug.ilike(search_pattern),
                    SharePage.description.ilike(search_pattern),
                )
            )

        # 获取总数
        count_query = select(func.count()).select_from(query.subquery())
        result = await db.execute(count_query)
        total = result.scalar()

        # 排序和分页
        query = query.order_by(desc(SharePage.created_at))
        query = query.offset((page - 1) * per_page).limit(per_page)

        # 执行查询
        result = await db.execute(query)
        share_pages = result.scalars().all()

        return list(share_pages), total

    @staticmethod
    async def verify_access(
        db: AsyncSession,
        slug: str,
        password: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        referer: Optional[str] = None,
    ) -> Tuple[bool, Optional[SharePage], str]:
        """
        验证分享页访问

        Args:
            db: 数据库会话
            slug: URL 别名
            password: 访问密码
            ip_address: IP 地址
            user_agent: User Agent
            referer: Referer

        Returns:
            Tuple[bool, Optional[SharePage], str]: (是否允许访问, 分享页对象, 错误信息)
        """
        # 获取分享页
        share_page = await SharePageService.get_share_page_by_slug(db, slug)

        if not share_page:
            return False, None, "分享页不存在"

        # 检查是否启用
        if not share_page.is_active:
            return False, share_page, "分享页已禁用"

        # 检查是否过期
        if share_page.is_expired():
            return False, share_page, "分享页已过期"

        # 检查访问次数限制
        if share_page.is_access_limit_reached():
            return False, share_page, "访问次数已达上限"

        # 检查密码
        password_correct = True
        if share_page.password_hash:
            if not password:
                # 记录密码尝试失败
                await SharePageService.log_access(
                    db, share_page.id, ip_address, user_agent,
                    referer, None, False, True
                )
                return False, share_page, "需要访问密码"

            if not verify_password(password, share_page.password_hash):
                # 记录密码错误
                await SharePageService.log_access(
                    db, share_page.id, ip_address, user_agent,
                    referer, None, False, True
                )
                return False, share_page, "访问密码错误"

        # 检查域名白名单（如果配置了）
        if share_page.allowed_domains and referer:
            from urllib.parse import urlparse
            referer_domain = urlparse(referer).netloc
            if referer_domain not in share_page.allowed_domains:
                return False, share_page, "域名不在白名单中"

        return True, share_page, ""

    @staticmethod
    async def get_display_accounts(
        db: AsyncSession,
        share_page: SharePage,
        include_password: bool = True,
    ) -> List[Dict]:
        """
        获取要显示的账号

        Args:
            db: 数据库会话
            share_page: 分享页对象
            include_password: 是否包含密码

        Returns:
            List[Dict]: 账号列表
        """
        # 获取所有账号
        result = await db.execute(
            select(AppleAccount).where(
                AppleAccount.id.in_(share_page.account_ids)
            )
        )
        accounts = result.scalars().all()

        # 根据显示模式选择账号
        if share_page.display_mode == "random":
            # 随机选择一个
            selected_accounts = [random.choice(accounts)] if accounts else []
        elif share_page.display_mode == "sequential":
            # 顺序选择（基于访问次数）
            index = share_page.access_count % len(accounts) if accounts else 0
            selected_accounts = [accounts[index]] if accounts else []
        else:  # all
            # 显示所有
            selected_accounts = accounts

        # 构建返回数据
        result_accounts = []
        for account in selected_accounts:
            account_data = {
                "id": account.id,
                "apple_id": account.apple_id,
            }

            # 解密密码（如果需要）
            if include_password and account.current_password:
                account_data["password"] = decrypt_sensitive_data(account.current_password)

            result_accounts.append(account_data)

        return result_accounts

    @staticmethod
    async def log_access(
        db: AsyncSession,
        share_page_id: int,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        referer: Optional[str] = None,
        shown_account_id: Optional[int] = None,
        access_granted: bool = True,
        password_attempt: bool = False,
    ) -> SharePageLog:
        """
        记录访问日志

        Args:
            db: 数据库会话
            share_page_id: 分享页ID
            ip_address: IP 地址
            user_agent: User Agent
            referer: Referer
            shown_account_id: 显示的账号ID
            access_granted: 是否允许访问
            password_attempt: 是否密码尝试

        Returns:
            SharePageLog: 访问日志对象
        """
        # 创建日志
        log = SharePageLog(
            share_page_id=share_page_id,
            ip_address=ip_address,
            user_agent=user_agent,
            referer=referer,
            shown_account_id=shown_account_id,
            access_granted=access_granted,
            password_attempt=password_attempt,
        )
        db.add(log)

        # 如果访问成功，更新分享页统计
        if access_granted:
            result = await db.execute(
                select(SharePage).where(SharePage.id == share_page_id)
            )
            share_page = result.scalar_one_or_none()

            if share_page:
                share_page.access_count += 1
                share_page.total_views += 1

                # 检查是否是新的 IP（unique view）
                result = await db.execute(
                    select(func.count(SharePageLog.id)).where(
                        and_(
                            SharePageLog.share_page_id == share_page_id,
                            SharePageLog.ip_address == ip_address,
                            SharePageLog.access_granted == True
                        )
                    )
                )
                ip_count = result.scalar() or 0

                if ip_count == 0:  # 第一次访问
                    share_page.unique_views += 1

        await db.commit()
        await db.refresh(log)

        return log

    @staticmethod
    async def get_access_logs(
        db: AsyncSession,
        page_id: int,
        user_id: int,
        page: int = 1,
        per_page: int = 50,
    ) -> Tuple[List[SharePageLog], int]:
        """
        获取访问日志

        Args:
            db: 数据库会话
            page_id: 分享页ID
            user_id: 用户ID
            page: 页码
            per_page: 每页数量

        Returns:
            Tuple[List[SharePageLog], int]: (日志列表, 总数)
        """
        # 检查分享页是否属于用户
        result = await db.execute(
            select(SharePage).where(
                and_(
                    SharePage.id == page_id,
                    SharePage.user_id == user_id
                )
            )
        )
        share_page = result.scalar_one_or_none()

        if not share_page:
            raise ValueError("分享页不存在")

        # 构建查询
        query = select(SharePageLog).where(SharePageLog.share_page_id == page_id)

        # 获取总数
        count_query = select(func.count()).select_from(query.subquery())
        result = await db.execute(count_query)
        total = result.scalar()

        # 排序和分页
        query = query.order_by(desc(SharePageLog.created_at))
        query = query.offset((page - 1) * per_page).limit(per_page)

        # 执行查询
        result = await db.execute(query)
        logs = result.scalars().all()

        return list(logs), total

    @staticmethod
    async def get_statistics(
        db: AsyncSession,
        page_id: int,
        user_id: int,
    ) -> SharePageStatsResponse:
        """
        获取分享页统计信息

        Args:
            db: 数据库会话
            page_id: 分享页ID
            user_id: 用户ID

        Returns:
            SharePageStatsResponse: 统计信息
        """
        # 检查分享页是否属于用户
        result = await db.execute(
            select(SharePage).where(
                and_(
                    SharePage.id == page_id,
                    SharePage.user_id == user_id
                )
            )
        )
        share_page = result.scalar_one_or_none()

        if not share_page:
            raise ValueError("分享页不存在")

        # 计算剩余访问次数
        remaining_access = None
        if share_page.access_limit:
            remaining_access = max(0, share_page.access_limit - share_page.access_count)

        # 获取最近访问记录
        result = await db.execute(
            select(SharePageLog)
            .where(
                and_(
                    SharePageLog.share_page_id == page_id,
                    SharePageLog.access_granted == True
                )
            )
            .order_by(desc(SharePageLog.created_at))
            .limit(10)
        )
        recent_visits = result.scalars().all()

        # 统计 top 国家（这里简化，实际需要 IP 定位服务）
        top_countries = []

        # 统计 top referers
        top_referers = []

        return SharePageStatsResponse(
            total_views=share_page.total_views,
            unique_views=share_page.unique_views,
            access_count=share_page.access_count,
            access_limit=share_page.access_limit,
            remaining_access=remaining_access,
            top_countries=top_countries,
            top_referers=top_referers,
            recent_visits=[SharePageLogResponse.model_validate(log) for log in recent_visits],
        )
