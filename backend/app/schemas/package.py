"""
套餐相关的 Pydantic Schemas
"""
from datetime import datetime
from typing import Optional
from decimal import Decimal
from pydantic import BaseModel, Field


# ========== 创建套餐 ==========
class PackageCreate(BaseModel):
    """创建套餐 Schema"""
    name: str = Field(..., min_length=1, max_length=100, description="套餐名称")
    description: Optional[str] = Field(None, description="套餐描述")

    # 权限配置
    max_accounts: int = Field(10, ge=1, description="最大账号数")
    max_share_pages: int = Field(5, ge=1, description="最大分享页数")
    max_nodes: int = Field(1, ge=1, description="最大节点数")
    min_unlock_interval: int = Field(3600, ge=60, description="最短解锁间隔(秒)")

    # 功能权限
    allow_custom_html: bool = Field(False, description="允许自定义 HTML")
    allow_view_password_history: bool = Field(False, description="允许查看历史密码")
    allow_batch_import: bool = Field(True, description="允许批量导入")
    allow_api_access: bool = Field(False, description="允许 API 访问")

    # 配额
    max_unlock_per_day: int = Field(100, ge=1, description="每日最大解锁次数")
    max_import_per_time: int = Field(100, ge=1, description="单次导入限制")

    # 价格
    price: Optional[Decimal] = Field(None, ge=0, description="价格")
    currency: str = Field("CNY", max_length=10, description="货币")

    sort_order: int = Field(0, description="排序")

    class Config:
        json_schema_extra = {
            "example": {
                "name": "专业版",
                "description": "适合中小企业",
                "max_accounts": 200,
                "max_share_pages": 20,
                "max_nodes": 5,
                "allow_custom_html": True,
                "price": 299.00
            }
        }


# ========== 更新套餐 ==========
class PackageUpdate(BaseModel):
    """更新套餐 Schema"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None)
    max_accounts: Optional[int] = Field(None, ge=1)
    max_share_pages: Optional[int] = Field(None, ge=1)
    max_nodes: Optional[int] = Field(None, ge=1)
    min_unlock_interval: Optional[int] = Field(None, ge=60)
    allow_custom_html: Optional[bool] = Field(None)
    allow_view_password_history: Optional[bool] = Field(None)
    allow_batch_import: Optional[bool] = Field(None)
    allow_api_access: Optional[bool] = Field(None)
    max_unlock_per_day: Optional[int] = Field(None, ge=1)
    max_import_per_time: Optional[int] = Field(None, ge=1)
    price: Optional[Decimal] = Field(None, ge=0)
    currency: Optional[str] = Field(None)
    is_active: Optional[bool] = Field(None)
    sort_order: Optional[int] = Field(None)


# ========== 套餐响应 ==========
class PackageResponse(BaseModel):
    """套餐响应 Schema"""
    id: int
    name: str
    description: Optional[str]
    max_accounts: int
    max_share_pages: int
    max_nodes: int
    min_unlock_interval: int
    allow_custom_html: bool
    allow_view_password_history: bool
    allow_batch_import: bool
    allow_api_access: bool
    max_unlock_per_day: int
    max_import_per_time: int
    price: Optional[Decimal]
    currency: str
    is_active: bool
    sort_order: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
