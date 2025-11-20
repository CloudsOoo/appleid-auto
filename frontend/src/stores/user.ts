import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { RouteLocationNormalizedLoaded } from 'vue-router'

/**
 * 用户信息类型定义
 */
export interface UserInfo {
  id: number
  username: string
  email: string
  role: 'user' | 'admin'
  is_active: boolean
  is_verified: boolean
  created_at: string
  two_factor_enabled?: boolean
}

/**
 * 用户权限类型定义
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
}

/**
 * 登录凭证类型
 */
export interface LoginCredentials {
  username: string
  password: string
}

/**
 * 登录响应类型
 */
export interface LoginResponse {
  access_token: string
  refresh_token: string
  token_type: string
  expires_in: number
  user: UserInfo
}

/**
 * 用户状态管理 Store
 *
 * 功能：
 * - 用户信息存储和管理
 * - Token 管理（access_token、refresh_token）
 * - 登录/登出状态管理
 * - 权限信息管理
 * - 持久化存储（localStorage）
 */
export const useUserStore = defineStore('user', () => {
  // ==================== 状态定义 ====================

  /**
   * 用户信息
   */
  const user = ref<UserInfo | null>(null)

  /**
   * Access Token
   */
  const token = ref<string>('')

  /**
   * Refresh Token
   */
  const refreshToken = ref<string>('')

  /**
   * 用户权限信息
   */
  const permission = ref<UserPermission | null>(null)

  // ==================== 计算属性 ====================

  /**
   * 是否已登录
   */
  const isLoggedIn = computed(() => {
    return !!token.value && !!user.value
  })

  /**
   * 是否为管理员
   */
  const isAdmin = computed(() => {
    return user.value?.role === 'admin'
  })

  /**
   * 是否已启用 2FA
   */
  const hasTwoFactor = computed(() => {
    return user.value?.two_factor_enabled === true
  })

  /**
   * 权限是否有效
   */
  const hasValidPermission = computed(() => {
    if (!permission.value) return false
    if (!permission.value.is_active) return false

    // 检查是否过期
    if (permission.value.expires_at) {
      const expiresAt = new Date(permission.value.expires_at)
      const now = new Date()
      return now < expiresAt
    }

    return true
  })

  // ==================== 方法 ====================

  /**
   * 设置 Token
   */
  function setToken(accessToken: string, refreshTokenValue?: string) {
    token.value = accessToken
    if (refreshTokenValue) {
      refreshToken.value = refreshTokenValue
    }

    // 持久化到 localStorage
    const tokenKey = import.meta.env.VITE_TOKEN_KEY || 'appleid_access_token'
    const refreshTokenKey = import.meta.env.VITE_REFRESH_TOKEN_KEY || 'appleid_refresh_token'

    localStorage.setItem(tokenKey, accessToken)
    if (refreshTokenValue) {
      localStorage.setItem(refreshTokenKey, refreshTokenValue)
    }
  }

  /**
   * 设置用户信息
   */
  function setUser(userInfo: UserInfo) {
    user.value = userInfo

    // 持久化到 localStorage
    localStorage.setItem('user_info', JSON.stringify(userInfo))
  }

  /**
   * 设置用户权限
   */
  function setPermission(permissionInfo: UserPermission) {
    permission.value = permissionInfo

    // 持久化到 localStorage
    localStorage.setItem('user_permission', JSON.stringify(permissionInfo))
  }

  /**
   * 登录
   * TODO: 实际项目中应该调用 API 接口，这里先使用 Mock 数据
   */
  async function login(credentials: LoginCredentials): Promise<boolean> {
    try {
      // TODO: 调用登录 API
      // import { loginApi } from '@/api/auth'
      // const response = await loginApi(credentials)

      // Mock 数据（临时实现）
      const mockResponse: LoginResponse = {
        access_token: 'mock-access-token-' + Date.now(),
        refresh_token: 'mock-refresh-token-' + Date.now(),
        token_type: 'bearer',
        expires_in: 3600,
        user: {
          id: 1,
          username: credentials.username,
          email: 'user@example.com',
          role: credentials.username === 'admin' ? 'admin' : 'user',
          is_active: true,
          is_verified: true,
          created_at: new Date().toISOString(),
          two_factor_enabled: false,
        }
      }

      // 保存 Token 和用户信息
      setToken(mockResponse.access_token, mockResponse.refresh_token)
      setUser(mockResponse.user)

      return true
    } catch (error) {
      console.error('登录失败:', error)
      return false
    }
  }

  /**
   * 登出
   */
  async function logout() {
    try {
      // TODO: 调用登出 API（可选，如果需要通知后端）
      // import { logoutApi } from '@/api/auth'
      // await logoutApi()

      // 清空状态
      user.value = null
      token.value = ''
      refreshToken.value = ''
      permission.value = null

      // 清空 localStorage
      const tokenKey = import.meta.env.VITE_TOKEN_KEY || 'appleid_access_token'
      const refreshTokenKey = import.meta.env.VITE_REFRESH_TOKEN_KEY || 'appleid_refresh_token'

      localStorage.removeItem(tokenKey)
      localStorage.removeItem(refreshTokenKey)
      localStorage.removeItem('user_info')
      localStorage.removeItem('user_permission')

      return true
    } catch (error) {
      console.error('登出失败:', error)
      return false
    }
  }

  /**
   * 刷新用户信息
   * TODO: 从后端 API 获取最新的用户信息
   */
  async function refreshUserInfo(): Promise<boolean> {
    try {
      if (!isLoggedIn.value) {
        return false
      }

      // TODO: 调用获取用户信息 API
      // import { getUserInfoApi } from '@/api/user'
      // const response = await getUserInfoApi()
      // setUser(response.data)

      return true
    } catch (error) {
      console.error('刷新用户信息失败:', error)
      return false
    }
  }

  /**
   * 刷新用户权限信息
   * TODO: 从后端 API 获取最新的权限信息
   */
  async function refreshPermission(): Promise<boolean> {
    try {
      if (!isLoggedIn.value) {
        return false
      }

      // TODO: 调用获取权限信息 API
      // import { getUserPermissionApi } from '@/api/user'
      // const response = await getUserPermissionApi()
      // setPermission(response.data)

      return true
    } catch (error) {
      console.error('刷新权限信息失败:', error)
      return false
    }
  }

  /**
   * 刷新 Token
   * TODO: 使用 refresh_token 获取新的 access_token
   */
  async function refreshAccessToken(): Promise<boolean> {
    try {
      if (!refreshToken.value) {
        return false
      }

      // TODO: 调用刷新 Token API
      // import { refreshTokenApi } from '@/api/auth'
      // const response = await refreshTokenApi({ refresh_token: refreshToken.value })
      // setToken(response.access_token, response.refresh_token)

      return true
    } catch (error) {
      console.error('刷新 Token 失败:', error)
      // Token 刷新失败，清除登录状态
      await logout()
      return false
    }
  }

  /**
   * 从 localStorage 恢复状态
   * 应用初始化时调用
   */
  function restoreFromStorage() {
    const tokenKey = import.meta.env.VITE_TOKEN_KEY || 'appleid_access_token'
    const refreshTokenKey = import.meta.env.VITE_REFRESH_TOKEN_KEY || 'appleid_refresh_token'

    // 恢复 Token
    const savedToken = localStorage.getItem(tokenKey)
    const savedRefreshToken = localStorage.getItem(refreshTokenKey)

    if (savedToken) {
      token.value = savedToken
    }
    if (savedRefreshToken) {
      refreshToken.value = savedRefreshToken
    }

    // 恢复用户信息
    const savedUser = localStorage.getItem('user_info')
    if (savedUser) {
      try {
        user.value = JSON.parse(savedUser)
      } catch (error) {
        console.error('恢复用户信息失败:', error)
      }
    }

    // 恢复权限信息
    const savedPermission = localStorage.getItem('user_permission')
    if (savedPermission) {
      try {
        permission.value = JSON.parse(savedPermission)
      } catch (error) {
        console.error('恢复权限信息失败:', error)
      }
    }
  }

  /**
   * 检查权限
   * @param requiredPermission 需要的权限键名
   */
  function hasPermission(requiredPermission: keyof UserPermission): boolean {
    if (!permission.value) return false
    if (!hasValidPermission.value) return false

    // 管理员拥有所有权限
    if (isAdmin.value) return true

    const value = permission.value[requiredPermission]

    // 布尔类型权限
    if (typeof value === 'boolean') {
      return value
    }

    // 数值类型权限（配额）
    if (typeof value === 'number') {
      return value > 0 || value === -1  // -1 表示无限制
    }

    return false
  }

  /**
   * 检查配额是否充足
   * @param quotaKey 配额键名
   * @param required 需要的数量
   */
  function hasQuota(quotaKey: keyof UserPermission, required: number = 1): boolean {
    if (!permission.value) return false
    if (!hasValidPermission.value) return false

    // 管理员拥有无限配额
    if (isAdmin.value) return true

    const value = permission.value[quotaKey]

    if (typeof value === 'number') {
      // -1 表示无限制
      if (value === -1) return true
      return value >= required
    }

    return false
  }

  // ==================== 返回 ====================

  return {
    // 状态
    user,
    token,
    refreshToken,
    permission,

    // 计算属性
    isLoggedIn,
    isAdmin,
    hasTwoFactor,
    hasValidPermission,

    // 方法
    setToken,
    setUser,
    setPermission,
    login,
    logout,
    refreshUserInfo,
    refreshPermission,
    refreshAccessToken,
    restoreFromStorage,
    hasPermission,
    hasQuota,
  }
})
