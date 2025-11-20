"""
系统模型
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


class SystemSetting(Base):
    """系统配置表"""

    __tablename__ = "system_settings"

    id = Column(Integer, primary_key=True, index=True)
    key = Column(String(100), unique=True, nullable=False, index=True)
    value = Column(Text, nullable=True)
    value_type = Column(String(20), default="string")  # string, integer, boolean, json

    category = Column(String(50), nullable=True, index=True)
    description = Column(Text, nullable=True)
    is_public = Column(Boolean, default=False)  # 是否公开（前端可访问）

    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def get_typed_value(self):
        """获取类型化的值"""
        if self.value is None:
            return None

        if self.value_type == "integer":
            return int(self.value)
        elif self.value_type == "boolean":
            return self.value.lower() in ("true", "1", "yes")
        elif self.value_type == "json":
            import json
            return json.loads(self.value)
        else:
            return self.value

    def __repr__(self):
        return f"<SystemSetting(key='{self.key}', value='{self.value}')>"


class APIKey(Base):
    """API 密钥表"""

    __tablename__ = "api_keys"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    # 密钥信息
    key_name = Column(String(100), nullable=True)
    api_key = Column(String(64), unique=True, nullable=False, index=True)
    api_secret = Column(String(64), nullable=False)

    # 权限范围
    scopes = Column(JSONB, nullable=True)  # ["accounts:read", "accounts:write", ...]

    # 限制
    rate_limit = Column(Integer, default=1000)  # 次/小时
    ip_whitelist = Column(JSONB, nullable=True)  # ["1.2.3.4", "5.6.7.8"]

    # 状态
    is_active = Column(Boolean, default=True, index=True)

    # 统计
    total_requests = Column(Integer, default=0)
    last_used_at = Column(DateTime, nullable=True)

    # 有效期
    expires_at = Column(DateTime, nullable=True)

    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关系
    user = relationship("User", back_populates="api_keys")

    def __repr__(self):
        return f"<APIKey(id={self.id}, name='{self.key_name}', user_id={self.user_id})>"


class OperationLog(Base):
    """操作日志表"""

    __tablename__ = "operation_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)

    # 操作信息
    action = Column(String(100), nullable=False, index=True)
    resource_type = Column(String(50), nullable=True, index=True)
    resource_id = Column(Integer, nullable=True)

    # 详情
    description = Column(Text, nullable=True)
    details = Column(JSONB, nullable=True)

    # 请求信息
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)

    # 结果
    status = Column(String(20), nullable=True)  # success, failed
    error_message = Column(Text, nullable=True)

    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    def __repr__(self):
        return f"<OperationLog(id={self.id}, action='{self.action}', user_id={self.user_id})>"
