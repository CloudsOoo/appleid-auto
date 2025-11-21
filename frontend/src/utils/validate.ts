/**
 * 表单验证工具
 *
 * 职责：
 * - 提供常用的表单验证规则
 * - 提供自定义验证器
 * - 兼容 Element Plus 表单验证
 *
 * 上游依赖：无
 * 下游调用者：组件表单验证
 */

import type { FormRule } from '@/types/common'

/**
 * 验证器类型
 */
export type Validator = (value: any) => boolean | string

/**
 * 邮箱验证
 */
export function isEmail(value: string): boolean {
  const reg = /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/
  return reg.test(value)
}

/**
 * 手机号验证（中国大陆）
 */
export function isPhone(value: string): boolean {
  const reg = /^1[3-9]\d{9}$/
  return reg.test(value)
}

/**
 * URL 验证
 */
export function isURL(value: string): boolean {
  try {
    new URL(value)
    return true
  } catch {
    return false
  }
}

/**
 * IP 地址验证（IPv4）
 */
export function isIPv4(value: string): boolean {
  const reg = /^((25[0-5]|2[0-4]\d|[01]?\d\d?)\.){3}(25[0-5]|2[0-4]\d|[01]?\d\d?)$/
  return reg.test(value)
}

/**
 * 用户名验证（字母、数字、下划线，4-20位）
 */
export function isUsername(value: string): boolean {
  const reg = /^[a-zA-Z0-9_]{4,20}$/
  return reg.test(value)
}

/**
 * 密码强度验证
 * @param value 密码
 * @param level 强度级别（weak: 最少6位 | medium: 包含字母和数字 | strong: 包含字母、数字和特殊字符）
 */
export function isStrongPassword(
  value: string,
  level: 'weak' | 'medium' | 'strong' = 'medium'
): boolean {
  if (level === 'weak') {
    return value.length >= 6
  } else if (level === 'medium') {
    const reg = /^(?=.*[A-Za-z])(?=.*\d)[A-Za-z\d]{8,}$/
    return reg.test(value)
  } else {
    const reg = /^(?=.*[A-Za-z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$/
    return reg.test(value)
  }
}

/**
 * 身份证号验证（中国大陆）
 */
export function isIDCard(value: string): boolean {
  const reg = /(^\d{15}$)|(^\d{18}$)|(^\d{17}(\d|X|x)$)/
  return reg.test(value)
}

/**
 * 整数验证
 */
export function isInteger(value: any): boolean {
  return Number.isInteger(Number(value))
}

/**
 * 正整数验证
 */
export function isPositiveInteger(value: any): boolean {
  const num = Number(value)
  return Number.isInteger(num) && num > 0
}

/**
 * 数字范围验证
 * @param value 值
 * @param min 最小值
 * @param max 最大值
 */
export function isInRange(value: any, min: number, max: number): boolean {
  const num = Number(value)
  return !isNaN(num) && num >= min && num <= max
}

/**
 * 字符串长度验证
 * @param value 字符串
 * @param min 最小长度
 * @param max 最大长度
 */
export function isLengthInRange(value: string, min: number, max?: number): boolean {
  const len = value.length
  return max !== undefined ? len >= min && len <= max : len >= min
}

/**
 * 中文验证
 */
export function isChinese(value: string): boolean {
  const reg = /^[\u4e00-\u9fa5]+$/
  return reg.test(value)
}

/**
 * 英文字母验证
 */
export function isAlpha(value: string): boolean {
  const reg = /^[a-zA-Z]+$/
  return reg.test(value)
}

/**
 * 字母和数字验证
 */
export function isAlphaNumeric(value: string): boolean {
  const reg = /^[a-zA-Z0-9]+$/
  return reg.test(value)
}

/**
 * 银行卡号验证
 */
export function isBankCard(value: string): boolean {
  const reg = /^[1-9]\d{9,29}$/
  return reg.test(value)
}

/**
 * 邮政编码验证（中国大陆）
 */
export function isPostalCode(value: string): boolean {
  const reg = /^[1-9]\d{5}$/
  return reg.test(value)
}

/**
 * JSON 字符串验证
 */
export function isJSON(value: string): boolean {
  try {
    JSON.parse(value)
    return true
  } catch {
    return false
  }
}

/**
 * Base64 字符串验证
 */
export function isBase64(value: string): boolean {
  const reg = /^[A-Za-z0-9+/]+=*$/
  return reg.test(value)
}

/**
 * 十六进制颜色值验证
 */
export function isHexColor(value: string): boolean {
  const reg = /^#([0-9a-fA-F]{3}|[0-9a-fA-F]{6})$/
  return reg.test(value)
}

/**
 * Apple ID 验证（邮箱格式）
 */
export function isAppleID(value: string): boolean {
  return isEmail(value)
}

/**
 * 卡密格式验证（XXXX-XXXX-XXXX-XXXX）
 */
export function isCardCode(value: string): boolean {
  const reg = /^[A-Z0-9]{4}-[A-Z0-9]{4}-[A-Z0-9]{4}-[A-Z0-9]{4}$/
  return reg.test(value)
}

/**
 * Slug 格式验证（小写字母、数字、连字符）
 */
export function isSlug(value: string): boolean {
  const reg = /^[a-z0-9]+(?:-[a-z0-9]+)*$/
  return reg.test(value)
}

// ==================== Element Plus 表单验证规则 ====================

/**
 * 必填验证规则
 * @param message 错误提示（可选）
 * @param trigger 触发方式（默认 blur）
 */
export function requiredRule(
  message?: string,
  trigger: 'blur' | 'change' = 'blur'
): FormRule {
  return {
    required: true,
    message: message || '该字段不能为空',
    trigger
  }
}

/**
 * 邮箱验证规则
 * @param message 错误提示（可选）
 */
export function emailRule(message?: string): FormRule {
  return {
    type: 'email',
    message: message || '请输入有效的邮箱地址',
    trigger: 'blur',
    validator: (rule, value, callback) => {
      if (!value) {
        callback()
      } else if (isEmail(value)) {
        callback()
      } else {
        callback(new Error(message || '请输入有效的邮箱地址'))
      }
    }
  }
}

/**
 * 手机号验证规则
 * @param message 错误提示（可选）
 */
export function phoneRule(message?: string): FormRule {
  return {
    message: message || '请输入有效的手机号',
    trigger: 'blur',
    validator: (rule, value, callback) => {
      if (!value) {
        callback()
      } else if (isPhone(value)) {
        callback()
      } else {
        callback(new Error(message || '请输入有效的手机号'))
      }
    }
  }
}

/**
 * URL 验证规则
 * @param message 错误提示（可选）
 */
export function urlRule(message?: string): FormRule {
  return {
    type: 'url',
    message: message || '请输入有效的 URL 地址',
    trigger: 'blur',
    validator: (rule, value, callback) => {
      if (!value) {
        callback()
      } else if (isURL(value)) {
        callback()
      } else {
        callback(new Error(message || '请输入有效的 URL 地址'))
      }
    }
  }
}

/**
 * 用户名验证规则
 * @param message 错误提示（可选）
 */
export function usernameRule(message?: string): FormRule {
  return {
    message: message || '用户名只能包含字母、数字和下划线，长度4-20位',
    trigger: 'blur',
    validator: (rule, value, callback) => {
      if (!value) {
        callback()
      } else if (isUsername(value)) {
        callback()
      } else {
        callback(new Error(message || '用户名只能包含字母、数字和下划线，长度4-20位'))
      }
    }
  }
}

/**
 * 密码强度验证规则
 * @param level 强度级别
 * @param message 错误提示（可选）
 */
export function passwordRule(
  level: 'weak' | 'medium' | 'strong' = 'medium',
  message?: string
): FormRule {
  const defaultMessages = {
    weak: '密码长度至少6位',
    medium: '密码至少8位，包含字母和数字',
    strong: '密码至少8位，包含字母、数字和特殊字符'
  }

  return {
    message: message || defaultMessages[level],
    trigger: 'blur',
    validator: (rule, value, callback) => {
      if (!value) {
        callback()
      } else if (isStrongPassword(value, level)) {
        callback()
      } else {
        callback(new Error(message || defaultMessages[level]))
      }
    }
  }
}

/**
 * 长度范围验证规则
 * @param min 最小长度
 * @param max 最大长度（可选）
 * @param message 错误提示（可选）
 */
export function lengthRule(min: number, max?: number, message?: string): FormRule {
  return {
    min,
    max,
    message: message || (max ? `长度必须在 ${min} 到 ${max} 之间` : `长度至少为 ${min}`),
    trigger: 'blur'
  }
}

/**
 * 数字范围验证规则
 * @param min 最小值
 * @param max 最大值
 * @param message 错误提示（可选）
 */
export function rangeRule(min: number, max: number, message?: string): FormRule {
  return {
    type: 'number',
    message: message || `数值必须在 ${min} 到 ${max} 之间`,
    trigger: 'blur',
    validator: (rule, value, callback) => {
      if (value === '' || value === null || value === undefined) {
        callback()
      } else if (isInRange(value, min, max)) {
        callback()
      } else {
        callback(new Error(message || `数值必须在 ${min} 到 ${max} 之间`))
      }
    }
  }
}

/**
 * 确认密码验证规则
 * @param getPassword 获取原密码的函数
 * @param message 错误提示（可选）
 */
export function confirmPasswordRule(
  getPassword: () => string,
  message?: string
): FormRule {
  return {
    message: message || '两次输入的密码不一致',
    trigger: 'blur',
    validator: (rule, value, callback) => {
      if (!value) {
        callback()
      } else if (value === getPassword()) {
        callback()
      } else {
        callback(new Error(message || '两次输入的密码不一致'))
      }
    }
  }
}

/**
 * Apple ID 验证规则
 * @param message 错误提示（可选）
 */
export function appleIDRule(message?: string): FormRule {
  return emailRule(message || '请输入有效的 Apple ID（邮箱格式）')
}

/**
 * 卡密格式验证规则
 * @param message 错误提示（可选）
 */
export function cardCodeRule(message?: string): FormRule {
  return {
    message: message || '卡密格式不正确（格式：XXXX-XXXX-XXXX-XXXX）',
    trigger: 'blur',
    validator: (rule, value, callback) => {
      if (!value) {
        callback()
      } else if (isCardCode(value)) {
        callback()
      } else {
        callback(new Error(message || '卡密格式不正确（格式：XXXX-XXXX-XXXX-XXXX）'))
      }
    }
  }
}

/**
 * Slug 验证规则（用于分享页 URL）
 * @param message 错误提示（可选）
 */
export function slugRule(message?: string): FormRule {
  return {
    message: message || 'URL 路径只能包含小写字母、数字和连字符',
    trigger: 'blur',
    validator: (rule, value, callback) => {
      if (!value) {
        callback()
      } else if (isSlug(value)) {
        callback()
      } else {
        callback(new Error(message || 'URL 路径只能包含小写字母、数字和连字符'))
      }
    }
  }
}
