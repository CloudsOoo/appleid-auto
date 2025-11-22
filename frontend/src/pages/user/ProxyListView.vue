<!--
  代理池管理页面

  职责：
  - 显示用户的代理列表
  - 支持添加/编辑/删除代理
  - 支持代理测试（测试连通性和响应速度）
  - 支持状态展示（成功率、响应时间）
  - 支持批量删除
  - 支持状态筛选

  上游依赖：
  - PageHeader（页面标题组件）
  - DataTable（表格组件）
  - StatusTag（状态标签组件）
  - FormDialog（表单对话框组件）
  - Vue Router（页面跳转）
  - Element Plus（UI 组件）
  - proxy API（代理相关接口）

  下游调用者：
  - 路由（/proxies）
  - Dashboard（快捷操作）
  - 侧边栏导航

  使用的 API：
  - GET /proxies - 获取代理列表
  - POST /proxies - 创建代理
  - PUT /proxies/{id} - 更新代理
  - DELETE /proxies/{id} - 删除代理
  - POST /proxies/{id}/test - 测试代理
-->

<template>
  <div class="proxy-list-view">
    <!-- 页面标题 -->
    <PageHeader
      title="代理池管理"
      description="管理您的代理服务器，用于 Apple ID 检测和解锁任务"
      :breadcrumbs="[
        { title: '首页', path: '/' },
        { title: '代理池管理' }
      ]"
    >
      <template #actions>
        <el-button type="primary" :icon="Plus" @click="handleAdd">
          添加代理
        </el-button>
        <el-button :icon="Connection" @click="handleTestAll">批量测试</el-button>
      </template>
    </PageHeader>

    <!-- 统计卡片 -->
    <el-row :gutter="20" class="stats-row">
      <el-col :xs="12" :sm="6">
        <div class="stat-card stat-card-total">
          <div class="stat-icon">
            <el-icon><Connection /></el-icon>
          </div>
          <div class="stat-content">
            <div class="stat-value">{{ stats.total }}</div>
            <div class="stat-label">代理总数</div>
          </div>
        </div>
      </el-col>
      <el-col :xs="12" :sm="6">
        <div class="stat-card stat-card-active">
          <div class="stat-icon">
            <el-icon><CircleCheck /></el-icon>
          </div>
          <div class="stat-content">
            <div class="stat-value">{{ stats.active }}</div>
            <div class="stat-label">可用代理</div>
          </div>
        </div>
      </el-col>
      <el-col :xs="12" :sm="6">
        <div class="stat-card stat-card-success">
          <div class="stat-icon">
            <el-icon><TrendCharts /></el-icon>
          </div>
          <div class="stat-content">
            <div class="stat-value">{{ stats.avgSuccessRate }}%</div>
            <div class="stat-label">平均成功率</div>
          </div>
        </div>
      </el-col>
      <el-col :xs="12" :sm="6">
        <div class="stat-card stat-card-speed">
          <div class="stat-icon">
            <el-icon><Timer /></el-icon>
          </div>
          <div class="stat-content">
            <div class="stat-value">{{ stats.avgResponseTime }}ms</div>
            <div class="stat-label">平均响应</div>
          </div>
        </div>
      </el-col>
    </el-row>

    <!-- 数据表格 -->
    <div class="table-card">
      <DataTable
        :data="proxyList"
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
        <!-- 自定义列：代理地址 -->
        <template #column-address="{ row }">
          <div class="proxy-address-cell">
            <el-tag :type="getProtocolTagType(row.protocol)" size="small">
              {{ row.protocol.toUpperCase() }}
            </el-tag>
            <span class="address-text">{{ row.host }}:{{ row.port }}</span>
          </div>
        </template>

        <!-- 自定义列：状态 -->
        <template #column-is_active="{ row }">
          <el-switch
            v-model="row.is_active"
            :loading="row.switching"
            @change="(val) => handleStatusChange(row, val)"
          />
        </template>

        <!-- 自定义列：成功率 -->
        <template #column-success_rate="{ row }">
          <div class="success-rate-cell">
            <el-progress
              :percentage="row.successRate"
              :status="getSuccessRateStatus(row.successRate)"
              :stroke-width="6"
              :show-text="false"
              style="width: 80px; display: inline-block; margin-right: 8px;"
            />
            <span :class="['rate-text', getSuccessRateClass(row.successRate)]">
              {{ row.successRate }}%
            </span>
          </div>
        </template>

        <!-- 自定义列：响应时间 -->
        <template #column-avg_response_time="{ row }">
          <span :class="['response-time', getResponseTimeClass(row.avg_response_time)]">
            {{ row.avg_response_time || '-' }}
            <template v-if="row.avg_response_time">ms</template>
          </span>
        </template>

        <!-- 自定义列：使用统计 -->
        <template #column-usage="{ row }">
          <div class="usage-cell">
            <span class="success-count">✓{{ row.success_count }}</span>
            <span class="fail-count">✗{{ row.fail_count }}</span>
          </div>
        </template>

        <!-- 自定义列：最后检测时间 -->
        <template #column-last_checked_at="{ row }">
          <span v-if="row.last_checked_at">{{ formatTime(row.last_checked_at) }}</span>
          <span v-else class="no-data">-</span>
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
            <el-option label="全部" value="" />
            <el-option label="可用" :value="true" />
            <el-option label="禁用" :value="false" />
          </el-select>
          <el-select
            v-model="filterProtocol"
            placeholder="协议类型"
            clearable
            style="width: 130px"
            @change="handleFilterChange"
          >
            <el-option label="全部协议" value="" />
            <el-option label="HTTP" value="http" />
            <el-option label="HTTPS" value="https" />
            <el-option label="SOCKS5" value="socks5" />
          </el-select>
        </template>
      </DataTable>
    </div>

    <!-- 添加/编辑代理对话框 -->
    <FormDialog
      v-model="formDialogVisible"
      :title="isEdit ? '编辑代理' : '添加代理'"
      :fields="formFields"
      :loading="formLoading"
      :model="formData"
      @submit="handleFormSubmit"
      @cancel="handleFormCancel"
    />

    <!-- 测试结果对话框 -->
    <el-dialog
      v-model="testResultDialogVisible"
      title="代理测试结果"
      width="500px"
      :close-on-click-modal="false"
    >
      <div v-if="testLoading" class="test-loading">
        <el-icon class="is-loading"><Loading /></el-icon>
        <span>正在测试代理连通性...</span>
      </div>
      <div v-else-if="testResult" class="test-result">
        <el-result
          :icon="testResult.success ? 'success' : 'error'"
          :title="testResult.success ? '测试成功' : '测试失败'"
          :sub-title="testResult.success ? `响应时间: ${testResult.response_time}ms` : testResult.error_message"
        >
          <template #extra>
            <el-button @click="testResultDialogVisible = false">关闭</el-button>
            <el-button v-if="!testResult.success" type="primary" @click="handleRetryTest">
              重新测试
            </el-button>
          </template>
        </el-result>
      </div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Plus,
  Connection,
  CircleCheck,
  TrendCharts,
  Timer,
  Loading,
  Edit,
  Delete,
  VideoPlay
} from '@element-plus/icons-vue'
import PageHeader from '@/components/common/PageHeader.vue'
import DataTable from '@/components/common/DataTable.vue'
import FormDialog from '@/components/common/FormDialog.vue'
import {
  getProxyListApi,
  createProxyApi,
  updateProxyApi,
  deleteProxyApi,
  testProxyApi,
  type Proxy,
  type CreateProxyRequest,
  type UpdateProxyRequest
} from '@/api/proxy'
import { formatDate } from '@/utils/date'

// ==================== 类型定义 ====================

interface ProxyWithExtra extends Proxy {
  switching?: boolean
  successRate: number
}

interface Stats {
  total: number
  active: number
  avgSuccessRate: number
  avgResponseTime: number
}

// ==================== 响应式数据 ====================

// 加载状态
const loading = ref(false)
const formLoading = ref(false)
const testLoading = ref(false)

// 代理列表数据
const proxyList = ref<ProxyWithExtra[]>([])
const total = ref(0)
const currentPage = ref(1)
const pageSize = ref(20)

// 筛选条件
const searchKeyword = ref('')
const filterStatus = ref<boolean | ''>('')
const filterProtocol = ref('')

// 对话框状态
const formDialogVisible = ref(false)
const testResultDialogVisible = ref(false)
const isEdit = ref(false)
const currentProxy = ref<Proxy | null>(null)

// 表单数据
const formData = reactive<CreateProxyRequest>({
  protocol: 'http',
  host: '',
  port: 8080,
  username: '',
  password: '',
  is_public: false
})

// 测试结果
const testResult = ref<{
  success: boolean
  response_time: number
  error_message?: string
} | null>(null)

// ==================== 计算属性 ====================

// 统计数据
const stats = computed<Stats>(() => {
  const list = proxyList.value
  const activeList = list.filter(p => p.is_active)
  const totalSuccess = list.reduce((sum, p) => sum + p.success_count, 0)
  const totalFail = list.reduce((sum, p) => sum + p.fail_count, 0)
  const totalUsage = totalSuccess + totalFail
  const avgSuccessRate = totalUsage > 0 ? Math.round((totalSuccess / totalUsage) * 100) : 0
  const avgResponseTime = list.length > 0
    ? Math.round(list.reduce((sum, p) => sum + (p.avg_response_time || 0), 0) / list.length)
    : 0

  return {
    total: total.value,
    active: activeList.length,
    avgSuccessRate,
    avgResponseTime
  }
})

// 表格列配置
const tableColumns = [
  { prop: 'id', label: 'ID', width: 80, sortable: true },
  { prop: 'address', label: '代理地址', minWidth: 200, slot: true },
  { prop: 'is_active', label: '状态', width: 100, slot: true },
  { prop: 'success_rate', label: '成功率', width: 160, slot: true },
  { prop: 'avg_response_time', label: '响应时间', width: 120, slot: true },
  { prop: 'usage', label: '使用统计', width: 140, slot: true },
  { prop: 'last_checked_at', label: '最后检测', width: 170, slot: true }
]

// 操作按钮配置
const actionButtons = [
  { key: 'test', label: '测试', icon: VideoPlay, type: 'success' },
  { key: 'edit', label: '编辑', icon: Edit, type: 'primary' },
  { key: 'delete', label: '删除', icon: Delete, type: 'danger' }
]

// 批量操作配置
const batchActions = [
  { key: 'test', label: '批量测试', icon: 'VideoPlay' },
  { key: 'enable', label: '批量启用', icon: 'Select' },
  { key: 'disable', label: '批量禁用', icon: 'CloseBold' },
  { key: 'delete', label: '批量删除', icon: 'Delete' }
]

// 表单字段配置
const formFields = computed(() => [
  {
    prop: 'protocol',
    label: '协议类型',
    type: 'select',
    required: true,
    options: [
      { label: 'HTTP', value: 'http' },
      { label: 'HTTPS', value: 'https' },
      { label: 'SOCKS5', value: 'socks5' }
    ]
  },
  {
    prop: 'host',
    label: '代理地址',
    type: 'text',
    required: true,
    placeholder: '请输入代理服务器地址（IP或域名）',
    rules: [
      { required: true, message: '请输入代理地址', trigger: 'blur' },
      { min: 1, max: 253, message: '代理地址长度在 1-253 字符', trigger: 'blur' }
    ]
  },
  {
    prop: 'port',
    label: '端口',
    type: 'number',
    required: true,
    min: 1,
    max: 65535,
    placeholder: '请输入端口号',
    rules: [
      { required: true, message: '请输入端口号', trigger: 'blur' },
      { type: 'number', min: 1, max: 65535, message: '端口范围 1-65535', trigger: 'blur' }
    ]
  },
  {
    prop: 'username',
    label: '用户名',
    type: 'text',
    placeholder: '代理认证用户名（可选）'
  },
  {
    prop: 'password',
    label: '密码',
    type: 'password',
    placeholder: '代理认证密码（可选）'
  },
  {
    prop: 'is_public',
    label: '公开代理',
    type: 'switch',
    description: '公开代理可被其他用户使用'
  }
])

// ==================== 方法 ====================

// 获取代理列表
async function fetchProxyList() {
  loading.value = true
  try {
    const params: Record<string, unknown> = {
      page: currentPage.value,
      size: pageSize.value
    }
    if (filterStatus.value !== '') {
      params.is_active = filterStatus.value
    }
    if (filterProtocol.value) {
      params.protocol = filterProtocol.value
    }
    if (searchKeyword.value) {
      params.keyword = searchKeyword.value
    }

    const res = await getProxyListApi(params)
    proxyList.value = (res.items || []).map(item => ({
      ...item,
      switching: false,
      successRate: calculateSuccessRate(item.success_count, item.fail_count)
    }))
    total.value = res.total || 0
  } catch (error) {
    console.error('获取代理列表失败:', error)
    ElMessage.error('获取代理列表失败')
  } finally {
    loading.value = false
  }
}

// 计算成功率
function calculateSuccessRate(success: number, fail: number): number {
  const total = success + fail
  return total > 0 ? Math.round((success / total) * 100) : 0
}

// 获取协议标签类型
function getProtocolTagType(protocol: string): string {
  const map: Record<string, string> = {
    http: 'info',
    https: 'success',
    socks5: 'warning'
  }
  return map[protocol] || 'info'
}

// 获取成功率状态
function getSuccessRateStatus(rate: number): string {
  if (rate >= 80) return 'success'
  if (rate >= 50) return 'warning'
  return 'exception'
}

// 获取成功率样式类
function getSuccessRateClass(rate: number): string {
  if (rate >= 80) return 'rate-success'
  if (rate >= 50) return 'rate-warning'
  return 'rate-danger'
}

// 获取响应时间样式类
function getResponseTimeClass(time: number | null): string {
  if (!time) return ''
  if (time <= 200) return 'time-fast'
  if (time <= 500) return 'time-normal'
  return 'time-slow'
}

// 格式化时间
function formatTime(time: string): string {
  return formatDate(time, 'MM-DD HH:mm')
}

// 处理搜索
function handleSearch(keyword: string) {
  searchKeyword.value = keyword
  currentPage.value = 1
  fetchProxyList()
}

// 处理刷新
function handleRefresh() {
  fetchProxyList()
}

// 处理分页变化
function handlePageChange(page: number) {
  currentPage.value = page
  fetchProxyList()
}

// 处理每页数量变化
function handleSizeChange(size: number) {
  pageSize.value = size
  currentPage.value = 1
  fetchProxyList()
}

// 处理筛选变化
function handleFilterChange() {
  currentPage.value = 1
  fetchProxyList()
}

// 处理状态切换
async function handleStatusChange(row: ProxyWithExtra, val: boolean) {
  row.switching = true
  try {
    await updateProxyApi(row.id, { is_active: val })
    ElMessage.success(val ? '代理已启用' : '代理已禁用')
  } catch (error) {
    console.error('更新代理状态失败:', error)
    row.is_active = !val // 回滚状态
    ElMessage.error('更新代理状态失败')
  } finally {
    row.switching = false
  }
}

// 处理添加代理
function handleAdd() {
  isEdit.value = false
  currentProxy.value = null
  resetFormData()
  formDialogVisible.value = true
}

// 处理行操作
function handleRowAction(action: string, row: Proxy) {
  switch (action) {
    case 'test':
      handleTestProxy(row)
      break
    case 'edit':
      handleEditProxy(row)
      break
    case 'delete':
      handleDeleteProxy(row)
      break
  }
}

// 处理编辑代理
function handleEditProxy(row: Proxy) {
  isEdit.value = true
  currentProxy.value = row
  Object.assign(formData, {
    protocol: row.protocol,
    host: row.host,
    port: row.port,
    username: row.username || '',
    password: row.password || '',
    is_public: row.is_public
  })
  formDialogVisible.value = true
}

// 处理删除代理
async function handleDeleteProxy(row: Proxy) {
  try {
    await ElMessageBox.confirm(
      `确定要删除代理 "${row.host}:${row.port}" 吗？`,
      '删除确认',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    await deleteProxyApi(row.id)
    ElMessage.success('删除成功')
    fetchProxyList()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除代理失败:', error)
      ElMessage.error('删除代理失败')
    }
  }
}

// 处理测试代理
async function handleTestProxy(row: Proxy) {
  currentProxy.value = row
  testResult.value = null
  testLoading.value = true
  testResultDialogVisible.value = true

  try {
    const res = await testProxyApi(row.id)
    testResult.value = res
    // 测试成功后刷新列表以更新统计数据
    if (res.success) {
      fetchProxyList()
    }
  } catch (error) {
    console.error('测试代理失败:', error)
    testResult.value = {
      success: false,
      response_time: 0,
      error_message: '测试请求失败，请稍后重试'
    }
  } finally {
    testLoading.value = false
  }
}

// 处理重新测试
function handleRetryTest() {
  if (currentProxy.value) {
    handleTestProxy(currentProxy.value)
  }
}

// 处理批量测试
async function handleTestAll() {
  const activeProxies = proxyList.value.filter(p => p.is_active)
  if (activeProxies.length === 0) {
    ElMessage.warning('没有可用的代理需要测试')
    return
  }

  ElMessage.info(`开始测试 ${activeProxies.length} 个代理...`)
  let successCount = 0
  let failCount = 0

  for (const proxy of activeProxies) {
    try {
      const res = await testProxyApi(proxy.id)
      if (res.success) {
        successCount++
      } else {
        failCount++
      }
    } catch {
      failCount++
    }
  }

  ElMessage.success(`测试完成：成功 ${successCount} 个，失败 ${failCount} 个`)
  fetchProxyList()
}

// 处理批量操作
async function handleBatchAction(action: string, selectedRows: Proxy[]) {
  if (!selectedRows || selectedRows.length === 0) {
    ElMessage.warning('请先选择要操作的代理')
    return
  }

  switch (action) {
    case 'test':
      ElMessage.info(`开始测试 ${selectedRows.length} 个代理...`)
      for (const row of selectedRows) {
        try {
          await testProxyApi(row.id)
        } catch {
          // 忽略单个失败
        }
      }
      ElMessage.success('批量测试完成')
      fetchProxyList()
      break

    case 'enable':
      for (const row of selectedRows) {
        try {
          await updateProxyApi(row.id, { is_active: true })
        } catch {
          // 忽略单个失败
        }
      }
      ElMessage.success('批量启用完成')
      fetchProxyList()
      break

    case 'disable':
      for (const row of selectedRows) {
        try {
          await updateProxyApi(row.id, { is_active: false })
        } catch {
          // 忽略单个失败
        }
      }
      ElMessage.success('批量禁用完成')
      fetchProxyList()
      break

    case 'delete':
      try {
        await ElMessageBox.confirm(
          `确定要删除选中的 ${selectedRows.length} 个代理吗？`,
          '批量删除确认',
          {
            confirmButtonText: '确定',
            cancelButtonText: '取消',
            type: 'warning'
          }
        )
        for (const row of selectedRows) {
          try {
            await deleteProxyApi(row.id)
          } catch {
            // 忽略单个失败
          }
        }
        ElMessage.success('批量删除完成')
        fetchProxyList()
      } catch {
        // 用户取消
      }
      break
  }
}

// 重置表单数据
function resetFormData() {
  Object.assign(formData, {
    protocol: 'http',
    host: '',
    port: 8080,
    username: '',
    password: '',
    is_public: false
  })
}

// 处理表单提交
async function handleFormSubmit(data: CreateProxyRequest) {
  formLoading.value = true
  try {
    if (isEdit.value && currentProxy.value) {
      const updateData: UpdateProxyRequest = {
        host: data.host,
        port: data.port,
        username: data.username,
        password: data.password,
        is_active: true
      }
      await updateProxyApi(currentProxy.value.id, updateData)
      ElMessage.success('编辑成功')
    } else {
      await createProxyApi(data)
      ElMessage.success('添加成功')
    }
    formDialogVisible.value = false
    fetchProxyList()
  } catch (error) {
    console.error('保存代理失败:', error)
    ElMessage.error(isEdit.value ? '编辑失败' : '添加失败')
  } finally {
    formLoading.value = false
  }
}

// 处理表单取消
function handleFormCancel() {
  formDialogVisible.value = false
}

// ==================== 生命周期 ====================

onMounted(() => {
  fetchProxyList()
})
</script>

<style lang="scss" scoped>
.proxy-list-view {
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

  &.stat-card-active .stat-icon {
    background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
  }

  &.stat-card-success .stat-icon {
    background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
  }

  &.stat-card-speed .stat-icon {
    background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
  }
}

// 表格卡片
.table-card {
  background: white;
  border-radius: 12px;
  padding: 20px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.05);
}

// 代理地址单元格
.proxy-address-cell {
  display: flex;
  align-items: center;
  gap: 8px;

  .address-text {
    font-family: 'SF Mono', Monaco, Consolas, monospace;
    font-size: 13px;
    color: #303133;
  }
}

// 成功率单元格
.success-rate-cell {
  display: flex;
  align-items: center;

  .rate-text {
    font-size: 13px;
    font-weight: 500;

    &.rate-success {
      color: #67c23a;
    }

    &.rate-warning {
      color: #e6a23c;
    }

    &.rate-danger {
      color: #f56c6c;
    }
  }
}

// 响应时间
.response-time {
  font-family: 'SF Mono', Monaco, Consolas, monospace;
  font-size: 13px;

  &.time-fast {
    color: #67c23a;
  }

  &.time-normal {
    color: #e6a23c;
  }

  &.time-slow {
    color: #f56c6c;
  }
}

// 使用统计单元格
.usage-cell {
  display: flex;
  gap: 12px;

  .success-count {
    color: #67c23a;
    font-size: 13px;
  }

  .fail-count {
    color: #f56c6c;
    font-size: 13px;
  }
}

// 无数据
.no-data {
  color: #c0c4cc;
}

// 测试对话框
.test-loading {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 40px 0;

  .el-icon {
    font-size: 48px;
    color: #409eff;
    margin-bottom: 16px;
  }

  span {
    color: #606266;
    font-size: 14px;
  }
}

.test-result {
  padding: 20px 0;
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
