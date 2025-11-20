"""
任务模型
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


class UnlockTask(Base):
    """解锁任务表"""

    __tablename__ = "unlock_tasks"

    id = Column(Integer, primary_key=True, index=True)
    account_id = Column(Integer, ForeignKey("apple_accounts.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    # 任务信息
    task_type = Column(String(50), nullable=False)  # unlock, disable_2fa, change_password, remove_devices
    task_id = Column(String(100), unique=True, nullable=True, index=True)  # Celery 任务 ID

    # 任务状态
    status = Column(String(50), default="pending", index=True)  # pending, processing, success, failed, cancelled
    priority = Column(Integer, default=0)

    # 执行信息
    node_id = Column(Integer, nullable=True)
    proxy_id = Column(Integer, nullable=True)

    # 结果
    result = Column(JSONB, nullable=True)
    error_message = Column(Text, nullable=True)
    retry_count = Column(Integer, default=0)
    max_retries = Column(Integer, default=3)

    # 时间信息
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    # 关系
    account = relationship("AppleAccount", back_populates="tasks")

    # 索引
    __table_args__ = (
        Index("idx_tasks_status_created", "status", "created_at"),
        Index("idx_tasks_account_status", "account_id", "status"),
    )

    def __repr__(self):
        return f"<UnlockTask(id={self.id}, type='{self.task_type}', status='{self.status}')>"
