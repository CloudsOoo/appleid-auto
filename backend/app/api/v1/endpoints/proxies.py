"""
代理池管理 API 端点

本模块实现代理池的完整 CRUD 操作和测试功能，包括：
- 添加代理
- 获取代理列表（支持分页和过滤）
- 更新代理配置
- 删除代理
- 测试代理可用性

业务场景：
    1. 用户可以添加自己的私有代理
    2. 管理员可以添加公共代理（user_id = NULL）
    3. 用户查看代理列表时，可以看到自己的私有代理和公共代理
    4. 代理测试会更新代理的健康状态和统计信息
    5. 代理池用于 Celery 任务中的网络请求

权限控制：
    - 添加代理：需要登录用户
    - 查看代理列表：需要登录用户
    - 更新代理：只能更新自己的代理
    - 删除代理：只能删除自己的代理
    - 测试代理：需要登录用户

依赖关系：
    上游：前端、系统管理员
    下游：ProxyService、Celery 任务（account_tasks、maintenance_tasks）
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_active_user
from app.db.database import get_db
from app.models.user import User
from app.schemas.proxy import (
    ProxyCreate,
    ProxyUpdate,
    ProxyResponse,
    ProxyTestResponse,
)
from app.services.proxy_service import ProxyService

router = APIRouter()


# ========================================
# 添加代理
# ========================================

@router.post("", response_model=ProxyResponse, status_code=status.HTTP_201_CREATED)
async def create_proxy(
    data: ProxyCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    添加代理

    业务逻辑：
        1. 验证用户身份（需要登录）
        2. 检查代理是否已存在（同一用户不能添加重复的 host:port）
        3. 创建代理记录，关联到当前用户
        4. 返回创建的代理信息

    权限要求：
        - 需要登录用户

    请求参数：
        - proxy_type: 代理类型（http/https/socks5）
        - host: 主机地址
        - port: 端口（1-65535）
        - username: 用户名（可选）
        - password: 密码（可选）
        - country: 国家代码（可选，如 US、CN）
        - region: 地区（可选）
        - priority: 优先级（0-10，默认0）

    返回结果：
        - 201: 创建成功，返回代理信息
        - 400: 代理已存在
        - 401: 未登录
        - 422: 参数验证失败

    示例：
        POST /api/v1/proxies
        {
            "proxy_type": "socks5",
            "host": "proxy.example.com",
            "port": 1080,
            "username": "user",
            "password": "pass",
            "country": "US",
            "priority": 1
        }

        Response:
        {
            "id": 1,
            "proxy_type": "socks5",
            "host": "proxy.example.com",
            "port": 1080,
            "username": "user",
            "status": "active",
            "is_active": true,
            "success_count": 0,
            "failure_count": 0,
            "success_rate": 0.0,
            "avg_response_time": null,
            "country": "US",
            "priority": 1,
            "created_at": "2025-11-20T12:00:00"
        }

    TODO (优先级 P1):
        - [ ] 添加代理数量配额限制（用户权限中的 max_proxies）
        - [ ] 添加代理有效性验证（创建时自动测试）
        - [ ] 支持批量导入代理（CSV/TXT 文件）
        - [ ] 添加代理去重逻辑（全局去重，避免多个用户添加相同代理）
    """
    try:
        # TODO: 检查用户权限中的代理数量配额
        # if user.permissions.proxies_count >= user.permissions.max_proxies:
        #     raise HTTPException(
        #         status_code=status.HTTP_403_FORBIDDEN,
        #         detail="已达到代理数量上限"
        #     )

        # 创建代理
        proxy = await ProxyService.create_proxy(
            db=db,
            user_id=current_user.id,
            data=data
        )

        return proxy

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"创建代理失败: {str(e)}"
        )


# ========================================
# 获取代理列表
# ========================================

@router.get("", response_model=dict, status_code=status.HTTP_200_OK)
async def get_proxy_list(
    page: int = Query(1, ge=1, description="页码"),
    per_page: int = Query(20, ge=1, le=100, description="每页数量"),
    status_filter: Optional[str] = Query(None, alias="status", description="状态过滤（active/failed/testing）"),
    is_active: Optional[bool] = Query(None, description="激活状态过滤"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    获取代理列表（分页）

    业务逻辑：
        1. 验证用户身份（需要登录）
        2. 查询用户自己的私有代理 + 公共代理
        3. 支持按状态、激活状态过滤
        4. 支持分页
        5. 返回代理列表和总数

    权限要求：
        - 需要登录用户

    查询参数：
        - page: 页码（默认1）
        - per_page: 每页数量（默认20，最大100）
        - status: 状态过滤（active/failed/testing）
        - is_active: 激活状态过滤（true/false）

    返回结果：
        - 200: 成功，返回代理列表
        - 401: 未登录

    示例：
        GET /api/v1/proxies?page=1&per_page=20&status=active

        Response:
        {
            "total": 50,
            "page": 1,
            "per_page": 20,
            "total_pages": 3,
            "items": [
                {
                    "id": 1,
                    "proxy_type": "socks5",
                    "host": "proxy.example.com",
                    "port": 1080,
                    "username": "user",
                    "status": "active",
                    "is_active": true,
                    "success_count": 100,
                    "failure_count": 5,
                    "success_rate": 95.24,
                    "avg_response_time": 234,
                    "country": "US",
                    "priority": 1,
                    "last_checked_at": "2025-11-20T12:00:00",
                    "created_at": "2025-11-19T10:00:00"
                }
            ]
        }

    TODO (优先级 P2):
        - [ ] 支持按国家/地区过滤
        - [ ] 支持按成功率排序
        - [ ] 支持按响应时间排序
        - [ ] 添加代理类型过滤
        - [ ] 添加搜索功能（按 host 搜索）
    """
    try:
        # 获取代理列表
        proxies, total = await ProxyService.get_proxy_list(
            db=db,
            user_id=current_user.id,
            page=page,
            per_page=per_page,
            status=status_filter,
            is_active=is_active,
        )

        # 计算总页数
        total_pages = (total + per_page - 1) // per_page

        return {
            "total": total,
            "page": page,
            "per_page": per_page,
            "total_pages": total_pages,
            "items": [ProxyResponse.model_validate(proxy) for proxy in proxies]
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取代理列表失败: {str(e)}"
        )


# ========================================
# 获取代理详情
# ========================================

@router.get("/{proxy_id}", response_model=ProxyResponse, status_code=status.HTTP_200_OK)
async def get_proxy(
    proxy_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    获取代理详情

    业务逻辑：
        1. 验证用户身份（需要登录）
        2. 查询代理详情
        3. 验证权限（只能查看自己的私有代理或公共代理）
        4. 返回代理详细信息

    权限要求：
        - 需要登录用户
        - 只能查看自己的私有代理或公共代理

    路径参数：
        - proxy_id: 代理 ID

    返回结果：
        - 200: 成功，返回代理详情
        - 401: 未登录
        - 404: 代理不存在或无权限访问

    示例：
        GET /api/v1/proxies/1

        Response:
        {
            "id": 1,
            "proxy_type": "socks5",
            "host": "proxy.example.com",
            "port": 1080,
            "status": "active",
            "success_rate": 95.24,
            ...
        }
    """
    proxy = await ProxyService.get_proxy(
        db=db,
        proxy_id=proxy_id,
        user_id=current_user.id
    )

    if not proxy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="代理不存在或无权限访问"
        )

    return proxy


# ========================================
# 更新代理
# ========================================

@router.put("/{proxy_id}", response_model=ProxyResponse, status_code=status.HTTP_200_OK)
async def update_proxy(
    proxy_id: int,
    data: ProxyUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    更新代理配置

    业务逻辑：
        1. 验证用户身份（需要登录）
        2. 查询代理是否存在
        3. 验证权限（只能更新自己的代理）
        4. 更新代理信息
        5. 返回更新后的代理信息

    权限要求：
        - 需要登录用户
        - 只能更新自己的私有代理

    路径参数：
        - proxy_id: 代理 ID

    请求参数（所有字段都是可选的）：
        - username: 用户名
        - password: 密码
        - country: 国家代码
        - region: 地区
        - priority: 优先级（0-10）
        - is_active: 激活状态

    返回结果：
        - 200: 更新成功，返回代理信息
        - 401: 未登录
        - 404: 代理不存在或无权限更新

    示例：
        PUT /api/v1/proxies/1
        {
            "priority": 5,
            "is_active": true
        }

        Response:
        {
            "id": 1,
            "priority": 5,
            "is_active": true,
            ...
        }

    TODO (优先级 P2):
        - [ ] 支持更新 host 和 port（需要检查是否与其他代理冲突）
        - [ ] 更新后自动重新测试代理
        - [ ] 添加更新历史记录
    """
    proxy = await ProxyService.update_proxy(
        db=db,
        proxy_id=proxy_id,
        user_id=current_user.id,
        data=data
    )

    if not proxy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="代理不存在或无权限更新"
        )

    return proxy


# ========================================
# 删除代理
# ========================================

@router.delete("/{proxy_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_proxy(
    proxy_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    删除代理

    业务逻辑：
        1. 验证用户身份（需要登录）
        2. 查询代理是否存在
        3. 验证权限（只能删除自己的代理）
        4. 删除代理记录
        5. 返回 204 No Content

    权限要求：
        - 需要登录用户
        - 只能删除自己的私有代理

    路径参数：
        - proxy_id: 代理 ID

    返回结果：
        - 204: 删除成功，无返回内容
        - 401: 未登录
        - 404: 代理不存在或无权限删除

    示例：
        DELETE /api/v1/proxies/1

        Response: 204 No Content

    TODO (优先级 P1):
        - [ ] 检查代理是否正在被任务使用（如果使用中，提示用户）
        - [ ] 软删除（标记为 deleted，而不是物理删除）
        - [ ] 添加删除历史记录
    """
    success = await ProxyService.delete_proxy(
        db=db,
        proxy_id=proxy_id,
        user_id=current_user.id
    )

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="代理不存在或无权限删除"
        )

    return None


# ========================================
# 测试代理
# ========================================

@router.post("/{proxy_id}/test", response_model=dict, status_code=status.HTTP_200_OK)
async def test_proxy(
    proxy_id: int,
    test_url: str = Query("https://www.apple.com", description="测试 URL"),
    timeout: int = Query(10, ge=1, le=60, description="超时时间（秒）"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    测试代理可用性

    业务逻辑：
        1. 验证用户身份（需要登录）
        2. 查询代理是否存在
        3. 验证权限（只能测试自己的代理或公共代理）
        4. 发送测试请求（通过代理访问指定 URL）
        5. 记录测试结果（响应时间、成功/失败状态）
        6. 更新代理统计信息（成功次数、失败次数、平均响应时间）
        7. 返回测试结果

    权限要求：
        - 需要登录用户
        - 只能测试自己的私有代理或公共代理

    路径参数：
        - proxy_id: 代理 ID

    查询参数：
        - test_url: 测试 URL（默认 https://www.apple.com）
        - timeout: 超时时间（默认10秒，最大60秒）

    返回结果：
        - 200: 测试完成，返回测试结果
        - 401: 未登录
        - 404: 代理不存在或无权限测试

    示例：
        POST /api/v1/proxies/1/test?test_url=https://www.apple.com&timeout=10

        Response (成功):
        {
            "success": true,
            "response_time": 234,
            "status": "active",
            "error_message": null,
            "message": "代理测试成功，响应时间：234ms"
        }

        Response (失败):
        {
            "success": false,
            "response_time": null,
            "status": "failed",
            "error_message": "Connection timeout",
            "message": "代理测试失败：Connection timeout"
        }

    TODO (优先级 P1):
        - [ ] 支持批量测试代理
        - [ ] 添加测试历史记录
        - [ ] 支持自定义测试规则（如检查响应内容、HTTP 状态码）
        - [ ] 添加 IP 地址检测（返回代理的出口 IP）
        - [ ] 支持地理位置检测（返回代理的国家/城市）
    """
    # 验证权限：检查代理是否属于当前用户
    proxy = await ProxyService.get_proxy(
        db=db,
        proxy_id=proxy_id,
        user_id=current_user.id
    )

    if not proxy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="代理不存在或无权限测试"
        )

    try:
        # 测试代理
        test_result = await ProxyService.test_proxy(
            db=db,
            proxy_id=proxy_id,
            test_url=test_url,
            timeout=timeout
        )

        # 构建响应
        return {
            "success": test_result.success,
            "response_time": test_result.response_time,
            "status": test_result.status,
            "error_message": test_result.error_message,
            "message": (
                f"代理测试成功，响应时间：{test_result.response_time}ms"
                if test_result.success
                else f"代理测试失败：{test_result.error_message}"
            )
        }

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"测试代理失败: {str(e)}"
        )


# ========================================
# 导出
# ========================================

__all__ = ["router"]
