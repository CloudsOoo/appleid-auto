"""
代理池模型
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
from sqlalchemy.orm import relationship

from app.db.database import Base


class Proxy(Base):
    """代理池表"""

    __tablename__ = "proxy_pool"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)  # NULL 为公共代理

    # 代理信息
    proxy_type = Column(String(20), nullable=False)  # http, https, socks5
    host = Column(String(255), nullable=False)
    port = Column(Integer, nullable=False)
    username = Column(String(100), nullable=True)
    password = Column(String(255), nullable=True)

    # 代理状态
    status = Column(String(50), default="active", index=True)  # active, failed, testing
    is_active = Column(Boolean, default=True, index=True)

    # 性能统计
    success_count = Column(Integer, default=0)
    failure_count = Column(Integer, default=0)
    avg_response_time = Column(Integer, nullable=True)  # 毫秒

    # 健康检查
    last_checked_at = Column(DateTime, nullable=True)
    last_success_at = Column(DateTime, nullable=True)
    last_error = Column(Text, nullable=True)

    # 地理位置
    country = Column(String(10), nullable=True)
    region = Column(String(50), nullable=True)

    # 优先级
    priority = Column(Integer, default=0, index=True)

    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关系
    user = relationship("User", back_populates="proxies")

    @property
    def proxy_url(self) -> str:
        """获取代理 URL"""
        if self.username and self.password:
            return f"{self.proxy_type}://{self.username}:{self.password}@{self.host}:{self.port}"
        return f"{self.proxy_type}://{self.host}:{self.port}"

    @property
    def success_rate(self) -> float:
        """获取成功率"""
        total = self.success_count + self.failure_count
        if total == 0:
            return 0.0
        return (self.success_count / total) * 100

    def __repr__(self):
        return f"<Proxy(id={self.id}, type='{self.proxy_type}', host='{self.host}:{self.port}')>"
