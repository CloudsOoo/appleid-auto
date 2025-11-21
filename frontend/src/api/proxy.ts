import { get, post, put, del } from '@/utils/request'

/**
 * 代理相关 API
 */

/**
 * 代理类型
 */
export interface Proxy {
  id: number
  user_id: number | null
  protocol: 'http' | 'https' | 'socks5'
  host: string
  port: number
  username: string | null
  password: string | null
  is_public: boolean
  is_active: boolean
  success_count: number
  fail_count: number
  avg_response_time: number
  last_checked_at: string | null
  created_at: string
}

/**
 * 代理列表参数
 */
export interface ProxyListParams {
  page?: number
  size?: number
  is_active?: boolean
}

/**
 * 代理列表响应
 */
export interface ProxyListResponse {
  items: Proxy[]
  total: number
  page: number
  size: number
}

/**
 * 创建代理请求
 */
export interface CreateProxyRequest {
  protocol: 'http' | 'https' | 'socks5'
  host: string
  port: number
  username?: string
  password?: string
  is_public?: boolean
}

/**
 * 更新代理请求
 */
export interface UpdateProxyRequest {
  host?: string
  port?: number
  username?: string
  password?: string
  is_active?: boolean
}

/**
 * 代理测试结果
 */
export interface ProxyTestResult {
  success: boolean
  response_time: number
  error_message?: string
}

/**
 * 获取代理列表
 */
export function getProxyListApi(params?: ProxyListParams) {
  return get<ProxyListResponse>('/proxies', params)
}

/**
 * 获取代理详情
 */
export function getProxyDetailApi(id: number) {
  return get<Proxy>(`/proxies/${id}`)
}

/**
 * 创建代理
 */
export function createProxyApi(data: CreateProxyRequest) {
  return post<Proxy>('/proxies', data)
}

/**
 * 更新代理
 */
export function updateProxyApi(id: number, data: UpdateProxyRequest) {
  return put<Proxy>(`/proxies/${id}`, data)
}

/**
 * 删除代理
 */
export function deleteProxyApi(id: number) {
  return del(`/proxies/${id}`)
}

/**
 * 测试代理
 */
export function testProxyApi(id: number) {
  return post<ProxyTestResult>(`/proxies/${id}/test`)
}
