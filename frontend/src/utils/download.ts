/**
 * 文件下载工具
 *
 * 职责：
 * - 提供文件下载功能
 * - 支持 Blob、URL、Base64 等多种下载方式
 * - 提供导出 CSV、JSON、Excel 等功能
 *
 * 上游依赖：format.ts（可选）
 * 下游调用者：组件、API 响应处理
 */

/**
 * 下载文件（通用方法）
 * @param url 文件 URL 或 Blob
 * @param filename 文件名
 */
export function downloadFile(url: string | Blob, filename: string): void {
  const link = document.createElement('a')
  link.style.display = 'none'

  if (url instanceof Blob) {
    link.href = URL.createObjectURL(url)
  } else {
    link.href = url
  }

  link.download = filename
  document.body.appendChild(link)
  link.click()

  // 清理
  setTimeout(() => {
    document.body.removeChild(link)

    if (url instanceof Blob) {
      URL.revokeObjectURL(link.href)
    }
  }, 100)
}

/**
 * 下载文本文件
 * @param content 文本内容
 * @param filename 文件名
 * @param mimeType MIME 类型（默认 text/plain）
 */
export function downloadText(
  content: string,
  filename: string,
  mimeType: string = 'text/plain'
): void {
  const blob = new Blob([content], { type: `${mimeType};charset=utf-8` })
  downloadFile(blob, filename)
}

/**
 * 下载 JSON 文件
 * @param data JSON 数据
 * @param filename 文件名
 * @param pretty 是否格式化（默认 true）
 */
export function downloadJSON(data: any, filename: string, pretty: boolean = true): void {
  const content = pretty ? JSON.stringify(data, null, 2) : JSON.stringify(data)
  downloadText(content, filename, 'application/json')
}

/**
 * 下载 CSV 文件
 * @param data 数据数组
 * @param filename 文件名
 * @param headers 表头（可选）
 */
export function downloadCSV(
  data: any[],
  filename: string,
  headers?: string[]
): void {
  if (!data || data.length === 0) {
    console.warn('[Download] No data to download')
    return
  }

  // 如果没有提供表头，使用第一行数据的键作为表头
  const csvHeaders = headers || Object.keys(data[0])

  // 构建 CSV 内容
  const csvRows: string[] = []

  // 添加表头
  csvRows.push(csvHeaders.map(escapeCSVValue).join(','))

  // 添加数据行
  data.forEach(row => {
    const values = csvHeaders.map(header => {
      const value = row[header]
      return escapeCSVValue(value)
    })
    csvRows.push(values.join(','))
  })

  const content = csvRows.join('\n')

  // 添加 BOM 以支持 Excel 打开 UTF-8 文件
  const blob = new Blob(['\ufeff' + content], { type: 'text/csv;charset=utf-8' })
  downloadFile(blob, filename)
}

/**
 * 转义 CSV 值
 * @param value 值
 */
function escapeCSVValue(value: any): string {
  if (value === null || value === undefined) {
    return ''
  }

  const str = String(value)

  // 如果包含逗号、引号、换行符，需要用引号包裹并转义引号
  if (str.includes(',') || str.includes('"') || str.includes('\n')) {
    return `"${str.replace(/"/g, '""')}"`
  }

  return str
}

/**
 * 下载 Excel 文件（基于 CSV）
 * @param data 数据数组
 * @param filename 文件名
 * @param headers 表头（可选）
 *
 * 注意：这是一个简化版本，使用 CSV 格式。
 * 如需真正的 Excel 格式（.xlsx），请使用 xlsx 库。
 */
export function downloadExcel(
  data: any[],
  filename: string,
  headers?: string[]
): void {
  // 确保文件名以 .xlsx 结尾
  if (!filename.endsWith('.xlsx')) {
    filename = filename.replace(/\.\w+$/, '') + '.xlsx'
  }

  downloadCSV(data, filename, headers)
}

/**
 * 下载 Base64 文件
 * @param base64 Base64 字符串
 * @param filename 文件名
 * @param mimeType MIME 类型
 */
export function downloadBase64(base64: string, filename: string, mimeType: string): void {
  // 移除 Base64 前缀（如 data:image/png;base64,）
  const base64Data = base64.replace(/^data:[^;]+;base64,/, '')

  // 解码 Base64
  const binaryString = atob(base64Data)
  const bytes = new Uint8Array(binaryString.length)

  for (let i = 0; i < binaryString.length; i++) {
    bytes[i] = binaryString.charCodeAt(i)
  }

  const blob = new Blob([bytes], { type: mimeType })
  downloadFile(blob, filename)
}

/**
 * 下载图片
 * @param url 图片 URL 或 Base64
 * @param filename 文件名
 */
export function downloadImage(url: string, filename: string): void {
  if (url.startsWith('data:image')) {
    // Base64 图片
    const mimeType = url.match(/data:(.*?);base64/)?.[1] || 'image/png'
    downloadBase64(url, filename, mimeType)
  } else {
    // URL 图片
    fetch(url)
      .then(response => response.blob())
      .then(blob => downloadFile(blob, filename))
      .catch(error => {
        console.error('[Download] Failed to download image:', error)
      })
  }
}

/**
 * 从 Blob 响应下载文件
 * @param response Blob 响应
 * @param defaultFilename 默认文件名
 */
export function downloadFromBlobResponse(response: any, defaultFilename: string = 'download'): void {
  // 尝试从 Content-Disposition 头获取文件名
  let filename = defaultFilename

  const contentDisposition = response.headers?.['content-disposition']
  if (contentDisposition) {
    const matches = /filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/.exec(contentDisposition)
    if (matches && matches[1]) {
      filename = matches[1].replace(/['"]/g, '')
      // 解码 URL 编码的文件名
      filename = decodeURIComponent(filename)
    }
  }

  // 下载 Blob
  if (response.data instanceof Blob) {
    downloadFile(response.data, filename)
  } else {
    console.error('[Download] Response data is not a Blob')
  }
}

/**
 * 批量下载文件
 * @param files 文件列表 [{ url, filename }]
 * @param delay 下载间隔（毫秒，默认 100ms）
 */
export async function downloadBatch(
  files: Array<{ url: string | Blob; filename: string }>,
  delay: number = 100
): Promise<void> {
  for (const file of files) {
    downloadFile(file.url, file.filename)

    // 延迟以避免浏览器阻止多个下载
    if (delay > 0) {
      await new Promise(resolve => setTimeout(resolve, delay))
    }
  }
}

/**
 * 导出表格数据（自动选择格式）
 * @param data 数据数组
 * @param filename 文件名（不含扩展名）
 * @param format 格式（csv | json | excel，默认 csv）
 * @param headers 表头（可选）
 */
export function exportData(
  data: any[],
  filename: string,
  format: 'csv' | 'json' | 'excel' = 'csv',
  headers?: string[]
): void {
  if (!data || data.length === 0) {
    console.warn('[Export] No data to export')
    return
  }

  switch (format) {
    case 'json':
      downloadJSON(data, `${filename}.json`)
      break

    case 'excel':
      downloadExcel(data, `${filename}.xlsx`, headers)
      break

    case 'csv':
    default:
      downloadCSV(data, `${filename}.csv`, headers)
      break
  }
}

/**
 * 打开文件选择对话框
 * @param accept 接受的文件类型（如 '.csv,.json' 或 'image/*'）
 * @param multiple 是否允许多选
 * @returns Promise<File[]>
 */
export function selectFiles(accept?: string, multiple: boolean = false): Promise<File[]> {
  return new Promise((resolve, reject) => {
    const input = document.createElement('input')
    input.type = 'file'
    input.style.display = 'none'

    if (accept) {
      input.accept = accept
    }

    if (multiple) {
      input.multiple = true
    }

    input.addEventListener('change', () => {
      const files = Array.from(input.files || [])

      if (files.length === 0) {
        reject(new Error('No file selected'))
      } else {
        resolve(files)
      }

      // 清理
      document.body.removeChild(input)
    })

    input.addEventListener('cancel', () => {
      reject(new Error('File selection cancelled'))
      document.body.removeChild(input)
    })

    document.body.appendChild(input)
    input.click()
  })
}

/**
 * 读取文件内容
 * @param file 文件对象
 * @param as 读取方式（text | json | dataURL | arrayBuffer，默认 text）
 * @returns Promise<string | any | ArrayBuffer>
 */
export function readFile(
  file: File,
  as: 'text' | 'json' | 'dataURL' | 'arrayBuffer' = 'text'
): Promise<string | any | ArrayBuffer> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader()

    reader.onload = () => {
      if (as === 'json') {
        try {
          const data = JSON.parse(reader.result as string)
          resolve(data)
        } catch (error) {
          reject(new Error('Failed to parse JSON'))
        }
      } else {
        resolve(reader.result as string | ArrayBuffer)
      }
    }

    reader.onerror = () => {
      reject(new Error('Failed to read file'))
    }

    switch (as) {
      case 'dataURL':
        reader.readAsDataURL(file)
        break

      case 'arrayBuffer':
        reader.readAsArrayBuffer(file)
        break

      case 'json':
      case 'text':
      default:
        reader.readAsText(file)
        break
    }
  })
}

/**
 * 复制文本到剪贴板
 * @param text 文本内容
 * @returns Promise<boolean>
 */
export async function copyToClipboard(text: string): Promise<boolean> {
  try {
    if (navigator.clipboard && navigator.clipboard.writeText) {
      // 现代浏览器
      await navigator.clipboard.writeText(text)
      return true
    } else {
      // 降级方案（旧浏览器）
      const textarea = document.createElement('textarea')
      textarea.value = text
      textarea.style.position = 'fixed'
      textarea.style.top = '0'
      textarea.style.left = '0'
      textarea.style.opacity = '0'

      document.body.appendChild(textarea)
      textarea.focus()
      textarea.select()

      const successful = document.execCommand('copy')
      document.body.removeChild(textarea)

      return successful
    }
  } catch (error) {
    console.error('[Clipboard] Failed to copy text:', error)
    return false
  }
}

/**
 * 从剪贴板读取文本
 * @returns Promise<string>
 */
export async function readFromClipboard(): Promise<string> {
  try {
    if (navigator.clipboard && navigator.clipboard.readText) {
      return await navigator.clipboard.readText()
    } else {
      throw new Error('Clipboard API not supported')
    }
  } catch (error) {
    console.error('[Clipboard] Failed to read text:', error)
    return ''
  }
}
