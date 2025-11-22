"""
套餐管理 API 端点

本模块实现套餐的查询和管理功能，包括：
- 用户查看套餐列表（公开）
- 管理员创建套餐
- 管理员更新套餐
- 管理员删除套餐

业务场景：
    1. 用户查看可用套餐，选择合适的套餐购买卡密
    2. 管理员创建不同等级的套餐（免费版、专业版、企业版等）
    3. 套餐定义了用户的权限配额（账号数、分享页数、节点数等）
    4. 激活卡密时，用户权限会继承套餐配置
    5. 管理员可以随时调整套餐配置和价格

权限控制：
    - 查看套餐列表：所有用户（包括未登录用户）
    - 创建套餐：仅管理员
    - 更新套餐：仅管理员
    - 删除套餐：仅管理员

依赖关系：
    上游：前端用户、管理员
    下游：PackageService、CardService（生成卡密时关联套餐）
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_admin
from app.db.database import get_db
from app.models.user import User
from app.schemas.package import (
    PackageCreate,
    PackageUpdate,
    PackageResponse,
)
from app.services.package_service import PackageService

router = APIRouter()


# ========================================
# 获取套餐列表（公开接口）
# ========================================

@router.get("", response_model=List[PackageResponse], status_code=status.HTTP_200_OK)
async def get_package_list(
    db: AsyncSession = Depends(get_db),
):
    """
    获取套餐列表（公开接口）

    业务逻辑：
        1. 查询所有激活的套餐（is_active = true）
        2. 按 sort_order 排序（从小到大）
        3. 返回套餐列表

    权限要求：
        - 无需登录，所有用户可访问

    使用场景：
        - 用户注册前查看套餐
        - 购买卡密页面展示套餐
        - 用户选择升级套餐

    返回结果：
        - 200: 成功，返回套餐列表

    示例：
        GET /api/v1/packages

        Response:
        [
            {
                "id": 1,
                "name": "免费版",
                "description": "适合个人用户",
                "max_accounts": 10,
                "max_share_pages": 5,
                "max_nodes": 1,
                "min_unlock_interval": 3600,
                "allow_custom_html": false,
                "allow_view_password_history": false,
                "allow_batch_import": true,
                "allow_api_access": false,
                "max_unlock_per_day": 100,
                "max_import_per_time": 100,
                "price": 0.00,
                "currency": "CNY",
                "is_active": true,
                "sort_order": 1,
                "created_at": "2025-11-20T10:00:00",
                "updated_at": "2025-11-20T10:00:00"
            },
            {
                "id": 2,
                "name": "专业版",
                "description": "适合中小企业",
                "max_accounts": 200,
                "max_share_pages": 20,
                "max_nodes": 5,
                "min_unlock_interval": 600,
                "allow_custom_html": true,
                "allow_view_password_history": true,
                "allow_batch_import": true,
                "allow_api_access": true,
                "max_unlock_per_day": 500,
                "max_import_per_time": 500,
                "price": 299.00,
                "currency": "CNY",
                "is_active": true,
                "sort_order": 2,
                "created_at": "2025-11-20T10:00:00",
                "updated_at": "2025-11-20T10:00:00"
            }
        ]

    套餐字段说明：
        - max_accounts: 最大账号数（Apple ID）
        - max_share_pages: 最大分享页数
        - max_nodes: 最大节点数
        - min_unlock_interval: 最短解锁间隔（秒）
        - allow_custom_html: 允许自定义 HTML（分享页）
        - allow_view_password_history: 允许查看历史密码
        - allow_batch_import: 允许批量导入
        - allow_api_access: 允许 API 访问
        - max_unlock_per_day: 每日最大解锁次数
        - max_import_per_time: 单次导入限制

    TODO (优先级 P2):
        - [ ] 添加套餐推荐标签（热门、推荐等）
        - [ ] 支持套餐对比功能
        - [ ] 添加套餐优惠活动（限时折扣）
    """
    try:
        # 获取所有激活的套餐
        packages = await PackageService.get_all_active_packages(db=db)
        return [PackageResponse.model_validate(pkg) for pkg in packages]

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取套餐列表失败: {str(e)}"
        )


# ========================================
# 管理员接口：创建套餐
# ========================================

@router.post("/admin/packages", response_model=PackageResponse, status_code=status.HTTP_201_CREATED)
async def create_package(
    data: PackageCreate,
    admin_user: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    创建套餐（管理员）

    业务逻辑：
        1. 验证管理员身份
        2. 创建套餐记录
        3. 返回套餐信息

    权限要求：
        - 需要管理员权限

    请求参数：
        - name: 套餐名称（必填，1-100字符）
        - description: 套餐描述（可选）
        - max_accounts: 最大账号数（默认10，最小1）
        - max_share_pages: 最大分享页数（默认5，最小1）
        - max_nodes: 最大节点数（默认1，最小1）
        - min_unlock_interval: 最短解锁间隔（默认3600秒，最小60秒）
        - allow_custom_html: 允许自定义 HTML（默认false）
        - allow_view_password_history: 允许查看历史密码（默认false）
        - allow_batch_import: 允许批量导入（默认true）
        - allow_api_access: 允许 API 访问（默认false）
        - max_unlock_per_day: 每日最大解锁次数（默认100，最小1）
        - max_import_per_time: 单次导入限制（默认100，最小1）
        - price: 价格（可选，最小0）
        - currency: 货币（默认CNY）
        - sort_order: 排序（默认0）

    返回结果：
        - 201: 创建成功，返回套餐信息
        - 403: 非管理员
        - 422: 参数验证失败

    示例：
        POST /api/v1/packages/admin/packages
        {
            "name": "企业版",
            "description": "适合大型企业",
            "max_accounts": 1000,
            "max_share_pages": 100,
            "max_nodes": 20,
            "min_unlock_interval": 60,
            "allow_custom_html": true,
            "allow_view_password_history": true,
            "allow_batch_import": true,
            "allow_api_access": true,
            "max_unlock_per_day": 5000,
            "max_import_per_time": 1000,
            "price": 999.00,
            "currency": "CNY",
            "sort_order": 3
        }

        Response:
        {
            "id": 3,
            "name": "企业版",
            "description": "适合大型企业",
            ...
        }

    TODO (优先级 P1):
        - [ ] 添加套餐名称唯一性检查
        - [ ] 支持套餐模板（快速创建常用套餐）
        - [ ] 添加套餐创建日志
    """
    try:
        # 创建套餐
        package = await PackageService.create_package(db=db, data=data)
        return package

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"创建套餐失败: {str(e)}"
        )


# ========================================
# 管理员接口：获取套餐列表（包括禁用的）
# ========================================

@router.get("/admin/packages", response_model=dict, status_code=status.HTTP_200_OK)
async def get_admin_package_list(
    page: int = Query(1, ge=1, description="页码"),
    per_page: int = Query(20, ge=1, le=100, description="每页数量"),
    is_active: Optional[bool] = Query(None, description="激活状态过滤"),
    include_inactive: bool = Query(True, description="是否包含禁用的套餐"),
    admin_user: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    获取套餐列表（管理员，包括禁用的）

    业务逻辑：
        1. 验证管理员身份
        2. 查询所有套餐（包括禁用的）
        3. 支持分页和过滤
        4. 返回套餐列表

    权限要求：
        - 需要管理员权限

    查询参数：
        - page: 页码（默认1）
        - per_page: 每页数量（默认20，最大100）
        - is_active: 激活状态过滤（true/false）
        - include_inactive: 是否包含禁用的套餐（默认true）

    返回结果：
        - 200: 成功，返回套餐列表
        - 403: 非管理员

    示例：
        GET /api/v1/packages/admin/packages?page=1&per_page=20&include_inactive=true

        Response:
        {
            "total": 5,
            "page": 1,
            "per_page": 20,
            "total_pages": 1,
            "items": [...]
        }
    """
    try:
        # 获取套餐列表
        packages, total = await PackageService.get_package_list(
            db=db,
            page=page,
            per_page=per_page,
            is_active=is_active,
            include_inactive=include_inactive,
        )

        # 计算总页数
        total_pages = (total + per_page - 1) // per_page

        return {
            "total": total,
            "page": page,
            "per_page": per_page,
            "total_pages": total_pages,
            "items": [PackageResponse.model_validate(pkg) for pkg in packages]
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取套餐列表失败: {str(e)}"
        )


# ========================================
# 管理员接口：获取套餐详情
# ========================================

@router.get("/admin/packages/{package_id}", response_model=PackageResponse, status_code=status.HTTP_200_OK)
async def get_package(
    package_id: int,
    admin_user: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    获取套餐详情（管理员）

    业务逻辑：
        1. 验证管理员身份
        2. 查询套餐详情
        3. 返回套餐信息

    权限要求：
        - 需要管理员权限

    路径参数：
        - package_id: 套餐 ID

    返回结果：
        - 200: 成功，返回套餐详情
        - 403: 非管理员
        - 404: 套餐不存在

    示例：
        GET /api/v1/packages/admin/packages/1

        Response:
        {
            "id": 1,
            "name": "免费版",
            ...
        }
    """
    package = await PackageService.get_package(db=db, package_id=package_id)

    if not package:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="套餐不存在"
        )

    return package


# ========================================
# 管理员接口：更新套餐
# ========================================

@router.put("/admin/packages/{package_id}", response_model=PackageResponse, status_code=status.HTTP_200_OK)
async def update_package(
    package_id: int,
    data: PackageUpdate,
    admin_user: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    更新套餐（管理员）

    业务逻辑：
        1. 验证管理员身份
        2. 查询套餐是否存在
        3. 更新套餐信息
        4. 返回更新后的套餐信息

    权限要求：
        - 需要管理员权限

    路径参数：
        - package_id: 套餐 ID

    请求参数（所有字段都是可选的）：
        - name: 套餐名称
        - description: 套餐描述
        - max_accounts: 最大账号数
        - max_share_pages: 最大分享页数
        - max_nodes: 最大节点数
        - min_unlock_interval: 最短解锁间隔
        - allow_custom_html: 允许自定义 HTML
        - allow_view_password_history: 允许查看历史密码
        - allow_batch_import: 允许批量导入
        - allow_api_access: 允许 API 访问
        - max_unlock_per_day: 每日最大解锁次数
        - max_import_per_time: 单次导入限制
        - price: 价格
        - currency: 货币
        - is_active: 激活状态
        - sort_order: 排序

    返回结果：
        - 200: 更新成功，返回套餐信息
        - 403: 非管理员
        - 404: 套餐不存在

    示例：
        PUT /api/v1/packages/admin/packages/1
        {
            "price": 199.00,
            "max_accounts": 150,
            "is_active": true
        }

        Response:
        {
            "id": 1,
            "price": 199.00,
            "max_accounts": 150,
            ...
        }

    注意事项：
        - 更新套餐不会影响已激活的用户权限
        - 如需批量更新用户权限，需要另外操作

    TODO (优先级 P1):
        - [ ] 添加更新历史记录
        - [ ] 支持批量更新已有用户的权限（可选）
        - [ ] 添加套餐更新通知
    """
    package = await PackageService.update_package(
        db=db,
        package_id=package_id,
        data=data
    )

    if not package:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="套餐不存在"
        )

    return package


# ========================================
# 管理员接口：删除套餐
# ========================================

@router.delete("/admin/packages/{package_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_package(
    package_id: int,
    admin_user: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    删除套餐（管理员）

    业务逻辑：
        1. 验证管理员身份
        2. 查询套餐是否存在
        3. 删除套餐记录
        4. 返回 204 No Content

    权限要求：
        - 需要管理员权限

    路径参数：
        - package_id: 套餐 ID

    返回结果：
        - 204: 删除成功，无返回内容
        - 403: 非管理员
        - 404: 套餐不存在

    示例：
        DELETE /api/v1/packages/admin/packages/1

        Response: 204 No Content

    注意事项：
        - 删除套餐是永久性的，无法恢复
        - 如果有卡密或用户权限关联此套餐，建议禁用而不是删除
        - 建议先将 is_active 设为 false，观察一段时间后再删除

    TODO (优先级 P0):
        - [ ] 检查是否有关联的卡密或用户权限（如果有，禁止删除）
        - [ ] 软删除（标记为 deleted，而不是物理删除）
        - [ ] 添加删除前确认
        - [ ] 记录删除历史
    """
    success = await PackageService.delete_package(db=db, package_id=package_id)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="套餐不存在"
        )

    return None


# ========================================
# 导出
# ========================================

__all__ = ["router"]
