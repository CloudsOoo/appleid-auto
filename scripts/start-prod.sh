#!/bin/bash

# Apple ID Auto 系统 - 生产环境启动脚本
# 使用方法: ./scripts/start-prod.sh

set -e

echo "🚀 启动 Apple ID Auto 生产环境..."

# 检查必要条件
if ! command -v docker &> /dev/null; then
    echo "❌ Docker 未安装"
    exit 1
fi

if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    echo "❌ Docker Compose 未安装"
    exit 1
fi

# 进入项目根目录
cd "$(dirname "$0")/.."

# 检查环境配置
if [ ! -f "backend/.env" ]; then
    echo "❌ 缺少 backend/.env 配置文件"
    echo "   请复制 backend/.env.example 并配置"
    exit 1
fi

# 检查 SSL 证书
if [ ! -f "nginx/ssl/cert.pem" ] || [ ! -f "nginx/ssl/key.pem" ]; then
    echo "⚠️ 警告: 缺少 SSL 证书"
    echo "   请将 cert.pem 和 key.pem 放入 nginx/ssl/ 目录"
    echo "   或使用 Let's Encrypt 获取免费证书"
fi

# 构建前端
echo "📦 构建前端..."
cd frontend
npm ci
npm run build
cd ..

# 启动 Docker 服务
echo "🐳 启动 Docker 服务..."
docker-compose up -d --build

# 等待服务启动
echo "⏳ 等待服务启动..."
sleep 15

# 检查服务状态
echo "📊 服务状态："
docker-compose ps

# 健康检查
echo ""
echo "🔍 健康检查："
for i in {1..5}; do
    if curl -s http://localhost:8000/health > /dev/null 2>&1; then
        echo "✅ 后端服务正常"
        break
    else
        echo "⏳ 等待后端启动... ($i/5)"
        sleep 5
    fi
done

echo ""
echo "=========================================="
echo "🎉 生产环境启动完成！"
echo ""
echo "日志查看："
echo "  docker-compose logs -f"
echo ""
echo "停止服务："
echo "  docker-compose down"
echo "=========================================="
