<!--
  任务列表页面

  职责：
  - 显示用户的解锁任务列表
  - 支持搜索和筛选（状态、任务类型）
  - 支持创建新任务
  - 支持取消任务
  - 支持查看任务详情
  - 显示任务统计信息

  上游依赖：
  - PageHeader（页面标题组件）
  - DataTable（表格组件）
  - StatusTag（状态标签组件）
  - FormDialog（表单对话框组件）
  - Vue Router（页面跳转）
  - Element Plus（UI 组件）

  下游调用者：
  - 路由（/tasks）
  - Dashboard（查看全部任务链接）
  - 侧边栏导航
-->

<template>
  <div class="task-list-view">
    <!-- 页面标题 -->
    <PageHeader
      title="任务管理"
      description="管理您的解锁任务"
      :breadcrumbs="[
        { title: '首页', path: '/' },
        { title: '任务管理' }
      ]"
    >
      <template #actions>
        <el-button type="primary" :icon="Plus" @click="handleCreate">
          创建任务
        </el-button>
        <el-button :icon="Refresh" @click="handleRefresh">刷新</el-button>
      </template>
    </PageHeader>

    <!-- 统计卡片 -->
    <div class="stats-row">
      <div class="stat-card stat-card--total">
        <div class="stat-icon">
          <el-icon :size="28"><Document /></el-icon>
        </div>
        <div class="stat-content">
          <div class="stat-label">总任务数</div>
          <div class="stat-value">{{ stats.total }}</div>
        </div>
      </div>
      <div class="stat-card stat-card--processing">
        <div class="stat-icon">
          <el-icon :size="28"><Loading /></el-icon>
        </div>
        <div class="stat-content">
          <div class="stat-label">进行中</div>
          <div class="stat-value">{{ stats.processing }}</div>
        </div>
      </div>
      <div class="stat-card stat-card--completed">
        <div class="stat-icon">
          <el-icon :size="28"><CircleCheck /></el-icon>
        </div>
        <div class="stat-content">
          <div class="stat-label">已完成</div>
          <div class="stat-value">{{ stats.completed }}</div>
        </div>
      </div>
      <div class="stat-card stat-card--failed">
        <div class="stat-icon">
          <el-icon :size="28"><CircleClose /></el-icon>
        </div>
        <div class="stat-content">
          <div class="stat-label">失败</div>
          <div class="stat-value">{{ stats.failed }}</div>
        </div>
      </div>
    </div>

    <!-- 数据表格 -->
    <div class="table-card">
      <DataTable
        :data="taskList"
        :columns="tableColumns"
        :loading="loading"
        :total="total"
        :current-page="currentPage"
        :page-size="pageSize"
        :show-selection="true"
        :show-toolbar="true"
        :show-search="true"
        :show-refresh="true"
        :show-batch-actions="true"
        :batch-actions="batchActions"
        :action-buttons="actionButtons"
        pagination-mode="server"
        @search="handleSearch"
        @refresh="handleRefresh"
        @page-change="handlePageChange"
        @size-change="handleSizeChange"
        @batch-action="handleBatchAction"
        @row-action="handleRowAction"
        @row-click="handleRowClick"
      >
        <!-- 自定义列：任务类型 -->
        <template #column-task_type="{ row }">
          <el-tag :type="getTaskTypeTagType(row.task_type)">
            {{ row.task_type }}
          </el-tag>
        </template>

        <!-- 自定义列：状态 -->
        <template #column-status="{ row }">
          <StatusTag :status="row.status" :text="row.statusText" />
        </template>

        <!-- 自定义列：进度 -->
        <template #column-progress="{ row }">
          <el-progress
            :percentage="row.progress"
            :status="getProgressStatus(row.status)"
            :stroke-width="8"
          />
        </template>

        <!-- 工具栏自定义操作 -->
        <template #toolbar-actions>
          <el-select
            v-model="filterStatus"
            placeholder="筛选状态"
            clearable
            style="width: 150px; margin-right: 12px"
            @change="handleFilterChange"
          >
            <el-option label="全部" value="" />
            <el-option label="待开始" value="pending" />
            <el-option label="进行中" value="processing" />
            <el-option label="已完成" value="completed" />
            <el-option label="失败" value="failed" />
            <el-option label="已取消" value="cancelled" />
          </el-select>

          <el-select
            v-model="filterTaskType"
            placeholder="任务类型"
            clearable
            style="width: 150px"
            @change="handleFilterChange"
          >
            <el-option label="全部" value="" />
            <el-option label="账号解锁" value="账号解锁" />
            <el-option label="密码重置" value="密码重置" />
            <el-option label="2FA 设置" value="2FA 设置" />
          </el-select>
        </template>
      </DataTable>
    </div>

    <!-- 创建任务对话框 -->
    <FormDialog
      v-model="createDialogVisible"
      title="创建解锁任务"
      :fields="createFormFields"
      :initial-data="currentTask"
      :rules="createFormRules"
      @submit="handleSubmit"
      @cancel="handleCancelCreate"
    />

    <!-- 任务详情对话框 -->
    <el-dialog
      v-model="detailDialogVisible"
      title="任务详情"
      width="700px"
      :close-on-click-modal="false"
    >
      <div v-if="currentTaskDetail" class="task-detail">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="任务ID">
            {{ currentTaskDetail.id }}
          </el-descriptions-item>
          <el-descriptions-item label="任务类型">
            <el-tag :type="getTaskTypeTagType(currentTaskDetail.task_type)">
              {{ currentTaskDetail.task_type }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="Apple ID">
            {{ currentTaskDetail.apple_id }}
          </el-descriptions-item>
          <el-descriptions-item label="状态">
            <StatusTag :status="currentTaskDetail.status" :text="currentTaskDetail.statusText" />
          </el-descriptions-item>
          <el-descriptions-item label="进度">
            <el-progress
              :percentage="currentTaskDetail.progress"
              :status="getProgressStatus(currentTaskDetail.status)"
            />
          </el-descriptions-item>
          <el-descriptions-item label="优先级">
            <el-tag :type="getPriorityTagType(currentTaskDetail.priority)">
              {{ getPriorityText(currentTaskDetail.priority) }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="创建时间">
            {{ currentTaskDetail.created_at }}
          </el-descriptions-item>
          <el-descriptions-item label="开始时间">
            {{ currentTaskDetail.started_at || '-' }}
          </el-descriptions-item>
          <el-descriptions-item label="完成时间">
            {{ currentTaskDetail.finished_at || '-' }}
          </el-descriptions-item>
          <el-descriptions-item label="耗时">
            {{ currentTaskDetail.duration || '-' }}
          </el-descriptions-item>
          <el-descriptions-item label="结果" :span="2">
            <div class="task-result">
              {{ currentTaskDetail.result || '等待执行' }}
            </div>
          </el-descriptions-item>
        </el-descriptions>

        <!-- 任务日志 -->
        <div class="task-logs">
          <h4>执行日志</h4>
          <el-timeline>
            <el-timeline-item
              v-for="(log, index) in currentTaskDetail.logs"
              :key="index"
              :timestamp="log.time"
              :type="log.type"
            >
              {{ log.message }}
            </el-timeline-item>
          </el-timeline>
          <el-empty v-if="!currentTaskDetail.logs || currentTaskDetail.logs.length === 0" description="暂无日志" />
        </div>
      </div>

      <template #footer>
        <el-button @click="detailDialogVisible = false">关闭</el-button>
        <el-button
          v-if="currentTaskDetail?.status === 'processing' || currentTaskDetail?.status === 'pending'"
          type="danger"
          @click="handleCancelTask(currentTaskDetail)"
        >
          取消任务
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox, type FormRules } from 'element-plus'
import {
  Plus,
  Refresh,
  Document,
  Loading,
  CircleCheck,
  CircleClose,
  View,
  Delete
} from '@element-plus/icons-vue'
import PageHeader from '@/components/common/PageHeader.vue'
import DataTable from '@/components/common/DataTable.vue'
import StatusTag from '@/components/common/StatusTag.vue'
import FormDialog from '@/components/common/FormDialog.vue'
import type { TableColumn, ActionButton, BatchAction } from '@/components/common/DataTable.vue'
import type { FormField } from '@/components/common/FormDialog.vue'

const router = useRouter()

/**
 * 统计数据
 */
const stats = reactive({
  total: 0,
  processing: 0,
  completed: 0,
  failed: 0
})

/**
 * 表格列配置
 */
const tableColumns: TableColumn[] = [
  { prop: 'id', label: 'ID', width: '80', sortable: true },
  { prop: 'apple_id', label: 'Apple ID', minWidth: '200' },
  { prop: 'task_type', label: '任务类型', width: '120' },
  { prop: 'status', label: '状态', width: '120' },
  { prop: 'progress', label: '进度', width: '150' },
  { prop: 'created_at', label: '创建时间', width: '180', sortable: true },
  { prop: 'finished_at', label: '完成时间', width: '180' }
]

/**
 * 操作按钮配置
 */
const actionButtons: ActionButton[] = [
  { key: 'view', label: '查看', type: 'primary', icon: 'View' },
  {
    key: 'cancel',
    label: '取消',
    type: 'danger',
    icon: 'Close',
    disabled: (row: any) => row.status !== 'processing' && row.status !== 'pending'
  }
]

/**
 * 批量操作配置
 */
const batchActions: BatchAction[] = [
  { key: 'cancel', label: '批量取消', icon: 'Close' },
  { key: 'delete', label: '批量删除', icon: 'Delete' }
]

/**
 * 创建任务表单字段
 */
const createFormFields: FormField[] = [
  {
    prop: 'account_id',
    label: '选择账号',
    type: 'select',
    required: true,
    placeholder: '请选择要解锁的账号',
    options: [] // 动态加载
  },
  {
    prop: 'task_type',
    label: '任务类型',
    type: 'select',
    required: true,
    placeholder: '请选择任务类型',
    options: [
      { label: '账号解锁', value: '账号解锁' },
      { label: '密码重置', value: '密码重置' },
      { label: '2FA 设置', value: '2FA 设置' }
    ]
  },
  {
    prop: 'priority',
    label: '优先级',
    type: 'select',
    required: false,
    placeholder: '请选择优先级（默认普通）',
    options: [
      { label: '低', value: 'low' },
      { label: '普通', value: 'normal' },
      { label: '高', value: 'high' },
      { label: '紧急', value: 'urgent' }
    ]
  },
  {
    prop: 'note',
    label: '备注',
    type: 'textarea',
    required: false,
    placeholder: '请输入备注信息（可选）',
    rows: 3
  }
]

/**
 * 创建任务表单验证规则
 */
const createFormRules: FormRules = {
  account_id: [
    { required: true, message: '请选择账号', trigger: 'change' }
  ],
  task_type: [
    { required: true, message: '请选择任务类型', trigger: 'change' }
  ]
}

/**
 * 任务列表数据
 */
const taskList = ref<any[]>([])

/**
 * 加载状态
 */
const loading = ref(false)

/**
 * 总数
 */
const total = ref(0)

/**
 * 当前页
 */
const currentPage = ref(1)

/**
 * 每页大小
 */
const pageSize = ref(20)

/**
 * 搜索关键词
 */
const searchKeyword = ref('')

/**
 * 筛选状态
 */
const filterStatus = ref('')

/**
 * 筛选任务类型
 */
const filterTaskType = ref('')

/**
 * 创建对话框可见性
 */
const createDialogVisible = ref(false)

/**
 * 当前任务
 */
const currentTask = ref<any>(null)

/**
 * 详情对话框可见性
 */
const detailDialogVisible = ref(false)

/**
 * 当前任务详情
 */
const currentTaskDetail = ref<any>(null)

/**
 * 加载统计数据
 */
async function loadStats() {
  try {
    // TODO: 调用 API 获取统计数据
    // import { getTaskStatsApi } from '@/api/tasks'
    // const data = await getTaskStatsApi()

    // Mock 数据
    stats.total = 156
    stats.processing = 3
    stats.completed = 145
    stats.failed = 8
  } catch (error) {
    console.error('[TaskListView] Load stats error:', error)
  }
}

/**
 * 加载任务列表
 */
async function loadTaskList() {
  try {
    loading.value = true

    // TODO: 调用 API 获取任务列表
    // import { getTaskListApi } from '@/api/tasks'
    // const response = await getTaskListApi({
    //   page: currentPage.value,
    //   page_size: pageSize.value,
    //   keyword: searchKeyword.value,
    //   status: filterStatus.value,
    //   task_type: filterTaskType.value
    // })
    // taskList.value = response.items
    // total.value = response.total

    // Mock 数据
    await new Promise(resolve => setTimeout(resolve, 500))

    const mockTasks = [
      {
        id: 1,
        apple_id: 'user1@icloud.com',
        task_type: '账号解锁',
        status: 'processing',
        statusText: '进行中',
        progress: 65,
        priority: 'high',
        created_at: '2025-11-21 14:00:00',
        started_at: '2025-11-21 14:05:00',
        finished_at: null
      },
      {
        id: 2,
        apple_id: 'user2@icloud.com',
        task_type: '密码重置',
        status: 'completed',
        statusText: '已完成',
        progress: 100,
        priority: 'normal',
        created_at: '2025-11-21 10:30:00',
        started_at: '2025-11-21 10:35:00',
        finished_at: '2025-11-21 10:45:00'
      },
      {
        id: 3,
        apple_id: 'user3@icloud.com',
        task_type: '账号解锁',
        status: 'failed',
        statusText: '失败',
        progress: 30,
        priority: 'normal',
        created_at: '2025-11-20 16:20:00',
        started_at: '2025-11-20 16:25:00',
        finished_at: '2025-11-20 16:30:00'
      },
      {
        id: 4,
        apple_id: 'user4@icloud.com',
        task_type: '2FA 设置',
        status: 'pending',
        statusText: '待开始',
        progress: 0,
        priority: 'low',
        created_at: '2025-11-21 15:00:00',
        started_at: null,
        finished_at: null
      }
    ]

    // 应用筛选
    let filteredTasks = mockTasks
    if (filterStatus.value) {
      filteredTasks = mockTasks.filter(task => task.status === filterStatus.value)
    }
    if (filterTaskType.value) {
      filteredTasks = filteredTasks.filter(task => task.task_type === filterTaskType.value)
    }
    if (searchKeyword.value) {
      filteredTasks = filteredTasks.filter(task =>
        task.apple_id.toLowerCase().includes(searchKeyword.value.toLowerCase())
      )
    }

    taskList.value = filteredTasks
    total.value = filteredTasks.length
  } catch (error) {
    console.error('[TaskListView] Load tasks error:', error)
    ElMessage.error('加载任务列表失败')
  } finally {
    loading.value = false
  }
}

/**
 * 搜索处理
 */
function handleSearch(keyword: string) {
  searchKeyword.value = keyword
  currentPage.value = 1
  loadTaskList()
}

/**
 * 刷新处理
 */
async function handleRefresh() {
  currentPage.value = 1
  searchKeyword.value = ''
  filterStatus.value = ''
  filterTaskType.value = ''
  await Promise.all([loadStats(), loadTaskList()])
}

/**
 * 分页变化
 */
function handlePageChange(page: number) {
  currentPage.value = page
  loadTaskList()
}

/**
 * 每页大小变化
 */
function handleSizeChange(size: number) {
  pageSize.value = size
  currentPage.value = 1
  loadTaskList()
}

/**
 * 筛选变化
 */
function handleFilterChange() {
  currentPage.value = 1
  loadTaskList()
}

/**
 * 创建任务
 */
async function handleCreate() {
  // TODO: 加载账号列表
  // import { getAccountListApi } from '@/api/accounts'
  // const accounts = await getAccountListApi({ page_size: 100 })
  // createFormFields[0].options = accounts.items.map(acc => ({
  //   label: acc.apple_id,
  //   value: acc.id
  // }))

  // Mock 数据
  createFormFields[0].options = [
    { label: 'user1@icloud.com', value: 1 },
    { label: 'user2@icloud.com', value: 2 },
    { label: 'user3@icloud.com', value: 3 }
  ]

  currentTask.value = null
  createDialogVisible.value = true
}

/**
 * 批量操作
 */
async function handleBatchAction(actionKey: string, rows: any[]) {
  switch (actionKey) {
    case 'cancel':
      await handleBatchCancel(rows)
      break
    case 'delete':
      await handleBatchDelete(rows)
      break
  }
}

/**
 * 批量取消
 */
async function handleBatchCancel(rows: any[]) {
  try {
    const validRows = rows.filter(r => r.status === 'processing' || r.status === 'pending')
    if (validRows.length === 0) {
      ElMessage.warning('没有可取消的任务')
      return
    }

    await ElMessageBox.confirm(
      `确定要取消选中的 ${validRows.length} 个任务吗？`,
      '批量取消',
      {
        type: 'warning',
        confirmButtonText: '确定',
        cancelButtonText: '取消'
      }
    )

    // TODO: 调用批量取消 API
    // import { batchCancelTasksApi } from '@/api/tasks'
    // await batchCancelTasksApi({ ids: validRows.map(r => r.id) })

    ElMessage.success('取消成功')
    loadTaskList()
    loadStats()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('[TaskListView] Batch cancel error:', error)
      ElMessage.error('取消失败')
    }
  }
}

/**
 * 批量删除
 */
async function handleBatchDelete(rows: any[]) {
  try {
    await ElMessageBox.confirm(
      `确定要删除选中的 ${rows.length} 个任务吗？此操作不可恢复。`,
      '批量删除',
      {
        type: 'warning',
        confirmButtonText: '确定删除',
        cancelButtonText: '取消'
      }
    )

    // TODO: 调用批量删除 API
    // import { batchDeleteTasksApi } from '@/api/tasks'
    // await batchDeleteTasksApi({ ids: rows.map(r => r.id) })

    ElMessage.success('删除成功')
    loadTaskList()
    loadStats()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('[TaskListView] Batch delete error:', error)
      ElMessage.error('删除失败')
    }
  }
}

/**
 * 行操作
 */
async function handleRowAction(actionKey: string, row: any) {
  switch (actionKey) {
    case 'view':
      await handleViewDetail(row)
      break
    case 'cancel':
      await handleCancelTask(row)
      break
  }
}

/**
 * 查看详情
 */
async function handleViewDetail(row: any) {
  try {
    // TODO: 调用 API 获取任务详情
    // import { getTaskDetailApi } from '@/api/tasks'
    // currentTaskDetail.value = await getTaskDetailApi(row.id)

    // Mock 数据
    currentTaskDetail.value = {
      ...row,
      duration: '5分32秒',
      result: row.status === 'completed' ? '解锁成功' : row.status === 'failed' ? '解锁失败：密码错误' : null,
      logs: [
        { time: '2025-11-21 14:05:00', message: '任务开始执行', type: 'primary' },
        { time: '2025-11-21 14:05:15', message: '正在连接 Apple 服务器', type: 'info' },
        { time: '2025-11-21 14:05:30', message: '验证账号信息', type: 'info' },
        { time: '2025-11-21 14:06:00', message: '正在解锁账号', type: 'warning' }
      ]
    }

    detailDialogVisible.value = true
  } catch (error) {
    console.error('[TaskListView] Get task detail error:', error)
    ElMessage.error('获取任务详情失败')
  }
}

/**
 * 取消任务
 */
async function handleCancelTask(row: any) {
  try {
    await ElMessageBox.confirm(
      `确定要取消任务 ${row.id} 吗？`,
      '取消任务',
      {
        type: 'warning',
        confirmButtonText: '确定',
        cancelButtonText: '取消'
      }
    )

    // TODO: 调用取消任务 API
    // import { cancelTaskApi } from '@/api/tasks'
    // await cancelTaskApi(row.id)

    ElMessage.success('任务已取消')
    detailDialogVisible.value = false
    loadTaskList()
    loadStats()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('[TaskListView] Cancel task error:', error)
      ElMessage.error('取消任务失败')
    }
  }
}

/**
 * 行点击
 */
async function handleRowClick(row: any) {
  await handleViewDetail(row)
}

/**
 * 表单提交
 */
async function handleSubmit(data: any) {
  try {
    // TODO: 调用创建任务 API
    // import { createTaskApi } from '@/api/tasks'
    // await createTaskApi(data)

    ElMessage.success('任务创建成功')
    createDialogVisible.value = false
    loadTaskList()
    loadStats()
  } catch (error) {
    console.error('[TaskListView] Submit error:', error)
    throw error
  }
}

/**
 * 取消创建
 */
function handleCancelCreate() {
  createDialogVisible.value = false
  currentTask.value = null
}

/**
 * 获取任务类型标签类型
 */
function getTaskTypeTagType(taskType: string): string {
  const typeMap: Record<string, string> = {
    '账号解锁': 'primary',
    '密码重置': 'warning',
    '2FA 设置': 'success'
  }
  return typeMap[taskType] || ''
}

/**
 * 获取进度条状态
 */
function getProgressStatus(status: string): 'success' | 'exception' | undefined {
  if (status === 'completed') return 'success'
  if (status === 'failed') return 'exception'
  return undefined
}

/**
 * 获取优先级标签类型
 */
function getPriorityTagType(priority: string): string {
  const priorityMap: Record<string, string> = {
    low: 'info',
    normal: '',
    high: 'warning',
    urgent: 'danger'
  }
  return priorityMap[priority] || ''
}

/**
 * 获取优先级文本
 */
function getPriorityText(priority: string): string {
  const textMap: Record<string, string> = {
    low: '低',
    normal: '普通',
    high: '高',
    urgent: '紧急'
  }
  return textMap[priority] || priority
}

/**
 * 组件挂载
 */
onMounted(async () => {
  await Promise.all([loadStats(), loadTaskList()])
})
</script>

<style scoped lang="scss">
.task-list-view {
  padding: 20px;

  .stats-row {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 16px;
    margin-bottom: 24px;

    .stat-card {
      display: flex;
      align-items: center;
      gap: 16px;
      padding: 20px;
      background: #fff;
      border-radius: 8px;
      box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);

      .stat-icon {
        flex-shrink: 0;
        width: 56px;
        height: 56px;
        display: flex;
        align-items: center;
        justify-content: center;
        border-radius: 12px;
        color: #fff;
      }

      &.stat-card--total .stat-icon {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
      }

      &.stat-card--processing .stat-icon {
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
      }

      &.stat-card--completed .stat-icon {
        background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%);
      }

      &.stat-card--failed .stat-icon {
        background: linear-gradient(135deg, #fa709a 0%, #fee140 100%);
      }

      .stat-content {
        flex: 1;

        .stat-label {
          margin-bottom: 8px;
          font-size: 14px;
          color: #909399;
        }

        .stat-value {
          font-size: 28px;
          font-weight: 700;
          color: #303133;
          line-height: 1;
        }
      }
    }
  }

  .table-card {
    background: #fff;
    border-radius: 8px;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
    padding: 16px;
  }

  .task-detail {
    .task-result {
      padding: 12px;
      background: #f5f7fa;
      border-radius: 4px;
      font-size: 14px;
      color: #606266;
    }

    .task-logs {
      margin-top: 24px;

      h4 {
        margin: 0 0 16px;
        font-size: 16px;
        font-weight: 600;
        color: #303133;
      }
    }
  }
}

// 响应式设计
@media (max-width: 1200px) {
  .task-list-view {
    .stats-row {
      grid-template-columns: repeat(2, 1fr);
    }
  }
}

@media (max-width: 768px) {
  .task-list-view {
    padding: 16px;

    .stats-row {
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

        .stat-content .stat-value {
          font-size: 24px;
        }
      }
    }
  }
}

@media (max-width: 480px) {
  .task-list-view {
    padding: 12px;

    .stats-row {
      grid-template-columns: 1fr;
      gap: 12px;
    }

    .table-card {
      padding: 12px;
    }
  }
}
</style>
