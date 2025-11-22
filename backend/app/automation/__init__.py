"""
Apple 自动化脚本模块

本模块提供 Apple ID 自动化操作的核心功能：
- apple_checker: 检查账号状态（登录测试、锁定检测、2FA 检测）
- apple_unlocker: 解锁账号（iforgot 流程、密保问题、验证码处理）

注意：这些功能需要根据实际业务需求进行实现
"""

from app.automation.apple_checker import check_apple_account
from app.automation.apple_unlocker import unlock_apple_account

__all__ = [
    "check_apple_account",
    "unlock_apple_account",
]
