"""
Celery 任务模块

本模块包含所有 Celery 异步任务的实现，包括：

1. 账号相关任务（account_tasks）：
   - check_account: 检测单个账号状态
   - batch_check_accounts: 批量检测账号（定时任务）
   - unlock_account: 解锁账号
   - disable_2fa: 关闭两步验证
   - change_password: 修改密码

2. 维护任务（maintenance_tasks）：
   - check_proxy_health: 代理池健康检查（每5分钟）
   - check_node_health: 节点健康检查（每1分钟）
   - check_permission_expiry: 权限过期检查（每10分钟）

3. 定时任务（scheduled_tasks）：
   - reset_daily_counts: 重置每日计数（每天00:00）
   - generate_daily_stats: 生成每日统计（每天01:00）

任务架构：
    API 端点 → TaskService → Celery 队列 → Worker 执行 → 数据库更新

任务队列优先级：
    - high_priority: 紧急任务（解锁、关闭2FA、手动检测）
    - default: 普通任务（批量检测、修改密码）
    - low_priority: 维护任务（代理检查、节点检查、统计）

使用方式：
    # 同步调用（不推荐，会阻塞）
    from app.tasks import check_account
    result = check_account(account_id=1)

    # 异步调用（推荐）
    from app.tasks import check_account
    task = check_account.apply_async(args=[1], queue="default")

    # 延迟调用（5分钟后执行）
    task = check_account.apply_async(args=[1], countdown=300)

    # 定时调用（指定时间执行）
    from datetime import datetime, timedelta
    eta = datetime.utcnow() + timedelta(hours=1)
    task = check_account.apply_async(args=[1], eta=eta)

启动 Worker：
    # 启动 Worker（gevent 协程池，100并发）
    celery -A app.celery_app worker --loglevel=info --pool=gevent --concurrency=100

    # 启动 Beat（定时任务调度器）
    celery -A app.celery_app beat --loglevel=info

    # 同时启动 Worker 和 Beat
    celery -A app.celery_app worker --beat --loglevel=info --pool=gevent --concurrency=100

    # 启动 Flower 监控
    celery -A app.celery_app flower --port=5555

监控和管理：
    # 查看任务状态
    from app.celery_app import celery_app
    result = celery_app.AsyncResult(task_id)
    print(result.status)  # PENDING, STARTED, SUCCESS, FAILURE, RETRY

    # 撤销任务
    celery_app.control.revoke(task_id, terminate=True)

    # 查看活跃任务
    i = celery_app.control.inspect()
    print(i.active())

    # 查看队列中的任务
    print(i.scheduled())
"""

# 导入所有任务
from app.tasks.account_tasks import (
    check_account,
    batch_check_accounts,
    unlock_account,
    disable_2fa,
    change_password,
)

from app.tasks.maintenance_tasks import (
    check_proxy_health,
    check_node_health,
    check_permission_expiry,
)

from app.tasks.scheduled_tasks import (
    reset_daily_counts,
    generate_daily_stats,
)


# 导出所有任务
__all__ = [
    # 账号任务
    "check_account",
    "batch_check_accounts",
    "unlock_account",
    "disable_2fa",
    "change_password",

    # 维护任务
    "check_proxy_health",
    "check_node_health",
    "check_permission_expiry",

    # 定时任务
    "reset_daily_counts",
    "generate_daily_stats",
]
