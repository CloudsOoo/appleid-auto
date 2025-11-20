# 初始化脚本使用指南

本目录包含数据库初始化和管理脚本。

## 📋 脚本列表

### 1. init_db.py - 数据库初始化脚本

**功能**：
- 创建所有数据库表
- 创建默认管理员账号
- 初始化管理员权限
- 验证数据库连接

**使用方法**：

```bash
# 方法 1：直接运行（需要先配置 .env 文件）
cd backend
python scripts/init_db.py

# 方法 2：使用 Docker Compose
docker-compose exec backend python scripts/init_db.py
```

**环境变量**：

脚本从 `.env` 文件读取以下配置：

```bash
# 数据库配置
DATABASE_URL=postgresql+asyncpg://postgres:postgres@db:5432/appleid_auto

# 管理员账号配置
ADMIN_USERNAME=admin              # 管理员用户名
ADMIN_EMAIL=admin@example.com     # 管理员邮箱
ADMIN_PASSWORD=Admin@123456       # 管理员密码（首次登录后请修改）
```

**输出示例**：

```
============================================================
🚀 Apple ID 自动解锁系统 - 数据库初始化
============================================================
📋 开始创建数据库表...
✅ 数据库表创建成功！
   创建的表：15 个
   - users
   - user_permissions
   - packages
   - cards
   ...

👤 检查默认管理员账号...
📝 创建管理员账号：admin
✅ 管理员账号创建成功！
   用户名: admin
   邮箱: admin@appleid-auto.local
   密码: Admin@123456
   ID: 1

🔑 检查管理员权限...
📝 创建管理员权限...
✅ 管理员权限创建成功！
   账号配额: 无限制
   分享页配额: 无限制
   节点配额: 无限制
   代理配额: 无限制
   功能权限: 全部开启

🔍 验证数据库...
✅ 数据库连接正常
   用户数量: 1

============================================================
🎉 数据库初始化完成！
============================================================

📝 管理员登录信息：
   用户名: admin
   密码: Admin@123456
   邮箱: admin@appleid-auto.local

⚠️  请在首次登录后立即修改管理员密码！

🔗 API 文档: http://localhost:8000/api/docs
============================================================
```

## 🚀 快速开始

### 步骤 1：配置环境变量

```bash
cd backend
cp .env.example .env
# 编辑 .env 文件，修改必要的配置项（特别是 SECRET_KEY 和 JWT_SECRET_KEY）
```

### 步骤 2：启动数据库服务

```bash
# 使用 Docker Compose 启动 PostgreSQL 和 Redis
docker-compose up -d db redis
```

### 步骤 3：运行初始化脚本

```bash
# 方法 1：本地运行
python scripts/init_db.py

# 方法 2：Docker 容器内运行
docker-compose exec backend python scripts/init_db.py
```

### 步骤 4：启动应用

```bash
# 方法 1：本地运行
python -m app.main

# 方法 2：使用 Uvicorn
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 方法 3：Docker Compose
docker-compose up backend
```

### 步骤 5：访问 API 文档

打开浏览器访问：http://localhost:8000/api/docs

使用管理员账号登录：
- 用户名：`admin`（或 .env 中配置的 ADMIN_USERNAME）
- 密码：`Admin@123456`（或 .env 中配置的 ADMIN_PASSWORD）

## 📚 Alembic 数据库迁移

### 生成迁移文件

```bash
cd backend

# 自动生成迁移（检测模型变化）
alembic revision --autogenerate -m "Initial migration"

# 手动创建迁移
alembic revision -m "Add new column"
```

### 应用迁移

```bash
# 升级到最新版本
alembic upgrade head

# 查看当前版本
alembic current

# 查看迁移历史
alembic history

# 降级到上一个版本
alembic downgrade -1

# 降级到指定版本
alembic downgrade <revision_id>
```

### 迁移文件位置

- 迁移配置：`backend/alembic.ini`
- 迁移脚本：`backend/alembic/env.py`
- 迁移版本：`backend/alembic/versions/*.py`

## ⚠️ 注意事项

### 1. 数据库连接

确保 PostgreSQL 服务正在运行，并且 `.env` 中的 `DATABASE_URL` 配置正确。

### 2. 开发模式

在 **开发模式** (`DEBUG=True`)，`init_db.py` 会先删除所有表再重新创建。

⚠️ **生产环境请务必设置 `DEBUG=False`**，避免数据丢失！

### 3. 密码安全

- 首次运行后，请立即修改管理员密码
- 生产环境必须修改 `.env` 中的 `ADMIN_PASSWORD`
- 生产环境必须使用强密码（包含大小写字母、数字、特殊字符）

### 4. 密钥安全

- `SECRET_KEY` 和 `JWT_SECRET_KEY` 必须是随机生成的强密钥
- 生成方式：`python3 -c "import secrets; print(secrets.token_urlsafe(64))"`
- 生产环境禁止使用示例密钥

### 5. 重新初始化

如果需要完全重新初始化数据库（**仅开发环境**）：

```bash
# 方法 1：手动删除数据库
docker-compose exec db psql -U postgres -c "DROP DATABASE appleid_auto; CREATE DATABASE appleid_auto;"

# 方法 2：删除 Docker 卷
docker-compose down -v
docker-compose up -d db redis

# 重新运行初始化脚本
python scripts/init_db.py
```

## 🔧 故障排查

### 问题 1：数据库连接失败

**错误**：`FATAL: password authentication failed for user "postgres"`

**解决**：
1. 检查 `.env` 中的 `DATABASE_URL` 配置
2. 确认 PostgreSQL 服务正在运行：`docker-compose ps`
3. 检查 PostgreSQL 日志：`docker-compose logs db`

### 问题 2：表已存在

**错误**：`relation "users" already exists`

**解决**：
- 开发环境：设置 `DEBUG=True`，脚本会自动删除旧表
- 生产环境：使用 Alembic 迁移管理表结构变更

### 问题 3：模块导入失败

**错误**：`ModuleNotFoundError: No module named 'app'`

**解决**：
1. 确保在 `backend` 目录下运行脚本
2. 确保已安装所有依赖：`pip install -r requirements.txt`

### 问题 4：权限问题

**错误**：`Permission denied: 'scripts/init_db.py'`

**解决**：
```bash
chmod +x scripts/init_db.py
```

## 📞 技术支持

如果遇到其他问题，请：
1. 检查日志输出的详细错误信息
2. 查看项目文档：`docs/`
3. 提交 Issue 到项目仓库
