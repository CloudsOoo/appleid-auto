/**
 * Vue 应用入口文件
 *
 * 功能：
 * - 创建 Vue 应用实例
 * - 注册全局插件（Pinia、Vue Router、Element Plus）
 * - 注册全局组件和指令
 * - 挂载应用到 DOM
 */

import { createApp } from 'vue'
import { createPinia } from 'pinia'

// Element Plus
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import zhCn from 'element-plus/es/locale/lang/zh-cn'
import * as ElementPlusIconsVue from '@element-plus/icons-vue'

// 路由
import { setupRouter } from './router'

// 根组件
import App from './App.vue'

// 全局样式
import './styles/index.scss'

/**
 * 创建并配置 Vue 应用
 */
async function bootstrap() {
  // 创建 Vue 应用实例
  const app = createApp(App)

  // 创建 Pinia 状态管理
  const pinia = createPinia()
  app.use(pinia)

  // 配置路由
  setupRouter(app)

  // 配置 Element Plus
  app.use(ElementPlus, {
    locale: zhCn,
    size: 'default',
  })

  // 注册 Element Plus 图标
  for (const [key, component] of Object.entries(ElementPlusIconsVue)) {
    app.component(key, component)
  }

  // 挂载应用
  app.mount('#app')

  console.log('🚀 Apple ID Auto System started successfully!')
}

// 启动应用
bootstrap().catch(err => {
  console.error('Application startup failed:', err)
})
