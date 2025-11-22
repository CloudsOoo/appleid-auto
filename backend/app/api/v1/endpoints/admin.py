"""
管理员 API 端点

本模块提供管理员专用的 API 接口，包括：
- 系统统计数据
- 系统设置管理
- 操作日志查看
- 批量操作

调用关系：
    客户端 → admin.py → dependencies.py → 各 Service → 数据库

端点列表：
1. GET /api/v1/admin/stats/overview - 获取系统概览统计
2. GET /api/v1/admin/stats/daily - 获取每日统计
3. GET /api/v1/admin/settings - 获取系统设置
4. PUT /api/v1/admin/settings - 更新系统设置
5. GET /api/v1/admin/logs - 获取操作日志
6. POST /api/v1/admin/init - 初始化系统
"""

from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.api.dependencies import get_current_admin
from app.models.user import User
from app.models.apple_account import AppleAccount
from app.models.task import UnlockTask
from app.models.card import Card
from app.models.proxy import Proxy
from app.models.node import Node
from app.models.share_page import SharePage
from app.models.system import SystemSetting, OperationLog
from app.schemas.common import MessageResponse


# 创建路由器
router = APIRouter()


# ========================================
# 系统概览统计
# ========================================

@router.get(
    "/stats/overview",
    summary="获取系统概览统计",
    description="获取系统整体运行状态统计",
)
async def get_overview_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin),
) -> Dict[str, Any]:
    """
    获取系统概览统计

    返回数据：
        - 用户统计（总数、活跃、今日新增）
        - 账号统计（总数、正常、锁定）
        - 任务统计（总数、成功、失败、进行中）
        - 系统状态（代理池、节点）
    """
    now = datetime.utcnow()
    today_start = datetime.combine(now.date(), datetime.min.time())

    # 用户统计
    total_users = await db.scalar(select(func.count(User.id)))
    active_users = await db.scalar(
        select(func.count(User.id)).where(User.is_active == True)
    )
    new_users_today = await db.scalar(
        select(func.count(User.id)).where(User.created_at >= today_start)
    )

    # 账号统计
    total_accounts = await db.scalar(select(func.count(AppleAccount.id)))
    normal_accounts = await db.scalar(
        select(func.count(AppleAccount.id)).where(AppleAccount.status == "normal")
    )
    locked_accounts = await db.scalar(
        select(func.count(AppleAccount.id)).where(AppleAccount.lock_status == True)
    )

    # 任务统计
    total_tasks = await db.scalar(select(func.count(UnlockTask.id)))
    success_tasks = await db.scalar(
        select(func.count(UnlockTask.id)).where(UnlockTask.status == "success")
    )
    failed_tasks = await db.scalar(
        select(func.count(UnlockTask.id)).where(UnlockTask.status == "failed")
    )
    pending_tasks = await db.scalar(
        select(func.count(UnlockTask.id)).where(
            UnlockTask.status.in_(["pending", "processing"])
        )
    )

    # 卡密统计
    total_cards = await db.scalar(select(func.count(Card.id)))
    unused_cards = await db.scalar(
        select(func.count(Card.id)).where(Card.status == "unused")
    )

    # 代理池统计
    total_proxies = await db.scalar(select(func.count(Proxy.id)))
    active_proxies = await db.scalar(
        select(func.count(Proxy.id)).where(Proxy.is_active == True)
    )

    # 节点统计
    total_nodes = await db.scalar(select(func.count(Node.id)))
    online_nodes = await db.scalar(
        select(func.count(Node.id)).where(Node.status == "online")
    )

    # 分享页统计
    total_share_pages = await db.scalar(select(func.count(SharePage.id)))
    active_share_pages = await db.scalar(
        select(func.count(SharePage.id)).where(SharePage.is_active == True)
    )

    return {
        "code": 200,
        "data": {
            "users": {
                "total": total_users or 0,
                "active": active_users or 0,
                "new_today": new_users_today or 0,
            },
            "accounts": {
                "total": total_accounts or 0,
                "normal": normal_accounts or 0,
                "locked": locked_accounts or 0,
            },
            "tasks": {
                "total": total_tasks or 0,
                "success": success_tasks or 0,
                "failed": failed_tasks or 0,
                "pending": pending_tasks or 0,
                "success_rate": round(
                    (success_tasks or 0) / max((total_tasks or 1), 1) * 100, 2
                ),
            },
            "cards": {
                "total": total_cards or 0,
                "unused": unused_cards or 0,
            },
            "proxies": {
                "total": total_proxies or 0,
                "active": active_proxies or 0,
            },
            "nodes": {
                "total": total_nodes or 0,
                "online": online_nodes or 0,
            },
            "share_pages": {
                "total": total_share_pages or 0,
                "active": active_share_pages or 0,
            },
            "timestamp": datetime.utcnow().isoformat(),
        }
    }


# ========================================
# 每日统计
# ========================================

@router.get(
    "/stats/daily",
    summary="获取每日统计",
    description="获取指定日期范围内的每日统计数据",
)
async def get_daily_stats(
    days: int = Query(7, ge=1, le=30, description="天数"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin),
) -> Dict[str, Any]:
    """
    获取每日统计数据

    参数：
        - days: 统计天数（1-30天）

    返回：
        - 每日新增用户
        - 每日新增账号
        - 每日任务执行情况
    """
    now = datetime.utcnow()
    stats = []

    for i in range(days):
        date = (now - timedelta(days=i)).date()
        start = datetime.combine(date, datetime.min.time())
        end = datetime.combine(date, datetime.max.time())

        # 每日新增用户
        new_users = await db.scalar(
            select(func.count(User.id)).where(
                and_(User.created_at >= start, User.created_at <= end)
            )
        )

        # 每日新增账号
        new_accounts = await db.scalar(
            select(func.count(AppleAccount.id)).where(
                and_(AppleAccount.created_at >= start, AppleAccount.created_at <= end)
            )
        )

        # 每日任务
        total_tasks = await db.scalar(
            select(func.count(UnlockTask.id)).where(
                and_(UnlockTask.created_at >= start, UnlockTask.created_at <= end)
            )
        )
        success_tasks = await db.scalar(
            select(func.count(UnlockTask.id)).where(
                and_(
                    UnlockTask.created_at >= start,
                    UnlockTask.created_at <= end,
                    UnlockTask.status == "success"
                )
            )
        )

        stats.append({
            "date": str(date),
            "new_users": new_users or 0,
            "new_accounts": new_accounts or 0,
            "total_tasks": total_tasks or 0,
            "success_tasks": success_tasks or 0,
        })

    return {
        "code": 200,
        "data": {
            "days": days,
            "stats": list(reversed(stats)),  # 按日期升序
        }
    }


# ========================================
# 系统设置
# ========================================

@router.get(
    "/settings",
    summary="获取系统设置",
    description="获取所有系统设置项",
)
async def get_system_settings(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin),
) -> Dict[str, Any]:
    """
    获取系统设置
    """
    query = select(SystemSetting)
    result = await db.execute(query)
    settings = result.scalars().all()

    settings_dict = {}
    for setting in settings:
        settings_dict[setting.key] = {
            "value": setting.value,
            "description": setting.description,
            "updated_at": setting.updated_at.isoformat() if setting.updated_at else None,
        }

    return {"code": 200, "data": settings_dict}


@router.put(
    "/settings/{key}",
    response_model=MessageResponse,
    summary="更新系统设置",
    description="更新指定的系统设置项",
)
async def update_system_setting(
    key: str,
    value: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    """
    更新系统设置

    参数：
        - key: 设置键名
        - value: 设置值
    """
    # 查找设置
    query = select(SystemSetting).where(SystemSetting.key == key)
    result = await db.execute(query)
    setting = result.scalars().first()

    if setting:
        # 更新现有设置
        setting.value = value
        setting.updated_at = datetime.utcnow()
    else:
        # 创建新设置
        setting = SystemSetting(key=key, value=value)
        db.add(setting)

    await db.commit()

    return MessageResponse(message=f"设置 {key} 已更新")


# ========================================
# 操作日志
# ========================================

@router.get(
    "/logs",
    summary="获取操作日志",
    description="获取系统操作日志，支持分页和过滤",
)
async def get_operation_logs(
    page: int = Query(1, ge=1, description="页码"),
    per_page: int = Query(20, ge=1, le=100, description="每页数量"),
    user_id: Optional[int] = Query(None, description="用户ID过滤"),
    action: Optional[str] = Query(None, description="操作类型过滤"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin),
) -> Dict[str, Any]:
    """
    获取操作日志

    参数：
        - page: 页码
        - per_page: 每页数量
        - user_id: 按用户过滤
        - action: 按操作类型过滤
    """
    # 构建查询
    query = select(OperationLog)

    if user_id:
        query = query.where(OperationLog.user_id == user_id)
    if action:
        query = query.where(OperationLog.action == action)

    # 计算总数
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar()

    # 分页
    offset = (page - 1) * per_page
    query = query.offset(offset).limit(per_page).order_by(OperationLog.created_at.desc())

    # 执行查询
    result = await db.execute(query)
    logs = result.scalars().all()

    # 转换响应格式
    log_list = [
        {
            "id": log.id,
            "user_id": log.user_id,
            "action": log.action,
            "resource_type": log.resource_type,
            "resource_id": log.resource_id,
            "details": log.details,
            "ip_address": log.ip_address,
            "user_agent": log.user_agent,
            "created_at": log.created_at.isoformat() if log.created_at else None,
        }
        for log in logs
    ]

    return {
        "code": 200,
        "data": {
            "items": log_list,
            "total": total,
            "page": page,
            "per_page": per_page,
            "total_pages": (total + per_page - 1) // per_page,
        }
    }


# ========================================
# 系统初始化
# ========================================

@router.post(
    "/init",
    response_model=MessageResponse,
    summary="初始化系统",
    description="初始化系统默认数据（仅首次使用）",
)
async def init_system(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    """
    初始化系统

    此接口用于：
        1. 创建默认系统设置
        2. 创建默认套餐
        3. 其他初始化操作

    注意：此操作应该只在系统首次部署时执行
    """
    from app.models.package import Package

    # 检查是否已初始化
    existing_settings = await db.scalar(select(func.count(SystemSetting.id)))
    if existing_settings and existing_settings > 0:
        return MessageResponse(message="系统已初始化，无需重复操作")

    # 创建默认系统设置
    default_settings = [
        SystemSetting(key="site_name", value="Apple ID 自动解锁系统", description="站点名称"),
        SystemSetting(key="site_description", value="Apple ID 批量管理与自动解锁", description="站点描述"),
        SystemSetting(key="maintenance_mode", value="false", description="维护模式"),
        SystemSetting(key="register_enabled", value="true", description="是否允许注册"),
        SystemSetting(key="default_package_id", value="1", description="默认套餐ID"),
    ]
    for setting in default_settings:
        db.add(setting)

    # 创建默认套餐
    default_packages = [
        Package(
            name="免费套餐",
            description="免费体验，功能有限",
            price=0,
            duration_days=30,
            max_accounts=5,
            max_share_pages=1,
            max_nodes=0,
            min_unlock_interval=3600,
            allow_custom_html=False,
            allow_view_password_history=False,
            allow_batch_import=False,
            allow_api_access=False,
            max_unlock_per_day=10,
            max_import_per_time=10,
            is_active=True,
            sort_order=1,
        ),
        Package(
            name="基础套餐",
            description="适合个人用户",
            price=29.9,
            duration_days=30,
            max_accounts=50,
            max_share_pages=5,
            max_nodes=1,
            min_unlock_interval=1800,
            allow_custom_html=True,
            allow_view_password_history=True,
            allow_batch_import=True,
            allow_api_access=False,
            max_unlock_per_day=100,
            max_import_per_time=50,
            is_active=True,
            sort_order=2,
        ),
        Package(
            name="专业套餐",
            description="适合企业用户",
            price=99.9,
            duration_days=30,
            max_accounts=500,
            max_share_pages=20,
            max_nodes=5,
            min_unlock_interval=300,
            allow_custom_html=True,
            allow_view_password_history=True,
            allow_batch_import=True,
            allow_api_access=True,
            max_unlock_per_day=1000,
            max_import_per_time=200,
            is_active=True,
            sort_order=3,
        ),
    ]
    for package in default_packages:
        db.add(package)

    await db.commit()

    return MessageResponse(message="系统初始化完成")


# ========================================
# 导出
# ========================================

__all__ = ["router"]
