/**
 * 分享页相关类型定义
 *
 * 职责：
 * - 定义分享页信息、访问日志等相关类型
 * - 提供分享页管理相关的请求和响应类型
 * - 定义分享页模板、显示模式等相关枚举
 */

import type { PaginationParams, PaginationResponse } from './common'

/**
 * 分享页显示模式
 */
export type DisplayMode = 'random' | 'sequence' | 'weighted'

/**
 * 分享页模板
 */
export type ShareTemplate = 'default' | 'minimal' | 'card' | 'table' | 'custom'

/**
 * 分享页信息
 */
export interface SharePage {
  id: number
  user_id: number
  username?: string
  // 基础信息
  title: string
  slug: string  // URL 路径（唯一）
  description?: string
  share_url: string  // 完整分享链接
  // 访问控制
  has_password: boolean
  password?: string  // 仅创建/更新时使用
  access_limit: number | null  // 访问限制次数（null 为不限制）
  access_count: number  // 当前访问次数
  expires_at: string | null  // 过期时间（null 为永不过期）
  allowed_domains: string[]  // 允许访问的域名（空数组为不限制）
  allowed_ips?: string[]  // 允许访问的IP（可选）
  // 显示设置
  display_mode: DisplayMode
  template: ShareTemplate
  show_password: boolean  // 是否显示密码
  show_devices_count: boolean  // 是否显示设备数量
  show_copy_button: boolean  // 是否显示复制按钮
  // 关联账号
  account_ids: number[]  // 关联的 Apple ID 列表
  accounts_count?: number  // 账号数量
  // 自定义样式
  custom_html_header?: string  // 自定义 HTML 头部
  custom_html_body?: string  // 自定义 HTML 正文
  custom_html_footer?: string  // 自定义 HTML 底部
  custom_css?: string  // 自定义 CSS
  custom_js?: string  // 自定义 JavaScript
  // 统计信息
  is_active: boolean
  total_views: number  // 总访问次数（页面加载）
  unique_views: number  // 唯一访问次数（IP去重）
  total_copies: number  // 总复制次数
  last_accessed_at: string | null  // 最后访问时间
  // 时间戳
  created_at: string
  updated_at: string
}

/**
 * 分享页列表查询参数
 */
export interface SharePageListParams extends PaginationParams {
  is_active?: boolean
  has_password?: boolean
  template?: ShareTemplate
  search?: string  // 搜索标题或 slug
  date_from?: string
  date_to?: string
  sort_by?: 'created_at' | 'updated_at' | 'total_views' | 'access_count'
  sort_order?: 'asc' | 'desc'
}

/**
 * 分享页列表响应
 */
export interface SharePageListResponse extends PaginationResponse<SharePage> {
  stats?: SharePageStats
}

/**
 * 分享页统计
 */
export interface SharePageStats {
  total: number
  active: number
  inactive: number
  expired: number
  password_protected: number
  total_views: number
  total_unique_views: number
  avg_views_per_page: number
}

/**
 * 创建分享页请求
 */
export interface CreateSharePageRequest {
  title: string
  slug: string
  description?: string
  password?: string
  access_limit?: number | null
  expires_at?: string | null
  allowed_domains?: string[]
  allowed_ips?: string[]
  display_mode?: DisplayMode
  template?: ShareTemplate
  show_password?: boolean
  show_devices_count?: boolean
  show_copy_button?: boolean
  account_ids: number[]
  custom_html_header?: string
  custom_html_body?: string
  custom_html_footer?: string
  custom_css?: string
  custom_js?: string
}

/**
 * 更新分享页请求
 */
export interface UpdateSharePageRequest {
  title?: string
  slug?: string
  description?: string
  password?: string | null  // null 表示移除密码
  access_limit?: number | null
  expires_at?: string | null
  allowed_domains?: string[]
  allowed_ips?: string[]
  display_mode?: DisplayMode
  template?: ShareTemplate
  show_password?: boolean
  show_devices_count?: boolean
  show_copy_button?: boolean
  account_ids?: number[]
  custom_html_header?: string
  custom_html_body?: string
  custom_html_footer?: string
  custom_css?: string
  custom_js?: string
  is_active?: boolean
}

/**
 * 分享页详情
 */
export interface SharePageDetail extends SharePage {
  accounts?: SharePageAccount[]  // 关联的账号列表
  recent_logs?: ShareAccessLog[]  // 最近访问日志
  stats_by_date?: SharePageDailyStats[]  // 按日期统计
  top_countries?: CountryStats[]  // 访问来源国家统计
}

/**
 * 分享页关联的账号信息（简化版）
 */
export interface SharePageAccount {
  id: number
  apple_id: string
  password?: string
  status: string
  devices_count: number
  tags: string[]
  weight?: number  // 权重（用于 weighted 显示模式）
}

/**
 * 分享页访问日志
 */
export interface ShareAccessLog {
  id: number
  share_page_id: number
  // 访问信息
  ip_address: string
  country?: string
  country_code?: string
  city?: string
  user_agent: string
  referer?: string
  // 展示信息
  shown_account_id: number | null  // 展示的账号ID
  shown_apple_id?: string  // 展示的 Apple ID
  access_granted: boolean  // 是否成功访问（通过密码验证等）
  password_attempts?: number  // 密码尝试次数
  // 操作信息
  copied: boolean  // 是否复制了账号
  copied_at?: string  // 复制时间
  // 时间戳
  created_at: string
}

/**
 * 访问日志查询参数
 */
export interface AccessLogListParams extends PaginationParams {
  share_page_id: number
  access_granted?: boolean
  copied?: boolean
  country?: string
  date_from?: string
  date_to?: string
  sort_by?: 'created_at'
  sort_order?: 'asc' | 'desc'
}

/**
 * 访问日志列表响应
 */
export interface AccessLogListResponse extends PaginationResponse<ShareAccessLog> {}

/**
 * 分享页每日统计
 */
export interface SharePageDailyStats {
  date: string
  total_views: number
  unique_views: number
  access_granted: number
  access_denied: number
  total_copies: number
}

/**
 * 国家统计
 */
export interface CountryStats {
  country: string
  country_code: string
  country_name: string
  count: number
  percentage: number
}

/**
 * 公开访问分享页请求
 */
export interface PublicShareAccessRequest {
  slug: string
  password?: string
}

/**
 * 公开访问分享页响应
 */
export interface PublicShareAccessResponse {
  success: boolean
  message?: string
  data?: {
    title: string
    description?: string
    account: {
      apple_id: string
      password: string
      devices_count?: number
      tags?: string[]
      note?: string
    }
    custom_html?: {
      header?: string
      body?: string
      footer?: string
    }
    custom_css?: string
    template: ShareTemplate
    show_copy_button: boolean
    access_token?: string  // 用于记录复制等操作
  }
}

/**
 * 记录复制操作请求
 */
export interface RecordCopyRequest {
  slug: string
  access_token: string
}

/**
 * 分享页模板配置
 */
export interface TemplateConfig {
  name: string
  template: ShareTemplate
  description: string
  preview_image?: string
  default_html_header?: string
  default_html_body?: string
  default_html_footer?: string
  default_css?: string
  supports_custom_html: boolean
  supports_custom_css: boolean
}

/**
 * 分享页权重配置（用于 weighted 显示模式）
 */
export interface AccountWeight {
  account_id: number
  weight: number  // 权重值（1-100）
}

/**
 * 批量更新分享页状态请求
 */
export interface BatchUpdateSharePageRequest {
  share_page_ids: number[]
  is_active?: boolean
  expires_at?: string | null
}

/**
 * 分享页克隆请求
 */
export interface CloneSharePageRequest {
  source_share_page_id: number
  new_title: string
  new_slug: string
  copy_accounts?: boolean
  copy_custom_html?: boolean
}
