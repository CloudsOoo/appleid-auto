import axios, { AxiosInstance, AxiosRequestConfig, AxiosResponse, AxiosError } from 'axios'
import { ElMessage } from 'element-plus'
import { useUserStore } from '@/stores/user'
import { getToken, isTokenExpired } from './auth'

/**
 * Axios 请求实例封装
 *
 * 功能：
 * - 请求拦截（自动添加 Token）
 * - 响应拦截（统一错误处理）
 * - Token 自动刷新
 * - 请求重复取消
 * - 超时设置
 */

/**
 * 创建 Axios 实例
 */
const service: AxiosInstance = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000',
  timeout: 30000, // 30 秒超时
  headers: {
    'Content-Type': 'application/json',
  },
})

/**
 * 正在刷新 Token 的标志
 */
let isRefreshing = false

/**
 * 等待 Token 刷新的请求队列
 */
let refreshSubscribers: ((token: string) => void)[] = []

/**
 * 添加请求到刷新队列
 */
function addRefreshSubscriber(callback: (token: string) => void) {
  refreshSubscribers.push(callback)
}

/**
 * 执行刷新队列中的所有请求
 */
function onTokenRefreshed(token: string) {
  refreshSubscribers.forEach(callback => callback(token))
  refreshSubscribers = []
}

/**
 * 请求拦截器
 */
service.interceptors.request.use(
  (config: any) => {
    // 1. 添加 Token
    const token = getToken()
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }

    // 2. 添加 API 路径前缀（如果需要）
    const apiPrefix = import.meta.env.VITE_API_PREFIX || '/api/v1'
    if (config.url && !config.url.startsWith('http')) {
      // 如果 URL 不以 / 开头，添加 /
      const url = config.url.startsWith('/') ? config.url : `/${config.url}`
      // 添加前缀
      config.url = `${apiPrefix}${url}`
    }

    // 3. 处理 GET 请求参数（移除空值）
    if (config.method === 'get' && config.params) {
      const params: any = {}
      Object.keys(config.params).forEach(key => {
        const value = config.params[key]
        if (value !== null && value !== undefined && value !== '') {
          params[key] = value
        }
      })
      config.params = params
    }

    return config
  },
  (error: AxiosError) => {
    console.error('请求错误:', error)
    return Promise.reject(error)
  }
)

/**
 * 响应拦截器
 */
service.interceptors.response.use(
  (response: AxiosResponse) => {
    // 直接返回 data
    return response.data
  },
  async (error: AxiosError) => {
    const { response, config } = error

    // 1. 网络错误
    if (!response) {
      ElMessage.error('网络连接失败，请检查网络设置')
      return Promise.reject(error)
    }

    const { status, data } = response as any

    // 2. Token 过期或无效（401）
    if (status === 401) {
      const originalRequest = config as any

      // 如果是刷新 Token 的请求失败，则清除登录状态
      if (originalRequest.url?.includes('/auth/refresh')) {
        ElMessage.error('登录已过期，请重新登录')
        const userStore = useUserStore()
        await userStore.logout()
        // 跳转到登录页
        window.location.href = '/login'
        return Promise.reject(error)
      }

      // 如果正在刷新 Token，将请求加入队列
      if (isRefreshing) {
        return new Promise(resolve => {
          addRefreshSubscriber((token: string) => {
            originalRequest.headers.Authorization = `Bearer ${token}`
            resolve(service(originalRequest))
          })
        })
      }

      // 开始刷新 Token
      isRefreshing = true

      try {
        const userStore = useUserStore()
        const success = await userStore.refreshAccessToken()

        if (success) {
          const newToken = userStore.token

          // 更新原请求的 Token
          originalRequest.headers.Authorization = `Bearer ${newToken}`

          // 执行队列中的请求
          onTokenRefreshed(newToken)

          // 重新发起原请求
          return service(originalRequest)
        } else {
          // 刷新失败，清除登录状态
          ElMessage.error('登录已过期，请重新登录')
          await userStore.logout()
          window.location.href = '/login'
          return Promise.reject(error)
        }
      } catch (refreshError) {
        console.error('刷新 Token 失败:', refreshError)
        const userStore = useUserStore()
        await userStore.logout()
        window.location.href = '/login'
        return Promise.reject(refreshError)
      } finally {
        isRefreshing = false
      }
    }

    // 3. 权限不足（403）
    if (status === 403) {
      ElMessage.error(data?.message || '权限不足')
      return Promise.reject(error)
    }

    // 4. 资源不存在（404）
    if (status === 404) {
      ElMessage.error(data?.message || '请求的资源不存在')
      return Promise.reject(error)
    }

    // 5. 请求参数错误（400、422）
    if (status === 400 || status === 422) {
      const message = data?.message || '请求参数错误'
      ElMessage.error(message)
      return Promise.reject(error)
    }

    // 6. 请求过多（429）
    if (status === 429) {
      ElMessage.error('请求过于频繁，请稍后再试')
      return Promise.reject(error)
    }

    // 7. 服务器错误（500+）
    if (status >= 500) {
      ElMessage.error(data?.message || '服务器错误，请稍后再试')
      return Promise.reject(error)
    }

    // 8. 其他错误
    ElMessage.error(data?.message || '请求失败')
    return Promise.reject(error)
  }
)

/**
 * 导出 Axios 实例
 */
export default service

/**
 * GET 请求封装
 */
export function get<T = any>(url: string, params?: any, config?: AxiosRequestConfig): Promise<T> {
  return service.get(url, { params, ...config })
}

/**
 * POST 请求封装
 */
export function post<T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<T> {
  return service.post(url, data, config)
}

/**
 * PUT 请求封装
 */
export function put<T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<T> {
  return service.put(url, data, config)
}

/**
 * DELETE 请求封装
 */
export function del<T = any>(url: string, config?: AxiosRequestConfig): Promise<T> {
  return service.delete(url, config)
}

/**
 * PATCH 请求封装
 */
export function patch<T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<T> {
  return service.patch(url, data, config)
}

/**
 * 文件上传封装
 */
export function upload<T = any>(url: string, formData: FormData, onProgress?: (progress: number) => void): Promise<T> {
  return service.post(url, formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
    onUploadProgress: (progressEvent) => {
      if (onProgress && progressEvent.total) {
        const progress = Math.round((progressEvent.loaded * 100) / progressEvent.total)
        onProgress(progress)
      }
    },
  })
}

/**
 * 文件下载封装
 */
export function download(url: string, filename?: string, params?: any): Promise<void> {
  return service
    .get(url, {
      params,
      responseType: 'blob',
    })
    .then((data: any) => {
      const blob = new Blob([data])
      const downloadUrl = window.URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = downloadUrl
      link.download = filename || 'download'
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
      window.URL.revokeObjectURL(downloadUrl)
    })
}
