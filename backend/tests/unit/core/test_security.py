"""
安全模块单元测试

测试目标：
- 密码哈希和验证
- JWT Token 生成和解码
- 随机字符串生成
- 卡密代码生成
- 加密/解密函数

测试文件：app/core/security.py

运行方式：
    pytest tests/unit/core/test_security.py -v
    pytest tests/unit/core/test_security.py -k "test_password" -v
"""

import pytest
from datetime import timedelta
from unittest.mock import patch, MagicMock
import re


class TestPasswordHashing:
    """密码哈希测试类"""

    def test_get_password_hash_returns_hashed_string(self):
        """测试：密码哈希应返回非空字符串"""
        from app.core.security import get_password_hash

        password = "TestPassword123!"
        hashed = get_password_hash(password)

        assert hashed is not None
        assert isinstance(hashed, str)
        assert len(hashed) > 0
        assert hashed != password  # 哈希值不应等于原密码

    def test_get_password_hash_different_for_same_password(self):
        """测试：相同密码的两次哈希应该不同（因为 salt）"""
        from app.core.security import get_password_hash

        password = "TestPassword123!"
        hash1 = get_password_hash(password)
        hash2 = get_password_hash(password)

        # bcrypt 使用随机 salt，所以每次哈希结果不同
        assert hash1 != hash2

    def test_verify_password_correct(self):
        """测试：正确密码验证应返回 True"""
        from app.core.security import get_password_hash, verify_password

        password = "TestPassword123!"
        hashed = get_password_hash(password)

        assert verify_password(password, hashed) is True

    def test_verify_password_incorrect(self):
        """测试：错误密码验证应返回 False"""
        from app.core.security import get_password_hash, verify_password

        password = "TestPassword123!"
        wrong_password = "WrongPassword456!"
        hashed = get_password_hash(password)

        assert verify_password(wrong_password, hashed) is False

    def test_verify_password_empty_password(self):
        """测试：空密码验证"""
        from app.core.security import get_password_hash, verify_password

        password = "TestPassword123!"
        hashed = get_password_hash(password)

        assert verify_password("", hashed) is False

    def test_password_hash_is_bcrypt_format(self):
        """测试：哈希格式应符合 bcrypt"""
        from app.core.security import get_password_hash

        password = "TestPassword123!"
        hashed = get_password_hash(password)

        # bcrypt 哈希以 $2b$ 或 $2a$ 开头
        assert hashed.startswith(("$2b$", "$2a$", "$2y$"))


class TestJWTTokens:
    """JWT Token 测试类"""

    def test_create_access_token_returns_string(self):
        """测试：创建访问令牌应返回字符串"""
        from app.core.security import create_access_token

        data = {"sub": "1", "username": "testuser"}
        token = create_access_token(data)

        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 0

    def test_create_access_token_with_custom_expiry(self):
        """测试：使用自定义过期时间创建令牌"""
        from app.core.security import create_access_token, decode_token

        data = {"sub": "1", "username": "testuser"}
        expires = timedelta(minutes=30)
        token = create_access_token(data, expires_delta=expires)

        decoded = decode_token(token)
        assert decoded is not None
        assert decoded["type"] == "access"

    def test_create_refresh_token_returns_string(self):
        """测试：创建刷新令牌应返回字符串"""
        from app.core.security import create_refresh_token

        data = {"sub": "1", "username": "testuser"}
        token = create_refresh_token(data)

        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 0

    def test_decode_token_valid(self):
        """测试：解码有效令牌"""
        from app.core.security import create_access_token, decode_token

        data = {"sub": "1", "username": "testuser"}
        token = create_access_token(data)
        decoded = decode_token(token)

        assert decoded is not None
        assert decoded["sub"] == "1"
        assert decoded["username"] == "testuser"
        assert decoded["type"] == "access"
        assert "exp" in decoded

    def test_decode_token_invalid(self):
        """测试：解码无效令牌应返回 None"""
        from app.core.security import decode_token

        invalid_token = "invalid.token.string"
        decoded = decode_token(invalid_token)

        assert decoded is None

    def test_decode_token_expired(self):
        """测试：解码过期令牌应返回 None"""
        from app.core.security import create_access_token, decode_token

        data = {"sub": "1", "username": "testuser"}
        # 创建已过期的令牌
        token = create_access_token(data, expires_delta=timedelta(seconds=-1))
        decoded = decode_token(token)

        assert decoded is None

    def test_access_token_has_access_type(self):
        """测试：访问令牌类型应为 access"""
        from app.core.security import create_access_token, decode_token

        data = {"sub": "1"}
        token = create_access_token(data)
        decoded = decode_token(token)

        assert decoded["type"] == "access"

    def test_refresh_token_has_refresh_type(self):
        """测试：刷新令牌类型应为 refresh"""
        from app.core.security import create_refresh_token, decode_token

        data = {"sub": "1"}
        token = create_refresh_token(data)
        decoded = decode_token(token)

        assert decoded["type"] == "refresh"

    def test_tokens_are_different(self):
        """测试：访问令牌和刷新令牌应该不同"""
        from app.core.security import create_access_token, create_refresh_token

        data = {"sub": "1", "username": "testuser"}
        access_token = create_access_token(data)
        refresh_token = create_refresh_token(data)

        assert access_token != refresh_token


class TestRandomGeneration:
    """随机生成函数测试类"""

    def test_generate_random_string_default_length(self):
        """测试：生成随机字符串默认长度"""
        from app.core.security import generate_random_string

        random_str = generate_random_string()

        assert random_str is not None
        assert isinstance(random_str, str)
        assert len(random_str) > 0

    def test_generate_random_string_custom_length(self):
        """测试：生成指定长度的随机字符串"""
        from app.core.security import generate_random_string

        random_str = generate_random_string(length=16)

        assert random_str is not None
        # URL-safe base64 编码后长度会变化
        assert len(random_str) > 0

    def test_generate_random_string_uniqueness(self):
        """测试：生成的随机字符串应该唯一"""
        from app.core.security import generate_random_string

        strings = [generate_random_string() for _ in range(100)]

        # 检查所有字符串都不相同
        assert len(strings) == len(set(strings))

    def test_generate_card_code_format(self):
        """测试：卡密代码格式应为 XXXX-XXXX-XXXX-XXXX"""
        from app.core.security import generate_card_code

        code = generate_card_code()

        # 检查格式
        pattern = r'^[A-F0-9]{4}-[A-F0-9]{4}-[A-F0-9]{4}-[A-F0-9]{4}$'
        assert re.match(pattern, code) is not None

    def test_generate_card_code_uniqueness(self):
        """测试：生成的卡密代码应该唯一"""
        from app.core.security import generate_card_code

        codes = [generate_card_code() for _ in range(100)]

        assert len(codes) == len(set(codes))

    def test_generate_node_key_format(self):
        """测试：节点密钥格式"""
        from app.core.security import generate_node_key

        key = generate_node_key()

        assert key.startswith("node_")
        assert len(key) > 10

    def test_generate_api_key_format(self):
        """测试：API Key 格式"""
        from app.core.security import generate_api_key

        api_key, api_secret = generate_api_key()

        assert api_key.startswith("ak_")
        assert api_secret.startswith("sk_")
        assert len(api_key) > 10
        assert len(api_secret) > 10


class TestHashAndEncryption:
    """哈希和加密函数测试类"""

    def test_hash_string_returns_hex(self):
        """测试：哈希字符串返回十六进制"""
        from app.core.security import hash_string

        text = "test string"
        hashed = hash_string(text)

        assert hashed is not None
        assert isinstance(hashed, str)
        # SHA256 产生 64 字符的十六进制字符串
        assert len(hashed) == 64
        # 检查是否为有效的十六进制
        assert all(c in '0123456789abcdef' for c in hashed)

    def test_hash_string_same_input_same_output(self):
        """测试：相同输入产生相同哈希"""
        from app.core.security import hash_string

        text = "test string"
        hash1 = hash_string(text)
        hash2 = hash_string(text)

        assert hash1 == hash2

    def test_hash_string_different_input_different_output(self):
        """测试：不同输入产生不同哈希"""
        from app.core.security import hash_string

        hash1 = hash_string("text1")
        hash2 = hash_string("text2")

        assert hash1 != hash2

    def test_encrypt_decrypt_sensitive_data(self):
        """测试：加密和解密敏感数据"""
        from app.core.security import encrypt_sensitive_data, decrypt_sensitive_data

        original = "sensitive data 123"
        encrypted = encrypt_sensitive_data(original)
        decrypted = decrypt_sensitive_data(encrypted)

        assert encrypted != original  # 加密后应该不同
        assert decrypted == original  # 解密后应该相同

    def test_encrypt_sensitive_data_is_base64(self):
        """测试：加密结果应为 base64 格式"""
        from app.core.security import encrypt_sensitive_data
        import base64

        original = "test data"
        encrypted = encrypt_sensitive_data(original)

        # 应该可以成功解码为 base64
        try:
            base64.b64decode(encrypted)
            is_valid_base64 = True
        except Exception:
            is_valid_base64 = False

        assert is_valid_base64


class TestEdgeCases:
    """边界情况测试类"""

    def test_hash_empty_password(self):
        """测试：空密码哈希"""
        from app.core.security import get_password_hash, verify_password

        empty_password = ""
        hashed = get_password_hash(empty_password)

        assert verify_password(empty_password, hashed) is True

    def test_hash_unicode_password(self):
        """测试：Unicode 密码哈希"""
        from app.core.security import get_password_hash, verify_password

        unicode_password = "密码Test123！"
        hashed = get_password_hash(unicode_password)

        assert verify_password(unicode_password, hashed) is True

    def test_hash_very_long_password(self):
        """测试：超长密码哈希"""
        from app.core.security import get_password_hash, verify_password

        long_password = "a" * 1000
        hashed = get_password_hash(long_password)

        assert verify_password(long_password, hashed) is True

    def test_token_with_special_characters_in_data(self):
        """测试：包含特殊字符的令牌数据"""
        from app.core.security import create_access_token, decode_token

        data = {"sub": "1", "username": "user@test.com", "name": "用户名"}
        token = create_access_token(data)
        decoded = decode_token(token)

        assert decoded["username"] == "user@test.com"
        assert decoded["name"] == "用户名"

    def test_encrypt_empty_string(self):
        """测试：加密空字符串"""
        from app.core.security import encrypt_sensitive_data, decrypt_sensitive_data

        empty = ""
        encrypted = encrypt_sensitive_data(empty)
        decrypted = decrypt_sensitive_data(encrypted)

        assert decrypted == empty

    def test_encrypt_unicode_data(self):
        """测试：加密 Unicode 数据"""
        from app.core.security import encrypt_sensitive_data, decrypt_sensitive_data

        unicode_data = "中文数据 🔐"
        encrypted = encrypt_sensitive_data(unicode_data)
        decrypted = decrypt_sensitive_data(encrypted)

        assert decrypted == unicode_data
