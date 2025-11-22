/**
 * Vue 应用入口文件
 *
 * 功能：
 * - 创建 Vue 应用实例
 * - 注册全局插件（Router、Pinia、Element Plus）
 * - 注册全局组件和指令
 * - 挂载应用到 DOM
 */

import { createApp } from 'vue'
import { createPinia } from 'pinia'

// Element Plus
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import zhCn from 'element-plus/dist/locale/zh-cn.mjs'
import * as ElementPlusIconsVue from '@element-plus/icons-vue'

// 应用核心
import App from './App.vue'
import router from './router'

// 全局样式
import './styles/index.scss'

// 创建应用实例
const app = createApp(App)

// 注册 Pinia 状态管理
const pinia = createPinia()
app.use(pinia)

// 注册 Vue Router
app.use(router)

// 注册 Element Plus
app.use(ElementPlus, {
  locale: zhCn,
  size: 'default',
})

// 注册 Element Plus 图标
for (const [key, component] of Object.entries(ElementPlusIconsVue)) {
  app.component(key, component)
}

// 全局错误处理
app.config.errorHandler = (err, vm, info) => {
  console.error('Vue Error:', err)
  console.error('Error Info:', info)
}

// 挂载应用
app.mount('#app')
