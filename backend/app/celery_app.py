"""
Celery 应用配置模块

本模块配置 Celery 分布式任务队列，包括：
- Celery 应用初始化
- 任务自动发现
- Redis 连接配置
- 任务重试、超时、并发等配置
- 任务监控和日志

架构说明：
    API 端点 → TaskService → Celery 任务队列 → Worker 执行 → 数据库更新

使用方式：
    # 启动 Worker
    celery -A app.celery_app worker --loglevel=info --pool=gevent --concurrency=100

    # 启动 Beat（定时任务调度器）
    celery -A app.celery_app beat --loglevel=info

    # 同时启动 Worker 和 Beat
    celery -A app.celery_app worker --beat --loglevel=info

    # 监控
    celery -A app.celery_app flower --port=5555

依赖关系：
    - Redis: 作为消息代理和结果后端
    - PostgreSQL: 任务状态持久化存储
    - Gevent: 协程池，支持高并发 I/O 任务
"""

from celery import Celery
from celery.schedules import crontab
from kombu import Exchange, Queue

from app.core.config import settings


# ========================================
# Celery 应用初始化
# ========================================

def create_celery_app() -> Celery:
    """
    创建并配置 Celery 应用实例

    配置说明：
        - Broker: Redis 数据库 1 (消息队列)
        - Backend: Redis 数据库 2 (结果存储)
        - 序列化: JSON (安全且跨语言兼容)
        - 时区: UTC (统一使用 UTC 时间)
        - 任务发现: 自动扫描 app.tasks 模块

    Returns:
        Celery: 配置好的 Celery 应用实例
    """
    celery_app = Celery(
        "appleid_auto",
        broker=settings.CELERY_BROKER_URL,
        backend=settings.CELERY_RESULT_BACKEND,
        include=[
            "app.tasks.account_tasks",      # 账号相关任务（检测、解锁、修改）
            "app.tasks.maintenance_tasks",  # 维护任务（代理检查、节点检查、权限过期）
            "app.tasks.scheduled_tasks",    # 定时任务（每日统计、计数重置）
        ]
    )

    # 应用配置
    celery_app.config_from_object(CeleryConfig)

    return celery_app


# ========================================
# Celery 配置类
# ========================================

class CeleryConfig:
    """
    Celery 配置类

    配置项说明：
        1. 任务序列化：JSON（安全、跨语言）
        2. 结果序列化：JSON
        3. 时区：UTC（避免时区混淆）
        4. 任务追踪：启用（可查询任务状态）
        5. 任务忽略结果：禁用（需要结果反馈）
        6. 任务压缩：gzip（节省带宽）
        7. 结果过期时间：24小时（自动清理）
        8. 任务超时：10分钟（避免任务卡死）
        9. 任务重试：3次（提高成功率）
        10. 并发：Gevent 协程池（支持高并发）
    """

    # ========== 序列化配置 ==========
    task_serializer = "json"              # 任务序列化格式
    result_serializer = "json"            # 结果序列化格式
    accept_content = ["json"]             # 接受的内容类型

    # ========== 时区配置 ==========
    timezone = "UTC"                      # 统一使用 UTC 时区
    enable_utc = True                     # 启用 UTC

    # ========== 任务配置 ==========
    task_track_started = True             # 追踪任务开始状态
    task_ignore_result = False            # 不忽略任务结果
    task_compression = "gzip"             # 启用 gzip 压缩
    task_acks_late = True                 # 任务执行后再确认（保证任务不丢失）
    worker_prefetch_multiplier = 4        # 预取任务数（提高并发）

    # ========== 结果后端配置 ==========
    result_expires = 86400                # 结果过期时间：24小时
    result_persistent = True              # 结果持久化
    result_compression = "gzip"           # 结果压缩

    # ========== 超时配置 ==========
    task_soft_time_limit = 540            # 软超时：9分钟（发送 SoftTimeLimitExceeded 异常）
    task_time_limit = 600                 # 硬超时：10分钟（强制终止）

    # ========== 重试配置 ==========
    task_default_retry_delay = 60         # 默认重试延迟：60秒
    task_max_retries = 3                  # 默认最大重试次数：3次

    # ========== 任务路由配置 ==========
    task_routes = {
        # 高优先级任务队列（紧急解锁、手动触发检测）
        "app.tasks.account_tasks.unlock_account": {"queue": "high_priority"},
        "app.tasks.account_tasks.disable_2fa": {"queue": "high_priority"},
        "app.tasks.account_tasks.check_account": {"queue": "high_priority"},

        # 普通优先级任务队列（批量检测、修改密码）
        "app.tasks.account_tasks.batch_check_accounts": {"queue": "default"},
        "app.tasks.account_tasks.change_password": {"queue": "default"},

        # 低优先级任务队列（维护任务、定时任务）
        "app.tasks.maintenance_tasks.*": {"queue": "low_priority"},
        "app.tasks.scheduled_tasks.*": {"queue": "low_priority"},
    }

    # ========== 队列配置 ==========
    task_queues = (
        # 高优先级队列（紧急任务）
        Queue(
            "high_priority",
            Exchange("high_priority"),
            routing_key="high_priority",
            priority=10,
        ),
        # 默认队列（普通任务）
        Queue(
            "default",
            Exchange("default"),
            routing_key="default",
            priority=5,
        ),
        # 低优先级队列（维护任务）
        Queue(
            "low_priority",
            Exchange("low_priority"),
            routing_key="low_priority",
            priority=1,
        ),
    )

    # ========== Beat 定时任务配置 ==========
    beat_schedule = {
        # 每小时批量检测账号状态
        "batch-check-accounts-hourly": {
            "task": "app.tasks.account_tasks.batch_check_accounts",
            "schedule": crontab(minute=0),  # 每小时整点执行
            "options": {"queue": "default", "priority": 5},
        },

        # 每5分钟检查代理池健康状态
        "check-proxy-health-5min": {
            "task": "app.tasks.maintenance_tasks.check_proxy_health",
            "schedule": crontab(minute="*/5"),  # 每5分钟执行
            "options": {"queue": "low_priority", "priority": 1},
        },

        # 每1分钟检查节点健康状态
        "check-node-health-1min": {
            "task": "app.tasks.maintenance_tasks.check_node_health",
            "schedule": crontab(minute="*/1"),  # 每1分钟执行
            "options": {"queue": "low_priority", "priority": 1},
        },

        # 每10分钟检查权限过期
        "check-permission-expiry-10min": {
            "task": "app.tasks.maintenance_tasks.check_permission_expiry",
            "schedule": crontab(minute="*/10"),  # 每10分钟执行
            "options": {"queue": "low_priority", "priority": 1},
        },

        # 每天凌晨0点重置每日计数
        "reset-daily-counts": {
            "task": "app.tasks.scheduled_tasks.reset_daily_counts",
            "schedule": crontab(hour=0, minute=0),  # 每天00:00执行
            "options": {"queue": "low_priority", "priority": 1},
        },

        # 每天凌晨1点生成每日统计
        "generate-daily-stats": {
            "task": "app.tasks.scheduled_tasks.generate_daily_stats",
            "schedule": crontab(hour=1, minute=0),  # 每天01:00执行
            "options": {"queue": "low_priority", "priority": 1},
        },
    }

    # ========== Worker 配置 ==========
    worker_pool = "gevent"                # 使用 gevent 协程池（支持高并发 I/O）
    worker_concurrency = 100              # 并发数：100个协程
    worker_max_tasks_per_child = 1000    # 每个 Worker 执行1000个任务后重启（防止内存泄漏）
    worker_disable_rate_limits = False    # 启用限流

    # ========== 日志配置 ==========
    worker_log_format = "[%(asctime)s: %(levelname)s/%(processName)s] %(message)s"
    worker_task_log_format = "[%(asctime)s: %(levelname)s/%(processName)s] [%(task_name)s(%(task_id)s)] %(message)s"

    # ========== 事件配置 ==========
    worker_send_task_events = True        # 发送任务事件（用于监控）
    task_send_sent_event = True           # 发送任务已发送事件

    # ========== 监控配置 ==========
    worker_hijack_root_logger = False     # 不劫持 root logger
    worker_log_color = True               # 启用彩色日志

    # ========== 安全配置 ==========
    task_reject_on_worker_lost = True     # Worker 丢失时拒绝任务
    task_ack_on_failure_or_timeout = True # 失败或超时时确认任务（避免重复执行）


# ========================================
# 创建 Celery 应用实例
# ========================================

celery_app = create_celery_app()


# ========================================
# 任务装饰器辅助函数
# ========================================

def task(*args, **kwargs):
    """
    任务装饰器（封装 Celery 的 task 装饰器）

    使用方式：
        from app.celery_app import task

        @task(bind=True, max_retries=3)
        def my_task(self, arg1, arg2):
            try:
                # 任务逻辑
                pass
            except Exception as exc:
                # 重试
                raise self.retry(exc=exc, countdown=60)

    参数说明：
        bind: 是否绑定任务实例（可访问 self.retry 等方法）
        max_retries: 最大重试次数
        default_retry_delay: 重试延迟（秒）
        autoretry_for: 自动重试的异常类型
        retry_backoff: 指数退避（True/False）
        retry_backoff_max: 最大退避时间（秒）
        retry_jitter: 添加随机抖动（避免重试风暴）
    """
    return celery_app.task(*args, **kwargs)


# ========================================
# TODO 列表
# ========================================

"""
TODO (优先级 P0):
    - [ ] 实现账号检测任务（check_account, batch_check_accounts）
    - [ ] 实现账号解锁任务（unlock_account）
    - [ ] 实现关闭 2FA 任务（disable_2fa）
    - [ ] 实现修改密码任务（change_password）
    - [ ] 实现维护任务（check_proxy_health, check_node_health, check_permission_expiry）
    - [ ] 实现定时任务（reset_daily_counts, generate_daily_stats）

TODO (优先级 P1):
    - [ ] 添加任务监控（Prometheus + Grafana）
    - [ ] 添加任务告警（失败率超过阈值时告警）
    - [ ] 添加任务日志（详细的执行日志）
    - [ ] 优化任务调度（动态调整并发数、队列优先级）

TODO (优先级 P2):
    - [ ] 支持任务取消（撤销正在执行的任务）
    - [ ] 支持任务暂停/恢复（暂停定时任务）
    - [ ] 支持任务链（任务完成后自动执行下一个任务）
    - [ ] 支持任务分组（批量管理任务）
    - [ ] 添加 Flower 监控面板配置
"""


# ========================================
# 导出
# ========================================

__all__ = ["celery_app", "task"]
