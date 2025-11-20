"""
节点相关的 Pydantic Schemas
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, HttpUrl


# ========== 注册节点 ==========
class NodeRegister(BaseModel):
    """注册节点 Schema"""
    node_name: str = Field(..., min_length=1, max_length=100, description="节点名称")
    node_url: Optional[HttpUrl] = Field(None, description="节点 API 地址")
    country: Optional[str] = Field(None, max_length=10, description="国家代码")
    region: Optional[str] = Field(None, max_length=50, description="地区")

    class Config:
        json_schema_extra = {
            "example": {
                "node_name": "解锁节点1",
                "node_url": "https://node1.example.com",
                "country": "US",
                "region": "West"
            }
        }


# ========== 节点心跳 ==========
class NodeHeartbeat(BaseModel):
    """节点心跳 Schema"""
    cpu_usage: float = Field(..., ge=0, le=100, description="CPU 使用率")
    memory_usage: float = Field(..., ge=0, le=100, description="内存使用率")
    task_queue_size: int = Field(0, ge=0, description="任务队列大小")

    class Config:
        json_schema_extra = {
            "example": {
                "cpu_usage": 35.5,
                "memory_usage": 60.2,
                "task_queue_size": 5
            }
        }


# ========== 节点响应 ==========
class NodeResponse(BaseModel):
    """节点响应 Schema"""
    id: int
    node_name: str
    node_key: str
    node_url: Optional[str]
    status: str
    is_active: bool
    cpu_usage: Optional[float]
    memory_usage: Optional[float]
    task_queue_size: int
    total_tasks: int
    success_tasks: int
    failed_tasks: int
    success_rate: float
    last_heartbeat_at: Optional[datetime]
    last_error: Optional[str]
    country: Optional[str]
    region: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


# ========== 节点列表查询 ==========
class NodeListQuery(BaseModel):
    """节点列表查询 Schema"""
    page: int = Field(1, ge=1, description="页码")
    per_page: int = Field(20, ge=1, le=100, description="每页数量")
    status: Optional[str] = Field(None, description="状态过滤")
    is_active: Optional[bool] = Field(None, description="激活状态过滤")
    country: Optional[str] = Field(None, description="国家过滤")
