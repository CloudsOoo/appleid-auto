"""
分享页管理 API 端点模块

本模块提供分享页的创建和管理功能，包括：
- CRUD 操作：创建、查询、更新、删除分享页
- 访问控制：密码保护、访问次数限制、域名白名单
- 自定义 HTML：支持自定义页头、页身、页脚
- 访问日志：记录和查询访问日志
- 统计信息：访问量、独立访客、地理分布等
- 公开访问：通过 slug 公开访问分享页

调用关系：
前端/客户端 → share_pages.py (本模块) → SharePageService → 数据库

业务流程：
1. 用户创建分享页 → 检查配额 → 过滤 HTML → 关联账号 → 生成分享链接
2. 访客访问分享页 → 验证密码 → 检查限制 → 记录日志 → 返回账号信息
3. 用户查看日志 → 过滤条件 → 分页返回访问记录

使用方式：
    from app.api.v1.endpoints.share_pages import router as share_pages_router

    app.include_router(share_pages_router, prefix="/api/v1", tags=["分享页管理"])
"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Request, Query
from fastapi.responses import HTMLResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.api.dependencies import (
    get_current_active_user,
    get_current_user_optional,
)
from app.models.user import User
from app.services.share_page_service import SharePageService
from app.schemas.share_page import (
    SharePageCreate,
    SharePageUpdate,
    SharePageResponse,
    SharePageAccess,
    SharePagePublicResponse,
    SharePageLogResponse,
    SharePageStatsResponse,
)


# ========== 创建路由 ==========
router = APIRouter()


# ========================================
# 分享页 CRUD 操作
# ========================================

@router.post("", response_model=SharePageResponse, status_code=status.HTTP_201_CREATED)
async def create_share_page(
    data: SharePageCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> SharePageResponse:
    """
    创建分享页

    业务逻辑：
        1. 验证用户身份和权限
        2. 检查分享页配额（max_share_pages）
        3. 验证 slug 唯一性（全局唯一）
        4. 验证账号归属（只能关联自己的账号）
        5. 如果包含自定义 HTML，检查权限（allow_custom_html）
        6. 过滤和清理自定义 HTML（防止 XSS）
        7. 创建分享页记录
        8. 生成分享 URL
        9. 返回分享页信息

    请求示例：
        POST /api/v1/share-pages
        {
            "title": "美区账号分享",
            "slug": "us-accounts",
            "description": "优质美区账号",
            "password": "pass123",
            "access_limit": 100,
            "display_mode": "random",
            "account_ids": [1, 2, 3, 4, 5],
            "custom_html_header": "<style>.custom { color: red; }</style>",
            "custom_html_body": "<div class=\"banner\">欢迎使用</div>",
            "custom_html_footer": "<footer>© 2025</footer>",
            "is_active": true
        }

    响应示例：
        {
            "id": 1,
            "title": "美区账号分享",
            "slug": "us-accounts",
            "share_url": "https://example.com/public/share/us-accounts",
            "has_password": true,
            "access_limit": 100,
            "access_count": 0,
            "display_mode": "random",
            "account_count": 5,
            "is_active": true,
            "total_views": 0,
            "unique_views": 0,
            "created_at": "2025-11-20T12:00:00"
        }

    错误处理：
        - 400: slug 已存在、账号不属于当前用户
        - 403: 配额不足、无自定义 HTML 权限
        - 500: 数据库错误

    TODO:
        - 添加分享页模板选择（预设多种模板）
        - 支持自定义 CSS（独立的样式文件）
        - 支持自定义 JavaScript（受限的脚本功能）
        - 添加分享页预览功能（创建前预览效果）
        - 支持二维码生成（方便分享）
    """
    try:
        # 调用服务层创建分享页
        share_page = await SharePageService.create_share_page(
            db=db,
            user_id=current_user.id,
            data=data
        )

        return SharePageResponse.model_validate(share_page)

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except PermissionError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"创建分享页失败: {str(e)}"
        )


@router.get("", response_model=dict, status_code=status.HTTP_200_OK)
async def get_share_page_list(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    is_active: Optional[bool] = Query(None),
    search: Optional[str] = Query(None),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> dict:
    """
    获取分享页列表

    业务逻辑：
        1. 验证用户身份
        2. 构建查询条件：
           - 激活状态过滤：true/false
           - 搜索过滤：标题、slug、描述模糊匹配
        3. 只查询当前用户的分享页
        4. 按创建时间倒序排序
        5. 分页查询
        6. 返回分享页列表和分页信息

    请求示例：
        GET /api/v1/share-pages?page=1&per_page=20&is_active=true&search=美区

    响应示例：
        {
            "items": [
                {
                    "id": 1,
                    "title": "美区账号分享",
                    "slug": "us-accounts",
                    "share_url": "https://example.com/public/share/us-accounts",
                    "has_password": true,
                    "access_count": 50,
                    "access_limit": 100,
                    "account_count": 5,
                    "is_active": true,
                    "total_views": 120,
                    "unique_views": 80,
                    "created_at": "2025-11-20T12:00:00"
                },
                ...
            ],
            "total": 10,
            "page": 1,
            "per_page": 20,
            "total_pages": 1
        }

    错误处理：
        - 500: 数据库错误

    TODO:
        - 支持按访问量排序
        - 支持按创建时间排序
        - 添加快速过滤（如：即将到期、访问量大的）
        - 支持批量操作（批量启用/禁用）
    """
    try:
        # 调用服务层获取列表
        share_pages, total = await SharePageService.get_share_page_list(
            db=db,
            user_id=current_user.id,
            page=page,
            per_page=per_page,
            is_active=is_active,
            search=search
        )

        # 转换为响应格式
        items = []
        for page_item in share_pages:
            item = SharePageResponse.model_validate(page_item)
            items.append(item.model_dump())

        return {
            "items": items,
            "total": total,
            "page": page,
            "per_page": per_page,
            "total_pages": (total + per_page - 1) // per_page
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取列表失败: {str(e)}"
        )


@router.get("/{page_id}", response_model=SharePageResponse, status_code=status.HTTP_200_OK)
async def get_share_page_detail(
    page_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> SharePageResponse:
    """
    获取分享页详情

    业务逻辑：
        1. 验证用户身份
        2. 验证分享页归属（只能查看自己的分享页）
        3. 从数据库查询分享页
        4. 返回完整分享页信息：
           - 基本信息（标题、slug、描述）
           - 访问控制（密码、限制、到期时间）
           - 显示配置（模式、模板）
           - 关联账号（账号 ID 列表）
           - 自定义 HTML（页头、页身、页脚）
           - 统计信息（访问量、独立访客）

    请求示例：
        GET /api/v1/share-pages/123

    响应示例：
        {
            "id": 123,
            "title": "美区账号分享",
            "slug": "us-accounts",
            "description": "优质美区账号",
            "share_url": "https://example.com/public/share/us-accounts",
            "has_password": true,
            "access_limit": 100,
            "access_count": 50,
            "expires_at": "2025-12-20T12:00:00",
            "display_mode": "random",
            "template": "default",
            "account_ids": [1, 2, 3, 4, 5],
            "account_count": 5,
            "custom_html_header": "<style>.custom { color: red; }</style>",
            "custom_html_body": "<div class=\"banner\">欢迎使用</div>",
            "custom_html_footer": "<footer>© 2025</footer>",
            "is_active": true,
            "total_views": 120,
            "unique_views": 80,
            "created_at": "2025-11-20T12:00:00",
            "updated_at": "2025-11-20T12:00:00"
        }

    错误处理：
        - 404: 分享页不存在或无权访问
        - 500: 数据库错误

    TODO:
        - 添加分享页二维码生成（嵌入响应）
        - 添加分享页性能统计（平均访问时长）
    """
    try:
        # 调用服务层获取分享页详情
        share_page = await SharePageService.get_share_page(
            db=db,
            page_id=page_id,
            user_id=current_user.id
        )

        if not share_page:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="分享页不存在"
            )

        return SharePageResponse.model_validate(share_page)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取分享页详情失败: {str(e)}"
        )


@router.put("/{page_id}", response_model=SharePageResponse, status_code=status.HTTP_200_OK)
async def update_share_page(
    page_id: int,
    data: SharePageUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> SharePageResponse:
    """
    更新分享页

    业务逻辑：
        1. 验证用户身份
        2. 验证分享页归属（只能修改自己的分享页）
        3. 如果修改账号列表，验证账号归属
        4. 如果修改自定义 HTML，检查权限并过滤
        5. 更新分享页信息
        6. 返回更新后的分享页信息

    请求示例：
        PUT /api/v1/share-pages/123
        {
            "title": "美区账号分享（更新）",
            "description": "更新后的描述",
            "access_limit": 200,
            "is_active": false
        }

    响应示例：
        {
            "id": 123,
            "title": "美区账号分享（更新）",
            "slug": "us-accounts",
            "description": "更新后的描述",
            "access_limit": 200,
            "is_active": false,
            "updated_at": "2025-11-20T13:00:00"
        }

    错误处理：
        - 400: 账号不属于当前用户
        - 403: 无自定义 HTML 权限
        - 404: 分享页不存在
        - 500: 数据库错误

    TODO:
        - 添加修改审计日志（记录哪些字段被修改了）
        - 支持版本历史（保存修改历史）
        - 修改时发送通知（如果分享页被频繁访问）
    """
    try:
        # 调用服务层更新分享页
        share_page = await SharePageService.update_share_page(
            db=db,
            page_id=page_id,
            user_id=current_user.id,
            data=data
        )

        if not share_page:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="分享页不存在"
            )

        return SharePageResponse.model_validate(share_page)

    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except PermissionError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"更新分享页失败: {str(e)}"
        )


@router.delete("/{page_id}", response_model=dict, status_code=status.HTTP_200_OK)
async def delete_share_page(
    page_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> dict:
    """
    删除分享页

    业务逻辑：
        1. 验证用户身份
        2. 验证分享页归属（只能删除自己的分享页）
        3. 验证分享页存在
        4. 删除关联的访问日志
        5. 删除分享页
        6. 更新用户权限的分享页计数
        7. 返回成功消息

    注意：
        - 删除操作是物理删除，不可恢复
        - 会同时删除所有访问日志

    请求示例：
        DELETE /api/v1/share-pages/123

    响应示例：
        {
            "page_id": 123,
            "title": "美区账号分享",
            "slug": "us-accounts",
            "message": "分享页已删除"
        }

    错误处理：
        - 404: 分享页不存在
        - 500: 数据库错误

    TODO:
        - 改为软删除（标记为已删除，保留数据）
        - 删除前检查访问量（如果访问量大，提示用户）
        - 添加删除确认机制
        - 删除时发送通知
    """
    try:
        # 调用服务层删除分享页
        success, page_info = await SharePageService.delete_share_page(
            db=db,
            page_id=page_id,
            user_id=current_user.id
        )

        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="分享页不存在"
            )

        return {
            "page_id": page_id,
            "title": page_info.get("title"),
            "slug": page_info.get("slug"),
            "message": "分享页已删除"
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"删除分享页失败: {str(e)}"
        )


# ========================================
# 访问日志和统计
# ========================================

@router.get("/{page_id}/logs", response_model=dict, status_code=status.HTTP_200_OK)
async def get_access_logs(
    page_id: int,
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> dict:
    """
    获取分享页访问日志

    业务逻辑：
        1. 验证用户身份
        2. 验证分享页归属（只能查看自己分享页的日志）
        3. 查询访问日志：
           - IP 地址
           - 地理位置（国家、地区、城市）
           - 展示的账号信息
           - 访问是否成功（密码验证）
           - User-Agent、Referer
           - 访问时间
        4. 按时间倒序排序
        5. 分页查询
        6. 返回日志列表和分页信息

    请求示例：
        GET /api/v1/share-pages/123/logs?page=1&per_page=20

    响应示例：
        {
            "items": [
                {
                    "id": 1,
                    "ip_address": "1.2.3.4",
                    "country": "CN",
                    "region": "Beijing",
                    "city": "Beijing",
                    "shown_account_id": 5,
                    "shown_apple_id": "example@icloud.com",
                    "access_granted": true,
                    "password_attempt": true,
                    "user_agent": "Mozilla/5.0...",
                    "referer": "https://google.com",
                    "created_at": "2025-11-20T12:00:00"
                },
                ...
            ],
            "total": 100,
            "page": 1,
            "per_page": 20,
            "total_pages": 5
        }

    错误处理：
        - 404: 分享页不存在
        - 500: 数据库错误

    TODO:
        - 支持按时间范围过滤
        - 支持按国家/地区过滤
        - 支持按访问结果过滤（成功/失败）
        - 添加导出功能（导出为 CSV）
        - 添加实时日志（WebSocket）
    """
    try:
        # 验证分享页归属
        share_page = await SharePageService.get_share_page(
            db=db,
            page_id=page_id,
            user_id=current_user.id
        )

        if not share_page:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="分享页不存在"
            )

        # 调用服务层获取访问日志
        logs, total = await SharePageService.get_access_logs(
            db=db,
            page_id=page_id,
            page=page,
            per_page=per_page
        )

        # 转换为响应格式
        items = []
        for log in logs:
            item = SharePageLogResponse.model_validate(log)
            items.append(item.model_dump())

        return {
            "items": items,
            "total": total,
            "page": page,
            "per_page": per_page,
            "total_pages": (total + per_page - 1) // per_page
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取访问日志失败: {str(e)}"
        )


@router.get("/{page_id}/stats", response_model=SharePageStatsResponse, status_code=status.HTTP_200_OK)
async def get_share_page_stats(
    page_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> SharePageStatsResponse:
    """
    获取分享页统计信息

    业务逻辑：
        1. 验证用户身份
        2. 验证分享页归属
        3. 统计信息：
           - 总访问量（total_views）
           - 独立访客数（unique_views，基于 IP）
           - 已使用次数（access_count）
           - 剩余次数（remaining_access = access_limit - access_count）
           - Top 国家分布（top_countries）
           - Top 来源（top_referers）
           - 最近访问记录（recent_visits）
        4. 返回统计信息

    请求示例：
        GET /api/v1/share-pages/123/stats

    响应示例：
        {
            "total_views": 120,
            "unique_views": 80,
            "access_count": 50,
            "access_limit": 100,
            "remaining_access": 50,
            "top_countries": [
                {"country": "CN", "count": 60},
                {"country": "US", "count": 30},
                {"country": "JP", "count": 10}
            ],
            "top_referers": [
                {"referer": "https://google.com", "count": 40},
                {"referer": "https://twitter.com", "count": 20}
            ],
            "recent_visits": [
                {
                    "id": 100,
                    "ip_address": "1.2.3.4",
                    "country": "CN",
                    "access_granted": true,
                    "created_at": "2025-11-20T12:00:00"
                },
                ...
            ]
        }

    错误处理：
        - 404: 分享页不存在
        - 500: 数据库错误

    TODO:
        - 添加时间趋势统计（按天/周/月）
        - 添加访问高峰时段分析
        - 添加转化率统计（访问成功率）
        - 支持导出统计报表
        - 添加设备类型统计（桌面/移动）
    """
    try:
        # 验证分享页归属
        share_page = await SharePageService.get_share_page(
            db=db,
            page_id=page_id,
            user_id=current_user.id
        )

        if not share_page:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="分享页不存在"
            )

        # 调用服务层获取统计信息
        stats = await SharePageService.get_statistics(
            db=db,
            page_id=page_id
        )

        return SharePageStatsResponse(**stats)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取统计信息失败: {str(e)}"
        )


# ========================================
# 公开访问（无需认证）
# ========================================

@router.get("/public/share/{slug}", response_model=None, status_code=status.HTTP_200_OK)
async def access_share_page(
    slug: str,
    password: Optional[str] = Query(None),
    request: Request = None,
    db: AsyncSession = Depends(get_db)
):
    """
    访问分享页（公开接口，无需认证）

    业务逻辑：
        1. 根据 slug 查询分享页
        2. 验证分享页是否激活
        3. 验证是否过期
        4. 验证访问次数限制
        5. 如果需要密码，验证密码
        6. 验证域名白名单（如果设置）
        7. 根据显示模式获取账号：
           - random: 随机返回一个账号
           - sequential: 按顺序返回下一个账号
           - all: 返回所有账号
        8. 记录访问日志（IP、地理位置、User-Agent、Referer）
        9. 增加访问计数
        10. 返回分享页内容和账号信息

    请求示例：
        GET /api/v1/share-pages/public/share/us-accounts?password=pass123

    响应示例（HTML 或 JSON）：
        {
            "title": "美区账号分享",
            "description": "优质美区账号",
            "account": {
                "apple_id": "example@icloud.com",
                "password": "password123"
            },
            "custom_html": {
                "header": "<style>.custom { color: red; }</style>",
                "body": "<div class=\"banner\">欢迎使用</div>",
                "footer": "<footer>© 2025</footer>"
            },
            "template": "default"
        }

    错误处理：
        - 404: 分享页不存在
        - 403: 密码错误、访问受限
        - 410: 分享页已过期或达到访问限制
        - 500: 数据库错误

    TODO:
        - 实现 HTML 模板渲染（返回 HTML 页面）
        - 添加防刷机制（同一 IP 限制访问频率）
        - 支持验证码（防止机器人）
        - 添加访问统计实时更新
        - 支持自定义域名绑定
    """
    try:
        # 获取客户端信息
        client_ip = request.client.host if request and request.client else None
        user_agent = request.headers.get("user-agent") if request else None
        referer = request.headers.get("referer") if request else None

        # 根据 slug 查询分享页
        share_page = await SharePageService.get_share_page_by_slug(db=db, slug=slug)

        if not share_page:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="分享页不存在"
            )

        # 验证访问权限
        access_data = SharePageAccess(password=password)
        is_granted, error_msg = await SharePageService.verify_access(
            db=db,
            share_page=share_page,
            password=access_data.password,
            client_ip=client_ip
        )

        if not is_granted:
            # 记录失败的访问日志
            await SharePageService.log_access(
                db=db,
                page_id=share_page.id,
                ip_address=client_ip,
                access_granted=False,
                password_attempt=bool(password),
                user_agent=user_agent,
                referer=referer
            )

            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=error_msg
            )

        # 获取要显示的账号
        accounts = await SharePageService.get_display_accounts(
            db=db,
            share_page=share_page
        )

        # 记录成功的访问日志
        shown_account_id = accounts[0]["id"] if accounts else None
        await SharePageService.log_access(
            db=db,
            page_id=share_page.id,
            ip_address=client_ip,
            shown_account_id=shown_account_id,
            access_granted=True,
            password_attempt=bool(password),
            user_agent=user_agent,
            referer=referer
        )

        # 构建响应
        custom_html = None
        if share_page.custom_html_header or share_page.custom_html_body or share_page.custom_html_footer:
            custom_html = {
                "header": share_page.custom_html_header,
                "body": share_page.custom_html_body,
                "footer": share_page.custom_html_footer
            }

        response_data = {
            "title": share_page.title,
            "description": share_page.description,
            "custom_html": custom_html,
            "template": share_page.template
        }

        # 根据显示模式返回账号信息
        if share_page.display_mode == "all":
            response_data["accounts"] = accounts
        else:
            response_data["account"] = accounts[0] if accounts else None

        # TODO: 根据模板渲染 HTML
        # if share_page.template != "json":
        #     return HTMLResponse(content=render_template(share_page.template, response_data))

        return SharePagePublicResponse(**response_data)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"访问分享页失败: {str(e)}"
        )


# ========== 导出路由 ==========
__all__ = ["router"]
