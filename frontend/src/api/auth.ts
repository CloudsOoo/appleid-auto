import { post, get } from '@/utils/request'
import type { UserInfo } from '@/stores/user'

/**
 * 认证相关 API
 */

/**
 * 注册请求参数
 */
export interface RegisterRequest {
  username: string
  email: string
  password: string
}

/**
 * 登录请求参数
 */
export interface LoginRequest {
  username: string
  password: string
}

/**
 * 登录响应
 */
export interface LoginResponse {
  access_token: string
  refresh_token: string
  token_type: string
  expires_in: number
  user: UserInfo
}

/**
 * Token 刷新响应
 */
export interface RefreshTokenResponse {
  access_token: string
  token_type: string
  expires_in: number
}

/**
 * 修改密码请求
 */
export interface ChangePasswordRequest {
  old_password: string
  new_password: string
}

/**
 * 2FA 启用响应
 */
export interface Enable2FAResponse {
  secret: string
  qr_code: string
}

/**
 * 2FA 验证请求
 */
export interface Verify2FARequest {
  code: string
}

/**
 * 用户注册
 */
export function registerApi(data: RegisterRequest) {
  return post<UserInfo>('/auth/register', data)
}

/**
 * 用户登录
 */
export function loginApi(data: LoginRequest) {
  return post<LoginResponse>('/auth/login', data)
}

/**
 * 刷新 Token
 */
export function refreshTokenApi() {
  return post<RefreshTokenResponse>('/auth/refresh')
}

/**
 * 登出
 */
export function logoutApi() {
  return post('/auth/logout')
}

/**
 * 获取当前用户信息
 */
export function getCurrentUserApi() {
  return get<UserInfo>('/auth/me')
}

/**
 * 修改密码
 */
export function changePasswordApi(data: ChangePasswordRequest) {
  return post('/auth/change-password', data)
}

/**
 * 启用 2FA
 */
export function enable2FAApi() {
  return post<Enable2FAResponse>('/auth/2fa/enable')
}

/**
 * 验证 2FA
 */
export function verify2FAApi(data: Verify2FARequest) {
  return post('/auth/2fa/verify', data)
}

/**
 * 禁用 2FA
 */
export function disable2FAApi(data: Verify2FARequest) {
  return post('/auth/2fa/disable', data)
}
