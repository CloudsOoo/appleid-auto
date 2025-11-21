import { get } from '@/utils/request'

/**
 * 统计分析相关 API
 */

/**
 * 用户统计概览响应
 */
export interface UserStatsOverview {
  user_info: {
    user_id: number
    username: string
    email: string
    is_active: boolean
  }
  accounts: {
    total: number
    locked: number
    normal: number
    max_accounts: number
  }
  tasks: {
    total: number
    pending: number
    in_progress: number
    completed: number
    failed: number
    success_rate: number
  }
  share_pages: {
    total: number
    enabled: number
    disabled: number
    total_views: number
    max_share_pages: number
  }
  permission: {
    expires_at: string | null
    days_remaining: number
    is_expired: boolean
    unlock_count_today: number
    max_unlock_per_day: number
  }
  nodes: {
    total: number
    online: number
    offline: number
    max_nodes: number
  }
}

/**
 * 管理员统计概览响应
 */
export interface AdminStatsOverview {
  users: {
    total: number
    active: number
    inactive: number
    today_new: number
  }
  accounts: {
    total: number
    locked: number
    normal: number
  }
  tasks: {
    total: number
    pending: number
    in_progress: number
    completed: number
    failed: number
    success_rate: number
  }
  share_pages: {
    total: number
    enabled: number
    disabled: number
    total_views: number
  }
  cards: {
    total: number
    activated: number
    unused: number
    revoked: number
  }
  nodes: {
    total: number
    online: number
    offline: number
  }
  proxies: {
    total: number
    available: number
    unavailable: number
  }
}

/**
 * 账号统计数据（按时间范围）
 */
export interface AccountStats {
  date: string
  total: number
  locked: number
  normal: number
  new_added: number
}

/**
 * 任务统计数据（按时间范围）
 */
export interface TaskStats {
  date: string
  total: number
  success: number
  failed: number
  success_rate: number
}

/**
 * 时间范围参数
 */
export interface TimeRangeParams {
  start_date?: string  // YYYY-MM-DD
  end_date?: string    // YYYY-MM-DD
  period?: 'day' | 'week' | 'month' | 'year'
}

/**
 * 获取用户统计概览
 * 获取当前用户的统计数据
 */
export function getUserStatsOverviewApi() {
  return get<UserStatsOverview>('/stats/overview')
}

/**
 * 获取管理员统计概览
 * 获取系统整体运营数据（仅管理员）
 */
export function getAdminStatsOverviewApi() {
  return get<AdminStatsOverview>('/stats/admin/overview')
}

/**
 * 获取账号统计趋势（用户）
 * 按时间范围获取账号统计数据
 */
export function getAccountStatsApi(params?: TimeRangeParams) {
  return get<AccountStats[]>('/stats/accounts', params)
}

/**
 * 获取任务统计趋势（用户）
 * 按时间范围获取任务统计数据
 */
export function getTaskStatsApi(params?: TimeRangeParams) {
  return get<TaskStats[]>('/stats/tasks', params)
}

/**
 * 获取分享页访问统计（用户）
 */
export function getSharePageStatsApi(sharePageId?: number, params?: TimeRangeParams) {
  if (sharePageId) {
    return get<any>(`/stats/share-pages/${sharePageId}`, params)
  }
  return get<any>('/stats/share-pages', params)
}

/**
 * 管理员：获取账号统计趋势（全局）
 */
export function getAdminAccountStatsApi(params?: TimeRangeParams) {
  return get<AccountStats[]>('/stats/admin/accounts', params)
}

/**
 * 管理员：获取任务统计趋势（全局）
 */
export function getAdminTaskStatsApi(params?: TimeRangeParams) {
  return get<TaskStats[]>('/stats/admin/tasks', params)
}

/**
 * 管理员：获取用户增长统计
 */
export function getAdminUserGrowthStatsApi(params?: TimeRangeParams) {
  return get<any>('/stats/admin/users/growth', params)
}

/**
 * 管理员：获取卡密使用统计
 */
export function getAdminCardStatsApi(params?: TimeRangeParams) {
  return get<any>('/stats/admin/cards', params)
}

/**
 * 管理员：获取节点性能统计
 */
export function getAdminNodeStatsApi(nodeId?: number, params?: TimeRangeParams) {
  if (nodeId) {
    return get<any>(`/stats/admin/nodes/${nodeId}`, params)
  }
  return get<any>('/stats/admin/nodes', params)
}

/**
 * 管理员：获取代理统计
 */
export function getAdminProxyStatsApi(params?: TimeRangeParams) {
  return get<any>('/stats/admin/proxies', params)
}
