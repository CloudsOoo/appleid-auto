"""
套餐模板模型
"""
from datetime import datetime
from decimal import Decimal
from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    Boolean,
    DateTime,
    Numeric,
    Index,
)
from sqlalchemy.orm import relationship

from app.db.database import Base


class Package(Base):
    """套餐模板表"""

    __tablename__ = "packages"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)

    # 权限配置
    max_accounts = Column(Integer, default=10)
    max_share_pages = Column(Integer, default=5)
    max_nodes = Column(Integer, default=1)
    min_unlock_interval = Column(Integer, default=3600)  # 秒

    # 功能权限
    allow_custom_html = Column(Boolean, default=False)
    allow_view_password_history = Column(Boolean, default=False)
    allow_batch_import = Column(Boolean, default=True)
    allow_api_access = Column(Boolean, default=False)

    # 配额
    max_unlock_per_day = Column(Integer, default=100)
    max_import_per_time = Column(Integer, default=100)

    # 价格信息
    price = Column(Numeric(10, 2), nullable=True)
    currency = Column(String(10), default="CNY")

    # 状态
    is_active = Column(Boolean, default=True, index=True)
    sort_order = Column(Integer, default=0)

    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关系
    cards = relationship("Card", back_populates="package")
    user_permissions = relationship("UserPermission", back_populates="package")

    def __repr__(self):
        return f"<Package(id={self.id}, name='{self.name}', price={self.price})>"
