"""
Pydantic Schemas 模块
"""
# 用户
from app.schemas.user import (
    UserCreate,
    UserLogin,
    UserUpdate,
    UserResponse,
    UserPermissionResponse,
    Token,
    TokenPayload,
    Enable2FAResponse,
    Verify2FA,
    ChangePassword,
)

# 卡密
from app.schemas.card import (
    CardActivate,
    CardGenerate,
    CardResponse,
    CardLogResponse,
    CardActivateResponse,
    CardStatusResponse,
    CardGenerateResponse,
)

# Apple ID
from app.schemas.account import (
    AppleAccountCreate,
    AppleAccountUpdate,
    AppleAccountResponse,
    AppleAccountDetailResponse,
    AppleAccountImport,
    AppleAccountImportResponse,
    PasswordHistoryResponse,
)

# 分享页
from app.schemas.share_page import (
    SharePageCreate,
    SharePageUpdate,
    SharePageResponse,
    SharePageAccess,
    SharePagePublicResponse,
    SharePageLogResponse,
)

# 任务
from app.schemas.task import (
    UnlockTaskCreate,
    UnlockTaskResponse,
    TaskStatsResponse,
)

# 代理
from app.schemas.proxy import (
    ProxyCreate,
    ProxyUpdate,
    ProxyResponse,
    ProxyTestResponse,
)

# 节点
from app.schemas.node import (
    NodeRegister,
    NodeHeartbeat,
    NodeResponse,
)

# 套餐
from app.schemas.package import (
    PackageCreate,
    PackageUpdate,
    PackageResponse,
)

# 通用
from app.schemas.common import (
    ResponseModel,
    PaginatedResponse,
    ErrorResponse,
    IDResponse,
    StatsResponse,
    HealthResponse,
)

__all__ = [
    # 用户
    "UserCreate",
    "UserLogin",
    "UserUpdate",
    "UserResponse",
    "UserPermissionResponse",
    "Token",
    "TokenPayload",
    "Enable2FAResponse",
    "Verify2FA",
    "ChangePassword",
    # 卡密
    "CardActivate",
    "CardGenerate",
    "CardResponse",
    "CardLogResponse",
    "CardActivateResponse",
    "CardStatusResponse",
    "CardGenerateResponse",
    # Apple ID
    "AppleAccountCreate",
    "AppleAccountUpdate",
    "AppleAccountResponse",
    "AppleAccountDetailResponse",
    "AppleAccountImport",
    "AppleAccountImportResponse",
    "PasswordHistoryResponse",
    # 分享页
    "SharePageCreate",
    "SharePageUpdate",
    "SharePageResponse",
    "SharePageAccess",
    "SharePagePublicResponse",
    "SharePageLogResponse",
    # 任务
    "UnlockTaskCreate",
    "UnlockTaskResponse",
    "TaskStatsResponse",
    # 代理
    "ProxyCreate",
    "ProxyUpdate",
    "ProxyResponse",
    "ProxyTestResponse",
    # 节点
    "NodeRegister",
    "NodeHeartbeat",
    "NodeResponse",
    # 套餐
    "PackageCreate",
    "PackageUpdate",
    "PackageResponse",
    # 通用
    "ResponseModel",
    "PaginatedResponse",
    "ErrorResponse",
    "IDResponse",
    "StatsResponse",
    "HealthResponse",
]
