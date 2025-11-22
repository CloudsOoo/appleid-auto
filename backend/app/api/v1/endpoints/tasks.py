"""
任务管理 API 端点模块

本模块提供任务的创建和管理功能，包括：
- 创建任务：创建解锁任务、关闭2FA任务、修改密码任务等
- 查询任务：列表查询、详情查询、统计信息
- 管理任务：取消任务

调用关系：
前端/客户端 → tasks.py (本模块) → TaskService → Celery 任务队列 → 数据库

业务流程：
1. 用户创建任务 → 验证权限 → 创建任务记录 → 调度到 Celery
2. 用户查询任务 → 应用过滤条件 → 分页返回
3. 用户取消任务 → 验证任务归属 → 取消 Celery 任务 → 更新状态

使用方式：
    from app.api.v1.endpoints.tasks import router as tasks_router

    app.include_router(tasks_router, prefix="/api/v1", tags=["任务管理"])
"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.api.dependencies import (
    get_current_active_user,
)
from app.models.user import User
from app.services.task_service import TaskService
from app.schemas.task import (
    UnlockTaskCreate,
    UnlockTaskResponse,
    TaskStatsResponse,
)


# ========== 创建路由 ==========
router = APIRouter(tags=["任务管理"])


# ========================================
# 任务 CRUD 操作
# ========================================

@router.post("/unlock", response_model=dict, status_code=status.HTTP_201_CREATED)
async def create_unlock_tasks(
    data: UnlockTaskCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> dict:
    """
    创建解锁任务

    业务逻辑：
        1. 验证用户身份和权限
        2. 验证账号归属（只能为自己的账号创建任务）
        3. 检查每日解锁次数配额（max_unlock_per_day）
        4. 验证任务类型：
           - unlock: 解锁账号
           - disable_2fa: 关闭两步验证
           - change_password: 修改密码
           - remove_devices: 删除设备
           - check_status: 检查状态
        5. 为每个账号创建一个任务记录
        6. 调度任务到 Celery 队列（TODO）
        7. 返回创建的任务列表

    请求示例：
        POST /api/v1/tasks/unlock
        {
            "account_ids": [1, 2, 3],
            "task_type": "unlock",
            "priority": 1
        }

    响应示例：
        {
            "total": 3,
            "tasks": [
                {
                    "id": 1,
                    "task_id": "abc123",
                    "account_id": 1,
                    "apple_id": "example1@icloud.com",
                    "task_type": "unlock",
                    "status": "pending",
                    "priority": 1,
                    "created_at": "2025-11-20T12:00:00"
                },
                ...
            ],
            "message": "任务创建成功"
        }

    错误处理：
        - 400: 账号不存在、配额不足
        - 403: 账号不属于当前用户
        - 500: 数据库错误、任务调度失败

    TODO:
        - 实现 Celery 任务调度（目前只创建数据库记录）
        - 添加任务批量取消功能
        - 支持定时任务（指定开始时间）
        - 添加任务依赖关系（某任务完成后才执行下一任务）
    """
    try:
        # 调用服务层创建任务
        tasks = await TaskService.create_tasks(
            db=db,
            user_id=current_user.id,
            account_ids=data.account_ids,
            task_type=data.task_type,
            priority=data.priority
        )

        # 转换为响应格式
        task_responses = []
        for task in tasks:
            task_response = UnlockTaskResponse.model_validate(task)
            task_responses.append(task_response.model_dump())

        return {
            "total": len(tasks),
            "tasks": task_responses,
            "message": "任务创建成功"
        }

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
            detail=f"创建任务失败: {str(e)}"
        )


@router.get("", response_model=dict, status_code=status.HTTP_200_OK)
async def get_task_list(
    page: int = 1,
    per_page: int = 20,
    status: Optional[str] = None,
    task_type: Optional[str] = None,
    account_id: Optional[int] = None,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> dict:
    """
    获取任务列表

    业务逻辑：
        1. 验证用户身份
        2. 构建查询条件：
           - 状态过滤：pending/processing/success/failed/cancelled
           - 类型过滤：unlock/disable_2fa/change_password/remove_devices/check_status
           - 账号过滤：指定账号 ID
        3. 只查询当前用户的任务
        4. 按创建时间倒序排序
        5. 分页查询
        6. 返回任务列表和分页信息

    请求示例：
        GET /api/v1/tasks?page=1&per_page=20&status=pending&task_type=unlock

    响应示例：
        {
            "items": [
                {
                    "id": 1,
                    "task_id": "abc123",
                    "account_id": 1,
                    "apple_id": "example@icloud.com",
                    "task_type": "unlock",
                    "status": "pending",
                    "priority": 1,
                    "retry_count": 0,
                    "max_retries": 3,
                    "created_at": "2025-11-20T12:00:00"
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
        - 支持按时间范围过滤（创建时间、完成时间）
        - 支持按执行节点过滤
        - 添加快速过滤（如：今天的任务、失败的任务）
        - 支持按优先级排序
        - 支持批量操作（批量取消、批量重试）
    """
    try:
        # 调用服务层获取列表
        tasks, total = await TaskService.get_task_list(
            db=db,
            user_id=current_user.id,
            page=page,
            per_page=per_page,
            status=status,
            task_type=task_type,
            account_id=account_id
        )

        # 转换为响应格式
        items = []
        for task in tasks:
            item = UnlockTaskResponse.model_validate(task)
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


@router.get("/{task_id}", response_model=UnlockTaskResponse, status_code=status.HTTP_200_OK)
async def get_task_detail(
    task_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> UnlockTaskResponse:
    """
    获取任务详情

    业务逻辑：
        1. 验证用户身份
        2. 验证任务归属（只能查看自己的任务）
        3. 从数据库查询任务
        4. 返回完整任务信息：
           - 基本信息（ID、类型、状态、优先级）
           - 关联信息（账号、节点、代理）
           - 执行信息（开始时间、完成时间、重试次数）
           - 结果信息（执行结果、错误信息）

    请求示例：
        GET /api/v1/tasks/123

    响应示例：
        {
            "id": 123,
            "task_id": "abc123def456",
            "account_id": 1,
            "apple_id": "example@icloud.com",
            "task_type": "unlock",
            "status": "success",
            "priority": 1,
            "node_id": 1,
            "node_name": "Node-001",
            "proxy_id": 5,
            "result": {
                "unlock_success": true,
                "unlock_method": "iforgot",
                "duration": 45.2
            },
            "error_message": null,
            "retry_count": 0,
            "max_retries": 3,
            "started_at": "2025-11-20T12:00:00",
            "completed_at": "2025-11-20T12:00:45",
            "created_at": "2025-11-20T11:59:00"
        }

    错误处理：
        - 404: 任务不存在或无权访问
        - 500: 数据库错误

    TODO:
        - 添加执行日志查询（详细的步骤日志）
        - 支持任务详情导出（PDF/JSON）
        - 添加任务耗时统计（各阶段耗时）
    """
    try:
        # 调用服务层获取任务详情
        task = await TaskService.get_task(
            db=db,
            task_id=task_id,
            user_id=current_user.id
        )

        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="任务不存在"
            )

        return UnlockTaskResponse.model_validate(task)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取任务详情失败: {str(e)}"
        )


@router.post("/{task_id}/cancel", response_model=dict, status_code=status.HTTP_200_OK)
async def cancel_task(
    task_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> dict:
    """
    取消任务

    业务逻辑：
        1. 验证用户身份
        2. 验证任务归属（只能取消自己的任务）
        3. 验证任务状态（只能取消 pending 或 processing 状态的任务）
        4. 如果任务在 Celery 队列中，撤销 Celery 任务（TODO）
        5. 更新任务状态为 cancelled
        6. 记录取消时间和原因
        7. 返回成功消息

    注意：
        - 已完成的任务（success/failed）无法取消
        - 已取消的任务无法再次取消

    请求示例：
        POST /api/v1/tasks/123/cancel

    响应示例：
        {
            "task_id": 123,
            "account_id": 1,
            "apple_id": "example@icloud.com",
            "status": "cancelled",
            "message": "任务已取消"
        }

    错误处理：
        - 400: 任务状态不允许取消
        - 404: 任务不存在
        - 500: 数据库错误、Celery 撤销失败

    TODO:
        - 实现 Celery 任务撤销（celery.control.revoke）
        - 添加取消原因字段（用户主动取消、超时取消等）
        - 支持批量取消（取消多个任务）
        - 取消时发送通知
    """
    try:
        # 调用服务层取消任务
        success, task_info = await TaskService.cancel_task(
            db=db,
            task_id=task_id,
            user_id=current_user.id
        )

        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=task_info.get("error", "取消任务失败")
            )

        return {
            "task_id": task_id,
            "account_id": task_info.get("account_id"),
            "apple_id": task_info.get("apple_id"),
            "status": "cancelled",
            "message": "任务已取消"
        }

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
            detail=f"取消任务失败: {str(e)}"
        )


@router.get("/stats", response_model=TaskStatsResponse, status_code=status.HTTP_200_OK)
async def get_task_stats(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> TaskStatsResponse:
    """
    获取任务统计信息

    业务逻辑：
        1. 验证用户身份
        2. 统计当前用户的所有任务：
           - 总任务数
           - 待执行任务数（pending）
           - 执行中任务数（processing）
           - 成功任务数（success）
           - 失败任务数（failed）
           - 已取消任务数（cancelled）
        3. 计算成功率：success / (success + failed) * 100%
        4. 返回统计信息

    请求示例：
        GET /api/v1/tasks/stats

    响应示例：
        {
            "total": 100,
            "pending": 5,
            "processing": 2,
            "success": 85,
            "failed": 5,
            "cancelled": 3,
            "success_rate": 94.44
        }

    错误处理：
        - 500: 数据库错误

    TODO:
        - 添加时间范围统计（今天、本周、本月）
        - 添加按任务类型统计
        - 添加平均执行时间统计
        - 添加失败原因分类统计
        - 支持导出统计报表
    """
    try:
        # 调用服务层获取统计信息
        stats = await TaskService.get_task_stats(
            db=db,
            user_id=current_user.id
        )

        return TaskStatsResponse(**stats)

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取统计信息失败: {str(e)}"
        )


# ========== 导出路由 ==========
__all__ = ["router"]
