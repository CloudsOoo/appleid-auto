<!--
  状态标签组件

  职责：
  - 显示各种状态标签（账号状态、任务状态、订单状态等）
  - 根据状态类型自动配置颜色和图标
  - 支持自定义颜色和图标
  - 支持点击事件
  - 支持加载状态

  上游依赖：
  - Element Plus（el-tag）
  - Element Plus Icons

  下游调用者：
  - DataTable（表格中的状态列）
  - AccountList（账号状态）
  - TaskList（任务状态）
  - OrderList（订单状态）
  - 所有需要显示状态的地方
-->

<template>
  <el-tag
    :type="computedType"
    :effect="effect"
    :size="size"
    :round="round"
    :closable="closable"
    :disable-transitions="disableTransitions"
    :hit="hit"
    :class="['status-tag', clickable && 'is-clickable', customClass]"
    @click="handleClick"
    @close="handleClose"
  >
    <!-- 加载图标 -->
    <el-icon v-if="loading" class="is-loading">
      <Loading />
    </el-icon>

    <!-- 状态图标 -->
    <el-icon v-else-if="computedIcon" class="status-icon">
      <component :is="computedIcon" />
    </el-icon>

    <!-- 状态文本 -->
    <span class="status-text">
      <slot>{{ text }}</slot>
    </span>
  </el-tag>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import {
  Loading,
  CircleCheck,
  CircleClose,
  Warning,
  Clock,
  Lock,
  Unlock,
  RefreshRight,
  Document,
  Edit,
  Delete,
  QuestionFilled
} from '@element-plus/icons-vue'
import type { Component } from 'vue'

/**
 * 状态类型（预定义）
 */
export type StatusType =
  | 'success'     // 成功/正常/已完成
  | 'warning'     // 警告/待处理
  | 'danger'      // 失败/错误/已禁用
  | 'info'        // 信息/进行中
  | 'primary'     // 主要
  | 'locked'      // 已锁定
  | 'unlocked'    // 已解锁
  | 'pending'     // 待处理
  | 'processing'  // 处理中
  | 'completed'   // 已完成
  | 'failed'      // 失败
  | 'cancelled'   // 已取消
  | 'draft'       // 草稿
  | 'custom'      // 自定义

/**
 * Props 配置
 */
interface Props {
  // 状态类型（使用预定义类型或 custom）
  status?: StatusType
  // 状态文本
  text?: string
  // 自定义 Element Plus tag 类型（会覆盖自动推断）
  type?: 'success' | 'warning' | 'danger' | 'info' | ''
  // 自定义图标（会覆盖自动推断）
  icon?: Component | string
  // 标签效果
  effect?: 'dark' | 'light' | 'plain'
  // 标签尺寸
  size?: 'large' | 'default' | 'small'
  // 是否圆角
  round?: boolean
  // 是否可关闭
  closable?: boolean
  // 是否禁用渐变动画
  disableTransitions?: boolean
  // 是否显示边框描边
  hit?: boolean
  // 是否可点击
  clickable?: boolean
  // 是否显示加载状态
  loading?: boolean
  // 自定义 CSS 类名
  customClass?: string
}

const props = withDefaults(defineProps<Props>(), {
  status: 'info',
  text: '',
  effect: 'light',
  size: 'default',
  round: false,
  closable: false,
  disableTransitions: false,
  hit: false,
  clickable: false,
  loading: false,
  customClass: ''
})

/**
 * Emits
 */
interface Emits {
  (e: 'click'): void
  (e: 'close'): void
}

const emit = defineEmits<Emits>()

/**
 * 状态配置映射
 */
const statusConfig = {
  success: { type: 'success', icon: CircleCheck },
  warning: { type: 'warning', icon: Warning },
  danger: { type: 'danger', icon: CircleClose },
  info: { type: 'info', icon: QuestionFilled },
  primary: { type: 'primary', icon: Document },
  locked: { type: 'danger', icon: Lock },
  unlocked: { type: 'success', icon: Unlock },
  pending: { type: 'warning', icon: Clock },
  processing: { type: 'info', icon: RefreshRight },
  completed: { type: 'success', icon: CircleCheck },
  failed: { type: 'danger', icon: CircleClose },
  cancelled: { type: 'info', icon: Delete },
  draft: { type: 'info', icon: Edit },
  custom: { type: '', icon: null }
} as const

/**
 * 计算标签类型
 */
const computedType = computed(() => {
  // 如果手动指定了 type，使用手动值
  if (props.type !== undefined) {
    return props.type
  }

  // 根据 status 自动推断
  const config = statusConfig[props.status]
  return config?.type || ''
})

/**
 * 计算图标
 */
const computedIcon = computed(() => {
  // 如果手动指定了 icon，使用手动值
  if (props.icon) {
    return props.icon
  }

  // 根据 status 自动推断
  const config = statusConfig[props.status]
  return config?.icon || null
})

/**
 * 点击处理
 */
function handleClick() {
  if (props.clickable && !props.loading) {
    emit('click')
  }
}

/**
 * 关闭处理
 */
function handleClose() {
  emit('close')
}
</script>

<style scoped lang="scss">
.status-tag {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  user-select: none;

  &.is-clickable {
    cursor: pointer;
    transition: opacity 0.2s;

    &:hover {
      opacity: 0.8;
    }

    &:active {
      opacity: 0.9;
    }
  }

  .status-icon {
    font-size: 14px;

    &.is-loading {
      animation: rotating 2s linear infinite;
    }
  }

  .status-text {
    line-height: 1;
  }
}

@keyframes rotating {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}

// 响应式设计
@media (max-width: 480px) {
  .status-tag {
    font-size: 12px;

    .status-icon {
      font-size: 12px;
    }
  }
}
</style>
