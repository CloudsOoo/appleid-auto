"""
Apple ID 账号模型
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
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from app.db.database import Base


class AppleAccount(Base):
    """Apple ID 账号表"""

    __tablename__ = "apple_accounts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    # 账号信息
    apple_id = Column(String(100), nullable=False, index=True)
    current_password = Column(String(255), nullable=True)  # 加密存储
    security_questions = Column(JSONB, nullable=True)  # 密保问题（加密）

    # 账号状态
    status = Column(String(50), default="normal", index=True)  # normal, locked, processing, error
    lock_status = Column(Boolean, default=False, index=True)
    two_factor_enabled = Column(Boolean, default=False)

    # App Store 信息
    app_store_country = Column(String(10), nullable=True)
    app_store_language = Column(String(10), nullable=True)
    account_name = Column(String(100), nullable=True)

    # 设备信息
    devices_count = Column(Integer, default=0)
    has_lost_mode = Column(Boolean, default=False)

    # 分类标签
    tags = Column(JSONB, nullable=True)  # ["tag1", "tag2"]
    category = Column(String(50), nullable=True)

    # 自动化配置
    auto_unlock = Column(Boolean, default=True)
    auto_disable_2fa = Column(Boolean, default=False)
    auto_change_password = Column(Boolean, default=False)
    auto_remove_devices = Column(Boolean, default=False)

    # 检测配置
    check_interval = Column(Integer, default=3600)  # 秒
    last_checked_at = Column(DateTime, nullable=True)
    next_check_at = Column(DateTime, nullable=True, index=True)

    # 操作记录
    last_unlocked_at = Column(DateTime, nullable=True)
    unlock_count = Column(Integer, default=0)
    last_error = Column(Text, nullable=True)
    error_count = Column(Integer, default=0)

    # 备注
    note = Column(Text, nullable=True)

    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关系
    user = relationship("User", back_populates="apple_accounts")
    password_history = relationship("PasswordHistory", back_populates="account", cascade="all, delete-orphan")
    tasks = relationship("UnlockTask", back_populates="account", cascade="all, delete-orphan")

    # 索引和约束
    __table_args__ = (
        Index("idx_accounts_user_status", "user_id", "status"),
        Index("idx_accounts_auto_unlock", "user_id", "auto_unlock", "next_check_at"),
        UniqueConstraint("user_id", "apple_id", name="uq_user_apple_id"),
    )

    def __repr__(self):
        return f"<AppleAccount(id={self.id}, apple_id='{self.apple_id}', status='{self.status}')>"


class PasswordHistory(Base):
    """密码历史表"""

    __tablename__ = "password_history"

    id = Column(Integer, primary_key=True, index=True)
    account_id = Column(Integer, ForeignKey("apple_accounts.id", ondelete="CASCADE"), nullable=False, index=True)

    password_hash = Column(String(255), nullable=False)  # 加密存储
    changed_by = Column(String(50), default="system")  # system, manual, auto

    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    # 关系
    account = relationship("AppleAccount", back_populates="password_history")

    def __repr__(self):
        return f"<PasswordHistory(id={self.id}, account_id={self.account_id}, changed_by='{self.changed_by}')>"
