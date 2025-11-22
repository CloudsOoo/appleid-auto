"""
Apple ID 账号管理 API 端点模块

本模块提供 Apple ID 账号的完整管理功能，包括：
- CRUD 操作：创建、查询、更新、删除账号
- 批量操作：批量导入、批量导出
- 历史记录：密码修改历史
- 手动操作：手动触发账号状态检测

调用关系：
前端/客户端 → accounts.py (本模块) → AppleAccountService → 数据库

业务流程：
1. 用户添加 Apple ID → 检查配额 → 加密存储密码 → 创建密码历史
2. 用户批量导入 → 解析文件 → 逐个验证并创建 → 返回成功/失败统计
3. 用户查询账号 → 应用过滤条件 → 分页返回
4. 用户手动检测 → 触发后台任务 → 更新账号状态

使用方式：
    from app.api.v1.endpoints.accounts import router as accounts_router

    app.include_router(accounts_router, prefix="/api/v1", tags=["Apple ID 管理"])
"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
import io
import csv

from app.db.database import get_db
from app.api.dependencies import (
    get_current_active_user,
)
from app.models.user import User
from app.services.apple_account_service import AppleAccountService
from app.schemas.account import (
    AppleAccountCreate,
    AppleAccountUpdate,
    AppleAccountResponse,
    AppleAccountDetailResponse,
    AppleAccountImport,
    AppleAccountImportResponse,
    PasswordHistoryResponse,
    TriggerCheck,
)


# ========== 创建路由 ==========
router = APIRouter()


# ========================================
# 账号 CRUD 操作
# ========================================

@router.post("", response_model=AppleAccountResponse, status_code=status.HTTP_201_CREATED)
async def create_account(
    data: AppleAccountCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> AppleAccountResponse:
    """
    添加 Apple ID 账号

    业务逻辑：
        1. 验证用户权限是否过期
        2. 检查账号配额是否充足（max_accounts）
        3. 验证 Apple ID 是否已存在（同一用户不能重复添加）
        4. 加密存储密码和密保问题
        5. 创建账号记录
        6. 创建初始密码历史记录
        7. 计算下次检测时间（当前时间 + check_interval）
        8. 更新用户权限的账号计数
        9. 返回账号信息（不含密码）

    请求示例：
        POST /api/v1/accounts
        {
            "apple_id": "example@icloud.com",
            "password": "password123",
            "security_questions": [
                {
                    "question": "您最喜欢的颜色是什么?",
                    "answer": "蓝色"
                }
            ],
            "tags": ["工作", "美区"],
            "category": "工作账号",
            "auto_unlock": true,
            "check_interval": 3600
        }

    响应示例：
        {
            "id": 1,
            "apple_id": "example@icloud.com",
            "status": "normal",
            "lock_status": false,
            "two_factor_enabled": false,
            "tags": ["工作", "美区"],
            "auto_unlock": true,
            "check_interval": 3600,
            "next_check_at": "2025-11-20T13:00:00",
            "unlock_count": 0,
            "created_at": "2025-11-20T12:00:00"
        }

    错误处理：
        - 400: 配额不足、Apple ID 已存在
        - 403: 用户权限已过期
        - 500: 数据库错误

    TODO:
        - 添加 Apple ID 格式验证（邮箱域名白名单）
        - 支持创建时自动验证账号有效性
        - 添加创建成功后的通知
    """
    try:
        # 调用服务层创建账号
        account = await AppleAccountService.create_account(
            db=db,
            user_id=current_user.id,
            data=data
        )

        return AppleAccountResponse.model_validate(account)

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"创建账号失败: {str(e)}"
        )


@router.get("", response_model=dict, status_code=status.HTTP_200_OK)
async def get_account_list(
    page: int = 1,
    per_page: int = 20,
    status: Optional[str] = None,
    lock_status: Optional[bool] = None,
    tag: Optional[str] = None,
    category: Optional[str] = None,
    search: Optional[str] = None,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> dict:
    """
    获取 Apple ID 账号列表

    业务逻辑：
        1. 验证用户身份
        2. 构建查询条件：
           - 状态过滤：normal/locked/error/disabled
           - 锁定状态过滤：true/false
           - 标签过滤：包含指定标签
           - 分类过滤：指定分类
           - 搜索过滤：Apple ID、备注模糊匹配
        3. 只查询当前用户的账号
        4. 分页查询
        5. 返回账号列表和分页信息（不含密码）

    请求示例：
        GET /api/v1/accounts?page=1&per_page=20&status=normal&lock_status=false&tag=工作&search=icloud

    响应示例：
        {
            "items": [
                {
                    "id": 1,
                    "apple_id": "example@icloud.com",
                    "status": "normal",
                    "lock_status": false,
                    "two_factor_enabled": false,
                    "tags": ["工作", "美区"],
                    "auto_unlock": true,
                    "unlock_count": 5,
                    "last_checked_at": "2025-11-20T12:00:00",
                    "created_at": "2025-11-20T10:00:00"
                },
                ...
            ],
            "total": 50,
            "page": 1,
            "per_page": 20,
            "total_pages": 3
        }

    错误处理：
        - 500: 数据库错误

    TODO:
        - 支持按最后检测时间排序
        - 支持按解锁次数排序
        - 添加快速过滤（如：今天检测过的、有错误的）
        - 支持多标签过滤（OR 关系）
    """
    try:
        # 调用服务层获取列表
        accounts, total = await AppleAccountService.get_account_list(
            db=db,
            user_id=current_user.id,
            page=page,
            per_page=per_page,
            status=status,
            lock_status=lock_status,
            tag=tag,
            category=category,
            search=search
        )

        # 转换为响应格式
        items = []
        for account in accounts:
            item = AppleAccountResponse.model_validate(account)
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


@router.get("/{account_id}", response_model=AppleAccountDetailResponse, status_code=status.HTTP_200_OK)
async def get_account_detail(
    account_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> AppleAccountDetailResponse:
    """
    获取 Apple ID 账号详情（含密码）

    业务逻辑：
        1. 验证用户身份
        2. 验证账号归属（只能查看自己的账号）
        3. 从数据库查询账号
        4. 解密密码和密保问题
        5. 返回完整账号信息（含密码）

    请求示例：
        GET /api/v1/accounts/123

    响应示例：
        {
            "id": 123,
            "apple_id": "example@icloud.com",
            "current_password": "password123",
            "security_questions": [
                {
                    "question": "您最喜欢的颜色是什么?",
                    "answer": "蓝色"
                }
            ],
            "status": "normal",
            "lock_status": false,
            "two_factor_enabled": false,
            "devices_count": 3,
            "tags": ["工作", "美区"],
            "auto_unlock": true,
            "check_interval": 3600,
            "unlock_count": 5,
            "created_at": "2025-11-20T10:00:00"
        }

    错误处理：
        - 404: 账号不存在或无权访问
        - 500: 数据库错误

    TODO:
        - 添加密码查看审计日志（记录谁在什么时候查看了密码）
        - 支持权限控制（某些套餐可能不允许查看密码）
    """
    try:
        # 调用服务层获取账号详情（含密码）
        account = await AppleAccountService.get_account(
            db=db,
            account_id=account_id,
            user_id=current_user.id,
            include_password=True
        )

        if not account:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="账号不存在"
            )

        return AppleAccountDetailResponse.model_validate(account)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取账号详情失败: {str(e)}"
        )


@router.put("/{account_id}", response_model=AppleAccountResponse, status_code=status.HTTP_200_OK)
async def update_account(
    account_id: int,
    data: AppleAccountUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> AppleAccountResponse:
    """
    更新 Apple ID 账号

    业务逻辑：
        1. 验证用户身份
        2. 验证账号归属（只能修改自己的账号）
        3. 如果修改密码：
           - 加密新密码
           - 创建密码历史记录
        4. 如果修改密保问题：
           - 加密新密保
        5. 更新账号信息
        6. 如果修改了 check_interval，重新计算 next_check_at
        7. 返回更新后的账号信息（不含密码）

    请求示例：
        PUT /api/v1/accounts/123
        {
            "password": "new_password",
            "tags": ["工作", "美区", "已验证"],
            "auto_unlock": false,
            "check_interval": 7200
        }

    响应示例：
        {
            "id": 123,
            "apple_id": "example@icloud.com",
            "status": "normal",
            "tags": ["工作", "美区", "已验证"],
            "auto_unlock": false,
            "check_interval": 7200,
            "next_check_at": "2025-11-20T14:00:00",
            "updated_at": "2025-11-20T12:00:00"
        }

    错误处理：
        - 404: 账号不存在
        - 500: 数据库错误

    TODO:
        - 添加修改审计日志（记录哪些字段被修改了）
        - 密码修改时发送通知
        - 支持批量更新（如批量修改标签）
    """
    try:
        # 调用服务层更新账号
        account = await AppleAccountService.update_account(
            db=db,
            account_id=account_id,
            user_id=current_user.id,
            data=data
        )

        if not account:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="账号不存在"
            )

        return AppleAccountResponse.model_validate(account)

    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"更新账号失败: {str(e)}"
        )


@router.delete("/{account_id}", response_model=dict, status_code=status.HTTP_200_OK)
async def delete_account(
    account_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> dict:
    """
    删除 Apple ID 账号

    业务逻辑：
        1. 验证用户身份
        2. 验证账号归属（只能删除自己的账号）
        3. 验证账号存在
        4. 删除关联的密码历史记录
        5. 删除账号
        6. 更新用户权限的账号计数
        7. 返回成功消息

    注意：
        - 删除操作是物理删除，不可恢复
        - 如果有关联的任务在执行，建议先取消任务

    请求示例：
        DELETE /api/v1/accounts/123

    响应示例：
        {
            "account_id": 123,
            "apple_id": "example@icloud.com",
            "message": "账号已删除"
        }

    错误处理：
        - 404: 账号不存在
        - 500: 数据库错误

    TODO:
        - 改为软删除（标记为已删除，保留数据）
        - 删除前检查是否有进行中的任务
        - 添加删除确认机制（需要输入密码或验证码）
        - 删除时发送通知
    """
    try:
        # 调用服务层删除账号
        success, account_info = await AppleAccountService.delete_account(
            db=db,
            account_id=account_id,
            user_id=current_user.id
        )

        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="账号不存在"
            )

        return {
            "account_id": account_id,
            "apple_id": account_info.get("apple_id"),
            "message": "账号已删除"
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"删除账号失败: {str(e)}"
        )


# ========================================
# 批量操作
# ========================================

@router.post("/import", response_model=AppleAccountImportResponse, status_code=status.HTTP_200_OK)
async def import_accounts(
    data: AppleAccountImport,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> AppleAccountImportResponse:
    """
    批量导入 Apple ID 账号

    业务逻辑：
        1. 验证用户身份
        2. 检查用户是否有批量导入权限（allow_batch_import）
        3. 检查导入数量是否超过限制（max_import_per_time）
        4. 逐个验证和创建账号：
           - 验证必填字段（apple_id, password）
           - 检查账号是否已存在
           - 检查配额是否充足
           - 创建账号和密码历史
        5. 记录成功和失败的账号
        6. 返回导入结果统计

    请求示例：
        POST /api/v1/accounts/import
        {
            "accounts": [
                {
                    "apple_id": "example1@icloud.com",
                    "password": "password123",
                    "tags": ["工作", "美区"],
                    "note": "测试账号1"
                },
                {
                    "apple_id": "example2@icloud.com",
                    "password": "password456",
                    "tags": ["个人"],
                    "note": "测试账号2"
                }
            ]
        }

    响应示例：
        {
            "total": 2,
            "success": 2,
            "failed": 0,
            "errors": [],
            "message": "导入完成"
        }

    响应示例（部分失败）：
        {
            "total": 2,
            "success": 1,
            "failed": 1,
            "errors": [
                {
                    "apple_id": "example2@icloud.com",
                    "reason": "该 Apple ID 已存在"
                }
            ],
            "message": "导入完成"
        }

    错误处理：
        - 400: 导入数量超过限制
        - 403: 无批量导入权限
        - 500: 数据库错误

    TODO:
        - 支持 Excel 文件导入（.xlsx, .xls）
        - 支持 CSV 文件导入
        - 添加导入预览功能（先验证，不实际导入）
        - 支持导入模板下载
        - 导入完成后发送通知（邮件/站内信）
    """
    try:
        # 调用服务层批量导入
        result = await AppleAccountService.import_accounts(
            db=db,
            user_id=current_user.id,
            accounts_data=data.accounts
        )

        return AppleAccountImportResponse(**result)

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
            detail=f"批量导入失败: {str(e)}"
        )


@router.get("/export", response_model=None, status_code=status.HTTP_200_OK)
async def export_accounts(
    format: str = "csv",
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    批量导出 Apple ID 账号

    业务逻辑：
        1. 验证用户身份
        2. 查询用户所有账号
        3. 解密密码和密保问题
        4. 根据格式生成导出文件：
           - CSV: 包含所有字段的 CSV 文件
           - JSON: JSON 格式的账号数据
           - Excel: Excel 格式（TODO）
        5. 返回文件流供下载

    导出字段：
        - Apple ID
        - 密码
        - 状态
        - 锁定状态
        - 2FA 状态
        - 标签
        - 分类
        - 备注
        - 创建时间
        - 最后检测时间

    请求示例：
        GET /api/v1/accounts/export?format=csv

    响应：
        Content-Type: text/csv
        Content-Disposition: attachment; filename="accounts_20251120_120000.csv"

        CSV 文件内容（示例）：
        apple_id,password,status,lock_status,tags,category,note,created_at
        example1@icloud.com,password123,normal,false,"工作,美区",工作账号,测试账号1,2025-11-20 12:00:00
        example2@icloud.com,password456,normal,false,个人,个人账号,测试账号2,2025-11-20 11:00:00

    错误处理：
        - 500: 数据库错误、文件生成错误

    TODO:
        - 支持 Excel 格式导出
        - 支持选择性导出（只导出选中的账号）
        - 支持导出时过滤（如只导出正常状态的账号）
        - 添加导出审计日志
        - 支持导出密保问题
    """
    try:
        # 调用服务层导出账号
        accounts_data = await AppleAccountService.export_accounts(
            db=db,
            user_id=current_user.id
        )

        # 根据格式生成文件
        if format == "csv":
            # 生成 CSV 文件
            output = io.StringIO()
            writer = csv.DictWriter(
                output,
                fieldnames=[
                    "apple_id", "password", "status", "lock_status",
                    "tags", "category", "note", "created_at"
                ]
            )
            writer.writeheader()
            writer.writerows(accounts_data)

            # 转换为字节流
            csv_content = output.getvalue()
            output.close()

            # 生成文件名
            from datetime import datetime
            filename = f"accounts_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.csv"

            # 返回文件流
            return StreamingResponse(
                io.BytesIO(csv_content.encode("utf-8-sig")),  # 使用 utf-8-sig 支持 Excel 打开
                media_type="text/csv",
                headers={
                    "Content-Disposition": f"attachment; filename={filename}"
                }
            )

        elif format == "json":
            # 生成 JSON 文件
            import json
            json_content = json.dumps(accounts_data, ensure_ascii=False, indent=2)

            # 生成文件名
            from datetime import datetime
            filename = f"accounts_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"

            # 返回文件流
            return StreamingResponse(
                io.BytesIO(json_content.encode("utf-8")),
                media_type="application/json",
                headers={
                    "Content-Disposition": f"attachment; filename={filename}"
                }
            )

        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"不支持的导出格式: {format}"
            )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"导出账号失败: {str(e)}"
        )


# ========================================
# 密码历史
# ========================================

@router.get("/{account_id}/password-history", response_model=list[PasswordHistoryResponse], status_code=status.HTTP_200_OK)
async def get_password_history(
    account_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> list[PasswordHistoryResponse]:
    """
    获取账号密码历史记录

    业务逻辑：
        1. 验证用户身份
        2. 验证账号归属（只能查看自己账号的密码历史）
        3. 验证用户是否有查看密码历史权限（allow_view_password_history）
        4. 查询密码历史记录（按时间倒序）
        5. 返回密码历史列表

    请求示例：
        GET /api/v1/accounts/123/password-history

    响应示例：
        [
            {
                "id": 3,
                "password": "new_password",
                "changed_by": "manual",
                "created_at": "2025-11-20T12:00:00"
            },
            {
                "id": 2,
                "password": "old_password",
                "changed_by": "auto",
                "created_at": "2025-11-19T10:00:00"
            },
            {
                "id": 1,
                "password": "initial_password",
                "changed_by": "manual",
                "created_at": "2025-11-18T15:00:00"
            }
        ]

    错误处理：
        - 403: 无查看密码历史权限
        - 404: 账号不存在
        - 500: 数据库错误

    TODO:
        - 添加分页功能（历史记录可能很多）
        - 支持按时间范围过滤
        - 添加查看审计日志
        - 支持导出密码历史
    """
    try:
        # 调用服务层获取密码历史
        history = await AppleAccountService.get_password_history(
            db=db,
            account_id=account_id,
            user_id=current_user.id
        )

        if history is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="账号不存在"
            )

        return [PasswordHistoryResponse.model_validate(h) for h in history]

    except HTTPException:
        raise
    except PermissionError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取密码历史失败: {str(e)}"
        )


# ========================================
# 手动操作
# ========================================

@router.post("/{account_id}/check", response_model=dict, status_code=status.HTTP_200_OK)
async def trigger_check(
    account_id: int,
    data: TriggerCheck,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> dict:
    """
    手动触发账号状态检测

    业务逻辑：
        1. 验证用户身份
        2. 验证账号归属（只能检测自己的账号）
        3. 验证账号存在
        4. 如果 force=False，检查距离上次检测是否满足间隔要求
        5. 如果 force=True，忽略间隔限制
        6. 创建后台检测任务（通过 Celery）
        7. 更新 last_checked_at 和 next_check_at
        8. 返回任务 ID 和状态

    请求示例：
        POST /api/v1/accounts/123/check
        {
            "force": false
        }

    响应示例：
        {
            "account_id": 123,
            "apple_id": "example@icloud.com",
            "task_id": "abc123def456",
            "message": "检测任务已创建",
            "estimated_time": 30
        }

    错误处理：
        - 400: 检测间隔未满足
        - 404: 账号不存在
        - 500: 任务创建失败

    TODO:
        - 实现 Celery 任务调用（目前只是占位）
        - 添加任务状态查询接口
        - 支持批量触发检测
        - 添加检测优先级（紧急检测可以插队）
        - 检测完成后发送通知
    """
    try:
        # 验证账号存在和归属
        account = await AppleAccountService.get_account(
            db=db,
            account_id=account_id,
            user_id=current_user.id
        )

        if not account:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="账号不存在"
            )

        # 检查检测间隔（非强制模式）
        if not data.force:
            from datetime import datetime
            if account.last_checked_at:
                elapsed = (datetime.utcnow() - account.last_checked_at).total_seconds()
                if elapsed < account.check_interval:
                    remaining = account.check_interval - elapsed
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"检测间隔未满足，还需等待 {int(remaining)} 秒"
                    )

        # TODO: 创建 Celery 检测任务
        # from app.tasks.account_tasks import check_account_status
        # task = check_account_status.delay(account_id)
        # task_id = task.id

        # 暂时返回模拟数据
        task_id = f"mock_task_{account_id}"

        # 更新检测时间
        from datetime import datetime, timedelta
        await AppleAccountService.update_account_status(
            db=db,
            account_id=account_id,
            last_checked_at=datetime.utcnow(),
            next_check_at=datetime.utcnow() + timedelta(seconds=account.check_interval)
        )

        return {
            "account_id": account_id,
            "apple_id": account.apple_id,
            "task_id": task_id,
            "message": "检测任务已创建",
            "estimated_time": 30  # 预计30秒完成
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"触发检测失败: {str(e)}"
        )


# ========== 导出路由 ==========
__all__ = ["router"]
