#!/bin/bash

# ============================================================
# Apple ID 自动解锁系统 - 生产环境部署脚本
# ============================================================

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }
log_step() { echo -e "${BLUE}[STEP]${NC} $1"; }

# 检测 Docker Compose 命令
detect_docker_compose() {
    if docker compose version >/dev/null 2>&1; then
        DOCKER_COMPOSE="docker compose"
    elif command -v docker-compose >/dev/null 2>&1; then
        DOCKER_COMPOSE="docker-compose"
    else
        log_error "Docker Compose 未安装"
        exit 1
    fi
}

# 生成密钥
generate_secret() {
    if command -v python3 >/dev/null 2>&1; then
        python3 -c "import secrets; print(secrets.token_urlsafe(48))"
    elif command -v openssl >/dev/null 2>&1; then
        openssl rand -base64 48 | tr -d '\n'
    else
        head -c 48 /dev/urandom | base64 | tr -d '\n'
    fi
}

# 主部署流程
main() {
    echo ""
    echo "╔══════════════════════════════════════════════════════════════╗"
    echo "║     🚀 Apple ID 自动解锁系统 - 生产环境部署                   ║"
    echo "╚══════════════════════════════════════════════════════════════╝"
    echo ""

    detect_docker_compose
    log_info "使用 Docker Compose: $DOCKER_COMPOSE"

    # 检查 .env.prod 文件
    if [ ! -f ".env.prod" ]; then
        log_step "创建生产环境配置文件..."
        cat > .env.prod << EOF
# 生产环境配置 - 自动生成于 $(date)
DB_USER=postgres
DB_PASSWORD=$(generate_secret)
DB_NAME=appleid_auto
SECRET_KEY=$(generate_secret)
JWT_SECRET_KEY=$(generate_secret)
JWT_EXPIRE=60
CORS_ORIGINS=["http://localhost","http://127.0.0.1"]
FLOWER_USER=admin
FLOWER_PASSWORD=$(generate_secret | head -c 16)
EOF
        log_info ".env.prod 已创建"
    fi

    # 加载环境变量
    export $(grep -v '^#' .env.prod | xargs)

    # 步骤 1: 构建镜像
    log_step "构建生产镜像..."
    $DOCKER_COMPOSE -f docker-compose.prod.yml build --no-cache

    # 步骤 2: 停止旧服务
    log_step "停止现有服务..."
    $DOCKER_COMPOSE -f docker-compose.prod.yml down 2>/dev/null || true

    # 步骤 3: 启动服务
    log_step "启动生产服务..."
    $DOCKER_COMPOSE -f docker-compose.prod.yml up -d

    # 步骤 4: 等待服务就绪
    log_step "等待服务启动..."
    sleep 20

    # 步骤 5: 健康检查
    log_step "执行健康检查..."

    # 检查后端
    for i in {1..30}; do
        if curl -sf http://localhost:8000/health >/dev/null 2>&1; then
            log_info "✅ 后端服务正常"
            break
        fi
        if [ $i -eq 30 ]; then
            log_error "❌ 后端服务未响应"
        fi
        sleep 2
    done

    # 检查前端
    for i in {1..10}; do
        if curl -sf http://localhost/health >/dev/null 2>&1; then
            log_info "✅ 前端服务正常"
            break
        fi
        if [ $i -eq 10 ]; then
            log_warn "⚠️ 前端服务未响应"
        fi
        sleep 2
    done

    # 检查 Celery
    if $DOCKER_COMPOSE -f docker-compose.prod.yml exec -T celery_worker celery -A app.celery_app inspect ping >/dev/null 2>&1; then
        log_info "✅ Celery Worker 正常"
    else
        log_warn "⚠️ Celery Worker 可能未就绪"
    fi

    # 显示状态
    echo ""
    log_step "服务状态:"
    $DOCKER_COMPOSE -f docker-compose.prod.yml ps

    # 显示访问信息
    echo ""
    echo -e "${GREEN}╔══════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║     🎉 部署完成！                                            ║${NC}"
    echo -e "${GREEN}╚══════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    echo -e "访问地址:"
    echo -e "  📍 前端:         http://localhost"
    echo -e "  📍 后端 API:     http://localhost:8000"
    echo -e "  📚 API 文档:     http://localhost:8000/api/docs"
    echo -e "  🌸 Flower 监控:  http://localhost:5555"
    echo ""
    echo -e "管理命令:"
    echo -e "  # 查看日志"
    echo -e "  $DOCKER_COMPOSE -f docker-compose.prod.yml logs -f"
    echo ""
    echo -e "  # 停止服务"
    echo -e "  $DOCKER_COMPOSE -f docker-compose.prod.yml down"
    echo ""
    echo -e "  # 重启服务"
    echo -e "  $DOCKER_COMPOSE -f docker-compose.prod.yml restart"
    echo ""
}

main "$@"
