/**
 * 应用入口文件
 *
 * 职责：
 * - 创建 Vue 应用实例
 * - 注册全局插件（Pinia、Router、Element Plus）
 * - 注册全局组件
 * - 注册全局指令
 * - 挂载应用
 *
 * 上游依赖：
 * - index.html（挂载点）
 *
 * 下游调用：
 * - App.vue（根组件）
 * - Router（路由系统）
 * - Pinia（状态管理）
 * - Element Plus（UI 框架）
 */

import { createApp } from 'vue'
import type { App as VueApp } from 'vue'

// 核心模块
import App from './App.vue'
import router from './router'
import { createPinia } from 'pinia'

// Element Plus
import ElementPlus from 'element-plus'
import zhCn from 'element-plus/es/locale/lang/zh-cn'
import 'element-plus/dist/index.css'
import * as ElementPlusIconsVue from '@element-plus/icons-vue'

// 全局样式
import '@/styles/common.scss'
import '@/styles/theme.scss'

// 全局组件
import PageHeader from '@/components/common/PageHeader.vue'
import DataTable from '@/components/common/DataTable.vue'
import StatusTag from '@/components/common/StatusTag.vue'
import LoadingOverlay from '@/components/common/LoadingOverlay.vue'

// Pinia 持久化插件
import piniaPluginPersistedstate from 'pinia-plugin-persistedstate'

/**
 * 注册全局组件
 */
function registerGlobalComponents(app: VueApp) {
  // 注册自定义全局组件
  app.component('PageHeader', PageHeader)
  app.component('DataTable', DataTable)
  app.component('StatusTag', StatusTag)
  app.component('LoadingOverlay', LoadingOverlay)

  // 注册 Element Plus 图标
  for (const [key, component] of Object.entries(ElementPlusIconsVue)) {
    app.component(key, component)
  }
}

/**
 * 注册全局指令
 */
function registerGlobalDirectives(app: VueApp) {
  // v-permission 权限指令
  app.directive('permission', {
    mounted(el, binding) {
      const { value } = binding
      if (value && !checkPermission(value)) {
        el.parentNode?.removeChild(el)
      }
    }
  })

  // v-loading 加载指令（Element Plus 已提供）

  // v-copy 复制指令
  app.directive('copy', {
    mounted(el, binding) {
      el.addEventListener('click', async () => {
        try {
          await navigator.clipboard.writeText(binding.value)
          // 可以添加复制成功提示
        } catch {
          // 降级方案
          const textarea = document.createElement('textarea')
          textarea.value = binding.value
          textarea.style.position = 'fixed'
          textarea.style.opacity = '0'
          document.body.appendChild(textarea)
          textarea.select()
          document.execCommand('copy')
          document.body.removeChild(textarea)
        }
      })
    }
  })

  // v-debounce 防抖指令
  app.directive('debounce', {
    mounted(el, binding) {
      let timer: ReturnType<typeof setTimeout> | null = null
      const delay = binding.arg ? parseInt(binding.arg) : 300

      el.addEventListener('click', (event: Event) => {
        if (timer) {
          clearTimeout(timer)
        }
        timer = setTimeout(() => {
          binding.value(event)
        }, delay)
      })
    }
  })

  // v-focus 自动聚焦指令
  app.directive('focus', {
    mounted(el) {
      const input = el.querySelector('input') || el
      input.focus()
    }
  })
}

/**
 * 检查权限
 */
function checkPermission(permission: string | string[]): boolean {
  // 从 Pinia store 获取用户权限
  // 这里简化处理，实际应该从 store 获取
  const userPermissions = JSON.parse(
    localStorage.getItem('user-permissions') || '[]'
  )

  if (Array.isArray(permission)) {
    return permission.some((p) => userPermissions.includes(p))
  }
  return userPermissions.includes(permission)
}

/**
 * 全局错误处理
 */
function setupErrorHandler(app: VueApp) {
  // Vue 错误处理
  app.config.errorHandler = (err, instance, info) => {
    console.error('Vue Error:', err)
    console.error('Component:', instance)
    console.error('Info:', info)

    // 可以在这里上报错误到监控系统
    // reportError(err, instance, info)
  }

  // Vue 警告处理（仅开发环境）
  if (import.meta.env.DEV) {
    app.config.warnHandler = (msg, instance, trace) => {
      console.warn('Vue Warning:', msg)
      console.warn('Trace:', trace)
    }
  }

  // 全局未捕获错误
  window.addEventListener('unhandledrejection', (event) => {
    console.error('Unhandled Promise Rejection:', event.reason)
    // reportError(event.reason)
  })

  window.addEventListener('error', (event) => {
    console.error('Global Error:', event.error)
    // reportError(event.error)
  })
}

/**
 * 性能监控（仅开发环境）
 */
function setupPerformanceMonitor() {
  if (import.meta.env.DEV) {
    // 监控页面加载性能
    window.addEventListener('load', () => {
      setTimeout(() => {
        const timing = performance.timing
        const loadTime = timing.loadEventEnd - timing.navigationStart
        const domReady = timing.domContentLoadedEventEnd - timing.navigationStart
        const firstPaint = performance.getEntriesByType('paint')[0]

        console.group('📊 Performance Metrics')
        console.log(`DOM Ready: ${domReady}ms`)
        console.log(`Page Load: ${loadTime}ms`)
        if (firstPaint) {
          console.log(`First Paint: ${firstPaint.startTime.toFixed(2)}ms`)
        }
        console.groupEnd()
      }, 0)
    })
  }
}

/**
 * 初始化应用
 */
async function initApp() {
  // 创建 Vue 应用
  const app = createApp(App)

  // 创建 Pinia 实例
  const pinia = createPinia()
  pinia.use(piniaPluginPersistedstate)

  // 注册插件
  app.use(pinia)
  app.use(router)
  app.use(ElementPlus, {
    locale: zhCn,
    size: 'default',
    zIndex: 3000
  })

  // 注册全局组件
  registerGlobalComponents(app)

  // 注册全局指令
  registerGlobalDirectives(app)

  // 设置错误处理
  setupErrorHandler(app)

  // 设置性能监控
  setupPerformanceMonitor()

  // 等待路由准备就绪
  await router.isReady()

  // 挂载应用
  app.mount('#app')

  // 开发环境日志
  if (import.meta.env.DEV) {
    console.log('🚀 App initialized successfully!')
    console.log('📦 Environment:', import.meta.env.MODE)
    console.log('🔧 Version:', import.meta.env.VITE_APP_VERSION || '1.0.0')
  }
}

// 启动应用
initApp().catch((error) => {
  console.error('Failed to initialize app:', error)
})
