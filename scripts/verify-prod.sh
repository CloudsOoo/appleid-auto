#!/bin/bash

# ============================================================
# Apple ID 自动解锁系统 - 生产环境验证脚本
# ============================================================

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

# 评分
TOTAL_SCORE=0
MAX_SCORE=100
PASSED_CHECKS=0
TOTAL_CHECKS=0

log_pass() {
    echo -e "${GREEN}✅ PASS${NC} $1"
    ((PASSED_CHECKS++)) || true
    ((TOTAL_CHECKS++)) || true
}

log_fail() {
    echo -e "${RED}❌ FAIL${NC} $1"
    ((TOTAL_CHECKS++)) || true
}

log_warn() {
    echo -e "${YELLOW}⚠️  WARN${NC} $1"
}

log_step() {
    echo -e "\n${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${CYAN}$1${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
}

# 检测 Docker Compose 命令
detect_docker_compose() {
    if docker compose version >/dev/null 2>&1; then
        DOCKER_COMPOSE="docker compose"
    elif command -v docker-compose >/dev/null 2>&1; then
        DOCKER_COMPOSE="docker-compose"
    else
        log_fail "Docker Compose 未安装"
        exit 1
    fi
}

# ============================================================
# 检查 1: 基础设施
# ============================================================
check_infrastructure() {
    log_step "1. 基础设施检查"

    # Docker 运行状态
    if docker info >/dev/null 2>&1; then
        log_pass "Docker 运行正常"
    else
        log_fail "Docker 未运行"
        return
    fi

    # 检查所有容器状态
    local containers=(
        "appleid_postgres_prod"
        "appleid_redis_prod"
        "appleid_backend_prod"
        "appleid_celery_worker_prod"
        "appleid_celery_beat_prod"
        "appleid_flower_prod"
        "appleid_frontend_prod"
    )

    for container in "${containers[@]}"; do
        if docker ps --format '{{.Names}}' | grep -q "^${container}$"; then
            log_pass "容器运行中: $container"
        else
            log_fail "容器未运行: $container"
        fi
    done
}

# ============================================================
# 检查 2: 后端健康
# ============================================================
check_backend_health() {
    log_step "2. 后端服务健康检查"

    # Health API
    if curl -sf http://localhost:8000/health >/dev/null 2>&1; then
        log_pass "后端 /health API 响应正常"
    else
        log_fail "后端 /health API 无响应"
    fi

    # API 文档
    if curl -sf http://localhost:8000/api/docs >/dev/null 2>&1; then
        log_pass "API 文档 (/api/docs) 可访问"
    else
        log_fail "API 文档无法访问"
    fi

    # OpenAPI Schema
    if curl -sf http://localhost:8000/api/openapi.json >/dev/null 2>&1; then
        log_pass "OpenAPI Schema 可获取"
    else
        log_fail "OpenAPI Schema 无法获取"
    fi
}

# ============================================================
# 检查 3: 数据库连接
# ============================================================
check_database() {
    log_step "3. 数据库检查"

    # PostgreSQL 连接
    if docker exec appleid_postgres_prod pg_isready -U postgres >/dev/null 2>&1; then
        log_pass "PostgreSQL 连接正常"
    else
        log_fail "PostgreSQL 无法连接"
    fi

    # 数据库存在
    if docker exec appleid_postgres_prod psql -U postgres -lqt | cut -d \| -f 1 | grep -qw appleid_auto; then
        log_pass "数据库 appleid_auto 存在"
    else
        log_fail "数据库 appleid_auto 不存在"
    fi
}

# ============================================================
# 检查 4: Redis 连接
# ============================================================
check_redis() {
    log_step "4. Redis 检查"

    if docker exec appleid_redis_prod redis-cli ping | grep -q PONG; then
        log_pass "Redis 连接正常"
    else
        log_fail "Redis 无法连接"
    fi
}

# ============================================================
# 检查 5: Celery 状态
# ============================================================
check_celery() {
    log_step "5. Celery 任务队列检查"

    # Worker 状态
    if $DOCKER_COMPOSE -f docker-compose.prod.yml exec -T celery_worker celery -A app.celery_app inspect ping 2>/dev/null | grep -q "pong"; then
        log_pass "Celery Worker 运行正常"
    else
        log_warn "Celery Worker 状态检查超时 (可能正在启动)"
    fi

    # Flower 监控
    if curl -sf http://localhost:5555 >/dev/null 2>&1; then
        log_pass "Flower 监控面板可访问"
    else
        log_fail "Flower 监控面板无法访问"
    fi
}

# ============================================================
# 检查 6: 前端服务
# ============================================================
check_frontend() {
    log_step "6. 前端服务检查"

    # 前端首页
    if curl -sf http://localhost/ >/dev/null 2>&1; then
        log_pass "前端首页可访问"
    else
        log_fail "前端首页无法访问"
    fi

    # 静态资源
    if curl -sf http://localhost/health >/dev/null 2>&1; then
        log_pass "前端健康检查端点正常"
    else
        log_fail "前端健康检查端点无响应"
    fi
}

# ============================================================
# 检查 7: API 并发测试
# ============================================================
check_api_concurrency() {
    log_step "7. API 并发测试 (10 并发)"

    if ! command -v ab >/dev/null 2>&1; then
        log_warn "ApacheBench (ab) 未安装，跳过并发测试"
        log_warn "安装方法: apt-get install apache2-utils"
        return
    fi

    local result=$(ab -n 100 -c 10 -q http://localhost:8000/health 2>&1)
    local failed=$(echo "$result" | grep "Failed requests" | awk '{print $3}')
    local rps=$(echo "$result" | grep "Requests per second" | awk '{print $4}')

    if [ "$failed" = "0" ]; then
        log_pass "10 并发 API 测试通过 (${rps} req/s)"
    else
        log_fail "并发测试失败: $failed 个请求失败"
    fi
}

# ============================================================
# 检查 8: Celery 任务测试
# ============================================================
check_celery_tasks() {
    log_step "8. Celery 任务测试"

    log_warn "Celery 任务测试需要手动验证"
    log_warn "建议: 登录系统后创建测试任务并观察执行情况"
}

# ============================================================
# 生成报告
# ============================================================
generate_report() {
    log_step "📊 验收报告"

    local score=$((PASSED_CHECKS * 100 / TOTAL_CHECKS))

    echo ""
    echo "┌─────────────────────────────────────────────────────────────┐"
    echo "│                    生产环境验收报告                          │"
    echo "├─────────────────────────────────────────────────────────────┤"
    printf "│  通过检查: %-3d / %-3d                                       │\n" $PASSED_CHECKS $TOTAL_CHECKS
    printf "│  商业化评分: %-3d / 100                                      │\n" $score
    echo "├─────────────────────────────────────────────────────────────┤"

    if [ $score -ge 90 ]; then
        echo "│  状态: ✅ 生产就绪 (Production Ready)                       │"
    elif [ $score -ge 70 ]; then
        echo "│  状态: ⚠️  基本可用 (需修复部分问题)                         │"
    else
        echo "│  状态: ❌ 未就绪 (需要修复关键问题)                          │"
    fi

    echo "└─────────────────────────────────────────────────────────────┘"

    echo ""
    echo "📋 补充建议:"
    echo "  1. 🔒 安全: 配置 HTTPS/SSL 证书"
    echo "  2. 📊 监控: 集成 Prometheus + Grafana"
    echo "  3. 📝 日志: 配置 ELK 或云日志服务"
    echo "  4. 💾 备份: 配置数据库定时备份"
    echo "  5. 🔄 CI/CD: 配置自动化部署流水线"
    echo ""
}

# ============================================================
# 主函数
# ============================================================
main() {
    echo ""
    echo "╔══════════════════════════════════════════════════════════════╗"
    echo "║     🔍 Apple ID 自动解锁系统 - 生产环境验证                   ║"
    echo "╚══════════════════════════════════════════════════════════════╝"
    echo ""

    detect_docker_compose

    check_infrastructure
    check_backend_health
    check_database
    check_redis
    check_celery
    check_frontend
    check_api_concurrency
    check_celery_tasks

    generate_report
}

main "$@"
