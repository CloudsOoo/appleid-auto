/**
 * 任务相关类型定义
 *
 * 职责：
 * - 定义解锁任务、检测任务等相关类型
 * - 提供任务管理相关的请求和响应类型
 * - 定义任务状态、结果等相关类型
 */

import type { PaginationParams, PaginationResponse } from './common'

/**
 * 任务类型
 */
export type TaskType = 'unlock' | 'check' | 'disable_2fa' | 'change_password'

/**
 * 任务状态
 */
export type TaskStatus = 'pending' | 'in_progress' | 'success' | 'failed' | 'cancelled'

/**
 * 解锁任务
 */
export interface UnlockTask {
  id: number
  task_id: string  // 唯一任务ID
  user_id: number
  account_id: number
  apple_id: string
  task_type: TaskType
  status: TaskStatus
  priority: number  // 优先级 (0-10)
  retry_count: number  // 重试次数
  max_retries: number  // 最大重试次数
  // 执行信息
  node_id: number | null  // 执行节点ID
  node_name?: string  // 执行节点名称
  proxy_id: number | null  // 使用的代理ID
  proxy_host?: string  // 代理地址
  // 任务结果
  result: TaskResult | null
  error_message?: string
  error_code?: string
  // 时间信息
  created_at: string
  started_at: string | null
  completed_at: string | null
  estimated_duration?: number  // 预计耗时（秒）
  actual_duration?: number  // 实际耗时（秒）
}

/**
 * 任务结果
 */
export interface TaskResult {
  success: boolean
  message: string
  steps?: TaskStep[]  // 执行步骤
  data?: {
    // 解锁任务结果
    unlocked?: boolean
    lock_removed_at?: string
    // 检测任务结果
    status?: string
    lock_status?: boolean
    two_factor_enabled?: boolean
    devices_count?: number
    // 2FA任务结果
    two_factor_disabled?: boolean
    // 通用数据
    [key: string]: any
  }
  logs?: string[]  // 详细日志
  screenshots?: string[]  // 截图URL
}

/**
 * 任务执行步骤
 */
export interface TaskStep {
  step: number
  name: string
  status: 'pending' | 'running' | 'success' | 'failed' | 'skipped'
  message?: string
  started_at?: string
  completed_at?: string
  duration?: number  // 耗时（毫秒）
}

/**
 * 任务列表查询参数
 */
export interface TaskListParams extends PaginationParams {
  task_type?: TaskType
  status?: TaskStatus
  account_id?: number
  node_id?: number
  search?: string  // 搜索 apple_id 或 task_id
  date_from?: string  // 开始日期
  date_to?: string  // 结束日期
  sort_by?: 'created_at' | 'started_at' | 'completed_at' | 'priority'
  sort_order?: 'asc' | 'desc'
}

/**
 * 任务列表响应
 */
export interface TaskListResponse extends PaginationResponse<UnlockTask> {
  stats?: TaskStats
}

/**
 * 任务统计
 */
export interface TaskStats {
  total: number
  pending: number
  in_progress: number
  success: number
  failed: number
  cancelled: number
  success_rate: number  // 成功率（百分比）
  avg_duration?: number  // 平均耗时（秒）
  total_duration?: number  // 总耗时（秒）
}

/**
 * 创建任务请求
 */
export interface CreateTaskRequest {
  account_ids: number[]
  task_type: TaskType
  priority?: number
  params?: {
    // 解锁任务参数
    use_proxy?: boolean
    proxy_id?: number
    // 修改密码任务参数
    new_password?: string
    // 通用参数
    [key: string]: any
  }
}

/**
 * 创建任务响应
 */
export interface CreateTaskResponse {
  task_ids: string[]
  created_count: number
  failed_count?: number
  errors?: Array<{
    account_id: number
    reason: string
  }>
}

/**
 * 任务详情
 */
export interface TaskDetail extends UnlockTask {
  account_details?: {
    apple_id: string
    status: string
    tags: string[]
  }
  node_details?: {
    node_name: string
    node_url: string
    country: string
  }
  proxy_details?: {
    proxy_type: string
    host: string
    port: number
    country: string
  }
  history?: TaskHistory[]  // 历史记录（重试记录）
}

/**
 * 任务历史记录
 */
export interface TaskHistory {
  attempt: number  // 第几次尝试
  status: TaskStatus
  result: TaskResult | null
  error_message?: string
  started_at: string
  completed_at: string
  duration: number
}

/**
 * 任务队列信息
 */
export interface TaskQueue {
  total: number
  pending: number
  in_progress: number
  avg_wait_time: number  // 平均等待时间（秒）
  estimated_completion_time?: string  // 预计完成时间
}

/**
 * 任务性能指标
 */
export interface TaskPerformance {
  date: string
  total_tasks: number
  success_tasks: number
  failed_tasks: number
  success_rate: number
  avg_duration: number
  max_duration: number
  min_duration: number
}

/**
 * 节点任务统计
 */
export interface NodeTaskStats {
  node_id: number
  node_name: string
  total_tasks: number
  success_tasks: number
  failed_tasks: number
  success_rate: number
  avg_duration: number
  current_queue_size: number
}

/**
 * 任务日志
 */
export interface TaskLog {
  id: number
  task_id: string
  level: 'debug' | 'info' | 'warn' | 'error'
  message: string
  details?: any
  created_at: string
}

/**
 * 批量取消任务请求
 */
export interface BatchCancelTaskRequest {
  task_ids: string[]
  reason?: string
}

/**
 * 批量重试任务请求
 */
export interface BatchRetryTaskRequest {
  task_ids: string[]
  reset_retry_count?: boolean
}
