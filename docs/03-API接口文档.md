# Apple ID 自动解锁系统 - API 接口文档

## 基础信息

- **Base URL**: `https://api.yourdomain.com/api/v1`
- **认证方式**: JWT Bearer Token
- **Content-Type**: `application/json`
- **字符编码**: UTF-8

---

## 通用响应格式

### 成功响应
```json
{
  "code": 200,
  "message": "success",
  "data": { ... }
}
```

### 错误响应
```json
{
  "code": 400,
  "message": "错误信息",
  "errors": { ... }  // 可选，详细错误
}
```

### HTTP 状态码
- `200` - 成功
- `201` - 创建成功
- `400` - 请求错误
- `401` - 未认证
- `403` - 无权限
- `404` - 资源不存在
- `422` - 数据验证失败
- `429` - 请求过多
- `500` - 服务器错误

---

## 1. 认证模块

### 1.1 用户注册
```
POST /auth/register
```

**请求参数**:
```json
{
  "username": "user123",
  "email": "user@example.com",
  "password": "SecurePass123!"
}
```

**响应**:
```json
{
  "code": 201,
  "message": "注册成功",
  "data": {
    "id": 1,
    "username": "user123",
    "email": "user@example.com",
    "role": "user",
    "created_at": "2025-11-20T10:00:00Z"
  }
}
```

---

### 1.2 用户登录
```
POST /auth/login
```

**请求参数**:
```json
{
  "username": "user123",
  "password": "SecurePass123!"
}
```

**响应**:
```json
{
  "code": 200,
  "message": "登录成功",
  "data": {
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "token_type": "bearer",
    "expires_in": 3600,
    "user": {
      "id": 1,
      "username": "user123",
      "email": "user@example.com",
      "role": "user"
    }
  }
}
```

---

### 1.3 刷新令牌
```
POST /auth/refresh
Authorization: Bearer {refresh_token}
```

**响应**:
```json
{
  "code": 200,
  "message": "刷新成功",
  "data": {
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "token_type": "bearer",
    "expires_in": 3600
  }
}
```

---

### 1.4 登出
```
POST /auth/logout
Authorization: Bearer {access_token}
```

**响应**:
```json
{
  "code": 200,
  "message": "登出成功"
}
```

---

### 1.5 获取当前用户信息
```
GET /auth/me
Authorization: Bearer {access_token}
```

**响应**:
```json
{
  "code": 200,
  "data": {
    "id": 1,
    "username": "user123",
    "email": "user@example.com",
    "role": "user",
    "is_active": true,
    "two_factor_enabled": false,
    "created_at": "2025-11-20T10:00:00Z",
    "permissions": {
      "max_accounts": 50,
      "max_share_pages": 5,
      "expires_at": "2026-11-20T10:00:00Z"
    }
  }
}
```

---

### 1.6 修改密码
```
POST /auth/change-password
Authorization: Bearer {access_token}
```

**请求参数**:
```json
{
  "old_password": "OldPass123!",
  "new_password": "NewPass456!"
}
```

**响应**:
```json
{
  "code": 200,
  "message": "密码修改成功"
}
```

---

### 1.7 启用 2FA
```
POST /auth/2fa/enable
Authorization: Bearer {access_token}
```

**响应**:
```json
{
  "code": 200,
  "data": {
    "secret": "JBSWY3DPEHPK3PXP",
    "qr_code": "data:image/png;base64,iVBORw0KGgo...",
    "backup_codes": ["12345678", "87654321", ...]
  }
}
```

---

### 1.8 验证 2FA
```
POST /auth/2fa/verify
Authorization: Bearer {access_token}
```

**请求参数**:
```json
{
  "code": "123456"
}
```

**响应**:
```json
{
  "code": 200,
  "message": "2FA 启用成功"
}
```

---

## 2. 卡密模块

### 2.1 激活卡密
```
POST /cards/activate
Authorization: Bearer {access_token}
```

**请求参数**:
```json
{
  "card_code": "XXXX-XXXX-XXXX-XXXX"
}
```

**响应**:
```json
{
  "code": 200,
  "message": "激活成功",
  "data": {
    "card_type": "time",
    "duration_days": 30,
    "package": {
      "name": "专业版",
      "max_accounts": 200,
      "max_share_pages": 20
    },
    "expires_at": "2025-12-20T10:00:00Z"
  }
}
```

---

### 2.2 查询卡密状态
```
GET /cards/status
Authorization: Bearer {access_token}
```

**响应**:
```json
{
  "code": 200,
  "data": {
    "is_activated": true,
    "card_type": "time",
    "package_name": "专业版",
    "activated_at": "2025-11-20T10:00:00Z",
    "expires_at": "2025-12-20T10:00:00Z",
    "days_remaining": 30
  }
}
```

---

### 2.3 管理员：生成卡密
```
POST /admin/cards/generate
Authorization: Bearer {admin_access_token}
```

**请求参数**:
```json
{
  "card_type": "time",
  "package_id": 2,
  "duration_days": 30,
  "quantity": 10,
  "batch_id": "BATCH_2025_001",
  "note": "双十一活动"
}
```

**响应**:
```json
{
  "code": 201,
  "message": "生成成功",
  "data": {
    "batch_id": "BATCH_2025_001",
    "quantity": 10,
    "cards": [
      "AAAA-BBBB-CCCC-DDDD",
      "EEEE-FFFF-GGGG-HHHH",
      ...
    ]
  }
}
```

---

### 2.4 管理员：导出卡密
```
GET /admin/cards/export?batch_id=BATCH_2025_001&format=csv
Authorization: Bearer {admin_access_token}
```

**响应**: CSV 文件下载

---

### 2.5 管理员：卡密列表
```
GET /admin/cards?page=1&per_page=20&status=unused
Authorization: Bearer {admin_access_token}
```

**响应**:
```json
{
  "code": 200,
  "data": {
    "items": [
      {
        "id": 1,
        "card_code": "AAAA-BBBB-CCCC-DDDD",
        "card_type": "time",
        "status": "unused",
        "package_name": "专业版",
        "duration_days": 30,
        "created_at": "2025-11-20T10:00:00Z"
      }
    ],
    "total": 100,
    "page": 1,
    "per_page": 20,
    "total_pages": 5
  }
}
```

---

### 2.6 管理员：作废卡密
```
POST /admin/cards/{card_id}/revoke
Authorization: Bearer {admin_access_token}
```

**请求参数**:
```json
{
  "reason": "误操作"
}
```

**响应**:
```json
{
  "code": 200,
  "message": "作废成功"
}
```

---

## 3. Apple ID 管理模块

### 3.1 添加 Apple ID
```
POST /accounts
Authorization: Bearer {access_token}
```

**请求参数**:
```json
{
  "apple_id": "example@icloud.com",
  "password": "password123",
  "security_questions": [
    {
      "question": "您最喜欢的颜色是什么?",
      "answer": "蓝色"
    }
  ],
  "tags": ["工作", "美区"],
  "auto_unlock": true,
  "check_interval": 3600
}
```

**响应**:
```json
{
  "code": 201,
  "message": "添加成功",
  "data": {
    "id": 1,
    "apple_id": "example@icloud.com",
    "status": "normal",
    "created_at": "2025-11-20T10:00:00Z"
  }
}
```

---

### 3.2 账号列表
```
GET /accounts?page=1&per_page=20&status=normal&tag=工作
Authorization: Bearer {access_token}
```

**响应**:
```json
{
  "code": 200,
  "data": {
    "items": [
      {
        "id": 1,
        "apple_id": "example@icloud.com",
        "status": "normal",
        "lock_status": false,
        "two_factor_enabled": false,
        "app_store_country": "US",
        "devices_count": 3,
        "tags": ["工作", "美区"],
        "last_checked_at": "2025-11-20T09:00:00Z",
        "unlock_count": 5,
        "created_at": "2025-11-20T08:00:00Z"
      }
    ],
    "total": 45,
    "page": 1,
    "per_page": 20,
    "total_pages": 3
  }
}
```

---

### 3.3 账号详情
```
GET /accounts/{account_id}
Authorization: Bearer {access_token}
```

**响应**:
```json
{
  "code": 200,
  "data": {
    "id": 1,
    "apple_id": "example@icloud.com",
    "status": "normal",
    "lock_status": false,
    "two_factor_enabled": false,
    "app_store_country": "US",
    "app_store_language": "en",
    "account_name": "John Doe",
    "devices_count": 3,
    "has_lost_mode": false,
    "tags": ["工作", "美区"],
    "category": "personal",
    "auto_unlock": true,
    "auto_disable_2fa": false,
    "check_interval": 3600,
    "last_checked_at": "2025-11-20T09:00:00Z",
    "next_check_at": "2025-11-20T10:00:00Z",
    "last_unlocked_at": "2025-11-19T15:00:00Z",
    "unlock_count": 5,
    "note": "测试账号",
    "created_at": "2025-11-20T08:00:00Z"
  }
}
```

---

### 3.4 更新账号
```
PUT /accounts/{account_id}
Authorization: Bearer {access_token}
```

**请求参数**:
```json
{
  "password": "new_password123",
  "tags": ["工作", "美区", "付费"],
  "auto_unlock": false,
  "note": "更新备注"
}
```

**响应**:
```json
{
  "code": 200,
  "message": "更新成功"
}
```

---

### 3.5 删除账号
```
DELETE /accounts/{account_id}
Authorization: Bearer {access_token}
```

**响应**:
```json
{
  "code": 200,
  "message": "删除成功"
}
```

---

### 3.6 批量导入
```
POST /accounts/import
Authorization: Bearer {access_token}
Content-Type: multipart/form-data
```

**请求参数**:
- `file`: CSV 文件
- `format`: `csv` 或 `json`

**CSV 格式**:
```csv
apple_id,password,tags,note
example1@icloud.com,pass123,"工作,美区","备注1"
example2@icloud.com,pass456,"个人","备注2"
```

**响应**:
```json
{
  "code": 201,
  "message": "导入成功",
  "data": {
    "total": 100,
    "success": 95,
    "failed": 5,
    "errors": [
      {
        "line": 10,
        "apple_id": "invalid@email",
        "reason": "邮箱格式错误"
      }
    ]
  }
}
```

---

### 3.7 批量导出
```
GET /accounts/export?format=csv&status=normal
Authorization: Bearer {access_token}
```

**响应**: CSV 文件下载

---

### 3.8 查看密码历史
```
GET /accounts/{account_id}/password-history
Authorization: Bearer {access_token}
```

**响应**:
```json
{
  "code": 200,
  "data": {
    "items": [
      {
        "id": 1,
        "password": "new_password123",
        "changed_by": "auto",
        "created_at": "2025-11-20T10:00:00Z"
      },
      {
        "id": 2,
        "password": "old_password456",
        "changed_by": "manual",
        "created_at": "2025-11-19T10:00:00Z"
      }
    ]
  }
}
```

---

## 4. 任务管理模块

### 4.1 创建解锁任务
```
POST /tasks/unlock
Authorization: Bearer {access_token}
```

**请求参数**:
```json
{
  "account_ids": [1, 2, 3],
  "task_type": "unlock",
  "priority": 1
}
```

**响应**:
```json
{
  "code": 201,
  "message": "任务创建成功",
  "data": {
    "task_ids": ["task_abc123", "task_def456", "task_ghi789"],
    "created_count": 3
  }
}
```

---

### 4.2 任务列表
```
GET /tasks?page=1&per_page=20&status=success&task_type=unlock
Authorization: Bearer {access_token}
```

**响应**:
```json
{
  "code": 200,
  "data": {
    "items": [
      {
        "id": 1,
        "task_id": "task_abc123",
        "account_id": 1,
        "apple_id": "example@icloud.com",
        "task_type": "unlock",
        "status": "success",
        "started_at": "2025-11-20T10:00:00Z",
        "completed_at": "2025-11-20T10:01:30Z",
        "result": {
          "success": true,
          "message": "解锁成功"
        }
      }
    ],
    "total": 150,
    "page": 1,
    "per_page": 20
  }
}
```

---

### 4.3 任务详情
```
GET /tasks/{task_id}
Authorization: Bearer {access_token}
```

**响应**:
```json
{
  "code": 200,
  "data": {
    "id": 1,
    "task_id": "task_abc123",
    "account_id": 1,
    "task_type": "unlock",
    "status": "success",
    "priority": 0,
    "node_id": 1,
    "node_name": "节点1",
    "proxy_id": 5,
    "retry_count": 1,
    "result": {
      "success": true,
      "steps": [
        "获取代理",
        "连接 Apple 服务器",
        "验证密保问题",
        "解锁成功"
      ]
    },
    "started_at": "2025-11-20T10:00:00Z",
    "completed_at": "2025-11-20T10:01:30Z"
  }
}
```

---

### 4.4 取消任务
```
POST /tasks/{task_id}/cancel
Authorization: Bearer {access_token}
```

**响应**:
```json
{
  "code": 200,
  "message": "任务已取消"
}
```

---

### 4.5 手动触发检测
```
POST /accounts/{account_id}/check
Authorization: Bearer {access_token}
```

**响应**:
```json
{
  "code": 200,
  "message": "检测任务已创建",
  "data": {
    "task_id": "task_check_xyz"
  }
}
```

---

## 5. 分享页模块

### 5.1 创建分享页
```
POST /share-pages
Authorization: Bearer {access_token}
```

**请求参数**:
```json
{
  "title": "美区账号分享",
  "slug": "us-accounts",
  "description": "优质美区账号",
  "password": "pass123",
  "access_limit": 100,
  "expires_at": "2025-12-20T00:00:00Z",
  "allowed_domains": ["example.com", "test.com"],
  "display_mode": "random",
  "template": "default",
  "account_ids": [1, 2, 3, 4, 5],
  "custom_html_header": "<style>.custom { color: red; }</style>",
  "custom_html_body": "<div class=\"banner\">欢迎使用</div>",
  "custom_html_footer": "<footer>© 2025</footer>"
}
```

**响应**:
```json
{
  "code": 201,
  "message": "创建成功",
  "data": {
    "id": 1,
    "slug": "us-accounts",
    "share_url": "https://yourdomain.com/share/us-accounts",
    "created_at": "2025-11-20T10:00:00Z"
  }
}
```

---

### 5.2 分享页列表
```
GET /share-pages?page=1&per_page=20
Authorization: Bearer {access_token}
```

**响应**:
```json
{
  "code": 200,
  "data": {
    "items": [
      {
        "id": 1,
        "title": "美区账号分享",
        "slug": "us-accounts",
        "share_url": "https://yourdomain.com/share/us-accounts",
        "has_password": true,
        "access_limit": 100,
        "access_count": 45,
        "is_active": true,
        "expires_at": "2025-12-20T00:00:00Z",
        "total_views": 120,
        "unique_views": 80,
        "created_at": "2025-11-20T10:00:00Z"
      }
    ],
    "total": 5,
    "page": 1,
    "per_page": 20
  }
}
```

---

### 5.3 分享页详情
```
GET /share-pages/{share_page_id}
Authorization: Bearer {access_token}
```

**响应**:
```json
{
  "code": 200,
  "data": {
    "id": 1,
    "title": "美区账号分享",
    "slug": "us-accounts",
    "description": "优质美区账号",
    "share_url": "https://yourdomain.com/share/us-accounts",
    "has_password": true,
    "access_limit": 100,
    "access_count": 45,
    "expires_at": "2025-12-20T00:00:00Z",
    "allowed_domains": ["example.com"],
    "display_mode": "random",
    "template": "default",
    "account_ids": [1, 2, 3, 4, 5],
    "custom_html_header": "<style>...</style>",
    "custom_html_body": "<div>...</div>",
    "custom_html_footer": "<footer>...</footer>",
    "is_active": true,
    "total_views": 120,
    "unique_views": 80
  }
}
```

---

### 5.4 更新分享页
```
PUT /share-pages/{share_page_id}
Authorization: Bearer {access_token}
```

**请求参数**: 同创建分享页

**响应**:
```json
{
  "code": 200,
  "message": "更新成功"
}
```

---

### 5.5 删除分享页
```
DELETE /share-pages/{share_page_id}
Authorization: Bearer {access_token}
```

**响应**:
```json
{
  "code": 200,
  "message": "删除成功"
}
```

---

### 5.6 访问分享页（公开接口）
```
GET /public/share/{slug}
```

**请求参数**:
```json
{
  "password": "pass123"  // 如果有密码保护
}
```

**响应**:
```json
{
  "code": 200,
  "data": {
    "title": "美区账号分享",
    "description": "优质美区账号",
    "account": {
      "apple_id": "example@icloud.com",
      "password": "password123"
    },
    "custom_html": {
      "header": "<style>...</style>",
      "body": "<div>...</div>",
      "footer": "<footer>...</footer>"
    }
  }
}
```

---

### 5.7 分享页访问日志
```
GET /share-pages/{share_page_id}/logs?page=1&per_page=20
Authorization: Bearer {access_token}
```

**响应**:
```json
{
  "code": 200,
  "data": {
    "items": [
      {
        "id": 1,
        "ip_address": "1.2.3.4",
        "country": "CN",
        "city": "Beijing",
        "shown_account_id": 1,
        "access_granted": true,
        "created_at": "2025-11-20T10:00:00Z"
      }
    ],
    "total": 120,
    "page": 1,
    "per_page": 20
  }
}
```

---

## 6. 代理池模块

### 6.1 添加代理
```
POST /proxies
Authorization: Bearer {access_token}
```

**请求参数**:
```json
{
  "proxy_type": "socks5",
  "host": "proxy.example.com",
  "port": 1080,
  "username": "user",
  "password": "pass",
  "country": "US",
  "priority": 1
}
```

**响应**:
```json
{
  "code": 201,
  "message": "添加成功",
  "data": {
    "id": 1,
    "proxy_type": "socks5",
    "host": "proxy.example.com",
    "port": 1080,
    "status": "active"
  }
}
```

---

### 6.2 代理列表
```
GET /proxies?page=1&per_page=20&status=active
Authorization: Bearer {access_token}
```

**响应**:
```json
{
  "code": 200,
  "data": {
    "items": [
      {
        "id": 1,
        "proxy_type": "socks5",
        "host": "proxy.example.com",
        "port": 1080,
        "status": "active",
        "success_count": 150,
        "failure_count": 5,
        "avg_response_time": 250,
        "country": "US",
        "last_checked_at": "2025-11-20T09:50:00Z"
      }
    ],
    "total": 20,
    "page": 1,
    "per_page": 20
  }
}
```

---

### 6.3 测试代理
```
POST /proxies/{proxy_id}/test
Authorization: Bearer {access_token}
```

**响应**:
```json
{
  "code": 200,
  "data": {
    "success": true,
    "response_time": 245,
    "ip_address": "1.2.3.4",
    "country": "US"
  }
}
```

---

### 6.4 删除代理
```
DELETE /proxies/{proxy_id}
Authorization: Bearer {access_token}
```

**响应**:
```json
{
  "code": 200,
  "message": "删除成功"
}
```

---

## 7. 节点管理模块

### 7.1 注册节点
```
POST /nodes/register
Authorization: Bearer {access_token}
```

**请求参数**:
```json
{
  "node_name": "解锁节点1",
  "node_url": "https://node1.example.com",
  "country": "US",
  "region": "West"
}
```

**响应**:
```json
{
  "code": 201,
  "message": "注册成功",
  "data": {
    "id": 1,
    "node_name": "解锁节点1",
    "node_key": "node_key_abc123",
    "status": "online"
  }
}
```

---

### 7.2 节点列表
```
GET /nodes?page=1&per_page=20&status=online
Authorization: Bearer {access_token}
```

**响应**:
```json
{
  "code": 200,
  "data": {
    "items": [
      {
        "id": 1,
        "node_name": "解锁节点1",
        "node_url": "https://node1.example.com",
        "status": "online",
        "cpu_usage": 35.5,
        "memory_usage": 60.2,
        "task_queue_size": 5,
        "total_tasks": 1000,
        "success_tasks": 950,
        "failed_tasks": 50,
        "last_heartbeat_at": "2025-11-20T09:58:00Z"
      }
    ],
    "total": 3,
    "page": 1,
    "per_page": 20
  }
}
```

---

### 7.3 节点心跳（节点调用）
```
POST /nodes/heartbeat
Authorization: Bearer {node_key}
```

**请求参数**:
```json
{
  "cpu_usage": 35.5,
  "memory_usage": 60.2,
  "task_queue_size": 5
}
```

**响应**:
```json
{
  "code": 200,
  "message": "心跳成功"
}
```

---

### 7.4 删除节点
```
DELETE /nodes/{node_id}
Authorization: Bearer {access_token}
```

**响应**:
```json
{
  "code": 200,
  "message": "删除成功"
}
```

---

## 8. 套餐管理模块

### 8.1 获取套餐列表（公开接口）
```
GET /packages
```

**说明**: 无需登录，所有用户可访问。仅返回激活的套餐。

**响应**:
```json
{
  "code": 200,
  "data": [
    {
      "id": 1,
      "name": "免费版",
      "description": "适合个人用户",
      "max_accounts": 10,
      "max_share_pages": 5,
      "max_nodes": 1,
      "min_unlock_interval": 3600,
      "allow_custom_html": false,
      "allow_view_password_history": false,
      "allow_batch_import": true,
      "allow_api_access": false,
      "max_unlock_per_day": 100,
      "max_import_per_time": 100,
      "price": 0.00,
      "currency": "CNY",
      "is_active": true,
      "sort_order": 1,
      "created_at": "2025-11-20T10:00:00Z"
    },
    {
      "id": 2,
      "name": "专业版",
      "description": "适合中小企业",
      "max_accounts": 200,
      "max_share_pages": 20,
      "max_nodes": 5,
      "min_unlock_interval": 600,
      "allow_custom_html": true,
      "allow_view_password_history": true,
      "allow_batch_import": true,
      "allow_api_access": true,
      "max_unlock_per_day": 500,
      "max_import_per_time": 500,
      "price": 299.00,
      "currency": "CNY",
      "is_active": true,
      "sort_order": 2,
      "created_at": "2025-11-20T10:00:00Z"
    }
  ]
}
```

---

### 8.2 管理员：获取套餐列表（含禁用）
```
GET /packages/admin/packages?page=1&per_page=20&include_inactive=true
Authorization: Bearer {admin_access_token}
```

**说明**: 管理员接口，可查看所有套餐（包括禁用的）。

**响应**:
```json
{
  "code": 200,
  "data": {
    "total": 4,
    "page": 1,
    "per_page": 20,
    "total_pages": 1,
    "items": [
      {
        "id": 1,
        "name": "专业版",
        "description": "适合中小企业",
        "max_accounts": 200,
        "max_share_pages": 20,
        "max_nodes": 5,
        "allow_custom_html": true,
        "price": 299.00,
        "is_active": true
      }
    ]
  }
}
```

---

### 8.3 管理员：创建套餐
```
POST /packages/admin/packages
Authorization: Bearer {admin_access_token}
```

**请求参数**:
```json
{
  "name": "企业版",
  "description": "适合大型企业",
  "max_accounts": 1000,
  "max_share_pages": 100,
  "max_nodes": 20,
  "min_unlock_interval": 60,
  "allow_custom_html": true,
  "allow_view_password_history": true,
  "allow_batch_import": true,
  "allow_api_access": true,
  "max_unlock_per_day": 5000,
  "max_import_per_time": 1000,
  "price": 999.00,
  "currency": "CNY",
  "sort_order": 3
}
```

**响应**:
```json
{
  "code": 201,
  "message": "创建成功",
  "data": {
    "id": 3,
    "name": "企业版",
    "description": "适合大型企业",
    "max_accounts": 1000,
    "price": 999.00,
    "created_at": "2025-11-20T10:00:00Z"
  }
}
```

---

### 8.4 管理员：获取套餐详情
```
GET /packages/admin/packages/{package_id}
Authorization: Bearer {admin_access_token}
```

**响应**:
```json
{
  "code": 200,
  "data": {
    "id": 1,
    "name": "免费版",
    "description": "适合个人用户",
    "max_accounts": 10,
    "max_share_pages": 5,
    "max_nodes": 1,
    "price": 0.00,
    "is_active": true,
    "created_at": "2025-11-20T10:00:00Z",
    "updated_at": "2025-11-20T10:00:00Z"
  }
}
```

---

### 8.5 管理员：更新套餐
```
PUT /packages/admin/packages/{package_id}
Authorization: Bearer {admin_access_token}
```

**请求参数**（所有字段都是可选的）:
```json
{
  "name": "专业版（升级）",
  "price": 199.00,
  "max_accounts": 150,
  "is_active": true
}
```

**响应**:
```json
{
  "code": 200,
  "message": "更新成功",
  "data": {
    "id": 1,
    "name": "专业版（升级）",
    "price": 199.00,
    "max_accounts": 150,
    "updated_at": "2025-11-20T11:00:00Z"
  }
}
```

---

### 8.6 管理员：删除套餐
```
DELETE /packages/admin/packages/{package_id}
Authorization: Bearer {admin_access_token}
```

**响应**:
```json
{
  "code": 204,
  "message": "删除成功"
}
```

**注意事项**:
- 删除套餐是永久性的，无法恢复
- 如果有卡密或用户权限关联此套餐，建议禁用而不是删除
- 建议先将 `is_active` 设为 false，观察一段时间后再删除

---

## 9. 系统配置模块（管理员）

### 9.1 获取系统配置
```
GET /admin/settings?category=general
Authorization: Bearer {admin_access_token}
```

**响应**:
```json
{
  "code": 200,
  "data": {
    "items": [
      {
        "key": "site_name",
        "value": "Apple ID Auto",
        "value_type": "string",
        "description": "网站名称"
      },
      {
        "key": "allow_registration",
        "value": "true",
        "value_type": "boolean",
        "description": "是否允许注册"
      }
    ]
  }
}
```

---

### 9.2 更新系统配置
```
PUT /admin/settings/{key}
Authorization: Bearer {admin_access_token}
```

**请求参数**:
```json
{
  "value": "新值"
}
```

**响应**:
```json
{
  "code": 200,
  "message": "更新成功"
}
```

---

## 10. 统计分析模块

### 10.1 用户统计概览
```
GET /stats/overview
Authorization: Bearer {access_token}
```

**说明**: 获取当前用户的统计数据。

**响应**:
```json
{
  "code": 200,
  "data": {
    "user_info": {
      "user_id": 1,
      "username": "user1",
      "email": "user1@example.com",
      "is_active": true
    },
    "accounts": {
      "total": 50,
      "locked": 5,
      "normal": 45,
      "max_accounts": 100
    },
    "tasks": {
      "total": 120,
      "pending": 3,
      "in_progress": 2,
      "completed": 100,
      "failed": 15,
      "success_rate": 86.96
    },
    "share_pages": {
      "total": 10,
      "enabled": 8,
      "disabled": 2,
      "total_views": 1234,
      "max_share_pages": 20
    },
    "permission": {
      "expires_at": "2025-12-31T00:00:00Z",
      "days_remaining": 365,
      "is_expired": false,
      "unlock_count_today": 15,
      "max_unlock_per_day": 500
    },
    "nodes": {
      "total": 3,
      "online": 2,
      "offline": 1,
      "max_nodes": 5
    }
  }
}
```

**统计维度说明**:
- **user_info**: 用户基本信息
- **accounts**: 账号统计（总数、已锁定、正常、配额）
- **tasks**: 任务统计（各状态分布、成功率）
- **share_pages**: 分享页统计（总数、启用数、访问次数）
- **permission**: 权限信息（有效期、剩余天数、今日解锁次数）
- **nodes**: 节点统计（总数、在线、离线）

---

### 10.2 管理员统计概览
```
GET /stats/admin/overview
Authorization: Bearer {admin_access_token}
```

**说明**: 获取系统整体运营数据（仅管理员）。

**响应**:
```json
{
  "code": 200,
  "data": {
    "users": {
      "total": 1234,
      "active": 1100,
      "inactive": 134,
      "today_new": 15
    },
    "accounts": {
      "total": 12340,
      "locked": 234,
      "normal": 12106
    },
    "tasks": {
      "total": 56789,
      "pending": 120,
      "in_progress": 45,
      "completed": 50000,
      "failed": 6624,
      "success_rate": 88.33
    },
    "share_pages": {
      "total": 567,
      "enabled": 450,
      "disabled": 117,
      "total_views": 123456
    },
    "cards": {
      "total": 500,
      "activated": 300,
      "unused": 150,
      "revoked": 50
    },
    "nodes": {
      "total": 89,
      "online": 75,
      "offline": 14
    },
    "proxies": {
      "total": 234,
      "available": 200,
      "unavailable": 34
    }
  }
}
```

**统计维度说明**:
- **users**: 用户统计（总数、激活、禁用、今日新增）
- **accounts**: 账号统计（总数、各状态分布）
- **tasks**: 任务统计（总数、各状态分布、成功率）
- **share_pages**: 分享页统计（总数、启用、禁用、总访问次数）
- **cards**: 卡密统计（总数、已激活、未使用、已作废）
- **nodes**: 节点统计（总数、在线、离线）
- **proxies**: 代理统计（总数、可用、不可用）

---

## 11. Webhook 通知（可选）

### 11.1 配置 Webhook
```
POST /webhooks
Authorization: Bearer {access_token}
```

**请求参数**:
```json
{
  "url": "https://yourserver.com/webhook",
  "events": ["unlock.success", "unlock.failed", "account.locked"],
  "secret": "webhook_secret_123"
}
```

**Webhook 推送格式**:
```json
{
  "event": "unlock.success",
  "data": {
    "account_id": 1,
    "apple_id": "example@icloud.com",
    "task_id": "task_abc123",
    "timestamp": "2025-11-20T10:00:00Z"
  },
  "signature": "sha256=..."
}
```

---

## 12. 限流规则

| 端点类型 | 限制 |
|---------|------|
| 公开接口 | 60次/分钟/IP |
| 认证接口 | 100次/分钟/用户 |
| 卡密激活 | 3次/小时/IP |
| 管理接口 | 200次/分钟/管理员 |

---

## 13. 错误码说明

| 错误码 | 说明 |
|-------|------|
| 1001 | 用户名已存在 |
| 1002 | 邮箱已存在 |
| 1003 | 用户名或密码错误 |
| 1004 | 令牌已过期 |
| 1005 | 令牌无效 |
| 2001 | 卡密不存在 |
| 2002 | 卡密已使用 |
| 2003 | 卡密已过期 |
| 2004 | 卡密尝试次数过多 |
| 3001 | 账号数量超出限制 |
| 3002 | Apple ID 已存在 |
| 3003 | 账号不存在 |
| 4001 | 分享页数量超出限制 |
| 4002 | slug 已存在 |
| 4003 | 自定义 HTML 包含危险标签 |
| 5001 | 节点数量超出限制 |
| 5002 | 节点离线 |
| 9001 | 权限不足 |
| 9002 | 请求过于频繁 |

---

**文档版本**: v1.0
**更新日期**: 2025-11-20
**作者**: Claude
