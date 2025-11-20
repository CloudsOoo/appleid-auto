import { createRouter, createWebHistory } from 'vue-router'
import type { App } from 'vue'
import routes from './routes'
import { setupRouterGuards } from './guards'

/**
 * 创建 Vue Router 实例
 *
 * 功能：
 * - 路由懒加载（所有页面组件按需加载）
 * - HTML5 History 模式
 * - 路由守卫（登录验证、权限控制）
 * - 页面标题动态设置
 * - 路由过渡动画支持
 */

const router = createRouter({
  // 使用 HTML5 History 模式
  // 生产环境需要服务器配置支持（Nginx、Apache 等）
  history: createWebHistory(import.meta.env.BASE_URL),

  // 路由配置
  routes,

  // 路由切换时滚动到顶部
  scrollBehavior(to, from, savedPosition) {
    // 如果有保存的位置（浏览器前进/后退），则恢复
    if (savedPosition) {
      return savedPosition
    }

    // 如果有锚点，则滚动到锚点
    if (to.hash) {
      return {
        el: to.hash,
        behavior: 'smooth',
      }
    }

    // 默认滚动到顶部
    return { top: 0 }
  },
})

/**
 * 配置路由守卫
 */
setupRouterGuards(router)

/**
 * 安装路由到 Vue 应用
 */
export function setupRouter(app: App) {
  app.use(router)
}

/**
 * 获取路由菜单（用于侧边栏渲染）
 * 过滤掉 hidden: true 的路由
 */
export function getRouteMenus(role: 'user' | 'admin' = 'user') {
  const targetRoutes = routes.filter(route => {
    // 用户路由：path === '/'
    // 管理后台路由：path === '/admin'
    if (role === 'user') {
      return route.path === '/'
    } else {
      return route.path === '/admin'
    }
  })

  if (targetRoutes.length === 0) return []

  const targetRoute = targetRoutes[0]
  if (!targetRoute.children) return []

  // 过滤掉 hidden: true 的路由
  return targetRoute.children
    .filter(child => !child.meta?.hidden)
    .map(child => ({
      path: child.path,
      name: child.name,
      title: child.meta?.title,
      icon: child.meta?.icon,
      meta: child.meta,
    }))
}

/**
 * 重置路由（用于退出登录）
 */
export function resetRouter() {
  // 重新创建路由实例
  const newRouter = createRouter({
    history: createWebHistory(import.meta.env.BASE_URL),
    routes,
  })

  // @ts-ignore
  router.matcher = newRouter.matcher
}

export default router
