"""
代理池服务
"""
from datetime import datetime
from typing import Optional, List, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, desc
import httpx
import asyncio

from app.models.proxy import Proxy
from app.schemas.proxy import (
    ProxyCreate,
    ProxyUpdate,
    ProxyResponse,
    ProxyTestResponse,
)


class ProxyService:
    """代理池服务类"""

    @staticmethod
    async def create_proxy(
        db: AsyncSession,
        user_id: Optional[int],
        data: ProxyCreate,
    ) -> Proxy:
        """
        创建代理

        Args:
            db: 数据库会话
            user_id: 用户ID（NULL 为公共代理）
            data: 创建数据

        Returns:
            Proxy: 创建的代理对象
        """
        # 检查代理是否已存在
        result = await db.execute(
            select(Proxy).where(
                and_(
                    Proxy.host == data.host,
                    Proxy.port == data.port,
                    Proxy.user_id == user_id
                )
            )
        )
        if result.scalar_one_or_none():
            raise ValueError("该代理已存在")

        # 创建代理
        proxy = Proxy(
            user_id=user_id,
            proxy_type=data.proxy_type,
            host=data.host,
            port=data.port,
            username=data.username,
            password=data.password,
            country=data.country,
            region=data.region,
            priority=data.priority,
            is_active=True,
            status="active",
        )

        db.add(proxy)
        await db.commit()
        await db.refresh(proxy)

        return proxy

    @staticmethod
    async def get_proxy(
        db: AsyncSession,
        proxy_id: int,
        user_id: Optional[int] = None,
    ) -> Optional[Proxy]:
        """
        获取代理详情

        Args:
            db: 数据库会话
            proxy_id: 代理ID
            user_id: 用户ID

        Returns:
            Proxy: 代理对象
        """
        query = select(Proxy).where(Proxy.id == proxy_id)

        # 如果指定了 user_id，只返回该用户或公共的代理
        if user_id is not None:
            query = query.where((Proxy.user_id == user_id) | (Proxy.user_id == None))

        result = await db.execute(query)
        return result.scalar_one_or_none()

    @staticmethod
    async def update_proxy(
        db: AsyncSession,
        proxy_id: int,
        user_id: Optional[int],
        data: ProxyUpdate,
    ) -> Optional[Proxy]:
        """
        更新代理

        Args:
            db: 数据库会话
            proxy_id: 代理ID
            user_id: 用户ID
            data: 更新数据

        Returns:
            Proxy: 更新后的代理对象
        """
        # 获取代理
        result = await db.execute(
            select(Proxy).where(
                and_(
                    Proxy.id == proxy_id,
                    Proxy.user_id == user_id
                )
            )
        )
        proxy = result.scalar_one_or_none()

        if not proxy:
            return None

        # 更新字段
        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(proxy, field, value)

        proxy.updated_at = datetime.utcnow()
        await db.commit()
        await db.refresh(proxy)

        return proxy

    @staticmethod
    async def delete_proxy(
        db: AsyncSession,
        proxy_id: int,
        user_id: Optional[int],
    ) -> bool:
        """
        删除代理

        Args:
            db: 数据库会话
            proxy_id: 代理ID
            user_id: 用户ID

        Returns:
            bool: 是否成功
        """
        # 获取代理
        result = await db.execute(
            select(Proxy).where(
                and_(
                    Proxy.id == proxy_id,
                    Proxy.user_id == user_id
                )
            )
        )
        proxy = result.scalar_one_or_none()

        if not proxy:
            return False

        await db.delete(proxy)
        await db.commit()
        return True

    @staticmethod
    async def get_proxy_list(
        db: AsyncSession,
        user_id: Optional[int] = None,
        page: int = 1,
        per_page: int = 20,
        status: Optional[str] = None,
        is_active: Optional[bool] = None,
    ) -> Tuple[List[Proxy], int]:
        """
        获取代理列表

        Args:
            db: 数据库会话
            user_id: 用户ID（NULL 返回公共代理）
            page: 页码
            per_page: 每页数量
            status: 状态过滤
            is_active: 激活状态过滤

        Returns:
            Tuple[List[Proxy], int]: (代理列表, 总数)
        """
        # 构建基础查询
        if user_id is not None:
            # 返回用户自己的和公共的代理
            query = select(Proxy).where(
                (Proxy.user_id == user_id) | (Proxy.user_id == None)
            )
        else:
            # 只返回公共代理
            query = select(Proxy).where(Proxy.user_id == None)

        # 应用过滤条件
        if status:
            query = query.where(Proxy.status == status)

        if is_active is not None:
            query = query.where(Proxy.is_active == is_active)

        # 获取总数
        count_query = select(func.count()).select_from(query.subquery())
        result = await db.execute(count_query)
        total = result.scalar()

        # 排序和分页
        query = query.order_by(desc(Proxy.priority), desc(Proxy.created_at))
        query = query.offset((page - 1) * per_page).limit(per_page)

        # 执行查询
        result = await db.execute(query)
        proxies = result.scalars().all()

        return list(proxies), total

    @staticmethod
    async def test_proxy(
        db: AsyncSession,
        proxy_id: int,
        test_url: str = "https://www.apple.com",
        timeout: int = 10,
    ) -> ProxyTestResponse:
        """
        测试代理

        Args:
            db: 数据库会话
            proxy_id: 代理ID
            test_url: 测试 URL
            timeout: 超时时间（秒）

        Returns:
            ProxyTestResponse: 测试结果
        """
        # 获取代理
        result = await db.execute(
            select(Proxy).where(Proxy.id == proxy_id)
        )
        proxy = result.scalar_one_or_none()

        if not proxy:
            raise ValueError("代理不存在")

        # 构建代理 URL
        proxy_url = proxy.proxy_url

        # 测试代理
        start_time = datetime.utcnow()
        success = False
        error_message = None
        response_time = None

        try:
            async with httpx.AsyncClient(proxies={"all://": proxy_url}, timeout=timeout) as client:
                response = await client.get(test_url)
                response.raise_for_status()
                success = True
                end_time = datetime.utcnow()
                response_time = int((end_time - start_time).total_seconds() * 1000)

        except Exception as e:
            error_message = str(e)

        # 更新代理状态
        proxy.last_checked_at = datetime.utcnow()

        if success:
            proxy.status = "active"
            proxy.success_count += 1
            proxy.last_success_at = datetime.utcnow()
            proxy.last_error = None

            # 更新平均响应时间
            if proxy.avg_response_time:
                proxy.avg_response_time = int((proxy.avg_response_time + response_time) / 2)
            else:
                proxy.avg_response_time = response_time
        else:
            proxy.status = "failed"
            proxy.failure_count += 1
            proxy.last_error = error_message

        await db.commit()

        return ProxyTestResponse(
            success=success,
            response_time=response_time,
            error_message=error_message,
            status=proxy.status,
        )

    @staticmethod
    async def get_best_proxy(
        db: AsyncSession,
        user_id: Optional[int] = None,
        country: Optional[str] = None,
    ) -> Optional[Proxy]:
        """
        获取最佳代理（内部使用，用于任务分配）

        Args:
            db: 数据库会话
            user_id: 用户ID
            country: 国家过滤

        Returns:
            Proxy: 最佳代理对象
        """
        # 构建查询
        if user_id is not None:
            query = select(Proxy).where(
                and_(
                    (Proxy.user_id == user_id) | (Proxy.user_id == None),
                    Proxy.is_active == True,
                    Proxy.status == "active"
                )
            )
        else:
            query = select(Proxy).where(
                and_(
                    Proxy.user_id == None,
                    Proxy.is_active == True,
                    Proxy.status == "active"
                )
            )

        # 国家过滤
        if country:
            query = query.where(Proxy.country == country)

        # 按优先级、成功率、响应时间排序
        query = query.order_by(
            desc(Proxy.priority),
            desc((Proxy.success_count / (Proxy.success_count + Proxy.failure_count + 1))),
            Proxy.avg_response_time.asc().nullslast()
        )

        result = await db.execute(query.limit(1))
        return result.scalar_one_or_none()

    @staticmethod
    async def health_check_all(
        db: AsyncSession,
        test_url: str = "https://www.apple.com",
        timeout: int = 10,
    ) -> dict:
        """
        健康检查所有代理（内部使用，由定时任务调用）

        Args:
            db: 数据库会话
            test_url: 测试 URL
            timeout: 超时时间

        Returns:
            dict: 检查结果
        """
        # 获取所有激活的代理
        result = await db.execute(
            select(Proxy).where(Proxy.is_active == True)
        )
        proxies = result.scalars().all()

        total = len(proxies)
        success = 0
        failed = 0

        # 测试所有代理
        for proxy in proxies:
            try:
                test_result = await ProxyService.test_proxy(db, proxy.id, test_url, timeout)
                if test_result.success:
                    success += 1
                else:
                    failed += 1
            except Exception:
                failed += 1

        return {
            "total": total,
            "success": success,
            "failed": failed,
            "message": f"健康检查完成，成功：{success}，失败：{failed}"
        }
