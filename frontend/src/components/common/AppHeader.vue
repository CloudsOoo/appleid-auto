<!--
  应用顶部导航栏组件

  职责：
  - 提供顶部导航栏通用功能
  - 支持侧边栏折叠控制
  - 提供面包屑导航
  - 提供主题切换、全屏切换
  - 提供用户信息下拉菜单
  - 支持通知消息展示
  - 支持管理员特定功能（系统状态、管理员标识）

  上游依赖：
  - Pinia Store（userStore、appStore）
  - Vue Router（面包屑导航）
  - Element Plus（UI 组件）

  下游调用者：
  - DefaultLayout（用户页面布局）
  - AdminLayout（管理后台布局）
-->

<template>
  <div class="app-header">
    <!-- 左侧区域 -->
    <div class="header-left">
      <!-- 折叠按钮 -->
      <el-button
        v-if="showCollapseButton"
        :icon="appStore.sidebarCollapsed ? 'Expand' : 'Fold'"
        circle
        @click="handleToggleSidebar"
      />

      <!-- 面包屑 -->
      <el-breadcrumb v-if="showBreadcrumb" separator="/" class="header-breadcrumb">
        <el-breadcrumb-item
          v-for="(item, index) in breadcrumbItems"
          :key="index"
          :to="item.path ? { path: item.path } : undefined"
        >
          {{ item.title }}
        </el-breadcrumb-item>
      </el-breadcrumb>

      <!-- 管理员标识 -->
      <el-tag v-if="showAdminBadge" type="danger" size="small" effect="dark">
        管理员
      </el-tag>

      <!-- 自定义左侧插槽 -->
      <slot name="left"></slot>
    </div>

    <!-- 右侧区域 -->
    <div class="header-right">
      <!-- 系统状态 -->
      <div v-if="showSystemStatus" class="system-status">
        <el-tooltip :content="systemStatusText" placement="bottom">
          <el-badge :value="systemErrorCount" :max="99" class="status-badge">
            <el-icon
              :size="20"
              :color="systemStatusColor"
              style="cursor: pointer;"
              @click="handleSystemStatusClick"
            >
              <component :is="systemStatusIcon" />
            </el-icon>
          </el-badge>
        </el-tooltip>
      </div>

      <!-- 通知消息 -->
      <el-badge
        v-if="showNotification"
        :value="notificationCount"
        :max="99"
        :hidden="notificationCount === 0"
        class="notification-badge"
      >
        <el-button
          icon="Bell"
          circle
          @click="handleShowNotifications"
        />
      </el-badge>

      <!-- 全屏切换 -->
      <el-tooltip
        v-if="showFullscreen"
        :content="isFullscreen ? '退出全屏' : '全屏'"
        placement="bottom"
      >
        <el-button
          :icon="isFullscreen ? 'Aim' : 'FullScreen'"
          circle
          @click="handleToggleFullscreen"
        />
      </el-tooltip>

      <!-- 主题切换 -->
      <el-tooltip
        v-if="showThemeToggle"
        :content="`切换到${appStore.theme === 'dark' ? '浅色' : '深色'}模式`"
        placement="bottom"
      >
        <el-button
          :icon="appStore.theme === 'dark' ? 'Sunny' : 'Moon'"
          circle
          @click="handleToggleTheme"
        />
      </el-tooltip>

      <!-- 自定义右侧插槽 -->
      <slot name="right"></slot>

      <!-- 用户信息下拉菜单 -->
      <el-dropdown v-if="showUserDropdown" trigger="click" @command="handleUserCommand">
        <div class="user-info">
          <el-avatar :size="32" :style="{ backgroundColor: avatarColor }">
            {{ userInitial }}
          </el-avatar>
          <span class="username">{{ userName }}</span>
        </div>
        <template #dropdown>
          <el-dropdown-menu>
            <el-dropdown-item command="profile">
              <el-icon><icon-user /></el-icon>
              个人中心
            </el-dropdown-item>
            <el-dropdown-item command="settings">
              <el-icon><icon-setting /></el-icon>
              设置
            </el-dropdown-item>
            <el-dropdown-item divided command="logout">
              <el-icon><icon-switch-button /></el-icon>
              退出登录
            </el-dropdown-item>
          </el-dropdown-menu>
        </template>
      </el-dropdown>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, onMounted, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useUserStore } from '@/stores/user'
import { useAppStore } from '@/stores/app'
import { ElMessage, ElMessageBox } from 'element-plus'

/**
 * Props 配置
 */
interface Props {
  // 基础功能
  showCollapseButton?: boolean      // 是否显示折叠按钮（默认 true）
  showBreadcrumb?: boolean          // 是否显示面包屑（默认 true）
  showThemeToggle?: boolean         // 是否显示主题切换（默认 true）
  showFullscreen?: boolean          // 是否显示全屏切换（默认 true）
  showUserDropdown?: boolean        // 是否显示用户下拉菜单（默认 true）

  // 管理员功能
  showAdminBadge?: boolean          // 是否显示管理员标识（默认 false）
  showSystemStatus?: boolean        // 是否显示系统状态（默认 false）
  showNotification?: boolean        // 是否显示通知消息（默认 false）

  // 自定义配置
  breadcrumbHome?: string           // 面包屑首页路径（默认 /dashboard）
  breadcrumbHomeTitle?: string      // 面包屑首页标题（默认 首页）
  avatarColor?: string              // 用户头像背景色（默认自动）
  notificationCount?: number        // 通知数量（默认 0）
  systemErrorCount?: number         // 系统错误数量（默认 0）
}

const props = withDefaults(defineProps<Props>(), {
  showCollapseButton: true,
  showBreadcrumb: true,
  showThemeToggle: true,
  showFullscreen: true,
  showUserDropdown: true,
  showAdminBadge: false,
  showSystemStatus: false,
  showNotification: false,
  breadcrumbHome: '/dashboard',
  breadcrumbHomeTitle: '首页',
  avatarColor: '',
  notificationCount: 0,
  systemErrorCount: 0
})

/**
 * Emits
 */
interface Emits {
  (e: 'toggle-sidebar'): void
  (e: 'show-notifications'): void
  (e: 'system-status-click'): void
}

const emit = defineEmits<Emits>()

/**
 * Stores & Router
 */
const userStore = useUserStore()
const appStore = useAppStore()
const route = useRoute()
const router = useRouter()

/**
 * 全屏状态
 */
const isFullscreen = ref(false)

/**
 * 面包屑项目
 */
const breadcrumbItems = computed(() => {
  const items: Array<{ title: string; path?: string }> = []

  // 添加首页
  items.push({
    title: props.breadcrumbHomeTitle,
    path: props.breadcrumbHome
  })

  // 添加当前页面
  const currentPageTitle = (route.meta?.title as string) || '页面'
  items.push({
    title: currentPageTitle
  })

  return items
})

/**
 * 用户信息
 */
const userName = computed(() => {
  return userStore.user?.username || '用户'
})

const userInitial = computed(() => {
  return userName.value[0]?.toUpperCase() || 'U'
})

const avatarColor = computed(() => {
  if (props.avatarColor) {
    return props.avatarColor
  }

  // 根据用户角色自动选择颜色
  if (userStore.user?.role === 'admin') {
    return '#f56c6c'
  }

  return '#409eff'
})

/**
 * 系统状态
 */
const systemStatusIcon = computed(() => {
  return props.systemErrorCount > 0 ? 'WarningFilled' : 'SuccessFilled'
})

const systemStatusColor = computed(() => {
  return props.systemErrorCount > 0 ? '#f56c6c' : '#67c23a'
})

const systemStatusText = computed(() => {
  return props.systemErrorCount > 0
    ? `系统异常（${props.systemErrorCount}）`
    : '系统运行正常'
})

/**
 * 切换侧边栏
 */
function handleToggleSidebar() {
  appStore.toggleSidebar()
  emit('toggle-sidebar')
}

/**
 * 切换主题
 */
function handleToggleTheme() {
  const newTheme = appStore.theme === 'light' ? 'dark' : 'light'
  appStore.setTheme(newTheme)
  ElMessage.success(`已切换到${newTheme === 'dark' ? '深色' : '浅色'}模式`)
}

/**
 * 切换全屏
 */
function handleToggleFullscreen() {
  if (!document.fullscreenElement) {
    // 进入全屏
    document.documentElement.requestFullscreen().then(() => {
      isFullscreen.value = true
      ElMessage.success('已进入全屏模式')
    }).catch((err) => {
      ElMessage.error('无法进入全屏模式')
      console.error('[Fullscreen] Failed to enter fullscreen:', err)
    })
  } else {
    // 退出全屏
    document.exitFullscreen().then(() => {
      isFullscreen.value = false
      ElMessage.success('已退出全屏模式')
    }).catch((err) => {
      ElMessage.error('无法退出全屏模式')
      console.error('[Fullscreen] Failed to exit fullscreen:', err)
    })
  }
}

/**
 * 监听全屏状态变化
 */
function handleFullscreenChange() {
  isFullscreen.value = !!document.fullscreenElement
}

/**
 * 显示通知列表
 */
function handleShowNotifications() {
  emit('show-notifications')
}

/**
 * 系统状态点击
 */
function handleSystemStatusClick() {
  emit('system-status-click')
}

/**
 * 用户下拉菜单命令处理
 */
async function handleUserCommand(command: string) {
  switch (command) {
    case 'profile':
      router.push('/profile')
      break

    case 'settings':
      // 根据用户角色跳转到不同的设置页面
      if (userStore.user?.role === 'admin') {
        router.push('/admin/settings')
      } else {
        router.push('/settings')
      }
      break

    case 'logout':
      await handleLogout()
      break

    default:
      console.warn('[AppHeader] Unknown command:', command)
  }
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
    // 用户取消操作或退出失败
    if (error !== 'cancel') {
      console.error('[AppHeader] Logout failed:', error)
    }
  }
}

/**
 * 生命周期
 */
onMounted(() => {
  // 监听全屏状态变化
  document.addEventListener('fullscreenchange', handleFullscreenChange)

  // 初始化全屏状态
  isFullscreen.value = !!document.fullscreenElement
})

onUnmounted(() => {
  // 移除全屏状态监听
  document.removeEventListener('fullscreenchange', handleFullscreenChange)
})
</script>

<style scoped lang="scss">
.app-header {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 20px;
  background-color: var(--el-bg-color);

  .header-left {
    display: flex;
    align-items: center;
    gap: 20px;
    flex: 1;

    .header-breadcrumb {
      flex: 1;
      max-width: 600px;
    }
  }

  .header-right {
    display: flex;
    align-items: center;
    gap: 15px;

    .system-status {
      display: flex;
      align-items: center;

      .status-badge {
        cursor: pointer;
      }
    }

    .notification-badge {
      display: flex;
      align-items: center;
    }

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
        white-space: nowrap;
      }
    }
  }
}

// 响应式设计
@media (max-width: 768px) {
  .app-header {
    padding: 0 10px;

    .header-left {
      gap: 10px;

      .header-breadcrumb {
        display: none;
      }

      .el-tag {
        display: none;
      }
    }

    .header-right {
      gap: 10px;

      .system-status {
        display: none;
      }

      .user-info {
        padding: 5px;

        .username {
          display: none;
        }
      }
    }
  }
}

// 小屏幕优化
@media (max-width: 480px) {
  .app-header {
    padding: 0 5px;

    .header-left {
      gap: 5px;
    }

    .header-right {
      gap: 5px;
    }
  }
}
</style>
