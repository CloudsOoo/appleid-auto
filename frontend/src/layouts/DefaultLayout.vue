<!--
  默认布局组件

  职责：
  - 提供带侧边栏和顶部栏的标准布局
  - 用于用户页面（Dashboard、账号管理等）
  - 支持侧边栏折叠/展开
  - 支持响应式设计（移动端自动收起侧边栏）

  上游依赖：
  - Vue Router（路由视图）
  - Element Plus（布局组件）
  - Pinia Store（应用状态）

  下游调用者：
  - 路由配置（用户页面路由）
-->

<template>
  <el-container class="default-layout">
    <!-- 侧边栏 -->
    <el-aside
      :width="sidebarWidth"
      :class="{ 'is-collapsed': appStore.sidebarCollapsed }"
      class="layout-sidebar"
    >
      <!-- 临时侧边栏内容（待 2.3 任务实现 AppSidebar 组件后替换） -->
      <div class="sidebar-placeholder">
        <div class="logo-section">
          <h2 v-if="!appStore.sidebarCollapsed">Apple ID Auto</h2>
          <h2 v-else>AIA</h2>
        </div>

        <el-menu
          :default-active="activeMenu"
          :collapse="appStore.sidebarCollapsed"
          :collapse-transition="false"
          class="sidebar-menu"
          router
        >
          <!-- 用户菜单 -->
          <el-menu-item index="/dashboard">
            <el-icon><icon-dashboard /></el-icon>
            <template #title>仪表盘</template>
          </el-menu-item>

          <el-menu-item index="/accounts">
            <el-icon><icon-user /></el-icon>
            <template #title>账号管理</template>
          </el-menu-item>

          <el-menu-item index="/tasks">
            <el-icon><icon-list /></el-icon>
            <template #title>任务管理</template>
          </el-menu-item>

          <el-menu-item index="/share-pages">
            <el-icon><icon-share /></el-icon>
            <template #title>分享页管理</template>
          </el-menu-item>
        </el-menu>
      </div>
    </el-aside>

    <!-- 主容器 -->
    <el-container class="main-container">
      <!-- 顶部栏 -->
      <el-header class="layout-header" height="60px">
        <!-- 临时顶部栏内容（待 2.2 任务实现 AppHeader 组件后替换） -->
        <div class="header-placeholder">
          <div class="header-left">
            <!-- 折叠按钮 -->
            <el-button
              :icon="appStore.sidebarCollapsed ? 'Expand' : 'Fold'"
              circle
              @click="toggleSidebar"
            />

            <!-- 面包屑（TODO: 实现面包屑组件） -->
            <el-breadcrumb separator="/">
              <el-breadcrumb-item :to="{ path: '/dashboard' }">首页</el-breadcrumb-item>
              <el-breadcrumb-item>{{ currentPageTitle }}</el-breadcrumb-item>
            </el-breadcrumb>
          </div>

          <div class="header-right">
            <!-- 主题切换 -->
            <el-button
              :icon="appStore.theme === 'dark' ? 'Sunny' : 'Moon'"
              circle
              @click="toggleTheme"
            />

            <!-- 用户信息 -->
            <el-dropdown trigger="click">
              <div class="user-info">
                <el-avatar :size="32">{{ userStore.user?.username?.[0]?.toUpperCase() || 'U' }}</el-avatar>
                <span class="username">{{ userStore.user?.username || '用户' }}</span>
              </div>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item @click="goToProfile">个人中心</el-dropdown-item>
                  <el-dropdown-item @click="goToSettings">设置</el-dropdown-item>
                  <el-dropdown-item divided @click="handleLogout">退出登录</el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
          </div>
        </div>
      </el-header>

      <!-- 主内容区 -->
      <el-main class="layout-main">
        <!-- 路由视图 -->
        <router-view v-slot="{ Component, route }">
          <transition name="fade-transform" mode="out-in">
            <keep-alive :include="cachedViews">
              <component :is="Component" :key="route.path" />
            </keep-alive>
          </transition>
        </router-view>
      </el-main>

      <!-- 页脚（可选） -->
      <el-footer v-if="showFooter" class="layout-footer" height="60px">
        <div class="footer-content">
          <span>© 2025 Apple ID Auto. All rights reserved.</span>
          <span>Version {{ appVersion }}</span>
        </div>
      </el-footer>
    </el-container>
  </el-container>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useUserStore } from '@/stores/user'
import { useAppStore } from '@/stores/app'
import { ElMessage, ElMessageBox } from 'element-plus'

/**
 * 布局配置
 */
const showFooter = ref(false)  // 是否显示页脚（默认隐藏）
const appVersion = ref('1.0.0')  // 应用版本号

/**
 * Stores
 */
const userStore = useUserStore()
const appStore = useAppStore()
const route = useRoute()
const router = useRouter()

/**
 * 侧边栏宽度（根据折叠状态动态计算）
 */
const sidebarWidth = computed(() => {
  return appStore.sidebarCollapsed ? '64px' : '240px'
})

/**
 * 当前激活的菜单项
 */
const activeMenu = computed(() => {
  return route.path
})

/**
 * 当前页面标题（从路由 meta 中获取）
 */
const currentPageTitle = computed(() => {
  return (route.meta?.title as string) || '页面'
})

/**
 * 缓存的视图列表（用于 keep-alive）
 */
const cachedViews = ref<string[]>([])

/**
 * 切换侧边栏折叠状态
 */
function toggleSidebar() {
  appStore.toggleSidebar()
}

/**
 * 切换主题
 */
function toggleTheme() {
  const newTheme = appStore.theme === 'light' ? 'dark' : 'light'
  appStore.setTheme(newTheme)
  ElMessage.success(`已切换到${newTheme === 'dark' ? '深色' : '浅色'}模式`)
}

/**
 * 前往个人中心
 */
function goToProfile() {
  router.push('/profile')
}

/**
 * 前往设置页面
 */
function goToSettings() {
  router.push('/settings')
}

/**
 * 退出登录
 */
async function handleLogout() {
  try {
    await ElMessageBox.confirm('确定要退出登录吗？', '提示', {
      type: 'warning',
      confirmButtonText: '确定',
      cancelButtonText: '取消'
    })

    await userStore.logout()
    ElMessage.success('已退出登录')
    router.push('/login')
  } catch (error) {
    // 用户取消操作
  }
}

/**
 * 监听移动端/PC端切换，自动调整侧边栏
 */
watch(
  () => appStore.isMobile,
  (isMobile) => {
    if (isMobile && !appStore.sidebarCollapsed) {
      appStore.setSidebarCollapsed(true)
    }
  },
  { immediate: true }
)

/**
 * 监听路由变化，更新缓存视图列表
 */
watch(
  () => route.path,
  () => {
    // TODO: 根据路由 meta.keepAlive 配置动态管理缓存视图
    // 这里暂时不实现，待后续优化
  }
)
</script>

<style scoped lang="scss">
.default-layout {
  width: 100%;
  height: 100vh;
  overflow: hidden;
}

.layout-sidebar {
  background-color: var(--el-menu-bg-color);
  border-right: 1px solid var(--el-border-color);
  transition: width 0.3s ease;
  overflow-x: hidden;
  overflow-y: auto;

  &.is-collapsed {
    width: 64px !important;
  }

  .sidebar-placeholder {
    height: 100%;
    display: flex;
    flex-direction: column;

    .logo-section {
      height: 60px;
      display: flex;
      align-items: center;
      justify-content: center;
      padding: 0 20px;
      border-bottom: 1px solid var(--el-border-color);

      h2 {
        margin: 0;
        font-size: 18px;
        font-weight: 600;
        color: var(--el-text-color-primary);
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
      }
    }

    .sidebar-menu {
      flex: 1;
      border-right: none;
    }
  }
}

.main-container {
  flex: 1;
  overflow: hidden;
}

.layout-header {
  background-color: var(--el-bg-color);
  border-bottom: 1px solid var(--el-border-color);
  padding: 0 20px;
  display: flex;
  align-items: center;

  .header-placeholder {
    width: 100%;
    display: flex;
    align-items: center;
    justify-content: space-between;

    .header-left {
      display: flex;
      align-items: center;
      gap: 20px;
    }

    .header-right {
      display: flex;
      align-items: center;
      gap: 15px;

      .user-info {
        display: flex;
        align-items: center;
        gap: 10px;
        cursor: pointer;
        padding: 5px 10px;
        border-radius: 4px;
        transition: background-color 0.3s;

        &:hover {
          background-color: var(--el-fill-color-light);
        }

        .username {
          font-size: 14px;
          color: var(--el-text-color-primary);
        }
      }
    }
  }
}

.layout-main {
  background-color: var(--el-bg-color-page);
  overflow-y: auto;
  padding: 20px;
}

.layout-footer {
  background-color: var(--el-bg-color);
  border-top: 1px solid var(--el-border-color);
  display: flex;
  align-items: center;
  justify-content: center;

  .footer-content {
    display: flex;
    align-items: center;
    justify-content: space-between;
    width: 100%;
    max-width: 1200px;
    font-size: 14px;
    color: var(--el-text-color-secondary);
  }
}

/* 路由过渡动画 */
.fade-transform-enter-active,
.fade-transform-leave-active {
  transition: all 0.3s;
}

.fade-transform-enter-from {
  opacity: 0;
  transform: translateX(-20px);
}

.fade-transform-leave-to {
  opacity: 0;
  transform: translateX(20px);
}

/* 响应式设计 */
@media (max-width: 768px) {
  .layout-header .header-left {
    gap: 10px;

    .el-breadcrumb {
      display: none;
    }
  }

  .layout-main {
    padding: 10px;
  }

  .layout-footer .footer-content {
    flex-direction: column;
    gap: 5px;
  }
}
</style>
