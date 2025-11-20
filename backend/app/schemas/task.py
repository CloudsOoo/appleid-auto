"""
任务相关的 Pydantic Schemas
"""
from datetime import datetime
from typing import Optional, Literal
from pydantic import BaseModel, Field


# ========== 创建解锁任务 ==========
class UnlockTaskCreate(BaseModel):
    """创建解锁任务 Schema"""
    account_ids: list[int] = Field(..., min_items=1, description="账号 ID 列表")
    task_type: Literal["unlock", "disable_2fa", "change_password", "remove_devices", "check_status"] = Field(
        ..., description="任务类型"
    )
    priority: int = Field(0, ge=0, le=10, description="优先级（0-10，越大越优先）")

    class Config:
        json_schema_extra = {
            "example": {
                "account_ids": [1, 2, 3],
                "task_type": "unlock",
                "priority": 1
            }
        }


# ========== 任务响应 ==========
class UnlockTaskResponse(BaseModel):
    """任务响应 Schema"""
    id: int
    task_id: Optional[str]
    account_id: int
    apple_id: Optional[str]  # 关联的 Apple ID
    task_type: str
    status: str
    priority: int
    node_id: Optional[int]
    node_name: Optional[str]
    proxy_id: Optional[int]
    result: Optional[dict]
    error_message: Optional[str]
    retry_count: int
    max_retries: int
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True


# ========== 任务列表查询 ==========
class TaskListQuery(BaseModel):
    """任务列表查询 Schema"""
    page: int = Field(1, ge=1, description="页码")
    per_page: int = Field(20, ge=1, le=100, description="每页数量")
    status: Optional[str] = Field(None, description="状态过滤")
    task_type: Optional[str] = Field(None, description="类型过滤")
    account_id: Optional[int] = Field(None, description="账号 ID 过滤")


# ========== 任务统计响应 ==========
class TaskStatsResponse(BaseModel):
    """任务统计响应 Schema"""
    total: int
    pending: int
    processing: int
    success: int
    failed: int
    cancelled: int
    success_rate: float
