#!/bin/bash

# ============================================================
# Apple ID 自动解锁系统 - 环境诊断脚本
# ============================================================

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

PASSED=0
FAILED=0

log_pass() {
    echo -e "${GREEN}✅ PASS${NC} $1"
    ((PASSED++))
}

log_fail() {
    echo -e "${RED}❌ FAIL${NC} $1"
    ((FAILED++))
}

log_warn() {
    echo -e "${YELLOW}⚠️  WARN${NC} $1"
}

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

echo ""
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║     🔍 Apple ID 自动解锁系统 - 环境诊断                      ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""

# ============================================================
# 1. 操作系统检查
# ============================================================
echo -e "${BLUE}━━━ 1. 操作系统信息 ━━━${NC}"
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    if [ -f /etc/os-release ]; then
        . /etc/os-release
        log_info "操作系统: $NAME $VERSION"
    fi
elif [[ "$OSTYPE" == "darwin"* ]]; then
    log_info "操作系统: macOS $(sw_vers -productVersion)"
fi
log_info "内核: $(uname -r)"
log_info "架构: $(uname -m)"
echo ""

# ============================================================
# 2. Docker 检查
# ============================================================
echo -e "${BLUE}━━━ 2. Docker 环境 ━━━${NC}"
if command -v docker >/dev/null 2>&1; then
    log_pass "Docker 已安装: $(docker --version | cut -d' ' -f3)"

    if docker info >/dev/null 2>&1; then
        log_pass "Docker 服务运行中"
    else
        log_fail "Docker 服务未运行"
        log_info "启动方法: sudo systemctl start docker"
    fi
else
    log_fail "Docker 未安装"
    log_info "安装方法: curl -fsSL https://get.docker.com | sh"
fi
echo ""

# ============================================================
# 3. Docker Compose 检查
# ============================================================
echo -e "${BLUE}━━━ 3. Docker Compose ━━━${NC}"
if docker compose version >/dev/null 2>&1; then
    log_pass "Docker Compose 已安装 (插件版): $(docker compose version --short)"
elif command -v docker-compose >/dev/null 2>&1; then
    log_pass "Docker Compose 已安装 (独立版): $(docker-compose --version | cut -d' ' -f4)"
else
    log_fail "Docker Compose 未安装"
    log_info "安装方法: sudo apt-get install docker-compose-plugin"
fi
echo ""

# ============================================================
# 4. Git 检查
# ============================================================
echo -e "${BLUE}━━━ 4. Git 版本控制 ━━━${NC}"
if command -v git >/dev/null 2>&1; then
    log_pass "Git 已安装: $(git --version | cut -d' ' -f3)"
else
    log_fail "Git 未安装"
    log_info "安装方法: sudo apt-get install git"
fi
echo ""

# ============================================================
# 5. Python 环境检查
# ============================================================
echo -e "${BLUE}━━━ 5. Python 环境 (可选) ━━━${NC}"
if command -v python3 >/dev/null 2>&1; then
    log_pass "Python3 已安装: $(python3 --version | cut -d' ' -f2)"

    # 检查 FastAPI
    if python3 -c "import fastapi" 2>/dev/null; then
        log_pass "FastAPI 已安装"
    else
        log_warn "FastAPI 未安装 (使用 Docker 可忽略)"
    fi
else
    log_warn "Python3 未安装 (使用 Docker 可忽略)"
fi
echo ""

# ============================================================
# 6. Node.js 环境检查
# ============================================================
echo -e "${BLUE}━━━ 6. Node.js 环境 (可选) ━━━${NC}"
if command -v node >/dev/null 2>&1; then
    log_pass "Node.js 已安装: $(node --version)"

    if command -v npm >/dev/null 2>&1; then
        log_pass "npm 已安装: $(npm --version)"
    fi
else
    log_warn "Node.js 未安装 (使用 Docker 可忽略)"
fi
echo ""

# ============================================================
# 7. 端口检查
# ============================================================
echo -e "${BLUE}━━━ 7. 端口占用检查 ━━━${NC}"
PORTS=(80 443 5432 6379 8000 5555)
for port in "${PORTS[@]}"; do
    if command -v lsof >/dev/null 2>&1; then
        if sudo lsof -i :$port >/dev/null 2>&1; then
            log_warn "端口 $port 已被占用"
        else
            log_pass "端口 $port 可用"
        fi
    elif command -v ss >/dev/null 2>&1; then
        if sudo ss -tulpn | grep -q ":$port "; then
            log_warn "端口 $port 已被占用"
        else
            log_pass "端口 $port 可用"
        fi
    fi
done
echo ""

# ============================================================
# 8. 磁盘空间检查
# ============================================================
echo -e "${BLUE}━━━ 8. 磁盘空间 ━━━${NC}"
DISK_AVAIL=$(df -BG . | tail -1 | awk '{print $4}' | sed 's/G//')
if [ "$DISK_AVAIL" -ge 20 ]; then
    log_pass "可用空间充足: ${DISK_AVAIL}GB"
elif [ "$DISK_AVAIL" -ge 10 ]; then
    log_warn "可用空间: ${DISK_AVAIL}GB (建议至少 20GB)"
else
    log_fail "可用空间不足: ${DISK_AVAIL}GB"
fi
echo ""

# ============================================================
# 9. 内存检查
# ============================================================
echo -e "${BLUE}━━━ 9. 内存资源 ━━━${NC}"
if command -v free >/dev/null 2>&1; then
    TOTAL_MEM=$(free -g | awk '/^Mem:/{print $2}')
    if [ "$TOTAL_MEM" -ge 4 ]; then
        log_pass "总内存: ${TOTAL_MEM}GB"
    else
        log_warn "总内存: ${TOTAL_MEM}GB (建议至少 4GB)"
    fi
elif [[ "$OSTYPE" == "darwin"* ]]; then
    TOTAL_MEM=$(($(sysctl -n hw.memsize) / 1024 / 1024 / 1024))
    log_pass "总内存: ${TOTAL_MEM}GB"
fi
echo ""

# ============================================================
# 10. 项目文件检查
# ============================================================
echo -e "${BLUE}━━━ 10. 项目文件完整性 ━━━${NC}"
FILES=(
    "backend/Dockerfile"
    "backend/requirements.txt"
    "backend/app/main.py"
    "frontend/Dockerfile"
    "frontend/package.json"
    "docker-compose.yml"
    "docker-compose.dev.yml"
    "docker-compose.prod.yml"
)

for file in "${FILES[@]}"; do
    if [ -f "$file" ]; then
        log_pass "$file"
    else
        log_fail "$file 缺失"
    fi
done
echo ""

# ============================================================
# 总结
# ============================================================
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║                       诊断总结                                ║"
echo "╠══════════════════════════════════════════════════════════════╣"
printf "║  通过: %-3d  |  失败: %-3d                                    ║\n" $PASSED $FAILED
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}✅ 环境检查全部通过！可以开始部署${NC}"
    echo ""
    echo "推荐部署命令:"
    echo "  # 一键安装"
    echo "  curl -fsSL https://raw.githubusercontent.com/CloudsOoo/appleid-auto/claude/appleid-auto/main/install.sh | bash"
    echo ""
    echo "  # 或手动部署"
    echo "  docker compose -f docker-compose.dev.yml up -d"
elif [ $FAILED -le 2 ]; then
    echo -e "${YELLOW}⚠️  发现少量问题，建议修复后部署${NC}"
    echo ""
    echo "查看详细文档:"
    echo "  cat docs/故障诊断指南.md"
else
    echo -e "${RED}❌ 发现较多问题，请先修复环境${NC}"
    echo ""
    echo "查看详细文档:"
    echo "  cat docs/故障诊断指南.md"
fi
echo ""
