#!/bin/bash

# Apple ID Auto 系统 - 开发环境启动脚本
# 使用方法: ./scripts/start-dev.sh

set -e

echo "🚀 启动 Apple ID Auto 开发环境..."

# 检查 Docker 是否安装
if ! command -v docker &> /dev/null; then
    echo "❌ Docker 未安装，请先安装 Docker"
    exit 1
fi

if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    echo "❌ Docker Compose 未安装，请先安装 Docker Compose"
    exit 1
fi

# 进入项目根目录
cd "$(dirname "$0")/.."

# 构建前端（如果需要）
if [ ! -d "frontend/dist" ]; then
    echo "📦 构建前端..."
    cd frontend
    npm install
    npm run build
    cd ..
fi

# 启动 Docker 服务
echo "🐳 启动 Docker 服务..."
docker-compose -f docker-compose.dev.yml up -d

# 等待服务启动
echo "⏳ 等待服务启动..."
sleep 10

# 检查服务状态
echo "📊 服务状态："
docker-compose -f docker-compose.dev.yml ps

# 健康检查
echo ""
echo "🔍 健康检查："
if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo "✅ 后端服务正常"
else
    echo "⚠️ 后端服务启动中，请稍后重试..."
fi

echo ""
echo "=========================================="
echo "🎉 开发环境启动完成！"
echo ""
echo "访问地址："
echo "  - 后端 API: http://localhost:8000"
echo "  - API 文档: http://localhost:8000/api/docs"
echo "  - Flower 监控: http://localhost:5555"
echo ""
echo "日志查看："
echo "  docker-compose -f docker-compose.dev.yml logs -f"
echo ""
echo "停止服务："
echo "  docker-compose -f docker-compose.dev.yml down"
echo "=========================================="
