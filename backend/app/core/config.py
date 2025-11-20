"""
应用配置模块
"""
from typing import List, Optional
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """应用配置"""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False
    )

    # 应用配置
    APP_NAME: str = "Apple ID Auto"
    APP_VERSION: str = "1.0.0"
    APP_ENV: str = "development"
    DEBUG: bool = True
    SECRET_KEY: str

    # 服务器配置
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    WORKERS: int = 4

    # 数据库配置
    DATABASE_URL: str
    DATABASE_POOL_SIZE: int = 20
    DATABASE_MAX_OVERFLOW: int = 10

    # Redis 配置
    REDIS_URL: str = "redis://localhost:6379/0"
    REDIS_PASSWORD: Optional[str] = None

    # Celery 配置
    CELERY_BROKER_URL: str = "redis://localhost:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/2"

    # JWT 配置
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # CORS 配置
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:5173"]

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v):
        if isinstance(v, str):
            return [i.strip() for i in v.split(",")]
        return v

    @property
    def ALLOWED_ORIGINS(self) -> List[str]:
        """获取允许的跨域源列表（兼容属性）"""
        return self.CORS_ORIGINS

    @property
    def ENVIRONMENT(self) -> str:
        """获取当前环境（兼容属性）"""
        return self.APP_ENV

    @property
    def ENABLE_RATE_LIMIT(self) -> bool:
        """是否启用限流（兼容属性）"""
        return self.RATE_LIMIT_ENABLED

    # 文件上传
    MAX_UPLOAD_SIZE: int = 10485760  # 10MB
    UPLOAD_DIR: str = "./uploads"

    # 日志配置
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "./logs/app.log"

    # 限流配置
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_PER_MINUTE: int = 60

    # 邮件配置
    SMTP_HOST: Optional[str] = None
    SMTP_PORT: int = 587
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    EMAIL_FROM: Optional[str] = None

    # Apple API 配置
    APPLE_API_TIMEOUT: int = 30
    APPLE_API_MAX_RETRIES: int = 3

    # 代理配置
    PROXY_CHECK_INTERVAL: int = 300  # 5分钟
    PROXY_TIMEOUT: int = 10

    # 节点配置
    NODE_HEARTBEAT_INTERVAL: int = 60  # 1分钟
    NODE_OFFLINE_THRESHOLD: int = 180  # 3分钟

    # 任务配置
    DEFAULT_CHECK_INTERVAL: int = 3600  # 1小时
    MAX_UNLOCK_RETRIES: int = 3

    # 安全配置
    MAX_LOGIN_ATTEMPTS: int = 5
    LOGIN_ATTEMPT_TIMEOUT: int = 300  # 5分钟
    CARD_MAX_ATTEMPTS: int = 3
    CARD_ATTEMPT_TIMEOUT: int = 3600  # 1小时

    # HTML 过滤白名单
    ALLOWED_HTML_TAGS: str = "div,span,p,a,img,h1,h2,h3,h4,h5,h6,ul,ol,li,br,hr,strong,em,code,pre,blockquote"
    ALLOWED_HTML_ATTRIBUTES: str = "class,id,style,href,src,alt,title"

    # 分享页配置
    SHARE_PAGE_DEFAULT_TEMPLATE: str = "default"
    SHARE_PAGE_MAX_CUSTOM_HTML_SIZE: int = 102400  # 100KB

    # 管理员配置
    ADMIN_USERNAME: str = "admin"
    ADMIN_EMAIL: str = "admin@appleid-auto.local"
    ADMIN_PASSWORD: str = "Admin@123456"

    @property
    def allowed_html_tags_list(self) -> List[str]:
        """获取允许的 HTML 标签列表"""
        return [tag.strip() for tag in self.ALLOWED_HTML_TAGS.split(",")]

    @property
    def allowed_html_attributes_list(self) -> List[str]:
        """获取允许的 HTML 属性列表"""
        return [attr.strip() for attr in self.ALLOWED_HTML_ATTRIBUTES.split(",")]


# 创建全局配置实例
settings = Settings()
