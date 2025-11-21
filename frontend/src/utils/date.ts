/**
 * 日期格式化工具
 *
 * 职责：
 * - 提供日期格式化功能
 * - 提供相对时间计算
 * - 提供日期范围工具
 * - 提供时区转换
 *
 * 上游依赖：无
 * 下游调用者：组件、格式化工具
 */

/**
 * 日期格式化选项
 */
export interface DateFormatOptions {
  locale?: string  // 语言环境（默认 zh-CN）
  timeZone?: string  // 时区（默认本地时区）
  use12Hour?: boolean  // 是否使用12小时制
}

/**
 * 格式化日期
 * @param date 日期（Date 对象、时间戳或日期字符串）
 * @param format 格式字符串
 * @returns 格式化后的字符串
 *
 * 格式说明：
 * - YYYY: 四位年份
 * - YY: 两位年份
 * - MM: 两位月份（01-12）
 * - M: 月份（1-12）
 * - DD: 两位日期（01-31）
 * - D: 日期（1-31）
 * - HH: 24小时制小时（00-23）
 * - hh: 12小时制小时（01-12）
 * - mm: 分钟（00-59）
 * - ss: 秒（00-59）
 * - SSS: 毫秒（000-999）
 * - A: 上午/下午（AM/PM）
 * - a: 上午/下午（am/pm）
 *
 * @example
 * formatDate(new Date(), 'YYYY-MM-DD HH:mm:ss') // '2025-11-21 10:30:45'
 * formatDate(new Date(), 'YYYY年MM月DD日') // '2025年11月21日'
 */
export function formatDate(
  date: Date | number | string,
  format: string = 'YYYY-MM-DD HH:mm:ss'
): string {
  const d = parseDate(date)

  if (!d || isNaN(d.getTime())) {
    return ''
  }

  const year = d.getFullYear()
  const month = d.getMonth() + 1
  const day = d.getDate()
  const hours = d.getHours()
  const minutes = d.getMinutes()
  const seconds = d.getSeconds()
  const milliseconds = d.getMilliseconds()

  const hours12 = hours % 12 || 12
  const ampm = hours < 12 ? 'AM' : 'PM'
  const ampmLower = ampm.toLowerCase()

  const replacements: Record<string, string> = {
    YYYY: String(year),
    YY: String(year).slice(-2),
    MM: String(month).padStart(2, '0'),
    M: String(month),
    DD: String(day).padStart(2, '0'),
    D: String(day),
    HH: String(hours).padStart(2, '0'),
    H: String(hours),
    hh: String(hours12).padStart(2, '0'),
    h: String(hours12),
    mm: String(minutes).padStart(2, '0'),
    m: String(minutes),
    ss: String(seconds).padStart(2, '0'),
    s: String(seconds),
    SSS: String(milliseconds).padStart(3, '0'),
    A: ampm,
    a: ampmLower
  }

  let result = format

  // 按长度降序替换，避免短格式覆盖长格式
  Object.keys(replacements)
    .sort((a, b) => b.length - a.length)
    .forEach(key => {
      result = result.replace(new RegExp(key, 'g'), replacements[key])
    })

  return result
}

/**
 * 解析日期
 * @param date 日期（Date 对象、时间戳或日期字符串）
 * @returns Date 对象或 null
 */
export function parseDate(date: Date | number | string | null | undefined): Date | null {
  if (!date) {
    return null
  }

  if (date instanceof Date) {
    return date
  }

  if (typeof date === 'number') {
    return new Date(date)
  }

  if (typeof date === 'string') {
    const parsed = new Date(date)
    return isNaN(parsed.getTime()) ? null : parsed
  }

  return null
}

/**
 * 获取相对时间
 * @param date 日期
 * @param options 格式化选项
 * @returns 相对时间字符串（如 "3分钟前"、"2小时前"）
 */
export function getRelativeTime(
  date: Date | number | string,
  options: DateFormatOptions = {}
): string {
  const d = parseDate(date)

  if (!d) {
    return ''
  }

  const now = Date.now()
  const diff = now - d.getTime()  // 毫秒差
  const locale = options.locale || 'zh-CN'

  const seconds = Math.floor(diff / 1000)
  const minutes = Math.floor(seconds / 60)
  const hours = Math.floor(minutes / 60)
  const days = Math.floor(hours / 24)
  const months = Math.floor(days / 30)
  const years = Math.floor(days / 365)

  if (locale === 'zh-CN') {
    if (seconds < 60) {
      return '刚刚'
    } else if (minutes < 60) {
      return `${minutes}分钟前`
    } else if (hours < 24) {
      return `${hours}小时前`
    } else if (days < 30) {
      return `${days}天前`
    } else if (months < 12) {
      return `${months}个月前`
    } else {
      return `${years}年前`
    }
  } else {
    // en-US
    if (seconds < 60) {
      return 'just now'
    } else if (minutes < 60) {
      return `${minutes} minute${minutes > 1 ? 's' : ''} ago`
    } else if (hours < 24) {
      return `${hours} hour${hours > 1 ? 's' : ''} ago`
    } else if (days < 30) {
      return `${days} day${days > 1 ? 's' : ''} ago`
    } else if (months < 12) {
      return `${months} month${months > 1 ? 's' : ''} ago`
    } else {
      return `${years} year${years > 1 ? 's' : ''} ago`
    }
  }
}

/**
 * 计算两个日期的时间差
 * @param startDate 开始日期
 * @param endDate 结束日期（默认当前时间）
 * @returns 时间差对象
 */
export function getDateDiff(
  startDate: Date | number | string,
  endDate: Date | number | string = new Date()
): {
  milliseconds: number
  seconds: number
  minutes: number
  hours: number
  days: number
} {
  const start = parseDate(startDate)
  const end = parseDate(endDate)

  if (!start || !end) {
    return {
      milliseconds: 0,
      seconds: 0,
      minutes: 0,
      hours: 0,
      days: 0
    }
  }

  const diff = Math.abs(end.getTime() - start.getTime())

  return {
    milliseconds: diff,
    seconds: Math.floor(diff / 1000),
    minutes: Math.floor(diff / (1000 * 60)),
    hours: Math.floor(diff / (1000 * 60 * 60)),
    days: Math.floor(diff / (1000 * 60 * 60 * 24))
  }
}

/**
 * 格式化持续时间
 * @param milliseconds 毫秒数
 * @param locale 语言环境
 * @returns 格式化后的持续时间（如 "2小时30分钟"）
 */
export function formatDuration(milliseconds: number, locale: string = 'zh-CN'): string {
  const seconds = Math.floor(milliseconds / 1000)
  const minutes = Math.floor(seconds / 60)
  const hours = Math.floor(minutes / 60)
  const days = Math.floor(hours / 24)

  const remainingHours = hours % 24
  const remainingMinutes = minutes % 60
  const remainingSeconds = seconds % 60

  if (locale === 'zh-CN') {
    const parts: string[] = []

    if (days > 0) parts.push(`${days}天`)
    if (remainingHours > 0) parts.push(`${remainingHours}小时`)
    if (remainingMinutes > 0) parts.push(`${remainingMinutes}分钟`)
    if (remainingSeconds > 0 && days === 0 && hours === 0) {
      parts.push(`${remainingSeconds}秒`)
    }

    return parts.join('') || '0秒'
  } else {
    const parts: string[] = []

    if (days > 0) parts.push(`${days}d`)
    if (remainingHours > 0) parts.push(`${remainingHours}h`)
    if (remainingMinutes > 0) parts.push(`${remainingMinutes}m`)
    if (remainingSeconds > 0 && days === 0 && hours === 0) {
      parts.push(`${remainingSeconds}s`)
    }

    return parts.join(' ') || '0s'
  }
}

/**
 * 判断是否为今天
 * @param date 日期
 */
export function isToday(date: Date | number | string): boolean {
  const d = parseDate(date)

  if (!d) {
    return false
  }

  const today = new Date()
  return (
    d.getFullYear() === today.getFullYear() &&
    d.getMonth() === today.getMonth() &&
    d.getDate() === today.getDate()
  )
}

/**
 * 判断是否为昨天
 * @param date 日期
 */
export function isYesterday(date: Date | number | string): boolean {
  const d = parseDate(date)

  if (!d) {
    return false
  }

  const yesterday = new Date()
  yesterday.setDate(yesterday.getDate() - 1)

  return (
    d.getFullYear() === yesterday.getFullYear() &&
    d.getMonth() === yesterday.getMonth() &&
    d.getDate() === yesterday.getDate()
  )
}

/**
 * 判断是否为本周
 * @param date 日期
 */
export function isThisWeek(date: Date | number | string): boolean {
  const d = parseDate(date)

  if (!d) {
    return false
  }

  const today = new Date()
  const firstDayOfWeek = new Date(today.setDate(today.getDate() - today.getDay()))
  const lastDayOfWeek = new Date(firstDayOfWeek)
  lastDayOfWeek.setDate(lastDayOfWeek.getDate() + 6)

  return d >= firstDayOfWeek && d <= lastDayOfWeek
}

/**
 * 获取日期范围
 * @param type 范围类型
 * @returns [开始日期, 结束日期]
 */
export function getDateRange(
  type: 'today' | 'yesterday' | 'week' | 'month' | 'year' | 'last7days' | 'last30days'
): [Date, Date] {
  const now = new Date()
  const today = new Date(now.getFullYear(), now.getMonth(), now.getDate())

  switch (type) {
    case 'today':
      return [
        today,
        new Date(today.getFullYear(), today.getMonth(), today.getDate(), 23, 59, 59, 999)
      ]

    case 'yesterday': {
      const yesterday = new Date(today)
      yesterday.setDate(yesterday.getDate() - 1)
      return [
        yesterday,
        new Date(yesterday.getFullYear(), yesterday.getMonth(), yesterday.getDate(), 23, 59, 59, 999)
      ]
    }

    case 'week': {
      const firstDay = new Date(today)
      firstDay.setDate(firstDay.getDate() - firstDay.getDay())
      const lastDay = new Date(firstDay)
      lastDay.setDate(lastDay.getDate() + 6)
      lastDay.setHours(23, 59, 59, 999)
      return [firstDay, lastDay]
    }

    case 'month': {
      const firstDay = new Date(now.getFullYear(), now.getMonth(), 1)
      const lastDay = new Date(now.getFullYear(), now.getMonth() + 1, 0, 23, 59, 59, 999)
      return [firstDay, lastDay]
    }

    case 'year': {
      const firstDay = new Date(now.getFullYear(), 0, 1)
      const lastDay = new Date(now.getFullYear(), 11, 31, 23, 59, 59, 999)
      return [firstDay, lastDay]
    }

    case 'last7days': {
      const startDay = new Date(today)
      startDay.setDate(startDay.getDate() - 6)
      const endDay = new Date(today)
      endDay.setHours(23, 59, 59, 999)
      return [startDay, endDay]
    }

    case 'last30days': {
      const startDay = new Date(today)
      startDay.setDate(startDay.getDate() - 29)
      const endDay = new Date(today)
      endDay.setHours(23, 59, 59, 999)
      return [startDay, endDay]
    }

    default:
      return [today, today]
  }
}

/**
 * 格式化日期范围
 * @param startDate 开始日期
 * @param endDate 结束日期
 * @param format 格式字符串
 * @param separator 分隔符
 */
export function formatDateRange(
  startDate: Date | number | string,
  endDate: Date | number | string,
  format: string = 'YYYY-MM-DD',
  separator: string = ' ~ '
): string {
  const start = formatDate(startDate, format)
  const end = formatDate(endDate, format)

  return `${start}${separator}${end}`
}

/**
 * 获取月份天数
 * @param year 年份
 * @param month 月份（1-12）
 */
export function getDaysInMonth(year: number, month: number): number {
  return new Date(year, month, 0).getDate()
}

/**
 * 判断是否为闰年
 * @param year 年份
 */
export function isLeapYear(year: number): boolean {
  return (year % 4 === 0 && year % 100 !== 0) || year % 400 === 0
}
