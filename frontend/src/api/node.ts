import { get, post, del } from '@/utils/request'

/**
 * 节点相关 API
 */

/**
 * 节点类型
 */
export interface Node {
  id: number
  user_id: number
  name: string
  key: string
  ip_address: string
  status: 'online' | 'offline' | 'busy'
  cpu_usage: number
  memory_usage: number
  task_queue_length: number
  last_heartbeat_at: string
  created_at: string
}

/**
 * 节点列表参数
 */
export interface NodeListParams {
  page?: number
  size?: number
  status?: string
}

/**
 * 节点列表响应
 */
export interface NodeListResponse {
  items: Node[]
  total: number
  page: number
  size: number
}

/**
 * 注册节点请求
 */
export interface RegisterNodeRequest {
  name: string
}

/**
 * 节点心跳请求
 */
export interface NodeHeartbeatRequest {
  cpu_usage: number
  memory_usage: number
  task_queue_length: number
}

/**
 * 获取节点列表
 */
export function getNodeListApi(params?: NodeListParams) {
  return get<NodeListResponse>('/nodes', params)
}

/**
 * 获取节点详情
 */
export function getNodeDetailApi(id: number) {
  return get<Node>(`/nodes/${id}`)
}

/**
 * 注册节点
 */
export function registerNodeApi(data: RegisterNodeRequest) {
  return post<Node>('/nodes/register', data)
}

/**
 * 节点心跳
 */
export function nodeHeartbeatApi(data: NodeHeartbeatRequest) {
  return post('/nodes/heartbeat', data)
}

/**
 * 删除节点
 */
export function deleteNodeApi(id: number) {
  return del(`/nodes/${id}`)
}
