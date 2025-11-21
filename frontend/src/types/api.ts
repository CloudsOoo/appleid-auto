/**
 * API 响应类型定义
 *
 * 职责：
 * - 定义 API 请求和响应的通用类型
 * - 提供统计分析相关的类型
 * - 定义代理、节点、系统配置等其他模块的类型
 */

import type { PaginationParams, PaginationResponse, TimeRangeParams } from './common'

/**
 * ==================== 代理池模块 ====================
 */

/**
 * 代理类型
 */
export type ProxyType = 'http' | 'https' | 'socks5'

/**
 * 代理状态
 */
export type ProxyStatus = 'active' | 'inactive' | 'testing' | 'failed'

/**
 * 代理信息
 */
export interface Proxy {
  id: number
  user_id: number
  proxy_type: ProxyType
  host: string
  port: number
  username?: string
  password?: string
  country?: string
  country_code?: string
  city?: string
  status: ProxyStatus
  priority: number  // 优先级
  // 统计信息
  success_count: number
  failure_count: number
  total_count: number
  success_rate: number
  avg_response_time: number  // 平均响应时间（毫秒）
  last_success_at: string | null
  last_failure_at: string | null
  last_checked_at: string | null
  // 时间戳
  created_at: string
  updated_at: string
}

/**
 * 代理列表查询参数
 */
export interface ProxyListParams extends PaginationParams {
  proxy_type?: ProxyType
  status?: ProxyStatus
  country?: string
  search?: string  // 搜索 host
  sort_by?: 'created_at' | 'success_rate' | 'avg_response_time'
  sort_order?: 'asc' | 'desc'
}

/**
 * 代理列表响应
 */
export interface ProxyListResponse extends PaginationResponse<Proxy> {}

/**
 * 创建代理请求
 */
export interface CreateProxyRequest {
  proxy_type: ProxyType
  host: string
  port: number
  username?: string
  password?: string
  country?: string
  priority?: number
}

/**
 * 更新代理请求
 */
export interface UpdateProxyRequest {
  proxy_type?: ProxyType
  host?: string
  port?: number
  username?: string
  password?: string
  country?: string
  priority?: number
  status?: ProxyStatus
}

/**
 * 测试代理响应
 */
export interface TestProxyResponse {
  success: boolean
  response_time: number
  ip_address?: string
  country?: string
  country_code?: string
  city?: string
  error?: string
}

/**
 * ==================== 节点管理模块 ====================
 */

/**
 * 节点状态
 */
export type NodeStatus = 'online' | 'offline' | 'busy' | 'maintenance'

/**
 * 节点信息
 */
export interface Node {
  id: number
  user_id: number
  node_name: string
  node_url: string
  node_key: string  // 节点密钥（用于认证）
  status: NodeStatus
  country?: string
  country_code?: string
  region?: string
  // 系统信息
  cpu_usage: number
  memory_usage: number
  disk_usage?: number
  network_speed?: number
  // 任务信息
  task_queue_size: number
  max_concurrent_tasks: number
  current_running_tasks: number
  total_tasks: number
  success_tasks: number
  failed_tasks: number
  success_rate: number
  avg_task_duration: number
  // 心跳信息
  last_heartbeat_at: string | null
  heartbeat_interval: number  // 心跳间隔（秒）
  // 时间戳
  created_at: string
  updated_at: string
}

/**
 * 节点列表查询参数
 */
export interface NodeListParams extends PaginationParams {
  status?: NodeStatus
  country?: string
  search?: string  // 搜索节点名称
  sort_by?: 'created_at' | 'success_rate' | 'task_queue_size'
  sort_order?: 'asc' | 'desc'
}

/**
 * 节点列表响应
 */
export interface NodeListResponse extends PaginationResponse<Node> {}

/**
 * 注册节点请求
 */
export interface RegisterNodeRequest {
  node_name: string
  node_url: string
  country?: string
  region?: string
  max_concurrent_tasks?: number
}

/**
 * 注册节点响应
 */
export interface RegisterNodeResponse {
  id: number
  node_name: string
  node_key: string  // 节点密钥
  status: NodeStatus
  created_at: string
}

/**
 * 节点心跳请求
 */
export interface NodeHeartbeatRequest {
  cpu_usage: number
  memory_usage: number
  disk_usage?: number
  network_speed?: number
  task_queue_size: number
  current_running_tasks: number
}

/**
 * 节点详情
 */
export interface NodeDetail extends Node {
  recent_tasks?: any[]  // 最近执行的任务
  performance_stats?: NodePerformanceStats[]  // 性能统计
  error_logs?: NodeErrorLog[]  // 错误日志
}

/**
 * 节点性能统计
 */
export interface NodePerformanceStats {
  timestamp: string
  cpu_usage: number
  memory_usage: number
  disk_usage: number
  task_queue_size: number
  response_time: number
}

/**
 * 节点错误日志
 */
export interface NodeErrorLog {
  id: number
  node_id: number
  error_type: string
  error_message: string
  stack_trace?: string
  created_at: string
}

/**
 * ==================== 统计分析模块 ====================
 */

/**
 * 用户统计概览
 */
export interface UserStatsOverview {
  user_info: {
    user_id: number
    username: string
    email: string
    is_active: boolean
    role: string
  }
  accounts: {
    total: number
    locked: number
    normal: number
    checking: number
    failed: number
    max_accounts: number
    usage_rate: number
  }
  tasks: {
    total: number
    pending: number
    in_progress: number
    completed: number
    failed: number
    cancelled: number
    success_rate: number
    avg_duration: number
  }
  share_pages: {
    total: number
    enabled: number
    disabled: number
    expired: number
    total_views: number
    unique_views: number
    max_share_pages: number
    usage_rate: number
  }
  permission: {
    package_name: string | null
    expires_at: string | null
    days_remaining: number | null
    is_expired: boolean
    unlock_count_today: number
    max_unlock_per_day: number
    quota_remaining: number
  }
  nodes: {
    total: number
    online: number
    offline: number
    busy: number
    max_nodes: number
    usage_rate: number
  }
  proxies: {
    total: number
    active: number
    inactive: number
    failed: number
  }
}

/**
 * 管理员统计概览
 */
export interface AdminStatsOverview {
  users: {
    total: number
    active: number
    inactive: number
    verified: number
    today_new: number
    this_week_new: number
    this_month_new: number
  }
  accounts: {
    total: number
    locked: number
    normal: number
    checking: number
    failed: number
    today_new: number
  }
  tasks: {
    total: number
    pending: number
    in_progress: number
    completed: number
    failed: number
    cancelled: number
    success_rate: number
    avg_duration: number
    today_total: number
    today_success: number
  }
  share_pages: {
    total: number
    enabled: number
    disabled: number
    expired: number
    password_protected: number
    total_views: number
    unique_views: number
    today_views: number
  }
  cards: {
    total: number
    activated: number
    unused: number
    expired: number
    revoked: number
    today_activated: number
    this_week_activated: number
  }
  nodes: {
    total: number
    online: number
    offline: number
    busy: number
    maintenance: number
    avg_cpu_usage: number
    avg_memory_usage: number
    total_queue_size: number
  }
  proxies: {
    total: number
    available: number
    unavailable: number
    testing: number
    avg_success_rate: number
  }
  system: {
    total_storage_used: number
    total_bandwidth_used: number
    avg_response_time: number
    uptime_percentage: number
  }
}

/**
 * 趋势统计数据
 */
export interface TrendStats {
  date: string
  value: number
  change?: number
  change_percentage?: number
}

/**
 * 账号趋势统计
 */
export interface AccountTrendStats extends TrendStats {
  total: number
  locked: number
  normal: number
  new_added: number
}

/**
 * 任务趋势统计
 */
export interface TaskTrendStats extends TrendStats {
  total: number
  success: number
  failed: number
  success_rate: number
  avg_duration: number
}

/**
 * ==================== 系统配置模块 ====================
 */

/**
 * 系统配置项
 */
export interface SystemSetting {
  key: string
  value: string
  value_type: 'string' | 'number' | 'boolean' | 'json'
  category: 'general' | 'security' | 'email' | 'storage' | 'api' | 'advanced'
  description: string
  is_public: boolean
  is_readonly: boolean
  created_at: string
  updated_at: string
}

/**
 * 系统配置列表查询参数
 */
export interface SettingListParams {
  category?: string
  include_readonly?: boolean
}

/**
 * 更新系统配置请求
 */
export interface UpdateSettingRequest {
  value: string
}

/**
 * ==================== Webhook 模块 ====================
 */

/**
 * Webhook 事件类型
 */
export type WebhookEvent =
  | 'unlock.success'
  | 'unlock.failed'
  | 'account.locked'
  | 'account.unlocked'
  | 'card.activated'
  | 'user.registered'

/**
 * Webhook 配置
 */
export interface Webhook {
  id: number
  user_id: number
  url: string
  events: WebhookEvent[]
  secret: string
  is_active: boolean
  last_triggered_at: string | null
  total_triggers: number
  success_triggers: number
  failed_triggers: number
  created_at: string
  updated_at: string
}

/**
 * 创建 Webhook 请求
 */
export interface CreateWebhookRequest {
  url: string
  events: WebhookEvent[]
  secret: string
}

/**
 * Webhook 日志
 */
export interface WebhookLog {
  id: number
  webhook_id: number
  event: WebhookEvent
  payload: any
  response_status: number
  response_body?: string
  error?: string
  triggered_at: string
}
