import { get, post } from '@/utils/request'

/**
 * 任务相关 API
 */

/**
 * 任务类型
 */
export interface UnlockTask {
  id: number
  user_id: number
  account_id: number
  task_type: 'unlock' | 'disable_2fa' | 'change_password'
  status: 'pending' | 'running' | 'success' | 'failed' | 'cancelled'
  priority: number
  node_id: number | null
  proxy_id: number | null
  started_at: string | null
  completed_at: string | null
  error_message: string | null
  retry_count: number
  created_at: string
  updated_at: string
}

/**
 * 任务列表参数
 */
export interface TaskListParams {
  page?: number
  size?: number
  status?: string
  task_type?: string
}

/**
 * 任务列表响应
 */
export interface TaskListResponse {
  items: UnlockTask[]
  total: number
  page: number
  size: number
}

/**
 * 创建任务请求
 */
export interface CreateTaskRequest {
  account_id: number
  task_type: 'unlock' | 'disable_2fa' | 'change_password'
  priority?: number
}

/**
 * 任务统计
 */
export interface TaskStats {
  total: number
  pending: number
  running: number
  success: number
  failed: number
  success_rate: number
  avg_duration: number
}

/**
 * 获取任务列表
 */
export function getTaskListApi(params?: TaskListParams) {
  return get<TaskListResponse>('/tasks', params)
}

/**
 * 获取任务详情
 */
export function getTaskDetailApi(id: number) {
  return get<UnlockTask>(`/tasks/${id}`)
}

/**
 * 创建解锁任务
 */
export function createUnlockTaskApi(data: CreateTaskRequest) {
  return post<UnlockTask>('/tasks/unlock', data)
}

/**
 * 取消任务
 */
export function cancelTaskApi(id: number) {
  return post(`/tasks/${id}/cancel`)
}

/**
 * 获取任务统计
 */
export function getTaskStatsApi() {
  return get<TaskStats>('/tasks/stats')
}
