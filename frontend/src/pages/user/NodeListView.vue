<!--
  节点管理页面

  职责：
  - 显示用户的解锁节点列表
  - 支持注册新节点
  - 支持删除节点
  - 显示节点状态（在线/离线/繁忙）
  - 显示节点性能信息（CPU/内存使用率、任务队列）
  - 显示心跳信息

  上游依赖：
  - PageHeader（页面标题组件）
  - DataTable（表格组件）
  - StatusTag（状态标签组件）
  - FormDialog（表单对话框组件）
  - Vue Router（页面跳转）
  - Element Plus（UI 组件）
  - node API（节点相关接口）

  下游调用者：
  - 路由（/nodes）
  - Dashboard（快捷操作）
  - 侧边栏导航

  使用的 API：
  - GET /nodes - 获取节点列表
  - POST /nodes/register - 注册节点
  - DELETE /nodes/{id} - 删除节点
-->

<template>
  <div class="node-list-view">
    <!-- 页面标题 -->
    <PageHeader
      title="节点管理"
      description="管理您的解锁节点，监控节点状态和性能"
      :breadcrumbs="[
        { title: '首页', path: '/' },
        { title: '节点管理' }
      ]"
    >
      <template #actions>
        <el-button type="primary" :icon="Plus" @click="handleAdd">
          注册节点
        </el-button>
        <el-button :icon="Refresh" @click="handleRefresh">刷新状态</el-button>
      </template>
    </PageHeader>

    <!-- 统计卡片 -->
    <el-row :gutter="20" class="stats-row">
      <el-col :xs="12" :sm="6">
        <div class="stat-card stat-card-total">
          <div class="stat-icon">
            <el-icon><Monitor /></el-icon>
          </div>
          <div class="stat-content">
            <div class="stat-value">{{ stats.total }}</div>
            <div class="stat-label">节点总数</div>
          </div>
        </div>
      </el-col>
      <el-col :xs="12" :sm="6">
        <div class="stat-card stat-card-online">
          <div class="stat-icon">
            <el-icon><CircleCheck /></el-icon>
          </div>
          <div class="stat-content">
            <div class="stat-value">{{ stats.online }}</div>
            <div class="stat-label">在线节点</div>
          </div>
        </div>
      </el-col>
      <el-col :xs="12" :sm="6">
        <div class="stat-card stat-card-busy">
          <div class="stat-icon">
            <el-icon><Loading /></el-icon>
          </div>
          <div class="stat-content">
            <div class="stat-value">{{ stats.busy }}</div>
            <div class="stat-label">繁忙节点</div>
          </div>
        </div>
      </el-col>
      <el-col :xs="12" :sm="6">
        <div class="stat-card stat-card-offline">
          <div class="stat-icon">
            <el-icon><CircleClose /></el-icon>
          </div>
          <div class="stat-content">
            <div class="stat-value">{{ stats.offline }}</div>
            <div class="stat-label">离线节点</div>
          </div>
        </div>
      </el-col>
    </el-row>

    <!-- 数据表格 -->
    <div class="table-card">
      <DataTable
        :data="nodeList"
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
      >
        <!-- 自定义列：节点名称 -->
        <template #column-name="{ row }">
          <div class="node-name-cell">
            <el-icon class="node-icon" :class="getStatusClass(row.status)">
              <Monitor />
            </el-icon>
            <span class="name-text">{{ row.name }}</span>
          </div>
        </template>

        <!-- 自定义列：状态 -->
        <template #column-status="{ row }">
          <el-tag :type="getStatusTagType(row.status)" effect="dark" round>
            <span class="status-dot" :class="getStatusClass(row.status)"></span>
            {{ getStatusText(row.status) }}
          </el-tag>
        </template>

        <!-- 自定义列：CPU使用率 -->
        <template #column-cpu_usage="{ row }">
          <div class="usage-cell">
            <el-progress
              :percentage="row.cpu_usage"
              :status="getUsageStatus(row.cpu_usage)"
              :stroke-width="6"
              :show-text="false"
              style="width: 60px; display: inline-block; margin-right: 8px;"
            />
            <span :class="['usage-text', getUsageClass(row.cpu_usage)]">
              {{ row.cpu_usage.toFixed(1) }}%
            </span>
          </div>
        </template>

        <!-- 自定义列：内存使用率 -->
        <template #column-memory_usage="{ row }">
          <div class="usage-cell">
            <el-progress
              :percentage="row.memory_usage"
              :status="getUsageStatus(row.memory_usage)"
              :stroke-width="6"
              :show-text="false"
              style="width: 60px; display: inline-block; margin-right: 8px;"
            />
            <span :class="['usage-text', getUsageClass(row.memory_usage)]">
              {{ row.memory_usage.toFixed(1) }}%
            </span>
          </div>
        </template>

        <!-- 自定义列：任务队列 -->
        <template #column-task_queue_length="{ row }">
          <el-badge
            :value="row.task_queue_length"
            :type="row.task_queue_length > 10 ? 'danger' : row.task_queue_length > 5 ? 'warning' : 'primary'"
            class="task-badge"
          />
        </template>

        <!-- 自定义列：IP地址 -->
        <template #column-ip_address="{ row }">
          <span class="ip-address">{{ row.ip_address }}</span>
        </template>

        <!-- 自定义列：最后心跳 -->
        <template #column-last_heartbeat_at="{ row }">
          <div class="heartbeat-cell">
            <span v-if="row.last_heartbeat_at" :class="{ 'heartbeat-warning': isHeartbeatStale(row.last_heartbeat_at) }">
              {{ formatRelativeTime(row.last_heartbeat_at) }}
            </span>
            <span v-else class="no-data">-</span>
          </div>
        </template>

        <!-- 工具栏自定义操作 -->
        <template #toolbar-actions>
          <el-select
            v-model="filterStatus"
            placeholder="筛选状态"
            clearable
            style="width: 130px"
            @change="handleFilterChange"
          >
            <el-option label="全部状态" value="" />
            <el-option label="在线" value="online" />
            <el-option label="离线" value="offline" />
            <el-option label="繁忙" value="busy" />
          </el-select>
        </template>
      </DataTable>
    </div>

    <!-- 注册节点对话框 -->
    <el-dialog
      v-model="registerDialogVisible"
      title="注册新节点"
      width="500px"
      :close-on-click-modal="false"
    >
      <el-form
        ref="registerFormRef"
        :model="registerForm"
        :rules="registerRules"
        label-width="100px"
      >
        <el-form-item label="节点名称" prop="name">
          <el-input
            v-model="registerForm.name"
            placeholder="请输入节点名称"
            maxlength="50"
            show-word-limit
          />
        </el-form-item>
        <el-alert
          title="注册说明"
          type="info"
          :closable="false"
          show-icon
          style="margin-top: 16px;"
        >
          <template #default>
            <p>注册成功后，您将获得一个节点密钥（Node Key）。</p>
            <p>请在解锁节点程序中配置此密钥以连接到系统。</p>
          </template>
        </el-alert>
      </el-form>
      <template #footer>
        <el-button @click="registerDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="registerLoading" @click="handleRegisterSubmit">
          注册
        </el-button>
      </template>
    </el-dialog>

    <!-- 节点密钥对话框 -->
    <el-dialog
      v-model="keyDialogVisible"
      title="节点注册成功"
      width="500px"
      :close-on-click-modal="false"
    >
      <el-result icon="success" title="节点注册成功">
        <template #sub-title>
          <p>请复制以下节点密钥，配置到您的解锁节点程序中</p>
        </template>
        <template #extra>
          <div class="node-key-container">
            <el-input
              v-model="registeredNodeKey"
              readonly
              class="key-input"
            >
              <template #append>
                <el-button :icon="CopyDocument" @click="handleCopyKey">复制</el-button>
              </template>
            </el-input>
            <el-alert
              type="warning"
              :closable="false"
              show-icon
              style="margin-top: 16px;"
            >
              请妥善保管此密钥，关闭对话框后将无法再次查看！
            </el-alert>
          </div>
        </template>
      </el-result>
      <template #footer>
        <el-button type="primary" @click="handleKeyDialogClose">我已复制密钥</el-button>
      </template>
    </el-dialog>

    <!-- 节点详情对话框 -->
    <el-dialog
      v-model="detailDialogVisible"
      title="节点详情"
      width="600px"
    >
      <template v-if="currentNode">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="节点ID">{{ currentNode.id }}</el-descriptions-item>
          <el-descriptions-item label="节点名称">{{ currentNode.name }}</el-descriptions-item>
          <el-descriptions-item label="IP地址">{{ currentNode.ip_address }}</el-descriptions-item>
          <el-descriptions-item label="状态">
            <el-tag :type="getStatusTagType(currentNode.status)" effect="dark" round>
              {{ getStatusText(currentNode.status) }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="CPU使用率">
            <span :class="getUsageClass(currentNode.cpu_usage)">
              {{ currentNode.cpu_usage.toFixed(1) }}%
            </span>
          </el-descriptions-item>
          <el-descriptions-item label="内存使用率">
            <span :class="getUsageClass(currentNode.memory_usage)">
              {{ currentNode.memory_usage.toFixed(1) }}%
            </span>
          </el-descriptions-item>
          <el-descriptions-item label="任务队列">
            {{ currentNode.task_queue_length }} 个任务
          </el-descriptions-item>
          <el-descriptions-item label="最后心跳">
            {{ currentNode.last_heartbeat_at ? formatTime(currentNode.last_heartbeat_at) : '-' }}
          </el-descriptions-item>
          <el-descriptions-item label="创建时间" :span="2">
            {{ formatTime(currentNode.created_at) }}
          </el-descriptions-item>
        </el-descriptions>

        <!-- 性能图表区域（占位） -->
        <div class="performance-charts">
          <el-divider>性能监控</el-divider>
          <el-row :gutter="20">
            <el-col :span="12">
              <div class="chart-placeholder">
                <el-icon><DataAnalysis /></el-icon>
                <span>CPU 使用率趋势图</span>
                <p class="placeholder-tip">敬请期待</p>
              </div>
            </el-col>
            <el-col :span="12">
              <div class="chart-placeholder">
                <el-icon><PieChart /></el-icon>
                <span>内存使用率趋势图</span>
                <p class="placeholder-tip">敬请期待</p>
              </div>
            </el-col>
          </el-row>
        </div>
      </template>
      <template #footer>
        <el-button @click="detailDialogVisible = false">关闭</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted, onUnmounted } from 'vue'
import { ElMessage, ElMessageBox, type FormInstance, type FormRules } from 'element-plus'
import {
  Plus,
  Refresh,
  Monitor,
  CircleCheck,
  CircleClose,
  Loading,
  CopyDocument,
  View,
  Delete,
  DataAnalysis,
  PieChart
} from '@element-plus/icons-vue'
import PageHeader from '@/components/common/PageHeader.vue'
import DataTable from '@/components/common/DataTable.vue'
import {
  getNodeListApi,
  registerNodeApi,
  deleteNodeApi,
  type Node,
  type RegisterNodeRequest
} from '@/api/node'
import { formatDate, formatRelative } from '@/utils/date'

// ==================== 类型定义 ====================

interface Stats {
  total: number
  online: number
  offline: number
  busy: number
}

// ==================== 响应式数据 ====================

// 加载状态
const loading = ref(false)
const registerLoading = ref(false)

// 节点列表数据
const nodeList = ref<Node[]>([])
const total = ref(0)
const currentPage = ref(1)
const pageSize = ref(20)

// 筛选条件
const searchKeyword = ref('')
const filterStatus = ref('')

// 对话框状态
const registerDialogVisible = ref(false)
const keyDialogVisible = ref(false)
const detailDialogVisible = ref(false)
const currentNode = ref<Node | null>(null)
const registeredNodeKey = ref('')

// 表单引用
const registerFormRef = ref<FormInstance>()

// 注册表单
const registerForm = reactive<RegisterNodeRequest>({
  name: ''
})

// 表单验证规则
const registerRules: FormRules = {
  name: [
    { required: true, message: '请输入节点名称', trigger: 'blur' },
    { min: 2, max: 50, message: '节点名称长度在 2-50 字符', trigger: 'blur' }
  ]
}

// 自动刷新定时器
let refreshTimer: ReturnType<typeof setInterval> | null = null

// ==================== 计算属性 ====================

// 统计数据
const stats = computed<Stats>(() => {
  const list = nodeList.value
  return {
    total: total.value,
    online: list.filter(n => n.status === 'online').length,
    offline: list.filter(n => n.status === 'offline').length,
    busy: list.filter(n => n.status === 'busy').length
  }
})

// 表格列配置
const tableColumns = [
  { prop: 'id', label: 'ID', width: 80, sortable: true },
  { prop: 'name', label: '节点名称', minWidth: 150, slot: true },
  { prop: 'status', label: '状态', width: 110, slot: true },
  { prop: 'ip_address', label: 'IP地址', width: 140, slot: true },
  { prop: 'cpu_usage', label: 'CPU', width: 140, slot: true },
  { prop: 'memory_usage', label: '内存', width: 140, slot: true },
  { prop: 'task_queue_length', label: '任务队列', width: 100, slot: true, align: 'center' },
  { prop: 'last_heartbeat_at', label: '最后心跳', width: 130, slot: true }
]

// 操作按钮配置
const actionButtons = [
  { key: 'detail', label: '详情', icon: View, type: 'primary' },
  { key: 'delete', label: '删除', icon: Delete, type: 'danger' }
]

// 批量操作配置
const batchActions = [
  { key: 'delete', label: '批量删除', icon: 'Delete' }
]

// ==================== 方法 ====================

// 获取节点列表
async function fetchNodeList() {
  loading.value = true
  try {
    const params: Record<string, unknown> = {
      page: currentPage.value,
      size: pageSize.value
    }
    if (filterStatus.value) {
      params.status = filterStatus.value
    }
    if (searchKeyword.value) {
      params.keyword = searchKeyword.value
    }

    const res = await getNodeListApi(params)
    nodeList.value = res.items || []
    total.value = res.total || 0
  } catch (error) {
    console.error('获取节点列表失败:', error)
    ElMessage.error('获取节点列表失败')
  } finally {
    loading.value = false
  }
}

// 获取状态标签类型
function getStatusTagType(status: string): string {
  const map: Record<string, string> = {
    online: 'success',
    offline: 'danger',
    busy: 'warning'
  }
  return map[status] || 'info'
}

// 获取状态文本
function getStatusText(status: string): string {
  const map: Record<string, string> = {
    online: '在线',
    offline: '离线',
    busy: '繁忙'
  }
  return map[status] || '未知'
}

// 获取状态样式类
function getStatusClass(status: string): string {
  const map: Record<string, string> = {
    online: 'status-online',
    offline: 'status-offline',
    busy: 'status-busy'
  }
  return map[status] || ''
}

// 获取使用率状态
function getUsageStatus(usage: number): string {
  if (usage >= 90) return 'exception'
  if (usage >= 70) return 'warning'
  return 'success'
}

// 获取使用率样式类
function getUsageClass(usage: number): string {
  if (usage >= 90) return 'usage-danger'
  if (usage >= 70) return 'usage-warning'
  return 'usage-normal'
}

// 检查心跳是否过期（超过5分钟）
function isHeartbeatStale(time: string): boolean {
  const lastTime = new Date(time).getTime()
  const now = Date.now()
  return now - lastTime > 5 * 60 * 1000
}

// 格式化时间
function formatTime(time: string): string {
  return formatDate(time, 'YYYY-MM-DD HH:mm:ss')
}

// 格式化相对时间
function formatRelativeTime(time: string): string {
  return formatRelative(time)
}

// 处理搜索
function handleSearch(keyword: string) {
  searchKeyword.value = keyword
  currentPage.value = 1
  fetchNodeList()
}

// 处理刷新
function handleRefresh() {
  fetchNodeList()
}

// 处理分页变化
function handlePageChange(page: number) {
  currentPage.value = page
  fetchNodeList()
}

// 处理每页数量变化
function handleSizeChange(size: number) {
  pageSize.value = size
  currentPage.value = 1
  fetchNodeList()
}

// 处理筛选变化
function handleFilterChange() {
  currentPage.value = 1
  fetchNodeList()
}

// 处理添加节点
function handleAdd() {
  registerForm.name = ''
  registerDialogVisible.value = true
}

// 处理行操作
function handleRowAction(action: string, row: Node) {
  switch (action) {
    case 'detail':
      handleViewDetail(row)
      break
    case 'delete':
      handleDeleteNode(row)
      break
  }
}

// 查看节点详情
function handleViewDetail(row: Node) {
  currentNode.value = row
  detailDialogVisible.value = true
}

// 删除节点
async function handleDeleteNode(row: Node) {
  try {
    await ElMessageBox.confirm(
      `确定要删除节点 "${row.name}" 吗？删除后该节点将无法继续执行任务。`,
      '删除确认',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    await deleteNodeApi(row.id)
    ElMessage.success('删除成功')
    fetchNodeList()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除节点失败:', error)
      ElMessage.error('删除节点失败')
    }
  }
}

// 处理批量操作
async function handleBatchAction(action: string, selectedRows: Node[]) {
  if (!selectedRows || selectedRows.length === 0) {
    ElMessage.warning('请先选择要操作的节点')
    return
  }

  switch (action) {
    case 'delete':
      try {
        await ElMessageBox.confirm(
          `确定要删除选中的 ${selectedRows.length} 个节点吗？`,
          '批量删除确认',
          {
            confirmButtonText: '确定',
            cancelButtonText: '取消',
            type: 'warning'
          }
        )
        for (const row of selectedRows) {
          try {
            await deleteNodeApi(row.id)
          } catch {
            // 忽略单个失败
          }
        }
        ElMessage.success('批量删除完成')
        fetchNodeList()
      } catch {
        // 用户取消
      }
      break
  }
}

// 处理注册提交
async function handleRegisterSubmit() {
  if (!registerFormRef.value) return

  try {
    await registerFormRef.value.validate()
    registerLoading.value = true

    const res = await registerNodeApi(registerForm)
    registeredNodeKey.value = res.key
    registerDialogVisible.value = false
    keyDialogVisible.value = true
    fetchNodeList()
  } catch (error) {
    if (error !== false) {
      console.error('注册节点失败:', error)
      ElMessage.error('注册节点失败')
    }
  } finally {
    registerLoading.value = false
  }
}

// 复制节点密钥
async function handleCopyKey() {
  try {
    await navigator.clipboard.writeText(registeredNodeKey.value)
    ElMessage.success('密钥已复制到剪贴板')
  } catch {
    ElMessage.error('复制失败，请手动复制')
  }
}

// 关闭密钥对话框
function handleKeyDialogClose() {
  keyDialogVisible.value = false
  registeredNodeKey.value = ''
}

// 启动自动刷新
function startAutoRefresh() {
  refreshTimer = setInterval(() => {
    fetchNodeList()
  }, 30000) // 每30秒刷新一次
}

// 停止自动刷新
function stopAutoRefresh() {
  if (refreshTimer) {
    clearInterval(refreshTimer)
    refreshTimer = null
  }
}

// ==================== 生命周期 ====================

onMounted(() => {
  fetchNodeList()
  startAutoRefresh()
})

onUnmounted(() => {
  stopAutoRefresh()
})
</script>

<style lang="scss" scoped>
.node-list-view {
  padding: 0;
}

// 统计卡片
.stats-row {
  margin-bottom: 20px;
}

.stat-card {
  display: flex;
  align-items: center;
  padding: 20px;
  border-radius: 12px;
  background: white;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.05);
  transition: all 0.3s ease;

  &:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 16px rgba(0, 0, 0, 0.1);
  }

  .stat-icon {
    width: 50px;
    height: 50px;
    border-radius: 12px;
    display: flex;
    align-items: center;
    justify-content: center;
    margin-right: 16px;

    .el-icon {
      font-size: 24px;
      color: white;
    }
  }

  .stat-content {
    flex: 1;

    .stat-value {
      font-size: 24px;
      font-weight: 600;
      color: #303133;
      line-height: 1.2;
    }

    .stat-label {
      font-size: 13px;
      color: #909399;
      margin-top: 4px;
    }
  }

  &.stat-card-total .stat-icon {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  }

  &.stat-card-online .stat-icon {
    background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
  }

  &.stat-card-busy .stat-icon {
    background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
  }

  &.stat-card-offline .stat-icon {
    background: linear-gradient(135deg, #bdc3c7 0%, #7f8c8d 100%);
  }
}

// 表格卡片
.table-card {
  background: white;
  border-radius: 12px;
  padding: 20px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.05);
}

// 节点名称单元格
.node-name-cell {
  display: flex;
  align-items: center;
  gap: 8px;

  .node-icon {
    font-size: 18px;

    &.status-online {
      color: #67c23a;
    }

    &.status-offline {
      color: #909399;
    }

    &.status-busy {
      color: #e6a23c;
    }
  }

  .name-text {
    font-weight: 500;
    color: #303133;
  }
}

// 状态标签
.status-dot {
  display: inline-block;
  width: 6px;
  height: 6px;
  border-radius: 50%;
  margin-right: 6px;

  &.status-online {
    background-color: #fff;
    box-shadow: 0 0 4px #fff;
  }

  &.status-offline {
    background-color: #fff;
    opacity: 0.7;
  }

  &.status-busy {
    background-color: #fff;
    animation: pulse 1.5s infinite;
  }
}

@keyframes pulse {
  0%, 100% {
    opacity: 1;
  }
  50% {
    opacity: 0.5;
  }
}

// 使用率单元格
.usage-cell {
  display: flex;
  align-items: center;

  .usage-text {
    font-size: 13px;
    font-weight: 500;

    &.usage-normal {
      color: #67c23a;
    }

    &.usage-warning {
      color: #e6a23c;
    }

    &.usage-danger {
      color: #f56c6c;
    }
  }
}

// 任务徽章
.task-badge {
  :deep(.el-badge__content) {
    font-size: 11px;
    height: 18px;
    line-height: 18px;
    padding: 0 6px;
  }
}

// IP地址
.ip-address {
  font-family: 'SF Mono', Monaco, Consolas, monospace;
  font-size: 13px;
  color: #606266;
}

// 心跳单元格
.heartbeat-cell {
  .heartbeat-warning {
    color: #e6a23c;
  }
}

// 无数据
.no-data {
  color: #c0c4cc;
}

// 节点密钥容器
.node-key-container {
  padding: 0 20px;

  .key-input {
    :deep(.el-input__wrapper) {
      font-family: 'SF Mono', Monaco, Consolas, monospace;
    }
  }
}

// 性能图表
.performance-charts {
  margin-top: 20px;
}

.chart-placeholder {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 150px;
  background: #f5f7fa;
  border-radius: 8px;
  color: #909399;

  .el-icon {
    font-size: 32px;
    margin-bottom: 8px;
  }

  span {
    font-size: 14px;
  }

  .placeholder-tip {
    font-size: 12px;
    color: #c0c4cc;
    margin-top: 4px;
  }
}

// 响应式设计
@media (max-width: 768px) {
  .stats-row {
    margin-bottom: 16px;
  }

  .stat-card {
    padding: 16px;
    margin-bottom: 12px;

    .stat-icon {
      width: 40px;
      height: 40px;
      margin-right: 12px;

      .el-icon {
        font-size: 20px;
      }
    }

    .stat-content {
      .stat-value {
        font-size: 20px;
      }

      .stat-label {
        font-size: 12px;
      }
    }
  }

  .table-card {
    padding: 12px;
    border-radius: 8px;
  }
}
</style>
