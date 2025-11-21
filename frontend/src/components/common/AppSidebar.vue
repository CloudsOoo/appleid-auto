<!--
  应用侧边栏组件

  职责：
  - 提供侧边栏导航菜单
  - 支持菜单折叠/展开
  - 支持一级和二级菜单（子菜单）
  - 活动菜单项高亮
  - Logo 展示（可折叠）
  - 支持从路由配置自动生成菜单
  - 支持自定义菜单配置

  上游依赖：
  - Pinia Store（appStore - 折叠状态）
  - Vue Router（路由导航、当前路由）
  - Element Plus（el-menu 组件）

  下游调用者：
  - DefaultLayout（用户页面布局）
  - AdminLayout（管理后台布局）
-->

<template>
  <div class="app-sidebar" :class="{ 'is-collapsed': collapsed }">
    <!-- Logo 区域 -->
    <div class="logo-section" :class="{ 'is-collapsed': collapsed }">
      <div class="logo-wrapper" @click="handleLogoClick">
        <!-- Logo 图标 -->
        <div v-if="showLogo" class="logo-icon">
          <img v-if="logoUrl" :src="logoUrl" :alt="logoText" class="logo-image" />
          <span v-else class="logo-text-icon">{{ logoIcon }}</span>
        </div>

        <!-- Logo 文本 -->
        <transition name="logo-fade">
          <h2 v-if="!collapsed && showLogoText" class="logo-text">
            {{ logoText }}
          </h2>
        </transition>
      </div>
    </div>

    <!-- 菜单区域 -->
    <el-scrollbar class="menu-scrollbar">
      <el-menu
        :default-active="activeMenu"
        :collapse="collapsed"
        :collapse-transition="false"
        :unique-opened="uniqueOpened"
        :router="menuRouter"
        class="sidebar-menu"
        @select="handleMenuSelect"
      >
        <!-- 菜单项渲染 -->
        <template v-for="item in menuItems" :key="item.path || item.index">
          <!-- 有子菜单的项（二级菜单） -->
          <el-sub-menu
            v-if="item.children && item.children.length > 0"
            :index="item.path || item.index"
          >
            <template #title>
              <el-icon v-if="item.icon">
                <component :is="item.icon" />
              </el-icon>
              <span>{{ item.title }}</span>
            </template>

            <!-- 子菜单项 -->
            <el-menu-item
              v-for="child in item.children"
              :key="child.path || child.index"
              :index="child.path || child.index"
            >
              <el-icon v-if="child.icon">
                <component :is="child.icon" />
              </el-icon>
              <template #title>{{ child.title }}</template>
            </el-menu-item>
          </el-sub-menu>

          <!-- 分割线 -->
          <el-divider v-else-if="item.type === 'divider'" :key="`divider-${item.index}`" />

          <!-- 无子菜单的项（一级菜单） -->
          <el-menu-item
            v-else
            :index="item.path || item.index"
          >
            <el-icon v-if="item.icon">
              <component :is="item.icon" />
            </el-icon>
            <template #title>{{ item.title }}</template>
          </el-menu-item>
        </template>
      </el-menu>
    </el-scrollbar>

    <!-- 底部插槽（可选） -->
    <div v-if="$slots.footer" class="sidebar-footer">
      <slot name="footer"></slot>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAppStore } from '@/stores/app'

/**
 * 菜单项类型定义
 */
export interface MenuItem {
  path?: string           // 路由路径（使用 router 模式时）
  index?: string          // 菜单索引（不使用 router 模式时）
  title: string           // 菜单标题
  icon?: string           // 图标名称（Element Plus 图标）
  children?: MenuItem[]   // 子菜单
  type?: 'divider'        // 特殊类型（分割线）
}

/**
 * Props 配置
 */
interface Props {
  // Logo 配置
  showLogo?: boolean          // 是否显示 Logo（默认 true）
  showLogoText?: boolean      // 是否显示 Logo 文字（默认 true）
  logoUrl?: string            // Logo 图片 URL（可选）
  logoIcon?: string           // Logo 图标字符（默认取 logoText 首字母）
  logoText?: string           // Logo 文字（默认 "Apple ID Auto"）
  logoClickable?: boolean     // Logo 是否可点击（默认 true）
  logoLink?: string           // Logo 点击跳转链接（默认 /dashboard）

  // 菜单配置
  menuItems?: MenuItem[]      // 菜单项配置（如果不提供，则从路由自动生成）
  collapsed?: boolean         // 是否折叠（默认从 appStore 读取）
  uniqueOpened?: boolean      // 是否只保持一个子菜单展开（默认 true）
  menuRouter?: boolean        // 是否使用路由模式（默认 true）

  // 自定义配置
  defaultActive?: string      // 默认激活的菜单项（默认从当前路由获取）
}

const props = withDefaults(defineProps<Props>(), {
  showLogo: true,
  showLogoText: true,
  logoIcon: '',
  logoText: 'Apple ID Auto',
  logoClickable: true,
  logoLink: '/dashboard',
  menuItems: () => [],
  collapsed: undefined,
  uniqueOpened: true,
  menuRouter: true,
  defaultActive: ''
})

/**
 * Emits
 */
interface Emits {
  (e: 'logo-click'): void
  (e: 'menu-select', index: string, indexPath: string[]): void
}

const emit = defineEmits<Emits>()

/**
 * Stores & Router
 */
const appStore = useAppStore()
const route = useRoute()
const router = useRouter()

/**
 * 折叠状态（优先使用 props，否则从 appStore 读取）
 */
const collapsed = computed(() => {
  return props.collapsed !== undefined ? props.collapsed : appStore.sidebarCollapsed
})

/**
 * Logo 图标（如果没有提供，取 logoText 首字母）
 */
const logoIcon = computed(() => {
  if (props.logoIcon) {
    return props.logoIcon
  }
  return props.logoText.split(' ').map(word => word[0]).join('').toUpperCase()
})

/**
 * 当前激活的菜单项
 */
const activeMenu = computed(() => {
  if (props.defaultActive) {
    return props.defaultActive
  }
  return route.path
})

/**
 * Logo 点击处理
 */
function handleLogoClick() {
  if (!props.logoClickable) {
    return
  }

  emit('logo-click')

  if (props.logoLink && props.menuRouter) {
    router.push(props.logoLink)
  }
}

/**
 * 菜单选择处理
 */
function handleMenuSelect(index: string, indexPath: string[]) {
  emit('menu-select', index, indexPath)
}

/**
 * 监听路由变化，自动滚动到激活的菜单项
 */
watch(
  () => route.path,
  () => {
    // TODO: 实现自动滚动到激活菜单项的逻辑
    // 这里可以使用 Element Plus 的 scrollIntoView 或自定义滚动逻辑
  }
)
</script>

<style scoped lang="scss">
.app-sidebar {
  height: 100%;
  display: flex;
  flex-direction: column;
  background-color: var(--el-menu-bg-color);
  transition: all 0.3s ease;

  // Logo 区域
  .logo-section {
    height: 60px;
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 0 20px;
    border-bottom: 1px solid var(--el-border-color);
    flex-shrink: 0;
    overflow: hidden;
    transition: all 0.3s ease;

    &.is-collapsed {
      padding: 0 10px;
    }

    .logo-wrapper {
      display: flex;
      align-items: center;
      gap: 12px;
      cursor: pointer;
      user-select: none;
      transition: opacity 0.3s;

      &:hover {
        opacity: 0.8;
      }

      .logo-icon {
        flex-shrink: 0;
        width: 32px;
        height: 32px;
        display: flex;
        align-items: center;
        justify-content: center;
        border-radius: 6px;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: #ffffff;

        .logo-image {
          width: 100%;
          height: 100%;
          object-fit: contain;
          border-radius: 6px;
        }

        .logo-text-icon {
          font-size: 18px;
          font-weight: 700;
          letter-spacing: 1px;
        }
      }

      .logo-text {
        margin: 0;
        font-size: 18px;
        font-weight: 600;
        color: var(--el-text-color-primary);
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
      }
    }
  }

  // 菜单滚动区域
  .menu-scrollbar {
    flex: 1;
    overflow: hidden;

    :deep(.el-scrollbar__view) {
      height: 100%;
    }
  }

  // 菜单样式
  .sidebar-menu {
    border-right: none;
    height: 100%;

    // 菜单项间距
    .el-menu-item,
    .el-sub-menu__title {
      height: 50px;
      line-height: 50px;
    }

    // 图标样式
    .el-icon {
      width: 20px;
      height: 20px;
      margin-right: 8px;
      font-size: 18px;
    }

    // 分割线样式
    .el-divider {
      margin: 10px 0;
    }
  }

  // 底部区域
  .sidebar-footer {
    flex-shrink: 0;
    padding: 10px;
    border-top: 1px solid var(--el-border-color);
  }

  // 折叠状态
  &.is-collapsed {
    .logo-section {
      .logo-wrapper {
        justify-content: center;
        gap: 0;
      }
    }
  }
}

// Logo 文字淡入淡出动画
.logo-fade-enter-active,
.logo-fade-leave-active {
  transition: opacity 0.3s ease;
}

.logo-fade-enter-from,
.logo-fade-leave-to {
  opacity: 0;
}

// 响应式设计
@media (max-width: 768px) {
  .app-sidebar {
    .logo-section {
      height: 56px;
      padding: 0 15px;

      &.is-collapsed {
        padding: 0 8px;
      }

      .logo-wrapper {
        .logo-icon {
          width: 28px;
          height: 28px;

          .logo-text-icon {
            font-size: 16px;
          }
        }

        .logo-text {
          font-size: 16px;
        }
      }
    }

    .sidebar-menu {
      .el-menu-item,
      .el-sub-menu__title {
        height: 46px;
        line-height: 46px;
      }
    }
  }
}

// 小屏幕优化
@media (max-width: 480px) {
  .app-sidebar {
    .logo-section {
      height: 52px;
      padding: 0 10px;

      .logo-wrapper {
        .logo-icon {
          width: 24px;
          height: 24px;

          .logo-text-icon {
            font-size: 14px;
          }
        }

        .logo-text {
          font-size: 15px;
        }
      }
    }

    .sidebar-menu {
      .el-menu-item,
      .el-sub-menu__title {
        height: 44px;
        line-height: 44px;
      }
    }
  }
}
</style>
