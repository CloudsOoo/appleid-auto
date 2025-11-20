"""
API 依赖注入模块

本模块提供 FastAPI 的依赖注入函数，用于：
- JWT 令牌验证和用户认证
- 权限检查
- 配额验证
- 管理员身份验证

调用关系：
所有需要认证的 API 端点都会使用这些依赖注入函数

示例：
    @router.get("/accounts")
    async def get_accounts(
        current_user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db)
    ):
        # current_user 自动从 JWT 中获取
        pass
"""

from typing import Optional, Callable
from fastapi import Depends, HTTPException, status, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.database import get_db
from app.models.user import User
from app.models.permission import UserPermission
from app.core.security import decode_token


# ========== JWT 安全方案 ==========
security = HTTPBearer(
    scheme_name="JWT Bearer",
    description="请在请求头中添加 Authorization: Bearer <token>",
)


# ========== 基础依赖：获取当前用户 ==========

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    获取当前登录用户（基础依赖）

    从 JWT 令牌中解析用户信息，并从数据库获取完整的用户对象

    Args:
        credentials: JWT 令牌（自动从 Authorization 头获取）
        db: 数据库会话

    Returns:
        User: 当前用户对象

    Raises:
        HTTPException 401: 令牌无效、过期或用户不存在

    业务逻辑:
        1. 从 Authorization 头获取 Bearer Token
        2. 解码 JWT 并提取 user_id
        3. 从数据库查询用户
        4. 验证用户是否存在
        5. 返回用户对象

    使用示例:
        @router.get("/me")
        async def get_me(current_user: User = Depends(get_current_user)):
            return current_user
    """
    # 获取 token
    token = credentials.credentials

    # 解码 token
    payload = decode_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的认证令牌",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 验证 token 类型（必须是 access token）
    if payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="令牌类型错误，请使用访问令牌",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 获取用户 ID
    user_id: int = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="令牌格式错误",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 从数据库查询用户
    result = await db.execute(
        select(User).where(User.id == user_id)
    )
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户不存在",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """
    获取当前激活的用户（增强依赖）

    在 get_current_user 基础上，额外验证用户是否被禁用

    Args:
        current_user: 当前用户（自动注入）

    Returns:
        User: 当前激活的用户对象

    Raises:
        HTTPException 403: 用户已被禁用

    业务逻辑:
        1. 依赖 get_current_user 获取用户
        2. 检查用户 is_active 状态
        3. 如果被禁用，返回 403 错误
        4. 否则返回用户对象

    使用示例:
        @router.post("/accounts")
        async def create_account(
            current_user: User = Depends(get_current_active_user)
        ):
            # 只有激活用户才能创建账号
            pass
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="用户已被禁用，请联系管理员"
        )

    return current_user


async def get_current_admin(
    current_user: User = Depends(get_current_active_user),
) -> User:
    """
    获取当前管理员用户（管理员依赖）

    在 get_current_active_user 基础上，额外验证用户是否是管理员

    Args:
        current_user: 当前激活用户（自动注入）

    Returns:
        User: 当前管理员用户对象

    Raises:
        HTTPException 403: 用户不是管理员

    业务逻辑:
        1. 依赖 get_current_active_user 获取激活用户
        2. 检查用户 is_admin 标志
        3. 如果不是管理员，返回 403 错误
        4. 否则返回管理员用户对象

    使用示例:
        @router.post("/admin/cards/generate")
        async def generate_cards(
            admin_user: User = Depends(get_current_admin)
        ):
            # 只有管理员才能生成卡密
            pass
    """
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要管理员权限"
        )

    return current_user


# ========== 权限检查依赖 ==========

async def get_user_permission(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> UserPermission:
    """
    获取用户权限对象（权限依赖）

    从数据库获取用户的完整权限配置

    Args:
        current_user: 当前激活用户（自动注入）
        db: 数据库会话

    Returns:
        UserPermission: 用户权限对象

    Raises:
        HTTPException 404: 用户权限不存在

    业务逻辑:
        1. 根据 user_id 查询权限表
        2. 如果不存在，返回 404 错误
        3. 返回权限对象

    使用示例:
        @router.post("/accounts")
        async def create_account(
            permission: UserPermission = Depends(get_user_permission)
        ):
            # 可以访问 permission.max_accounts 等配置
            pass
    """
    result = await db.execute(
        select(UserPermission).where(UserPermission.user_id == current_user.id)
    )
    permission = result.scalar_one_or_none()

    if not permission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户权限不存在，请联系管理员"
        )

    return permission


def check_permission(permission_name: str) -> Callable:
    """
    权限检查装饰器工厂（高阶函数）

    创建一个检查特定权限的依赖注入函数

    Args:
        permission_name: 权限名称（如 "allow_custom_html"）

    Returns:
        Callable: 权限检查依赖函数

    Raises:
        HTTPException 403: 用户没有该权限或权限已过期

    业务逻辑:
        1. 获取用户权限对象
        2. 检查权限是否过期
        3. 检查是否有指定的权限
        4. 如果没有权限或过期，返回 403 错误

    使用示例:
        @router.post("/share-pages")
        async def create_share_page(
            current_user: User = Depends(get_current_user),
            _: None = Depends(check_permission("allow_custom_html"))
        ):
            # 只有拥有自定义 HTML 权限的用户才能访问
            pass
    """
    async def permission_checker(
        permission: UserPermission = Depends(get_user_permission),
    ) -> None:
        # 检查权限是否过期
        if permission.is_expired():
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="权限已过期，请续费"
            )

        # 检查是否有指定权限
        has_permission = getattr(permission, permission_name, False)
        if not has_permission:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"没有 {permission_name} 权限"
            )

    return permission_checker


def check_quota(quota_name: str, required: int = 1) -> Callable:
    """
    配额检查装饰器工厂（高阶函数）

    创建一个检查用户配额的依赖注入函数

    Args:
        quota_name: 配额名称（如 "max_accounts"）
        required: 需要的配额数量（默认 1）

    Returns:
        Callable: 配额检查依赖函数

    Raises:
        HTTPException 403: 配额不足

    业务逻辑:
        1. 获取用户权限对象
        2. 检查权限是否过期
        3. 检查配额是否充足
        4. 如果配额不足，返回 403 错误

    使用示例:
        @router.post("/accounts")
        async def create_account(
            _: None = Depends(check_quota("max_accounts", 1))
        ):
            # 自动检查用户是否还有账号配额
            pass

    TODO:
        - 支持更复杂的配额计算逻辑
        - 支持配额预留机制
    """
    async def quota_checker(
        permission: UserPermission = Depends(get_user_permission),
        db: AsyncSession = Depends(get_db),
    ) -> None:
        from app.services.permission_service import PermissionService

        # 检查权限是否过期
        if permission.is_expired():
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="权限已过期，无法使用"
            )

        # 检查配额
        has_quota, error_msg = await PermissionService.check_quota(
            db, permission.user_id, quota_name, required
        )

        if not has_quota:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=error_msg
            )

    return quota_checker


# ========== API Key 认证依赖 ==========

async def get_api_key(
    x_api_key: Optional[str] = Header(None),
    x_api_secret: Optional[str] = Header(None),
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    API Key 认证（用于开放 API）

    通过 API Key 和 Secret 验证用户身份，用于第三方集成

    Args:
        x_api_key: API Key（从请求头获取）
        x_api_secret: API Secret（从请求头获取）
        db: 数据库会话

    Returns:
        User: 用户对象

    Raises:
        HTTPException 401: API Key 无效或缺失
        HTTPException 403: API Key 已禁用

    业务逻辑:
        1. 验证是否提供了 API Key 和 Secret
        2. 从数据库查询 API Key
        3. 验证 Secret 是否匹配
        4. 检查 API Key 是否激活
        5. 返回关联的用户对象

    使用示例:
        @router.post("/api/external/unlock")
        async def external_unlock(
            user: User = Depends(get_api_key)
        ):
            # 使用 API Key 认证的外部接口
            pass

    TODO:
        - 实现 API Key 限流
        - 记录 API 调用日志
        - 支持 API Key 权限范围（scope）
    """
    # TODO: 实现 API Key 认证逻辑
    # 1. 查询 api_keys 表
    # 2. 验证 key 和 secret
    # 3. 检查是否激活
    # 4. 返回用户对象
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="API Key 认证功能尚未实现"
    )


# ========== 可选认证依赖 ==========

async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(
        HTTPBearer(auto_error=False)
    ),
    db: AsyncSession = Depends(get_db),
) -> Optional[User]:
    """
    获取当前用户（可选）

    如果提供了有效的 JWT，返回用户对象；否则返回 None
    用于某些公开接口，但需要区分登录/未登录状态

    Args:
        credentials: JWT 令牌（可选）
        db: 数据库会话

    Returns:
        Optional[User]: 用户对象或 None

    业务逻辑:
        1. 如果没有提供 token，返回 None
        2. 如果提供了 token，尝试解析
        3. 如果解析失败，返回 None（不抛出异常）
        4. 如果解析成功，返回用户对象

    使用示例:
        @router.get("/public/share/{slug}")
        async def access_share_page(
            current_user: Optional[User] = Depends(get_current_user_optional)
        ):
            # 登录用户可能有额外权限，但未登录也能访问
            if current_user:
                # 已登录用户的逻辑
                pass
            else:
                # 未登录用户的逻辑
                pass
    """
    if not credentials:
        return None

    try:
        token = credentials.credentials
        payload = decode_token(token)
        if not payload:
            return None

        user_id: int = payload.get("sub")
        if not user_id:
            return None

        result = await db.execute(
            select(User).where(User.id == user_id)
        )
        user = result.scalar_one_or_none()
        return user

    except Exception:
        # 任何错误都返回 None，不影响公开接口访问
        return None


# ========== 工具函数：手动权限检查 ==========

async def verify_permission(
    db: AsyncSession,
    user_id: int,
    permission_name: str,
) -> bool:
    """
    手动验证用户权限（工具函数）

    在业务逻辑中手动检查权限，不使用依赖注入

    Args:
        db: 数据库会话
        user_id: 用户ID
        permission_name: 权限名称

    Returns:
        bool: 是否有权限

    业务逻辑:
        1. 查询用户权限
        2. 检查是否过期
        3. 检查指定权限
        4. 返回布尔值

    使用示例:
        # 在 Service 层使用
        has_html_permission = await verify_permission(
            db, user_id, "allow_custom_html"
        )
        if not has_html_permission:
            raise ValueError("没有自定义 HTML 权限")
    """
    from app.services.permission_service import PermissionService

    try:
        return await PermissionService.check_permission(db, user_id, permission_name)
    except Exception:
        return False


# ========== 导出所有依赖 ==========

__all__ = [
    "get_current_user",
    "get_current_active_user",
    "get_current_admin",
    "get_user_permission",
    "check_permission",
    "check_quota",
    "get_api_key",
    "get_current_user_optional",
    "verify_permission",
]
