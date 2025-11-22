<!--
  根组件

  职责：
  - 应用根节点
  - 全局 Layout 配置
  - 主题切换支持
  - 全局消息/通知配置
  - 路由视图挂载

  上游依赖：
  - main.ts（应用入口）
  - router（路由配置）
  - appStore（应用状态）

  下游调用者：
  - 所有页面组件（通过 router-view）
-->

<template>
  <el-config-provider :locale="locale" :size="size" :z-index="zIndex">
    <div
      id="app-container"
      :class="[
        'app-container',
        `theme-${theme}`,
        { 'is-mobile': isMobile }
      ]"
    >
      <!-- 路由视图 -->
      <router-view v-slot="{ Component, route }">
        <transition :name="transitionName" mode="out-in">
          <keep-alive :include="cachedViews">
            <component :is="Component" :key="route.path" />
          </keep-alive>
        </transition>
      </router-view>

      <!-- 全局加载遮罩 -->
      <LoadingOverlay
        v-if="globalLoading"
        :text="loadingText"
        fullscreen
      />

      <!-- 返回顶部按钮 -->
      <el-backtop :right="40" :bottom="40" :visibility-height="200">
        <div class="backtop-btn">
          <el-icon><ArrowUp /></el-icon>
        </div>
      </el-backtop>
    </div>
  </el-config-provider>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'
import { useRoute } from 'vue-router'
import { ElConfigProvider } from 'element-plus'
import zhCn from 'element-plus/es/locale/lang/zh-cn'
import enUs from 'element-plus/es/locale/lang/en'
import { ArrowUp } from '@element-plus/icons-vue'
import { useAppStore } from '@/stores/app'
import LoadingOverlay from '@/components/common/LoadingOverlay.vue'

// Store
const appStore = useAppStore()
const route = useRoute()

// Element Plus 配置
const size = ref<'large' | 'default' | 'small'>('default')
const zIndex = ref(3000)

// 语言配置
const locale = computed(() => {
  return appStore.language === 'zh-CN' ? zhCn : enUs
})

// 主题
const theme = computed(() => appStore.theme)

// 移动端检测
const isMobile = computed(() => appStore.isMobile)

// 全局加载状态
const globalLoading = ref(false)
const loadingText = ref('加载中...')

// 缓存的视图（keep-alive）
const cachedViews = computed(() => {
  // 可以从路由 meta 中获取需要缓存的视图
  const cached: string[] = []
  // 根据需求添加需要缓存的组件名称
  return cached
})

// 页面过渡动画名称
const transitionName = computed(() => {
  // 根据路由深度或配置决定过渡动画
  return route.meta.transition || 'fade'
})

/**
 * 设置主题到 HTML 属性
 */
function updateTheme(newTheme: string) {
  const html = document.documentElement

  if (newTheme === 'auto') {
    // 跟随系统
    const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches
    html.setAttribute('data-theme', prefersDark ? 'dark' : 'light')
  } else {
    html.setAttribute('data-theme', newTheme)
  }
}

/**
 * 检测设备类型
 */
function checkDevice() {
  const width = window.innerWidth
  appStore.setDevice(width < 768 ? 'mobile' : 'desktop')
}

/**
 * 监听系统主题变化
 */
function setupThemeListener() {
  const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)')

  const handleChange = (e: MediaQueryListEvent) => {
    if (appStore.theme === 'auto') {
      document.documentElement.setAttribute(
        'data-theme',
        e.matches ? 'dark' : 'light'
      )
    }
  }

  mediaQuery.addEventListener('change', handleChange)

  // 返回清理函数
  return () => {
    mediaQuery.removeEventListener('change', handleChange)
  }
}

/**
 * 设置页面标题
 */
function updateDocumentTitle() {
  const title = route.meta.title
  if (title) {
    document.title = `${title} - Apple ID 自动解锁系统`
  } else {
    document.title = 'Apple ID 自动解锁系统'
  }
}

// 监听主题变化
watch(() => appStore.theme, (newTheme) => {
  updateTheme(newTheme)
}, { immediate: true })

// 监听路由变化，更新标题
watch(() => route.path, () => {
  updateDocumentTitle()
}, { immediate: true })

// 窗口大小变化监听
let resizeHandler: () => void
let cleanupThemeListener: () => void

onMounted(() => {
  // 检测设备类型
  checkDevice()

  // 监听窗口大小变化
  resizeHandler = () => {
    checkDevice()
  }
  window.addEventListener('resize', resizeHandler)

  // 监听系统主题变化
  cleanupThemeListener = setupThemeListener()

  // 初始化主题
  updateTheme(appStore.theme)
})

onUnmounted(() => {
  if (resizeHandler) {
    window.removeEventListener('resize', resizeHandler)
  }
  if (cleanupThemeListener) {
    cleanupThemeListener()
  }
})

// 暴露全局加载方法
defineExpose({
  showLoading: (text?: string) => {
    loadingText.value = text || '加载中...'
    globalLoading.value = true
  },
  hideLoading: () => {
    globalLoading.value = false
  }
})
</script>

<style lang="scss">
// 应用容器
.app-container {
  min-height: 100vh;
  background-color: var(--bg-page);
  transition: background-color 0.3s ease;
}

// 返回顶部按钮
.backtop-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 40px;
  height: 40px;
  background: var(--color-primary);
  color: #fff;
  border-radius: 50%;
  box-shadow: 0 4px 12px rgba(64, 158, 255, 0.4);
  transition: all 0.3s ease;

  &:hover {
    transform: translateY(-2px);
    box-shadow: 0 6px 16px rgba(64, 158, 255, 0.5);
  }

  .el-icon {
    font-size: 20px;
  }
}

// 页面过渡动画
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

.slide-enter-active,
.slide-leave-active {
  transition: all 0.3s ease;
}

.slide-enter-from {
  opacity: 0;
  transform: translateX(20px);
}

.slide-leave-to {
  opacity: 0;
  transform: translateX(-20px);
}

.zoom-enter-active,
.zoom-leave-active {
  transition: all 0.2s ease;
}

.zoom-enter-from,
.zoom-leave-to {
  opacity: 0;
  transform: scale(0.95);
}

// 移动端适配
.is-mobile {
  // 移动端特定样式
  .el-dialog {
    width: 90% !important;
    margin: 5vh auto !important;
  }

  .el-drawer {
    width: 100% !important;
  }

  .el-message-box {
    width: 90% !important;
  }
}

// 打印样式
@media print {
  .backtop-btn,
  .el-backtop {
    display: none !important;
  }
}
</style>
