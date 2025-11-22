"""
加密工具模块

本模块提供数据加密和解密功能，包括：
- 密码加密存储
- 敏感数据加密/解密
- 密钥管理

安全说明：
    - 使用 AES-256-GCM 加密敏感数据
    - 使用 Fernet 对称加密（基于 AES-128-CBC）
    - 所有密钥从 SECRET_KEY 派生
    - 加密数据包含随机 IV/Nonce，每次加密结果不同
"""

import base64
import hashlib
import secrets
from typing import Optional

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from app.core.config import settings


# ========================================
# 密钥派生
# ========================================

def _derive_key(salt: bytes = b"appleid_auto_salt") -> bytes:
    """
    从 SECRET_KEY 派生加密密钥

    使用 PBKDF2 算法派生密钥，增加暴力破解难度

    Args:
        salt: 盐值（默认使用固定盐，可根据需要改为随机盐）

    Returns:
        bytes: 派生的 32 字节密钥
    """
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100000,
    )
    return kdf.derive(settings.SECRET_KEY.encode())


def _get_fernet_key() -> bytes:
    """
    获取 Fernet 兼容的密钥

    Fernet 要求 32 字节 base64 编码的密钥

    Returns:
        bytes: Fernet 兼容的密钥
    """
    derived = _derive_key()
    return base64.urlsafe_b64encode(derived)


# ========================================
# Fernet 加密（推荐用于一般敏感数据）
# ========================================

def encrypt_data(plaintext: str) -> str:
    """
    加密敏感数据

    使用 Fernet 对称加密算法（基于 AES-128-CBC + HMAC）

    Args:
        plaintext: 要加密的明文字符串

    Returns:
        str: 加密后的 base64 编码密文

    Example:
        >>> encrypted = encrypt_data("my_password")
        >>> print(encrypted)  # gAAAAABh...
    """
    if not plaintext:
        return ""

    fernet = Fernet(_get_fernet_key())
    encrypted = fernet.encrypt(plaintext.encode())
    return encrypted.decode()


def decrypt_data(ciphertext: str) -> str:
    """
    解密敏感数据

    使用 Fernet 对称加密算法解密

    Args:
        ciphertext: 加密后的 base64 编码密文

    Returns:
        str: 解密后的明文字符串

    Raises:
        InvalidToken: 密文无效或密钥错误

    Example:
        >>> decrypted = decrypt_data("gAAAAABh...")
        >>> print(decrypted)  # my_password
    """
    if not ciphertext:
        return ""

    fernet = Fernet(_get_fernet_key())
    decrypted = fernet.decrypt(ciphertext.encode())
    return decrypted.decode()


# ========================================
# AES-GCM 加密（用于需要更高安全性的场景）
# ========================================

def encrypt_aes_gcm(plaintext: str) -> str:
    """
    使用 AES-256-GCM 加密数据

    AES-GCM 提供认证加密，同时保证机密性和完整性

    Args:
        plaintext: 要加密的明文字符串

    Returns:
        str: base64 编码的 nonce + 密文
    """
    if not plaintext:
        return ""

    key = _derive_key()
    aesgcm = AESGCM(key)
    nonce = secrets.token_bytes(12)  # 96-bit nonce
    ciphertext = aesgcm.encrypt(nonce, plaintext.encode(), None)

    # 返回 nonce + ciphertext 的 base64 编码
    return base64.urlsafe_b64encode(nonce + ciphertext).decode()


def decrypt_aes_gcm(ciphertext: str) -> str:
    """
    使用 AES-256-GCM 解密数据

    Args:
        ciphertext: base64 编码的 nonce + 密文

    Returns:
        str: 解密后的明文字符串

    Raises:
        InvalidTag: 密文被篡改或密钥错误
    """
    if not ciphertext:
        return ""

    key = _derive_key()
    aesgcm = AESGCM(key)

    data = base64.urlsafe_b64decode(ciphertext.encode())
    nonce = data[:12]
    ct = data[12:]

    plaintext = aesgcm.decrypt(nonce, ct, None)
    return plaintext.decode()


# ========================================
# 哈希函数
# ========================================

def hash_data(data: str, salt: Optional[str] = None) -> str:
    """
    对数据进行 SHA-256 哈希

    用于生成不可逆的数据摘要

    Args:
        data: 要哈希的数据
        salt: 可选的盐值

    Returns:
        str: 十六进制哈希值
    """
    if salt:
        data = f"{salt}{data}"
    return hashlib.sha256(data.encode()).hexdigest()


def generate_random_key(length: int = 32) -> str:
    """
    生成随机密钥

    Args:
        length: 密钥长度（字节数）

    Returns:
        str: URL 安全的 base64 编码随机字符串
    """
    return secrets.token_urlsafe(length)


def generate_api_key() -> str:
    """
    生成 API 密钥

    格式：ak_前缀 + 32字符随机字符串

    Returns:
        str: API 密钥
    """
    return f"ak_{secrets.token_urlsafe(24)}"


# ========================================
# 导出
# ========================================

__all__ = [
    "encrypt_data",
    "decrypt_data",
    "encrypt_aes_gcm",
    "decrypt_aes_gcm",
    "hash_data",
    "generate_random_key",
    "generate_api_key",
]
