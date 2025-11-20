"""
卡密相关的 Pydantic Schemas
"""
from datetime import datetime
from typing import Optional, Literal
from pydantic import BaseModel, Field


# ========== 卡密激活 ==========
class CardActivate(BaseModel):
    """卡密激活 Schema"""
    card_code: str = Field(..., min_length=10, max_length=64, description="卡密代码")

    class Config:
        json_schema_extra = {
            "example": {
                "card_code": "AAAA-BBBB-CCCC-DDDD"
            }
        }


# ========== 卡密生成 ==========
class CardGenerate(BaseModel):
    """卡密生成 Schema"""
    card_type: Literal["time", "usage", "permanent"] = Field(..., description="卡密类型")
    package_id: int = Field(..., description="套餐 ID")
    duration_days: Optional[int] = Field(None, ge=1, le=3650, description="有效天数（time类型必填）")
    usage_count: Optional[int] = Field(None, ge=1, le=100000, description="使用次数（usage类型必填）")
    quantity: int = Field(1, ge=1, le=1000, description="生成数量")
    batch_id: Optional[str] = Field(None, max_length=50, description="批次 ID")
    note: Optional[str] = Field(None, max_length=500, description="备注")

    class Config:
        json_schema_extra = {
            "example": {
                "card_type": "time",
                "package_id": 2,
                "duration_days": 30,
                "quantity": 10,
                "batch_id": "BATCH_2025_001",
                "note": "双十一活动"
            }
        }


# ========== 卡密响应 ==========
class CardResponse(BaseModel):
    """卡密响应 Schema"""
    id: int
    card_code: str
    card_type: str
    package_id: Optional[int]
    package_name: Optional[str] = None
    duration_days: Optional[int]
    usage_count: Optional[int]
    status: str
    activated_by: Optional[int]
    activated_by_username: Optional[str] = None
    activated_at: Optional[datetime]
    activated_ip: Optional[str]
    expires_at: Optional[datetime]
    used_count: int
    batch_id: Optional[str]
    note: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


# ========== 卡密批量生成响应 ==========
class CardGenerateResponse(BaseModel):
    """卡密批量生成响应 Schema"""
    batch_id: str
    quantity: int
    cards: list[str]
    message: str = "生成成功"


# ========== 卡密激活响应 ==========
class CardActivateResponse(BaseModel):
    """卡密激活响应 Schema"""
    card_type: str
    duration_days: Optional[int]
    usage_count: Optional[int]
    package: dict
    expires_at: Optional[datetime]
    message: str = "激活成功"


# ========== 卡密状态响应 ==========
class CardStatusResponse(BaseModel):
    """卡密状态响应 Schema"""
    is_activated: bool
    card_type: Optional[str]
    package_name: Optional[str]
    activated_at: Optional[datetime]
    expires_at: Optional[datetime]
    days_remaining: Optional[int]
    usage_count: Optional[int]
    used_count: Optional[int]


# ========== 卡密日志响应 ==========
class CardLogResponse(BaseModel):
    """卡密日志响应 Schema"""
    id: int
    card_id: int
    user_id: Optional[int]
    username: Optional[str]
    action: str
    details: Optional[dict]
    ip_address: Optional[str]
    user_agent: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


# ========== 卡密列表查询 ==========
class CardListQuery(BaseModel):
    """卡密列表查询 Schema"""
    page: int = Field(1, ge=1, description="页码")
    per_page: int = Field(20, ge=1, le=100, description="每页数量")
    status: Optional[str] = Field(None, description="状态过滤")
    card_type: Optional[str] = Field(None, description="类型过滤")
    batch_id: Optional[str] = Field(None, description="批次过滤")
    search: Optional[str] = Field(None, description="搜索卡密代码")


# ========== 卡密作废 ==========
class CardRevoke(BaseModel):
    """卡密作废 Schema"""
    reason: str = Field(..., min_length=1, max_length=500, description="作废原因")


# ========== 卡密延期 ==========
class CardExtend(BaseModel):
    """卡密延期 Schema"""
    extend_days: int = Field(..., ge=1, le=3650, description="延长天数")
    reason: Optional[str] = Field(None, max_length=500, description="延期原因")
