/**
 * 通用类型定义
 *
 * 职责：
 * - 定义项目中所有通用的基础类型
 * - 提供分页、响应、错误等公共类型
 * - 避免在各个模块中重复定义相同类型
 */

/**
 * 分页请求参数
 */
export interface PaginationParams {
  page?: number
  per_page?: number
}

/**
 * 分页响应数据
 */
export interface PaginationResponse<T> {
  items: T[]
  total: number
  page: number
  per_page: number
  total_pages: number
}

/**
 * API 统一响应格式
 */
export interface ApiResponse<T = any> {
  code: number
  message: string
  data: T
  errors?: Record<string, string[]>
}

/**
 * API 错误响应
 */
export interface ApiError {
  code: number
  message: string
  errors?: Record<string, string[]>
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
 * 排序参数
 */
export interface SortParams {
  sort_by?: string
  sort_order?: 'asc' | 'desc'
}

/**
 * 搜索参数
 */
export interface SearchParams {
  search?: string
  search_field?: string
}

/**
 * 状态枚举
 */
export enum Status {
  ACTIVE = 'active',
  INACTIVE = 'inactive',
  PENDING = 'pending',
  COMPLETED = 'completed',
  FAILED = 'failed',
  CANCELLED = 'cancelled'
}

/**
 * 通用状态类型
 */
export type CommonStatus = 'active' | 'inactive' | 'pending' | 'completed' | 'failed' | 'cancelled'

/**
 * 用户角色
 */
export enum UserRole {
  USER = 'user',
  ADMIN = 'admin'
}

/**
 * 用户角色类型
 */
export type RoleType = 'user' | 'admin'

/**
 * 主题类型
 */
export type Theme = 'light' | 'dark' | 'auto'

/**
 * 语言类型
 */
export type Language = 'zh-CN' | 'en-US'

/**
 * 文件上传响应
 */
export interface UploadResponse {
  url: string
  filename: string
  size: number
  mime_type: string
}

/**
 * 批量操作请求
 */
export interface BatchOperationRequest {
  ids: number[]
  action: string
  params?: Record<string, any>
}

/**
 * 批量操作响应
 */
export interface BatchOperationResponse {
  success: number
  failed: number
  errors?: Array<{
    id: number
    reason: string
  }>
}

/**
 * 导入结果
 */
export interface ImportResult {
  total: number
  success: number
  failed: number
  errors?: Array<{
    line: number
    data?: any
    reason: string
  }>
}

/**
 * 导出参数
 */
export interface ExportParams {
  format?: 'csv' | 'json' | 'xlsx'
  fields?: string[]
  filters?: Record<string, any>
}

/**
 * 统计数据通用格式
 */
export interface StatsData {
  label: string
  value: number
  percentage?: number
  trend?: 'up' | 'down' | 'stable'
  change?: number
}

/**
 * 时间序列数据
 */
export interface TimeSeriesData {
  date: string
  value: number
  [key: string]: any
}

/**
 * 选项类型（用于下拉框等）
 */
export interface Option<T = any> {
  label: string
  value: T
  disabled?: boolean
  children?: Option<T>[]
}

/**
 * 表单规则类型
 */
export interface FormRule {
  required?: boolean
  message?: string
  type?: 'string' | 'number' | 'boolean' | 'email' | 'url' | 'array' | 'object'
  min?: number
  max?: number
  pattern?: RegExp
  validator?: (rule: any, value: any, callback: any) => void
  trigger?: 'blur' | 'change'
}

/**
 * 表格列配置
 */
export interface TableColumn {
  prop: string
  label: string
  width?: string | number
  minWidth?: string | number
  align?: 'left' | 'center' | 'right'
  sortable?: boolean
  fixed?: 'left' | 'right'
  formatter?: (row: any, column: any, cellValue: any, index: number) => any
  slot?: string
}

/**
 * 菜单项类型
 */
export interface MenuItem {
  id: string
  title: string
  icon?: string
  path?: string
  children?: MenuItem[]
  meta?: {
    requiresAuth?: boolean
    roles?: RoleType[]
    permission?: string
    hidden?: boolean
    badge?: string | number
  }
}

/**
 * 面包屑项
 */
export interface BreadcrumbItem {
  title: string
  path?: string
}

/**
 * 通知消息类型
 */
export interface Notification {
  id: string
  type: 'info' | 'success' | 'warning' | 'error'
  title: string
  message: string
  duration?: number
  timestamp: string
  read?: boolean
}

/**
 * 日志级别
 */
export enum LogLevel {
  DEBUG = 'debug',
  INFO = 'info',
  WARN = 'warn',
  ERROR = 'error'
}

/**
 * 操作日志
 */
export interface OperationLog {
  id: number
  user_id: number
  username: string
  action: string
  module: string
  description: string
  ip_address: string
  user_agent: string
  created_at: string
}

/**
 * 键值对类型
 */
export type KeyValuePair<T = any> = Record<string, T>

/**
 * ID 类型（支持字符串和数字）
 */
export type ID = string | number

/**
 * 时间戳类型
 */
export type Timestamp = string | number | Date

/**
 * 回调函数类型
 */
export type Callback<T = void> = (data?: T) => void

/**
 * 异步回调函数类型
 */
export type AsyncCallback<T = void> = (data?: T) => Promise<void>
