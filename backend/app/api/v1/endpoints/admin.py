"""
管理员 API 端点

本模块提供管理员相关的 API 接口，包括：
- 系统设置管理
- API 密钥管理
- 操作日志查询
- 系统状态监控
"""

from typing import Optional, List
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_

from app.db.database import get_db
from app.api.dependencies import get_current_admin
from app.models.user import User
from app.models.system import SystemSetting, APIKey, OperationLog
from app.models.apple_account import AppleAccount
from app.models.card import Card
from app.models.task import UnlockTask
from pydantic import BaseModel, Field


# 创建路由器
router = APIRouter()


# ========== Schemas ==========
class SystemSettingUpdate(BaseModel):
    """系统设置更新"""
    value: str = Field(..., description="设置值")
    description: Optional[str] = Field(None, description="描述")


class APIKeyCreate(BaseModel):
    """API 密钥创建"""
    name: str = Field(..., max_length=100, description="名称")
    expires_at: Optional[datetime] = Field(None, description="过期时间")


class SystemSettingResponse(BaseModel):
    """系统设置响应"""
    id: int
    key: str
    value: str
    description: Optional[str]
    updated_at: datetime

    class Config:
        from_attributes = True


class APIKeyResponse(BaseModel):
    """API 密钥响应"""
    id: int
    name: str
    key_prefix: str
    is_active: bool
    created_at: datetime
    expires_at: Optional[datetime]
    last_used_at: Optional[datetime]

    class Config:
        from_attributes = True


class OperationLogResponse(BaseModel):
    """操作日志响应"""
    id: int
    user_id: Optional[int]
    username: Optional[str]
    action: str
    resource_type: str
    resource_id: Optional[int]
    details: Optional[str]
    ip_address: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


# ========== 系统概览 ==========
@router.get("/overview")
async def get_system_overview(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    """
    获取系统概览统计信息
    """
    # 用户统计
    user_count = await db.execute(select(func.count(User.id)))
    total_users = user_count.scalar() or 0

    # Apple ID 统计
    account_count = await db.execute(select(func.count(AppleAccount.id)))
    total_accounts = account_count.scalar() or 0

    # 卡密统计
    card_count = await db.execute(select(func.count(Card.id)))
    total_cards = card_count.scalar() or 0

    active_cards = await db.execute(
        select(func.count(Card.id)).where(Card.status == "active")
    )
    active_card_count = active_cards.scalar() or 0

    # 任务统计
    task_count = await db.execute(select(func.count(UnlockTask.id)))
    total_tasks = task_count.scalar() or 0

    today = datetime.utcnow().date()
    today_start = datetime.combine(today, datetime.min.time())

    today_tasks = await db.execute(
        select(func.count(UnlockTask.id)).where(
            UnlockTask.created_at >= today_start
        )
    )
    today_task_count = today_tasks.scalar() or 0

    return {
        "users": {
            "total": total_users,
        },
        "accounts": {
            "total": total_accounts,
        },
        "cards": {
            "total": total_cards,
            "active": active_card_count,
        },
        "tasks": {
            "total": total_tasks,
            "today": today_task_count,
        },
    }


# ========== 系统设置 ==========
@router.get("/settings", response_model=List[SystemSettingResponse])
async def get_system_settings(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    """
    获取所有系统设置
    """
    result = await db.execute(select(SystemSetting).order_by(SystemSetting.key))
    settings = result.scalars().all()
    return settings


@router.put("/settings/{key}", response_model=SystemSettingResponse)
async def update_system_setting(
    key: str,
    setting_update: SystemSettingUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    """
    更新系统设置
    """
    result = await db.execute(
        select(SystemSetting).where(SystemSetting.key == key)
    )
    setting = result.scalar_one_or_none()

    if not setting:
        # 创建新设置
        setting = SystemSetting(
            key=key,
            value=setting_update.value,
            description=setting_update.description,
        )
        db.add(setting)
    else:
        setting.value = setting_update.value
        if setting_update.description is not None:
            setting.description = setting_update.description
        setting.updated_at = datetime.utcnow()

    await db.commit()
    await db.refresh(setting)
    return setting


# ========== API 密钥管理 ==========
@router.get("/api-keys", response_model=List[APIKeyResponse])
async def get_api_keys(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    """
    获取所有 API 密钥
    """
    result = await db.execute(
        select(APIKey).order_by(APIKey.created_at.desc())
    )
    keys = result.scalars().all()
    return keys


@router.post("/api-keys")
async def create_api_key(
    key_create: APIKeyCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    """
    创建新的 API 密钥
    """
    import secrets

    # 生成随机密钥
    full_key = secrets.token_urlsafe(32)
    key_prefix = full_key[:8]

    api_key = APIKey(
        name=key_create.name,
        key=full_key,
        key_prefix=key_prefix,
        expires_at=key_create.expires_at,
        created_by=current_user.id,
    )

    db.add(api_key)
    await db.commit()
    await db.refresh(api_key)

    # 只在创建时返回完整密钥
    return {
        "id": api_key.id,
        "name": api_key.name,
        "key": full_key,  # 完整密钥只显示一次
        "key_prefix": key_prefix,
        "expires_at": api_key.expires_at,
        "message": "请保存好此密钥，它只会显示一次！"
    }


@router.delete("/api-keys/{key_id}")
async def delete_api_key(
    key_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    """
    删除 API 密钥
    """
    result = await db.execute(select(APIKey).where(APIKey.id == key_id))
    api_key = result.scalar_one_or_none()

    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API 密钥不存在"
        )

    await db.delete(api_key)
    await db.commit()

    return {"message": "API 密钥已删除"}


# ========== 操作日志 ==========
@router.get("/logs", response_model=dict)
async def get_operation_logs(
    page: int = Query(1, ge=1, description="页码"),
    per_page: int = Query(20, ge=1, le=100, description="每页数量"),
    action: Optional[str] = Query(None, description="操作类型"),
    resource_type: Optional[str] = Query(None, description="资源类型"),
    user_id: Optional[int] = Query(None, description="用户ID"),
    start_date: Optional[datetime] = Query(None, description="开始时间"),
    end_date: Optional[datetime] = Query(None, description="结束时间"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    """
    获取操作日志列表
    """
    # 构建查询
    query = select(OperationLog)
    count_query = select(func.count(OperationLog.id))

    filters = []

    if action:
        filters.append(OperationLog.action == action)
    if resource_type:
        filters.append(OperationLog.resource_type == resource_type)
    if user_id:
        filters.append(OperationLog.user_id == user_id)
    if start_date:
        filters.append(OperationLog.created_at >= start_date)
    if end_date:
        filters.append(OperationLog.created_at <= end_date)

    if filters:
        query = query.where(and_(*filters))
        count_query = count_query.where(and_(*filters))

    # 获取总数
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    # 分页
    offset = (page - 1) * per_page
    query = query.offset(offset).limit(per_page).order_by(OperationLog.id.desc())

    result = await db.execute(query)
    logs = result.scalars().all()

    return {
        "items": [OperationLogResponse.model_validate(log) for log in logs],
        "total": total,
        "page": page,
        "per_page": per_page,
        "pages": (total + per_page - 1) // per_page,
    }
