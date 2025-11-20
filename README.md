# 🍎 Apple ID 自动解锁 & 批量管理系统（商业版）

<div align="center">

[![License](https://img.shields.io/badge/license-Commercial-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)](https://fastapi.tiangolo.com/)
[![Vue](https://img.shields.io/badge/Vue-3.3+-brightgreen.svg)](https://vuejs.org/)
[![Docker](https://img.shields.io/badge/docker-ready-blue.svg)](https://www.docker.com/)

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
- **框架**: FastAPI 0.104+
- **数据库**: PostgreSQL 15+
- **缓存**: Redis 7.0+
- **任务队列**: Celery 5.3+
- **ORM**: SQLAlchemy 2.0+
- **认证**: JWT (python-jose)
- **密码加密**: Bcrypt (passlib)
- **HTML 过滤**: Bleach

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
nano backend/.env  # 修改必要配置

# 3. 生成密钥
python3 -c "import secrets; print(secrets.token_urlsafe(64))"

# 4. 启动服务
docker-compose up -d

# 5. 初始化数据库
docker-compose exec backend alembic upgrade head

# 6. 访问系统
# 前端: http://localhost
# API 文档: http://localhost/api/docs
# Flower: http://localhost:5555
```

### 默认账号
- **用户名**: admin
- **密码**: Admin@123456
- ⚠️ **首次登录后请立即修改密码！**

---

## 📁 项目结构

```
appleid-auto/
├── backend/                    # 后端代码
│   ├── app/
│   │   ├── api/               # API 路由
│   │   │   └── v1/
│   │   │       ├── endpoints/ # 端点实现
│   │   │       └── api.py     # 路由汇总
│   │   ├── core/              # 核心配置
│   │   │   ├── config.py      # 配置管理
│   │   │   └── security.py    # 安全工具
│   │   ├── db/                # 数据库
│   │   │   ├── database.py    # 数据库连接
│   │   │   └── redis.py       # Redis 连接
│   │   ├── models/            # 数据库模型
│   │   │   ├── user.py
│   │   │   ├── card.py
│   │   │   ├── apple_account.py
│   │   │   ├── share_page.py
│   │   │   └── ...
│   │   ├── schemas/           # Pydantic Schemas
│   │   ├── services/          # 业务逻辑
│   │   ├── tasks/             # Celery 任务
│   │   ├── utils/             # 工具函数
│   │   │   └── html_filter.py # HTML 安全过滤
│   │   └── main.py            # 应用入口
│   ├── alembic/               # 数据库迁移
│   ├── tests/                 # 测试
│   ├── requirements.txt       # Python 依赖
│   ├── Dockerfile            # Docker 镜像
│   └── .env.example          # 环境变量模板
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
├── scripts/                   # 脚本
│   ├── backup.sh             # 备份脚本
│   └── create_admin.py       # 创建管理员
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

---

## ⚙️ 配置说明

### 必须修改的配置（backend/.env）

```bash
# 应用密钥（必须修改！）
SECRET_KEY=your-secret-key-here-change-in-production
JWT_SECRET_KEY=your-jwt-secret-key-change-in-production

# 数据库配置
DATABASE_URL=postgresql+asyncpg://postgres:postgres@postgres:5432/appleid_auto

# Redis 配置
REDIS_URL=redis://redis:6379/0

# 管理员账号
ADMIN_USERNAME=admin
ADMIN_EMAIL=admin@appleid-auto.local
ADMIN_PASSWORD=Admin@123456  # 请修改强密码

# CORS（生产环境修改为实际域名）
CORS_ORIGINS=["https://your-domain.com"]
```

### 可选配置

```bash
# 邮件通知（可选）
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-password

# 性能优化
DATABASE_POOL_SIZE=50
CELERY_CONCURRENCY=8
WORKERS=4

# 安全配置
MAX_LOGIN_ATTEMPTS=5
CARD_MAX_ATTEMPTS=3
RATE_LIMIT_PER_MINUTE=60
```

---

## 💻 开发指南

### 后端开发

```bash
# 进入后端目录
cd backend

# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt

# 运行开发服务器
uvicorn app.main:app --reload

# 运行测试
pytest

# 代码格式化
black app/
isort app/
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

### 数据库迁移

```bash
# 创建迁移文件
alembic revision --autogenerate -m "描述"

# 执行迁移
alembic upgrade head

# 回滚
alembic downgrade -1
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

### Q: 如何修改管理员密码？
A: 登录后在个人设置中修改，或使用脚本：
```bash
docker-compose exec backend python scripts/reset_password.py
```

### Q: 如何生成卡密？
A: 使用管理员账号登录，进入"卡密管理" → "生成卡密"

### Q: 如何配置 SSL 证书？
A: 参考 [SSL 证书配置](docs/04-部署指南.md#ssl-证书配置)

### Q: 如何备份数据？
A: 使用提供的备份脚本：
```bash
./scripts/backup.sh
```

更多问题请查看 [FAQ](docs/FAQ.md)（准备中）

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
- 邮箱: license@appleid-auto.com
- 微信: xxx

---

## 📞 联系方式

- **作者**: @Tracy
- **邮箱**: support@appleid-auto.com
- **官网**: https://appleid-auto.com
- **文档**: https://docs.appleid-auto.com
- **GitHub**: https://github.com/yourusername/appleid-auto

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
