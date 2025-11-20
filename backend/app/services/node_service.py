"""
节点管理服务
"""
from datetime import datetime, timedelta
from typing import Optional, List, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, desc

from app.models.node import Node
from app.models.permission import UserPermission
from app.core.security import generate_node_key
from app.core.config import settings
from app.schemas.node import (
    NodeRegister,
    NodeHeartbeat,
    NodeResponse,
)


class NodeService:
    """节点管理服务类"""

    @staticmethod
    async def check_node_quota(
        db: AsyncSession,
        user_id: int
    ) -> Tuple[bool, str]:
        """
        检查节点配额

        Args:
            db: 数据库会话
            user_id: 用户ID

        Returns:
            Tuple[bool, str]: (是否有配额, 错误信息)
        """
        # 获取用户权限
        result = await db.execute(
            select(UserPermission).where(UserPermission.user_id == user_id)
        )
        permission = result.scalar_one_or_none()

        if not permission:
            return False, "用户权限不存在"

        # 检查是否过期
        if permission.is_expired():
            return False, "用户权限已过期"

        # 检查节点数量配额
        result = await db.execute(
            select(func.count(Node.id)).where(Node.user_id == user_id)
        )
        current_count = result.scalar() or 0

        if current_count >= permission.max_nodes:
            return False, f"节点数量已达上限（{permission.max_nodes}）"

        return True, ""

    @staticmethod
    async def register_node(
        db: AsyncSession,
        user_id: int,
        data: NodeRegister,
    ) -> Node:
        """
        注册节点

        Args:
            db: 数据库会话
            user_id: 用户ID
            data: 注册数据

        Returns:
            Node: 创建的节点对象
        """
        # 检查配额
        has_quota, error_msg = await NodeService.check_node_quota(db, user_id)
        if not has_quota:
            raise ValueError(error_msg)

        # 生成节点密钥
        node_key = generate_node_key()

        # 创建节点
        node = Node(
            user_id=user_id,
            node_name=data.node_name,
            node_key=node_key,
            node_url=data.node_url,
            country=data.country,
            region=data.region,
            status="online",
            is_active=True,
            last_heartbeat_at=datetime.utcnow(),
        )

        db.add(node)

        # 更新用户权限计数
        result = await db.execute(
            select(UserPermission).where(UserPermission.user_id == user_id)
        )
        permission = result.scalar_one()
        permission.nodes_count += 1

        await db.commit()
        await db.refresh(node)

        return node

    @staticmethod
    async def get_node_by_key(
        db: AsyncSession,
        node_key: str,
    ) -> Optional[Node]:
        """
        通过密钥获取节点

        Args:
            db: 数据库会话
            node_key: 节点密钥

        Returns:
            Node: 节点对象
        """
        result = await db.execute(
            select(Node).where(Node.node_key == node_key)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_node(
        db: AsyncSession,
        node_id: int,
        user_id: int,
    ) -> Optional[Node]:
        """
        获取节点详情

        Args:
            db: 数据库会话
            node_id: 节点ID
            user_id: 用户ID

        Returns:
            Node: 节点对象
        """
        result = await db.execute(
            select(Node).where(
                and_(
                    Node.id == node_id,
                    Node.user_id == user_id
                )
            )
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_node_list(
        db: AsyncSession,
        user_id: int,
        page: int = 1,
        per_page: int = 20,
        status: Optional[str] = None,
        is_active: Optional[bool] = None,
    ) -> Tuple[List[Node], int]:
        """
        获取节点列表

        Args:
            db: 数据库会话
            user_id: 用户ID
            page: 页码
            per_page: 每页数量
            status: 状态过滤
            is_active: 激活状态过滤

        Returns:
            Tuple[List[Node], int]: (节点列表, 总数)
        """
        # 构建基础查询
        query = select(Node).where(Node.user_id == user_id)

        # 应用过滤条件
        if status:
            query = query.where(Node.status == status)

        if is_active is not None:
            query = query.where(Node.is_active == is_active)

        # 获取总数
        count_query = select(func.count()).select_from(query.subquery())
        result = await db.execute(count_query)
        total = result.scalar()

        # 排序和分页
        query = query.order_by(desc(Node.created_at))
        query = query.offset((page - 1) * per_page).limit(per_page)

        # 执行查询
        result = await db.execute(query)
        nodes = result.scalars().all()

        return list(nodes), total

    @staticmethod
    async def delete_node(
        db: AsyncSession,
        node_id: int,
        user_id: int,
    ) -> bool:
        """
        删除节点

        Args:
            db: 数据库会话
            node_id: 节点ID
            user_id: 用户ID

        Returns:
            bool: 是否成功
        """
        # 获取节点
        result = await db.execute(
            select(Node).where(
                and_(
                    Node.id == node_id,
                    Node.user_id == user_id
                )
            )
        )
        node = result.scalar_one_or_none()

        if not node:
            return False

        await db.delete(node)

        # 更新用户权限计数
        result = await db.execute(
            select(UserPermission).where(UserPermission.user_id == user_id)
        )
        permission = result.scalar_one_or_none()
        if permission and permission.nodes_count > 0:
            permission.nodes_count -= 1

        await db.commit()
        return True

    @staticmethod
    async def update_heartbeat(
        db: AsyncSession,
        node_key: str,
        data: NodeHeartbeat,
    ) -> bool:
        """
        更新节点心跳

        Args:
            db: 数据库会话
            node_key: 节点密钥
            data: 心跳数据

        Returns:
            bool: 是否成功
        """
        # 获取节点
        node = await NodeService.get_node_by_key(db, node_key)

        if not node:
            return False

        # 更新心跳信息
        node.last_heartbeat_at = datetime.utcnow()
        node.status = "online"
        node.cpu_usage = data.cpu_usage
        node.memory_usage = data.memory_usage
        node.task_queue_size = data.task_queue_size

        await db.commit()
        return True

    @staticmethod
    async def update_task_stats(
        db: AsyncSession,
        node_id: int,
        success: bool,
    ) -> bool:
        """
        更新节点任务统计（内部使用，由任务完成时调用）

        Args:
            db: 数据库会话
            node_id: 节点ID
            success: 是否成功

        Returns:
            bool: 是否成功
        """
        result = await db.execute(
            select(Node).where(Node.id == node_id)
        )
        node = result.scalar_one_or_none()

        if not node:
            return False

        node.total_tasks += 1
        if success:
            node.success_tasks += 1
        else:
            node.failed_tasks += 1

        await db.commit()
        return True

    @staticmethod
    async def get_best_node(
        db: AsyncSession,
        user_id: int,
    ) -> Optional[Node]:
        """
        获取最佳节点（内部使用，用于任务分配）

        Args:
            db: 数据库会话
            user_id: 用户ID

        Returns:
            Node: 最佳节点对象
        """
        # 获取用户的在线节点
        result = await db.execute(
            select(Node).where(
                and_(
                    Node.user_id == user_id,
                    Node.is_active == True,
                    Node.status == "online"
                )
            )
        )
        nodes = result.scalars().all()

        if not nodes:
            return None

        # 过滤掉心跳超时的节点
        online_nodes = [node for node in nodes if node.is_online()]

        if not online_nodes:
            return None

        # 选择任务队列最小、成功率最高的节点
        best_node = min(
            online_nodes,
            key=lambda n: (
                n.task_queue_size,
                -(n.success_tasks / (n.total_tasks + 1))
            )
        )

        return best_node

    @staticmethod
    async def health_check_all(
        db: AsyncSession,
    ) -> dict:
        """
        健康检查所有节点（内部使用，由定时任务调用）

        Args:
            db: 数据库会话

        Returns:
            dict: 检查结果
        """
        # 获取所有激活的节点
        result = await db.execute(
            select(Node).where(Node.is_active == True)
        )
        nodes = result.scalars().all()

        total = len(nodes)
        online = 0
        offline = 0

        # 检查所有节点
        threshold = datetime.utcnow() - timedelta(seconds=settings.NODE_OFFLINE_THRESHOLD)

        for node in nodes:
            if node.last_heartbeat_at and node.last_heartbeat_at > threshold:
                # 在线
                if node.status != "online":
                    node.status = "online"
                online += 1
            else:
                # 离线
                if node.status != "offline":
                    node.status = "offline"
                offline += 1

        await db.commit()

        return {
            "total": total,
            "online": online,
            "offline": offline,
            "message": f"健康检查完成，在线：{online}，离线：{offline}"
        }
