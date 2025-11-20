"""
卡密模型
"""
from datetime import datetime
from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    DateTime,
    ForeignKey,
    Index,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from app.db.database import Base


class Card(Base):
    """卡密表"""

    __tablename__ = "cards"

    id = Column(Integer, primary_key=True, index=True)
    card_code = Column(String(64), unique=True, nullable=False, index=True)
    card_type = Column(String(20), nullable=False)  # time, usage, permanent

    # 套餐关联
    package_id = Column(Integer, ForeignKey("packages.id"), nullable=True)

    # 时长/次数配置
    duration_days = Column(Integer, nullable=True)  # time类型使用
    usage_count = Column(Integer, nullable=True)  # usage类型使用

    # 状态
    status = Column(String(20), default="unused", index=True)  # unused, used, expired, revoked

    # 激活信息
    activated_by = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    activated_at = Column(DateTime, nullable=True)
    activated_ip = Column(String(45), nullable=True)
    expires_at = Column(DateTime, nullable=True)

    # 使用统计
    used_count = Column(Integer, default=0)

    # 批次信息
    batch_id = Column(String(50), nullable=True, index=True)

    # 备注
    note = Column(Text, nullable=True)

    # 创建信息
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关系
    package = relationship("Package", back_populates="cards")
    activated_user = relationship("User", back_populates="cards", foreign_keys=[activated_by])
    logs = relationship("CardLog", back_populates="card", cascade="all, delete-orphan")

    # 索引
    __table_args__ = (
        Index("idx_cards_status_type", "status", "card_type"),
    )

    def __repr__(self):
        return f"<Card(id={self.id}, code='{self.card_code}', type='{self.card_type}', status='{self.status}')>"


class CardLog(Base):
    """卡密使用日志表"""

    __tablename__ = "card_logs"

    id = Column(Integer, primary_key=True, index=True)
    card_id = Column(Integer, ForeignKey("cards.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)

    action = Column(String(50), nullable=False, index=True)  # activate, revoke, extend

    # 操作详情
    details = Column(JSONB, nullable=True)
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)

    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    # 关系
    card = relationship("Card", back_populates="logs")

    def __repr__(self):
        return f"<CardLog(id={self.id}, card_id={self.card_id}, action='{self.action}')>"
