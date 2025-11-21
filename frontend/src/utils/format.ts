/**
 * 数据格式化工具
 *
 * 职责：
 * - 提供数字、货币、文件大小等格式化
 * - 提供字符串处理工具
 * - 提供数据脱敏工具
 *
 * 上游依赖：无
 * 下游调用者：组件、表格列、统计图表
 */

/**
 * 格式化数字
 * @param value 数字
 * @param decimals 小数位数（默认 2）
 * @param thousandsSeparator 千位分隔符（默认逗号）
 * @returns 格式化后的字符串
 *
 * @example
 * formatNumber(1234567.89) // '1,234,567.89'
 * formatNumber(1234567.89, 0) // '1,234,568'
 */
export function formatNumber(
  value: number | string,
  decimals: number = 2,
  thousandsSeparator: string = ','
): string {
  const num = Number(value)

  if (isNaN(num)) {
    return '0'
  }

  const parts = num.toFixed(decimals).split('.')
  const integerPart = parts[0].replace(/\B(?=(\d{3})+(?!\d))/g, thousandsSeparator)

  return decimals > 0 && parts[1] ? `${integerPart}.${parts[1]}` : integerPart
}

/**
 * 格式化货币
 * @param value 金额
 * @param currency 货币符号（默认 ¥）
 * @param decimals 小数位数（默认 2）
 *
 * @example
 * formatCurrency(1234.56) // '¥1,234.56'
 * formatCurrency(1234.56, '$') // '$1,234.56'
 */
export function formatCurrency(
  value: number | string,
  currency: string = '¥',
  decimals: number = 2
): string {
  return `${currency}${formatNumber(value, decimals)}`
}

/**
 * 格式化百分比
 * @param value 数值（0-1 或 0-100）
 * @param decimals 小数位数（默认 2）
 * @param isDecimal 是否为小数形式（默认 true）
 *
 * @example
 * formatPercentage(0.1234) // '12.34%'
 * formatPercentage(12.34, 2, false) // '12.34%'
 */
export function formatPercentage(
  value: number | string,
  decimals: number = 2,
  isDecimal: boolean = true
): string {
  const num = Number(value)

  if (isNaN(num)) {
    return '0%'
  }

  const percentage = isDecimal ? num * 100 : num
  return `${percentage.toFixed(decimals)}%`
}

/**
 * 格式化文件大小
 * @param bytes 字节数
 * @param decimals 小数位数（默认 2）
 *
 * @example
 * formatFileSize(1024) // '1.00 KB'
 * formatFileSize(1048576) // '1.00 MB'
 */
export function formatFileSize(bytes: number, decimals: number = 2): string {
  if (bytes === 0) {
    return '0 B'
  }

  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB', 'TB', 'PB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))

  return `${(bytes / Math.pow(k, i)).toFixed(decimals)} ${sizes[i]}`
}

/**
 * 格式化带宽速度
 * @param bytesPerSecond 每秒字节数
 * @param decimals 小数位数（默认 2）
 *
 * @example
 * formatBandwidth(1024) // '1.00 KB/s'
 * formatBandwidth(1048576) // '1.00 MB/s'
 */
export function formatBandwidth(bytesPerSecond: number, decimals: number = 2): string {
  return `${formatFileSize(bytesPerSecond, decimals)}/s`
}

/**
 * 格式化数字为紧凑形式
 * @param value 数字
 * @param locale 语言环境（默认 zh-CN）
 *
 * @example
 * formatCompactNumber(1234) // '1.2千'
 * formatCompactNumber(1234567) // '123.5万'
 */
export function formatCompactNumber(value: number, locale: string = 'zh-CN'): string {
  if (locale === 'zh-CN') {
    if (value < 10000) {
      return String(value)
    } else if (value < 100000000) {
      return `${(value / 10000).toFixed(1)}万`
    } else {
      return `${(value / 100000000).toFixed(1)}亿`
    }
  } else {
    // en-US
    if (value < 1000) {
      return String(value)
    } else if (value < 1000000) {
      return `${(value / 1000).toFixed(1)}K`
    } else if (value < 1000000000) {
      return `${(value / 1000000).toFixed(1)}M`
    } else {
      return `${(value / 1000000000).toFixed(1)}B`
    }
  }
}

/**
 * 格式化手机号（脱敏）
 * @param phone 手机号
 * @param maskChar 掩码字符（默认 *）
 *
 * @example
 * formatPhone('13812345678') // '138****5678'
 */
export function formatPhone(phone: string, maskChar: string = '*'): string {
  if (!phone || phone.length !== 11) {
    return phone
  }

  return phone.replace(/(\d{3})\d{4}(\d{4})/, `$1${maskChar.repeat(4)}$2`)
}

/**
 * 格式化邮箱（脱敏）
 * @param email 邮箱
 * @param maskChar 掩码字符（默认 *）
 *
 * @example
 * formatEmail('example@gmail.com') // 'ex***e@gmail.com'
 */
export function formatEmail(email: string, maskChar: string = '*'): string {
  if (!email || !email.includes('@')) {
    return email
  }

  const [username, domain] = email.split('@')

  if (username.length <= 2) {
    return email
  }

  const firstChar = username[0]
  const lastChar = username[username.length - 1]
  const maskedUsername = `${firstChar}${maskChar.repeat(3)}${lastChar}`

  return `${maskedUsername}@${domain}`
}

/**
 * 格式化身份证号（脱敏）
 * @param idCard 身份证号
 * @param maskChar 掩码字符（默认 *）
 *
 * @example
 * formatIDCard('110101199001011234') // '110101********1234'
 */
export function formatIDCard(idCard: string, maskChar: string = '*'): string {
  if (!idCard || idCard.length < 15) {
    return idCard
  }

  return idCard.replace(/(\d{6})\d+(\d{4})/, `$1${maskChar.repeat(8)}$2`)
}

/**
 * 格式化银行卡号（脱敏 + 空格分隔）
 * @param cardNumber 银行卡号
 * @param maskChar 掩码字符（默认 *）
 *
 * @example
 * formatBankCard('6222021234567890123') // '6222 **** **** **** 0123'
 */
export function formatBankCard(cardNumber: string, maskChar: string = '*'): string {
  if (!cardNumber || cardNumber.length < 16) {
    return cardNumber
  }

  const first4 = cardNumber.slice(0, 4)
  const last4 = cardNumber.slice(-4)
  const masked = `${first4} ${maskChar.repeat(4)} ${maskChar.repeat(4)} ${maskChar.repeat(4)} ${last4}`

  return masked
}

/**
 * 格式化 Apple ID（脱敏）
 * @param appleId Apple ID
 * @param maskChar 掩码字符（默认 *）
 *
 * @example
 * formatAppleID('example@icloud.com') // 'ex***e@icloud.com'
 */
export function formatAppleID(appleId: string, maskChar: string = '*'): string {
  return formatEmail(appleId, maskChar)
}

/**
 * 截断字符串
 * @param text 文本
 * @param maxLength 最大长度
 * @param ellipsis 省略号（默认 ...）
 *
 * @example
 * truncate('这是一段很长的文本内容', 10) // '这是一段很长的...'
 */
export function truncate(text: string, maxLength: number, ellipsis: string = '...'): string {
  if (!text || text.length <= maxLength) {
    return text
  }

  return text.slice(0, maxLength - ellipsis.length) + ellipsis
}

/**
 * 首字母大写
 * @param text 文本
 *
 * @example
 * capitalize('hello world') // 'Hello world'
 */
export function capitalize(text: string): string {
  if (!text) {
    return text
  }

  return text.charAt(0).toUpperCase() + text.slice(1)
}

/**
 * 驼峰命名转换
 * @param text 文本（snake_case 或 kebab-case）
 *
 * @example
 * camelCase('hello_world') // 'helloWorld'
 * camelCase('hello-world') // 'helloWorld'
 */
export function camelCase(text: string): string {
  return text.replace(/[-_](.)/g, (_, char) => char.toUpperCase())
}

/**
 * 下划线命名转换
 * @param text 文本（camelCase）
 *
 * @example
 * snakeCase('helloWorld') // 'hello_world'
 */
export function snakeCase(text: string): string {
  return text.replace(/([A-Z])/g, '_$1').toLowerCase().replace(/^_/, '')
}

/**
 * 连字符命名转换
 * @param text 文本（camelCase）
 *
 * @example
 * kebabCase('helloWorld') // 'hello-world'
 */
export function kebabCase(text: string): string {
  return text.replace(/([A-Z])/g, '-$1').toLowerCase().replace(/^-/, '')
}

/**
 * 格式化IP地址（脱敏）
 * @param ip IP地址
 * @param maskChar 掩码字符（默认 *）
 *
 * @example
 * formatIP('192.168.1.100') // '192.168.***.***'
 */
export function formatIP(ip: string, maskChar: string = '*'): string {
  if (!ip) {
    return ip
  }

  const parts = ip.split('.')

  if (parts.length !== 4) {
    return ip
  }

  return `${parts[0]}.${parts[1]}.${maskChar.repeat(3)}.${maskChar.repeat(3)}`
}

/**
 * 格式化代理地址
 * @param proxy 代理对象
 *
 * @example
 * formatProxy({ host: '127.0.0.1', port: 1080, type: 'socks5' })
 * // 'socks5://127.0.0.1:1080'
 */
export function formatProxy(proxy: {
  type?: string
  host: string
  port: number
  username?: string
  password?: string
}): string {
  const { type = 'http', host, port, username, password } = proxy

  if (username && password) {
    return `${type}://${username}:${password}@${host}:${port}`
  }

  return `${type}://${host}:${port}`
}

/**
 * 高亮关键词
 * @param text 文本
 * @param keyword 关键词
 * @param className CSS 类名（默认 highlight）
 *
 * @example
 * highlightKeyword('hello world', 'world')
 * // 'hello <span class="highlight">world</span>'
 */
export function highlightKeyword(
  text: string,
  keyword: string,
  className: string = 'highlight'
): string {
  if (!text || !keyword) {
    return text
  }

  const reg = new RegExp(`(${keyword})`, 'gi')
  return text.replace(reg, `<span class="${className}">$1</span>`)
}

/**
 * 移除 HTML 标签
 * @param html HTML 字符串
 *
 * @example
 * stripHTML('<p>Hello <strong>World</strong></p>') // 'Hello World'
 */
export function stripHTML(html: string): string {
  if (!html) {
    return html
  }

  const div = document.createElement('div')
  div.innerHTML = html
  return div.textContent || div.innerText || ''
}

/**
 * 转义 HTML 特殊字符
 * @param text 文本
 *
 * @example
 * escapeHTML('<div>Hello</div>') // '&lt;div&gt;Hello&lt;/div&gt;'
 */
export function escapeHTML(text: string): string {
  const div = document.createElement('div')
  div.textContent = text
  return div.innerHTML
}

/**
 * 解析查询字符串
 * @param search 查询字符串（如 ?name=foo&age=20）
 *
 * @example
 * parseQueryString('?name=foo&age=20') // { name: 'foo', age: '20' }
 */
export function parseQueryString(search: string): Record<string, string> {
  const params = new URLSearchParams(search)
  const result: Record<string, string> = {}

  params.forEach((value, key) => {
    result[key] = value
  })

  return result
}

/**
 * 构建查询字符串
 * @param params 参数对象
 *
 * @example
 * buildQueryString({ name: 'foo', age: '20' }) // 'name=foo&age=20'
 */
export function buildQueryString(params: Record<string, any>): string {
  const searchParams = new URLSearchParams()

  Object.entries(params).forEach(([key, value]) => {
    if (value !== null && value !== undefined) {
      searchParams.append(key, String(value))
    }
  })

  return searchParams.toString()
}
