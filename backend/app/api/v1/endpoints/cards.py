"""
卡密管理 API 端点模块

本模块提供卡密的管理和激活功能，包括：
- 用户端：激活卡密、查询状态
- 管理端：生成卡密、列表查询、导出、作废、延期

调用关系：
前端/客户端 → cards.py (本模块) → CardService → 数据库

业务流程：
1. 用户激活卡密 → 应用套餐权限 → 获得功能使用权
2. 管理员生成卡密 → 批量创建 → 导出分发
3. 管理员管理卡密 → 作废/延期 → 灵活控制

使用方式：
    from app.api.v1.endpoints.cards import router as cards_router

    app.include_router(cards_router, prefix="/api/v1", tags=["卡密"])
"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.api.dependencies import (
    get_current_active_user,
    get_current_admin,
)
from app.models.user import User
from app.services.card_service import CardService
from app.schemas.card import (
    CardActivate,
    CardActivateResponse,
    CardStatusResponse,
    CardGenerate,
    CardGenerateResponse,
    CardResponse,
    CardRevoke,
    CardExtend,
)


# ========== 创建路由 ==========
router = APIRouter(
    prefix="/cards",
    tags=["卡密管理"],
)


# ========================================
# 用户端接口（需要登录）
# ========================================

@router.post("/activate", response_model=CardActivateResponse, status_code=status.HTTP_200_OK)
async def activate_card(
    data: CardActivate,
    request: Request,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> CardActivateResponse:
    """
    激活卡密

    业务逻辑：
        1. 验证卡密代码存在且未使用
        2. 检查卡密状态（unused/used/expired/revoked）
        3. 获取关联的套餐信息
        4. 计算到期时间（time类型）
        5. 更新卡密状态为已使用
        6. 创建或更新用户权限（应用套餐配置）
        7. 记录激活日志（IP、User-Agent）
        8. 返回激活结果和套餐信息

    请求示例：
        POST /api/v1/cards/activate
        {
            "card_code": "AAAA-BBBB-CCCC-DDDD"
        }

    响应示例：
        {
            "card_type": "time",
            "duration_days": 30,
            "usage_count": null,
            "package": {
                "id": 2,
                "name": "专业版",
                "max_accounts": 50,
                "max_share_pages": 10
            },
            "expires_at": "2025-12-20T12:00:00",
            "message": "激活成功"
        }

    错误处理：
        - 400: 卡密不存在、已使用、已过期、已作废
        - 404: 套餐不存在
        - 500: 数据库错误

    TODO:
        - 添加卡密激活限制（同一用户不能重复激活）
        - 支持卡密叠加（多个卡密可以叠加使用）
        - 发送激活成功通知（邮件/站内信）
    """
    try:
        # 获取客户端信息
        client_ip = request.client.host if request.client else None
        user_agent = request.headers.get("user-agent")

        # 调用服务层激活卡密
        result = await CardService.activate_card(
            db=db,
            user_id=current_user.id,
            card_code=data.card_code,
            ip_address=client_ip,
            user_agent=user_agent
        )

        return CardActivateResponse(**result)

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"激活卡密失败: {str(e)}"
        )


@router.get("/status", response_model=CardStatusResponse, status_code=status.HTTP_200_OK)
async def get_card_status(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> CardStatusResponse:
    """
    查询当前用户的卡密状态

    业务逻辑：
        1. 查询用户权限表
        2. 如果未激活，返回未激活状态
        3. 如果已激活，返回：
           - 卡密类型
           - 套餐名称
           - 激活时间
           - 到期时间
           - 剩余天数
           - 使用次数（usage类型）

    请求示例：
        GET /api/v1/cards/status

    响应示例（已激活）：
        {
            "is_activated": true,
            "card_type": "time",
            "package_name": "专业版",
            "activated_at": "2025-11-20T12:00:00",
            "expires_at": "2025-12-20T12:00:00",
            "days_remaining": 30,
            "usage_count": null,
            "used_count": null
        }

    响应示例（未激活）：
        {
            "is_activated": false,
            "card_type": null,
            "package_name": null,
            "activated_at": null,
            "expires_at": null,
            "days_remaining": null,
            "usage_count": null,
            "used_count": null
        }

    错误处理：
        - 500: 数据库错误

    TODO:
        - 添加权限过期提醒（剩余3天时提示续费）
        - 支持多卡密查询（用户可能激活过多个卡密）
    """
    try:
        result = await CardService.get_card_status(db=db, user_id=current_user.id)
        return CardStatusResponse(**result)

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"查询状态失败: {str(e)}"
        )


# ========================================
# 管理员接口（需要管理员权限）
# ========================================

@router.post("/admin/generate", response_model=CardGenerateResponse, status_code=status.HTTP_201_CREATED)
async def generate_cards(
    data: CardGenerate,
    admin_user: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
) -> CardGenerateResponse:
    """
    批量生成卡密（管理员专用）

    业务逻辑：
        1. 验证管理员权限
        2. 验证套餐 ID 存在
        3. 验证卡密类型和参数匹配：
           - time 类型必须指定 duration_days
           - usage 类型必须指定 usage_count
           - permanent 类型无需额外参数
        4. 生成批次 ID（如未提供）
        5. 批量生成唯一卡密代码
        6. 插入数据库
        7. 返回批次 ID 和卡密列表

    请求示例：
        POST /api/v1/cards/admin/generate
        {
            "card_type": "time",
            "package_id": 2,
            "duration_days": 30,
            "quantity": 10,
            "batch_id": "BATCH_2025_001",
            "note": "双十一活动"
        }

    响应示例：
        {
            "batch_id": "BATCH_2025_001",
            "quantity": 10,
            "cards": [
                "AAAA-BBBB-CCCC-DDDD",
                "EEEE-FFFF-GGGG-HHHH",
                ...
            ],
            "message": "生成成功"
        }

    错误处理：
        - 400: 参数错误（类型不匹配、套餐不存在）
        - 403: 无管理员权限
        - 500: 数据库错误

    TODO:
        - 支持自定义卡密格式（前缀、长度、分隔符）
        - 支持卡密防伪标识（二维码、水印）
        - 添加生成限制（防止滥用，如单次最多1000个）
        - 导出时自动生成 Excel 文件
    """
    try:
        # 调用服务层生成卡密
        cards = await CardService.generate_cards(
            db=db,
            admin_id=admin_user.id,
            card_type=data.card_type,
            package_id=data.package_id,
            quantity=data.quantity,
            duration_days=data.duration_days,
            usage_count=data.usage_count,
            batch_id=data.batch_id,
            note=data.note
        )

        # 构建响应
        batch_id = data.batch_id or f"BATCH_{cards[0].split('-')[0]}"

        return CardGenerateResponse(
            batch_id=batch_id,
            quantity=len(cards),
            cards=cards,
            message="生成成功"
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"生成卡密失败: {str(e)}"
        )


@router.get("/admin/list", response_model=dict, status_code=status.HTTP_200_OK)
async def get_card_list(
    page: int = 1,
    per_page: int = 20,
    status: Optional[str] = None,
    card_type: Optional[str] = None,
    batch_id: Optional[str] = None,
    search: Optional[str] = None,
    admin_user: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
) -> dict:
    """
    获取卡密列表（管理员专用）

    业务逻辑：
        1. 验证管理员权限
        2. 构建查询条件：
           - 状态过滤：unused/used/expired/revoked
           - 类型过滤：time/usage/permanent
           - 批次过滤：batch_id
           - 搜索过滤：卡密代码模糊匹配
        3. 分页查询
        4. 返回卡密列表和总数

    请求示例：
        GET /api/v1/cards/admin/list?page=1&per_page=20&status=unused&card_type=time&batch_id=BATCH_2025_001

    响应示例：
        {
            "items": [
                {
                    "id": 1,
                    "card_code": "AAAA-BBBB-CCCC-DDDD",
                    "card_type": "time",
                    "package_id": 2,
                    "package_name": "专业版",
                    "duration_days": 30,
                    "usage_count": null,
                    "status": "unused",
                    "activated_by": null,
                    "activated_at": null,
                    "expires_at": null,
                    "batch_id": "BATCH_2025_001",
                    "note": "双十一活动",
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
        - 403: 无管理员权限
        - 500: 数据库错误

    TODO:
        - 支持导出查询结果
        - 添加统计信息（各状态数量、各类型数量）
        - 支持按日期范围过滤
    """
    try:
        # 调用服务层获取列表
        cards, total = await CardService.get_card_list(
            db=db,
            page=page,
            per_page=per_page,
            status=status,
            card_type=card_type,
            batch_id=batch_id,
            search=search
        )

        # 转换为响应格式
        items = []
        for card in cards:
            item = CardResponse.model_validate(card)
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


@router.get("/admin/export", response_model=dict, status_code=status.HTTP_200_OK)
async def export_cards(
    batch_id: Optional[str] = None,
    status: str = "unused",
    admin_user: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
) -> dict:
    """
    导出卡密（管理员专用）

    业务逻辑：
        1. 验证管理员权限
        2. 根据批次 ID 和状态过滤卡密
        3. 导出卡密代码列表
        4. 返回卡密数组（前端可下载为 txt 或 Excel）

    请求示例：
        GET /api/v1/cards/admin/export?batch_id=BATCH_2025_001&status=unused

    响应示例：
        {
            "batch_id": "BATCH_2025_001",
            "status": "unused",
            "count": 100,
            "cards": [
                "AAAA-BBBB-CCCC-DDDD",
                "EEEE-FFFF-GGGG-HHHH",
                ...
            ]
        }

    错误处理：
        - 403: 无管理员权限
        - 500: 数据库错误

    TODO:
        - 支持导出为 Excel 文件（直接下载）
        - 支持导出为 CSV 文件
        - 导出时包含更多信息（套餐名称、有效期等）
        - 记录导出日志（谁在什么时候导出了哪些卡密）
    """
    try:
        # 调用服务层导出卡密
        cards = await CardService.export_cards(
            db=db,
            batch_id=batch_id,
            status=status
        )

        return {
            "batch_id": batch_id,
            "status": status,
            "count": len(cards),
            "cards": cards
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"导出卡密失败: {str(e)}"
        )


@router.post("/admin/{card_id}/revoke", response_model=dict, status_code=status.HTTP_200_OK)
async def revoke_card(
    card_id: int,
    data: CardRevoke,
    admin_user: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
) -> dict:
    """
    作废卡密（管理员专用）

    业务逻辑：
        1. 验证管理员权限
        2. 验证卡密存在
        3. 将卡密状态改为 revoked
        4. 记录作废日志（原因、操作人）
        5. 返回成功消息

    注意：
        - 作废操作不会影响已激活的用户权限
        - 如需同时禁用用户，需要单独操作

    请求示例：
        POST /api/v1/cards/admin/123/revoke
        {
            "reason": "卡密泄露，需要作废"
        }

    响应示例：
        {
            "card_id": 123,
            "status": "revoked",
            "message": "卡密已作废"
        }

    错误处理：
        - 400: 卡密不存在
        - 403: 无管理员权限
        - 500: 数据库错误

    TODO:
        - 支持批量作废
        - 作废时同时禁用已激活该卡密的用户
        - 发送作废通知给相关用户
    """
    try:
        # 调用服务层作废卡密
        success = await CardService.revoke_card(
            db=db,
            card_id=card_id,
            admin_id=admin_user.id,
            reason=data.reason
        )

        if success:
            return {
                "card_id": card_id,
                "status": "revoked",
                "message": "卡密已作废"
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="作废卡密失败"
            )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"作废卡密失败: {str(e)}"
        )


@router.post("/admin/{card_id}/extend", response_model=dict, status_code=status.HTTP_200_OK)
async def extend_card(
    card_id: int,
    data: CardExtend,
    admin_user: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
) -> dict:
    """
    延期卡密（管理员专用）

    业务逻辑：
        1. 验证管理员权限
        2. 验证卡密存在且为 time 类型
        3. 验证卡密有到期时间
        4. 延长卡密到期时间（加上 extend_days）
        5. 如果卡密已激活，同时延长用户权限
        6. 记录延期日志（延长天数、原因、操作人）
        7. 返回成功消息和新的到期时间

    注意：
        - 只能延期 time 类型的卡密
        - usage 和 permanent 类型不支持延期

    请求示例：
        POST /api/v1/cards/admin/123/extend
        {
            "extend_days": 30,
            "reason": "用户反馈服务问题，补偿延期"
        }

    响应示例：
        {
            "card_id": 123,
            "extend_days": 30,
            "new_expires_at": "2026-01-20T12:00:00",
            "message": "延期成功"
        }

    错误处理：
        - 400: 卡密不存在、非time类型、无到期时间
        - 403: 无管理员权限
        - 500: 数据库错误

    TODO:
        - 支持批量延期
        - 延期时发送通知给用户
        - 支持缩短有效期（负数延期）
    """
    try:
        # 调用服务层延期卡密
        success = await CardService.extend_card(
            db=db,
            card_id=card_id,
            admin_id=admin_user.id,
            extend_days=data.extend_days,
            reason=data.reason
        )

        if success:
            # 获取更新后的卡密信息
            from app.models.card import Card
            from sqlalchemy import select

            result = await db.execute(select(Card).where(Card.id == card_id))
            card = result.scalar_one_or_none()

            return {
                "card_id": card_id,
                "extend_days": data.extend_days,
                "new_expires_at": card.expires_at.isoformat() if card and card.expires_at else None,
                "message": "延期成功"
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="延期卡密失败"
            )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"延期卡密失败: {str(e)}"
        )


# ========== 导出路由 ==========
__all__ = ["router"]
