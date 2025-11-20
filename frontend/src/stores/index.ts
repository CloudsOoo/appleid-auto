import { createPinia } from 'pinia'
import type { App } from 'vue'

/**
 * Pinia 状态管理主文件
 *
 * 功能：
 * - 创建 Pinia 实例
 * - 安装到 Vue 应用
 * - 导出所有 Store
 */

/**
 * 创建 Pinia 实例
 */
const pinia = createPinia()

/**
 * 安装 Pinia 到 Vue 应用
 */
export function setupStore(app: App) {
  app.use(pinia)
}

/**
 * 导出 Pinia 实例（用于在非组件中使用）
 */
export { pinia }

/**
 * 导出所有 Store
 */
export { useUserStore } from './user'
export { useAppStore } from './app'

/**
 * 导出类型定义
 */
export type { UserInfo, UserPermission, LoginCredentials, LoginResponse } from './user'
export type { Theme, Language } from './app'

/**
 * 初始化所有 Store
 * 在应用启动时调用，恢复持久化状态
 */
export function initStores() {
  // 导入 Store
  const { useUserStore } = await import('./user')
  const { useAppStore } = await import('./app')

  // 获取 Store 实例
  const userStore = useUserStore(pinia)
  const appStore = useAppStore(pinia)

  // 恢复状态
  userStore.restoreFromStorage()
  appStore.restoreFromStorage()

  console.log('✅ Pinia stores initialized')
}

export default pinia
