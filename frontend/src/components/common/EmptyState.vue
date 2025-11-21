<!--
  空状态组件

  职责：
  - 显示空数据状态（无数据、搜索无结果、网络错误等）
  - 支持自定义图标和文本
  - 支持操作按钮（如"添加数据"、"重试"等）
  - 支持自定义插槽
  - 支持不同的空状态类型（无数据、错误、无权限等）

  上游依赖：
  - Element Plus（el-button, el-empty）
  - Element Plus Icons

  下游调用者：
  - DataTable（表格无数据时显示）
  - AccountList（账号列表为空）
  - TaskList（任务列表为空）
  - 所有可能出现空数据的页面
-->

<template>
  <div class="empty-state" :class="[`empty-state--${type}`, customClass]">
    <div class="empty-content">
      <!-- 图标区域 -->
      <div class="empty-icon">
        <slot name="icon">
          <el-icon v-if="computedIcon" :size="iconSize">
            <component :is="computedIcon" />
          </el-icon>
          <img v-else-if="image" :src="image" :alt="title" class="empty-image" />
        </slot>
      </div>

      <!-- 文本区域 -->
      <div class="empty-text">
        <h3 v-if="title || $slots.title" class="empty-title">
          <slot name="title">{{ title }}</slot>
        </h3>
        <p v-if="description || $slots.description" class="empty-description">
          <slot name="description">{{ description }}</slot>
        </p>
      </div>

      <!-- 操作按钮区域 -->
      <div v-if="$slots.actions || actionText" class="empty-actions">
        <slot name="actions">
          <el-button
            v-if="actionText"
            :type="actionType"
            :icon="actionIcon"
            @click="handleAction"
          >
            {{ actionText }}
          </el-button>
        </slot>
      </div>

      <!-- 额外内容 -->
      <div v-if="$slots.extra" class="empty-extra">
        <slot name="extra"></slot>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import {
  Document,
  Search,
  Warning,
  Lock,
  Connection,
  FolderOpened,
  Plus,
  RefreshRight
} from '@element-plus/icons-vue'
import type { Component } from 'vue'

/**
 * 空状态类型
 */
export type EmptyType =
  | 'empty'        // 无数据
  | 'search'       // 搜索无结果
  | 'error'        // 错误
  | 'forbidden'    // 无权限
  | 'network'      // 网络错误
  | 'custom'       // 自定义

/**
 * Props 配置
 */
interface Props {
  // 空状态类型
  type?: EmptyType
  // 标题
  title?: string
  // 描述
  description?: string
  // 自定义图标
  icon?: Component | string
  // 自定义图片
  image?: string
  // 图标大小
  iconSize?: number
  // 操作按钮文本
  actionText?: string
  // 操作按钮类型
  actionType?: 'primary' | 'success' | 'warning' | 'danger' | 'info' | 'default'
  // 操作按钮图标
  actionIcon?: Component
  // 自定义 CSS 类名
  customClass?: string
}

const props = withDefaults(defineProps<Props>(), {
  type: 'empty',
  title: '',
  description: '',
  iconSize: 100,
  actionType: 'primary'
})

/**
 * Emits
 */
interface Emits {
  (e: 'action'): void
}

const emit = defineEmits<Emits>()

/**
 * 空状态配置映射
 */
const emptyConfig = {
  empty: {
    icon: FolderOpened,
    title: '暂无数据',
    description: '当前没有任何数据'
  },
  search: {
    icon: Search,
    title: '无搜索结果',
    description: '未找到符合条件的数据，请尝试其他搜索条件'
  },
  error: {
    icon: Warning,
    title: '加载失败',
    description: '数据加载失败，请稍后重试'
  },
  forbidden: {
    icon: Lock,
    title: '无权限',
    description: '您没有权限查看此内容'
  },
  network: {
    icon: Connection,
    title: '网络错误',
    description: '网络连接失败，请检查网络设置'
  },
  custom: {
    icon: Document,
    title: '',
    description: ''
  }
} as const

/**
 * 计算图标
 */
const computedIcon = computed(() => {
  // 如果手动指定了 icon 或 image，优先使用
  if (props.icon || props.image) {
    return props.icon
  }

  // 根据 type 自动推断
  const config = emptyConfig[props.type]
  return config?.icon || null
})

/**
 * 计算标题
 */
const computedTitle = computed(() => {
  if (props.title) {
    return props.title
  }
  return emptyConfig[props.type]?.title || ''
})

/**
 * 计算描述
 */
const computedDescription = computed(() => {
  if (props.description) {
    return props.description
  }
  return emptyConfig[props.type]?.description || ''
})

/**
 * 操作按钮处理
 */
function handleAction() {
  emit('action')
}
</script>

<style scoped lang="scss">
.empty-state {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 300px;
  padding: 40px 20px;

  .empty-content {
    display: flex;
    flex-direction: column;
    align-items: center;
    text-align: center;
    max-width: 400px;

    .empty-icon {
      margin-bottom: 24px;
      color: var(--el-text-color-placeholder);

      .empty-image {
        max-width: 200px;
        height: auto;
      }
    }

    .empty-text {
      margin-bottom: 24px;

      .empty-title {
        margin: 0 0 12px;
        font-size: 18px;
        font-weight: 500;
        color: var(--el-text-color-primary);
        line-height: 1.5;
      }

      .empty-description {
        margin: 0;
        font-size: 14px;
        color: var(--el-text-color-secondary);
        line-height: 1.6;
      }
    }

    .empty-actions {
      display: flex;
      gap: 12px;
      flex-wrap: wrap;
      justify-content: center;
    }

    .empty-extra {
      margin-top: 16px;
      width: 100%;
    }
  }

  // 不同类型的颜色
  &.empty-state--error {
    .empty-icon {
      color: var(--el-color-danger);
    }
  }

  &.empty-state--forbidden {
    .empty-icon {
      color: var(--el-color-warning);
    }
  }

  &.empty-state--network {
    .empty-icon {
      color: var(--el-color-info);
    }
  }
}

// 响应式设计
@media (max-width: 768px) {
  .empty-state {
    min-height: 250px;
    padding: 30px 20px;

    .empty-content {
      .empty-icon {
        margin-bottom: 20px;

        :deep(.el-icon) {
          font-size: 80px !important;
        }

        .empty-image {
          max-width: 160px;
        }
      }

      .empty-text {
        margin-bottom: 20px;

        .empty-title {
          font-size: 16px;
        }

        .empty-description {
          font-size: 13px;
        }
      }
    }
  }
}

@media (max-width: 480px) {
  .empty-state {
    min-height: 200px;
    padding: 20px 16px;

    .empty-content {
      .empty-icon {
        margin-bottom: 16px;

        :deep(.el-icon) {
          font-size: 60px !important;
        }

        .empty-image {
          max-width: 120px;
        }
      }

      .empty-text {
        margin-bottom: 16px;

        .empty-title {
          font-size: 15px;
        }

        .empty-description {
          font-size: 12px;
        }
      }

      .empty-actions {
        gap: 8px;

        :deep(.el-button) {
          font-size: 13px;
        }
      }
    }
  }
}
</style>
