/**
 * Token 管理工具
 *
 * 功能：
 * - Token 存储和获取
 * - Token 有效性检查
 * - Token 清除
 */

/**
 * 获取 Token 存储 key
 */
function getTokenKey(): string {
  return import.meta.env.VITE_TOKEN_KEY || 'appleid_access_token'
}

/**
 * 获取 Refresh Token 存储 key
 */
function getRefreshTokenKey(): string {
  return import.meta.env.VITE_REFRESH_TOKEN_KEY || 'appleid_refresh_token'
}

/**
 * 获取 Access Token
 */
export function getToken(): string | null {
  return localStorage.getItem(getTokenKey())
}

/**
 * 设置 Access Token
 */
export function setToken(token: string): void {
  localStorage.setItem(getTokenKey(), token)
}

/**
 * 获取 Refresh Token
 */
export function getRefreshToken(): string | null {
  return localStorage.getItem(getRefreshTokenKey())
}

/**
 * 设置 Refresh Token
 */
export function setRefreshToken(token: string): void {
  localStorage.setItem(getRefreshTokenKey(), token)
}

/**
 * 移除 Access Token
 */
export function removeToken(): void {
  localStorage.removeItem(getTokenKey())
}

/**
 * 移除 Refresh Token
 */
export function removeRefreshToken(): void {
  localStorage.removeItem(getRefreshTokenKey())
}

/**
 * 清除所有 Token
 */
export function clearTokens(): void {
  removeToken()
  removeRefreshToken()
}

/**
 * 检查是否有 Token
 */
export function hasToken(): boolean {
  return !!getToken()
}

/**
 * 解析 JWT Token（不验证签名）
 * 用于获取 Token 中的信息（如过期时间）
 */
export function parseJWT(token: string): any {
  try {
    const base64Url = token.split('.')[1]
    const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/')
    const jsonPayload = decodeURIComponent(
      atob(base64)
        .split('')
        .map(c => '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2))
        .join('')
    )
    return JSON.parse(jsonPayload)
  } catch (error) {
    console.error('解析 JWT 失败:', error)
    return null
  }
}

/**
 * 检查 Token 是否过期
 * @param token JWT Token
 * @param buffer 提前刷新的时间缓冲（秒），默认 60 秒
 */
export function isTokenExpired(token: string, buffer: number = 60): boolean {
  const payload = parseJWT(token)
  if (!payload || !payload.exp) {
    return true
  }

  const now = Math.floor(Date.now() / 1000)
  return payload.exp - now < buffer
}

/**
 * 获取 Token 剩余有效时间（秒）
 */
export function getTokenRemainingTime(token: string): number {
  const payload = parseJWT(token)
  if (!payload || !payload.exp) {
    return 0
  }

  const now = Math.floor(Date.now() / 1000)
  return Math.max(0, payload.exp - now)
}
