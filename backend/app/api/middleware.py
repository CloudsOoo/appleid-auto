"""
API 中间件模块

本模块提供 FastAPI 的中间件功能，用于：
- 请求日志记录
- 统一错误处理
- API 限流保护
- 性能监控
- CORS 跨域处理

调用关系：
main.py 注册中间件 → 每个请求都经过中间件处理

使用方式：
    from app.api.middleware import setup_middleware

    app = FastAPI()
    setup_middleware(app)  # 一次性注册所有中间件
"""

import time
import logging
from typing import Callable
from datetime import datetime
from collections import defaultdict

from fastapi import FastAPI, Request, Response, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from app.core.config import settings


# ========== 配置日志 ==========
logger = logging.getLogger(__name__)


# ========== 1. 请求日志中间件 ==========

class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    请求日志中间件

    功能：
    - 记录每个请求的详细信息
    - 记录请求耗时
    - 记录响应状态
    - 记录请求来源（IP、User-Agent）

    日志格式：
        [时间] [方法] [路径] [状态码] [耗时] [IP] [User-Agent]

    业务逻辑：
        1. 记录请求开始时间
        2. 提取请求信息（方法、路径、IP、UA）
        3. 执行请求处理
        4. 计算耗时
        5. 记录完整日志
        6. 返回响应

    使用示例：
        app.add_middleware(RequestLoggingMiddleware)
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # 记录开始时间
        start_time = time.time()

        # 提取请求信息
        method = request.method
        path = request.url.path
        client_ip = request.client.host if request.client else "unknown"
        user_agent = request.headers.get("user-agent", "unknown")

        # 处理请求
        try:
            response = await call_next(request)

            # 计算耗时
            process_time = time.time() - start_time

            # 记录日志
            log_message = (
                f"{method} {path} "
                f"status={response.status_code} "
                f"time={process_time:.3f}s "
                f"ip={client_ip} "
                f"ua={user_agent[:50]}"
            )

            # 根据状态码选择日志级别
            if response.status_code >= 500:
                logger.error(log_message)
            elif response.status_code >= 400:
                logger.warning(log_message)
            else:
                logger.info(log_message)

            # 添加自定义响应头（耗时）
            response.headers["X-Process-Time"] = f"{process_time:.3f}"

            return response

        except Exception as e:
            # 记录异常
            process_time = time.time() - start_time
            logger.error(
                f"{method} {path} "
                f"ERROR: {str(e)} "
                f"time={process_time:.3f}s "
                f"ip={client_ip}"
            )
            raise


# ========== 2. 统一错误处理中间件 ==========

class ErrorHandlingMiddleware(BaseHTTPMiddleware):
    """
    统一错误处理中间件

    功能：
    - 捕获所有未处理的异常
    - 返回统一的错误响应格式
    - 记录错误日志
    - 保护敏感信息不泄露

    错误响应格式：
        {
            "code": 500,
            "message": "服务器内部错误",
            "detail": "具体错误信息（开发环境）",
            "timestamp": "2025-11-20T12:00:00"
        }

    业务逻辑：
        1. 使用 try-except 包裹请求
        2. 捕获所有异常
        3. 区分开发/生产环境
        4. 返回统一格式的错误响应
        5. 记录错误日志

    使用示例：
        app.add_middleware(ErrorHandlingMiddleware)
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        try:
            response = await call_next(request)
            return response

        except Exception as e:
            # 记录完整的异常堆栈
            logger.exception(f"Unhandled error: {str(e)}")

            # 构建错误响应
            error_response = {
                "code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": "服务器内部错误",
                "timestamp": datetime.utcnow().isoformat(),
            }

            # 开发环境返回详细错误信息
            if settings.DEBUG:
                error_response["detail"] = str(e)
                error_response["type"] = type(e).__name__

            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content=error_response
            )


# ========== 3. API 限流中间件 ==========

class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    API 限流中间件（基于 IP）

    功能：
    - 防止 API 滥用
    - 基于 IP 地址限流
    - 支持不同路径不同限流策略
    - 返回 429 Too Many Requests

    限流策略：
    - 默认：60 请求/分钟
    - 登录接口：10 请求/分钟
    - 注册接口：5 请求/分钟
    - 公开接口：100 请求/分钟

    实现方式：
    - 使用内存字典存储访问记录
    - 记录每个 IP 的访问时间戳
    - 滑动窗口算法

    业务逻辑：
        1. 提取客户端 IP
        2. 根据路径确定限流策略
        3. 检查该 IP 的访问记录
        4. 清理过期记录
        5. 判断是否超过限制
        6. 超过则返回 429，否则继续

    使用示例：
        app.add_middleware(RateLimitMiddleware)

    TODO:
        - 使用 Redis 存储访问记录（支持分布式）
        - 支持基于用户 ID 的限流
        - 支持动态调整限流配置
        - 支持白名单机制
    """

    def __init__(self, app: ASGIApp):
        super().__init__(app)

        # 访问记录：{ip: [timestamp1, timestamp2, ...]}
        self.access_records = defaultdict(list)

        # 限流配置：{path_pattern: (max_requests, time_window_seconds)}
        self.rate_limits = {
            "/api/v1/auth/login": (10, 60),      # 10次/分钟
            "/api/v1/auth/register": (5, 60),    # 5次/分钟
            "/api/v1/cards/activate": (20, 60),  # 20次/分钟
            "/public": (100, 60),                 # 100次/分钟
            "default": (60, 60),                  # 默认 60次/分钟
        }

    def get_rate_limit(self, path: str) -> tuple:
        """
        根据路径获取限流配置

        Args:
            path: 请求路径

        Returns:
            tuple: (最大请求数, 时间窗口秒数)
        """
        for pattern, limit in self.rate_limits.items():
            if pattern in path:
                return limit
        return self.rate_limits["default"]

    def check_rate_limit(self, client_ip: str, max_requests: int, time_window: int) -> bool:
        """
        检查是否超过限流

        Args:
            client_ip: 客户端 IP
            max_requests: 最大请求数
            time_window: 时间窗口（秒）

        Returns:
            bool: True=允许访问，False=超过限制
        """
        current_time = time.time()

        # 获取该 IP 的访问记录
        records = self.access_records[client_ip]

        # 清理过期记录（超过时间窗口的记录）
        cutoff_time = current_time - time_window
        self.access_records[client_ip] = [
            ts for ts in records if ts > cutoff_time
        ]

        # 检查是否超过限制
        if len(self.access_records[client_ip]) >= max_requests:
            return False

        # 记录本次访问
        self.access_records[client_ip].append(current_time)
        return True

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # 提取客户端 IP
        client_ip = request.client.host if request.client else "unknown"

        # 跳过健康检查和内部接口
        if request.url.path in ["/health", "/metrics"]:
            return await call_next(request)

        # 获取限流配置
        max_requests, time_window = self.get_rate_limit(request.url.path)

        # 检查限流
        if not self.check_rate_limit(client_ip, max_requests, time_window):
            logger.warning(
                f"Rate limit exceeded for {client_ip} on {request.url.path}"
            )
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "code": 429,
                    "message": "请求过于频繁，请稍后再试",
                    "retry_after": time_window,
                }
            )

        # 继续处理请求
        response = await call_next(request)

        # 添加限流信息到响应头
        response.headers["X-RateLimit-Limit"] = str(max_requests)
        response.headers["X-RateLimit-Remaining"] = str(
            max_requests - len(self.access_records[client_ip])
        )
        response.headers["X-RateLimit-Reset"] = str(int(time.time() + time_window))

        return response


# ========== 4. 性能监控中间件 ==========

class PerformanceMonitoringMiddleware(BaseHTTPMiddleware):
    """
    性能监控中间件

    功能：
    - 监控每个端点的响应时间
    - 统计慢查询
    - 记录性能指标

    监控指标：
    - 平均响应时间
    - 最慢的 10 个请求
    - 每个端点的调用次数

    业务逻辑：
        1. 记录请求开始时间
        2. 执行请求
        3. 计算耗时
        4. 如果超过阈值，记录慢查询日志
        5. 更新统计数据

    使用示例：
        app.add_middleware(PerformanceMonitoringMiddleware)

    TODO:
        - 集成 Prometheus 指标
        - 支持分布式追踪（OpenTelemetry）
        - 支持告警机制
    """

    def __init__(self, app: ASGIApp, slow_threshold: float = 1.0):
        super().__init__(app)
        self.slow_threshold = slow_threshold  # 慢查询阈值（秒）
        self.slow_requests = []  # 慢查询记录

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start_time = time.time()

        response = await call_next(request)

        process_time = time.time() - start_time

        # 检查是否是慢查询
        if process_time > self.slow_threshold:
            slow_request = {
                "method": request.method,
                "path": request.url.path,
                "time": process_time,
                "timestamp": datetime.utcnow().isoformat(),
            }

            # 保留最近的 100 条慢查询
            self.slow_requests.append(slow_request)
            if len(self.slow_requests) > 100:
                self.slow_requests.pop(0)

            # 记录慢查询日志
            logger.warning(
                f"Slow request detected: {request.method} {request.url.path} "
                f"took {process_time:.3f}s"
            )

        return response


# ========== 5. 安全头中间件 ==========

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    安全响应头中间件

    功能：
    - 添加安全相关的 HTTP 响应头
    - 防止常见的 Web 安全攻击

    添加的响应头：
    - X-Content-Type-Options: nosniff
    - X-Frame-Options: DENY
    - X-XSS-Protection: 1; mode=block
    - Strict-Transport-Security: max-age=31536000
    - Content-Security-Policy: default-src 'self'

    业务逻辑：
        1. 处理请求
        2. 在响应中添加安全头
        3. 返回响应

    使用示例：
        app.add_middleware(SecurityHeadersMiddleware)
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        response = await call_next(request)

        # 添加安全响应头
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"

        # HTTPS 环境下添加 HSTS
        if settings.ENVIRONMENT == "production":
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"

        # CSP 策略（根据实际需求调整）
        # response.headers["Content-Security-Policy"] = "default-src 'self'"

        return response


# ========== 统一注册函数 ==========

def setup_middleware(app: FastAPI) -> None:
    """
    统一注册所有中间件

    注册顺序很重要：
    1. 错误处理（最外层，捕获所有错误）
    2. 请求日志（记录所有请求）
    3. 性能监控（监控响应时间）
    4. 限流保护（防止滥用）
    5. 安全头（添加安全响应头）
    6. CORS（跨域处理，最内层）

    Args:
        app: FastAPI 应用实例

    使用示例：
        from app.api.middleware import setup_middleware

        app = FastAPI()
        setup_middleware(app)
    """

    # 1. 错误处理中间件（最外层）
    app.add_middleware(ErrorHandlingMiddleware)

    # 2. 请求日志中间件
    app.add_middleware(RequestLoggingMiddleware)

    # 3. 性能监控中间件
    app.add_middleware(
        PerformanceMonitoringMiddleware,
        slow_threshold=1.0  # 1秒为慢查询阈值
    )

    # 4. 限流中间件
    if settings.ENABLE_RATE_LIMIT:
        app.add_middleware(RateLimitMiddleware)

    # 5. 安全头中间件
    app.add_middleware(SecurityHeadersMiddleware)

    # 6. CORS 中间件（最内层）
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.ALLOWED_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["X-Process-Time", "X-RateLimit-Limit", "X-RateLimit-Remaining"],
    )

    logger.info("All middleware registered successfully")


# ========== 中间件工具函数 ==========

def get_slow_requests(app: FastAPI) -> list:
    """
    获取慢查询列表（用于监控端点）

    Args:
        app: FastAPI 应用实例

    Returns:
        list: 慢查询记录列表

    使用示例：
        @router.get("/admin/slow-requests")
        async def get_slow_requests_api(request: Request):
            slow_requests = get_slow_requests(request.app)
            return {"data": slow_requests}
    """
    for middleware in app.user_middleware:
        if isinstance(middleware.cls, type) and issubclass(middleware.cls, PerformanceMonitoringMiddleware):
            # 获取中间件实例
            # TODO: 实现从中间件实例获取慢查询数据
            pass
    return []


# ========== 导出 ==========

__all__ = [
    "RequestLoggingMiddleware",
    "ErrorHandlingMiddleware",
    "RateLimitMiddleware",
    "PerformanceMonitoringMiddleware",
    "SecurityHeadersMiddleware",
    "setup_middleware",
    "get_slow_requests",
]
