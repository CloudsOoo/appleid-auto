"""
节点模型
"""
from datetime import datetime, timedelta
from decimal import Decimal
from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    Boolean,
    DateTime,
    Numeric,
    ForeignKey,
    Index,
)
from sqlalchemy.orm import relationship

from app.db.database import Base


class Node(Base):
    """解锁节点表"""

    __tablename__ = "nodes"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    # 节点信息
    node_name = Column(String(100), nullable=False)
    node_key = Column(String(64), unique=True, nullable=False)
    node_url = Column(String(255), nullable=True)

    # 节点状态
    status = Column(String(50), default="offline", index=True)  # online, offline, error
    is_active = Column(Boolean, default=True, index=True)

    # 性能信息
    cpu_usage = Column(Numeric(5, 2), nullable=True)
    memory_usage = Column(Numeric(5, 2), nullable=True)
    task_queue_size = Column(Integer, default=0)

    # 统计信息
    total_tasks = Column(Integer, default=0)
    success_tasks = Column(Integer, default=0)
    failed_tasks = Column(Integer, default=0)

    # 健康检查
    last_heartbeat_at = Column(DateTime, nullable=True, index=True)
    last_error = Column(Text, nullable=True)

    # 地理位置
    country = Column(String(10), nullable=True)
    region = Column(String(50), nullable=True)

    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关系
    user = relationship("User", back_populates="nodes")

    def is_online(self) -> bool:
        """判断节点是否在线"""
        if not self.last_heartbeat_at:
            return False
        from app.core.config import settings
        threshold = datetime.utcnow() - timedelta(seconds=settings.NODE_OFFLINE_THRESHOLD)
        return self.last_heartbeat_at > threshold

    def __repr__(self):
        return f"<Node(id={self.id}, name='{self.node_name}', status='{self.status}')>"
