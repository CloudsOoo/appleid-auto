"""
认证服务
"""
from datetime import datetime, timedelta
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import pyotp
import qrcode
import io
import base64

from app.models.user import User
from app.models.permission import UserPermission
from app.core.security import (
    verify_password,
    get_password_hash,
    create_access_token,
    create_refresh_token,
    decode_token,
)
from app.core.config import settings


class AuthService:
    """认证服务类"""

    @staticmethod
    async def register_user(
        db: AsyncSession,
        username: str,
        email: str,
        password: str,
        full_name: Optional[str] = None
    ) -> User:
        """
        注册新用户

        Args:
            db: 数据库会话
            username: 用户名
            email: 邮箱
            password: 密码
            full_name: 全名

        Returns:
            User: 新创建的用户对象
        """
        # 检查用户名是否已存在
        result = await db.execute(select(User).where(User.username == username))
        if result.scalar_one_or_none():
            raise ValueError("用户名已存在")

        # 检查邮箱是否已存在
        result = await db.execute(select(User).where(User.email == email))
        if result.scalar_one_or_none():
            raise ValueError("邮箱已存在")

        # 创建用户
        user = User(
            username=username,
            email=email,
            password_hash=get_password_hash(password),
            full_name=full_name,
            role="user",
            is_active=True,
        )
        db.add(user)
        await db.flush()

        # 创建默认权限（免费版）
        permission = UserPermission(
            user_id=user.id,
            max_accounts=5,
            max_share_pages=1,
            max_nodes=1,
            min_unlock_interval=3600,
            allow_custom_html=False,
            allow_view_password_history=False,
            allow_batch_import=True,
            allow_api_access=False,
            max_unlock_per_day=10,
            max_import_per_time=10,
        )
        db.add(permission)
        await db.commit()
        await db.refresh(user)

        return user

    @staticmethod
    async def authenticate_user(
        db: AsyncSession,
        username: str,
        password: str,
        otp_code: Optional[str] = None
    ) -> Optional[User]:
        """
        验证用户登录

        Args:
            db: 数据库会话
            username: 用户名或邮箱
            password: 密码
            otp_code: 2FA 验证码

        Returns:
            User: 用户对象，验证失败返回 None
        """
        # 查询用户（用户名或邮箱）
        result = await db.execute(
            select(User).where(
                (User.username == username) | (User.email == username)
            )
        )
        user = result.scalar_one_or_none()

        if not user:
            return None

        # 验证密码
        if not verify_password(password, user.password_hash):
            return None

        # 检查是否需要 2FA
        if user.two_factor_enabled:
            if not otp_code:
                raise ValueError("需要 2FA 验证码")

            totp = pyotp.TOTP(user.two_factor_secret)
            if not totp.verify(otp_code):
                raise ValueError("2FA 验证码错误")

        # 更新最后登录时间
        user.last_login_at = datetime.utcnow()
        await db.commit()

        return user

    @staticmethod
    def create_tokens(user_id: int) -> dict:
        """
        创建访问令牌和刷新令牌

        Args:
            user_id: 用户 ID

        Returns:
            dict: 包含 access_token 和 refresh_token 的字典
        """
        access_token = create_access_token({"sub": user_id})
        refresh_token = create_refresh_token({"sub": user_id})

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        }

    @staticmethod
    async def get_current_user(
        db: AsyncSession,
        token: str
    ) -> Optional[User]:
        """
        根据 Token 获取当前用户

        Args:
            db: 数据库会话
            token: JWT Token

        Returns:
            User: 用户对象
        """
        payload = decode_token(token)
        if not payload:
            return None

        user_id = payload.get("sub")
        if not user_id:
            return None

        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()

        if not user or not user.is_active:
            return None

        return user

    @staticmethod
    async def change_password(
        db: AsyncSession,
        user: User,
        old_password: str,
        new_password: str
    ) -> bool:
        """
        修改密码

        Args:
            db: 数据库会话
            user: 用户对象
            old_password: 旧密码
            new_password: 新密码

        Returns:
            bool: 是否成功
        """
        # 验证旧密码
        if not verify_password(old_password, user.password_hash):
            raise ValueError("旧密码错误")

        # 更新密码
        user.password_hash = get_password_hash(new_password)
        await db.commit()

        return True

    @staticmethod
    def enable_2fa(user: User) -> dict:
        """
        启用 2FA

        Args:
            user: 用户对象

        Returns:
            dict: 包含 secret 和 qr_code 的字典
        """
        # 生成密钥
        secret = pyotp.random_base32()

        # 生成二维码
        totp = pyotp.TOTP(secret)
        provisioning_uri = totp.provisioning_uri(
            user.email,
            issuer_name=settings.APP_NAME
        )

        # 生成二维码图片
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(provisioning_uri)
        qr.make(fit=True)

        img = qr.make_image(fill_color="black", back_color="white")
        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        qr_code_base64 = base64.b64encode(buffer.getvalue()).decode()

        # 生成备份码
        backup_codes = [pyotp.random_base32()[:8] for _ in range(10)]

        return {
            "secret": secret,
            "qr_code": f"data:image/png;base64,{qr_code_base64}",
            "backup_codes": backup_codes,
        }

    @staticmethod
    async def verify_and_enable_2fa(
        db: AsyncSession,
        user: User,
        secret: str,
        code: str
    ) -> bool:
        """
        验证并启用 2FA

        Args:
            db: 数据库会话
            user: 用户对象
            secret: 2FA 密钥
            code: 验证码

        Returns:
            bool: 是否成功
        """
        totp = pyotp.TOTP(secret)
        if not totp.verify(code):
            raise ValueError("验证码错误")

        # 启用 2FA
        user.two_factor_enabled = True
        user.two_factor_secret = secret
        await db.commit()

        return True

    @staticmethod
    async def disable_2fa(
        db: AsyncSession,
        user: User,
        password: str
    ) -> bool:
        """
        关闭 2FA

        Args:
            db: 数据库会话
            user: 用户对象
            password: 密码

        Returns:
            bool: 是否成功
        """
        # 验证密码
        if not verify_password(password, user.password_hash):
            raise ValueError("密码错误")

        # 关闭 2FA
        user.two_factor_enabled = False
        user.two_factor_secret = None
        await db.commit()

        return True
