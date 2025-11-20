"""
统计 API 端点

本模块实现系统统计功能，包括：
- 用户统计概览（普通用户）
- 管理员统计概览（管理员）

业务场景：
    1. 用户查看自己的使用情况（账号数、任务数、分享页数、配额等）
    2. 管理员查看系统整体运营数据（用户数、账号数、任务数、成功率等）
    3. 为用户提供直观的数据概览，辅助决策

权限控制：
    - 用户统计概览：需要登录
    - 管理员统计概览：仅管理员

依赖关系：
    上游：前端 Dashboard 页面
    下游：Database（直接查询统计数据）
"""

from datetime import datetime, timedelta
from typing import Dict, Any
from fastapi import APIRouter, Depends, status
from sqlalchemy import func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.dependencies import get_current_active_user, get_current_admin, get_db
from app.models.user import User
from app.models.apple_account import AppleAccount
from app.models.task import UnlockTask
from app.models.share_page import SharePage
from app.models.card import Card
from app.models.node import Node
from app.models.proxy import Proxy
from app.models.permission import UserPermission

router = APIRouter(prefix="/stats", tags=["stats"])


# ========================================
# 用户统计概览
# ========================================

@router.get("/overview", response_model=Dict[str, Any], status_code=status.HTTP_200_OK)
async def get_user_stats_overview(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    获取用户统计概览

    业务逻辑：
        1. 统计用户的账号数量（总数、已锁定、正常）
        2. 统计用户的任务数量（总数、各状态分布）
        3. 统计用户的分享页数量（总数、启用数）
        4. 统计用户的今日解锁次数和配额
        5. 获取用户的权限信息（有效期、剩余天数）

    权限要求：
        - 需要登录

    返回结果：
        - 200: 成功，返回统计数据

    示例：
        GET /api/v1/stats/overview

        Response:
        {
            "user_info": {
                "user_id": 1,
                "username": "user1",
                "email": "user1@example.com",
                "is_active": true
            },
            "accounts": {
                "total": 50,
                "locked": 5,
                "normal": 45,
                "max_accounts": 100
            },
            "tasks": {
                "total": 120,
                "pending": 3,
                "in_progress": 2,
                "completed": 100,
                "failed": 15,
                "success_rate": 86.96
            },
            "share_pages": {
                "total": 10,
                "enabled": 8,
                "disabled": 2,
                "total_views": 1234,
                "max_share_pages": 20
            },
            "permission": {
                "expires_at": "2025-12-31T00:00:00",
                "days_remaining": 365,
                "is_expired": false,
                "unlock_count_today": 15,
                "max_unlock_per_day": 500
            },
            "nodes": {
                "total": 3,
                "online": 2,
                "offline": 1,
                "max_nodes": 5
            }
        }

    TODO (优先级 P2):
        - [ ] 添加缓存（Redis）减少数据库查询
        - [ ] 支持时间范围过滤（本周、本月、本年）
        - [ ] 添加趋势数据（相比昨日、上周的增长率）
    """
    try:
        # 1. 用户基本信息
        user_info = {
            "user_id": current_user.id,
            "username": current_user.username,
            "email": current_user.email,
            "is_active": current_user.is_active,
        }

        # 2. 账号统计
        from sqlalchemy import select

        # 总账号数
        total_accounts_query = select(func.count(AppleAccount.id)).where(
            AppleAccount.user_id == current_user.id
        )
        total_accounts = await db.scalar(total_accounts_query) or 0

        # 已锁定账号数
        locked_accounts_query = select(func.count(AppleAccount.id)).where(
            and_(
                AppleAccount.user_id == current_user.id,
                AppleAccount.status == "locked"
            )
        )
        locked_accounts = await db.scalar(locked_accounts_query) or 0

        # 正常账号数
        normal_accounts = total_accounts - locked_accounts

        # 获取权限配额
        permission_query = select(UserPermission).where(
            UserPermission.user_id == current_user.id
        )
        permission_result = await db.execute(permission_query)
        permission = permission_result.scalar_one_or_none()

        accounts_stats = {
            "total": total_accounts,
            "locked": locked_accounts,
            "normal": normal_accounts,
            "max_accounts": permission.max_accounts if permission else 0
        }

        # 3. 任务统计
        # 总任务数
        total_tasks_query = select(func.count(UnlockTask.id)).where(
            UnlockTask.user_id == current_user.id
        )
        total_tasks = await db.scalar(total_tasks_query) or 0

        # 各状态任务数
        pending_tasks_query = select(func.count(UnlockTask.id)).where(
            and_(
                UnlockTask.user_id == current_user.id,
                UnlockTask.status == "pending"
            )
        )
        pending_tasks = await db.scalar(pending_tasks_query) or 0

        in_progress_tasks_query = select(func.count(UnlockTask.id)).where(
            and_(
                UnlockTask.user_id == current_user.id,
                UnlockTask.status == "in_progress"
            )
        )
        in_progress_tasks = await db.scalar(in_progress_tasks_query) or 0

        completed_tasks_query = select(func.count(UnlockTask.id)).where(
            and_(
                UnlockTask.user_id == current_user.id,
                UnlockTask.status == "completed"
            )
        )
        completed_tasks = await db.scalar(completed_tasks_query) or 0

        failed_tasks_query = select(func.count(UnlockTask.id)).where(
            and_(
                UnlockTask.user_id == current_user.id,
                UnlockTask.status == "failed"
            )
        )
        failed_tasks = await db.scalar(failed_tasks_query) or 0

        # 成功率
        success_rate = 0.0
        if total_tasks > 0:
            success_rate = round((completed_tasks / total_tasks) * 100, 2)

        tasks_stats = {
            "total": total_tasks,
            "pending": pending_tasks,
            "in_progress": in_progress_tasks,
            "completed": completed_tasks,
            "failed": failed_tasks,
            "success_rate": success_rate
        }

        # 4. 分享页统计
        total_share_pages_query = select(func.count(SharePage.id)).where(
            SharePage.user_id == current_user.id
        )
        total_share_pages = await db.scalar(total_share_pages_query) or 0

        enabled_share_pages_query = select(func.count(SharePage.id)).where(
            and_(
                SharePage.user_id == current_user.id,
                SharePage.is_active == True
            )
        )
        enabled_share_pages = await db.scalar(enabled_share_pages_query) or 0

        disabled_share_pages = total_share_pages - enabled_share_pages

        # 总访问次数
        total_views_query = select(func.sum(SharePage.view_count)).where(
            SharePage.user_id == current_user.id
        )
        total_views = await db.scalar(total_views_query) or 0

        share_pages_stats = {
            "total": total_share_pages,
            "enabled": enabled_share_pages,
            "disabled": disabled_share_pages,
            "total_views": total_views,
            "max_share_pages": permission.max_share_pages if permission else 0
        }

        # 5. 权限信息
        permission_stats = {
            "expires_at": None,
            "days_remaining": 0,
            "is_expired": True,
            "unlock_count_today": 0,
            "max_unlock_per_day": 0
        }

        if permission:
            now = datetime.utcnow()
            days_remaining = 0
            is_expired = True

            if permission.expires_at:
                days_remaining = (permission.expires_at - now).days
                is_expired = permission.expires_at < now

            permission_stats = {
                "expires_at": permission.expires_at.isoformat() if permission.expires_at else None,
                "days_remaining": max(0, days_remaining),
                "is_expired": is_expired,
                "unlock_count_today": permission.unlock_count_today,
                "max_unlock_per_day": permission.max_unlock_per_day
            }

        # 6. 节点统计
        total_nodes_query = select(func.count(Node.id)).where(
            Node.user_id == current_user.id
        )
        total_nodes = await db.scalar(total_nodes_query) or 0

        online_nodes_query = select(func.count(Node.id)).where(
            and_(
                Node.user_id == current_user.id,
                Node.status == "online"
            )
        )
        online_nodes = await db.scalar(online_nodes_query) or 0

        offline_nodes = total_nodes - online_nodes

        nodes_stats = {
            "total": total_nodes,
            "online": online_nodes,
            "offline": offline_nodes,
            "max_nodes": permission.max_nodes if permission else 0
        }

        # 返回统计数据
        return {
            "user_info": user_info,
            "accounts": accounts_stats,
            "tasks": tasks_stats,
            "share_pages": share_pages_stats,
            "permission": permission_stats,
            "nodes": nodes_stats
        }

    except Exception as e:
        from fastapi import HTTPException
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取统计数据失败: {str(e)}"
        )


# ========================================
# 管理员统计概览
# ========================================

@router.get("/admin/overview", response_model=Dict[str, Any], status_code=status.HTTP_200_OK)
async def get_admin_stats_overview(
    admin_user: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    获取管理员统计概览（系统整体数据）

    业务逻辑：
        1. 统计用户总数（总数、激活、禁用、今日新增）
        2. 统计账号总数（总数、各状态分布）
        3. 统计任务总数（总数、各状态分布、成功率）
        4. 统计分享页总数（总数、访问次数）
        5. 统计卡密（总数、已激活、未使用、已作废）
        6. 统计节点（总数、在线、离线）
        7. 统计代理（总数、可用、不可用）

    权限要求：
        - 需要管理员权限

    返回结果：
        - 200: 成功，返回统计数据
        - 403: 非管理员

    示例：
        GET /api/v1/stats/admin/overview

        Response:
        {
            "users": {
                "total": 1234,
                "active": 1100,
                "inactive": 134,
                "today_new": 15
            },
            "accounts": {
                "total": 12340,
                "locked": 234,
                "normal": 12106
            },
            "tasks": {
                "total": 56789,
                "pending": 120,
                "in_progress": 45,
                "completed": 50000,
                "failed": 6624,
                "success_rate": 88.33
            },
            "share_pages": {
                "total": 567,
                "enabled": 450,
                "disabled": 117,
                "total_views": 123456
            },
            "cards": {
                "total": 500,
                "activated": 300,
                "unused": 150,
                "revoked": 50
            },
            "nodes": {
                "total": 89,
                "online": 75,
                "offline": 14
            },
            "proxies": {
                "total": 234,
                "available": 200,
                "unavailable": 34
            }
        }

    TODO (优先级 P1):
        - [ ] 添加缓存（Redis）减少数据库查询
        - [ ] 支持时间范围过滤（本周、本月、本年）
        - [ ] 添加趋势图数据（7天、30天趋势）
        - [ ] 导出统计报表（CSV、Excel）
    """
    try:
        from sqlalchemy import select

        # 1. 用户统计
        total_users_query = select(func.count(User.id))
        total_users = await db.scalar(total_users_query) or 0

        active_users_query = select(func.count(User.id)).where(User.is_active == True)
        active_users = await db.scalar(active_users_query) or 0

        inactive_users = total_users - active_users

        # 今日新增用户
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        today_new_users_query = select(func.count(User.id)).where(
            User.created_at >= today_start
        )
        today_new_users = await db.scalar(today_new_users_query) or 0

        users_stats = {
            "total": total_users,
            "active": active_users,
            "inactive": inactive_users,
            "today_new": today_new_users
        }

        # 2. 账号统计
        total_accounts_query = select(func.count(AppleAccount.id))
        total_accounts = await db.scalar(total_accounts_query) or 0

        locked_accounts_query = select(func.count(AppleAccount.id)).where(
            AppleAccount.status == "locked"
        )
        locked_accounts = await db.scalar(locked_accounts_query) or 0

        normal_accounts = total_accounts - locked_accounts

        accounts_stats = {
            "total": total_accounts,
            "locked": locked_accounts,
            "normal": normal_accounts
        }

        # 3. 任务统计
        total_tasks_query = select(func.count(UnlockTask.id))
        total_tasks = await db.scalar(total_tasks_query) or 0

        pending_tasks_query = select(func.count(UnlockTask.id)).where(
            UnlockTask.status == "pending"
        )
        pending_tasks = await db.scalar(pending_tasks_query) or 0

        in_progress_tasks_query = select(func.count(UnlockTask.id)).where(
            UnlockTask.status == "in_progress"
        )
        in_progress_tasks = await db.scalar(in_progress_tasks_query) or 0

        completed_tasks_query = select(func.count(UnlockTask.id)).where(
            UnlockTask.status == "completed"
        )
        completed_tasks = await db.scalar(completed_tasks_query) or 0

        failed_tasks_query = select(func.count(UnlockTask.id)).where(
            UnlockTask.status == "failed"
        )
        failed_tasks = await db.scalar(failed_tasks_query) or 0

        success_rate = 0.0
        if total_tasks > 0:
            success_rate = round((completed_tasks / total_tasks) * 100, 2)

        tasks_stats = {
            "total": total_tasks,
            "pending": pending_tasks,
            "in_progress": in_progress_tasks,
            "completed": completed_tasks,
            "failed": failed_tasks,
            "success_rate": success_rate
        }

        # 4. 分享页统计
        total_share_pages_query = select(func.count(SharePage.id))
        total_share_pages = await db.scalar(total_share_pages_query) or 0

        enabled_share_pages_query = select(func.count(SharePage.id)).where(
            SharePage.is_active == True
        )
        enabled_share_pages = await db.scalar(enabled_share_pages_query) or 0

        disabled_share_pages = total_share_pages - enabled_share_pages

        total_views_query = select(func.sum(SharePage.view_count))
        total_views = await db.scalar(total_views_query) or 0

        share_pages_stats = {
            "total": total_share_pages,
            "enabled": enabled_share_pages,
            "disabled": disabled_share_pages,
            "total_views": total_views
        }

        # 5. 卡密统计
        total_cards_query = select(func.count(Card.id))
        total_cards = await db.scalar(total_cards_query) or 0

        activated_cards_query = select(func.count(Card.id)).where(
            Card.status == "activated"
        )
        activated_cards = await db.scalar(activated_cards_query) or 0

        unused_cards_query = select(func.count(Card.id)).where(
            Card.status == "unused"
        )
        unused_cards = await db.scalar(unused_cards_query) or 0

        revoked_cards_query = select(func.count(Card.id)).where(
            Card.status == "revoked"
        )
        revoked_cards = await db.scalar(revoked_cards_query) or 0

        cards_stats = {
            "total": total_cards,
            "activated": activated_cards,
            "unused": unused_cards,
            "revoked": revoked_cards
        }

        # 6. 节点统计
        total_nodes_query = select(func.count(Node.id))
        total_nodes = await db.scalar(total_nodes_query) or 0

        online_nodes_query = select(func.count(Node.id)).where(
            Node.status == "online"
        )
        online_nodes = await db.scalar(online_nodes_query) or 0

        offline_nodes = total_nodes - online_nodes

        nodes_stats = {
            "total": total_nodes,
            "online": online_nodes,
            "offline": offline_nodes
        }

        # 7. 代理统计
        total_proxies_query = select(func.count(Proxy.id))
        total_proxies = await db.scalar(total_proxies_query) or 0

        available_proxies_query = select(func.count(Proxy.id)).where(
            and_(
                Proxy.status == "available",
                Proxy.is_active == True
            )
        )
        available_proxies = await db.scalar(available_proxies_query) or 0

        unavailable_proxies = total_proxies - available_proxies

        proxies_stats = {
            "total": total_proxies,
            "available": available_proxies,
            "unavailable": unavailable_proxies
        }

        # 返回统计数据
        return {
            "users": users_stats,
            "accounts": accounts_stats,
            "tasks": tasks_stats,
            "share_pages": share_pages_stats,
            "cards": cards_stats,
            "nodes": nodes_stats,
            "proxies": proxies_stats
        }

    except Exception as e:
        from fastapi import HTTPException
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取管理员统计数据失败: {str(e)}"
        )


# ========================================
# 导出
# ========================================

__all__ = ["router"]
