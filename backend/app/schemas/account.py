"""
Apple ID 账号相关的 Pydantic Schemas
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field


# ========== Apple ID 创建 ==========
class AppleAccountCreate(BaseModel):
    """创建 Apple ID Schema"""
    apple_id: EmailStr = Field(..., description="Apple ID（邮箱）")
    password: str = Field(..., min_length=1, description="密码")
    security_questions: Optional[list[dict]] = Field(None, description="密保问题")
    tags: Optional[list[str]] = Field(None, description="标签")
    category: Optional[str] = Field(None, max_length=50, description="分类")
    note: Optional[str] = Field(None, description="备注")

    # 自动化配置
    auto_unlock: bool = Field(True, description="是否自动解锁")
    auto_disable_2fa: bool = Field(False, description="是否自动关闭2FA")
    auto_change_password: bool = Field(False, description="是否自动修改密码")
    auto_remove_devices: bool = Field(False, description="是否自动删除设备")
    check_interval: int = Field(3600, ge=300, description="检测间隔（秒）")

    class Config:
        json_schema_extra = {
            "example": {
                "apple_id": "example@icloud.com",
                "password": "password123",
                "security_questions": [
                    {
                        "question": "您最喜欢的颜色是什么?",
                        "answer": "蓝色"
                    }
                ],
                "tags": ["工作", "美区"],
                "auto_unlock": True,
                "check_interval": 3600
            }
        }


# ========== Apple ID 更新 ==========
class AppleAccountUpdate(BaseModel):
    """更新 Apple ID Schema"""
    password: Optional[str] = Field(None, description="密码")
    security_questions: Optional[list[dict]] = Field(None, description="密保问题")
    tags: Optional[list[str]] = Field(None, description="标签")
    category: Optional[str] = Field(None, description="分类")
    note: Optional[str] = Field(None, description="备注")
    auto_unlock: Optional[bool] = Field(None, description="是否自动解锁")
    auto_disable_2fa: Optional[bool] = Field(None, description="是否自动关闭2FA")
    auto_change_password: Optional[bool] = Field(None, description="是否自动修改密码")
    auto_remove_devices: Optional[bool] = Field(None, description="是否自动删除设备")
    check_interval: Optional[int] = Field(None, ge=300, description="检测间隔（秒）")


# ========== Apple ID 响应 ==========
class AppleAccountResponse(BaseModel):
    """Apple ID 响应 Schema"""
    id: int
    apple_id: str
    status: str
    lock_status: bool
    two_factor_enabled: bool
    app_store_country: Optional[str]
    app_store_language: Optional[str]
    account_name: Optional[str]
    devices_count: int
    has_lost_mode: bool
    tags: Optional[list[str]]
    category: Optional[str]
    auto_unlock: bool
    auto_disable_2fa: bool
    auto_change_password: bool
    auto_remove_devices: bool
    check_interval: int
    last_checked_at: Optional[datetime]
    next_check_at: Optional[datetime]
    last_unlocked_at: Optional[datetime]
    unlock_count: int
    last_error: Optional[str]
    error_count: int
    note: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ========== Apple ID 详细响应（含密码）==========
class AppleAccountDetailResponse(AppleAccountResponse):
    """Apple ID 详细响应（含密码）"""
    current_password: Optional[str] = None
    security_questions: Optional[list[dict]] = None


# ========== 密码历史响应 ==========
class PasswordHistoryResponse(BaseModel):
    """密码历史响应 Schema"""
    id: int
    password: str
    changed_by: str
    created_at: datetime

    class Config:
        from_attributes = True


# ========== 批量导入 ==========
class AppleAccountImport(BaseModel):
    """批量导入 Apple ID Schema"""
    accounts: list[dict] = Field(..., description="账号列表")

    class Config:
        json_schema_extra = {
            "example": {
                "accounts": [
                    {
                        "apple_id": "example1@icloud.com",
                        "password": "password123",
                        "tags": ["工作", "美区"],
                        "note": "测试账号1"
                    },
                    {
                        "apple_id": "example2@icloud.com",
                        "password": "password456",
                        "tags": ["个人"],
                        "note": "测试账号2"
                    }
                ]
            }
        }


# ========== 批量导入响应 ==========
class AppleAccountImportResponse(BaseModel):
    """批量导入响应 Schema"""
    total: int
    success: int
    failed: int
    errors: list[dict] = []
    message: str = "导入完成"


# ========== 账号列表查询 ==========
class AppleAccountListQuery(BaseModel):
    """账号列表查询 Schema"""
    page: int = Field(1, ge=1, description="页码")
    per_page: int = Field(20, ge=1, le=100, description="每页数量")
    status: Optional[str] = Field(None, description="状态过滤")
    lock_status: Optional[bool] = Field(None, description="锁定状态过滤")
    tag: Optional[str] = Field(None, description="标签过滤")
    category: Optional[str] = Field(None, description="分类过滤")
    search: Optional[str] = Field(None, description="搜索关键词")


# ========== 手动触发检测 ==========
class TriggerCheck(BaseModel):
    """手动触发检测 Schema"""
    force: bool = Field(False, description="是否强制检测（忽略间隔限制）")
