/**
 * 本地存储工具
 *
 * 职责：
 * - 封装 localStorage 和 sessionStorage 操作
 * - 提供 JSON 序列化/反序列化
 * - 支持过期时间设置
 * - 提供存储空间管理
 *
 * 上游依赖：无
 * 下游调用者：Store、组件、其他工具函数
 */

/**
 * 存储类型
 */
export type StorageType = 'local' | 'session'

/**
 * 存储项结构（支持过期时间）
 */
interface StorageItem<T> {
  value: T
  expires?: number  // 过期时间戳（毫秒）
}

/**
 * 获取存储引擎
 */
function getStorage(type: StorageType = 'local'): Storage {
  return type === 'local' ? localStorage : sessionStorage
}

/**
 * 存储数据
 * @param key 存储键
 * @param value 存储值（支持任意 JSON 可序列化的类型）
 * @param type 存储类型（默认 localStorage）
 * @param expires 过期时间（毫秒），不传则永不过期
 */
export function setItem<T = any>(
  key: string,
  value: T,
  type: StorageType = 'local',
  expires?: number
): void {
  try {
    const storage = getStorage(type)
    const item: StorageItem<T> = {
      value,
      expires: expires ? Date.now() + expires : undefined
    }
    storage.setItem(key, JSON.stringify(item))
  } catch (error) {
    console.error(`[Storage] Failed to set item "${key}":`, error)
  }
}

/**
 * 获取数据
 * @param key 存储键
 * @param type 存储类型（默认 localStorage）
 * @returns 存储值，不存在或已过期返回 null
 */
export function getItem<T = any>(
  key: string,
  type: StorageType = 'local'
): T | null {
  try {
    const storage = getStorage(type)
    const itemStr = storage.getItem(key)

    if (!itemStr) {
      return null
    }

    const item: StorageItem<T> = JSON.parse(itemStr)

    // 检查是否过期
    if (item.expires && Date.now() > item.expires) {
      removeItem(key, type)
      return null
    }

    return item.value
  } catch (error) {
    console.error(`[Storage] Failed to get item "${key}":`, error)
    return null
  }
}

/**
 * 删除数据
 * @param key 存储键
 * @param type 存储类型（默认 localStorage）
 */
export function removeItem(key: string, type: StorageType = 'local'): void {
  try {
    const storage = getStorage(type)
    storage.removeItem(key)
  } catch (error) {
    console.error(`[Storage] Failed to remove item "${key}":`, error)
  }
}

/**
 * 清空存储
 * @param type 存储类型（默认 localStorage）
 */
export function clear(type: StorageType = 'local'): void {
  try {
    const storage = getStorage(type)
    storage.clear()
  } catch (error) {
    console.error(`[Storage] Failed to clear storage:`, error)
  }
}

/**
 * 检查键是否存在
 * @param key 存储键
 * @param type 存储类型（默认 localStorage）
 */
export function hasItem(key: string, type: StorageType = 'local'): boolean {
  return getItem(key, type) !== null
}

/**
 * 获取所有键
 * @param type 存储类型（默认 localStorage）
 */
export function getAllKeys(type: StorageType = 'local'): string[] {
  try {
    const storage = getStorage(type)
    return Object.keys(storage)
  } catch (error) {
    console.error('[Storage] Failed to get all keys:', error)
    return []
  }
}

/**
 * 获取存储大小（字节）
 * @param type 存储类型（默认 localStorage）
 */
export function getStorageSize(type: StorageType = 'local'): number {
  try {
    const storage = getStorage(type)
    let size = 0

    for (const key in storage) {
      if (storage.hasOwnProperty(key)) {
        size += key.length + (storage.getItem(key)?.length || 0)
      }
    }

    return size
  } catch (error) {
    console.error('[Storage] Failed to calculate storage size:', error)
    return 0
  }
}

/**
 * 获取存储大小（格式化）
 * @param type 存储类型（默认 localStorage）
 */
export function getStorageSizeFormatted(type: StorageType = 'local'): string {
  const size = getStorageSize(type)

  if (size < 1024) {
    return `${size} B`
  } else if (size < 1024 * 1024) {
    return `${(size / 1024).toFixed(2)} KB`
  } else {
    return `${(size / (1024 * 1024)).toFixed(2)} MB`
  }
}

/**
 * 清理过期数据
 * @param type 存储类型（默认 localStorage）
 * @returns 清理的键数量
 */
export function cleanExpired(type: StorageType = 'local'): number {
  try {
    const storage = getStorage(type)
    const keys = getAllKeys(type)
    let cleanedCount = 0

    keys.forEach(key => {
      try {
        const itemStr = storage.getItem(key)
        if (itemStr) {
          const item: StorageItem<any> = JSON.parse(itemStr)

          // 如果已过期则删除
          if (item.expires && Date.now() > item.expires) {
            storage.removeItem(key)
            cleanedCount++
          }
        }
      } catch {
        // 忽略解析错误
      }
    })

    return cleanedCount
  } catch (error) {
    console.error('[Storage] Failed to clean expired items:', error)
    return 0
  }
}

/**
 * 批量设置数据
 * @param items 键值对对象
 * @param type 存储类型（默认 localStorage）
 */
export function setItems(
  items: Record<string, any>,
  type: StorageType = 'local'
): void {
  Object.entries(items).forEach(([key, value]) => {
    setItem(key, value, type)
  })
}

/**
 * 批量获取数据
 * @param keys 键数组
 * @param type 存储类型（默认 localStorage）
 */
export function getItems<T = any>(
  keys: string[],
  type: StorageType = 'local'
): Record<string, T | null> {
  const result: Record<string, T | null> = {}

  keys.forEach(key => {
    result[key] = getItem<T>(key, type)
  })

  return result
}

/**
 * 批量删除数据
 * @param keys 键数组
 * @param type 存储类型（默认 localStorage）
 */
export function removeItems(keys: string[], type: StorageType = 'local'): void {
  keys.forEach(key => {
    removeItem(key, type)
  })
}

/**
 * 存储命名空间管理
 * 用于避免键冲突，提供带前缀的存储操作
 */
export class StorageNamespace {
  private prefix: string
  private type: StorageType

  constructor(namespace: string, type: StorageType = 'local') {
    this.prefix = `${namespace}:`
    this.type = type
  }

  /**
   * 获取完整键名
   */
  private getFullKey(key: string): string {
    return `${this.prefix}${key}`
  }

  /**
   * 设置数据
   */
  set<T = any>(key: string, value: T, expires?: number): void {
    setItem(this.getFullKey(key), value, this.type, expires)
  }

  /**
   * 获取数据
   */
  get<T = any>(key: string): T | null {
    return getItem<T>(this.getFullKey(key), this.type)
  }

  /**
   * 删除数据
   */
  remove(key: string): void {
    removeItem(this.getFullKey(key), this.type)
  }

  /**
   * 检查键是否存在
   */
  has(key: string): boolean {
    return hasItem(this.getFullKey(key), this.type)
  }

  /**
   * 获取命名空间下的所有键
   */
  getAllKeys(): string[] {
    return getAllKeys(this.type)
      .filter(key => key.startsWith(this.prefix))
      .map(key => key.substring(this.prefix.length))
  }

  /**
   * 清空命名空间下的所有数据
   */
  clear(): void {
    const keys = getAllKeys(this.type).filter(key => key.startsWith(this.prefix))
    removeItems(keys, this.type)
  }
}

/**
 * 创建命名空间存储
 * @param namespace 命名空间名称
 * @param type 存储类型（默认 localStorage）
 */
export function createNamespace(
  namespace: string,
  type: StorageType = 'local'
): StorageNamespace {
  return new StorageNamespace(namespace, type)
}
