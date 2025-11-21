import { get, post, put, del } from '@/utils/request'

/**
 * 套餐管理相关 API
 */

/**
 * 套餐类型
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
 * 套餐列表参数（管理员）
 */
export interface PackageListParams {
  page?: number
  per_page?: number
  include_inactive?: boolean
}

/**
 * 套餐列表响应（管理员）
 */
export interface PackageListResponse {
  items: Package[]
  total: number
  page: number
  per_page: number
  total_pages: number
}

/**
 * 创建套餐请求
 */
export interface CreatePackageRequest {
  name: string
  description: string
  max_accounts: number
  max_share_pages: number
  max_nodes: number
  max_proxies?: number
  max_concurrent_tasks?: number
  min_unlock_interval: number
  allow_custom_html: boolean
  allow_view_password_history: boolean
  allow_batch_import: boolean
  allow_api_access: boolean
  max_unlock_per_day: number
  max_import_per_time: number
  price: number
  currency?: string
  sort_order?: number
}

/**
 * 更新套餐请求
 */
export interface UpdatePackageRequest {
  name?: string
  description?: string
  max_accounts?: number
  max_share_pages?: number
  max_nodes?: number
  max_proxies?: number
  max_concurrent_tasks?: number
  min_unlock_interval?: number
  allow_custom_html?: boolean
  allow_view_password_history?: boolean
  allow_batch_import?: boolean
  allow_api_access?: boolean
  max_unlock_per_day?: number
  max_import_per_time?: number
  price?: number
  currency?: string
  is_active?: boolean
  sort_order?: number
}

/**
 * 获取套餐列表（公开接口）
 * 无需登录，所有用户可访问。仅返回激活的套餐。
 */
export function getPackageListApi() {
  return get<Package[]>('/packages')
}

/**
 * 管理员：获取套餐列表（含禁用）
 */
export function getAdminPackageListApi(params?: PackageListParams) {
  return get<PackageListResponse>('/admin/packages', params)
}

/**
 * 管理员：获取套餐详情
 */
export function getPackageDetailApi(id: number) {
  return get<Package>(`/admin/packages/${id}`)
}

/**
 * 管理员：创建套餐
 */
export function createPackageApi(data: CreatePackageRequest) {
  return post<Package>('/admin/packages', data)
}

/**
 * 管理员：更新套餐
 */
export function updatePackageApi(id: number, data: UpdatePackageRequest) {
  return put<Package>(`/admin/packages/${id}`, data)
}

/**
 * 管理员：删除套餐
 * 注意：删除套餐是永久性的，无法恢复
 * 如果有卡密或用户权限关联此套餐，建议禁用而不是删除
 */
export function deletePackageApi(id: number) {
  return del(`/admin/packages/${id}`)
}

/**
 * 管理员：启用套餐
 */
export function enablePackageApi(id: number) {
  return put(`/admin/packages/${id}`, { is_active: true })
}

/**
 * 管理员：禁用套餐
 */
export function disablePackageApi(id: number) {
  return put(`/admin/packages/${id}`, { is_active: false })
}
