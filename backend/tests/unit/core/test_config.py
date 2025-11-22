"""
配置模块单元测试

测试目标：
- 配置加载
- 环境变量解析
- 配置属性
- 配置验证器

测试文件：app/core/config.py

运行方式：
    pytest tests/unit/core/test_config.py -v
    pytest tests/unit/core/test_config.py -k "test_settings" -v
"""

import pytest
import os
from unittest.mock import patch


class TestSettingsBasic:
    """基础配置测试类"""

    def test_settings_instance_exists(self):
        """测试：配置实例应该存在"""
        from app.core.config import settings

        assert settings is not None

    def test_settings_has_app_name(self):
        """测试：配置应包含应用名称"""
        from app.core.config import settings

        assert hasattr(settings, 'APP_NAME')
        assert isinstance(settings.APP_NAME, str)
        assert len(settings.APP_NAME) > 0

    def test_settings_has_app_version(self):
        """测试：配置应包含应用版本"""
        from app.core.config import settings

        assert hasattr(settings, 'APP_VERSION')
        assert isinstance(settings.APP_VERSION, str)

    def test_settings_has_debug_flag(self):
        """测试：配置应包含调试标志"""
        from app.core.config import settings

        assert hasattr(settings, 'DEBUG')
        assert isinstance(settings.DEBUG, bool)


class TestJWTSettings:
    """JWT 配置测试类"""

    def test_jwt_secret_key_exists(self):
        """测试：JWT 密钥应存在"""
        from app.core.config import settings

        assert hasattr(settings, 'JWT_SECRET_KEY')
        assert settings.JWT_SECRET_KEY is not None
        assert len(settings.JWT_SECRET_KEY) > 0

    def test_jwt_algorithm_default(self):
        """测试：JWT 算法默认值"""
        from app.core.config import settings

        assert hasattr(settings, 'JWT_ALGORITHM')
        assert settings.JWT_ALGORITHM == "HS256"

    def test_jwt_access_token_expire_minutes(self):
        """测试：访问令牌过期时间配置"""
        from app.core.config import settings

        assert hasattr(settings, 'JWT_ACCESS_TOKEN_EXPIRE_MINUTES')
        assert isinstance(settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES, int)
        assert settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES > 0

    def test_jwt_refresh_token_expire_days(self):
        """测试：刷新令牌过期天数配置"""
        from app.core.config import settings

        assert hasattr(settings, 'JWT_REFRESH_TOKEN_EXPIRE_DAYS')
        assert isinstance(settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS, int)
        assert settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS > 0


class TestDatabaseSettings:
    """数据库配置测试类"""

    def test_database_url_exists(self):
        """测试：数据库 URL 应存在"""
        from app.core.config import settings

        assert hasattr(settings, 'DATABASE_URL')
        assert settings.DATABASE_URL is not None

    def test_database_pool_size(self):
        """测试：数据库连接池大小"""
        from app.core.config import settings

        assert hasattr(settings, 'DATABASE_POOL_SIZE')
        assert isinstance(settings.DATABASE_POOL_SIZE, int)
        assert settings.DATABASE_POOL_SIZE > 0

    def test_database_max_overflow(self):
        """测试：数据库连接池溢出配置"""
        from app.core.config import settings

        assert hasattr(settings, 'DATABASE_MAX_OVERFLOW')
        assert isinstance(settings.DATABASE_MAX_OVERFLOW, int)


class TestRedisSettings:
    """Redis 配置测试类"""

    def test_redis_url_exists(self):
        """测试：Redis URL 应存在"""
        from app.core.config import settings

        assert hasattr(settings, 'REDIS_URL')
        assert settings.REDIS_URL is not None
        assert 'redis://' in settings.REDIS_URL


class TestCORSSettings:
    """CORS 配置测试类"""

    def test_cors_origins_exists(self):
        """测试：CORS 源配置应存在"""
        from app.core.config import settings

        assert hasattr(settings, 'CORS_ORIGINS')
        assert isinstance(settings.CORS_ORIGINS, list)

    def test_cors_origins_is_list(self):
        """测试：CORS 源应为列表"""
        from app.core.config import settings

        assert isinstance(settings.CORS_ORIGINS, list)
        for origin in settings.CORS_ORIGINS:
            assert isinstance(origin, str)

    def test_allowed_origins_property(self):
        """测试：ALLOWED_ORIGINS 属性应返回 CORS_ORIGINS"""
        from app.core.config import settings

        assert settings.ALLOWED_ORIGINS == settings.CORS_ORIGINS


class TestSecuritySettings:
    """安全配置测试类"""

    def test_max_login_attempts(self):
        """测试：最大登录尝试次数"""
        from app.core.config import settings

        assert hasattr(settings, 'MAX_LOGIN_ATTEMPTS')
        assert isinstance(settings.MAX_LOGIN_ATTEMPTS, int)
        assert settings.MAX_LOGIN_ATTEMPTS > 0

    def test_login_attempt_timeout(self):
        """测试：登录尝试超时配置"""
        from app.core.config import settings

        assert hasattr(settings, 'LOGIN_ATTEMPT_TIMEOUT')
        assert isinstance(settings.LOGIN_ATTEMPT_TIMEOUT, int)
        assert settings.LOGIN_ATTEMPT_TIMEOUT > 0

    def test_card_max_attempts(self):
        """测试：卡密最大尝试次数"""
        from app.core.config import settings

        assert hasattr(settings, 'CARD_MAX_ATTEMPTS')
        assert isinstance(settings.CARD_MAX_ATTEMPTS, int)

    def test_card_attempt_timeout(self):
        """测试：卡密尝试超时配置"""
        from app.core.config import settings

        assert hasattr(settings, 'CARD_ATTEMPT_TIMEOUT')
        assert isinstance(settings.CARD_ATTEMPT_TIMEOUT, int)


class TestHTMLSettings:
    """HTML 过滤配置测试类"""

    def test_allowed_html_tags_exists(self):
        """测试：允许的 HTML 标签配置应存在"""
        from app.core.config import settings

        assert hasattr(settings, 'ALLOWED_HTML_TAGS')
        assert isinstance(settings.ALLOWED_HTML_TAGS, str)

    def test_allowed_html_attributes_exists(self):
        """测试：允许的 HTML 属性配置应存在"""
        from app.core.config import settings

        assert hasattr(settings, 'ALLOWED_HTML_ATTRIBUTES')
        assert isinstance(settings.ALLOWED_HTML_ATTRIBUTES, str)

    def test_allowed_html_tags_list_property(self):
        """测试：HTML 标签列表属性"""
        from app.core.config import settings

        tags = settings.allowed_html_tags_list

        assert isinstance(tags, list)
        assert len(tags) > 0
        assert all(isinstance(tag, str) for tag in tags)

    def test_allowed_html_attributes_list_property(self):
        """测试：HTML 属性列表属性"""
        from app.core.config import settings

        attrs = settings.allowed_html_attributes_list

        assert isinstance(attrs, list)
        assert len(attrs) > 0
        assert all(isinstance(attr, str) for attr in attrs)


class TestUploadSettings:
    """上传配置测试类"""

    def test_max_upload_size(self):
        """测试：最大上传大小配置"""
        from app.core.config import settings

        assert hasattr(settings, 'MAX_UPLOAD_SIZE')
        assert isinstance(settings.MAX_UPLOAD_SIZE, int)
        assert settings.MAX_UPLOAD_SIZE > 0

    def test_upload_dir(self):
        """测试：上传目录配置"""
        from app.core.config import settings

        assert hasattr(settings, 'UPLOAD_DIR')
        assert isinstance(settings.UPLOAD_DIR, str)


class TestRateLimitSettings:
    """限流配置测试类"""

    def test_rate_limit_enabled(self):
        """测试：限流启用配置"""
        from app.core.config import settings

        assert hasattr(settings, 'RATE_LIMIT_ENABLED')
        assert isinstance(settings.RATE_LIMIT_ENABLED, bool)

    def test_rate_limit_per_minute(self):
        """测试：每分钟限流次数"""
        from app.core.config import settings

        assert hasattr(settings, 'RATE_LIMIT_PER_MINUTE')
        assert isinstance(settings.RATE_LIMIT_PER_MINUTE, int)
        assert settings.RATE_LIMIT_PER_MINUTE > 0


class TestProxySettings:
    """代理配置测试类"""

    def test_proxy_check_interval(self):
        """测试：代理检查间隔"""
        from app.core.config import settings

        assert hasattr(settings, 'PROXY_CHECK_INTERVAL')
        assert isinstance(settings.PROXY_CHECK_INTERVAL, int)
        assert settings.PROXY_CHECK_INTERVAL > 0

    def test_proxy_timeout(self):
        """测试：代理超时配置"""
        from app.core.config import settings

        assert hasattr(settings, 'PROXY_TIMEOUT')
        assert isinstance(settings.PROXY_TIMEOUT, int)
        assert settings.PROXY_TIMEOUT > 0


class TestNodeSettings:
    """节点配置测试类"""

    def test_node_heartbeat_interval(self):
        """测试：节点心跳间隔"""
        from app.core.config import settings

        assert hasattr(settings, 'NODE_HEARTBEAT_INTERVAL')
        assert isinstance(settings.NODE_HEARTBEAT_INTERVAL, int)
        assert settings.NODE_HEARTBEAT_INTERVAL > 0

    def test_node_offline_threshold(self):
        """测试：节点离线阈值"""
        from app.core.config import settings

        assert hasattr(settings, 'NODE_OFFLINE_THRESHOLD')
        assert isinstance(settings.NODE_OFFLINE_THRESHOLD, int)
        assert settings.NODE_OFFLINE_THRESHOLD > 0


class TestTaskSettings:
    """任务配置测试类"""

    def test_default_check_interval(self):
        """测试：默认检查间隔"""
        from app.core.config import settings

        assert hasattr(settings, 'DEFAULT_CHECK_INTERVAL')
        assert isinstance(settings.DEFAULT_CHECK_INTERVAL, int)
        assert settings.DEFAULT_CHECK_INTERVAL > 0

    def test_max_unlock_retries(self):
        """测试：最大解锁重试次数"""
        from app.core.config import settings

        assert hasattr(settings, 'MAX_UNLOCK_RETRIES')
        assert isinstance(settings.MAX_UNLOCK_RETRIES, int)
        assert settings.MAX_UNLOCK_RETRIES > 0


class TestSharePageSettings:
    """分享页配置测试类"""

    def test_share_page_default_template(self):
        """测试：分享页默认模板"""
        from app.core.config import settings

        assert hasattr(settings, 'SHARE_PAGE_DEFAULT_TEMPLATE')
        assert isinstance(settings.SHARE_PAGE_DEFAULT_TEMPLATE, str)

    def test_share_page_max_custom_html_size(self):
        """测试：分享页最大自定义 HTML 大小"""
        from app.core.config import settings

        assert hasattr(settings, 'SHARE_PAGE_MAX_CUSTOM_HTML_SIZE')
        assert isinstance(settings.SHARE_PAGE_MAX_CUSTOM_HTML_SIZE, int)
        assert settings.SHARE_PAGE_MAX_CUSTOM_HTML_SIZE > 0


class TestAdminSettings:
    """管理员配置测试类"""

    def test_admin_username(self):
        """测试：管理员用户名"""
        from app.core.config import settings

        assert hasattr(settings, 'ADMIN_USERNAME')
        assert isinstance(settings.ADMIN_USERNAME, str)
        assert len(settings.ADMIN_USERNAME) > 0

    def test_admin_email(self):
        """测试：管理员邮箱"""
        from app.core.config import settings

        assert hasattr(settings, 'ADMIN_EMAIL')
        assert isinstance(settings.ADMIN_EMAIL, str)
        assert '@' in settings.ADMIN_EMAIL

    def test_admin_password(self):
        """测试：管理员密码"""
        from app.core.config import settings

        assert hasattr(settings, 'ADMIN_PASSWORD')
        assert isinstance(settings.ADMIN_PASSWORD, str)
        assert len(settings.ADMIN_PASSWORD) >= 8


class TestEnvironmentProperty:
    """环境属性测试类"""

    def test_environment_property(self):
        """测试：ENVIRONMENT 属性应返回 APP_ENV"""
        from app.core.config import settings

        assert settings.ENVIRONMENT == settings.APP_ENV

    def test_enable_rate_limit_property(self):
        """测试：ENABLE_RATE_LIMIT 属性应返回 RATE_LIMIT_ENABLED"""
        from app.core.config import settings

        assert settings.ENABLE_RATE_LIMIT == settings.RATE_LIMIT_ENABLED


class TestCORSOriginsValidator:
    """CORS Origins 验证器测试类"""

    def test_parse_cors_origins_from_string(self):
        """测试：从字符串解析 CORS Origins"""
        from app.core.config import Settings

        # 测试验证器
        result = Settings.parse_cors_origins("http://localhost:3000,http://localhost:5173")

        assert isinstance(result, list)
        assert len(result) == 2
        assert "http://localhost:3000" in result
        assert "http://localhost:5173" in result

    def test_parse_cors_origins_from_list(self):
        """测试：从列表解析 CORS Origins"""
        from app.core.config import Settings

        origins = ["http://localhost:3000", "http://localhost:5173"]
        result = Settings.parse_cors_origins(origins)

        assert result == origins

    def test_parse_cors_origins_strips_whitespace(self):
        """测试：解析时去除空白"""
        from app.core.config import Settings

        result = Settings.parse_cors_origins(" http://localhost:3000 , http://localhost:5173 ")

        assert "http://localhost:3000" in result
        assert "http://localhost:5173" in result
