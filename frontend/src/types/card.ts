/**
 * 卡密相关类型定义
 *
 * 职责：
 * - 定义卡密信息、激活记录等相关类型
 * - 提供卡密管理相关的请求和响应类型
 * - 定义卡密类型、状态等相关枚举
 */

import type { PaginationParams, PaginationResponse } from './common'

/**
 * 卡密类型
 */
export type CardType = 'time' | 'permanent' | 'trial'

/**
 * 卡密状态
 */
export type CardStatus = 'unused' | 'activated' | 'expired' | 'revoked'

/**
 * 卡密信息
 */
export interface LicenseCard {
  id: number
  card_code: string  // 卡密码（格式：XXXX-XXXX-XXXX-XXXX）
  card_type: CardType
  status: CardStatus
  // 套餐信息
  package_id: number
  package_name: string
  // 时长卡密信息
  duration_days: number | null  // 有效天数（时长卡密）
  // 批次信息
  batch_id: string | null  // 批次ID
  batch_note?: string  // 批次备注
  // 激活信息
  activated_by_user_id: number | null  // 激活用户ID
  activated_by_username?: string  // 激活用户名
  activated_at: string | null  // 激活时间
  activated_ip?: string  // 激活IP
  // 有效期
  expires_at: string | null  // 过期时间（激活后计算）
  // 作废信息
  revoked_at: string | null  // 作废时间
  revoked_by?: string  // 作废操作人
  revoke_reason?: string  // 作废原因
  // 其他
  note?: string  // 备注
  created_at: string
  updated_at: string
}

/**
 * 卡密列表查询参数
 */
export interface CardListParams extends PaginationParams {
  card_type?: CardType
  status?: CardStatus
  package_id?: number
  batch_id?: string
  search?: string  // 搜索卡密码
  date_from?: string  // 创建日期范围
  date_to?: string
  sort_by?: 'created_at' | 'activated_at' | 'expires_at'
  sort_order?: 'asc' | 'desc'
}

/**
 * 卡密列表响应
 */
export interface CardListResponse extends PaginationResponse<LicenseCard> {
  stats?: CardStats
}

/**
 * 卡密统计
 */
export interface CardStats {
  total: number
  unused: number
  activated: number
  expired: number
  revoked: number
  // 按类型统计
  time_cards: number
  permanent_cards: number
  trial_cards: number
  // 近期统计
  activated_today: number
  activated_this_week: number
  activated_this_month: number
}

/**
 * 激活卡密请求
 */
export interface ActivateCardRequest {
  card_code: string
}

/**
 * 激活卡密响应
 */
export interface ActivateCardResponse {
  success: boolean
  message: string
  data: {
    card_type: CardType
    duration_days: number | null
    package: {
      id: number
      name: string
      max_accounts: number
      max_share_pages: number
      max_nodes: number
      [key: string]: any
    }
    expires_at: string | null
    activated_at: string
  }
}

/**
 * 卡密状态查询响应
 */
export interface CardStatusResponse {
  is_activated: boolean
  card_type?: CardType
  package_name?: string
  activated_at?: string
  expires_at?: string | null
  days_remaining?: number | null
  is_expired: boolean
}

/**
 * 生成卡密请求
 */
export interface GenerateCardRequest {
  card_type: CardType
  package_id: number
  duration_days?: number | null  // 时长卡密必填
  quantity: number  // 生成数量
  batch_id?: string  // 批次ID（可选，系统自动生成）
  note?: string  // 批次备注
}

/**
 * 生成卡密响应
 */
export interface GenerateCardResponse {
  success: boolean
  message: string
  data: {
    batch_id: string
    quantity: number
    cards: string[]  // 卡密码列表
    created_count: number
  }
}

/**
 * 延期卡密请求
 */
export interface ExtendCardRequest {
  card_id: number
  extend_days: number  // 延长天数
  reason?: string  // 延期原因
}

/**
 * 作废卡密请求
 */
export interface RevokeCardRequest {
  card_id: number
  reason: string  // 作废原因
}

/**
 * 卡密详情
 */
export interface CardDetail extends LicenseCard {
  package_details?: {
    id: number
    name: string
    description: string
    max_accounts: number
    max_share_pages: number
    max_nodes: number
    price: number
    currency: string
    [key: string]: any
  }
  activation_history?: CardActivationHistory[]
  usage_stats?: CardUsageStats
}

/**
 * 卡密激活历史（如果允许多次激活）
 */
export interface CardActivationHistory {
  id: number
  user_id: number
  username: string
  activated_at: string
  activated_ip: string
  expires_at: string | null
  is_current: boolean
}

/**
 * 卡密使用统计
 */
export interface CardUsageStats {
  total_accounts: number
  total_tasks: number
  total_share_pages: number
  first_used_at: string
  last_used_at: string
}

/**
 * 批次信息
 */
export interface CardBatch {
  batch_id: string
  card_type: CardType
  package_id: number
  package_name: string
  duration_days: number | null
  total_quantity: number
  unused_count: number
  activated_count: number
  expired_count: number
  revoked_count: number
  note?: string
  created_by: string
  created_at: string
}

/**
 * 批次列表查询参数
 */
export interface BatchListParams extends PaginationParams {
  card_type?: CardType
  package_id?: number
  search?: string  // 搜索批次ID或备注
  date_from?: string
  date_to?: string
}

/**
 * 批次列表响应
 */
export interface BatchListResponse extends PaginationResponse<CardBatch> {}

/**
 * 卡密导出参数
 */
export interface CardExportParams {
  batch_id?: string
  status?: CardStatus
  format?: 'csv' | 'xlsx' | 'json'
  include_activated?: boolean
}

/**
 * 卡密导入请求（管理员批量导入现有卡密）
 */
export interface CardImportRequest {
  file?: File | Blob
  format: 'csv' | 'json'
  data?: string
  card_type: CardType
  package_id: number
  duration_days?: number
  batch_id?: string
  note?: string
}

/**
 * 套餐信息（用于卡密生成时选择）
 */
export interface Package {
  id: number
  name: string
  description: string
  max_accounts: number
  max_share_pages: number
  max_nodes: number
  max_proxies: number
  max_concurrent_tasks: number
  min_unlock_interval: number
  allow_custom_html: boolean
  allow_view_password_history: boolean
  allow_batch_import: boolean
  allow_api_access: boolean
  max_unlock_per_day: number
  max_import_per_time: number
  price: number
  currency: string
  is_active: boolean
  sort_order: number
  created_at: string
  updated_at?: string
}

/**
 * 套餐列表查询参数
 */
export interface PackageListParams extends PaginationParams {
  include_inactive?: boolean
  min_price?: number
  max_price?: number
}

/**
 * 套餐列表响应
 */
export interface PackageListResponse extends PaginationResponse<Package> {}
