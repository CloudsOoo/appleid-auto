import { get, post } from '@/utils/request'

/**
 * 卡密相关 API
 */

/**
 * 卡密类型
 */
export interface Card {
  id: number
  code: string
  package_id: number | null
  status: 'unused' | 'used' | 'expired' | 'revoked'
  duration_days: number
  used_by: number | null
  used_at: string | null
  expires_at: string | null
  created_at: string
}

/**
 * 卡密列表参数
 */
export interface CardListParams {
  page?: number
  size?: number
  status?: string
}

/**
 * 卡密列表响应
 */
export interface CardListResponse {
  items: Card[]
  total: number
  page: number
  size: number
}

/**
 * 生成卡密请求
 */
export interface GenerateCardsRequest {
  count: number
  package_id?: number
  duration_days: number
}

/**
 * 激活卡密请求
 */
export interface ActivateCardRequest {
  code: string
}

/**
 * 激活卡密（用户）
 */
export function activateCardApi(data: ActivateCardRequest) {
  return post('/cards/activate', data)
}

/**
 * 查询卡密状态
 */
export function getCardStatusApi(code: string) {
  return get<Card>(`/cards/status?code=${code}`)
}

/**
 * 生成卡密（管理员）
 */
export function generateCardsApi(data: GenerateCardsRequest) {
  return post<Card[]>('/cards/admin/generate', data)
}

/**
 * 获取卡密列表（管理员）
 */
export function getCardListApi(params?: CardListParams) {
  return get<CardListResponse>('/cards/admin/list', params)
}

/**
 * 导出卡密（管理员）
 */
export function exportCardsApi(params?: any) {
  return get('/cards/admin/export', params)
}

/**
 * 作废卡密（管理员）
 */
export function revokeCardApi(id: number) {
  return post(`/cards/admin/${id}/revoke`)
}

/**
 * 延期卡密（管理员）
 */
export function extendCardApi(id: number, days: number) {
  return post(`/cards/admin/${id}/extend`, { days })
}
