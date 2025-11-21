/**
 * Apple ID 账号相关类型定义
 *
 * 职责：
 * - 定义 Apple ID 账号信息类型
 * - 提供账号管理相关的请求和响应类型
 * - 定义账号状态、安全问题等相关类型
 */

import type { PaginationParams, PaginationResponse, ImportResult } from './common'

/**
 * Apple ID 账号状态
 */
export type AccountStatus = 'normal' | 'locked' | 'checking' | 'failed' | 'disabled'

/**
 * Apple ID 账号信息
 */
export interface AppleAccount {
  id: number
  user_id: number
  apple_id: string
  password: string  // 加密后的密码
  status: AccountStatus
  lock_status: boolean  // 是否被锁定
  two_factor_enabled: boolean  // 是否启用了2FA
  // 账号详情
  app_store_country: string  // App Store 国家/地区
  app_store_language?: string  // App Store 语言
  account_name?: string  // 账号姓名
  birthday?: string  // 生日
  phone_number?: string  // 手机号（部分）
  // 设备信息
  devices_count: number  // 设备数量
  has_lost_mode: boolean  // 是否有丢失模式
  trusted_devices?: string[]  // 受信任设备列表
  // 分类和标签
  tags: string[]  // 标签（如：工作、美区、付费等）
  category?: string  // 分类
  note?: string  // 备注
  // 自动化设置
  auto_unlock: boolean  // 是否自动解锁
  auto_disable_2fa: boolean  // 是否自动关闭2FA
  check_interval: number  // 检测间隔（秒）
  priority: number  // 优先级（0-10）
  // 统计信息
  unlock_count: number  // 解锁次数
  check_count: number  // 检测次数
  last_checked_at: string | null  // 最后检测时间
  next_check_at: string | null  // 下次检测时间
  last_unlocked_at: string | null  // 最后解锁时间
  last_error?: string  // 最后错误信息
  // 时间戳
  created_at: string
  updated_at: string
}

/**
 * 安全问题
 */
export interface SecurityQuestion {
  question: string
  answer: string
}

/**
 * 账号列表查询参数
 */
export interface AccountListParams extends PaginationParams {
  status?: AccountStatus
  lock_status?: boolean
  two_factor_enabled?: boolean
  tag?: string
  category?: string
  search?: string  // 搜索 apple_id
  app_store_country?: string
  sort_by?: 'created_at' | 'updated_at' | 'last_checked_at' | 'unlock_count'
  sort_order?: 'asc' | 'desc'
}

/**
 * 账号列表响应
 */
export interface AccountListResponse extends PaginationResponse<AppleAccount> {
  stats?: {
    total: number
    normal: number
    locked: number
    checking: number
    failed: number
  }
}

/**
 * 创建账号请求
 */
export interface CreateAccountRequest {
  apple_id: string
  password: string
  security_questions?: SecurityQuestion[]
  tags?: string[]
  category?: string
  note?: string
  auto_unlock?: boolean
  auto_disable_2fa?: boolean
  check_interval?: number
  priority?: number
}

/**
 * 更新账号请求
 */
export interface UpdateAccountRequest {
  password?: string
  security_questions?: SecurityQuestion[]
  tags?: string[]
  category?: string
  note?: string
  auto_unlock?: boolean
  auto_disable_2fa?: boolean
  check_interval?: number
  priority?: number
  status?: AccountStatus
}

/**
 * 批量导入请求
 */
export interface BatchImportRequest {
  file?: File | Blob
  format: 'csv' | 'json'
  data?: string  // CSV 或 JSON 字符串
  auto_unlock?: boolean
  check_interval?: number
  tags?: string[]
}

/**
 * 批量导入响应
 */
export interface BatchImportResponse extends ImportResult {
  imported_ids?: number[]
}

/**
 * 密码历史记录
 */
export interface PasswordHistory {
  id: number
  account_id: number
  password: string
  changed_by: 'manual' | 'auto' | 'system'
  changed_by_user?: string
  note?: string
  created_at: string
}

/**
 * 账号检测结果
 */
export interface AccountCheckResult {
  account_id: number
  apple_id: string
  status: AccountStatus
  lock_status: boolean
  two_factor_enabled: boolean
  devices_count: number
  has_lost_mode: boolean
  app_store_country: string
  checked_at: string
  error?: string
}

/**
 * 账号详情（包含完整信息）
 */
export interface AccountDetail extends AppleAccount {
  security_questions?: SecurityQuestion[]
  password_history?: PasswordHistory[]
  recent_tasks?: any[]  // 最近的任务记录
  device_list?: Device[]  // 设备列表
}

/**
 * 设备信息
 */
export interface Device {
  id: string
  name: string
  model: string
  os_version: string
  is_trusted: boolean
  last_seen_at: string
}

/**
 * 账号标签统计
 */
export interface AccountTagStats {
  tag: string
  count: number
  normal_count: number
  locked_count: number
}

/**
 * 账号分类统计
 */
export interface AccountCategoryStats {
  category: string
  count: number
  unlock_count: number
}

/**
 * 账号国家/地区统计
 */
export interface AccountCountryStats {
  country: string
  country_name: string
  count: number
  locked_count: number
}

/**
 * 批量操作账号请求
 */
export interface BatchAccountOperation {
  account_ids: number[]
  action: 'unlock' | 'check' | 'disable_2fa' | 'delete' | 'update_tags'
  params?: {
    tags?: string[]
    auto_unlock?: boolean
    check_interval?: number
  }
}

/**
 * 批量操作响应
 */
export interface BatchAccountOperationResponse {
  success: number
  failed: number
  task_ids?: string[]  // 如果是解锁操作，返回任务ID
  errors?: Array<{
    account_id: number
    apple_id: string
    reason: string
  }>
}
