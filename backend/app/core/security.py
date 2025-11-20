"""
安全工具函数
"""
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from passlib.context import CryptContext
from jose import jwt, JWTError
import secrets
import hashlib

from app.core.config import settings

# 密码加密上下文
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """验证密码"""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """获取密码哈希"""
    return pwd_context.hash(password)


def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """创建访问令牌"""
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire, "type": "access"})
    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    return encoded_jwt


def create_refresh_token(data: Dict[str, Any]) -> str:
    """创建刷新令牌"""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh"})
    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    return encoded_jwt


def decode_token(token: str) -> Optional[Dict[str, Any]]:
    """解码令牌"""
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        return payload
    except JWTError:
        return None


def generate_random_string(length: int = 32) -> str:
    """生成随机字符串"""
    return secrets.token_urlsafe(length)


def generate_card_code() -> str:
    """生成卡密代码（格式：XXXX-XXXX-XXXX-XXXX）"""
    segments = []
    for _ in range(4):
        segment = secrets.token_hex(2).upper()
        segments.append(segment)
    return "-".join(segments)


def generate_node_key() -> str:
    """生成节点密钥"""
    return f"node_{secrets.token_urlsafe(32)}"


def generate_api_key() -> tuple[str, str]:
    """生成 API Key 和 Secret"""
    api_key = f"ak_{secrets.token_urlsafe(24)}"
    api_secret = f"sk_{secrets.token_urlsafe(32)}"
    return api_key, api_secret


def hash_string(text: str) -> str:
    """哈希字符串（SHA256）"""
    return hashlib.sha256(text.encode()).hexdigest()


def encrypt_sensitive_data(data: str, key: Optional[str] = None) -> str:
    """
    加密敏感数据（简单实现，生产环境建议使用 Fernet）
    TODO: 使用更安全的加密方式
    """
    # 这里使用简单的编码，实际应该使用 cryptography.fernet
    import base64
    encoded = base64.b64encode(data.encode()).decode()
    return encoded


def decrypt_sensitive_data(encrypted_data: str, key: Optional[str] = None) -> str:
    """
    解密敏感数据
    TODO: 使用更安全的解密方式
    """
    import base64
    decoded = base64.b64decode(encrypted_data.encode()).decode()
    return decoded
