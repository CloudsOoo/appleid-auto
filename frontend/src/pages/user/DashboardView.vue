<!--
  用户仪表盘页面

  职责：
  - 显示用户数据统计（账号数、任务数、分享页数等）
  - 展示最近任务列表
  - 展示最近账号列表
  - 提供快捷操作入口
  - 显示系统公告和提示

  上游依赖：
  - PageHeader（页面标题组件）
  - DataTable（表格组件）
  - StatusTag（状态标签组件）
  - EmptyState（空状态组件）
  - Vue Router（页面跳转）
  - userStore（用户信息）

  下游调用者：
  - 路由（/dashboard）
  - 登录成功后自动跳转
  - 侧边栏导航点击
-->

<template>
  <div class="dashboard-view">
    <!-- 页面标题 -->
    <PageHeader title="仪表盘" description="欢迎回来，查看您的账号和任务概况">
      <template #actions>
        <el-button type="primary" :icon="Plus" @click="handleAddAccount">
          添加账号
        </el-button>
        <el-button :icon="Refresh" @click="handleRefresh">刷新</el-button>
      </template>
    </PageHeader>

    <!-- 统计卡片 -->
    <div class="stats-grid">
      <div
        v-for="stat in stats"
        :key="stat.key"
        class="stat-card"
        :class="`stat-card--${stat.key}`"
        @click="handleStatClick(stat.key)"
      >
        <div class="stat-icon">
          <el-icon :size="32">
            <component :is="stat.icon" />
          </el-icon>
        </div>
        <div class="stat-content">
          <div class="stat-label">{{ stat.label }}</div>
          <div class="stat-value">
            <span class="number">{{ stat.value }}</span>
            <span v-if="stat.unit" class="unit">{{ stat.unit }}</span>
          </div>
          <div v-if="stat.trend" class="stat-trend" :class="stat.trend.type">
            <el-icon :size="14">
              <component :is="stat.trend.type === 'up' ? TrendCharts : Bottom" />
            </el-icon>
            <span>{{ stat.trend.value }}</span>
          </div>
        </div>
      </div>
    </div>

    <!-- 主要内容区 -->
    <el-row :gutter="20" class="content-row">
      <!-- 左侧：最近任务 -->
      <el-col :xs="24" :lg="14">
        <div class="content-card">
          <div class="card-header">
            <h3 class="card-title">最近任务</h3>
            <el-link type="primary" :underline="false" @click="handleViewAllTasks">
              查看全部 <el-icon><ArrowRight /></el-icon>
            </el-link>
          </div>
          <div class="card-body">
            <DataTable
              :data="recentTasks"
              :columns="taskColumns"
              :loading="taskLoading"
              :show-pagination="false"
              :show-toolbar="false"
              :show-selection="false"
              :show-actions="true"
              :action-buttons="taskActions"
              @row-action="handleTaskAction"
              @row-click="handleTaskClick"
            >
              <template #column-status="{ row }">
                <StatusTag :status="row.status" :text="row.statusText" />
              </template>
            </DataTable>

            <EmptyState
              v-if="recentTasks.length === 0 && !taskLoading"
              type="empty"
              title="暂无任务"
              description="您还没有创建任何任务"
              action-text="创建任务"
              @action="handleCreateTask"
            />
          </div>
        </div>
      </el-col>

      <!-- 右侧：最近账号 -->
      <el-col :xs="24" :lg="10">
        <div class="content-card">
          <div class="card-header">
            <h3 class="card-title">最近账号</h3>
            <el-link type="primary" :underline="false" @click="handleViewAllAccounts">
              查看全部 <el-icon><ArrowRight /></el-icon>
            </el-link>
          </div>
          <div class="card-body">
            <div v-if="!accountLoading" class="account-list">
              <div
                v-for="account in recentAccounts"
                :key="account.id"
                class="account-item"
                @click="handleAccountClick(account)"
              >
                <div class="account-avatar">
                  <el-icon :size="24"><UserFilled /></el-icon>
                </div>
                <div class="account-info">
                  <div class="account-email">{{ account.apple_id }}</div>
                  <div class="account-time">{{ account.updated_at }}</div>
                </div>
                <StatusTag :status="account.status" :text="account.statusText" size="small" />
              </div>
            </div>

            <LoadingOverlay v-if="accountLoading" :visible="accountLoading" text="加载中..." />

            <EmptyState
              v-if="recentAccounts.length === 0 && !accountLoading"
              type="empty"
              title="暂无账号"
              description="您还没有添加任何账号"
              action-text="添加账号"
              @action="handleAddAccount"
            />
          </div>
        </div>
      </el-col>
    </el-row>

    <!-- 快捷操作 -->
    <div class="quick-actions">
      <h3 class="section-title">快捷操作</h3>
      <div class="action-grid">
        <div
          v-for="action in quickActions"
          :key="action.key"
          class="action-card"
          @click="handleQuickAction(action.key)"
        >
          <div class="action-icon" :style="{ background: action.color }">
            <el-icon :size="28">
              <component :is="action.icon" />
            </el-icon>
          </div>
          <div class="action-label">{{ action.label }}</div>
          <div class="action-desc">{{ action.desc }}</div>
        </div>
      </div>
    </div>

    <!-- 系统公告（可选） -->
    <div v-if="announcements.length > 0" class="announcements">
      <h3 class="section-title">系统公告</h3>
      <el-alert
        v-for="announcement in announcements"
        :key="announcement.id"
        :title="announcement.title"
        :type="announcement.type"
        :closable="true"
        class="announcement-item"
      >
        {{ announcement.content }}
      </el-alert>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import {
  Plus,
  Refresh,
  ArrowRight,
  UserFilled,
  TrendCharts,
  Bottom,
  User,
  Document,
  Share,
  Clock,
  UploadFilled,
  Setting,
  Warning,
  Files
} from '@element-plus/icons-vue'
import { useUserStore } from '@/stores/user'
import PageHeader from '@/components/common/PageHeader.vue'
import DataTable from '@/components/common/DataTable.vue'
import StatusTag from '@/components/common/StatusTag.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import LoadingOverlay from '@/components/common/LoadingOverlay.vue'
import type { TableColumn, ActionButton } from '@/components/common/DataTable.vue'

const router = useRouter()
const userStore = useUserStore()

/**
 * 统计数据
 */
const stats = reactive([
  {
    key: 'accounts',
    label: '账号总数',
    value: 0,
    unit: '个',
    icon: User,
    trend: { type: 'up', value: '+12%' }
  },
  {
    key: 'tasks',
    label: '任务总数',
    value: 0,
    unit: '个',
    icon: Document,
    trend: { type: 'up', value: '+8%' }
  },
  {
    key: 'shares',
    label: '分享页',
    value: 0,
    unit: '个',
    icon: Share,
    trend: null
  },
  {
    key: 'processing',
    label: '进行中',
    value: 0,
    unit: '个',
    icon: Clock,
    trend: null
  }
])

/**
 * 最近任务列表
 */
const recentTasks = ref<any[]>([])
const taskLoading = ref(false)

/**
 * 任务表格列配置
 */
const taskColumns: TableColumn[] = [
  { prop: 'id', label: 'ID', width: '80', sortable: true },
  { prop: 'apple_id', label: 'Apple ID', minWidth: '200' },
  { prop: 'task_type', label: '任务类型', width: '120' },
  { prop: 'status', label: '状态', width: '120' },
  { prop: 'created_at', label: '创建时间', width: '180', sortable: true }
]

/**
 * 任务操作按钮
 */
const taskActions: ActionButton[] = [
  { key: 'view', label: '查看', type: 'primary', icon: 'View' }
]

/**
 * 最近账号列表
 */
const recentAccounts = ref<any[]>([])
const accountLoading = ref(false)

/**
 * 快捷操作
 */
const quickActions = [
  {
    key: 'add-account',
    label: '添加账号',
    desc: '添加新的 Apple ID',
    icon: Plus,
    color: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)'
  },
  {
    key: 'create-task',
    label: '创建任务',
    desc: '创建解锁任务',
    icon: Document,
    color: 'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)'
  },
  {
    key: 'import',
    label: '批量导入',
    desc: '批量导入账号',
    icon: UploadFilled,
    color: 'linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)'
  },
  {
    key: 'export',
    label: '导出数据',
    desc: '导出账号数据',
    icon: Files,
    color: 'linear-gradient(135deg, #43e97b 0%, #38f9d7 100%)'
  },
  {
    key: 'settings',
    label: '系统设置',
    desc: '个人设置和偏好',
    icon: Setting,
    color: 'linear-gradient(135deg, #fa709a 0%, #fee140 100%)'
  },
  {
    key: 'help',
    label: '帮助中心',
    desc: '查看使用文档',
    icon: Warning,
    color: 'linear-gradient(135deg, #30cfd0 0%, #330867 100%)'
  }
]

/**
 * 系统公告
 */
const announcements = ref<any[]>([])

/**
 * 加载统计数据
 */
async function loadStats() {
  try {
    // TODO: 调用 API 获取统计数据
    // import { getStatsApi } from '@/api/dashboard'
    // const data = await getStatsApi()

    // Mock 数据（临时实现）
    stats[0].value = 28
    stats[1].value = 156
    stats[2].value = 5
    stats[3].value = 3
  } catch (error) {
    console.error('[DashboardView] Load stats error:', error)
  }
}

/**
 * 加载最近任务
 */
async function loadRecentTasks() {
  try {
    taskLoading.value = true

    // TODO: 调用 API 获取最近任务
    // import { getRecentTasksApi } from '@/api/tasks'
    // recentTasks.value = await getRecentTasksApi({ limit: 5 })

    // Mock 数据（临时实现）
    recentTasks.value = [
      {
        id: 1,
        apple_id: 'user1@example.com',
        task_type: '账号解锁',
        status: 'processing',
        statusText: '进行中',
        created_at: '2025-11-21 10:30:00'
      },
      {
        id: 2,
        apple_id: 'user2@example.com',
        task_type: '密码重置',
        status: 'completed',
        statusText: '已完成',
        created_at: '2025-11-21 09:15:00'
      },
      {
        id: 3,
        apple_id: 'user3@example.com',
        task_type: '账号解锁',
        status: 'failed',
        statusText: '失败',
        created_at: '2025-11-20 18:45:00'
      }
    ]
  } catch (error) {
    console.error('[DashboardView] Load tasks error:', error)
  } finally {
    taskLoading.value = false
  }
}

/**
 * 加载最近账号
 */
async function loadRecentAccounts() {
  try {
    accountLoading.value = true

    // TODO: 调用 API 获取最近账号
    // import { getRecentAccountsApi } from '@/api/accounts'
    // recentAccounts.value = await getRecentAccountsApi({ limit: 5 })

    // Mock 数据（临时实现）
    await new Promise(resolve => setTimeout(resolve, 500))
    recentAccounts.value = [
      {
        id: 1,
        apple_id: 'test1@icloud.com',
        status: 'unlocked',
        statusText: '正常',
        updated_at: '2 小时前'
      },
      {
        id: 2,
        apple_id: 'test2@icloud.com',
        status: 'locked',
        statusText: '已锁定',
        updated_at: '3 小时前'
      },
      {
        id: 3,
        apple_id: 'test3@icloud.com',
        status: 'pending',
        statusText: '待验证',
        updated_at: '5 小时前'
      },
      {
        id: 4,
        apple_id: 'test4@icloud.com',
        status: 'unlocked',
        statusText: '正常',
        updated_at: '1 天前'
      }
    ]
  } catch (error) {
    console.error('[DashboardView] Load accounts error:', error)
  } finally {
    accountLoading.value = false
  }
}

/**
 * 加载公告
 */
async function loadAnnouncements() {
  try {
    // TODO: 调用 API 获取公告
    // import { getAnnouncementsApi } from '@/api/system'
    // announcements.value = await getAnnouncementsApi()

    // Mock 数据（临时实现）
    announcements.value = [
      {
        id: 1,
        title: '系统维护通知',
        content: '系统将于 2025-11-25 02:00-04:00 进行维护，届时服务将暂停。',
        type: 'warning'
      }
    ]
  } catch (error) {
    console.error('[DashboardView] Load announcements error:', error)
  }
}

/**
 * 刷新数据
 */
async function handleRefresh() {
  ElMessage.success('正在刷新数据...')
  await Promise.all([
    loadStats(),
    loadRecentTasks(),
    loadRecentAccounts(),
    loadAnnouncements()
  ])
  ElMessage.success('刷新成功')
}

/**
 * 统计卡片点击
 */
function handleStatClick(key: string) {
  switch (key) {
    case 'accounts':
      router.push('/accounts')
      break
    case 'tasks':
      router.push('/tasks')
      break
    case 'shares':
      router.push('/share-pages')
      break
    case 'processing':
      router.push('/tasks?status=processing')
      break
  }
}

/**
 * 任务操作
 */
function handleTaskAction(actionKey: string, row: any) {
  if (actionKey === 'view') {
    router.push(`/tasks/${row.id}`)
  }
}

/**
 * 任务行点击
 */
function handleTaskClick(row: any) {
  router.push(`/tasks/${row.id}`)
}

/**
 * 账号点击
 */
function handleAccountClick(account: any) {
  router.push(`/accounts/${account.id}`)
}

/**
 * 查看全部任务
 */
function handleViewAllTasks() {
  router.push('/tasks')
}

/**
 * 查看全部账号
 */
function handleViewAllAccounts() {
  router.push('/accounts')
}

/**
 * 添加账号
 */
function handleAddAccount() {
  router.push('/accounts/add')
}

/**
 * 创建任务
 */
function handleCreateTask() {
  router.push('/tasks/create')
}

/**
 * 快捷操作
 */
function handleQuickAction(key: string) {
  switch (key) {
    case 'add-account':
      handleAddAccount()
      break
    case 'create-task':
      handleCreateTask()
      break
    case 'import':
      router.push('/accounts/import')
      break
    case 'export':
      ElMessage.info('导出功能即将上线')
      break
    case 'settings':
      router.push('/profile')
      break
    case 'help':
      router.push('/help')
      break
  }
}

/**
 * 组件挂载
 */
onMounted(async () => {
  await handleRefresh()
})
</script>

<style scoped lang="scss">
.dashboard-view {
  padding: 20px;

  .stats-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
    gap: 20px;
    margin-bottom: 24px;

    .stat-card {
      display: flex;
      align-items: center;
      gap: 16px;
      padding: 24px;
      background: #fff;
      border-radius: 8px;
      box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
      cursor: pointer;
      transition: all 0.3s;

      &:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.12);
      }

      .stat-icon {
        flex-shrink: 0;
        width: 64px;
        height: 64px;
        display: flex;
        align-items: center;
        justify-content: center;
        border-radius: 12px;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: #fff;
      }

      &.stat-card--tasks .stat-icon {
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
      }

      &.stat-card--shares .stat-icon {
        background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
      }

      &.stat-card--processing .stat-icon {
        background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%);
      }

      .stat-content {
        flex: 1;

        .stat-label {
          margin-bottom: 8px;
          font-size: 14px;
          color: #909399;
        }

        .stat-value {
          margin-bottom: 4px;
          display: flex;
          align-items: baseline;
          gap: 4px;

          .number {
            font-size: 32px;
            font-weight: 700;
            color: #303133;
            line-height: 1;
          }

          .unit {
            font-size: 14px;
            color: #909399;
          }
        }

        .stat-trend {
          display: flex;
          align-items: center;
          gap: 4px;
          font-size: 13px;

          &.up {
            color: #67c23a;
          }

          &.down {
            color: #f56c6c;
          }
        }
      }
    }
  }

  .content-row {
    margin-bottom: 24px;

    .content-card {
      background: #fff;
      border-radius: 8px;
      box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
      overflow: hidden;

      .card-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 20px 24px;
        border-bottom: 1px solid #ebeef5;

        .card-title {
          margin: 0;
          font-size: 18px;
          font-weight: 600;
          color: #303133;
        }
      }

      .card-body {
        padding: 16px;
        min-height: 200px;
        position: relative;

        .account-list {
          .account-item {
            display: flex;
            align-items: center;
            gap: 12px;
            padding: 12px;
            border-radius: 8px;
            cursor: pointer;
            transition: background 0.2s;

            &:hover {
              background: #f5f7fa;
            }

            & + .account-item {
              margin-top: 8px;
            }

            .account-avatar {
              flex-shrink: 0;
              width: 40px;
              height: 40px;
              display: flex;
              align-items: center;
              justify-content: center;
              border-radius: 50%;
              background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
              color: #fff;
            }

            .account-info {
              flex: 1;
              min-width: 0;

              .account-email {
                font-size: 14px;
                font-weight: 500;
                color: #303133;
                margin-bottom: 4px;
                overflow: hidden;
                text-overflow: ellipsis;
                white-space: nowrap;
              }

              .account-time {
                font-size: 12px;
                color: #909399;
              }
            }
          }
        }
      }
    }
  }

  .quick-actions {
    margin-bottom: 24px;

    .section-title {
      margin: 0 0 16px;
      font-size: 18px;
      font-weight: 600;
      color: #303133;
    }

    .action-grid {
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(160px, 1fr));
      gap: 16px;

      .action-card {
        padding: 20px;
        background: #fff;
        border-radius: 8px;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
        text-align: center;
        cursor: pointer;
        transition: all 0.3s;

        &:hover {
          transform: translateY(-4px);
          box-shadow: 0 6px 16px rgba(0, 0, 0, 0.12);
        }

        .action-icon {
          width: 56px;
          height: 56px;
          margin: 0 auto 12px;
          display: flex;
          align-items: center;
          justify-content: center;
          border-radius: 12px;
          color: #fff;
        }

        .action-label {
          margin-bottom: 4px;
          font-size: 15px;
          font-weight: 500;
          color: #303133;
        }

        .action-desc {
          font-size: 12px;
          color: #909399;
        }
      }
    }
  }

  .announcements {
    .section-title {
      margin: 0 0 16px;
      font-size: 18px;
      font-weight: 600;
      color: #303133;
    }

    .announcement-item {
      & + .announcement-item {
        margin-top: 12px;
      }
    }
  }
}

// 响应式设计
@media (max-width: 1200px) {
  .dashboard-view {
    .stats-grid {
      grid-template-columns: repeat(2, 1fr);
    }

    .quick-actions .action-grid {
      grid-template-columns: repeat(3, 1fr);
    }
  }
}

@media (max-width: 768px) {
  .dashboard-view {
    padding: 16px;

    .stats-grid {
      grid-template-columns: repeat(2, 1fr);
      gap: 12px;

      .stat-card {
        padding: 16px;

        .stat-icon {
          width: 48px;
          height: 48px;

          :deep(.el-icon) {
            font-size: 24px !important;
          }
        }

        .stat-content {
          .stat-value .number {
            font-size: 24px;
          }
        }
      }
    }

    .content-row {
      margin-bottom: 16px;
    }

    .quick-actions .action-grid {
      grid-template-columns: repeat(2, 1fr);
    }
  }
}

@media (max-width: 480px) {
  .dashboard-view {
    padding: 12px;

    .stats-grid {
      grid-template-columns: 1fr;
    }

    .quick-actions .action-grid {
      grid-template-columns: repeat(2, 1fr);
      gap: 12px;

      .action-card {
        padding: 16px;

        .action-icon {
          width: 48px;
          height: 48px;

          :deep(.el-icon) {
            font-size: 24px !important;
          }
        }

        .action-label {
          font-size: 14px;
        }
      }
    }
  }
}
</style>
