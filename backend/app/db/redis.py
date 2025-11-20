"""
Redis 连接配置
"""
import redis.asyncio as redis
from typing import Optional
from app.core.config import settings


class RedisClient:
    """Redis 客户端单例"""

    _instance: Optional[redis.Redis] = None

    @classmethod
    async def get_client(cls) -> redis.Redis:
        """获取 Redis 客户端"""
        if cls._instance is None:
            cls._instance = await redis.from_url(
                settings.REDIS_URL,
                password=settings.REDIS_PASSWORD,
                encoding="utf-8",
                decode_responses=True,
                max_connections=50,
            )
        return cls._instance

    @classmethod
    async def close(cls):
        """关闭 Redis 连接"""
        if cls._instance:
            await cls._instance.close()
            cls._instance = None


async def get_redis() -> redis.Redis:
    """获取 Redis 客户端（用于依赖注入）"""
    return await RedisClient.get_client()
