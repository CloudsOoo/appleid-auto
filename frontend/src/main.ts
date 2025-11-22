import { createApp } from 'vue'
import ElementPlus from 'element-plus'
import * as ElementPlusIconsVue from '@element-plus/icons-vue'
import 'element-plus/dist/index.css'

import App from './App.vue'
import { setupStore } from './stores'
import { setupRouter } from './router'

/**
 * 创建并配置 Vue 应用
 */
async function bootstrap() {
  // 创建 Vue 应用实例
  const app = createApp(App)

  // 注册 Element Plus
  app.use(ElementPlus)

  // 注册 Element Plus 图标
  for (const [key, component] of Object.entries(ElementPlusIconsVue)) {
    app.component(key, component)
  }

  // 安装 Pinia 状态管理
  setupStore(app)

  // 安装路由
  setupRouter(app)

  // 挂载应用
  app.mount('#app')
}

bootstrap()
