"""
分享页相关的 Pydantic Schemas
"""
from datetime import datetime
from typing import Optional, Literal
from pydantic import BaseModel, Field, field_validator


# ========== 分享页创建 ==========
class SharePageCreate(BaseModel):
    """创建分享页 Schema"""
    title: str = Field(..., min_length=1, max_length=200, description="标题")
    slug: str = Field(..., min_length=3, max_length=100, description="URL 别名")
    description: Optional[str] = Field(None, description="描述")

    # 访问控制
    password: Optional[str] = Field(None, min_length=1, max_length=128, description="访问密码")
    access_limit: Optional[int] = Field(None, ge=1, description="访问次数限制")
    expires_at: Optional[datetime] = Field(None, description="到期时间")
    allowed_domains: Optional[list[str]] = Field(None, description="域名白名单")

    # 显示配置
    display_mode: Literal["random", "sequential", "all"] = Field("random", description="显示模式")
    template: str = Field("default", max_length=50, description="模板名称")

    # 账号关联
    account_ids: list[int] = Field(..., min_items=1, description="关联的 Apple ID")

    # 自定义 HTML
    custom_html_header: Optional[str] = Field(None, description="自定义 <head> 内容")
    custom_html_body: Optional[str] = Field(None, description="自定义 body 顶部内容")
    custom_html_footer: Optional[str] = Field(None, description="自定义 body 底部内容")

    is_active: bool = Field(True, description="是否启用")

    @field_validator("slug")
    @classmethod
    def validate_slug(cls, v: str) -> str:
        """验证 slug"""
        if not v.replace("-", "").replace("_", "").isalnum():
            raise ValueError("slug 只能包含字母、数字、连字符和下划线")
        return v.lower()

    class Config:
        json_schema_extra = {
            "example": {
                "title": "美区账号分享",
                "slug": "us-accounts",
                "description": "优质美区账号",
                "password": "pass123",
                "access_limit": 100,
                "display_mode": "random",
                "account_ids": [1, 2, 3, 4, 5],
                "custom_html_header": "<style>.custom { color: red; }</style>",
                "custom_html_body": "<div class=\"banner\">欢迎使用</div>",
                "custom_html_footer": "<footer>© 2025</footer>"
            }
        }


# ========== 分享页更新 ==========
class SharePageUpdate(BaseModel):
    """更新分享页 Schema"""
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None)
    password: Optional[str] = Field(None)
    access_limit: Optional[int] = Field(None, ge=1)
    expires_at: Optional[datetime] = Field(None)
    allowed_domains: Optional[list[str]] = Field(None)
    display_mode: Optional[Literal["random", "sequential", "all"]] = Field(None)
    template: Optional[str] = Field(None)
    account_ids: Optional[list[int]] = Field(None, min_items=1)
    custom_html_header: Optional[str] = Field(None)
    custom_html_body: Optional[str] = Field(None)
    custom_html_footer: Optional[str] = Field(None)
    is_active: Optional[bool] = Field(None)


# ========== 分享页响应 ==========
class SharePageResponse(BaseModel):
    """分享页响应 Schema"""
    id: int
    title: str
    slug: str
    description: Optional[str]
    share_url: str  # 完整的分享 URL
    has_password: bool
    access_limit: Optional[int]
    access_count: int
    expires_at: Optional[datetime]
    allowed_domains: Optional[list[str]]
    display_mode: str
    template: str
    account_ids: list[int]
    account_count: int  # 关联账号数量
    custom_html_header: Optional[str]
    custom_html_body: Optional[str]
    custom_html_footer: Optional[str]
    is_active: bool
    total_views: int
    unique_views: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ========== 分享页访问 ==========
class SharePageAccess(BaseModel):
    """访问分享页 Schema"""
    password: Optional[str] = Field(None, description="访问密码")


# ========== 分享页公开响应 ==========
class SharePagePublicResponse(BaseModel):
    """分享页公开响应 Schema"""
    title: str
    description: Optional[str]
    account: Optional[dict] = None  # {"apple_id": "xxx", "password": "xxx"}
    accounts: Optional[list[dict]] = None  # 如果 display_mode 为 all
    custom_html: Optional[dict] = None  # {"header": "...", "body": "...", "footer": "..."}
    template: str


# ========== 分享页日志响应 ==========
class SharePageLogResponse(BaseModel):
    """分享页访问日志响应 Schema"""
    id: int
    ip_address: Optional[str]
    country: Optional[str]
    region: Optional[str]
    city: Optional[str]
    shown_account_id: Optional[int]
    shown_apple_id: Optional[str]
    access_granted: bool
    password_attempt: bool
    user_agent: Optional[str]
    referer: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


# ========== 分享页列表查询 ==========
class SharePageListQuery(BaseModel):
    """分享页列表查询 Schema"""
    page: int = Field(1, ge=1, description="页码")
    per_page: int = Field(20, ge=1, le=100, description="每页数量")
    is_active: Optional[bool] = Field(None, description="激活状态过滤")
    search: Optional[str] = Field(None, description="搜索关键词")


# ========== 分享页统计响应 ==========
class SharePageStatsResponse(BaseModel):
    """分享页统计响应 Schema"""
    total_views: int
    unique_views: int
    access_count: int
    access_limit: Optional[int]
    remaining_access: Optional[int]
    top_countries: list[dict]  # [{"country": "CN", "count": 100}, ...]
    top_referers: list[dict]
    recent_visits: list[SharePageLogResponse]
