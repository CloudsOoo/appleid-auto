import { get, post, put, del } from '@/utils/request'

/**
 * 分享页相关 API
 */

/**
 * 分享页类型
 */
export interface SharePage {
  id: number
  user_id: number
  title: string
  slug: string
  content: string
  password: string | null
  is_active: boolean
  view_count: number
  created_at: string
  updated_at: string
}

/**
 * 分享页列表参数
 */
export interface SharePageListParams {
  page?: number
  size?: number
  is_active?: boolean
}

/**
 * 分享页列表响应
 */
export interface SharePageListResponse {
  items: SharePage[]
  total: number
  page: number
  size: number
}

/**
 * 创建分享页请求
 */
export interface CreateSharePageRequest {
  title: string
  slug: string
  content: string
  password?: string
  is_active?: boolean
}

/**
 * 更新分享页请求
 */
export interface UpdateSharePageRequest {
  title?: string
  content?: string
  password?: string
  is_active?: boolean
}

/**
 * 分享页日志
 */
export interface SharePageLog {
  id: number
  share_page_id: number
  ip_address: string
  user_agent: string
  accessed_at: string
}

/**
 * 分享页统计
 */
export interface SharePageStats {
  total_views: number
  unique_views: number
  today_views: number
  week_views: number
}

/**
 * 获取分享页列表
 */
export function getSharePageListApi(params?: SharePageListParams) {
  return get<SharePageListResponse>('/share-pages', params)
}

/**
 * 获取分享页详情
 */
export function getSharePageDetailApi(id: number) {
  return get<SharePage>(`/share-pages/${id}`)
}

/**
 * 创建分享页
 */
export function createSharePageApi(data: CreateSharePageRequest) {
  return post<SharePage>('/share-pages', data)
}

/**
 * 更新分享页
 */
export function updateSharePageApi(id: number, data: UpdateSharePageRequest) {
  return put<SharePage>(`/share-pages/${id}`, data)
}

/**
 * 删除分享页
 */
export function deleteSharePageApi(id: number) {
  return del(`/share-pages/${id}`)
}

/**
 * 获取访问日志
 */
export function getSharePageLogsApi(id: number, params?: any) {
  return get<SharePageLog[]>(`/share-pages/${id}/logs`, params)
}

/**
 * 获取分享页统计
 */
export function getSharePageStatsApi(id: number) {
  return get<SharePageStats>(`/share-pages/${id}/stats`)
}

/**
 * 访问分享页（公开）
 */
export function accessSharePageApi(slug: string, password?: string) {
  return get<SharePage>(`/public/share/${slug}`, { password })
}
