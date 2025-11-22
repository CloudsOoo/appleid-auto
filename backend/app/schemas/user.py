"""
用户相关的 Pydantic Schemas
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field, field_validator


# ========== 用户注册 ==========
class UserCreate(BaseModel):
    """用户注册 Schema"""
    username: str = Field(..., min_length=3, max_length=50, description="用户名")
    email: EmailStr = Field(..., description="邮箱")
    password: str = Field(..., min_length=8, max_length=128, description="密码")
    full_name: Optional[str] = Field(None, max_length=100, description="全名")

    @field_validator("username")
    @classmethod
    def validate_username(cls, v: str) -> str:
        """验证用户名"""
        if not v.isalnum() and "_" not in v:
            raise ValueError("用户名只能包含字母、数字和下划线")
        return v

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        """验证密码强度"""
        if not any(c.isupper() for c in v):
            raise ValueError("密码必须包含至少一个大写字母")
        if not any(c.islower() for c in v):
            raise ValueError("密码必须包含至少一个小写字母")
        if not any(c.isdigit() for c in v):
            raise ValueError("密码必须包含至少一个数字")
        return v


# ========== 用户登录 ==========
class UserLogin(BaseModel):
    """用户登录 Schema"""
    username: str = Field(..., description="用户名或邮箱")
    password: str = Field(..., description="密码")
    otp_code: Optional[str] = Field(None, description="2FA 验证码")


# ========== 用户更新 ==========
class UserUpdate(BaseModel):
    """用户更新 Schema"""
    full_name: Optional[str] = Field(None, max_length=100)
    phone: Optional[str] = Field(None, max_length=20)
    avatar_url: Optional[str] = Field(None, max_length=255)


# ========== 修改密码 ==========
class ChangePassword(BaseModel):
    """修改密码 Schema"""
    old_password: str = Field(..., description="旧密码")
    new_password: str = Field(..., min_length=8, description="新密码")

    @field_validator("new_password")
    @classmethod
    def validate_new_password(cls, v: str) -> str:
        """验证新密码强度"""
        if not any(c.isupper() for c in v):
            raise ValueError("密码必须包含至少一个大写字母")
        if not any(c.islower() for c in v):
            raise ValueError("密码必须包含至少一个小写字母")
        if not any(c.isdigit() for c in v):
            raise ValueError("密码必须包含至少一个数字")
        return v


# ========== 用户权限 Schema ==========
class UserPermissionResponse(BaseModel):
    """用户权限响应 Schema"""
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
    authorized_at: Optional[datetime]
    expires_at: Optional[datetime]
    accounts_count: int
    share_pages_count: int
    nodes_count: int
    unlock_count_today: int

    class Config:
        from_attributes = True


# ========== 用户响应 ==========
class UserResponse(BaseModel):
    """用户响应 Schema"""
    id: int
    username: str
    email: str
    role: str
    is_active: bool
    is_verified: bool
    two_factor_enabled: bool
    full_name: Optional[str]
    phone: Optional[str]
    avatar_url: Optional[str]
    created_at: datetime
    last_login_at: Optional[datetime]
    permissions: Optional[UserPermissionResponse] = None

    class Config:
        from_attributes = True


# ========== JWT Token ==========
class Token(BaseModel):
    """JWT Token Schema"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserResponse


class TokenPayload(BaseModel):
    """Token 载荷 Schema"""
    sub: int  # 用户 ID
    type: str  # access 或 refresh
    exp: Optional[datetime] = None


# ========== 2FA 相关 ==========
class Enable2FAResponse(BaseModel):
    """启用 2FA 响应"""
    secret: str
    qr_code: str
    backup_codes: list[str]


class Verify2FA(BaseModel):
    """验证 2FA"""
    code: str = Field(..., min_length=6, max_length=6, description="6位验证码")


# ========== 用户列表查询 ==========
class UserListQuery(BaseModel):
    """用户列表查询 Schema"""
    page: int = Field(1, ge=1, description="页码")
    per_page: int = Field(20, ge=1, le=100, description="每页数量")
    role: Optional[str] = Field(None, description="角色过滤")
    is_active: Optional[bool] = Field(None, description="激活状态过滤")
    search: Optional[str] = Field(None, description="搜索关键词")


# ========== 兼容别名（用于 API 导入一致性） ==========
# 这些别名确保 auth.py 等模块的导入能够正常工作
ChangePasswordRequest = ChangePassword
Verify2FARequest = Verify2FA
TokenResponse = Token
