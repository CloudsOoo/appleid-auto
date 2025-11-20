"""
用户权限模型
"""
from datetime import datetime, date
from sqlalchemy import (
    Column,
    Integer,
    Boolean,
    DateTime,
    Date,
    ForeignKey,
    Index,
)
from sqlalchemy.orm import relationship

from app.db.database import Base


class UserPermission(Base):
    """用户权限表"""

    __tablename__ = "user_permissions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False, index=True)
    package_id = Column(Integer, ForeignKey("packages.id"), nullable=True)

    # 权限配置（继承自套餐，可自定义覆盖）
    max_accounts = Column(Integer, default=10)
    max_share_pages = Column(Integer, default=5)
    max_nodes = Column(Integer, default=1)
    min_unlock_interval = Column(Integer, default=3600)

    allow_custom_html = Column(Boolean, default=False)
    allow_view_password_history = Column(Boolean, default=False)
    allow_batch_import = Column(Boolean, default=True)
    allow_api_access = Column(Boolean, default=False)

    max_unlock_per_day = Column(Integer, default=100)
    max_import_per_time = Column(Integer, default=100)

    # 授权时间
    authorized_at = Column(DateTime, nullable=True)
    expires_at = Column(DateTime, nullable=True, index=True)

    # 使用统计
    accounts_count = Column(Integer, default=0)
    share_pages_count = Column(Integer, default=0)
    nodes_count = Column(Integer, default=0)
    unlock_count_today = Column(Integer, default=0)
    last_reset_date = Column(Date, nullable=True)

    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关系
    user = relationship("User", back_populates="permissions")
    package = relationship("Package", back_populates="user_permissions")

    def is_expired(self) -> bool:
        """检查是否已过期"""
        if not self.expires_at:
            return False
        return datetime.utcnow() > self.expires_at

    def reset_daily_counters(self):
        """重置每日计数器"""
        today = date.today()
        if not self.last_reset_date or self.last_reset_date < today:
            self.unlock_count_today = 0
            self.last_reset_date = today

    def __repr__(self):
        return f"<UserPermission(id={self.id}, user_id={self.user_id}, max_accounts={self.max_accounts})>"
