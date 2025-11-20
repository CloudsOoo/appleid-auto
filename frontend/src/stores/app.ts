import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

/**
 * 主题类型
 */
export type Theme = 'light' | 'dark' | 'auto'

/**
 * 语言类型
 */
export type Language = 'zh-CN' | 'en-US'

/**
 * 应用状态管理 Store
 *
 * 功能：
 * - 侧边栏状态管理（展开/折叠）
 * - 主题管理（亮色/暗色/自动）
 * - 语言管理（中文/英文）
 * - 设备类型检测（移动端/PC端）
 * - 持久化存储（localStorage）
 */
export const useAppStore = defineStore('app', () => {
  // ==================== 状态定义 ====================

  /**
   * 侧边栏是否折叠
   */
  const sidebarCollapsed = ref<boolean>(false)

  /**
   * 主题
   */
  const theme = ref<Theme>('light')

  /**
   * 语言
   */
  const language = ref<Language>('zh-CN')

  /**
   * 是否为移动端
   */
  const isMobile = ref<boolean>(false)

  /**
   * 页面加载状态
   */
  const loading = ref<boolean>(false)

  // ==================== 计算属性 ====================

  /**
   * 实际使用的主题（处理 auto 模式）
   */
  const effectiveTheme = computed(() => {
    if (theme.value === 'auto') {
      // 检测系统主题偏好
      if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
        return 'dark'
      }
      return 'light'
    }
    return theme.value
  })

  /**
   * 是否为暗色主题
   */
  const isDark = computed(() => {
    return effectiveTheme.value === 'dark'
  })

  // ==================== 方法 ====================

  /**
   * 切换侧边栏状态
   */
  function toggleSidebar() {
    sidebarCollapsed.value = !sidebarCollapsed.value
    saveToStorage()
  }

  /**
   * 设置侧边栏状态
   */
  function setSidebarCollapsed(collapsed: boolean) {
    sidebarCollapsed.value = collapsed
    saveToStorage()
  }

  /**
   * 设置主题
   */
  function setTheme(newTheme: Theme) {
    theme.value = newTheme

    // 应用主题到 document
    applyTheme(effectiveTheme.value)

    saveToStorage()
  }

  /**
   * 切换主题（亮色 ↔ 暗色）
   */
  function toggleTheme() {
    const newTheme = isDark.value ? 'light' : 'dark'
    setTheme(newTheme)
  }

  /**
   * 应用主题到 DOM
   */
  function applyTheme(themeValue: 'light' | 'dark') {
    if (themeValue === 'dark') {
      document.documentElement.classList.add('dark')
    } else {
      document.documentElement.classList.remove('dark')
    }
  }

  /**
   * 设置语言
   */
  function setLanguage(newLanguage: Language) {
    language.value = newLanguage

    // TODO: 集成 i18n 后，设置 i18n 语言
    // import { i18n } from '@/i18n'
    // i18n.global.locale.value = newLanguage

    saveToStorage()
  }

  /**
   * 切换语言
   */
  function toggleLanguage() {
    const newLanguage = language.value === 'zh-CN' ? 'en-US' : 'zh-CN'
    setLanguage(newLanguage)
  }

  /**
   * 设置设备类型
   */
  function setMobile(mobile: boolean) {
    isMobile.value = mobile

    // 移动端自动折叠侧边栏
    if (mobile) {
      sidebarCollapsed.value = true
    }
  }

  /**
   * 检测设备类型
   */
  function detectDevice() {
    const width = window.innerWidth
    setMobile(width < 768)  // 768px 以下视为移动端
  }

  /**
   * 设置页面加载状态
   */
  function setLoading(isLoading: boolean) {
    loading.value = isLoading
  }

  /**
   * 保存到 localStorage
   */
  function saveToStorage() {
    const appState = {
      sidebarCollapsed: sidebarCollapsed.value,
      theme: theme.value,
      language: language.value,
    }

    localStorage.setItem('app_state', JSON.stringify(appState))
  }

  /**
   * 从 localStorage 恢复状态
   * 应用初始化时调用
   */
  function restoreFromStorage() {
    const saved = localStorage.getItem('app_state')

    if (saved) {
      try {
        const appState = JSON.parse(saved)

        // 恢复侧边栏状态
        if (typeof appState.sidebarCollapsed === 'boolean') {
          sidebarCollapsed.value = appState.sidebarCollapsed
        }

        // 恢复主题
        if (appState.theme) {
          theme.value = appState.theme
          applyTheme(effectiveTheme.value)
        }

        // 恢复语言
        if (appState.language) {
          language.value = appState.language
        }
      } catch (error) {
        console.error('恢复应用状态失败:', error)
      }
    }

    // 检测设备类型
    detectDevice()

    // 监听窗口大小变化
    window.addEventListener('resize', detectDevice)

    // 监听系统主题变化（如果使用 auto 模式）
    if (window.matchMedia) {
      window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', (e) => {
        if (theme.value === 'auto') {
          applyTheme(e.matches ? 'dark' : 'light')
        }
      })
    }
  }

  /**
   * 重置应用状态
   */
  function reset() {
    sidebarCollapsed.value = false
    theme.value = 'light'
    language.value = 'zh-CN'
    loading.value = false

    // 清除 localStorage
    localStorage.removeItem('app_state')

    // 重新应用主题
    applyTheme('light')
  }

  // ==================== 返回 ====================

  return {
    // 状态
    sidebarCollapsed,
    theme,
    language,
    isMobile,
    loading,

    // 计算属性
    effectiveTheme,
    isDark,

    // 方法
    toggleSidebar,
    setSidebarCollapsed,
    setTheme,
    toggleTheme,
    setLanguage,
    toggleLanguage,
    setMobile,
    detectDevice,
    setLoading,
    restoreFromStorage,
    reset,
  }
})
