@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

:: ============================================================
:: Apple ID 自动解锁系统 - Windows 一键安装脚本
:: ============================================================
::
:: 使用方法：双击运行此脚本，或在命令行执行 install.bat
::
:: 前置要求：
:: - Windows 10/11
:: - Docker Desktop 已安装并运行
:: - Git 已安装（可选，脚本会检测）
::
:: ============================================================

title Apple ID 自动解锁系统 - 安装程序

echo.
echo ╔══════════════════════════════════════════════════════════════╗
echo ║                                                              ║
echo ║     🍎 Apple ID 自动解锁系统 - Windows 安装脚本              ║
echo ║                                                              ║
echo ╚══════════════════════════════════════════════════════════════╝
echo.

:: 检查管理员权限
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo [警告] 建议以管理员身份运行此脚本
    echo.
)

:: 检查 Docker
echo [检查] 正在检查 Docker...
docker --version >nul 2>&1
if %errorLevel% neq 0 (
    echo [错误] Docker 未安装或未运行
    echo.
    echo 请先安装 Docker Desktop:
    echo https://www.docker.com/products/docker-desktop
    echo.
    pause
    exit /b 1
)
echo [成功] Docker 已安装

:: 检查 Docker 是否运行
docker info >nul 2>&1
if %errorLevel% neq 0 (
    echo [错误] Docker Desktop 未运行，请先启动 Docker Desktop
    pause
    exit /b 1
)
echo [成功] Docker 正在运行

:: 检查 Git
echo [检查] 正在检查 Git...
git --version >nul 2>&1
if %errorLevel% neq 0 (
    echo [警告] Git 未安装，将使用 ZIP 下载方式
    set USE_GIT=0
) else (
    echo [成功] Git 已安装
    set USE_GIT=1
)

:: 设置安装目录
set "INSTALL_DIR=%USERPROFILE%\appleid-auto"
echo.
echo [信息] 安装目录: %INSTALL_DIR%

:: 检查目录是否存在
if exist "%INSTALL_DIR%" (
    echo [信息] 项目目录已存在
    set /p UPDATE="是否更新到最新版本？(Y/N): "
    if /i "!UPDATE!"=="Y" (
        cd /d "%INSTALL_DIR%"
        if %USE_GIT%==1 (
            git pull origin main 2>nul || git pull origin master 2>nul
        )
    )
) else (
    if %USE_GIT%==1 (
        echo [步骤] 正在克隆项目...
        git clone https://github.com/CloudsOoo/appleid-auto.git "%INSTALL_DIR%"
    ) else (
        echo [步骤] 正在下载项目...
        powershell -Command "Invoke-WebRequest -Uri 'https://github.com/CloudsOoo/appleid-auto/archive/refs/heads/main.zip' -OutFile '%TEMP%\appleid-auto.zip'"
        powershell -Command "Expand-Archive -Path '%TEMP%\appleid-auto.zip' -DestinationPath '%USERPROFILE%' -Force"
        ren "%USERPROFILE%\appleid-auto-main" "appleid-auto"
    )
)

cd /d "%INSTALL_DIR%"

:: 配置环境变量
echo.
echo [步骤] 配置环境变量...

if exist "backend\.env" (
    set /p RECONFIG="配置文件已存在，是否重新配置？(Y/N): "
    if /i not "!RECONFIG!"=="Y" goto :skip_config
)

:: 生成随机密钥
for /f %%i in ('powershell -Command "[Convert]::ToBase64String([System.Security.Cryptography.RandomNumberGenerator]::GetBytes(48))"') do set SECRET_KEY=%%i
for /f %%i in ('powershell -Command "[Convert]::ToBase64String([System.Security.Cryptography.RandomNumberGenerator]::GetBytes(48))"') do set JWT_SECRET_KEY=%%i

:: 获取管理员信息
echo.
echo 请设置管理员信息（直接回车使用默认值）：
set /p ADMIN_USERNAME="管理员用户名 [admin]: "
if "%ADMIN_USERNAME%"=="" set ADMIN_USERNAME=admin

set /p ADMIN_EMAIL="管理员邮箱 [admin@example.com]: "
if "%ADMIN_EMAIL%"=="" set ADMIN_EMAIL=admin@example.com

set /p ADMIN_PASSWORD="管理员密码 [Admin@123456]: "
if "%ADMIN_PASSWORD%"=="" set ADMIN_PASSWORD=Admin@123456

:: 创建配置文件
(
echo # Apple ID 自动解锁系统 - 环境配置
echo # 生成时间: %date% %time%
echo.
echo APP_NAME=Apple ID Auto
echo APP_VERSION=1.0.0
echo APP_ENV=production
echo DEBUG=False
echo SECRET_KEY=%SECRET_KEY%
echo.
echo HOST=0.0.0.0
echo PORT=8000
echo WORKERS=4
echo.
echo DATABASE_URL=postgresql+asyncpg://postgres:postgres@postgres:5432/appleid_auto
echo DATABASE_POOL_SIZE=20
echo DATABASE_MAX_OVERFLOW=10
echo.
echo REDIS_URL=redis://redis:6379/0
echo CELERY_BROKER_URL=redis://redis:6379/1
echo CELERY_RESULT_BACKEND=redis://redis:6379/2
echo.
echo JWT_SECRET_KEY=%JWT_SECRET_KEY%
echo JWT_ALGORITHM=HS256
echo JWT_ACCESS_TOKEN_EXPIRE_MINUTES=60
echo JWT_REFRESH_TOKEN_EXPIRE_DAYS=7
echo.
echo CORS_ORIGINS=["http://localhost","http://localhost:3000","http://localhost:5173"]
echo.
echo LOG_LEVEL=INFO
echo LOG_FILE=./logs/app.log
echo.
echo RATE_LIMIT_ENABLED=True
echo RATE_LIMIT_PER_MINUTE=60
echo.
echo ADMIN_USERNAME=%ADMIN_USERNAME%
echo ADMIN_EMAIL=%ADMIN_EMAIL%
echo ADMIN_PASSWORD=%ADMIN_PASSWORD%
echo.
echo APPLE_API_TIMEOUT=30
echo APPLE_API_MAX_RETRIES=3
echo PROXY_CHECK_INTERVAL=300
echo PROXY_TIMEOUT=10
echo NODE_HEARTBEAT_INTERVAL=60
echo NODE_OFFLINE_THRESHOLD=180
echo DEFAULT_CHECK_INTERVAL=3600
echo MAX_UNLOCK_RETRIES=3
echo MAX_LOGIN_ATTEMPTS=5
echo LOGIN_ATTEMPT_TIMEOUT=300
echo CARD_MAX_ATTEMPTS=3
echo CARD_ATTEMPT_TIMEOUT=3600
) > backend\.env

echo [成功] 配置文件已生成

:skip_config

:: 启动服务
echo.
echo [步骤] 启动 Docker 服务...

if exist "docker-compose.dev.yml" (
    docker-compose -f docker-compose.dev.yml down 2>nul
    docker-compose -f docker-compose.dev.yml up -d --build
) else (
    docker-compose down 2>nul
    docker-compose up -d --build
)

echo [信息] 等待服务启动（约30秒）...
timeout /t 30 /nobreak >nul

:: 初始化数据库
echo.
echo [步骤] 初始化数据库...
docker-compose -f docker-compose.dev.yml exec -T backend python scripts/init_db.py 2>nul
if %errorLevel% neq 0 (
    echo [信息] 数据库可能已初始化
)

:: 健康检查
echo.
echo [步骤] 健康检查...
curl -s http://localhost:8000/health >nul 2>&1
if %errorLevel%==0 (
    echo [成功] 后端服务正常运行
) else (
    echo [警告] 后端服务可能未完全启动，请稍后重试
)

:: 显示服务状态
echo.
echo [信息] 服务状态：
docker-compose -f docker-compose.dev.yml ps 2>nul || docker-compose ps

:: 完成
echo.
echo ╔══════════════════════════════════════════════════════════════╗
echo ║                                                              ║
echo ║     🎉 安装完成！                                            ║
echo ║                                                              ║
echo ╚══════════════════════════════════════════════════════════════╝
echo.
echo 访问地址：
echo   📍 后端 API:     http://localhost:8000
echo   📚 API 文档:     http://localhost:8000/api/docs
echo   🌸 Flower 监控:  http://localhost:5555
echo.
echo 管理员账号：
echo   👤 用户名: %ADMIN_USERNAME%
echo   📧 邮箱:   %ADMIN_EMAIL%
echo   🔑 密码:   (您设置的密码)
echo.
echo 项目目录: %INSTALL_DIR%
echo.
echo ⚠️  安全提示：首次登录后请立即修改密码！
echo.
pause
