import { get, post, put, del, upload, download } from '@/utils/request'

/**
 * Apple ID 相关 API
 */

/**
 * Apple ID 账号类型
 */
export interface AppleAccount {
  id: number
  user_id: number
  apple_id: string
  password: string
  status: 'active' | 'locked' | 'checking' | 'failed'
  locked_at: string | null
  unlocked_at: string | null
  last_checked_at: string | null
  next_check_at: string | null
  unlock_count: number
  created_at: string
  updated_at: string
}

/**
 * 账号列表查询参数
 */
export interface AccountListParams {
  page?: number
  size?: number
  status?: string
  keyword?: string
}

/**
 * 账号列表响应
 */
export interface AccountListResponse {
  items: AppleAccount[]
  total: number
  page: number
  size: number
}

/**
 * 创建账号请求
 */
export interface CreateAccountRequest {
  apple_id: string
  password: string
}

/**
 * 更新账号请求
 */
export interface UpdateAccountRequest {
  password?: string
  status?: string
}

/**
 * 批量导入请求
 */
export interface BatchImportRequest {
  accounts: Array<{
    apple_id: string
    password: string
  }>
}

/**
 * 密码历史类型
 */
export interface PasswordHistory {
  id: number
  account_id: number
  old_password: string
  new_password: string
  changed_at: string
}

/**
 * 获取账号列表
 */
export function getAccountListApi(params?: AccountListParams) {
  return get<AccountListResponse>('/accounts', params)
}

/**
 * 获取账号详情
 */
export function getAccountDetailApi(id: number) {
  return get<AppleAccount>(`/accounts/${id}`)
}

/**
 * 创建账号
 */
export function createAccountApi(data: CreateAccountRequest) {
  return post<AppleAccount>('/accounts', data)
}

/**
 * 更新账号
 */
export function updateAccountApi(id: number, data: UpdateAccountRequest) {
  return put<AppleAccount>(`/accounts/${id}`, data)
}

/**
 * 删除账号
 */
export function deleteAccountApi(id: number) {
  return del(`/accounts/${id}`)
}

/**
 * 批量导入账号
 */
export function batchImportAccountsApi(data: BatchImportRequest) {
  return post('/accounts/import', data)
}

/**
 * 批量导出账号
 */
export function batchExportAccountsApi(params?: any) {
  return download('/accounts/export', 'accounts.csv', params)
}

/**
 * 获取密码历史
 */
export function getPasswordHistoryApi(id: number) {
  return get<PasswordHistory[]>(`/accounts/${id}/password-history`)
}

/**
 * 手动触发检测
 */
export function triggerCheckApi(id: number) {
  return post(`/accounts/${id}/check`)
}
