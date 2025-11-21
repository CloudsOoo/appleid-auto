/**
 * 类型定义统一导出
 *
 * 职责：
 * - 集中导出所有类型定义模块
 * - 提供统一的类型访问入口
 * - 方便组件和模块中按需导入类型
 *
 * 使用示例：
 * ```typescript
 * // 方式 1: 从统一入口导入
 * import type { User, AppleAccount, UnlockTask } from '@/types'
 *
 * // 方式 2: 从具体模块导入
 * import type { User, UserPermission } from '@/types/user'
 * import type { AppleAccount } from '@/types/account'
 *
 * // 方式 3: 命名空间导入
 * import type * as UserTypes from '@/types/user'
 * import type * as AccountTypes from '@/types/account'
 * ```
 */

// ==================== 通用类型 ====================
export * from './common'

// ==================== 用户类型 ====================
export * from './user'

// ==================== Apple ID 账号类型 ====================
export * from './account'

// ==================== 任务类型 ====================
export * from './task'

// ==================== 卡密类型 ====================
export * from './card'

// ==================== 分享页类型 ====================
export * from './share'

// ==================== API 响应类型 ====================
export * from './api'
