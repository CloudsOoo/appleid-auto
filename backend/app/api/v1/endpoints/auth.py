"""
认证 API 端点

本模块提供用户认证相关的所有 API 接口，包括：
- 用户注册和登录
- 令牌刷新和登出
- 密码管理
- 2FA 双因素认证

调用关系：
    客户端 → auth.py → dependencies.py → AuthService → 数据库

端点列表：
1. POST /api/v1/auth/register - 用户注册
2. POST /api/v1/auth/login - 用户登录
3. POST /api/v1/auth/refresh - 刷新令牌
4. POST /api/v1/auth/logout - 登出
5. GET /api/v1/auth/me - 获取当前用户
6. POST /api/v1/auth/change-password - 修改密码
7. POST /api/v1/auth/2fa/enable - 启用 2FA
8. POST /api/v1/auth/2fa/verify - 验证 2FA
9. POST /api/v1/auth/2fa/disable - 关闭 2FA
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.services.auth_service import AuthService
from app.api.dependencies import get_current_user, get_current_active_user
from app.schemas.user import (
    UserCreate,
    UserLogin,
    UserResponse,
    UserUpdate,
    ChangePasswordRequest,
    Enable2FAResponse,
    Verify2FARequest,
    TokenResponse,
)
from app.models.user import User
from app.core.security import create_access_token, create_refresh_token, decode_token


# 创建路由器
router = APIRouter(tags=["认证"])


# ========== 1. 用户注册 ==========

@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="用户注册",
    description="创建新用户账号",
)
async def register(
    user_data: UserCreate,
    db: AsyncSession = Depends(get_db)
) -> UserResponse:
    """
    用户注册接口

    业务逻辑：
        1. 接收用户注册信息（用户名、邮箱、密码）
        2. 调用 AuthService.register_user 创建用户
        3. 自动创建默认权限记录
        4. 返回用户信息（不含密码）

    请求体：
        - username: 用户名（3-50字符）
        - email: 邮箱地址
        - password: 密码（最少8位，需包含大小写字母和数字）
        - full_name: 全名（可选）

    响应：
        - 201: 注册成功，返回用户信息
        - 400: 用户名或邮箱已存在
        - 422: 请求参数验证失败

    示例：
        POST /api/v1/auth/register
        {
            "username": "testuser",
            "email": "test@example.com",
            "password": "Test@123456",
            "full_name": "测试用户"
        }

    TODO:
        - 添加邮箱验证功能
        - 添加验证码机制
        - 添加注册审核功能（可选）
    """
    try:
        # 调用 Service 创建用户
        user = await AuthService.register_user(
            db=db,
            username=user_data.username,
            email=user_data.email,
            password=user_data.password,
            full_name=user_data.full_name,
        )

        return UserResponse.model_validate(user)

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"注册失败：{str(e)}"
        )


# ========== 2. 用户登录 ==========

@router.post(
    "/login",
    response_model=TokenResponse,
    summary="用户登录",
    description="使用用户名和密码登录，返回访问令牌",
)
async def login(
    credentials: UserLogin,
    request: Request,
    db: AsyncSession = Depends(get_db)
) -> TokenResponse:
    """
    用户登录接口

    业务逻辑：
        1. 接收用户名和密码
        2. 调用 AuthService.authenticate_user 验证用户
        3. 如果启用了 2FA，验证 OTP 码
        4. 生成 access_token 和 refresh_token
        5. 更新用户最后登录时间和 IP
        6. 返回令牌信息

    请求体：
        - username: 用户名
        - password: 密码
        - otp_code: 2FA 验证码（如果启用了 2FA）

    响应：
        - 200: 登录成功，返回令牌
        - 401: 用户名或密码错误
        - 401: 2FA 验证码错误
        - 403: 用户已被禁用

    示例：
        POST /api/v1/auth/login
        {
            "username": "testuser",
            "password": "Test@123456",
            "otp_code": "123456"  # 可选，仅当启用 2FA 时需要
        }

    响应示例：
        {
            "access_token": "eyJhbGciOiJIUzI1NiIs...",
            "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
            "token_type": "bearer",
            "expires_in": 3600
        }
    """
    try:
        # 验证用户身份
        user = await AuthService.authenticate_user(
            db=db,
            username=credentials.username,
            password=credentials.password,
            otp_code=credentials.otp_code,
        )

        # 检查用户是否激活
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="用户已被禁用，请联系管理员"
            )

        # 生成令牌
        access_token = create_access_token(data={"sub": user.id})
        refresh_token = create_refresh_token(data={"sub": user.id})

        # 更新最后登录信息
        client_ip = request.client.host if request.client else None
        await AuthService.update_last_login(db, user.id, client_ip)

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=3600,  # 1小时
        )

    except ValueError as e:
        # 认证失败
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"登录失败：{str(e)}"
        )


# ========== 3. 刷新令牌 ==========

@router.post(
    "/refresh",
    response_model=TokenResponse,
    summary="刷新访问令牌",
    description="使用 refresh_token 获取新的 access_token",
)
async def refresh_token(
    refresh_token: str,
    db: AsyncSession = Depends(get_db)
) -> TokenResponse:
    """
    刷新令牌接口

    业务逻辑：
        1. 接收 refresh_token
        2. 验证 refresh_token 是否有效
        3. 检查用户是否存在且激活
        4. 生成新的 access_token 和 refresh_token
        5. 返回新令牌

    请求体：
        - refresh_token: 刷新令牌

    响应：
        - 200: 刷新成功，返回新令牌
        - 401: refresh_token 无效或过期
        - 403: 用户已被禁用

    示例：
        POST /api/v1/auth/refresh
        {
            "refresh_token": "eyJhbGciOiJIUzI1NiIs..."
        }

    TODO:
        - 实现令牌黑名单机制（防止令牌复用）
        - 添加令牌家族追踪（检测令牌盗用）
    """
    try:
        # 解码 refresh_token
        payload = decode_token(refresh_token)
        if not payload:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="无效的刷新令牌",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # 验证令牌类型
        if payload.get("type") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="令牌类型错误",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # 获取用户
        user_id = payload.get("sub")
        user = await db.get(User, user_id)

        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="用户不存在",
                headers={"WWW-Authenticate": "Bearer"},
            )

        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="用户已被禁用"
            )

        # 生成新令牌
        new_access_token = create_access_token(data={"sub": user.id})
        new_refresh_token = create_refresh_token(data={"sub": user.id})

        return TokenResponse(
            access_token=new_access_token,
            refresh_token=new_refresh_token,
            token_type="bearer",
            expires_in=3600,
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"令牌刷新失败：{str(e)}"
        )


# ========== 4. 登出 ==========

@router.post(
    "/logout",
    status_code=status.HTTP_200_OK,
    summary="用户登出",
    description="登出当前用户（客户端应删除令牌）",
)
async def logout(
    current_user: User = Depends(get_current_user),
) -> dict:
    """
    用户登出接口

    业务逻辑：
        1. 获取当前用户（验证令牌）
        2. 返回成功响应
        3. 客户端应删除本地存储的令牌

    注意：
        - 由于使用的是无状态 JWT，服务端不存储会话
        - 实际的登出操作由客户端完成（删除令牌）
        - 如需服务端强制登出，需实现令牌黑名单机制

    响应：
        - 200: 登出成功
        - 401: 未认证

    TODO:
        - 实现令牌黑名单（将当前令牌加入黑名单）
        - 记录登出日志
        - 支持踢出指定设备
    """
    return {
        "code": 200,
        "message": "登出成功",
        "data": {
            "user_id": current_user.id,
            "username": current_user.username
        }
    }


# ========== 5. 获取当前用户信息 ==========

@router.get(
    "/me",
    response_model=UserResponse,
    summary="获取当前用户信息",
    description="获取当前登录用户的详细信息",
)
async def get_current_user_info(
    current_user: User = Depends(get_current_active_user),
) -> UserResponse:
    """
    获取当前用户信息接口

    业务逻辑：
        1. 从令牌中获取当前用户
        2. 返回用户信息（不含密码）

    响应：
        - 200: 返回用户信息
        - 401: 未认证
        - 403: 用户已被禁用

    示例：
        GET /api/v1/auth/me
        Authorization: Bearer <access_token>

    响应示例：
        {
            "id": 1,
            "username": "testuser",
            "email": "test@example.com",
            "full_name": "测试用户",
            "is_active": true,
            "is_admin": false,
            "two_factor_enabled": false,
            "created_at": "2025-11-20T12:00:00",
            "last_login_at": "2025-11-20T12:30:00"
        }
    """
    return UserResponse.model_validate(current_user)


# ========== 6. 修改密码 ==========

@router.post(
    "/change-password",
    status_code=status.HTTP_200_OK,
    summary="修改密码",
    description="修改当前用户的密码",
)
async def change_password(
    password_data: ChangePasswordRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> dict:
    """
    修改密码接口

    业务逻辑：
        1. 验证当前用户身份
        2. 验证旧密码是否正确
        3. 验证新密码格式
        4. 更新密码
        5. 可选：使所有旧令牌失效

    请求体：
        - old_password: 旧密码
        - new_password: 新密码（需符合密码策略）

    响应：
        - 200: 修改成功
        - 400: 旧密码错误
        - 401: 未认证
        - 422: 新密码不符合要求

    示例：
        POST /api/v1/auth/change-password
        {
            "old_password": "OldPass@123",
            "new_password": "NewPass@123"
        }

    TODO:
        - 发送密码修改通知邮件
        - 强制重新登录所有设备
        - 记录密码修改历史
    """
    try:
        # 调用 Service 修改密码
        success = await AuthService.change_password(
            db=db,
            user_id=current_user.id,
            old_password=password_data.old_password,
            new_password=password_data.new_password,
        )

        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="旧密码错误"
            )

        return {
            "code": 200,
            "message": "密码修改成功",
            "data": {
                "user_id": current_user.id,
                "updated_at": "now"  # TODO: 返回实际时间
            }
        }

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"密码修改失败：{str(e)}"
        )


# ========== 7. 启用 2FA ==========

@router.post(
    "/2fa/enable",
    response_model=Enable2FAResponse,
    summary="启用双因素认证",
    description="为当前用户启用 2FA，返回 QR 码和备用码",
)
async def enable_2fa(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> Enable2FAResponse:
    """
    启用 2FA 接口

    业务逻辑：
        1. 验证用户身份
        2. 检查是否已启用 2FA
        3. 生成 TOTP 密钥
        4. 生成 QR 码（供验证器 APP 扫描）
        5. 生成备用码（用于紧急情况）
        6. 返回 QR 码和备用码
        7. 用户需要验证后才正式启用

    响应：
        - 200: 返回 QR 码和配置信息
        - 400: 2FA 已启用
        - 401: 未认证

    示例：
        POST /api/v1/auth/2fa/enable

    响应示例：
        {
            "secret": "JBSWY3DPEHPK3PXP",
            "qr_code": "data:image/png;base64,iVBOR...",
            "backup_codes": ["12345678", "87654321", ...],
            "message": "请使用验证器 APP 扫描二维码，然后提交验证码以完成启用"
        }

    下一步：
        用户扫描二维码后，需要调用 /2fa/verify 验证并完成启用
    """
    try:
        # 检查是否已启用
        if current_user.two_factor_enabled:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="双因素认证已启用"
            )

        # 生成 2FA 配置
        result = AuthService.enable_2fa(current_user)

        # 保存到数据库（临时状态，验证后才正式启用）
        current_user.two_factor_secret = result["secret"]
        await db.commit()

        return Enable2FAResponse(
            secret=result["secret"],
            qr_code=result["qr_code"],
            backup_codes=result["backup_codes"],
            message="请使用验证器 APP 扫描二维码，然后提交验证码以完成启用"
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"启用 2FA 失败：{str(e)}"
        )


# ========== 8. 验证并完成 2FA 启用 ==========

@router.post(
    "/2fa/verify",
    status_code=status.HTTP_200_OK,
    summary="验证 2FA 验证码",
    description="验证 2FA 验证码以完成启用",
)
async def verify_2fa(
    verify_data: Verify2FARequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> dict:
    """
    验证 2FA 接口

    业务逻辑：
        1. 获取用户的 TOTP 密钥
        2. 验证用户提交的 OTP 码
        3. 如果正确，正式启用 2FA
        4. 返回成功响应

    请求体：
        - otp_code: 6位验证码

    响应：
        - 200: 验证成功，2FA 已启用
        - 400: 验证码错误
        - 401: 未认证

    示例：
        POST /api/v1/auth/2fa/verify
        {
            "otp_code": "123456"
        }
    """
    try:
        # 验证 OTP 码
        is_valid = AuthService.verify_totp(
            current_user.two_factor_secret,
            verify_data.otp_code
        )

        if not is_valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="验证码错误"
            )

        # 正式启用 2FA
        current_user.two_factor_enabled = True
        await db.commit()

        return {
            "code": 200,
            "message": "双因素认证已成功启用",
            "data": {
                "two_factor_enabled": True
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"验证失败：{str(e)}"
        )


# ========== 9. 关闭 2FA ==========

@router.post(
    "/2fa/disable",
    status_code=status.HTTP_200_OK,
    summary="关闭双因素认证",
    description="关闭当前用户的 2FA",
)
async def disable_2fa(
    verify_data: Verify2FARequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> dict:
    """
    关闭 2FA 接口

    业务逻辑：
        1. 验证用户身份
        2. 验证 OTP 码（确保是本人操作）
        3. 关闭 2FA
        4. 清除 TOTP 密钥

    请求体：
        - otp_code: 6位验证码（用于验证身份）

    响应：
        - 200: 关闭成功
        - 400: 2FA 未启用或验证码错误
        - 401: 未认证

    示例：
        POST /api/v1/auth/2fa/disable
        {
            "otp_code": "123456"
        }

    TODO:
        - 发送 2FA 关闭通知邮件
        - 记录安全操作日志
    """
    try:
        # 检查是否已启用
        if not current_user.two_factor_enabled:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="双因素认证未启用"
            )

        # 验证 OTP 码
        is_valid = AuthService.verify_totp(
            current_user.two_factor_secret,
            verify_data.otp_code
        )

        if not is_valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="验证码错误"
            )

        # 关闭 2FA
        current_user.two_factor_enabled = False
        current_user.two_factor_secret = None
        await db.commit()

        return {
            "code": 200,
            "message": "双因素认证已关闭",
            "data": {
                "two_factor_enabled": False
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"关闭 2FA 失败：{str(e)}"
        )
