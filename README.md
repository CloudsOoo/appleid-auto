# 🍎 Apple ID 自动解锁 & 批量管理系统（商业版）

<div align="center">

[![License](https://img.shields.io/badge/license-Commercial-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109+-green.svg)](https://fastapi.tiangolo.com/)
[![Vue](https://img.shields.io/badge/Vue-3.3+-brightgreen.svg)](https://vuejs.org/)
[![Docker](https://img.shields.io/badge/docker-ready-blue.svg)](https://www.docker.com/)
[![Backend](https://img.shields.io/badge/backend-99%25%20complete-brightgreen.svg)](#开发进度)

**一个功能完整的商业级 SaaS 系统，用于 Apple ID 自动化管理、解锁和批量操作**

[功能特性](#功能特性) •
[快速开始](#快速开始) •
[文档](#文档) •
[技术栈](#技术栈) •
[截图](#截图) •
[License](#license)

</div>

---

## 📋 目录

- [项目简介](#项目简介)
- [核心功能](#核心功能)
- [技术栈](#技术栈)
- [快速开始](#快速开始)
- [项目结构](#项目结构)
- [文档](#文档)
- [配置说明](#配置说明)
- [开发指南](#开发指南)
- [部署](#部署)
- [常见问题](#常见问题)
- [贡献](#贡献)
- [License](#license)

---

## 🎯 项目简介

Apple ID 自动解锁系统是一个功能强大的商业级 SaaS 平台，专为需要管理大量 Apple ID 账号的用户设计。系统提供自动解锁、批量管理、分享页生成、代理池管理等全方位功能。

### 为什么选择我们？

✅ **全自动化** - 定时检测、自动解锁、无需人工干预
✅ **商业级** - 完整的权限系统、卡密授权、多租户支持
✅ **高性能** - 异步架构、任务队列、分布式部署
✅ **安全可靠** - HTML 白名单过滤、XSS 防护、加密存储
✅ **易于部署** - Docker 一键部署、完整文档
✅ **功能丰富** - 分享页、代理池、节点集群、API 接口

---

## 🚀 核心功能

### 1️⃣ Apple ID 全自动处理

- ✅ 定时检测账号锁定状态
- ✅ 自动解锁（使用密保问题）
- ✅ 自动关闭 2FA
- ✅ 自动修改密码并记录历史
- ✅ 自动删除所有设备
- ✅ 自动检测/修改 App Store 地区
- ✅ 自动检测/修改语言和姓名
- ✅ 自动移除"丢失模式"设备
- ✅ 支持批量账号管理
- ✅ 支持分类标签
- ✅ 支持导入导出（CSV/Excel）

### 2️⃣ 分享页系统（参考 appleauto.pro）

- ✅ 多账号随机/顺序显示
- ✅ 密码访问保护
- ✅ 有效期控制
- ✅ 访问次数限制
- ✅ 域名白名单绑定
- ✅ 多模板支持
- ⭐ **自定义 HTML** (Header/Body/Footer)
- ✅ 访问日志记录
- ✅ 统计分析

### 3️⃣ 代理池 + 后端集群

- ✅ 支持多个解锁节点
- ✅ 节点自动注册/剔除
- ✅ 任务智能分发
- ✅ IP 池自动轮换
- ✅ 请求失败自动切换
- ✅ 支持 Socks5/HTTP 代理
- ✅ 代理健康检查
- ✅ 负载均衡

### 4️⃣ 用户系统 & 权限管理

可配置的用户权限：
- 📊 最大可添加账号数量
- ⏰ 最短解锁间隔
- 🎨 自定义 HTML 权限
- 📄 分享页数量限制
- 🔑 历史密码查看权限
- 🖥️ 节点数量限制
- 📥 账号导入限制

### 5️⃣ 卡密授权系统

- ✅ 纯本地生成（不对接发卡网）
- ✅ 支持三种类型：
  - ⏱️ 按天（time）
  - 🔢 按次数（usage）
  - ♾️ 永久（permanent）
- ✅ 批量生成
- ✅ 导出 CSV/TXT
- ✅ 激活日志
- ✅ 使用统计
- ✅ 手动作废/延期

### 6️⃣ 其他功能

- 📊 数据统计分析
- 📝 操作日志
- 🔔 Webhook 通知（可选）
- 🔐 2FA 双因素认证
- 🌍 多语言支持（准备中）
- 📱 移动端适配（准备中）

---

## 🛠️ 技术栈

### 后端
- **框架**: FastAPI 0.109.2
- **数据库**: PostgreSQL 15+ (asyncpg 0.29.0)
- **缓存**: Redis 5.0.1
- **任务队列**: Celery 5.3.6 + Gevent 24.2.1
- **ORM**: SQLAlchemy 2.0.28 (async)
- **数据验证**: Pydantic 2.6.1
- **认证**: JWT (python-jose 3.3.0)
- **密码加密**: Bcrypt (passlib 1.7.4)
- **HTML 过滤**: Bleach 6.1.0
- **HTTP 客户端**: HTTPX 0.27.0
- **2FA**: PyOTP 2.9.0

### 前端
- **框架**: Vue 3.3+ (Composition API)
- **UI 库**: Element Plus 2.4+
- **状态管理**: Pinia
- **路由**: Vue Router 4
- **HTTP**: Axios
- **构建**: Vite 5

### 部署
- **容器化**: Docker + Docker Compose
- **反向代理**: Nginx
- **SSL**: Let's Encrypt (Certbot)
- **监控**: Flower (Celery)

---

## ⚡ 快速开始

### 前置要求
- Docker 20.10+
- Docker Compose 2.0+
- Git

### 一键启动

```bash
# 1. 克隆项目
git clone https://github.com/CloudsOoo/appleid-auto.git
cd appleid-auto

# 2. 配置环境变量
cp backend/.env.example backend/.env

# 3. 修改必要配置（特别是密钥）
nano backend/.env
# 生成随机密钥：
# python3 -c "import secrets; print(secrets.token_urlsafe(64))"

# 4. 启动基础服务（PostgreSQL、Redis）
docker-compose up -d db redis

# 5. 初始化数据库（创建表和默认管理员）
docker-compose exec backend python scripts/init_db.py
# 或本地运行：
# cd backend && python scripts/init_db.py

# 6. 启动所有服务
docker-compose up -d

# 7. 访问系统
# API 文档: http://localhost:8000/api/docs
# Flower (Celery监控): http://localhost:5555
# 前端: http://localhost (待开发)
```

### 默认管理员账号

初始化脚本会自动创建管理员账号（配置在 `.env` 文件中）：

- **用户名**: admin（可在 `.env` 中修改 `ADMIN_USERNAME`）
- **邮箱**: admin@appleid-auto.local（可修改 `ADMIN_EMAIL`）
- **密码**: Admin@123456（可修改 `ADMIN_PASSWORD`）

⚠️ **重要安全提示**:
1. 首次登录后立即修改密码
2. 生产环境必须修改默认密码
3. 使用强密码（包含大小写字母、数字、特殊字符）

---

## 📁 项目结构

```
appleid-auto/
├── backend/                    # 后端代码
│   ├── app/
│   │   ├── api/               # API 路由
│   │   │   ├── middleware.py  # 中间件
│   │   │   └── v1/
│   │   │       ├── dependencies.py # 依赖注入
│   │   │       ├── endpoints/ # API 端点实现
│   │   │       │   ├── auth.py        # 认证 (9个端点)
│   │   │       │   ├── users.py       # 用户管理
│   │   │       │   ├── cards.py       # 卡密 (7个端点)
│   │   │       │   ├── accounts.py    # Apple ID (9个端点)
│   │   │       │   ├── tasks.py       # 任务 (5个端点)
│   │   │       │   ├── share_pages.py # 分享页 (8个端点)
│   │   │       │   ├── proxies.py     # 代理池 (6个端点)
│   │   │       │   ├── nodes.py       # 节点 (5个端点)
│   │   │       │   ├── packages.py    # 套餐 (6个端点)
│   │   │       │   ├── stats.py       # 统计 (2个端点)
│   │   │       │   └── admin.py       # 管理员
│   │   │       └── api.py     # 路由汇总 (57个端点)
│   │   ├── core/              # 核心配置
│   │   │   ├── config.py      # 配置管理
│   │   │   └── security.py    # 安全工具 (JWT、密码哈希)
│   │   ├── db/                # 数据库
│   │   │   ├── database.py    # 数据库连接 (SQLAlchemy异步)
│   │   │   └── redis.py       # Redis 连接
│   │   ├── models/            # 数据库模型 (11个模型)
│   │   │   ├── user.py
│   │   │   ├── permission.py  # 权限、套餐
│   │   │   ├── card.py        # 卡密、卡密日志
│   │   │   ├── apple_account.py # Apple ID、密码历史
│   │   │   ├── task.py        # 解锁任务
│   │   │   ├── share_page.py  # 分享页、访问日志
│   │   │   ├── proxy.py       # 代理池
│   │   │   ├── node.py        # 节点
│   │   │   ├── package.py     # 套餐
│   │   │   └── system.py      # 系统设置、API密钥、操作日志
│   │   ├── schemas/           # Pydantic Schemas (35+ schemas)
│   │   ├── services/          # 业务逻辑层 (8个服务)
│   │   │   ├── auth_service.py       # 认证服务
│   │   │   ├── card_service.py       # 卡密服务
│   │   │   ├── apple_account_service.py # Apple ID服务
│   │   │   ├── task_service.py       # 任务服务
│   │   │   ├── share_page_service.py # 分享页服务
│   │   │   ├── proxy_service.py      # 代理池服务
│   │   │   ├── node_service.py       # 节点服务
│   │   │   ├── package_service.py    # 套餐服务
│   │   │   └── permission_service.py # 权限服务
│   │   ├── tasks/             # Celery 任务 (10个任务)
│   │   │   ├── account_tasks.py    # 账号检测、解锁
│   │   │   ├── maintenance_tasks.py # 维护任务
│   │   │   └── scheduled_tasks.py  # 定时任务
│   │   ├── utils/             # 工具函数
│   │   │   ├── encryption.py  # 加密解密
│   │   │   └── html_filter.py # HTML 安全过滤
│   │   ├── celery_app.py      # Celery 应用配置
│   │   └── main.py            # FastAPI 应用入口
│   ├── scripts/               # 初始化脚本 ✨ 新增
│   │   ├── init_db.py         # 数据库初始化（创建表、管理员）
│   │   └── README.md          # 脚本使用文档
│   ├── alembic/               # 数据库迁移
│   │   ├── versions/          # 迁移版本
│   │   ├── env.py             # Alembic 配置
│   │   └── alembic.ini        # Alembic 配置
│   ├── tests/                 # 测试 (待开发)
│   ├── requirements.txt       # Python 依赖 (25个核心包)
│   ├── Dockerfile             # Docker 镜像
│   └── .env.example           # 环境变量模板 (254行)
│
├── frontend/                  # 前端代码
│   ├── public/               # 静态资源
│   ├── src/
│   │   ├── api/              # API 请求
│   │   ├── components/       # 组件
│   │   │   ├── admin/        # 管理员组件
│   │   │   ├── user/         # 用户组件
│   │   │   └── share/        # 分享页组件
│   │   ├── pages/            # 页面
│   │   ├── router/           # 路由
│   │   ├── stores/           # 状态管理
│   │   └── main.js           # 入口文件
│   ├── package.json          # 前端依赖
│   └── vite.config.js        # Vite 配置
│
├── nginx/                     # Nginx 配置
│   ├── nginx.conf            # Nginx 主配置
│   └── ssl/                  # SSL 证书
│
├── docs/                      # 文档
│   ├── 01-系统架构设计.md
│   ├── 02-数据库设计.md
│   ├── 03-API接口文档.md
│   ├── 04-部署指南.md
│   └── ...
│
├── docker-compose.yml         # Docker Compose 配置
├── .gitignore
├── LICENSE
└── README.md                  # 本文件
```

---

## 📚 文档

完整文档位于 `docs/` 目录：

1. **[系统架构设计](docs/01-系统架构设计.md)** - 技术栈、架构图、模块说明
2. **[数据库设计](docs/02-数据库设计.md)** - 完整的表结构、字段说明
3. **[API 接口文档](docs/03-API接口文档.md)** - 所有 API 端点的详细说明
4. **[部署指南](docs/04-部署指南.md)** - 生产环境部署、SSL 配置、集群部署
5. **[剩余开发任务清单](docs/06-剩余开发任务清单.md)** - 开发进度追踪

---

## 📈 开发进度

### 后端开发 - 99% 完成 ✨

#### ✅ 已完成模块（13000+ 行代码）

| 模块 | 完成度 | 代码量 | 说明 |
|------|--------|--------|------|
| **数据库模型** | 100% | 11个模型 | User、Permission、Card、Account、Task等 |
| **Pydantic Schemas** | 100% | 35+ schemas | 完整的数据验证和序列化 |
| **Service 层** | 100% | 3500+ 行 | 8个核心服务，完整的业务逻辑 |
| **API 端点** | 100% | 5500+ 行 | 57个端点，涵盖所有核心功能 |
| **Celery 任务系统** | 100% | 1950+ 行 | 10个异步任务，定时调度 |
| **依赖注入与中间件** | 100% | 1000+ 行 | 权限控制、日志、限流、监控 |
| **应用集成** | 100% | 107 行 | FastAPI应用入口、中间件注册 |
| **项目配置** | 100% | 405+ 行 | .env.example、requirements.txt |
| **初始化脚本** | 100% | 392 行 | 数据库初始化、默认管理员 |

#### 🚧 待完成

- [ ] 前端开发（Vue3 + TypeScript + Element Plus）
- [ ] 单元测试和集成测试
- [ ] Apple 自动化脚本集成（Playwright/Selenium）

#### 📊 API 端点统计

**共 57 个 API 端点**：
- 认证 (auth): 9个端点（注册、登录、2FA等）
- 卡密 (cards): 7个端点（生成、激活、管理）
- Apple ID (accounts): 9个端点（CRUD、导入导出）
- 任务 (tasks): 5个端点（创建、查询、取消）
- 分享页 (share_pages): 8个端点（CRUD、访问验证）
- 代理池 (proxies): 6个端点（CRUD、测试）
- 节点 (nodes): 5个端点（注册、心跳、管理）
- 套餐 (packages): 6个端点（CRUD、公开列表）
- 统计 (stats): 2个端点（用户统计、管理员统计）

所有端点均包含：
- 完整的请求/响应模型
- 权限控制（用户/管理员）
- 错误处理
- API 文档（OpenAPI/Swagger）

---

## ⚙️ 配置说明

### 环境变量配置（backend/.env）

完整的配置模板见 `backend/.env.example`（254行，19个配置分类）

#### 🔴 必须修改的配置

```bash
# 应用密钥（必须修改！生成方式见下方）
SECRET_KEY=your-secret-key-here-please-change-it
JWT_SECRET_KEY=your-jwt-secret-key-here-please-change-it

# 生成随机密钥：
# python3 -c "import secrets; print(secrets.token_urlsafe(64))"

# 数据库配置
DATABASE_URL=postgresql+asyncpg://postgres:postgres@db:5432/appleid_auto

# Redis 配置
REDIS_URL=redis://redis:6379/0
CELERY_BROKER_URL=redis://redis:6379/1
CELERY_RESULT_BACKEND=redis://redis:6379/2

# 管理员账号（初始化脚本会使用）
ADMIN_USERNAME=admin
ADMIN_EMAIL=admin@appleid-auto.local
ADMIN_PASSWORD=Admin@123456  # ⚠️ 生产环境务必修改

# CORS（生产环境修改为实际域名）
CORS_ORIGINS=http://localhost:3000,http://localhost:5173
```

#### ⚙️ 可选配置

```bash
# 应用配置
APP_ENV=development  # production / development
DEBUG=True           # 生产环境设为 False

# 服务器配置
HOST=0.0.0.0
PORT=8000
WORKERS=4            # 建议设为 CPU 核心数 * 2 + 1

# 数据库连接池
DATABASE_POOL_SIZE=20
DATABASE_MAX_OVERFLOW=10

# 邮件通知（可选）
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
EMAIL_FROM=noreply@appleid-auto.local

# Apple API 配置
APPLE_API_TIMEOUT=30
APPLE_API_MAX_RETRIES=3

# 代理配置
PROXY_CHECK_INTERVAL=300  # 5分钟
PROXY_TIMEOUT=10

# 节点配置
NODE_HEARTBEAT_INTERVAL=60      # 1分钟
NODE_OFFLINE_THRESHOLD=180      # 3分钟

# 任务配置
DEFAULT_CHECK_INTERVAL=3600     # 1小时
MAX_UNLOCK_RETRIES=3

# 安全配置
MAX_LOGIN_ATTEMPTS=5
LOGIN_ATTEMPT_TIMEOUT=300       # 5分钟
CARD_MAX_ATTEMPTS=3
CARD_ATTEMPT_TIMEOUT=3600       # 1小时

# 限流配置
RATE_LIMIT_ENABLED=True
RATE_LIMIT_PER_MINUTE=60

# 日志配置
LOG_LEVEL=INFO
LOG_FILE=./logs/app.log
```

完整配置项说明请查看 `backend/.env.example`

---

## 💻 开发指南

### 后端开发

```bash
# 1. 进入后端目录
cd backend

# 2. 创建虚拟环境
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 3. 安装依赖
pip install -r requirements.txt

# 4. 配置环境变量
cp .env.example .env
nano .env  # 修改必要配置

# 5. 启动 PostgreSQL 和 Redis（Docker）
docker-compose up -d db redis

# 6. 初始化数据库
python scripts/init_db.py

# 7. 运行开发服务器
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 8. 启动 Celery Worker（新终端）
celery -A app.celery_app worker --loglevel=info --pool=gevent --concurrency=100

# 9. 启动 Celery Beat（新终端）
celery -A app.celery_app beat --loglevel=info

# 10. 启动 Flower（Celery 监控，可选）
celery -A app.celery_app flower --port=5555

# 访问：
# - API 文档: http://localhost:8000/api/docs
# - Flower: http://localhost:5555
```

#### 代码质量工具

```bash
# 代码格式化
black app/
isort app/

# 代码检查
flake8 app/
pylint app/

# 类型检查
mypy app/

# 运行测试
pytest tests/ -v

# 测试覆盖率
pytest tests/ --cov=app --cov-report=html
```

### 前端开发

```bash
# 进入前端目录
cd frontend

# 安装依赖
npm install

# 运行开发服务器
npm run dev

# 构建生产版本
npm run build

# 代码格式化
npm run format
```

### 数据库管理

#### 初始化数据库（首次使用）

```bash
# 使用初始化脚本（推荐）
cd backend
python scripts/init_db.py

# 脚本功能：
# 1. 创建所有数据库表（15个表）
# 2. 创建默认管理员账号
# 3. 初始化管理员权限（无限配额）
# 4. 验证数据库连接

# 查看详细说明：
cat scripts/README.md
```

#### 数据库迁移（Alembic）

```bash
# 生成迁移文件（自动检测模型变化）
alembic revision --autogenerate -m "描述变更内容"

# 执行迁移（升级到最新版本）
alembic upgrade head

# 查看当前版本
alembic current

# 查看迁移历史
alembic history

# 回滚到上一个版本
alembic downgrade -1

# 回滚到指定版本
alembic downgrade <revision_id>
```

#### 重置数据库（开发环境）

```bash
# ⚠️ 警告：将删除所有数据！

# 方法 1：使用 Docker
docker-compose exec db psql -U postgres -c "DROP DATABASE appleid_auto; CREATE DATABASE appleid_auto;"
python scripts/init_db.py

# 方法 2：删除 Docker 卷
docker-compose down -v
docker-compose up -d db redis
python scripts/init_db.py
```

---

## 🚢 部署

### 单机部署
```bash
docker-compose up -d
```

### 生产环境部署
参考 [部署指南](docs/04-部署指南.md)

### 集群部署
支持多节点、负载均衡、数据库主从复制

详见 [集群部署](docs/04-部署指南.md#集群部署)

---

## ❓ 常见问题

### Q: 首次部署如何初始化数据库？

A: 使用初始化脚本（推荐）：
```bash
# Docker 环境
docker-compose up -d db redis
docker-compose exec backend python scripts/init_db.py

# 本地环境
cd backend
python scripts/init_db.py
```

脚本会自动创建所有表和默认管理员账号。详见 `backend/scripts/README.md`

### Q: 忘记管理员密码怎么办？

A: 方法 1 - 重新运行初始化脚本（会跳过已存在的账号）：
```bash
python scripts/init_db.py
```

方法 2 - 直接修改 `.env` 中的 `ADMIN_PASSWORD` 后重新运行初始化脚本。

方法 3 - 登录数据库手动重置：
```bash
docker-compose exec db psql -U postgres appleid_auto
UPDATE users SET password_hash = '<new_hash>' WHERE username = 'admin';
```

### Q: 数据库连接失败怎么办？

A: 检查以下几点：
1. PostgreSQL 服务是否运行：`docker-compose ps db`
2. `.env` 中的 `DATABASE_URL` 配置是否正确
3. 数据库是否已创建：`docker-compose exec db psql -U postgres -l`
4. 防火墙是否阻止了端口 5432

### Q: 如何生成卡密？

A: 使用管理员账号登录后：
1. 进入"卡密管理" → "生成卡密"
2. 选择类型（按天/按次/永久）、数量、套餐
3. 点击生成，可导出为 CSV/TXT

或通过 API：
```bash
curl -X POST http://localhost:8000/api/v1/cards/admin/generate \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"type": "time", "duration_days": 30, "quantity": 10, "package_id": 1}'
```

### Q: 如何配置 SSL 证书？

A: 参考 [SSL 证书配置](docs/04-部署指南.md#ssl-证书配置)

### Q: 如何监控 Celery 任务？

A: 访问 Flower 监控面板：
```bash
# 启动 Flower
celery -A app.celery_app flower --port=5555

# 访问 http://localhost:5555
```

### Q: 数据库表结构发生变化如何迁移？

A: 使用 Alembic 迁移：
```bash
# 自动生成迁移文件
alembic revision --autogenerate -m "描述变更"

# 执行迁移
alembic upgrade head
```

更多问题请查看：
- [脚本使用文档](backend/scripts/README.md)
- [部署指南](docs/04-部署指南.md)
- [API 文档](docs/03-API接口文档.md)

---

## 🤝 贡献

欢迎贡献代码、报告问题、提出建议！

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 提交 Pull Request

---

## 📄 License

本项目采用商业许可证。

**未经授权不得用于商业用途。**

如需商业授权，请联系：
- 邮箱: support@yszcpay.de
  
---

## 📞 联系方式

- **作者**: @Tracy
- **邮箱**: support@yszcpay.de
- **GitHub**: https://github.com/CloudsOoo/appleid-auto

---

## 🙏 致谢

- [FastAPI](https://fastapi.tiangolo.com/) - 现代化的 Python Web 框架
- [Vue.js](https://vuejs.org/) - 渐进式 JavaScript 框架
- [Element Plus](https://element-plus.org/) - Vue 3 UI 组件库
- [appleauto.pro](https://appleauto.pro/) - 参考设计

---

## ⭐ Star History

如果这个项目对你有帮助，请给一个 ⭐️ Star！

---

<div align="center">

**Built with ❤️ by Tracy**

© 2025 Apple ID Auto. All Rights Reserved.

</div>
