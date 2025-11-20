"""
通用的 Pydantic Schemas
"""
from typing import Optional, Generic, TypeVar, Any
from pydantic import BaseModel, Field

T = TypeVar("T")


# ========== 通用响应 ==========
class ResponseModel(BaseModel, Generic[T]):
    """通用响应模型"""
    code: int = Field(200, description="状态码")
    message: str = Field("success", description="消息")
    data: Optional[T] = Field(None, description="数据")


# ========== 分页响应 ==========
class PaginatedResponse(BaseModel, Generic[T]):
    """分页响应模型"""
    items: list[T] = Field([], description="数据列表")
    total: int = Field(0, description="总数")
    page: int = Field(1, description="当前页")
    per_page: int = Field(20, description="每页数量")
    total_pages: int = Field(0, description="总页数")

    @classmethod
    def create(cls, items: list[T], total: int, page: int, per_page: int):
        """创建分页响应"""
        total_pages = (total + per_page - 1) // per_page if per_page > 0 else 0
        return cls(
            items=items,
            total=total,
            page=page,
            per_page=per_page,
            total_pages=total_pages
        )


# ========== 错误响应 ==========
class ErrorResponse(BaseModel):
    """错误响应模型"""
    code: int = Field(..., description="错误码")
    message: str = Field(..., description="错误消息")
    errors: Optional[dict[str, Any]] = Field(None, description="详细错误")


# ========== ID 响应 ==========
class IDResponse(BaseModel):
    """ID 响应模型"""
    id: int = Field(..., description="ID")
    message: str = Field("操作成功", description="消息")


# ========== 统计响应 ==========
class StatsResponse(BaseModel):
    """统计响应模型"""
    total_accounts: int = Field(0, description="总账号数")
    normal_accounts: int = Field(0, description="正常账号数")
    locked_accounts: int = Field(0, description="锁定账号数")
    total_unlocks: int = Field(0, description="总解锁次数")
    success_rate: float = Field(0.0, description="成功率")
    total_share_pages: int = Field(0, description="总分享页数")
    total_views: int = Field(0, description="总浏览量")
    active_nodes: int = Field(0, description="活跃节点数")
    active_proxies: int = Field(0, description="活跃代理数")


# ========== 健康检查响应 ==========
class HealthResponse(BaseModel):
    """健康检查响应"""
    status: str = Field("healthy", description="状态")
    version: str = Field(..., description="版本")
    database: str = Field("connected", description="数据库状态")
    redis: str = Field("connected", description="Redis 状态")
