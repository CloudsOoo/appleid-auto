"""
分享页模型
"""
from datetime import datetime
from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    Boolean,
    DateTime,
    ForeignKey,
    Index,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from app.db.database import Base


class SharePage(Base):
    """分享页表"""

    __tablename__ = "share_pages"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    # 基本信息
    title = Column(String(200), nullable=False)
    slug = Column(String(100), unique=True, nullable=False, index=True)
    description = Column(Text, nullable=True)

    # 访问控制
    password_hash = Column(String(255), nullable=True)  # 访问密码（加密）
    access_limit = Column(Integer, nullable=True)  # 访问次数限制（NULL 无限制）
    access_count = Column(Integer, default=0)

    # 有效期
    expires_at = Column(DateTime, nullable=True, index=True)  # 到期时间（NULL 永久）

    # 域名白名单
    allowed_domains = Column(JSONB, nullable=True)  # ["domain1.com", "domain2.com"]

    # 显示配置
    display_mode = Column(String(20), default="random")  # random, sequential, all
    template = Column(String(50), default="default")

    # 账号关联
    account_ids = Column(JSONB, nullable=False)  # [1, 2, 3, 4, 5]

    # ⭐ 自定义 HTML（核心功能）
    custom_html_header = Column(Text, nullable=True)  # 插入 <head>
    custom_html_body = Column(Text, nullable=True)    # 正文顶部
    custom_html_footer = Column(Text, nullable=True)  # body 底部

    # 状态
    is_active = Column(Boolean, default=True, index=True)

    # 统计
    total_views = Column(Integer, default=0)
    unique_views = Column(Integer, default=0)

    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关系
    user = relationship("User", back_populates="share_pages")
    logs = relationship("SharePageLog", back_populates="share_page", cascade="all, delete-orphan")

    # 索引
    __table_args__ = (
        Index("idx_share_pages_user_active", "user_id", "is_active"),
    )

    def is_expired(self) -> bool:
        """检查是否已过期"""
        if not self.expires_at:
            return False
        return datetime.utcnow() > self.expires_at

    def is_access_limit_reached(self) -> bool:
        """检查访问次数是否已达上限"""
        if not self.access_limit:
            return False
        return self.access_count >= self.access_limit

    def __repr__(self):
        return f"<SharePage(id={self.id}, slug='{self.slug}', title='{self.title}')>"


class SharePageLog(Base):
    """分享页访问日志表"""

    __tablename__ = "share_page_logs"

    id = Column(Integer, primary_key=True, index=True)
    share_page_id = Column(Integer, ForeignKey("share_pages.id", ondelete="CASCADE"), nullable=False, index=True)

    # 访问信息
    ip_address = Column(String(45), nullable=True, index=True)
    user_agent = Column(Text, nullable=True)
    referer = Column(String(500), nullable=True)

    # 地理位置
    country = Column(String(10), nullable=True)
    region = Column(String(50), nullable=True)
    city = Column(String(50), nullable=True)

    # 显示的账号
    shown_account_id = Column(Integer, nullable=True)

    # 访问结果
    access_granted = Column(Boolean, default=True)
    password_attempt = Column(Boolean, default=False)

    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    # 关系
    share_page = relationship("SharePage", back_populates="logs")

    def __repr__(self):
        return f"<SharePageLog(id={self.id}, page_id={self.share_page_id}, ip='{self.ip_address}')>"
