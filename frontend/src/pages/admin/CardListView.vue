<!--
  管理员卡密管理页面

  职责：
  - 显示卡密列表（分页、搜索、筛选）
  - 卡密状态管理（作废、延期）
  - 卡密导出
  - 跳转到卡密生成页面

  上游依赖：
  - PageHeader（页面标题组件）
  - DataTable（表格组件）
  - StatusTag（状态标签组件）
  - LoadingOverlay（加载遮罩组件）
  - Vue Router（页面跳转）
  - Element Plus（UI 组件）
  - card API（卡密相关接口）
  - package API（套餐相关接口）

  下游调用者：
  - 路由（/admin/cards）
  - AdminLayout 侧边栏导航
  - Admin Dashboard 快捷操作

  使用的 API：
  - GET /cards/admin/list - 获取卡密列表
  - GET /cards/admin/export - 导出卡密
  - POST /cards/admin/:id/revoke - 作废卡密
  - POST /cards/admin/:id/extend - 延期卡密
  - GET /packages - 获取套餐列表（用于显示套餐名称）
-->

<template>
  <div class="admin-card-list-view">
    <!-- 页面标题 -->
    <PageHeader
      title="卡密管理"
      description="管理系统卡密、生成和状态"
      :breadcrumbs="[
        { title: '管理后台', path: '/admin' },
        { title: '卡密管理' }
      ]"
    >
      <template #actions>
        <el-button type="primary" :icon="Plus" @click="goToGenerate">
          生成卡密
        </el-button>
        <el-button :icon="Download" @click="handleExport" :loading="exportLoading">
          导出
        </el-button>
        <el-button :icon="Refresh" @click="handleRefresh" :loading="loading">
          刷新
        </el-button>
      </template>
    </PageHeader>

    <!-- 统计卡片 -->
    <el-row :gutter="20" class="stats-row">
      <el-col :xs="12" :sm="6">
        <div class="stat-card stat-total">
          <div class="stat-icon">
            <el-icon><Ticket /></el-icon>
          </div>
          <div class="stat-content">
            <div class="stat-value">{{ stats.total }}</div>
            <div class="stat-label">卡密总数</div>
          </div>
        </div>
      </el-col>
      <el-col :xs="12" :sm="6">
        <div class="stat-card stat-unused">
          <div class="stat-icon">
            <el-icon><CircleCheck /></el-icon>
          </div>
          <div class="stat-content">
            <div class="stat-value">{{ stats.unused }}</div>
            <div class="stat-label">未使用</div>
          </div>
        </div>
      </el-col>
      <el-col :xs="12" :sm="6">
        <div class="stat-card stat-used">
          <div class="stat-icon">
            <el-icon><Check /></el-icon>
          </div>
          <div class="stat-content">
            <div class="stat-value">{{ stats.used }}</div>
            <div class="stat-label">已使用</div>
          </div>
        </div>
      </el-col>
      <el-col :xs="12" :sm="6">
        <div class="stat-card stat-revoked">
          <div class="stat-icon">
            <el-icon><CircleClose /></el-icon>
          </div>
          <div class="stat-content">
            <div class="stat-value">{{ stats.revoked }}</div>
            <div class="stat-label">已作废</div>
          </div>
        </div>
      </el-col>
    </el-row>

    <!-- 筛选工具栏 -->
    <div class="filter-bar">
      <el-row :gutter="16">
        <el-col :xs="24" :sm="8" :md="6">
          <el-input
            v-model="searchKeyword"
            placeholder="搜索卡密码"
            clearable
            :prefix-icon="Search"
            @input="handleSearchDebounce"
          />
        </el-col>
        <el-col :xs="12" :sm="6" :md="4">
          <el-select
            v-model="filterStatus"
            placeholder="状态"
            clearable
            @change="handleFilter"
          >
            <el-option label="全部" value="" />
            <el-option label="未使用" value="unused" />
            <el-option label="已使用" value="used" />
            <el-option label="已过期" value="expired" />
            <el-option label="已作废" value="revoked" />
          </el-select>
        </el-col>
        <el-col :xs="12" :sm="6" :md="4">
          <el-select
            v-model="filterPackage"
            placeholder="套餐"
            clearable
            @change="handleFilter"
          >
            <el-option label="全部" value="" />
            <el-option label="无套餐" :value="0" />
            <el-option
              v-for="pkg in packageList"
              :key="pkg.id"
              :label="pkg.name"
              :value="pkg.id"
            />
          </el-select>
        </el-col>
      </el-row>
    </div>

    <!-- 卡密列表 -->
    <DataTable
      :data="cardList"
      :columns="columns"
      :loading="loading"
      :show-selection="true"
      :show-index="true"
      :show-actions="true"
      :row-actions="rowActions"
      :batch-actions="batchActions"
      :show-batch-actions="true"
      pagination-mode="server"
      :total="pagination.total"
      :page-size="pagination.pageSize"
      @page-change="handlePageChange"
      @row-action="handleRowAction"
      @batch-action="handleBatchAction"
      @selection-change="handleSelectionChange"
    >
      <!-- 卡密码列 -->
      <template #column-code="{ row }">
        <div class="code-cell">
          <code class="card-code">{{ row.code }}</code>
          <el-button
            link
            type="primary"
            :icon="CopyDocument"
            @click="copyCode(row.code)"
            size="small"
          />
        </div>
      </template>

      <!-- 套餐列 -->
      <template #column-package_id="{ row }">
        <el-tag v-if="row.package_id" size="small">
          {{ getPackageName(row.package_id) }}
        </el-tag>
        <span v-else class="text-muted">无套餐</span>
      </template>

      <!-- 状态列 -->
      <template #column-status="{ row }">
        <StatusTag
          :status="getStatusType(row.status)"
          :text="getStatusText(row.status)"
        />
      </template>

      <!-- 有效期列 -->
      <template #column-duration_days="{ row }">
        <span>{{ row.duration_days }} 天</span>
      </template>

      <!-- 使用者列 -->
      <template #column-used_by="{ row }">
        <template v-if="row.used_by">
          <el-link type="primary" @click="viewUser(row.used_by)">
            用户 #{{ row.used_by }}
          </el-link>
        </template>
        <span v-else class="text-muted">-</span>
      </template>

      <!-- 使用时间列 -->
      <template #column-used_at="{ row }">
        <span v-if="row.used_at">{{ formatTime(row.used_at) }}</span>
        <span v-else class="text-muted">-</span>
      </template>

      <!-- 过期时间列 -->
      <template #column-expires_at="{ row }">
        <template v-if="row.expires_at">
          <span :class="{ 'text-danger': isExpired(row.expires_at) }">
            {{ formatTime(row.expires_at) }}
          </span>
        </template>
        <span v-else class="text-muted">-</span>
      </template>

      <!-- 创建时间列 -->
      <template #column-created_at="{ row }">
        {{ formatTime(row.created_at) }}
      </template>
    </DataTable>

    <!-- 延期对话框 -->
    <el-dialog
      v-model="extendDialogVisible"
      title="延期卡密"
      width="400px"
      :close-on-click-modal="false"
    >
      <el-form :model="extendForm" label-width="100px">
        <el-form-item label="卡密码">
          <code class="card-code">{{ currentCard?.code }}</code>
        </el-form-item>
        <el-form-item label="当前状态">
          <StatusTag
            v-if="currentCard"
            :status="getStatusType(currentCard.status)"
            :text="getStatusText(currentCard.status)"
          />
        </el-form-item>
        <el-form-item label="延期天数" required>
          <el-input-number
            v-model="extendForm.days"
            :min="1"
            :max="3650"
            placeholder="请输入延期天数"
          />
          <span class="form-tip">天</span>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="extendDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleExtendSubmit" :loading="extendLoading">
          确定延期
        </el-button>
      </template>
    </el-dialog>

    <!-- 卡密详情对话框 -->
    <el-dialog
      v-model="detailDialogVisible"
      title="卡密详情"
      width="500px"
    >
      <el-descriptions :column="1" border v-if="currentCard">
        <el-descriptions-item label="卡密 ID">{{ currentCard.id }}</el-descriptions-item>
        <el-descriptions-item label="卡密码">
          <code class="card-code">{{ currentCard.code }}</code>
        </el-descriptions-item>
        <el-descriptions-item label="关联套餐">
          <el-tag v-if="currentCard.package_id" size="small">
            {{ getPackageName(currentCard.package_id) }}
          </el-tag>
          <span v-else class="text-muted">无套餐</span>
        </el-descriptions-item>
        <el-descriptions-item label="状态">
          <StatusTag
            :status="getStatusType(currentCard.status)"
            :text="getStatusText(currentCard.status)"
          />
        </el-descriptions-item>
        <el-descriptions-item label="有效期">{{ currentCard.duration_days }} 天</el-descriptions-item>
        <el-descriptions-item label="使用者">
          <template v-if="currentCard.used_by">
            用户 #{{ currentCard.used_by }}
          </template>
          <span v-else class="text-muted">未使用</span>
        </el-descriptions-item>
        <el-descriptions-item label="使用时间">
          <span v-if="currentCard.used_at">{{ formatTime(currentCard.used_at) }}</span>
          <span v-else class="text-muted">-</span>
        </el-descriptions-item>
        <el-descriptions-item label="过期时间">
          <span v-if="currentCard.expires_at">{{ formatTime(currentCard.expires_at) }}</span>
          <span v-else class="text-muted">-</span>
        </el-descriptions-item>
        <el-descriptions-item label="创建时间">{{ formatTime(currentCard.created_at) }}</el-descriptions-item>
      </el-descriptions>
      <template #footer>
        <el-button @click="detailDialogVisible = false">关闭</el-button>
      </template>
    </el-dialog>

    <LoadingOverlay :visible="pageLoading" text="处理中..." />
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Refresh,
  Search,
  Plus,
  Download,
  Ticket,
  CircleCheck,
  CircleClose,
  Check,
  CopyDocument
} from '@element-plus/icons-vue'
import PageHeader from '@/components/common/PageHeader.vue'
import DataTable from '@/components/common/DataTable.vue'
import StatusTag from '@/components/common/StatusTag.vue'
import LoadingOverlay from '@/components/common/LoadingOverlay.vue'
import type { TableColumn, ActionButton, BatchAction } from '@/components/common/DataTable.vue'
import {
  getCardListApi,
  exportCardsApi,
  revokeCardApi,
  extendCardApi,
  type Card,
  type CardListParams
} from '@/api/card'
import { getPackageListApi, type Package } from '@/api/package'
import { formatDate } from '@/utils/date'

// ==================== 路由 ====================

const router = useRouter()

// ==================== 响应式数据 ====================

const loading = ref(false)
const pageLoading = ref(false)
const exportLoading = ref(false)

// 统计数据
const stats = reactive({
  total: 0,
  unused: 0,
  used: 0,
  revoked: 0
})

// 卡密列表
const cardList = ref<Card[]>([])

// 套餐列表
const packageList = ref<Package[]>([])
const packageMap = ref<Record<number, string>>({})

// 分页
const pagination = reactive({
  page: 1,
  pageSize: 20,
  total: 0
})

// 筛选
const searchKeyword = ref('')
const filterStatus = ref('')
const filterPackage = ref<number | string>('')
let searchTimer: ReturnType<typeof setTimeout> | null = null

// 选中的卡密
const selectedCards = ref<Card[]>([])

// 当前卡密
const currentCard = ref<Card | null>(null)

// 对话框
const detailDialogVisible = ref(false)
const extendDialogVisible = ref(false)

// 延期表单
const extendForm = reactive({
  days: 30
})
const extendLoading = ref(false)

// ==================== 表格配置 ====================

const columns: TableColumn[] = [
  { prop: 'id', label: 'ID', width: 70 },
  { prop: 'code', label: '卡密码', minWidth: 180 },
  { prop: 'package_id', label: '套餐', width: 120 },
  { prop: 'status', label: '状态', width: 100 },
  { prop: 'duration_days', label: '有效期', width: 80 },
  { prop: 'used_by', label: '使用者', width: 100 },
  { prop: 'used_at', label: '使用时间', width: 150 },
  { prop: 'expires_at', label: '过期时间', width: 150 },
  { prop: 'created_at', label: '创建时间', width: 150 }
]

const rowActions: ActionButton[] = [
  { key: 'view', label: '详情', type: 'primary' },
  { key: 'extend', label: '延期', type: 'warning' },
  { key: 'revoke', label: '作废', type: 'danger' }
]

const batchActions: BatchAction[] = [
  { key: 'export', label: '导出选中', type: 'primary' },
  { key: 'revoke', label: '批量作废', type: 'danger', confirmText: '确定要作废选中的卡密吗？此操作不可恢复！' }
]

// ==================== 方法 ====================

// 获取套餐列表
async function fetchPackageList() {
  try {
    const data = await getPackageListApi()
    packageList.value = data || []
    // 构建映射
    packageMap.value = {}
    packageList.value.forEach(pkg => {
      packageMap.value[pkg.id] = pkg.name
    })
  } catch (error) {
    console.error('获取套餐列表失败:', error)
  }
}

// 获取卡密列表
async function fetchCardList() {
  loading.value = true
  try {
    const params: CardListParams = {
      page: pagination.page,
      size: pagination.pageSize
    }
    if (filterStatus.value) {
      params.status = filterStatus.value
    }
    // 注意：后端可能不支持按套餐筛选，这里预留

    const data = await getCardListApi(params)
    cardList.value = data.items || []
    pagination.total = data.total || 0

    // 计算统计数据
    calculateStats()
  } catch (error) {
    console.error('获取卡密列表失败:', error)
    ElMessage.error('获取卡密列表失败')
  } finally {
    loading.value = false
  }
}

// 计算统计数据
function calculateStats() {
  stats.total = pagination.total
  stats.unused = cardList.value.filter(c => c.status === 'unused').length
  stats.used = cardList.value.filter(c => c.status === 'used').length
  stats.revoked = cardList.value.filter(c => c.status === 'revoked').length
}

// 刷新
function handleRefresh() {
  pagination.page = 1
  fetchCardList()
}

// 搜索防抖
function handleSearchDebounce() {
  if (searchTimer) {
    clearTimeout(searchTimer)
  }
  searchTimer = setTimeout(() => {
    pagination.page = 1
    fetchCardList()
  }, 300)
}

// 筛选
function handleFilter() {
  pagination.page = 1
  fetchCardList()
}

// 分页变化
function handlePageChange({ page, pageSize }: { page: number; pageSize: number }) {
  pagination.page = page
  pagination.pageSize = pageSize
  fetchCardList()
}

// 选择变化
function handleSelectionChange(selection: Card[]) {
  selectedCards.value = selection
}

// 行操作
async function handleRowAction({ action, row }: { action: string; row: Card }) {
  currentCard.value = row

  switch (action) {
    case 'view':
      detailDialogVisible.value = true
      break
    case 'extend':
      if (row.status === 'revoked') {
        ElMessage.warning('已作废的卡密不能延期')
        return
      }
      extendForm.days = 30
      extendDialogVisible.value = true
      break
    case 'revoke':
      await handleRevoke(row)
      break
  }
}

// 批量操作
async function handleBatchAction({ action }: { action: string }) {
  if (selectedCards.value.length === 0) {
    ElMessage.warning('请先选择卡密')
    return
  }

  switch (action) {
    case 'export':
      await handleBatchExport()
      break
    case 'revoke':
      await handleBatchRevoke()
      break
  }
}

// 跳转到生成页面
function goToGenerate() {
  router.push('/admin/cards/generate')
}

// 导出卡密
async function handleExport() {
  exportLoading.value = true
  try {
    const params: any = {}
    if (filterStatus.value) {
      params.status = filterStatus.value
    }

    const data = await exportCardsApi(params)
    // 假设返回的是文件数据或下载链接
    if (typeof data === 'string') {
      // 如果是 CSV 字符串
      downloadFile(data, 'cards.csv', 'text/csv')
    } else {
      ElMessage.success('导出成功')
    }
  } catch (error) {
    console.error('导出失败:', error)
    ElMessage.error('导出失败')
  } finally {
    exportLoading.value = false
  }
}

// 批量导出选中
async function handleBatchExport() {
  const codes = selectedCards.value.map(c => c.code).join('\n')
  downloadFile(codes, 'selected_cards.txt', 'text/plain')
  ElMessage.success(`已导出 ${selectedCards.value.length} 个卡密`)
}

// 下载文件
function downloadFile(content: string, filename: string, type: string) {
  const blob = new Blob([content], { type })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = filename
  link.click()
  URL.revokeObjectURL(url)
}

// 作废卡密
async function handleRevoke(card: Card) {
  if (card.status === 'revoked') {
    ElMessage.warning('该卡密已作废')
    return
  }
  if (card.status === 'used') {
    ElMessage.warning('已使用的卡密不能作废')
    return
  }

  try {
    await ElMessageBox.confirm(
      `确定要作废卡密 "${card.code}" 吗？此操作不可恢复！`,
      '作废确认',
      { type: 'warning' }
    )

    pageLoading.value = true
    await revokeCardApi(card.id)
    ElMessage.success('卡密已作废')
    fetchCardList()
  } catch (error: any) {
    if (error !== 'cancel') {
      console.error('作废卡密失败:', error)
      ElMessage.error('作废卡密失败')
    }
  } finally {
    pageLoading.value = false
  }
}

// 批量作废
async function handleBatchRevoke() {
  const validCards = selectedCards.value.filter(c => c.status === 'unused')
  if (validCards.length === 0) {
    ElMessage.warning('没有可作废的卡密（只能作废未使用的卡密）')
    return
  }

  try {
    pageLoading.value = true
    const promises = validCards.map(c => revokeCardApi(c.id))
    await Promise.all(promises)

    ElMessage.success(`已作废 ${validCards.length} 个卡密`)
    fetchCardList()
  } catch (error) {
    console.error('批量作废失败:', error)
    ElMessage.error('批量作废失败')
  } finally {
    pageLoading.value = false
  }
}

// 延期提交
async function handleExtendSubmit() {
  if (!currentCard.value) return
  if (extendForm.days < 1) {
    ElMessage.warning('请输入有效的延期天数')
    return
  }

  extendLoading.value = true
  try {
    await extendCardApi(currentCard.value.id, extendForm.days)
    ElMessage.success(`卡密已延期 ${extendForm.days} 天`)
    extendDialogVisible.value = false
    fetchCardList()
  } catch (error) {
    console.error('延期失败:', error)
    ElMessage.error('延期失败')
  } finally {
    extendLoading.value = false
  }
}

// 复制卡密码
function copyCode(code: string) {
  navigator.clipboard.writeText(code).then(() => {
    ElMessage.success('已复制到剪贴板')
  }).catch(() => {
    ElMessage.error('复制失败')
  })
}

// 查看用户
function viewUser(userId: number) {
  router.push(`/admin/users?id=${userId}`)
}

// 格式化时间
function formatTime(time: string): string {
  return formatDate(time, 'YYYY-MM-DD HH:mm')
}

// 获取套餐名称
function getPackageName(packageId: number): string {
  return packageMap.value[packageId] || `套餐 #${packageId}`
}

// 获取状态类型
function getStatusType(status: string): string {
  const map: Record<string, string> = {
    unused: 'success',
    used: 'primary',
    expired: 'warning',
    revoked: 'danger'
  }
  return map[status] || 'info'
}

// 获取状态文本
function getStatusText(status: string): string {
  const map: Record<string, string> = {
    unused: '未使用',
    used: '已使用',
    expired: '已过期',
    revoked: '已作废'
  }
  return map[status] || status
}

// 是否过期
function isExpired(expiresAt: string): boolean {
  return new Date(expiresAt) < new Date()
}

// ==================== 生命周期 ====================

onMounted(() => {
  fetchPackageList()
  fetchCardList()
})
</script>

<style lang="scss" scoped>
.admin-card-list-view {
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
  margin-bottom: 16px;
  transition: all 0.3s ease;

  &:hover {
    transform: translateY(-4px);
    box-shadow: 0 8px 24px rgba(0, 0, 0, 0.12);
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
      font-size: 28px;
      font-weight: 700;
      color: #303133;
      line-height: 1.2;
    }

    .stat-label {
      font-size: 13px;
      color: #909399;
      margin-top: 4px;
    }
  }

  &.stat-total .stat-icon {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  }

  &.stat-unused .stat-icon {
    background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
  }

  &.stat-used .stat-icon {
    background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
  }

  &.stat-revoked .stat-icon {
    background: linear-gradient(135deg, #bdc3c7 0%, #95a5a6 100%);
  }
}

// 筛选栏
.filter-bar {
  background: white;
  padding: 16px 20px;
  border-radius: 12px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.05);
  margin-bottom: 20px;

  .el-select {
    width: 100%;
  }
}

// 卡密码样式
.code-cell {
  display: flex;
  align-items: center;
  gap: 8px;
}

.card-code {
  font-family: 'Consolas', 'Monaco', monospace;
  background: #f5f7fa;
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 13px;
  color: #606266;
  letter-spacing: 1px;
}

// 文本样式
.text-muted {
  color: #909399;
}

.text-danger {
  color: #f56c6c;
}

// 表单提示
.form-tip {
  margin-left: 8px;
  color: #909399;
}

// 响应式设计
@media (max-width: 768px) {
  .stat-card {
    padding: 16px;

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
        font-size: 24px;
      }

      .stat-label {
        font-size: 12px;
      }
    }
  }

  .filter-bar {
    .el-col {
      margin-bottom: 12px;

      &:last-child {
        margin-bottom: 0;
      }
    }
  }
}
</style>
