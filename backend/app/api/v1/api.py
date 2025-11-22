"""
API v1 路由汇总
"""
from fastapi import APIRouter

from app.api.v1.endpoints import (
    auth,
    users,
    cards,
    accounts,
    tasks,
    share_pages,
    proxies,
    nodes,
    packages,
    stats,
    admin,
)

api_router = APIRouter()

# 认证相关
api_router.include_router(auth.router, prefix="/auth", tags=["认证"])

# 用户相关
api_router.include_router(users.router, prefix="/users", tags=["用户"])

# 卡密相关
api_router.include_router(cards.router, prefix="/cards", tags=["卡密"])

# Apple ID 管理
api_router.include_router(accounts.router, prefix="/accounts", tags=["Apple ID 管理"])

# 任务管理
api_router.include_router(tasks.router, prefix="/tasks", tags=["任务管理"])

# 分享页
api_router.include_router(share_pages.router, prefix="/share-pages", tags=["分享页"])

# 代理池
api_router.include_router(proxies.router, prefix="/proxies", tags=["代理池"])

# 节点管理
api_router.include_router(nodes.router, prefix="/nodes", tags=["节点管理"])

# 套餐管理
api_router.include_router(packages.router, prefix="/packages", tags=["套餐管理"])

# 统计
api_router.include_router(stats.router, prefix="/stats", tags=["统计"])

# 管理员接口
api_router.include_router(admin.router, prefix="/admin", tags=["管理员"])
