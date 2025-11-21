/**
 * 用户相关类型定义
 *
 * 职责：
 * - 定义用户信息、权限、认证等相关类型
 * - 提供用户管理相关的请求和响应类型
 */

import type { RoleType, PaginationParams, PaginationResponse } from './common'

/**
 * 用户信息
 */
export interface User {
  id: number
  username: string
  email: string
  role: RoleType
  is_active: boolean
  is_verified: boolean
  two_factor_enabled: boolean
  avatar?: string
  phone?: string
  created_at: string
  updated_at: string
  last_login_at?: string
}

/**
 * 用户权限配置
 */
export interface UserPermission {
  id: number
  user_id: number
  package_id: number | null
  package_name?: string
  // 配额限制
  max_accounts: number
  max_share_pages: number
  max_nodes: number
  max_proxies: number
  max_concurrent_tasks: number
  max_unlock_per_day: number
  max_import_per_time: number
  // 时间限制
  check_interval: number  // 检测间隔（秒）
  min_unlock_interval: number  // 最小解锁间隔（秒）
  // 功能权限
  allow_custom_html: boolean
  allow_api_access: boolean
  allow_export: boolean
  allow_batch_import: boolean
  allow_view_password_history: boolean
  // 有效期
  expires_at: string | null
  is_active: boolean
  created_at: string
  updated_at: string
}

/**
 * 用户统计信息
 */
export interface UserStats {
  total_accounts: number
  active_accounts: number
  locked_accounts: number
  total_tasks: number
  success_tasks: number
  failed_tasks: number
  success_rate: number
  total_share_pages: number
  active_share_pages: number
  total_views: number
  unlock_count_today: number
  remaining_quota: {
    accounts: number
    share_pages: number
    unlocks_today: number
  }
}

/**
 * 登录凭证
 */
export interface LoginCredentials {
  username: string
  password: string
  remember?: boolean
  captcha?: string
}

/**
 * 登录响应
 */
export interface LoginResponse {
  access_token: string
  refresh_token: string
  token_type: string
  expires_in: number
  user: User
  permission?: UserPermission
}

/**
 * 注册请求
 */
export interface RegisterRequest {
  username: string
  email: string
  password: string
  password_confirm?: string
  invitation_code?: string
  captcha?: string
}

/**
 * 刷新令牌响应
 */
export interface RefreshTokenResponse {
  access_token: string
  token_type: string
  expires_in: number
}

/**
 * 修改密码请求
 */
export interface ChangePasswordRequest {
  old_password: string
  new_password: string
  new_password_confirm?: string
}

/**
 * 2FA 启用响应
 */
export interface Enable2FAResponse {
  secret: string
  qr_code: string
  backup_codes: string[]
}

/**
 * 2FA 验证请求
 */
export interface Verify2FARequest {
  code: string
  backup_code?: string
}

/**
 * 用户列表查询参数
 */
export interface UserListParams extends PaginationParams {
  role?: RoleType
  is_active?: boolean
  search?: string
  sort_by?: 'created_at' | 'updated_at' | 'last_login_at'
  sort_order?: 'asc' | 'desc'
}

/**
 * 用户列表响应
 */
export interface UserListResponse extends PaginationResponse<User> {}

/**
 * 更新用户请求
 */
export interface UpdateUserRequest {
  username?: string
  email?: string
  role?: RoleType
  is_active?: boolean
  is_verified?: boolean
  avatar?: string
  phone?: string
}

/**
 * 更新用户权限请求
 */
export interface UpdateUserPermissionRequest {
  package_id?: number | null
  max_accounts?: number
  max_share_pages?: number
  max_nodes?: number
  max_proxies?: number
  max_concurrent_tasks?: number
  max_unlock_per_day?: number
  max_import_per_time?: number
  check_interval?: number
  min_unlock_interval?: number
  allow_custom_html?: boolean
  allow_api_access?: boolean
  allow_export?: boolean
  allow_batch_import?: boolean
  allow_view_password_history?: boolean
  expires_at?: string | null
  is_active?: boolean
}

/**
 * 用户配置
 */
export interface UserSettings {
  theme: 'light' | 'dark' | 'auto'
  language: 'zh-CN' | 'en-US'
  notifications: {
    email: boolean
    webhook: boolean
    unlock_success: boolean
    unlock_failed: boolean
    account_locked: boolean
  }
  display: {
    items_per_page: number
    show_sidebar: boolean
    compact_mode: boolean
  }
}

/**
 * 用户活动记录
 */
export interface UserActivity {
  id: number
  user_id: number
  action: string
  module: string
  description: string
  ip_address: string
  user_agent: string
  created_at: string
}

/**
 * 在线用户信息
 */
export interface OnlineUser {
  user_id: number
  username: string
  avatar?: string
  last_active_at: string
  ip_address: string
}
