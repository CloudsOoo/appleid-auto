"""
节点管理 API 端点

本模块实现节点的注册、查询、心跳和删除功能，包括：
- 注册节点（生成唯一密钥）
- 获取节点列表（支持分页和过滤）
- 节点心跳上报（更新状态和性能数据）
- 删除节点

业务场景：
    1. 用户注册解锁节点，系统生成唯一节点密钥（node_key）
    2. 节点使用密钥定期上报心跳（CPU、内存、任务队列）
    3. 系统根据心跳判断节点在线状态（3分钟内有心跳为在线）
    4. Celery 任务根据节点负载自动分配任务
    5. 用户可以查看节点列表和删除节点

权限控制：
    - 注册节点：需要登录用户，检查配额
    - 查看节点列表：只能查看自己的节点
    - 节点心跳：使用节点密钥认证（不需要用户登录）
    - 删除节点：只能删除自己的节点

依赖关系：
    上游：解锁节点客户端、前端用户
    下游：NodeService、Celery 任务（account_tasks）
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query, Header
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_active_user, get_db
from app.models.user import User
from app.schemas.node import (
    NodeRegister,
    NodeHeartbeat,
    NodeResponse,
)
from app.services.node_service import NodeService

router = APIRouter(tags=["节点管理"])


# ========================================
# 注册节点
# ========================================

@router.post("/register", response_model=NodeResponse, status_code=status.HTTP_201_CREATED)
async def register_node(
    data: NodeRegister,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    注册解锁节点

    业务逻辑：
        1. 验证用户身份（需要登录）
        2. 检查节点配额（用户权限中的 max_nodes）
        3. 生成唯一节点密钥（node_key，用于后续心跳认证）
        4. 创建节点记录，关联到当前用户
        5. 更新用户权限中的节点计数（nodes_count）
        6. 返回节点信息（包含节点密钥）

    权限要求：
        - 需要登录用户
        - 需要有可用的节点配额

    节点配额检查：
        - 用户权限中的 max_nodes 限制
        - 如果 nodes_count >= max_nodes，返回 403
        - 如果用户权限已过期，返回 403

    请求参数：
        - node_name: 节点名称（必填，1-100字符）
        - node_url: 节点 API 地址（可选，用于管理节点）
        - country: 国家代码（可选，如 US、CN）
        - region: 地区（可选）

    返回结果：
        - 201: 注册成功，返回节点信息（包含 node_key）
        - 403: 配额不足或权限已过期
        - 401: 未登录
        - 422: 参数验证失败

    示例：
        POST /api/v1/nodes/register
        {
            "node_name": "解锁节点1",
            "node_url": "https://node1.example.com",
            "country": "US",
            "region": "West"
        }

        Response:
        {
            "id": 1,
            "node_name": "解锁节点1",
            "node_key": "nk_a1b2c3d4e5f6g7h8",  // 重要：保存此密钥用于心跳
            "node_url": "https://node1.example.com",
            "status": "online",
            "is_active": true,
            "cpu_usage": null,
            "memory_usage": null,
            "task_queue_size": 0,
            "total_tasks": 0,
            "success_tasks": 0,
            "failed_tasks": 0,
            "success_rate": 0.0,
            "last_heartbeat_at": "2025-11-20T12:00:00",
            "country": "US",
            "region": "West",
            "created_at": "2025-11-20T12:00:00"
        }

    节点密钥说明：
        - node_key 是节点的唯一标识，用于心跳认证
        - 节点客户端应该保存此密钥，并在每次心跳时携带
        - 密钥格式：nk_<16位随机字符串>
        - 密钥不可修改，如需更换请删除节点后重新注册

    TODO (优先级 P1):
        - [ ] 添加节点白名单（IP 白名单）
        - [ ] 支持节点分组（按功能、地区分组）
        - [ ] 添加节点配置项（最大并发任务数等）
        - [ ] 支持节点批量注册
    """
    try:
        # 注册节点（会自动检查配额）
        node = await NodeService.register_node(
            db=db,
            user_id=current_user.id,
            data=data
        )

        return node

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"注册节点失败: {str(e)}"
        )


# ========================================
# 获取节点列表
# ========================================

@router.get("", response_model=dict, status_code=status.HTTP_200_OK)
async def get_node_list(
    page: int = Query(1, ge=1, description="页码"),
    per_page: int = Query(20, ge=1, le=100, description="每页数量"),
    status_filter: Optional[str] = Query(None, alias="status", description="状态过滤（online/offline/error）"),
    is_active: Optional[bool] = Query(None, description="激活状态过滤"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    获取节点列表（分页）

    业务逻辑：
        1. 验证用户身份（需要登录）
        2. 查询用户自己的节点（只能看到自己的节点）
        3. 支持按状态、激活状态过滤
        4. 支持分页
        5. 返回节点列表和总数

    权限要求：
        - 需要登录用户
        - 只能查看自己的节点

    查询参数：
        - page: 页码（默认1）
        - per_page: 每页数量（默认20，最大100）
        - status: 状态过滤（online/offline/error）
        - is_active: 激活状态过滤（true/false）

    节点状态说明：
        - online: 在线（3分钟内有心跳）
        - offline: 离线（超过3分钟无心跳）
        - error: 错误状态（节点报告错误）

    返回结果：
        - 200: 成功，返回节点列表
        - 401: 未登录

    示例：
        GET /api/v1/nodes?page=1&per_page=20&status=online

        Response:
        {
            "total": 5,
            "page": 1,
            "per_page": 20,
            "total_pages": 1,
            "items": [
                {
                    "id": 1,
                    "node_name": "解锁节点1",
                    "node_key": "nk_a1b2c3d4e5f6g7h8",
                    "node_url": "https://node1.example.com",
                    "status": "online",
                    "is_active": true,
                    "cpu_usage": 35.5,
                    "memory_usage": 60.2,
                    "task_queue_size": 5,
                    "total_tasks": 100,
                    "success_tasks": 95,
                    "failed_tasks": 5,
                    "success_rate": 95.0,
                    "last_heartbeat_at": "2025-11-20T12:00:00",
                    "country": "US",
                    "region": "West",
                    "created_at": "2025-11-19T10:00:00"
                }
            ]
        }

    TODO (优先级 P2):
        - [ ] 支持按国家/地区过滤
        - [ ] 支持按成功率排序
        - [ ] 支持按负载排序（CPU、内存、队列大小）
        - [ ] 添加搜索功能（按名称搜索）
    """
    try:
        # 获取节点列表
        nodes, total = await NodeService.get_node_list(
            db=db,
            user_id=current_user.id,
            page=page,
            per_page=per_page,
            status=status_filter,
            is_active=is_active,
        )

        # 计算总页数
        total_pages = (total + per_page - 1) // per_page

        # 计算成功率
        items = []
        for node in nodes:
            node_dict = NodeResponse.model_validate(node).model_dump()
            # 计算成功率
            if node.total_tasks > 0:
                node_dict["success_rate"] = round((node.success_tasks / node.total_tasks) * 100, 2)
            else:
                node_dict["success_rate"] = 0.0
            items.append(node_dict)

        return {
            "total": total,
            "page": page,
            "per_page": per_page,
            "total_pages": total_pages,
            "items": items
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取节点列表失败: {str(e)}"
        )


# ========================================
# 获取节点详情
# ========================================

@router.get("/{node_id}", response_model=NodeResponse, status_code=status.HTTP_200_OK)
async def get_node(
    node_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    获取节点详情

    业务逻辑：
        1. 验证用户身份（需要登录）
        2. 查询节点详情
        3. 验证权限（只能查看自己的节点）
        4. 返回节点详细信息

    权限要求：
        - 需要登录用户
        - 只能查看自己的节点

    路径参数：
        - node_id: 节点 ID

    返回结果：
        - 200: 成功，返回节点详情
        - 401: 未登录
        - 404: 节点不存在或无权限访问

    示例：
        GET /api/v1/nodes/1

        Response:
        {
            "id": 1,
            "node_name": "解锁节点1",
            "status": "online",
            "success_rate": 95.0,
            ...
        }
    """
    node = await NodeService.get_node(
        db=db,
        node_id=node_id,
        user_id=current_user.id
    )

    if not node:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="节点不存在或无权限访问"
        )

    return node


# ========================================
# 节点心跳
# ========================================

@router.post("/heartbeat", response_model=dict, status_code=status.HTTP_200_OK)
async def node_heartbeat(
    data: NodeHeartbeat,
    x_node_key: str = Header(..., alias="X-Node-Key", description="节点密钥"),
    db: AsyncSession = Depends(get_db),
):
    """
    节点心跳上报

    业务逻辑：
        1. 验证节点密钥（X-Node-Key 请求头）
        2. 查询节点是否存在
        3. 更新节点心跳时间（last_heartbeat_at）
        4. 更新节点状态为 online
        5. 更新节点性能数据（CPU、内存、任务队列）
        6. 返回成功响应

    权限要求：
        - 需要有效的节点密钥（不需要用户登录）
        - 节点密钥在 HTTP 请求头中：X-Node-Key

    请求头：
        - X-Node-Key: 节点密钥（注册时获得）

    请求参数：
        - cpu_usage: CPU 使用率（0-100）
        - memory_usage: 内存使用率（0-100）
        - task_queue_size: 任务队列大小（当前正在处理的任务数）

    心跳间隔：
        - 建议每 30-60 秒上报一次心跳
        - 超过 3 分钟无心跳，系统将标记节点为 offline
        - offline 状态的节点不会接收新任务

    返回结果：
        - 200: 心跳成功
        - 401: 节点密钥无效
        - 422: 参数验证失败

    示例：
        POST /api/v1/nodes/heartbeat
        Headers:
            X-Node-Key: nk_a1b2c3d4e5f6g7h8
        Body:
        {
            "cpu_usage": 35.5,
            "memory_usage": 60.2,
            "task_queue_size": 5
        }

        Response:
        {
            "success": true,
            "message": "心跳上报成功",
            "status": "online",
            "timestamp": "2025-11-20T12:00:00"
        }

    节点客户端实现示例：
        ```python
        import httpx
        import asyncio
        import psutil

        NODE_KEY = "nk_a1b2c3d4e5f6g7h8"
        API_URL = "https://api.example.com/api/v1/nodes/heartbeat"

        async def send_heartbeat():
            while True:
                try:
                    # 收集性能数据
                    cpu_usage = psutil.cpu_percent(interval=1)
                    memory_usage = psutil.virtual_memory().percent
                    task_queue_size = get_current_task_count()

                    # 发送心跳
                    async with httpx.AsyncClient() as client:
                        response = await client.post(
                            API_URL,
                            headers={"X-Node-Key": NODE_KEY},
                            json={
                                "cpu_usage": cpu_usage,
                                "memory_usage": memory_usage,
                                "task_queue_size": task_queue_size
                            }
                        )
                        response.raise_for_status()
                        print("心跳成功")

                except Exception as e:
                    print(f"心跳失败: {e}")

                # 等待 60 秒
                await asyncio.sleep(60)
        ```

    TODO (优先级 P1):
        - [ ] 添加心跳数据校验（CPU/内存范围检查）
        - [ ] 支持节点报告错误状态
        - [ ] 添加心跳频率限制（避免过于频繁）
        - [ ] 记录心跳历史（用于性能分析）
    """
    try:
        # 更新心跳
        success = await NodeService.update_heartbeat(
            db=db,
            node_key=x_node_key,
            data=data
        )

        if not success:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="节点密钥无效"
            )

        from datetime import datetime
        return {
            "success": True,
            "message": "心跳上报成功",
            "status": "online",
            "timestamp": datetime.utcnow().isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"心跳上报失败: {str(e)}"
        )


# ========================================
# 删除节点
# ========================================

@router.delete("/{node_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_node(
    node_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    删除节点

    业务逻辑：
        1. 验证用户身份（需要登录）
        2. 查询节点是否存在
        3. 验证权限（只能删除自己的节点）
        4. 删除节点记录
        5. 更新用户权限中的节点计数（nodes_count - 1）
        6. 返回 204 No Content

    权限要求：
        - 需要登录用户
        - 只能删除自己的节点

    路径参数：
        - node_id: 节点 ID

    返回结果：
        - 204: 删除成功，无返回内容
        - 401: 未登录
        - 404: 节点不存在或无权限删除

    示例：
        DELETE /api/v1/nodes/1

        Response: 204 No Content

    注意事项：
        - 删除节点是永久性的，无法恢复
        - 删除后节点密钥失效，无法再上报心跳
        - 如需重新使用，需要重新注册节点

    TODO (优先级 P1):
        - [ ] 检查节点是否有正在执行的任务（如果有，提示用户）
        - [ ] 软删除（标记为 deleted，而不是物理删除）
        - [ ] 添加删除前确认（避免误删）
        - [ ] 记录删除历史
    """
    success = await NodeService.delete_node(
        db=db,
        node_id=node_id,
        user_id=current_user.id
    )

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="节点不存在或无权限删除"
        )

    return None


# ========================================
# 导出
# ========================================

__all__ = ["router"]
