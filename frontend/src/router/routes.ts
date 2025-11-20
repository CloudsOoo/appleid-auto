import type { RouteRecordRaw } from 'vue-router'

/**
 * 路由配置文件
 *
 * 说明：
 * - meta.requiresAuth: 是否需要登录
 * - meta.requiresAdmin: 是否需要管理员权限
 * - meta.title: 页面标题
 * - meta.keepAlive: 是否缓存页面
 * - meta.icon: 菜单图标（用于侧边栏）
 * - meta.hidden: 是否在菜单中隐藏
 */

const routes: RouteRecordRaw[] = [
  // ==================== 公开路由 ====================
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/pages/auth/LoginView.vue'),
    meta: {
      title: '登录',
      requiresAuth: false,
      hidden: true,
    }
  },
  {
    path: '/register',
    name: 'Register',
    component: () => import('@/pages/auth/RegisterView.vue'),
    meta: {
      title: '注册',
      requiresAuth: false,
      hidden: true,
    }
  },
  {
    path: '/2fa',
    name: 'TwoFactor',
    component: () => import('@/pages/auth/TwoFactorView.vue'),
    meta: {
      title: '双因素认证',
      requiresAuth: false,
      hidden: true,
    }
  },

  // 分享页访问（公开）
  {
    path: '/share/:slug',
    name: 'SharePage',
    component: () => import('@/pages/public/ShareView.vue'),
    meta: {
      title: '分享页',
      requiresAuth: false,
      hidden: true,
    }
  },

  // ==================== 用户路由 ====================
  {
    path: '/',
    component: () => import('@/layouts/DefaultLayout.vue'),
    redirect: '/dashboard',
    meta: {
      requiresAuth: true,
    },
    children: [
      // 用户仪表盘
      {
        path: '/dashboard',
        name: 'Dashboard',
        component: () => import('@/pages/user/DashboardView.vue'),
        meta: {
          title: '仪表盘',
          icon: 'Dashboard',
          requiresAuth: true,
        }
      },

      // Apple ID 管理
      {
        path: '/accounts',
        name: 'AccountList',
        component: () => import('@/pages/user/AccountListView.vue'),
        meta: {
          title: 'Apple ID 管理',
          icon: 'User',
          requiresAuth: true,
          keepAlive: true,
        }
      },
      {
        path: '/accounts/create',
        name: 'AccountCreate',
        component: () => import('@/pages/user/AccountFormView.vue'),
        meta: {
          title: '添加账号',
          requiresAuth: true,
          hidden: true,
        }
      },
      {
        path: '/accounts/:id/edit',
        name: 'AccountEdit',
        component: () => import('@/pages/user/AccountFormView.vue'),
        meta: {
          title: '编辑账号',
          requiresAuth: true,
          hidden: true,
        }
      },
      {
        path: '/accounts/import',
        name: 'AccountImport',
        component: () => import('@/pages/user/AccountImportView.vue'),
        meta: {
          title: '批量导入',
          requiresAuth: true,
          hidden: true,
        }
      },

      // 任务管理
      {
        path: '/tasks',
        name: 'TaskList',
        component: () => import('@/pages/user/TaskListView.vue'),
        meta: {
          title: '任务管理',
          icon: 'List',
          requiresAuth: true,
          keepAlive: true,
        }
      },
      {
        path: '/tasks/:id',
        name: 'TaskDetail',
        component: () => import('@/pages/user/TaskDetailView.vue'),
        meta: {
          title: '任务详情',
          requiresAuth: true,
          hidden: true,
        }
      },

      // 分享页管理
      {
        path: '/share-pages',
        name: 'SharePageList',
        component: () => import('@/pages/user/SharePageListView.vue'),
        meta: {
          title: '分享页管理',
          icon: 'Share',
          requiresAuth: true,
          keepAlive: true,
        }
      },
      {
        path: '/share-pages/create',
        name: 'SharePageCreate',
        component: () => import('@/pages/user/SharePageFormView.vue'),
        meta: {
          title: '创建分享页',
          requiresAuth: true,
          hidden: true,
        }
      },
      {
        path: '/share-pages/:id/edit',
        name: 'SharePageEdit',
        component: () => import('@/pages/user/SharePageFormView.vue'),
        meta: {
          title: '编辑分享页',
          requiresAuth: true,
          hidden: true,
        }
      },

      // 代理池管理
      {
        path: '/proxies',
        name: 'ProxyList',
        component: () => import('@/pages/user/ProxyListView.vue'),
        meta: {
          title: '代理池管理',
          icon: 'Connection',
          requiresAuth: true,
          keepAlive: true,
        }
      },

      // 节点管理
      {
        path: '/nodes',
        name: 'NodeList',
        component: () => import('@/pages/user/NodeListView.vue'),
        meta: {
          title: '节点管理',
          icon: 'Monitor',
          requiresAuth: true,
          keepAlive: true,
        }
      },

      // 卡密激活
      {
        path: '/activate',
        name: 'CardActivate',
        component: () => import('@/pages/user/CardActivateView.vue'),
        meta: {
          title: '卡密激活',
          icon: 'Key',
          requiresAuth: true,
        }
      },

      // 用户设置
      {
        path: '/settings',
        name: 'Settings',
        component: () => import('@/pages/user/SettingsView.vue'),
        meta: {
          title: '用户设置',
          icon: 'Setting',
          requiresAuth: true,
        }
      },
    ]
  },

  // ==================== 管理后台路由 ====================
  {
    path: '/admin',
    component: () => import('@/layouts/AdminLayout.vue'),
    redirect: '/admin/dashboard',
    meta: {
      requiresAuth: true,
      requiresAdmin: true,
    },
    children: [
      // 管理员仪表盘
      {
        path: '/admin/dashboard',
        name: 'AdminDashboard',
        component: () => import('@/pages/admin/DashboardView.vue'),
        meta: {
          title: '管理员面板',
          icon: 'DataBoard',
          requiresAuth: true,
          requiresAdmin: true,
        }
      },

      // 用户管理
      {
        path: '/admin/users',
        name: 'UserManagement',
        component: () => import('@/pages/admin/UserListView.vue'),
        meta: {
          title: '用户管理',
          icon: 'User',
          requiresAuth: true,
          requiresAdmin: true,
        }
      },

      // 卡密管理
      {
        path: '/admin/cards',
        name: 'CardManagement',
        component: () => import('@/pages/admin/CardListView.vue'),
        meta: {
          title: '卡密管理',
          icon: 'Tickets',
          requiresAuth: true,
          requiresAdmin: true,
        }
      },
      {
        path: '/admin/cards/generate',
        name: 'CardGenerate',
        component: () => import('@/pages/admin/CardGenerateView.vue'),
        meta: {
          title: '生成卡密',
          requiresAuth: true,
          requiresAdmin: true,
          hidden: true,
        }
      },

      // 套餐管理
      {
        path: '/admin/packages',
        name: 'PackageManagement',
        component: () => import('@/pages/admin/PackageListView.vue'),
        meta: {
          title: '套餐管理',
          icon: 'Box',
          requiresAuth: true,
          requiresAdmin: true,
        }
      },

      // 统计分析
      {
        path: '/admin/stats',
        name: 'Statistics',
        component: () => import('@/pages/admin/StatsView.vue'),
        meta: {
          title: '统计分析',
          icon: 'DataAnalysis',
          requiresAuth: true,
          requiresAdmin: true,
        }
      },
    ]
  },

  // ==================== 错误页面 ====================
  {
    path: '/403',
    name: 'Forbidden',
    component: () => import('@/pages/error/403.vue'),
    meta: {
      title: '无权限',
      requiresAuth: false,
      hidden: true,
    }
  },
  {
    path: '/404',
    name: 'NotFound',
    component: () => import('@/pages/error/404.vue'),
    meta: {
      title: '页面不存在',
      requiresAuth: false,
      hidden: true,
    }
  },
  {
    path: '/:pathMatch(.*)*',
    redirect: '/404',
    meta: {
      hidden: true,
    }
  },
]

export default routes
