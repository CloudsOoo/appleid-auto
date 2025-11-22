"""
测试配置文件

职责：
- 定义全局 fixtures
- 配置测试环境
- 提供测试数据工厂
- Mock 外部依赖

使用方式：
- pytest 自动加载此文件
- fixtures 可在所有测试文件中使用
"""

import os
import sys
from datetime import datetime, timedelta
from typing import Generator, AsyncGenerator, Dict, Any
from unittest.mock import MagicMock, AsyncMock, patch

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

# 设置测试环境变量（必须在导入 app 之前）
os.environ["APP_ENV"] = "testing"
os.environ["DEBUG"] = "true"
os.environ["SECRET_KEY"] = "test-secret-key-for-testing-only"
os.environ["JWT_SECRET_KEY"] = "test-jwt-secret-key-for-testing"
os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["REDIS_URL"] = "redis://localhost:6379/15"

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# ==========================================
# 数据库 Fixtures
# ==========================================

@pytest.fixture(scope="session")
def engine():
    """创建测试数据库引擎（内存 SQLite）"""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=False
    )
    yield engine
    engine.dispose()


@pytest.fixture(scope="function")
def db_session(engine) -> Generator[Session, None, None]:
    """创建数据库会话（每个测试函数独立）"""
    # 导入 models 以创建表
    from app.models import Base

    # 创建所有表
    Base.metadata.create_all(bind=engine)

    # 创建会话
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = TestingSessionLocal()

    try:
        yield session
    finally:
        session.close()
        # 清理所有表数据
        Base.metadata.drop_all(bind=engine)


# ==========================================
# Mock Fixtures
# ==========================================

@pytest.fixture
def mock_redis():
    """Mock Redis 客户端"""
    mock = MagicMock()
    mock.get = MagicMock(return_value=None)
    mock.set = MagicMock(return_value=True)
    mock.delete = MagicMock(return_value=1)
    mock.exists = MagicMock(return_value=False)
    mock.incr = MagicMock(return_value=1)
    mock.expire = MagicMock(return_value=True)
    mock.ttl = MagicMock(return_value=-1)
    return mock


@pytest.fixture
def mock_settings():
    """Mock 配置对象"""
    class MockSettings:
        APP_NAME = "Apple ID Auto Test"
        APP_VERSION = "1.0.0"
        APP_ENV = "testing"
        DEBUG = True
        SECRET_KEY = "test-secret-key"
        JWT_SECRET_KEY = "test-jwt-secret-key"
        JWT_ALGORITHM = "HS256"
        JWT_ACCESS_TOKEN_EXPIRE_MINUTES = 60
        JWT_REFRESH_TOKEN_EXPIRE_DAYS = 7
        DATABASE_URL = "sqlite:///:memory:"
        REDIS_URL = "redis://localhost:6379/15"
        MAX_LOGIN_ATTEMPTS = 5
        LOGIN_ATTEMPT_TIMEOUT = 300
        CARD_MAX_ATTEMPTS = 3
        CARD_ATTEMPT_TIMEOUT = 3600
        ALLOWED_HTML_TAGS = "div,span,p,a"
        ALLOWED_HTML_ATTRIBUTES = "class,id,href"

        @property
        def allowed_html_tags_list(self):
            return self.ALLOWED_HTML_TAGS.split(",")

        @property
        def allowed_html_attributes_list(self):
            return self.ALLOWED_HTML_ATTRIBUTES.split(",")

    return MockSettings()


# ==========================================
# 用户数据 Fixtures
# ==========================================

@pytest.fixture
def sample_user_data() -> Dict[str, Any]:
    """示例用户数据"""
    return {
        "username": "testuser",
        "email": "test@example.com",
        "password": "TestPassword123!",
        "is_active": True,
        "role": "user"
    }


@pytest.fixture
def sample_admin_data() -> Dict[str, Any]:
    """示例管理员数据"""
    return {
        "username": "admin",
        "email": "admin@example.com",
        "password": "AdminPassword123!",
        "is_active": True,
        "role": "admin"
    }


@pytest.fixture
def sample_apple_account_data() -> Dict[str, Any]:
    """示例 Apple ID 账号数据"""
    return {
        "apple_id": "test@icloud.com",
        "password": "ApplePassword123",
        "region": "US",
        "status": "active",
        "description": "Test account"
    }


@pytest.fixture
def sample_card_data() -> Dict[str, Any]:
    """示例卡密数据"""
    return {
        "code": "ABCD-1234-EFGH-5678",
        "package_id": 1,
        "duration_days": 30,
        "status": "unused"
    }


# ==========================================
# Token Fixtures
# ==========================================

@pytest.fixture
def valid_access_token() -> str:
    """生成有效的访问令牌"""
    from app.core.security import create_access_token
    return create_access_token({"sub": "1", "username": "testuser"})


@pytest.fixture
def valid_refresh_token() -> str:
    """生成有效的刷新令牌"""
    from app.core.security import create_refresh_token
    return create_refresh_token({"sub": "1", "username": "testuser"})


@pytest.fixture
def expired_token() -> str:
    """生成过期的令牌"""
    from app.core.security import create_access_token
    from datetime import timedelta
    return create_access_token(
        {"sub": "1", "username": "testuser"},
        expires_delta=timedelta(seconds=-1)
    )


# ==========================================
# HTTP 客户端 Fixtures
# ==========================================

@pytest.fixture
def auth_headers(valid_access_token) -> Dict[str, str]:
    """认证请求头"""
    return {"Authorization": f"Bearer {valid_access_token}"}


# ==========================================
# 辅助函数
# ==========================================

def create_test_user(db_session, **kwargs):
    """创建测试用户"""
    from app.models.user import User
    from app.core.security import get_password_hash

    default_data = {
        "username": "testuser",
        "email": "test@example.com",
        "hashed_password": get_password_hash("TestPassword123!"),
        "is_active": True,
        "role": "user"
    }
    default_data.update(kwargs)

    user = User(**default_data)
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


# ==========================================
# pytest 配置
# ==========================================

def pytest_configure(config):
    """pytest 配置钩子"""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )
    config.addinivalue_line(
        "markers", "unit: marks tests as unit tests"
    )


def pytest_collection_modifyitems(config, items):
    """自动添加 markers"""
    for item in items:
        if "integration" in item.nodeid:
            item.add_marker(pytest.mark.integration)
        elif "unit" in item.nodeid:
            item.add_marker(pytest.mark.unit)
