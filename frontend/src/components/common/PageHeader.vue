<!--
  页面标题组件

  职责：
  - 提供统一的页面标题样式
  - 支持面包屑导航
  - 支持页面操作按钮（右侧按钮组）
  - 支持副标题/描述信息
  - 支持返回按钮
  - 支持自定义插槽

  上游依赖：
  - Element Plus（el-breadcrumb, el-button）
  - Vue Router（路由跳转）

  下游调用者：
  - AccountList（账号管理页面）
  - TaskList（任务管理页面）
  - UserManagement（用户管理页面）
  - PackageManagement（套餐管理页面）
  - 所有需要标题栏的页面
-->

<template>
  <div class="page-header">
    <!-- 面包屑导航 -->
    <el-breadcrumb v-if="breadcrumbs && breadcrumbs.length > 0" class="page-breadcrumb" separator="/">
      <el-breadcrumb-item
        v-for="(item, index) in breadcrumbs"
        :key="index"
        :to="item.path"
      >
        {{ item.title }}
      </el-breadcrumb-item>
    </el-breadcrumb>

    <!-- 标题区域 -->
    <div class="header-main">
      <div class="header-left">
        <!-- 返回按钮 -->
        <el-button
          v-if="showBack"
          class="back-button"
          :icon="ArrowLeft"
          circle
          @click="handleBack"
        />

        <!-- 标题内容 -->
        <div class="header-content">
          <div class="header-title-row">
            <!-- 自定义标题插槽 -->
            <slot name="title">
              <h1 class="page-title">{{ title }}</h1>
            </slot>

            <!-- 标签插槽（用于状态标签等） -->
            <slot name="tags"></slot>
          </div>

          <!-- 副标题/描述 -->
          <p v-if="description || $slots.description" class="page-description">
            <slot name="description">{{ description }}</slot>
          </p>
        </div>
      </div>

      <!-- 右侧操作区 -->
      <div v-if="$slots.actions" class="header-actions">
        <slot name="actions"></slot>
      </div>
    </div>

    <!-- 额外内容区域（例如 tabs、filters） -->
    <div v-if="$slots.extra" class="header-extra">
      <slot name="extra"></slot>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ArrowLeft } from '@element-plus/icons-vue'
import { useRouter } from 'vue-router'

/**
 * 面包屑项类型
 */
export interface BreadcrumbItem {
  title: string       // 面包屑文本
  path?: string       // 路由路径（可选，不填则不可点击）
}

/**
 * Props 配置
 */
interface Props {
  title?: string                  // 页面标题
  description?: string            // 页面描述/副标题
  breadcrumbs?: BreadcrumbItem[]  // 面包屑导航
  showBack?: boolean              // 是否显示返回按钮（默认 false）
  backPath?: string               // 自定义返回路径（默认使用 router.back()）
}

const props = withDefaults(defineProps<Props>(), {
  title: '',
  description: '',
  showBack: false
})

/**
 * Emits
 */
interface Emits {
  (e: 'back'): void  // 返回事件
}

const emit = defineEmits<Emits>()

const router = useRouter()

/**
 * 返回按钮处理
 */
function handleBack() {
  emit('back')

  if (props.backPath) {
    router.push(props.backPath)
  } else {
    router.back()
  }
}
</script>

<style scoped lang="scss">
.page-header {
  margin-bottom: 20px;
  padding: 20px 24px;
  background-color: #fff;
  border-radius: 4px;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);

  .page-breadcrumb {
    margin-bottom: 16px;
    font-size: 14px;
  }

  .header-main {
    display: flex;
    align-items: flex-start;
    justify-content: space-between;
    gap: 20px;

    .header-left {
      flex: 1;
      display: flex;
      align-items: flex-start;
      gap: 16px;
      min-width: 0; // 防止 flex 子元素溢出

      .back-button {
        margin-top: 4px;
        flex-shrink: 0;
      }

      .header-content {
        flex: 1;
        min-width: 0;

        .header-title-row {
          display: flex;
          align-items: center;
          gap: 12px;
          flex-wrap: wrap;

          .page-title {
            margin: 0;
            font-size: 24px;
            font-weight: 600;
            color: var(--el-text-color-primary);
            line-height: 32px;
          }
        }

        .page-description {
          margin: 8px 0 0;
          font-size: 14px;
          color: var(--el-text-color-secondary);
          line-height: 22px;
        }
      }
    }

    .header-actions {
      flex-shrink: 0;
      display: flex;
      align-items: center;
      gap: 12px;
      flex-wrap: wrap;
    }
  }

  .header-extra {
    margin-top: 16px;
    padding-top: 16px;
    border-top: 1px solid var(--el-border-color-lighter);
  }
}

// 响应式设计
@media (max-width: 768px) {
  .page-header {
    padding: 16px;
    margin-bottom: 16px;

    .header-main {
      flex-direction: column;
      align-items: stretch;

      .header-left {
        .header-content {
          .header-title-row {
            .page-title {
              font-size: 20px;
              line-height: 28px;
            }
          }

          .page-description {
            font-size: 13px;
          }
        }
      }

      .header-actions {
        width: 100%;
        justify-content: flex-start;
      }
    }
  }
}

@media (max-width: 480px) {
  .page-header {
    padding: 12px;
    margin-bottom: 12px;

    .page-breadcrumb {
      margin-bottom: 12px;
      font-size: 13px;
    }

    .header-main {
      .header-left {
        gap: 12px;

        .header-content {
          .header-title-row {
            .page-title {
              font-size: 18px;
              line-height: 24px;
            }
          }
        }
      }

      .header-actions {
        gap: 8px;

        :deep(.el-button) {
          font-size: 13px;
        }
      }
    }

    .header-extra {
      margin-top: 12px;
      padding-top: 12px;
    }
  }
}
</style>
