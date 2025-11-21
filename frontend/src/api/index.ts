/**
 * API 模块统一导出
 *
 * 功能：
 * - 集中导出所有 API 模块
 * - 提供统一的 API 访问入口
 * - 方便组件中按需导入
 */

// ==================== 认证模块 ====================
export * from './auth'

// ==================== 用户模块 ====================
export * from './user'

// ==================== Apple ID 管理模块 ====================
export * from './account'

// ==================== 任务管理模块 ====================
export * from './task'

// ==================== 卡密模块 ====================
export * from './card'

// ==================== 分享页模块 ====================
export * from './share'

// ==================== 代理池模块 ====================
export * from './proxy'

// ==================== 节点管理模块 ====================
export * from './node'

// ==================== 套餐管理模块 ====================
export * from './package'

// ==================== 统计分析模块 ====================
export * from './stats'

/**
 * 使用示例：
 *
 * // 方式 1: 从具体模块导入
 * import { loginApi, registerApi } from '@/api/auth'
 * import { getAccountListApi } from '@/api/account'
 *
 * // 方式 2: 从统一入口导入
 * import { loginApi, registerApi, getAccountListApi } from '@/api'
 *
 * // 方式 3: 命名空间导入
 * import * as AuthAPI from '@/api/auth'
 * AuthAPI.loginApi({ username: 'test', password: '123456' })
 */
