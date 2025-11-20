"""
FastAPI 主应用

本模块是 FastAPI 应用的入口文件，负责：
- 应用初始化和配置
- 中间件注册（统一由 setup_middleware 管理）
- 路由注册
- 生命周期管理（数据库连接等）
- 全局异常处理
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.db.database import init_db, close_db
from app.db.redis import RedisClient
from app.api.v1.api import api_router
from app.api.middleware import setup_middleware


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时
    print("🚀 启动 Apple ID Auto 系统...")
    await init_db()
    await RedisClient.get_client()
    print("✅ 数据库和 Redis 连接成功")

    yield

    # 关闭时
    print("🛑 关闭系统...")
    await close_db()
    await RedisClient.close()
    print("✅ 系统已关闭")


# 创建 FastAPI 应用
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Apple ID 自动解锁 & 批量管理系统 API",
    docs_url="/api/docs" if settings.DEBUG else None,
    redoc_url="/api/redoc" if settings.DEBUG else None,
    lifespan=lifespan,
)

# 可信主机中间件（生产环境）
# 注意：此中间件需要在其他中间件之前注册
if not settings.DEBUG:
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=["*"],  # 生产环境应该配置具体域名
    )

# 注册所有自定义中间件
# 包括：ErrorHandling、RequestLogging、PerformanceMonitoring、RateLimit、SecurityHeaders、CORS
# 注意：setup_middleware 会按正确的顺序注册所有中间件
setup_middleware(app)


# 全局异常处理
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """全局异常处理器"""
    return JSONResponse(
        status_code=500,
        content={"code": 500, "message": "服务器内部错误", "detail": str(exc) if settings.DEBUG else None},
    )


# 健康检查
@app.get("/health")
async def health_check():
    """健康检查接口"""
    return {"status": "healthy", "version": settings.APP_VERSION}


# 根路径
@app.get("/")
async def root():
    """根路径"""
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "docs": "/api/docs" if settings.DEBUG else None,
    }


# 注册 API 路由
app.include_router(api_router, prefix="/api/v1")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        workers=settings.WORKERS if not settings.DEBUG else 1,
    )
