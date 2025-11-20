import type { Router } from 'vue-router'
import { ElMessage } from 'element-plus'

/**
 * 路由守卫配置
 *
 * 功能：
 * - 登录验证（requiresAuth）
 * - 权限验证（requiresAdmin）
 * - 页面标题设置
 * - 进度条控制
 */

// TODO: 导入用户状态管理（Pinia store）
// import { useUserStore } from '@/stores/user'

/**
 * 检查用户是否已登录
 * TODO: 实现后需要从 Pinia store 获取登录状态
 */
function isAuthenticated(): boolean {
  // 临时实现：检查 localStorage 中是否有 token
  const tokenKey = import.meta.env.VITE_TOKEN_KEY || 'appleid_access_token'
  const token = localStorage.getItem(tokenKey)
  return !!token

  // 最终实现（需要 Pinia store）：
  // const userStore = useUserStore()
  // return userStore.isLoggedIn
}

/**
 * 检查用户是否为管理员
 * TODO: 实现后需要从 Pinia store 获取用户角色
 */
function isAdmin(): boolean {
  // 临时实现：从 localStorage 获取用户信息
  const userInfo = localStorage.getItem('user_info')
  if (!userInfo) return false

  try {
    const user = JSON.parse(userInfo)
    return user.role === 'admin'
  } catch {
    return false
  }

  // 最终实现（需要 Pinia store）：
  // const userStore = useUserStore()
  // return userStore.user?.role === 'admin'
}

/**
 * 设置页面标题
 */
function setPageTitle(title?: string) {
  const appTitle = import.meta.env.VITE_APP_TITLE || 'Apple ID 自动解锁系统'
  document.title = title ? `${title} - ${appTitle}` : appTitle
}

/**
 * 配置路由守卫
 */
export function setupRouterGuards(router: Router) {
  // 全局前置守卫
  router.beforeEach((to, from, next) => {
    // 1. 启动进度条
    // TODO: 集成 NProgress 或自定义进度条
    // NProgress.start()

    // 2. 检查是否需要登录
    const requiresAuth = to.matched.some(record => record.meta.requiresAuth)

    if (requiresAuth) {
      if (!isAuthenticated()) {
        // 未登录，跳转到登录页
        ElMessage.warning('请先登录')
        next({
          path: '/login',
          query: { redirect: to.fullPath } // 保存目标路由，登录后跳转
        })
        return
      }

      // 3. 检查是否需要管理员权限
      const requiresAdmin = to.matched.some(record => record.meta.requiresAdmin)

      if (requiresAdmin && !isAdmin()) {
        // 不是管理员，跳转到 403 页面
        ElMessage.error('权限不足')
        next('/403')
        return
      }
    }

    // 4. 如果已登录，不允许访问登录/注册页面
    if (isAuthenticated() && (to.path === '/login' || to.path === '/register')) {
      next('/')
      return
    }

    // 5. 设置页面标题
    setPageTitle(to.meta.title as string)

    // 6. 放行
    next()
  })

  // 全局后置守卫
  router.afterEach(() => {
    // 完成进度条
    // TODO: 集成 NProgress 或自定义进度条
    // NProgress.done()
  })

  // 路由错误处理
  router.onError((error) => {
    console.error('路由错误:', error)
    ElMessage.error('页面加载失败，请刷新重试')
  })
}

/**
 * 路由守卫工具函数
 */

/**
 * 获取重定向路径
 * 用于登录后跳转到原目标页面
 */
export function getRedirectPath(route: any): string {
  const { query } = route
  const redirect = query.redirect as string

  // 如果有 redirect 参数且不是登录页，则跳转到该页面
  if (redirect && redirect !== '/login' && redirect !== '/register') {
    return redirect
  }

  // 否则跳转到首页
  return '/'
}

/**
 * 动态添加路由（用于权限路由）
 * TODO: 如果需要动态权限路由，可以在这里实现
 */
export function addDynamicRoutes(router: Router, routes: any[]) {
  routes.forEach(route => {
    router.addRoute(route)
  })
}
