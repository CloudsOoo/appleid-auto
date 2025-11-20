"""
代理相关的 Pydantic Schemas
"""
from datetime import datetime
from typing import Optional, Literal
from pydantic import BaseModel, Field


# ========== 添加代理 ==========
class ProxyCreate(BaseModel):
    """添加代理 Schema"""
    proxy_type: Literal["http", "https", "socks5"] = Field(..., description="代理类型")
    host: str = Field(..., min_length=1, max_length=255, description="主机地址")
    port: int = Field(..., ge=1, le=65535, description="端口")
    username: Optional[str] = Field(None, max_length=100, description="用户名")
    password: Optional[str] = Field(None, max_length=255, description="密码")
    country: Optional[str] = Field(None, max_length=10, description="国家代码")
    region: Optional[str] = Field(None, max_length=50, description="地区")
    priority: int = Field(0, ge=0, le=10, description="优先级")

    class Config:
        json_schema_extra = {
            "example": {
                "proxy_type": "socks5",
                "host": "proxy.example.com",
                "port": 1080,
                "username": "user",
                "password": "pass",
                "country": "US",
                "priority": 1
            }
        }


# ========== 更新代理 ==========
class ProxyUpdate(BaseModel):
    """更新代理 Schema"""
    username: Optional[str] = Field(None)
    password: Optional[str] = Field(None)
    country: Optional[str] = Field(None)
    region: Optional[str] = Field(None)
    priority: Optional[int] = Field(None, ge=0, le=10)
    is_active: Optional[bool] = Field(None)


# ========== 代理响应 ==========
class ProxyResponse(BaseModel):
    """代理响应 Schema"""
    id: int
    proxy_type: str
    host: str
    port: int
    username: Optional[str]
    status: str
    is_active: bool
    success_count: int
    failure_count: int
    success_rate: float
    avg_response_time: Optional[int]
    country: Optional[str]
    region: Optional[str]
    priority: int
    last_checked_at: Optional[datetime]
    last_success_at: Optional[datetime]
    last_error: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


# ========== 代理测试响应 ==========
class ProxyTestResponse(BaseModel):
    """代理测试响应 Schema"""
    success: bool
    response_time: Optional[int]
    ip_address: Optional[str]
    country: Optional[str]
    error: Optional[str]


# ========== 代理列表查询 ==========
class ProxyListQuery(BaseModel):
    """代理列表查询 Schema"""
    page: int = Field(1, ge=1, description="页码")
    per_page: int = Field(20, ge=1, le=100, description="每页数量")
    status: Optional[str] = Field(None, description="状态过滤")
    proxy_type: Optional[str] = Field(None, description="类型过滤")
    country: Optional[str] = Field(None, description="国家过滤")
    is_active: Optional[bool] = Field(None, description="激活状态过滤")
