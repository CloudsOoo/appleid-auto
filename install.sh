#!/bin/bash

# ============================================================
# Apple ID 自动解锁系统 - 一键安装脚本
# ============================================================
#
# 使用方法：
#   curl -fsSL https://raw.githubusercontent.com/CloudsOoo/appleid-auto/main/install.sh | bash
#   或
#   wget -qO- https://raw.githubusercontent.com/CloudsOoo/appleid-auto/main/install.sh | bash
#   或
#   bash install.sh
#
# 支持系统：Ubuntu 18.04+, Debian 10+, CentOS 7+, macOS
# ============================================================

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# 日志函数
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_step() {
    echo -e "${BLUE}[STEP]${NC} $1"
}

# 打印 Banner
print_banner() {
    echo -e "${CYAN}"
    echo "╔══════════════════════════════════════════════════════════════╗"
    echo "║                                                              ║"
    echo "║     🍎 Apple ID 自动解锁系统 - 一键安装脚本                  ║"
    echo "║                                                              ║"
    echo "║     版本: 1.0.0                                              ║"
    echo "║     作者: Tracy                                              ║"
    echo "║                                                              ║"
    echo "╚══════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
}

# 检测操作系统
detect_os() {
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        if [ -f /etc/os-release ]; then
            . /etc/os-release
            OS=$NAME
            OS_ID=$ID
            VER=$VERSION_ID
        elif [ -f /etc/redhat-release ]; then
            OS="CentOS"
            OS_ID="centos"
        else
            OS=$(uname -s)
            OS_ID="unknown"
        fi
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        OS="macOS"
        OS_ID="macos"
        VER=$(sw_vers -productVersion)
    else
        OS=$(uname -s)
        OS_ID="unknown"
    fi

    log_info "检测到操作系统: $OS"
}

# 检查命令是否存在
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# 安装 Docker
install_docker() {
    if command_exists docker; then
        log_info "Docker 已安装: $(docker --version)"
        return 0
    fi

    log_step "正在安装 Docker..."

    case $OS_ID in
        ubuntu|debian)
            sudo apt-get update
            sudo apt-get install -y apt-transport-https ca-certificates curl gnupg lsb-release
            curl -fsSL https://download.docker.com/linux/$OS_ID/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
            echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/$OS_ID $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
            sudo apt-get update
            sudo apt-get install -y docker-ce docker-ce-cli containerd.io
            ;;
        centos|rhel|fedora)
            sudo yum install -y yum-utils
            sudo yum-config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo
            sudo yum install -y docker-ce docker-ce-cli containerd.io
            sudo systemctl start docker
            sudo systemctl enable docker
            ;;
        macos)
            log_error "macOS 请手动安装 Docker Desktop: https://www.docker.com/products/docker-desktop"
            exit 1
            ;;
        *)
            log_error "不支持的操作系统，请手动安装 Docker"
            exit 1
            ;;
    esac

    # 添加当前用户到 docker 组
    if [ "$OS_ID" != "macos" ]; then
        sudo usermod -aG docker $USER 2>/dev/null || true
    fi

    log_info "Docker 安装完成"
}

# 安装 Docker Compose
install_docker_compose() {
    if command_exists docker-compose || docker compose version >/dev/null 2>&1; then
        log_info "Docker Compose 已安装"
        return 0
    fi

    log_step "正在安装 Docker Compose..."

    # 尝试使用 Docker 插件版本
    if docker compose version >/dev/null 2>&1; then
        log_info "Docker Compose (插件版) 已可用"
        return 0
    fi

    # 安装独立版本
    COMPOSE_VERSION=$(curl -s https://api.github.com/repos/docker/compose/releases/latest | grep '"tag_name"' | sed -E 's/.*"([^"]+)".*/\1/')
    if [ -z "$COMPOSE_VERSION" ]; then
        COMPOSE_VERSION="v2.24.0"
    fi

    sudo curl -L "https://github.com/docker/compose/releases/download/${COMPOSE_VERSION}/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    sudo chmod +x /usr/local/bin/docker-compose

    log_info "Docker Compose 安装完成"
}

# 安装 Git
install_git() {
    if command_exists git; then
        log_info "Git 已安装: $(git --version)"
        return 0
    fi

    log_step "正在安装 Git..."

    case $OS_ID in
        ubuntu|debian)
            sudo apt-get update
            sudo apt-get install -y git
            ;;
        centos|rhel|fedora)
            sudo yum install -y git
            ;;
        macos)
            xcode-select --install 2>/dev/null || true
            ;;
        *)
            log_error "请手动安装 Git"
            exit 1
            ;;
    esac

    log_info "Git 安装完成"
}

# 生成随机密钥
generate_secret_key() {
    if command_exists python3; then
        python3 -c "import secrets; print(secrets.token_urlsafe(64))"
    elif command_exists openssl; then
        openssl rand -base64 48 | tr -d '\n'
    else
        head -c 64 /dev/urandom | base64 | tr -d '\n'
    fi
}

# 克隆或更新项目
clone_project() {
    INSTALL_DIR="${INSTALL_DIR:-$HOME/appleid-auto}"

    if [ -d "$INSTALL_DIR" ]; then
        log_info "项目目录已存在: $INSTALL_DIR"
        read -p "是否更新到最新版本？(y/n) " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            cd "$INSTALL_DIR"
            git pull origin main 2>/dev/null || git pull origin master 2>/dev/null || true
        fi
    else
        log_step "正在克隆项目到 $INSTALL_DIR..."
        git clone https://github.com/CloudsOoo/appleid-auto.git "$INSTALL_DIR"
    fi

    cd "$INSTALL_DIR"
    log_info "项目目录: $(pwd)"
}

# 配置环境变量
configure_env() {
    log_step "配置环境变量..."

    ENV_FILE="backend/.env"

    if [ -f "$ENV_FILE" ]; then
        log_info "环境配置文件已存在"
        read -p "是否重新生成配置？(y/n) " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            return 0
        fi
    fi

    # 生成密钥
    SECRET_KEY=$(generate_secret_key)
    JWT_SECRET_KEY=$(generate_secret_key)

    # 询问管理员信息
    echo ""
    echo -e "${PURPLE}请设置管理员信息（直接回车使用默认值）：${NC}"

    read -p "管理员用户名 [admin]: " ADMIN_USERNAME
    ADMIN_USERNAME=${ADMIN_USERNAME:-admin}

    read -p "管理员邮箱 [admin@example.com]: " ADMIN_EMAIL
    ADMIN_EMAIL=${ADMIN_EMAIL:-admin@example.com}

    read -sp "管理员密码 [Admin@123456]: " ADMIN_PASSWORD
    echo
    ADMIN_PASSWORD=${ADMIN_PASSWORD:-Admin@123456}

    # 生成配置文件
    cat > "$ENV_FILE" << EOF
# ============================================================
# Apple ID 自动解锁系统 - 环境配置
# 生成时间: $(date)
# ============================================================

# 应用配置
APP_NAME=Apple ID Auto
APP_VERSION=1.0.0
APP_ENV=production
DEBUG=False
SECRET_KEY=${SECRET_KEY}

# 服务器配置
HOST=0.0.0.0
PORT=8000
WORKERS=4

# 数据库配置
DATABASE_URL=postgresql+asyncpg://postgres:postgres@postgres:5432/appleid_auto
DATABASE_POOL_SIZE=20
DATABASE_MAX_OVERFLOW=10

# Redis 配置
REDIS_URL=redis://redis:6379/0

# Celery 配置
CELERY_BROKER_URL=redis://redis:6379/1
CELERY_RESULT_BACKEND=redis://redis:6379/2

# JWT 配置
JWT_SECRET_KEY=${JWT_SECRET_KEY}
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=60
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7

# CORS 配置
CORS_ORIGINS=["http://localhost","http://localhost:3000","http://localhost:5173"]

# 日志配置
LOG_LEVEL=INFO
LOG_FILE=./logs/app.log

# 限流配置
RATE_LIMIT_ENABLED=True
RATE_LIMIT_PER_MINUTE=60

# 管理员配置
ADMIN_USERNAME=${ADMIN_USERNAME}
ADMIN_EMAIL=${ADMIN_EMAIL}
ADMIN_PASSWORD=${ADMIN_PASSWORD}

# Apple API 配置
APPLE_API_TIMEOUT=30
APPLE_API_MAX_RETRIES=3

# 代理配置
PROXY_CHECK_INTERVAL=300
PROXY_TIMEOUT=10

# 节点配置
NODE_HEARTBEAT_INTERVAL=60
NODE_OFFLINE_THRESHOLD=180

# 任务配置
DEFAULT_CHECK_INTERVAL=3600
MAX_UNLOCK_RETRIES=3

# 安全配置
MAX_LOGIN_ATTEMPTS=5
LOGIN_ATTEMPT_TIMEOUT=300
CARD_MAX_ATTEMPTS=3
CARD_ATTEMPT_TIMEOUT=3600
EOF

    log_info "环境配置文件已生成"
}

# 构建前端
build_frontend() {
    log_step "构建前端..."

    if [ -d "frontend/dist" ]; then
        log_info "前端已构建，跳过"
        return 0
    fi

    # 检查是否有 Node.js
    if command_exists npm; then
        cd frontend
        npm install --silent
        npm run build
        cd ..
        log_info "前端构建完成"
    else
        log_warn "未安装 Node.js，将在 Docker 中构建前端"
    fi
}

# 启动服务
start_services() {
    log_step "启动 Docker 服务..."

    # 确保 Docker 正在运行
    if ! docker info >/dev/null 2>&1; then
        log_error "Docker 未运行，请先启动 Docker"
        exit 1
    fi

    # 使用开发配置启动（无 SSL）
    if [ -f "docker-compose.dev.yml" ]; then
        docker-compose -f docker-compose.dev.yml down 2>/dev/null || true
        docker-compose -f docker-compose.dev.yml up -d --build
    else
        docker-compose down 2>/dev/null || true
        docker-compose up -d --build
    fi

    log_info "等待服务启动..."
    sleep 15
}

# 初始化数据库
init_database() {
    log_step "初始化数据库..."

    # 等待数据库就绪
    for i in {1..30}; do
        if docker-compose -f docker-compose.dev.yml exec -T postgres pg_isready -U postgres >/dev/null 2>&1; then
            break
        fi
        echo -n "."
        sleep 2
    done
    echo ""

    # 执行初始化脚本
    if docker-compose -f docker-compose.dev.yml exec -T backend python scripts/init_db.py 2>/dev/null; then
        log_info "数据库初始化完成"
    else
        log_warn "数据库可能已初始化，跳过"
    fi
}

# 健康检查
health_check() {
    log_step "执行健康检查..."

    # 检查后端
    for i in {1..10}; do
        if curl -s http://localhost:8000/health >/dev/null 2>&1; then
            log_info "✅ 后端服务正常"
            break
        fi
        if [ $i -eq 10 ]; then
            log_warn "后端服务可能未完全启动，请稍后检查"
        fi
        sleep 3
    done

    # 检查服务状态
    echo ""
    echo -e "${CYAN}服务状态：${NC}"
    docker-compose -f docker-compose.dev.yml ps 2>/dev/null || docker-compose ps
}

# 打印完成信息
print_success() {
    echo ""
    echo -e "${GREEN}"
    echo "╔══════════════════════════════════════════════════════════════╗"
    echo "║                                                              ║"
    echo "║     🎉 安装完成！                                            ║"
    echo "║                                                              ║"
    echo "╚══════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"

    # 获取本机 IP
    LOCAL_IP=$(hostname -I 2>/dev/null | awk '{print $1}' || echo "localhost")

    echo -e "${CYAN}访问地址：${NC}"
    echo -e "  📍 后端 API:     http://${LOCAL_IP}:8000"
    echo -e "  📚 API 文档:     http://${LOCAL_IP}:8000/api/docs"
    echo -e "  🌸 Flower 监控:  http://${LOCAL_IP}:5555"
    echo ""
    echo -e "${CYAN}管理员账号：${NC}"
    echo -e "  👤 用户名: ${ADMIN_USERNAME:-admin}"
    echo -e "  📧 邮箱:   ${ADMIN_EMAIL:-admin@example.com}"
    echo -e "  🔑 密码:   (您设置的密码)"
    echo ""
    echo -e "${CYAN}常用命令：${NC}"
    echo -e "  # 查看日志"
    echo -e "  cd $INSTALL_DIR && docker-compose -f docker-compose.dev.yml logs -f"
    echo ""
    echo -e "  # 停止服务"
    echo -e "  cd $INSTALL_DIR && docker-compose -f docker-compose.dev.yml down"
    echo ""
    echo -e "  # 重启服务"
    echo -e "  cd $INSTALL_DIR && docker-compose -f docker-compose.dev.yml restart"
    echo ""
    echo -e "  # 更新系统"
    echo -e "  cd $INSTALL_DIR && git pull && docker-compose -f docker-compose.dev.yml up -d --build"
    echo ""
    echo -e "${YELLOW}⚠️  安全提示：${NC}"
    echo -e "  1. 首次登录后请立即修改密码"
    echo -e "  2. 生产环境请配置 SSL 证书"
    echo -e "  3. 定期备份数据库"
    echo ""
    echo -e "${PURPLE}项目目录: $INSTALL_DIR${NC}"
    echo ""
}

# 卸载
uninstall() {
    INSTALL_DIR="${INSTALL_DIR:-$HOME/appleid-auto}"

    echo -e "${RED}警告：此操作将删除所有数据！${NC}"
    read -p "确定要卸载吗？(输入 YES 确认) " confirm

    if [ "$confirm" = "YES" ]; then
        cd "$INSTALL_DIR" 2>/dev/null || true
        docker-compose -f docker-compose.dev.yml down -v 2>/dev/null || true
        docker-compose down -v 2>/dev/null || true
        cd ~
        rm -rf "$INSTALL_DIR"
        log_info "卸载完成"
    else
        log_info "取消卸载"
    fi
}

# 主函数
main() {
    print_banner

    # 解析参数
    case "${1:-}" in
        uninstall|remove)
            uninstall
            exit 0
            ;;
        -h|--help)
            echo "用法: $0 [选项]"
            echo ""
            echo "选项:"
            echo "  (无参数)    安装系统"
            echo "  uninstall   卸载系统"
            echo "  -h, --help  显示帮助"
            exit 0
            ;;
    esac

    # 检测系统
    detect_os

    echo ""
    log_info "开始安装 Apple ID 自动解锁系统..."
    echo ""

    # 安装依赖
    install_git
    install_docker
    install_docker_compose

    # 克隆项目
    clone_project

    # 配置环境
    configure_env

    # 构建前端（可选）
    # build_frontend

    # 启动服务
    start_services

    # 初始化数据库
    init_database

    # 健康检查
    health_check

    # 打印成功信息
    print_success
}

# 运行主函数
main "$@"
