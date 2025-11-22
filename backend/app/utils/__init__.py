"""
工具模块

提供各种通用工具函数
"""
from app.utils.encryption import (
    encrypt_data,
    decrypt_data,
    encrypt_aes_gcm,
    decrypt_aes_gcm,
    hash_data,
    generate_random_key,
    generate_api_key,
)
from app.utils.html_filter import (
    html_filter,
    clean_html,
    validate_custom_html,
)

__all__ = [
    # 加密工具
    "encrypt_data",
    "decrypt_data",
    "encrypt_aes_gcm",
    "decrypt_aes_gcm",
    "hash_data",
    "generate_random_key",
    "generate_api_key",
    # HTML 过滤
    "html_filter",
    "clean_html",
    "validate_custom_html",
]
