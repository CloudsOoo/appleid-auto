<!--
  加载遮罩组件

  职责：
  - 提供全局/局部加载遮罩
  - 支持自定义加载文本
  - 支持自定义加载图标
  - 支持背景模糊效果
  - 支持全屏模式
  - 支持固定定位和绝对定位

  上游依赖：
  - Element Plus（el-loading）
  - Element Plus Icons

  下游调用者：
  - 所有需要显示加载状态的页面/组件
  - FormDialog（提交时显示加载）
  - DataTable（加载数据时显示）
  - 异步操作场景
-->

<template>
  <Transition name="loading-fade">
    <div
      v-show="visible"
      class="loading-overlay"
      :class="{
        'is-fullscreen': fullscreen,
        'is-blur': blur,
        'is-absolute': !fullscreen
      }"
      :style="{ zIndex }"
    >
      <div class="loading-content">
        <!-- 加载图标 -->
        <div class="loading-icon">
          <slot name="icon">
            <el-icon v-if="computedIcon" :size="iconSize" class="is-loading">
              <component :is="computedIcon" />
            </el-icon>
            <div v-else class="default-spinner">
              <div class="spinner-circle"></div>
            </div>
          </slot>
        </div>

        <!-- 加载文本 -->
        <div v-if="text || $slots.text" class="loading-text">
          <slot name="text">{{ text }}</slot>
        </div>

        <!-- 额外内容 -->
        <div v-if="$slots.extra" class="loading-extra">
          <slot name="extra"></slot>
        </div>
      </div>
    </div>
  </Transition>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { Loading } from '@element-plus/icons-vue'
import type { Component } from 'vue'

/**
 * Props 配置
 */
interface Props {
  // 是否显示加载遮罩
  visible?: boolean
  // 加载文本
  text?: string
  // 自定义图标
  icon?: Component | string
  // 图标大小
  iconSize?: number
  // 是否全屏显示
  fullscreen?: boolean
  // 是否背景模糊
  blur?: boolean
  // 层级
  zIndex?: number
}

const props = withDefaults(defineProps<Props>(), {
  visible: false,
  text: '加载中...',
  iconSize: 40,
  fullscreen: false,
  blur: false,
  zIndex: 2000
})

/**
 * 计算图标
 */
const computedIcon = computed(() => {
  return props.icon || Loading
})
</script>

<style scoped lang="scss">
.loading-overlay {
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: rgba(255, 255, 255, 0.9);
  transition: opacity 0.3s;

  &.is-fullscreen {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
  }

  &.is-absolute {
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
  }

  &.is-blur {
    backdrop-filter: blur(2px);
  }

  .loading-content {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 16px;

    .loading-icon {
      color: var(--el-color-primary);

      .is-loading {
        animation: rotating 2s linear infinite;
      }

      .default-spinner {
        position: relative;
        width: 40px;
        height: 40px;

        .spinner-circle {
          position: absolute;
          width: 100%;
          height: 100%;
          border: 3px solid var(--el-color-primary-light-5);
          border-top-color: var(--el-color-primary);
          border-radius: 50%;
          animation: rotating 1s linear infinite;
        }
      }
    }

    .loading-text {
      font-size: 14px;
      color: var(--el-text-color-primary);
      line-height: 1.5;
      text-align: center;
    }

    .loading-extra {
      text-align: center;
    }
  }
}

// 进入/离开动画
.loading-fade-enter-active,
.loading-fade-leave-active {
  transition: opacity 0.3s;
}

.loading-fade-enter-from,
.loading-fade-leave-to {
  opacity: 0;
}

@keyframes rotating {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}

// 暗色模式适配
@media (prefers-color-scheme: dark) {
  .loading-overlay {
    background-color: rgba(0, 0, 0, 0.7);
  }
}

// 响应式设计
@media (max-width: 480px) {
  .loading-overlay {
    .loading-content {
      gap: 12px;

      .loading-icon {
        .default-spinner {
          width: 32px;
          height: 32px;
        }
      }

      .loading-text {
        font-size: 13px;
      }
    }
  }
}
</style>
