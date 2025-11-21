<!--
  空白布局组件

  职责：
  - 提供极简布局，用于认证页面（登录、注册、2FA等）
  - 不包含侧边栏和顶部栏
  - 支持居中内容展示
  - 支持可选的背景图或渐变

  上游依赖：
  - Vue Router（路由视图）
  - Pinia Store（应用状态，主题等）

  下游调用者：
  - 路由配置（登录、注册、2FA页面路由）
-->

<template>
  <div class="blank-layout" :class="[`theme-${appStore.theme}`]">
    <!-- 背景装饰 -->
    <div class="background-decoration">
      <div class="decoration-circle decoration-circle-1"></div>
      <div class="decoration-circle decoration-circle-2"></div>
      <div class="decoration-circle decoration-circle-3"></div>
    </div>

    <!-- 主内容区 -->
    <div class="content-wrapper">
      <!-- Logo（可选） -->
      <div v-if="showLogo" class="logo-section">
        <div class="logo">
          <h1 class="logo-text">Apple ID Auto</h1>
          <p class="logo-subtitle">自动化管理你的 Apple ID 账号</p>
        </div>
      </div>

      <!-- 路由视图 -->
      <div class="content-section">
        <router-view v-slot="{ Component, route }">
          <transition :name="transitionName" mode="out-in">
            <component :is="Component" :key="route.path" />
          </transition>
        </router-view>
      </div>

      <!-- 页脚（可选） -->
      <div v-if="showFooter" class="footer-section">
        <div class="footer-links">
          <a href="#" class="footer-link">帮助中心</a>
          <span class="footer-separator">|</span>
          <a href="#" class="footer-link">服务条款</a>
          <span class="footer-separator">|</span>
          <a href="#" class="footer-link">隐私政策</a>
        </div>
        <p class="copyright">© 2025 Apple ID Auto. All rights reserved.</p>
      </div>
    </div>

    <!-- 主题切换按钮（右上角） -->
    <div class="theme-toggle">
      <el-button
        :icon="appStore.theme === 'dark' ? 'Sunny' : 'Moon'"
        circle
        @click="toggleTheme"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import { useAppStore } from '@/stores/app'
import { ElMessage } from 'element-plus'

/**
 * Props 配置
 */
interface Props {
  showLogo?: boolean      // 是否显示 Logo（默认 true）
  showFooter?: boolean    // 是否显示页脚（默认 true）
  transitionName?: string // 过渡动画名称（默认 fade）
}

const props = withDefaults(defineProps<Props>(), {
  showLogo: true,
  showFooter: true,
  transitionName: 'fade'
})

/**
 * Stores
 */
const appStore = useAppStore()
const route = useRoute()

/**
 * 切换主题
 */
function toggleTheme() {
  const newTheme = appStore.theme === 'light' ? 'dark' : 'light'
  appStore.setTheme(newTheme)
  ElMessage.success(`已切换到${newTheme === 'dark' ? '深色' : '浅色'}模式`)
}
</script>

<style scoped lang="scss">
.blank-layout {
  position: relative;
  width: 100%;
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  overflow: hidden;

  // 深色主题
  &.theme-dark {
    background: linear-gradient(135deg, #1a202c 0%, #2d3748 100%);
  }

  // 背景装饰
  .background-decoration {
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    pointer-events: none;
    overflow: hidden;

    .decoration-circle {
      position: absolute;
      border-radius: 50%;
      background: rgba(255, 255, 255, 0.1);
      backdrop-filter: blur(10px);
      animation: float 20s infinite ease-in-out;

      &.decoration-circle-1 {
        width: 400px;
        height: 400px;
        top: -200px;
        left: -200px;
        animation-delay: 0s;
      }

      &.decoration-circle-2 {
        width: 300px;
        height: 300px;
        bottom: -150px;
        right: -150px;
        animation-delay: 5s;
      }

      &.decoration-circle-3 {
        width: 200px;
        height: 200px;
        top: 50%;
        right: 10%;
        animation-delay: 10s;
      }
    }
  }

  // 主内容区
  .content-wrapper {
    position: relative;
    z-index: 1;
    width: 100%;
    max-width: 500px;
    padding: 20px;
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 30px;

    // Logo 区域
    .logo-section {
      text-align: center;

      .logo {
        .logo-text {
          margin: 0;
          font-size: 32px;
          font-weight: 700;
          color: #ffffff;
          text-shadow: 0 2px 10px rgba(0, 0, 0, 0.2);
          letter-spacing: 1px;
        }

        .logo-subtitle {
          margin: 10px 0 0;
          font-size: 14px;
          color: rgba(255, 255, 255, 0.9);
          font-weight: 400;
        }
      }
    }

    // 内容区域
    .content-section {
      width: 100%;
      background: var(--el-bg-color);
      border-radius: 12px;
      box-shadow: 0 10px 40px rgba(0, 0, 0, 0.2);
      overflow: hidden;
    }

    // 页脚区域
    .footer-section {
      text-align: center;
      color: rgba(255, 255, 255, 0.9);

      .footer-links {
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 10px;
        margin-bottom: 10px;

        .footer-link {
          color: rgba(255, 255, 255, 0.9);
          text-decoration: none;
          font-size: 14px;
          transition: color 0.3s;

          &:hover {
            color: #ffffff;
            text-decoration: underline;
          }
        }

        .footer-separator {
          color: rgba(255, 255, 255, 0.5);
        }
      }

      .copyright {
        margin: 0;
        font-size: 13px;
        color: rgba(255, 255, 255, 0.7);
      }
    }
  }

  // 主题切换按钮
  .theme-toggle {
    position: absolute;
    top: 20px;
    right: 20px;
    z-index: 10;
  }
}

// 浮动动画
@keyframes float {
  0%, 100% {
    transform: translate(0, 0) scale(1);
    opacity: 0.3;
  }
  50% {
    transform: translate(30px, -30px) scale(1.1);
    opacity: 0.5;
  }
}

// 路由过渡动画
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

// 响应式设计
@media (max-width: 768px) {
  .blank-layout {
    .content-wrapper {
      max-width: 100%;
      padding: 15px;
      gap: 20px;

      .logo-section .logo {
        .logo-text {
          font-size: 26px;
        }

        .logo-subtitle {
          font-size: 13px;
        }
      }

      .footer-section {
        .footer-links {
          flex-wrap: wrap;
          font-size: 13px;
        }

        .copyright {
          font-size: 12px;
        }
      }
    }

    .background-decoration {
      .decoration-circle {
        &.decoration-circle-1 {
          width: 250px;
          height: 250px;
          top: -125px;
          left: -125px;
        }

        &.decoration-circle-2 {
          width: 200px;
          height: 200px;
          bottom: -100px;
          right: -100px;
        }

        &.decoration-circle-3 {
          display: none;
        }
      }
    }

    .theme-toggle {
      top: 15px;
      right: 15px;
    }
  }
}

// 小屏幕优化
@media (max-width: 480px) {
  .blank-layout {
    .content-wrapper {
      padding: 10px;

      .content-section {
        border-radius: 8px;
      }

      .footer-section .footer-links {
        flex-direction: column;
        gap: 5px;

        .footer-separator {
          display: none;
        }
      }
    }
  }
}
</style>
