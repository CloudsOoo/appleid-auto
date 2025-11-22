"""
用户管理 API 端点

本模块提供用户管理相关的 API 接口，包括：
- 获取用户列表（管理员）
- 获取用户详情
- 更新用户信息
- 禁用/启用用户
- 删除用户（管理员）

调用关系：
    客户端 → users.py → dependencies.py → AuthService → 数据库

端点列表：
1. GET /api/v1/users - 获取用户列表（管理员）
2. GET /api/v1/users/{user_id} - 获取用户详情
3. PUT /api/v1/users/{user_id} - 更新用户信息
4. PATCH /api/v1/users/{user_id}/status - 修改用户状态
5. DELETE /api/v1/users/{user_id} - 删除用户（管理员）
6. GET /api/v1/users/{user_id}/permissions - 获取用户权限
7. PUT /api/v1/users/{user_id}/permissions - 更新用户权限
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy import select, or_, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.api.dependencies import get_current_user, get_current_active_user, get_current_admin
from app.models.user import User
from app.models.permission import UserPermission
from app.schemas.user import (
    UserResponse,
    UserUpdate,
    UserPermissionResponse,
    UserListQuery,
)
from app.schemas.common import PaginatedResponse, MessageResponse


# 创建路由器
router = APIRouter()


# ========================================
# 用户列表（管理员）
# ========================================

@router.get(
    "",
    response_model=PaginatedResponse,
    summary="获取用户列表",
    description="管理员获取所有用户列表，支持分页和搜索",
)
async def get_users(
    page: int = Query(1, ge=1, description="页码"),
    per_page: int = Query(20, ge=1, le=100, description="每页数量"),
    role: Optional[str] = Query(None, description="角色过滤"),
    is_active: Optional[bool] = Query(None, description="激活状态过滤"),
    search: Optional[str] = Query(None, description="搜索关键词"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    """
    获取用户列表（管理员专用）

    业务逻辑：
        1. 验证管理员权限
        2. 构建查询条件
        3. 执行分页查询
        4. 返回用户列表

    查询参数：
        - page: 页码（默认1）
        - per_page: 每页数量（默认20，最大100）
        - role: 按角色过滤（user/admin）
        - is_active: 按激活状态过滤
        - search: 搜索用户名或邮箱

    响应：
        - 200: 返回分页的用户列表
        - 403: 无管理员权限
    """
    # 构建基础查询
    query = select(User)

    # 应用过滤条件
    if role:
        query = query.where(User.role == role)
    if is_active is not None:
        query = query.where(User.is_active == is_active)
    if search:
        query = query.where(
            or_(
                User.username.ilike(f"%{search}%"),
                User.email.ilike(f"%{search}%"),
                User.full_name.ilike(f"%{search}%"),
            )
        )

    # 计算总数
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar()

    # 分页
    offset = (page - 1) * per_page
    query = query.offset(offset).limit(per_page).order_by(User.created_at.desc())

    # 执行查询
    result = await db.execute(query)
    users = result.scalars().all()

    # 转换响应格式
    user_responses = [UserResponse.model_validate(user) for user in users]

    return {
        "code": 200,
        "data": {
            "items": user_responses,
            "total": total,
            "page": page,
            "per_page": per_page,
            "total_pages": (total + per_page - 1) // per_page,
        }
    }


# ========================================
# 获取用户详情
# ========================================

@router.get(
    "/{user_id}",
    response_model=UserResponse,
    summary="获取用户详情",
    description="获取指定用户的详细信息",
)
async def get_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    获取用户详情

    业务逻辑：
        1. 验证权限（本人或管理员）
        2. 查询用户信息
        3. 返回用户详情

    路径参数：
        - user_id: 用户 ID

    响应：
        - 200: 返回用户详情
        - 403: 无权限查看
        - 404: 用户不存在
    """
    # 检查权限：只能查看自己或管理员可查看所有
    if current_user.id != user_id and current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权查看其他用户信息"
        )

    # 查询用户
    query = select(User).where(User.id == user_id)
    result = await db.execute(query)
    user = result.scalars().first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )

    return UserResponse.model_validate(user)


# ========================================
# 更新用户信息
# ========================================

@router.put(
    "/{user_id}",
    response_model=UserResponse,
    summary="更新用户信息",
    description="更新用户基本信息",
)
async def update_user(
    user_id: int,
    user_data: UserUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    更新用户信息

    业务逻辑：
        1. 验证权限（本人或管理员）
        2. 查询并更新用户信息
        3. 返回更新后的用户信息

    路径参数：
        - user_id: 用户 ID

    请求体：
        - full_name: 全名
        - phone: 手机号
        - avatar_url: 头像 URL

    响应：
        - 200: 更新成功
        - 403: 无权限
        - 404: 用户不存在
    """
    # 检查权限
    if current_user.id != user_id and current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权修改其他用户信息"
        )

    # 查询用户
    query = select(User).where(User.id == user_id)
    result = await db.execute(query)
    user = result.scalars().first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )

    # 更新用户信息
    update_data = user_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(user, field, value)

    await db.commit()
    await db.refresh(user)

    return UserResponse.model_validate(user)


# ========================================
# 修改用户状态
# ========================================

@router.patch(
    "/{user_id}/status",
    response_model=MessageResponse,
    summary="修改用户状态",
    description="启用或禁用用户",
)
async def update_user_status(
    user_id: int,
    is_active: bool,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    """
    修改用户状态（管理员专用）

    业务逻辑：
        1. 验证管理员权限
        2. 不能禁用自己
        3. 更新用户状态

    路径参数：
        - user_id: 用户 ID

    查询参数：
        - is_active: 是否激活

    响应：
        - 200: 状态修改成功
        - 400: 不能禁用自己
        - 404: 用户不存在
    """
    # 不能禁用自己
    if user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="不能禁用自己"
        )

    # 查询用户
    query = select(User).where(User.id == user_id)
    result = await db.execute(query)
    user = result.scalars().first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )

    # 更新状态
    user.is_active = is_active
    await db.commit()

    status_text = "启用" if is_active else "禁用"
    return MessageResponse(message=f"用户已{status_text}")


# ========================================
# 删除用户
# ========================================

@router.delete(
    "/{user_id}",
    response_model=MessageResponse,
    summary="删除用户",
    description="删除用户及其所有数据（管理员）",
)
async def delete_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    """
    删除用户（管理员专用）

    业务逻辑：
        1. 验证管理员权限
        2. 不能删除自己
        3. 删除用户及相关数据

    路径参数：
        - user_id: 用户 ID

    响应：
        - 200: 删除成功
        - 400: 不能删除自己
        - 404: 用户不存在

    注意：此操作不可逆，会删除用户的所有数据
    """
    # 不能删除自己
    if user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="不能删除自己"
        )

    # 查询用户
    query = select(User).where(User.id == user_id)
    result = await db.execute(query)
    user = result.scalars().first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )

    # 删除用户（级联删除相关数据）
    await db.delete(user)
    await db.commit()

    return MessageResponse(message="用户已删除")


# ========================================
# 获取用户权限
# ========================================

@router.get(
    "/{user_id}/permissions",
    response_model=UserPermissionResponse,
    summary="获取用户权限",
    description="获取用户的权限配置",
)
async def get_user_permissions(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    获取用户权限

    业务逻辑：
        1. 验证权限（本人或管理员）
        2. 查询用户权限配置
        3. 返回权限信息

    路径参数：
        - user_id: 用户 ID

    响应：
        - 200: 返回权限配置
        - 403: 无权限
        - 404: 用户或权限不存在
    """
    # 检查权限
    if current_user.id != user_id and current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权查看其他用户权限"
        )

    # 查询权限
    query = select(UserPermission).where(UserPermission.user_id == user_id)
    result = await db.execute(query)
    permission = result.scalars().first()

    if not permission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户权限不存在"
        )

    return UserPermissionResponse.model_validate(permission)


# ========================================
# 导出
# ========================================

__all__ = ["router"]
