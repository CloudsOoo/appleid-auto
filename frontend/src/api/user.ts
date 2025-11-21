import { get, post, put, del } from '@/utils/request'

/**
 * 用户管理相关 API
 */

/**
 * 用户信息类型（完整）
 */
export interface User {
  id: number
  username: string
  email: string
  role: 'user' | 'admin'
  is_active: boolean
  is_verified: boolean
  created_at: string
  updated_at: string
  two_factor_enabled?: boolean
}

/**
 * 用户权限类型
 */
export interface UserPermission {
  id: number
  user_id: number
  package_id: number | null
  max_accounts: number
  max_share_pages: number
  max_nodes: number
  max_proxies: number
  max_concurrent_tasks: number
  check_interval: number
  allow_custom_html: boolean
  allow_api_access: boolean
  allow_export: boolean
  allow_batch_import: boolean
  expires_at: string | null
  is_active: boolean
  created_at: string
  updated_at: string
}

/**
 * 用户列表参数（管理员）
 */
export interface UserListParams {
  page?: number
  per_page?: number
  role?: string
  is_active?: boolean
  search?: string
}

/**
 * 用户列表响应
 */
export interface UserListResponse {
  items: User[]
  total: number
  page: number
  per_page: number
  total_pages: number
}

/**
 * 更新用户请求
 */
export interface UpdateUserRequest {
  username?: string
  email?: string
  role?: 'user' | 'admin'
  is_active?: boolean
  is_verified?: boolean
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
  check_interval?: number
  allow_custom_html?: boolean
  allow_api_access?: boolean
  allow_export?: boolean
  allow_batch_import?: boolean
  expires_at?: string | null
  is_active?: boolean
}

/**
 * 获取当前用户信息
 * （与 /auth/me 类似，但可能包含更多详细信息）
 */
export function getCurrentUserApi() {
  return get<User>('/users/me')
}

/**
 * 更新当前用户信息
 */
export function updateCurrentUserApi(data: UpdateUserRequest) {
  return put<User>('/users/me', data)
}

/**
 * 获取当前用户权限
 */
export function getCurrentUserPermissionApi() {
  return get<UserPermission>('/users/me/permission')
}

/**
 * 管理员：获取用户列表
 */
export function getUserListApi(params?: UserListParams) {
  return get<UserListResponse>('/admin/users', params)
}

/**
 * 管理员：获取用户详情
 */
export function getUserDetailApi(id: number) {
  return get<User>(`/admin/users/${id}`)
}

/**
 * 管理员：更新用户信息
 */
export function updateUserApi(id: number, data: UpdateUserRequest) {
  return put<User>(`/admin/users/${id}`, data)
}

/**
 * 管理员：删除用户
 */
export function deleteUserApi(id: number) {
  return del(`/admin/users/${id}`)
}

/**
 * 管理员：获取用户权限
 */
export function getUserPermissionApi(userId: number) {
  return get<UserPermission>(`/admin/users/${userId}/permission`)
}

/**
 * 管理员：更新用户权限
 */
export function updateUserPermissionApi(userId: number, data: UpdateUserPermissionRequest) {
  return put<UserPermission>(`/admin/users/${userId}/permission`, data)
}

/**
 * 管理员：禁用用户
 */
export function disableUserApi(id: number) {
  return post(`/admin/users/${id}/disable`)
}

/**
 * 管理员：启用用户
 */
export function enableUserApi(id: number) {
  return post(`/admin/users/${id}/enable`)
}
