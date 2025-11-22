"""
认证服务单元测试

测试目标：
- 用户注册
- 用户登录认证
- Token 创建
- 密码修改
- 2FA 启用/验证/关闭

测试文件：app/services/auth_service.py

运行方式：
    pytest tests/unit/services/test_auth_service.py -v
    pytest tests/unit/services/test_auth_service.py -k "test_register" -v

Mock 策略：
    - 使用 pytest-asyncio 处理异步测试
    - Mock 数据库会话
    - Mock pyotp 进行 2FA 测试
"""

import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch
import pyotp


# ==========================================
# AuthService.create_tokens 测试
# ==========================================

class TestCreateTokens:
    """Token 创建测试类"""

    def test_create_tokens_returns_dict(self):
        """测试：创建令牌应返回字典"""
        from app.services.auth_service import AuthService

        result = AuthService.create_tokens(user_id=1)

        assert isinstance(result, dict)
        assert "access_token" in result
        assert "refresh_token" in result
        assert "token_type" in result
        assert "expires_in" in result

    def test_create_tokens_token_type_is_bearer(self):
        """测试：令牌类型应为 bearer"""
        from app.services.auth_service import AuthService

        result = AuthService.create_tokens(user_id=1)

        assert result["token_type"] == "bearer"

    def test_create_tokens_has_valid_access_token(self):
        """测试：访问令牌应该有效"""
        from app.services.auth_service import AuthService
        from app.core.security import decode_token

        result = AuthService.create_tokens(user_id=1)
        decoded = decode_token(result["access_token"])

        assert decoded is not None
        assert decoded["sub"] == 1
        assert decoded["type"] == "access"

    def test_create_tokens_has_valid_refresh_token(self):
        """测试：刷新令牌应该有效"""
        from app.services.auth_service import AuthService
        from app.core.security import decode_token

        result = AuthService.create_tokens(user_id=1)
        decoded = decode_token(result["refresh_token"])

        assert decoded is not None
        assert decoded["sub"] == 1
        assert decoded["type"] == "refresh"

    def test_create_tokens_expires_in_positive(self):
        """测试：过期时间应为正数"""
        from app.services.auth_service import AuthService

        result = AuthService.create_tokens(user_id=1)

        assert result["expires_in"] > 0

    def test_create_tokens_different_user_ids(self):
        """测试：不同用户 ID 生成不同令牌"""
        from app.services.auth_service import AuthService

        result1 = AuthService.create_tokens(user_id=1)
        result2 = AuthService.create_tokens(user_id=2)

        assert result1["access_token"] != result2["access_token"]
        assert result1["refresh_token"] != result2["refresh_token"]


# ==========================================
# AuthService.register_user 测试
# ==========================================

class TestRegisterUser:
    """用户注册测试类"""

    @pytest.mark.asyncio
    async def test_register_user_success(self):
        """测试：成功注册用户"""
        from app.services.auth_service import AuthService

        # Mock 数据库会话
        mock_db = AsyncMock()
        mock_db.execute = AsyncMock()
        mock_db.add = MagicMock()
        mock_db.flush = AsyncMock()
        mock_db.commit = AsyncMock()
        mock_db.refresh = AsyncMock()

        # Mock 查询结果（用户名和邮箱都不存在）
        mock_result = MagicMock()
        mock_result.scalar_one_or_none = MagicMock(return_value=None)
        mock_db.execute.return_value = mock_result

        # 执行注册
        user = await AuthService.register_user(
            db=mock_db,
            username="newuser",
            email="newuser@example.com",
            password="TestPassword123!"
        )

        # 验证
        assert mock_db.add.called
        assert mock_db.commit.called

    @pytest.mark.asyncio
    async def test_register_user_username_exists(self):
        """测试：用户名已存在应抛出异常"""
        from app.services.auth_service import AuthService

        # Mock 数据库会话
        mock_db = AsyncMock()

        # Mock 查询结果（用户名已存在）
        mock_existing_user = MagicMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none = MagicMock(return_value=mock_existing_user)
        mock_db.execute = AsyncMock(return_value=mock_result)

        # 应该抛出异常
        with pytest.raises(ValueError, match="用户名已存在"):
            await AuthService.register_user(
                db=mock_db,
                username="existinguser",
                email="new@example.com",
                password="TestPassword123!"
            )

    @pytest.mark.asyncio
    async def test_register_user_email_exists(self):
        """测试：邮箱已存在应抛出异常"""
        from app.services.auth_service import AuthService

        # Mock 数据库会话
        mock_db = AsyncMock()

        # 第一次查询（用户名）返回 None，第二次查询（邮箱）返回存在的用户
        mock_existing_user = MagicMock()
        mock_result_none = MagicMock()
        mock_result_none.scalar_one_or_none = MagicMock(return_value=None)
        mock_result_exists = MagicMock()
        mock_result_exists.scalar_one_or_none = MagicMock(return_value=mock_existing_user)

        mock_db.execute = AsyncMock(side_effect=[mock_result_none, mock_result_exists])

        # 应该抛出异常
        with pytest.raises(ValueError, match="邮箱已存在"):
            await AuthService.register_user(
                db=mock_db,
                username="newuser",
                email="existing@example.com",
                password="TestPassword123!"
            )


# ==========================================
# AuthService.authenticate_user 测试
# ==========================================

class TestAuthenticateUser:
    """用户认证测试类"""

    @pytest.mark.asyncio
    async def test_authenticate_user_success(self):
        """测试：成功认证用户"""
        from app.services.auth_service import AuthService
        from app.core.security import get_password_hash

        # Mock 用户对象
        mock_user = MagicMock()
        mock_user.password_hash = get_password_hash("TestPassword123!")
        mock_user.two_factor_enabled = False
        mock_user.last_login_at = None

        # Mock 数据库会话
        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none = MagicMock(return_value=mock_user)
        mock_db.execute = AsyncMock(return_value=mock_result)
        mock_db.commit = AsyncMock()

        # 执行认证
        result = await AuthService.authenticate_user(
            db=mock_db,
            username="testuser",
            password="TestPassword123!"
        )

        assert result == mock_user
        assert mock_db.commit.called

    @pytest.mark.asyncio
    async def test_authenticate_user_wrong_password(self):
        """测试：密码错误应返回 None"""
        from app.services.auth_service import AuthService
        from app.core.security import get_password_hash

        # Mock 用户对象
        mock_user = MagicMock()
        mock_user.password_hash = get_password_hash("TestPassword123!")
        mock_user.two_factor_enabled = False

        # Mock 数据库会话
        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none = MagicMock(return_value=mock_user)
        mock_db.execute = AsyncMock(return_value=mock_result)

        # 执行认证（错误密码）
        result = await AuthService.authenticate_user(
            db=mock_db,
            username="testuser",
            password="WrongPassword!"
        )

        assert result is None

    @pytest.mark.asyncio
    async def test_authenticate_user_not_found(self):
        """测试：用户不存在应返回 None"""
        from app.services.auth_service import AuthService

        # Mock 数据库会话（用户不存在）
        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none = MagicMock(return_value=None)
        mock_db.execute = AsyncMock(return_value=mock_result)

        # 执行认证
        result = await AuthService.authenticate_user(
            db=mock_db,
            username="nonexistent",
            password="TestPassword123!"
        )

        assert result is None

    @pytest.mark.asyncio
    async def test_authenticate_user_2fa_required(self):
        """测试：启用 2FA 但未提供验证码应抛出异常"""
        from app.services.auth_service import AuthService
        from app.core.security import get_password_hash

        # Mock 用户对象（启用了 2FA）
        mock_user = MagicMock()
        mock_user.password_hash = get_password_hash("TestPassword123!")
        mock_user.two_factor_enabled = True
        mock_user.two_factor_secret = pyotp.random_base32()

        # Mock 数据库会话
        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none = MagicMock(return_value=mock_user)
        mock_db.execute = AsyncMock(return_value=mock_result)

        # 应该抛出异常（需要 2FA）
        with pytest.raises(ValueError, match="需要 2FA 验证码"):
            await AuthService.authenticate_user(
                db=mock_db,
                username="testuser",
                password="TestPassword123!"
            )

    @pytest.mark.asyncio
    async def test_authenticate_user_2fa_success(self):
        """测试：2FA 验证成功"""
        from app.services.auth_service import AuthService
        from app.core.security import get_password_hash

        # 生成 2FA 密钥和验证码
        secret = pyotp.random_base32()
        totp = pyotp.TOTP(secret)
        valid_code = totp.now()

        # Mock 用户对象
        mock_user = MagicMock()
        mock_user.password_hash = get_password_hash("TestPassword123!")
        mock_user.two_factor_enabled = True
        mock_user.two_factor_secret = secret
        mock_user.last_login_at = None

        # Mock 数据库会话
        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none = MagicMock(return_value=mock_user)
        mock_db.execute = AsyncMock(return_value=mock_result)
        mock_db.commit = AsyncMock()

        # 执行认证
        result = await AuthService.authenticate_user(
            db=mock_db,
            username="testuser",
            password="TestPassword123!",
            otp_code=valid_code
        )

        assert result == mock_user

    @pytest.mark.asyncio
    async def test_authenticate_user_2fa_wrong_code(self):
        """测试：2FA 验证码错误应抛出异常"""
        from app.services.auth_service import AuthService
        from app.core.security import get_password_hash

        # Mock 用户对象
        mock_user = MagicMock()
        mock_user.password_hash = get_password_hash("TestPassword123!")
        mock_user.two_factor_enabled = True
        mock_user.two_factor_secret = pyotp.random_base32()

        # Mock 数据库会话
        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none = MagicMock(return_value=mock_user)
        mock_db.execute = AsyncMock(return_value=mock_result)

        # 应该抛出异常（错误验证码）
        with pytest.raises(ValueError, match="2FA 验证码错误"):
            await AuthService.authenticate_user(
                db=mock_db,
                username="testuser",
                password="TestPassword123!",
                otp_code="000000"
            )


# ==========================================
# AuthService.change_password 测试
# ==========================================

class TestChangePassword:
    """密码修改测试类"""

    @pytest.mark.asyncio
    async def test_change_password_success(self):
        """测试：成功修改密码"""
        from app.services.auth_service import AuthService
        from app.core.security import get_password_hash

        # Mock 用户对象
        mock_user = MagicMock()
        mock_user.password_hash = get_password_hash("OldPassword123!")

        # Mock 数据库会话
        mock_db = AsyncMock()
        mock_db.commit = AsyncMock()

        # 执行修改密码
        result = await AuthService.change_password(
            db=mock_db,
            user=mock_user,
            old_password="OldPassword123!",
            new_password="NewPassword456!"
        )

        assert result is True
        assert mock_db.commit.called

    @pytest.mark.asyncio
    async def test_change_password_wrong_old_password(self):
        """测试：旧密码错误应抛出异常"""
        from app.services.auth_service import AuthService
        from app.core.security import get_password_hash

        # Mock 用户对象
        mock_user = MagicMock()
        mock_user.password_hash = get_password_hash("OldPassword123!")

        # Mock 数据库会话
        mock_db = AsyncMock()

        # 应该抛出异常
        with pytest.raises(ValueError, match="旧密码错误"):
            await AuthService.change_password(
                db=mock_db,
                user=mock_user,
                old_password="WrongOldPassword!",
                new_password="NewPassword456!"
            )


# ==========================================
# AuthService.enable_2fa 测试
# ==========================================

class TestEnable2FA:
    """2FA 启用测试类"""

    def test_enable_2fa_returns_dict(self):
        """测试：启用 2FA 应返回字典"""
        from app.services.auth_service import AuthService

        # Mock 用户对象
        mock_user = MagicMock()
        mock_user.email = "test@example.com"

        result = AuthService.enable_2fa(mock_user)

        assert isinstance(result, dict)
        assert "secret" in result
        assert "qr_code" in result
        assert "backup_codes" in result

    def test_enable_2fa_secret_is_valid(self):
        """测试：2FA 密钥应该有效"""
        from app.services.auth_service import AuthService

        mock_user = MagicMock()
        mock_user.email = "test@example.com"

        result = AuthService.enable_2fa(mock_user)

        # 密钥应该是有效的 base32
        assert len(result["secret"]) > 0
        # 可以用来创建 TOTP
        totp = pyotp.TOTP(result["secret"])
        code = totp.now()
        assert len(code) == 6

    def test_enable_2fa_qr_code_is_base64(self):
        """测试：二维码应该是 base64 格式"""
        from app.services.auth_service import AuthService

        mock_user = MagicMock()
        mock_user.email = "test@example.com"

        result = AuthService.enable_2fa(mock_user)

        assert result["qr_code"].startswith("data:image/png;base64,")

    def test_enable_2fa_has_backup_codes(self):
        """测试：应该生成备份码"""
        from app.services.auth_service import AuthService

        mock_user = MagicMock()
        mock_user.email = "test@example.com"

        result = AuthService.enable_2fa(mock_user)

        assert len(result["backup_codes"]) == 10
        for code in result["backup_codes"]:
            assert len(code) == 8


# ==========================================
# AuthService.verify_and_enable_2fa 测试
# ==========================================

class TestVerifyAndEnable2FA:
    """2FA 验证并启用测试类"""

    @pytest.mark.asyncio
    async def test_verify_and_enable_2fa_success(self):
        """测试：验证并启用 2FA 成功"""
        from app.services.auth_service import AuthService

        # 生成密钥和验证码
        secret = pyotp.random_base32()
        totp = pyotp.TOTP(secret)
        valid_code = totp.now()

        # Mock 用户和数据库
        mock_user = MagicMock()
        mock_db = AsyncMock()
        mock_db.commit = AsyncMock()

        result = await AuthService.verify_and_enable_2fa(
            db=mock_db,
            user=mock_user,
            secret=secret,
            code=valid_code
        )

        assert result is True
        assert mock_user.two_factor_enabled is True
        assert mock_user.two_factor_secret == secret
        assert mock_db.commit.called

    @pytest.mark.asyncio
    async def test_verify_and_enable_2fa_wrong_code(self):
        """测试：验证码错误应抛出异常"""
        from app.services.auth_service import AuthService

        secret = pyotp.random_base32()

        mock_user = MagicMock()
        mock_db = AsyncMock()

        with pytest.raises(ValueError, match="验证码错误"):
            await AuthService.verify_and_enable_2fa(
                db=mock_db,
                user=mock_user,
                secret=secret,
                code="000000"
            )


# ==========================================
# AuthService.disable_2fa 测试
# ==========================================

class TestDisable2FA:
    """2FA 关闭测试类"""

    @pytest.mark.asyncio
    async def test_disable_2fa_success(self):
        """测试：成功关闭 2FA"""
        from app.services.auth_service import AuthService
        from app.core.security import get_password_hash

        # Mock 用户
        mock_user = MagicMock()
        mock_user.password_hash = get_password_hash("TestPassword123!")
        mock_user.two_factor_enabled = True
        mock_user.two_factor_secret = pyotp.random_base32()

        # Mock 数据库
        mock_db = AsyncMock()
        mock_db.commit = AsyncMock()

        result = await AuthService.disable_2fa(
            db=mock_db,
            user=mock_user,
            password="TestPassword123!"
        )

        assert result is True
        assert mock_user.two_factor_enabled is False
        assert mock_user.two_factor_secret is None
        assert mock_db.commit.called

    @pytest.mark.asyncio
    async def test_disable_2fa_wrong_password(self):
        """测试：密码错误应抛出异常"""
        from app.services.auth_service import AuthService
        from app.core.security import get_password_hash

        mock_user = MagicMock()
        mock_user.password_hash = get_password_hash("TestPassword123!")

        mock_db = AsyncMock()

        with pytest.raises(ValueError, match="密码错误"):
            await AuthService.disable_2fa(
                db=mock_db,
                user=mock_user,
                password="WrongPassword!"
            )


# ==========================================
# AuthService.get_current_user 测试
# ==========================================

class TestGetCurrentUser:
    """获取当前用户测试类"""

    @pytest.mark.asyncio
    async def test_get_current_user_success(self):
        """测试：成功获取当前用户"""
        from app.services.auth_service import AuthService
        from app.core.security import create_access_token

        # 创建有效令牌
        token = create_access_token({"sub": 1})

        # Mock 用户
        mock_user = MagicMock()
        mock_user.id = 1
        mock_user.is_active = True

        # Mock 数据库
        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none = MagicMock(return_value=mock_user)
        mock_db.execute = AsyncMock(return_value=mock_result)

        result = await AuthService.get_current_user(db=mock_db, token=token)

        assert result == mock_user

    @pytest.mark.asyncio
    async def test_get_current_user_invalid_token(self):
        """测试：无效令牌应返回 None"""
        from app.services.auth_service import AuthService

        mock_db = AsyncMock()

        result = await AuthService.get_current_user(
            db=mock_db,
            token="invalid.token.here"
        )

        assert result is None

    @pytest.mark.asyncio
    async def test_get_current_user_inactive(self):
        """测试：非活跃用户应返回 None"""
        from app.services.auth_service import AuthService
        from app.core.security import create_access_token

        token = create_access_token({"sub": 1})

        # Mock 非活跃用户
        mock_user = MagicMock()
        mock_user.id = 1
        mock_user.is_active = False

        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none = MagicMock(return_value=mock_user)
        mock_db.execute = AsyncMock(return_value=mock_result)

        result = await AuthService.get_current_user(db=mock_db, token=token)

        assert result is None

    @pytest.mark.asyncio
    async def test_get_current_user_not_found(self):
        """测试：用户不存在应返回 None"""
        from app.services.auth_service import AuthService
        from app.core.security import create_access_token

        token = create_access_token({"sub": 999})

        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none = MagicMock(return_value=None)
        mock_db.execute = AsyncMock(return_value=mock_result)

        result = await AuthService.get_current_user(db=mock_db, token=token)

        assert result is None
