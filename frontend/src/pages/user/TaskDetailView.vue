<template>
  <div class="task-detail-view">
    <PageHeader
      title="任务详情"
      :show-back="true"
      @back="handleBack"
    >
      <template #tags>
        <StatusTag
          :type="getStatusType(taskDetail.status)"
          :text="getStatusText(taskDetail.status)"
        />
        <el-tag :type="getTaskTypeColor(taskDetail.task_type)" size="large">
          {{ getTaskTypeText(taskDetail.task_type) }}
        </el-tag>
        <el-tag :type="getPriorityColor(taskDetail.priority)" size="large">
          {{ getPriorityText(taskDetail.priority) }}
        </el-tag>
      </template>
      <template #actions>
        <el-button
          v-if="canCancel"
          type="warning"
          :icon="Close"
          @click="handleCancelTask"
        >
          取消任务
        </el-button>
        <el-button
          v-if="canRetry"
          type="primary"
          :icon="Refresh"
          @click="handleRetryTask"
        >
          重试任务
        </el-button>
        <el-button
          v-if="canDelete"
          type="danger"
          :icon="Delete"
          @click="handleDeleteTask"
        >
          删除任务
        </el-button>
        <el-button :icon="Refresh" @click="handleRefresh">
          刷新
        </el-button>
      </template>
    </PageHeader>

    <LoadingOverlay :loading="loading" text="加载任务详情..." />

    <div v-if="!loading" class="detail-container">
      <!-- 基本信息卡片 -->
      <el-card class="info-card" shadow="never">
        <template #header>
          <div class="card-header">
            <el-icon :size="18"><InfoFilled /></el-icon>
            <span>基本信息</span>
          </div>
        </template>

        <el-descriptions :column="2" border>
          <el-descriptions-item label="任务ID">
            <el-tag type="info">{{ taskDetail.id }}</el-tag>
          </el-descriptions-item>

          <el-descriptions-item label="Apple ID">
            <div class="apple-id-cell">
              <el-icon><User /></el-icon>
              <span>{{ taskDetail.apple_id }}</span>
            </div>
          </el-descriptions-item>

          <el-descriptions-item label="任务类型">
            <el-tag :type="getTaskTypeColor(taskDetail.task_type)">
              {{ getTaskTypeText(taskDetail.task_type) }}
            </el-tag>
          </el-descriptions-item>

          <el-descriptions-item label="任务状态">
            <StatusTag
              :type="getStatusType(taskDetail.status)"
              :text="getStatusText(taskDetail.status)"
            />
          </el-descriptions-item>

          <el-descriptions-item label="优先级">
            <el-tag :type="getPriorityColor(taskDetail.priority)">
              {{ getPriorityText(taskDetail.priority) }}
            </el-tag>
          </el-descriptions-item>

          <el-descriptions-item label="创建时间">
            {{ formatDateTime(taskDetail.created_at) }}
          </el-descriptions-item>

          <el-descriptions-item label="开始时间">
            {{ taskDetail.started_at ? formatDateTime(taskDetail.started_at) : '-' }}
          </el-descriptions-item>

          <el-descriptions-item label="完成时间">
            {{ taskDetail.finished_at ? formatDateTime(taskDetail.finished_at) : '-' }}
          </el-descriptions-item>

          <el-descriptions-item label="耗时" :span="2">
            <el-tag v-if="taskDetail.duration" type="info">
              {{ formatDuration(taskDetail.duration) }}
            </el-tag>
            <span v-else>-</span>
          </el-descriptions-item>

          <el-descriptions-item label="备注" :span="2">
            {{ taskDetail.note || '-' }}
          </el-descriptions-item>
        </el-descriptions>
      </el-card>

      <!-- 执行进度卡片 -->
      <el-card class="progress-card" shadow="never">
        <template #header>
          <div class="card-header">
            <el-icon :size="18"><TrendCharts /></el-icon>
            <span>执行进度</span>
          </div>
        </template>

        <div class="progress-content">
          <div class="progress-info">
            <span class="progress-label">任务进度</span>
            <span class="progress-percentage">{{ taskDetail.progress }}%</span>
          </div>
          <el-progress
            :percentage="taskDetail.progress"
            :status="getProgressStatus(taskDetail.status)"
            :stroke-width="20"
          />

          <!-- 当前步骤 -->
          <div v-if="taskDetail.current_step" class="current-step">
            <el-icon><Clock /></el-icon>
            <span>当前步骤：{{ taskDetail.current_step }}</span>
          </div>

          <!-- 进度说明 -->
          <div class="progress-description">
            <div class="step-item" v-for="(step, index) in progressSteps" :key="index">
              <div class="step-icon" :class="{ completed: step.completed, active: step.active }">
                <el-icon v-if="step.completed"><Check /></el-icon>
                <span v-else>{{ index + 1 }}</span>
              </div>
              <div class="step-content">
                <div class="step-title">{{ step.title }}</div>
                <div class="step-desc">{{ step.description }}</div>
              </div>
            </div>
          </div>
        </div>
      </el-card>

      <!-- 执行日志卡片 -->
      <el-card class="logs-card" shadow="never">
        <template #header>
          <div class="card-header">
            <el-icon :size="18"><Document /></el-icon>
            <span>执行日志</span>
            <div class="header-actions">
              <el-radio-group v-model="logLevel" size="small">
                <el-radio-button value="all">全部</el-radio-button>
                <el-radio-button value="info">信息</el-radio-button>
                <el-radio-button value="warning">警告</el-radio-button>
                <el-radio-button value="error">错误</el-radio-button>
              </el-radio-group>
            </div>
          </div>
        </template>

        <div class="logs-content">
          <el-timeline v-if="filteredLogs.length > 0">
            <el-timeline-item
              v-for="(log, index) in filteredLogs"
              :key="index"
              :timestamp="log.time"
              :type="getLogType(log.level)"
              placement="top"
            >
              <div class="log-item">
                <div class="log-level" :class="'log-level--' + log.level">
                  {{ log.level.toUpperCase() }}
                </div>
                <div class="log-message">{{ log.message }}</div>
              </div>
            </el-timeline-item>
          </el-timeline>

          <EmptyState
            v-else
            type="empty"
            title="暂无日志"
            description="任务还未开始执行或没有生成日志"
          />
        </div>
      </el-card>

      <!-- 任务结果卡片 -->
      <el-card
        v-if="taskDetail.result"
        class="result-card"
        shadow="never"
      >
        <template #header>
          <div class="card-header">
            <el-icon :size="18"><DataAnalysis /></el-icon>
            <span>任务结果</span>
          </div>
        </template>

        <div class="result-content">
          <!-- 成功结果 -->
          <el-result
            v-if="taskDetail.status === 'completed'"
            icon="success"
            title="任务执行成功"
            :sub-title="taskDetail.result.message || '任务已成功完成'"
          >
            <template #extra>
              <el-descriptions :column="2" border>
                <el-descriptions-item
                  v-for="(value, key) in taskDetail.result.data"
                  :key="key"
                  :label="formatResultKey(key)"
                >
                  {{ value }}
                </el-descriptions-item>
              </el-descriptions>
            </template>
          </el-result>

          <!-- 失败结果 -->
          <el-result
            v-else-if="taskDetail.status === 'failed'"
            icon="error"
            title="任务执行失败"
            :sub-title="taskDetail.result.error || '任务执行过程中发生错误'"
          >
            <template #extra>
              <el-alert
                v-if="taskDetail.result.error_detail"
                type="error"
                :closable="false"
                show-icon
              >
                <template #title>
                  <div class="error-detail">
                    <p><strong>错误详情：</strong></p>
                    <pre>{{ taskDetail.result.error_detail }}</pre>
                  </div>
                </template>
              </el-alert>

              <div v-if="taskDetail.result.suggestions" class="suggestions">
                <h4>建议操作：</h4>
                <ul>
                  <li v-for="(suggestion, index) in taskDetail.result.suggestions" :key="index">
                    {{ suggestion }}
                  </li>
                </ul>
              </div>
            </template>
          </el-result>

          <!-- 取消结果 -->
          <el-result
            v-else-if="taskDetail.status === 'cancelled'"
            icon="warning"
            title="任务已取消"
            :sub-title="taskDetail.result.message || '任务被用户手动取消'"
          />
        </div>
      </el-card>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted, onUnmounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  InfoFilled,
  TrendCharts,
  Document,
  DataAnalysis,
  User,
  Clock,
  Check,
  Close,
  Refresh,
  Delete
} from '@element-plus/icons-vue'
import PageHeader from '@/components/common/PageHeader.vue'
import StatusTag from '@/components/common/StatusTag.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import LoadingOverlay from '@/components/common/LoadingOverlay.vue'

// ==================== 类型定义 ====================

interface TaskDetail {
  id: number
  apple_id: string
  task_type: string
  status: string
  priority: string
  progress: number
  current_step: string
  created_at: string
  started_at?: string
  finished_at?: string
  duration?: number
  note: string
  logs: TaskLog[]
  result?: TaskResult
}

interface TaskLog {
  time: string
  level: 'info' | 'warning' | 'error'
  message: string
}

interface TaskResult {
  message?: string
  error?: string
  error_detail?: string
  suggestions?: string[]
  data?: Record<string, any>
}

interface ProgressStep {
  title: string
  description: string
  completed: boolean
  active: boolean
}

// ==================== 路由和状态 ====================

const router = useRouter()
const route = useRoute()

const taskId = computed(() => route.params.id as string)

// ==================== 数据状态 ====================

const loading = ref(false)
const logLevel = ref('all')

// 任务详情
const taskDetail = ref<TaskDetail>({
  id: 0,
  apple_id: '',
  task_type: '',
  status: '',
  priority: '',
  progress: 0,
  current_step: '',
  created_at: '',
  note: '',
  logs: []
})

// 自动刷新定时器
let refreshTimer: NodeJS.Timeout | null = null

// ==================== 计算属性 ====================

// 过滤后的日志
const filteredLogs = computed(() => {
  if (logLevel.value === 'all') {
    return taskDetail.value.logs
  }
  return taskDetail.value.logs.filter(log => log.level === logLevel.value)
})

// 进度步骤
const progressSteps = computed<ProgressStep[]>(() => {
  const steps = [
    { title: '初始化', description: '准备任务执行环境' },
    { title: '连接验证', description: '验证账号连接状态' },
    { title: '执行操作', description: '执行解锁/重置操作' },
    { title: '结果确认', description: '确认操作结果' },
    { title: '完成', description: '任务执行完成' }
  ]

  const progress = taskDetail.value.progress
  return steps.map((step, index) => ({
    ...step,
    completed: progress >= (index + 1) * 20,
    active: progress >= index * 20 && progress < (index + 1) * 20
  }))
})

// 是否可以取消
const canCancel = computed(() => {
  return ['pending', 'processing'].includes(taskDetail.value.status)
})

// 是否可以重试
const canRetry = computed(() => {
  return ['failed', 'cancelled'].includes(taskDetail.value.status)
})

// 是否可以删除
const canDelete = computed(() => {
  return ['completed', 'failed', 'cancelled'].includes(taskDetail.value.status)
})

// ==================== 数据加载 ====================

/**
 * 加载任务详情
 */
async function loadTaskDetail() {
  loading.value = true

  try {
    // TODO: 调用 API 获取任务详情
    // const { data } = await taskApi.getDetail(taskId.value)

    // 模拟 API 调用
    await new Promise(resolve => setTimeout(resolve, 500))

    // 模拟任务数据
    taskDetail.value = {
      id: parseInt(taskId.value),
      apple_id: 'test@example.com',
      task_type: 'unlock',
      status: 'processing',
      priority: 'high',
      progress: 60,
      current_step: '执行解锁操作',
      created_at: '2025-11-21 10:00:00',
      started_at: '2025-11-21 10:01:00',
      duration: 120,
      note: '紧急解锁任务',
      logs: [
        {
          time: '2025-11-21 10:00:00',
          level: 'info',
          message: '任务已创建，等待执行'
        },
        {
          time: '2025-11-21 10:01:00',
          level: 'info',
          message: '开始执行任务'
        },
        {
          time: '2025-11-21 10:01:05',
          level: 'info',
          message: '正在初始化执行环境...'
        },
        {
          time: '2025-11-21 10:01:10',
          level: 'info',
          message: '正在验证账号连接状态...'
        },
        {
          time: '2025-11-21 10:01:15',
          level: 'warning',
          message: '检测到账号已锁定，开始解锁流程'
        },
        {
          time: '2025-11-21 10:01:20',
          level: 'info',
          message: '正在执行解锁操作...'
        }
      ]
    }
  } catch (error: any) {
    console.error('加载任务详情失败:', error)
    ElMessage.error(error.message || '加载失败，请稍后重试')
    // 加载失败，返回列表页
    router.push('/tasks')
  } finally {
    loading.value = false
  }
}

/**
 * 刷新任务详情
 */
async function handleRefresh() {
  await loadTaskDetail()
  ElMessage.success('刷新成功')
}

// ==================== 任务操作 ====================

/**
 * 取消任务
 */
async function handleCancelTask() {
  try {
    await ElMessageBox.confirm(
      '确定要取消此任务吗？取消后任务将停止执行。',
      '取消任务',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )

    // TODO: 调用 API 取消任务
    // await taskApi.cancel(taskId.value)

    // 模拟 API 调用
    await new Promise(resolve => setTimeout(resolve, 500))

    ElMessage.success('任务已取消')
    await loadTaskDetail()
  } catch (error: any) {
    if (error !== 'cancel') {
      console.error('取消任务失败:', error)
      ElMessage.error(error.message || '取消失败，请稍后重试')
    }
  }
}

/**
 * 重试任务
 */
async function handleRetryTask() {
  try {
    await ElMessageBox.confirm(
      '确定要重试此任务吗？任务将重新开始执行。',
      '重试任务',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'info'
      }
    )

    // TODO: 调用 API 重试任务
    // await taskApi.retry(taskId.value)

    // 模拟 API 调用
    await new Promise(resolve => setTimeout(resolve, 500))

    ElMessage.success('任务已重新开始执行')
    await loadTaskDetail()
  } catch (error: any) {
    if (error !== 'cancel') {
      console.error('重试任务失败:', error)
      ElMessage.error(error.message || '重试失败，请稍后重试')
    }
  }
}

/**
 * 删除任务
 */
async function handleDeleteTask() {
  try {
    await ElMessageBox.confirm(
      '确定要删除此任务吗？删除后将无法恢复。',
      '删除任务',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'error'
      }
    )

    // TODO: 调用 API 删除任务
    // await taskApi.delete(taskId.value)

    // 模拟 API 调用
    await new Promise(resolve => setTimeout(resolve, 500))

    ElMessage.success('任务已删除')
    router.push('/tasks')
  } catch (error: any) {
    if (error !== 'cancel') {
      console.error('删除任务失败:', error)
      ElMessage.error(error.message || '删除失败，请稍后重试')
    }
  }
}

// ==================== 工具方法 ====================

/**
 * 格式化日期时间
 */
function formatDateTime(dateTime: string): string {
  if (!dateTime) return '-'
  // TODO: 使用 date.ts 的格式化方法
  return dateTime
}

/**
 * 格式化持续时间
 */
function formatDuration(seconds: number): string {
  if (!seconds) return '-'

  const hours = Math.floor(seconds / 3600)
  const minutes = Math.floor((seconds % 3600) / 60)
  const secs = seconds % 60

  if (hours > 0) {
    return `${hours} 小时 ${minutes} 分钟 ${secs} 秒`
  } else if (minutes > 0) {
    return `${minutes} 分钟 ${secs} 秒`
  } else {
    return `${secs} 秒`
  }
}

/**
 * 格式化结果键名
 */
function formatResultKey(key: string): string {
  const keyMap: Record<string, string> = {
    unlock_time: '解锁时间',
    attempts: '尝试次数',
    method: '解锁方式',
    new_password: '新密码',
    verification_code: '验证码',
    recovery_email: '恢复邮箱'
  }
  return keyMap[key] || key
}

/**
 * 获取状态类型
 */
function getStatusType(status: string): any {
  const map: Record<string, any> = {
    pending: 'info',
    processing: 'primary',
    completed: 'success',
    failed: 'danger',
    cancelled: 'warning'
  }
  return map[status] || 'info'
}

/**
 * 获取状态文本
 */
function getStatusText(status: string): string {
  const map: Record<string, string> = {
    pending: '待执行',
    processing: '执行中',
    completed: '已完成',
    failed: '失败',
    cancelled: '已取消'
  }
  return map[status] || status
}

/**
 * 获取进度状态
 */
function getProgressStatus(status: string): 'success' | 'exception' | undefined {
  if (status === 'completed') return 'success'
  if (status === 'failed') return 'exception'
  return undefined
}

/**
 * 获取任务类型颜色
 */
function getTaskTypeColor(type: string): string {
  const map: Record<string, string> = {
    unlock: 'primary',
    reset_password: 'success',
    setup_2fa: 'warning'
  }
  return map[type] || ''
}

/**
 * 获取任务类型文本
 */
function getTaskTypeText(type: string): string {
  const map: Record<string, string> = {
    unlock: '账号解锁',
    reset_password: '密码重置',
    setup_2fa: '2FA 设置'
  }
  return map[type] || type
}

/**
 * 获取优先级颜色
 */
function getPriorityColor(priority: string): string {
  const map: Record<string, string> = {
    low: 'info',
    normal: '',
    high: 'warning',
    urgent: 'danger'
  }
  return map[priority] || ''
}

/**
 * 获取优先级文本
 */
function getPriorityText(priority: string): string {
  const map: Record<string, string> = {
    low: '低',
    normal: '普通',
    high: '高',
    urgent: '紧急'
  }
  return map[priority] || priority
}

/**
 * 获取日志类型
 */
function getLogType(level: string): 'primary' | 'success' | 'warning' | 'danger' | 'info' {
  const map: Record<string, any> = {
    info: 'primary',
    warning: 'warning',
    error: 'danger'
  }
  return map[level] || 'info'
}

/**
 * 返回上一页
 */
function handleBack() {
  router.push('/tasks')
}

// ==================== 自动刷新 ====================

/**
 * 启动自动刷新（处理中的任务）
 */
function startAutoRefresh() {
  if (['pending', 'processing'].includes(taskDetail.value.status)) {
    refreshTimer = setInterval(() => {
      loadTaskDetail()
    }, 5000) // 每 5 秒刷新一次
  }
}

/**
 * 停止自动刷新
 */
function stopAutoRefresh() {
  if (refreshTimer) {
    clearInterval(refreshTimer)
    refreshTimer = null
  }
}

// ==================== 生命周期 ====================

onMounted(async () => {
  await loadTaskDetail()
  startAutoRefresh()
})

onUnmounted(() => {
  stopAutoRefresh()
})
</script>

<style scoped lang="scss">
.task-detail-view {
  padding: 20px;
  min-height: 100vh;
  background-color: #f5f7fa;
}

.detail-container {
  max-width: 1400px;
  margin: 0 auto;
  display: flex;
  flex-direction: column;
  gap: 20px;
}

/* 卡片通用样式 */
.el-card {
  border-radius: 8px;

  :deep(.el-card__header) {
    background-color: #fafafa;
    border-bottom: 1px solid #e8e8e8;
  }
}

.card-header {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 16px;
  font-weight: 500;
  color: #303133;

  .header-actions {
    margin-left: auto;
  }
}

/* Apple ID 单元格 */
.apple-id-cell {
  display: flex;
  align-items: center;
  gap: 8px;

  .el-icon {
    color: #409eff;
  }
}

/* 进度卡片 */
.progress-content {
  padding: 10px 0;
}

.progress-info {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;

  .progress-label {
    font-size: 14px;
    color: #606266;
  }

  .progress-percentage {
    font-size: 18px;
    font-weight: 600;
    color: #409eff;
  }
}

.current-step {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 15px;
  padding: 12px;
  background-color: #ecf5ff;
  border-radius: 4px;
  color: #409eff;
  font-size: 14px;
}

.progress-description {
  margin-top: 20px;
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.step-item {
  display: flex;
  align-items: flex-start;
  gap: 12px;

  .step-icon {
    width: 32px;
    height: 32px;
    border-radius: 50%;
    background-color: #e4e7ed;
    color: #909399;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 14px;
    font-weight: 600;
    flex-shrink: 0;

    &.active {
      background-color: #409eff;
      color: white;
    }

    &.completed {
      background-color: #67c23a;
      color: white;
    }
  }

  .step-content {
    flex: 1;
    padding-top: 4px;

    .step-title {
      font-size: 14px;
      font-weight: 500;
      color: #303133;
      margin-bottom: 4px;
    }

    .step-desc {
      font-size: 13px;
      color: #909399;
      line-height: 1.5;
    }
  }
}

/* 日志卡片 */
.logs-content {
  max-height: 500px;
  overflow-y: auto;

  &::-webkit-scrollbar {
    width: 6px;
  }

  &::-webkit-scrollbar-thumb {
    background-color: #dcdfe6;
    border-radius: 3px;

    &:hover {
      background-color: #c0c4cc;
    }
  }
}

.log-item {
  display: flex;
  align-items: flex-start;
  gap: 12px;

  .log-level {
    padding: 2px 8px;
    border-radius: 3px;
    font-size: 12px;
    font-weight: 600;
    white-space: nowrap;

    &.log-level--info {
      background-color: #ecf5ff;
      color: #409eff;
    }

    &.log-level--warning {
      background-color: #fdf6ec;
      color: #e6a23c;
    }

    &.log-level--error {
      background-color: #fef0f0;
      color: #f56c6c;
    }
  }

  .log-message {
    flex: 1;
    font-size: 14px;
    color: #606266;
    line-height: 1.6;
    word-break: break-word;
  }
}

/* 结果卡片 */
.result-content {
  :deep(.el-result) {
    padding: 20px 0;
  }

  .error-detail {
    text-align: left;

    p {
      margin: 0 0 10px 0;
    }

    pre {
      background-color: #f5f7fa;
      padding: 15px;
      border-radius: 4px;
      font-size: 13px;
      line-height: 1.6;
      overflow-x: auto;
      color: #303133;
    }
  }

  .suggestions {
    margin-top: 20px;
    text-align: left;

    h4 {
      font-size: 16px;
      color: #303133;
      margin: 0 0 10px 0;
    }

    ul {
      margin: 0;
      padding-left: 20px;

      li {
        font-size: 14px;
        color: #606266;
        line-height: 1.8;
      }
    }
  }
}

/* 响应式设计 */
@media screen and (max-width: 768px) {
  .task-detail-view {
    padding: 10px;
  }

  .detail-container {
    gap: 15px;
  }

  :deep(.el-descriptions) {
    .el-descriptions__label {
      width: 100px !important;
    }
  }

  .progress-description {
    gap: 10px;
  }

  .step-item {
    .step-icon {
      width: 28px;
      height: 28px;
      font-size: 12px;
    }

    .step-content {
      .step-title {
        font-size: 13px;
      }

      .step-desc {
        font-size: 12px;
      }
    }
  }

  .log-item {
    flex-direction: column;
    gap: 8px;
  }
}

@media screen and (max-width: 480px) {
  .task-detail-view {
    padding: 5px;
  }

  .card-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 10px;

    .header-actions {
      width: 100%;
      margin-left: 0;

      .el-radio-group {
        width: 100%;
        display: flex;

        .el-radio-button {
          flex: 1;
        }
      }
    }
  }

  :deep(.el-descriptions) {
    font-size: 13px;
  }

  .progress-info {
    .progress-label {
      font-size: 13px;
    }

    .progress-percentage {
      font-size: 16px;
    }
  }
}
</style>
