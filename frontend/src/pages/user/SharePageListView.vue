<template>
  <div class="share-page-list-view">
    <PageHeader title="分享页管理">
      <template #description>
        管理所有分享页面，支持创建、编辑、删除和访问统计
      </template>
      <template #actions>
        <el-button type="primary" :icon="Plus" @click="handleCreate">
          创建分享页
        </el-button>
      </template>
    </PageHeader>

    <!-- 统计卡片 -->
    <div class="stats-row">
      <div class="stat-card stat-card--total">
        <div class="stat-icon">
          <el-icon :size="28"><Document /></el-icon>
        </div>
        <div class="stat-content">
          <div class="stat-label">总分享页</div>
          <div class="stat-value">{{ stats.total }}</div>
        </div>
      </div>

      <div class="stat-card stat-card--active">
        <div class="stat-icon">
          <el-icon :size="28"><Check /></el-icon>
        </div>
        <div class="stat-content">
          <div class="stat-label">已启用</div>
          <div class="stat-value">{{ stats.active }}</div>
        </div>
      </div>

      <div class="stat-card stat-card--views">
        <div class="stat-icon">
          <el-icon :size="28"><View /></el-icon>
        </div>
        <div class="stat-content">
          <div class="stat-label">总访问量</div>
          <div class="stat-value">{{ formatNumber(stats.total_views) }}</div>
        </div>
      </div>

      <div class="stat-card stat-card--today">
        <div class="stat-icon">
          <el-icon :size="28"><TrendCharts /></el-icon>
        </div>
        <div class="stat-content">
          <div class="stat-label">今日访问</div>
          <div class="stat-value">{{ formatNumber(stats.today_views) }}</div>
        </div>
      </div>
    </div>

    <!-- 数据表格 -->
    <DataTable
      :data="tableData"
      :columns="columns"
      :loading="loading"
      :total="total"
      :show-selection="true"
      :show-index="true"
      :show-actions="true"
      :show-toolbar="true"
      :show-search="true"
      :show-refresh="true"
      :show-batch-actions="true"
      :row-actions="rowActions"
      :batch-actions="batchActions"
      pagination-mode="server"
      title="分享页列表"
      row-key="id"
      @refresh="handleRefresh"
      @search="handleSearch"
      @page-change="handlePageChange"
      @row-action="handleRowAction"
      @batch-action="handleBatchAction"
    >
      <!-- 自定义列：标题 -->
      <template #column-title="{ row }">
        <div class="title-cell">
          <span class="title-text">{{ row.title }}</span>
          <el-tooltip v-if="row.password_protected" content="密码保护" placement="top">
            <el-icon color="#e6a23c"><Lock /></el-icon>
          </el-tooltip>
        </div>
      </template>

      <!-- 自定义列：分享链接 -->
      <template #column-share_url="{ row }">
        <div class="url-cell">
          <el-input
            :model-value="row.share_url"
            readonly
            size="small"
          >
            <template #append>
              <el-button :icon="CopyDocument" @click="handleCopyUrl(row.share_url)">
                复制
              </el-button>
            </template>
          </el-input>
        </div>
      </template>

      <!-- 自定义列：状态 -->
      <template #column-status="{ row }">
        <el-switch
          :model-value="row.status === 'active'"
          :loading="row.switching"
          @change="handleToggleStatus(row)"
        />
      </template>

      <!-- 自定义列：访问量 -->
      <template #column-view_count="{ row }">
        <el-tag type="info">{{ formatNumber(row.view_count) }} 次</el-tag>
      </template>

      <!-- 自定义列：访问控制 -->
      <template #column-access_control="{ row }">
        <div class="access-control-cell">
          <el-tag v-if="row.password_protected" type="warning" size="small">
            密码保护
          </el-tag>
          <el-tag v-if="row.ip_whitelist && row.ip_whitelist.length > 0" type="info" size="small">
            IP白名单
          </el-tag>
          <el-tag v-if="row.expire_at" type="danger" size="small">
            限时访问
          </el-tag>
          <span v-if="!row.password_protected && (!row.ip_whitelist || row.ip_whitelist.length === 0) && !row.expire_at">
            公开
          </span>
        </div>
      </template>

      <!-- 自定义列：更新时间 -->
      <template #column-updated_at="{ row }">
        {{ formatDateTime(row.updated_at) }}
      </template>
    </DataTable>

    <!-- 访问日志对话框 -->
    <el-dialog
      v-model="accessLogDialogVisible"
      title="访问日志"
      width="900px"
      :close-on-click-modal="false"
    >
      <DataTable
        :data="accessLogs"
        :columns="logColumns"
        :loading="logLoading"
        :show-pagination="true"
        :show-toolbar="false"
        pagination-mode="client"
      >
        <!-- 自定义列：访问结果 -->
        <template #column-result="{ row }">
          <StatusTag
            :type="row.result === 'success' ? 'success' : 'danger'"
            :text="row.result === 'success' ? '成功' : '失败'"
          />
        </template>
      </DataTable>
    </el-dialog>

    <!-- 访问统计对话框 -->
    <el-dialog
      v-model="statsDialogVisible"
      title="访问统计"
      width="800px"
      :close-on-click-modal="false"
    >
      <div class="stats-content">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="总访问量">
            {{ formatNumber(currentSharePage.view_count) }}
          </el-descriptions-item>
          <el-descriptions-item label="今日访问量">
            {{ formatNumber(currentSharePage.today_views) }}
          </el-descriptions-item>
          <el-descriptions-item label="本周访问量">
            {{ formatNumber(currentSharePage.week_views) }}
          </el-descriptions-item>
          <el-descriptions-item label="本月访问量">
            {{ formatNumber(currentSharePage.month_views) }}
          </el-descriptions-item>
          <el-descriptions-item label="独立访客">
            {{ formatNumber(currentSharePage.unique_visitors) }}
          </el-descriptions-item>
          <el-descriptions-item label="复制次数">
            {{ formatNumber(currentSharePage.copy_count) }}
          </el-descriptions-item>
        </el-descriptions>

        <!-- TODO: 添加 ECharts 图表展示访问趋势 -->
        <div class="stats-chart">
          <el-alert type="info" :closable="false">
            访问趋势图表功能开发中...
          </el-alert>
        </div>
      </div>
    </el-dialog>

    <!-- 二维码对话框 -->
    <el-dialog
      v-model="qrcodeDialogVisible"
      title="分享二维码"
      width="400px"
      :close-on-click-modal="false"
    >
      <div class="qrcode-content">
        <div class="qrcode-placeholder">
          <el-icon :size="150" color="#dcdfe6"><Picture /></el-icon>
          <p>二维码生成功能开发中...</p>
        </div>
        <div class="qrcode-url">
          <el-input
            :model-value="currentShareUrl"
            readonly
            size="large"
          >
            <template #append>
              <el-button :icon="CopyDocument" @click="handleCopyUrl(currentShareUrl)">
                复制链接
              </el-button>
            </template>
          </el-input>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Plus,
  Document,
  Check,
  View,
  TrendCharts,
  Lock,
  CopyDocument,
  Picture
} from '@element-plus/icons-vue'
import PageHeader from '@/components/common/PageHeader.vue'
import DataTable from '@/components/common/DataTable.vue'
import StatusTag from '@/components/common/StatusTag.vue'
import type { TableColumn, ActionButton, BatchAction } from '@/components/common/DataTable.vue'

// ==================== 类型定义 ====================

interface SharePage {
  id: number
  title: string
  slug: string
  share_url: string
  status: 'active' | 'inactive'
  password_protected: boolean
  ip_whitelist?: string[]
  expire_at?: string
  view_count: number
  today_views?: number
  week_views?: number
  month_views?: number
  unique_visitors?: number
  copy_count?: number
  created_at: string
  updated_at: string
  switching?: boolean
}

interface AccessLog {
  id: number
  ip: string
  user_agent: string
  result: 'success' | 'failed'
  visited_at: string
}

interface Stats {
  total: number
  active: number
  total_views: number
  today_views: number
}

// ==================== 路由 ====================

const router = useRouter()

// ==================== 数据状态 ====================

const loading = ref(false)
const tableData = ref<SharePage[]>([])
const total = ref(0)

// 统计数据
const stats = reactive<Stats>({
  total: 0,
  active: 0,
  total_views: 0,
  today_views: 0
})

// 对话框状态
const accessLogDialogVisible = ref(false)
const statsDialogVisible = ref(false)
const qrcodeDialogVisible = ref(false)

// 访问日志
const accessLogs = ref<AccessLog[]>([])
const logLoading = ref(false)

// 当前分享页
const currentSharePage = ref<SharePage>({
  id: 0,
  title: '',
  slug: '',
  share_url: '',
  status: 'active',
  password_protected: false,
  view_count: 0,
  created_at: '',
  updated_at: ''
})

const currentShareUrl = ref('')

// ==================== 表格配置 ====================

const columns: TableColumn[] = [
  { prop: 'id', label: 'ID', width: 80 },
  { prop: 'title', label: '标题', minWidth: 200 },
  { prop: 'slug', label: 'Slug', width: 150 },
  { prop: 'share_url', label: '分享链接', minWidth: 250 },
  { prop: 'status', label: '状态', width: 80 },
  { prop: 'view_count', label: '访问量', width: 100 },
  { prop: 'access_control', label: '访问控制', width: 180 },
  { prop: 'updated_at', label: '更新时间', width: 180 }
]

const rowActions: ActionButton[] = [
  {
    label: '编辑',
    type: 'primary',
    action: 'edit'
  },
  {
    label: '预览',
    type: 'success',
    action: 'preview'
  },
  {
    label: '统计',
    type: 'info',
    action: 'stats'
  },
  {
    label: '日志',
    type: 'warning',
    action: 'logs'
  },
  {
    label: '二维码',
    type: 'info',
    action: 'qrcode'
  },
  {
    label: '删除',
    type: 'danger',
    action: 'delete'
  }
]

const batchActions: BatchAction[] = [
  {
    label: '批量删除',
    type: 'danger',
    action: 'batch_delete'
  },
  {
    label: '批量启用',
    type: 'success',
    action: 'batch_enable'
  },
  {
    label: '批量禁用',
    type: 'warning',
    action: 'batch_disable'
  }
]

// 访问日志列表配置
const logColumns: TableColumn[] = [
  { prop: 'id', label: 'ID', width: 80 },
  { prop: 'ip', label: 'IP地址', width: 150 },
  { prop: 'user_agent', label: 'User Agent', minWidth: 300, showOverflowTooltip: true },
  { prop: 'result', label: '访问结果', width: 100 },
  { prop: 'visited_at', label: '访问时间', width: 180 }
]

// ==================== 数据加载 ====================

/**
 * 加载分享页列表
 */
async function loadSharePages(params: any = {}) {
  loading.value = true

  try {
    // TODO: 调用 API 获取分享页列表
    // const { data } = await shareApi.getList(params)

    // 模拟 API 调用
    await new Promise(resolve => setTimeout(resolve, 500))

    // 模拟数据
    const mockData: SharePage[] = [
      {
        id: 1,
        title: '官方 Apple ID 分享',
        slug: 'official-apple-id',
        share_url: 'https://example.com/s/official-apple-id',
        status: 'active',
        password_protected: true,
        ip_whitelist: ['192.168.1.100'],
        view_count: 1523,
        today_views: 52,
        week_views: 385,
        month_views: 1200,
        unique_visitors: 856,
        copy_count: 324,
        created_at: '2025-11-01 10:00:00',
        updated_at: '2025-11-21 15:30:00'
      },
      {
        id: 2,
        title: '测试账号分享',
        slug: 'test-accounts',
        share_url: 'https://example.com/s/test-accounts',
        status: 'active',
        password_protected: false,
        view_count: 856,
        today_views: 28,
        week_views: 198,
        month_views: 650,
        unique_visitors: 432,
        copy_count: 156,
        created_at: '2025-11-05 14:20:00',
        updated_at: '2025-11-20 10:15:00'
      },
      {
        id: 3,
        title: '临时分享页',
        slug: 'temp-share',
        share_url: 'https://example.com/s/temp-share',
        status: 'inactive',
        password_protected: true,
        expire_at: '2025-12-31 23:59:59',
        view_count: 234,
        today_views: 5,
        week_views: 45,
        month_views: 180,
        unique_visitors: 128,
        copy_count: 67,
        created_at: '2025-11-15 09:00:00',
        updated_at: '2025-11-21 08:00:00'
      },
      {
        id: 4,
        title: 'VIP 专属账号',
        slug: 'vip-accounts',
        share_url: 'https://example.com/s/vip-accounts',
        status: 'active',
        password_protected: true,
        ip_whitelist: ['10.0.0.0/24'],
        view_count: 3421,
        today_views: 89,
        week_views: 642,
        month_views: 2800,
        unique_visitors: 1523,
        copy_count: 892,
        created_at: '2025-10-20 11:30:00',
        updated_at: '2025-11-21 16:45:00'
      }
    ]

    tableData.value = mockData
    total.value = mockData.length

    // 更新统计数据
    stats.total = mockData.length
    stats.active = mockData.filter(item => item.status === 'active').length
    stats.total_views = mockData.reduce((sum, item) => sum + item.view_count, 0)
    stats.today_views = mockData.reduce((sum, item) => sum + (item.today_views || 0), 0)
  } catch (error: any) {
    console.error('加载分享页列表失败:', error)
    ElMessage.error(error.message || '加载失败，请稍后重试')
  } finally {
    loading.value = false
  }
}

/**
 * 加载访问日志
 */
async function loadAccessLogs(sharePageId: number) {
  logLoading.value = true

  try {
    // TODO: 调用 API 获取访问日志
    // const { data } = await shareApi.getAccessLogs(sharePageId)

    // 模拟 API 调用
    await new Promise(resolve => setTimeout(resolve, 500))

    // 模拟数据
    accessLogs.value = [
      {
        id: 1,
        ip: '192.168.1.100',
        user_agent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        result: 'success',
        visited_at: '2025-11-21 16:30:00'
      },
      {
        id: 2,
        ip: '192.168.1.101',
        user_agent: 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)',
        result: 'success',
        visited_at: '2025-11-21 16:25:00'
      },
      {
        id: 3,
        ip: '192.168.1.102',
        user_agent: 'Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X)',
        result: 'failed',
        visited_at: '2025-11-21 16:20:00'
      }
    ]
  } catch (error: any) {
    console.error('加载访问日志失败:', error)
    ElMessage.error(error.message || '加载失败，请稍后重试')
  } finally {
    logLoading.value = false
  }
}

// ==================== 事件处理 ====================

/**
 * 刷新
 */
function handleRefresh() {
  loadSharePages()
}

/**
 * 搜索
 */
function handleSearch(keyword: string) {
  loadSharePages({ keyword })
}

/**
 * 分页变化
 */
function handlePageChange(page: number, pageSize: number) {
  loadSharePages({ page, pageSize })
}

/**
 * 创建分享页
 */
function handleCreate() {
  router.push('/share-pages/create')
}

/**
 * 行操作
 */
async function handleRowAction(action: string, row: SharePage) {
  switch (action) {
    case 'edit':
      router.push(`/share-pages/edit/${row.id}`)
      break
    case 'preview':
      window.open(row.share_url, '_blank')
      break
    case 'stats':
      currentSharePage.value = row
      statsDialogVisible.value = true
      break
    case 'logs':
      currentSharePage.value = row
      accessLogDialogVisible.value = true
      await loadAccessLogs(row.id)
      break
    case 'qrcode':
      currentShareUrl.value = row.share_url
      qrcodeDialogVisible.value = true
      break
    case 'delete':
      await handleDelete(row)
      break
  }
}

/**
 * 批量操作
 */
async function handleBatchAction(action: string, rows: SharePage[]) {
  switch (action) {
    case 'batch_delete':
      await handleBatchDelete(rows)
      break
    case 'batch_enable':
      await handleBatchToggleStatus(rows, true)
      break
    case 'batch_disable':
      await handleBatchToggleStatus(rows, false)
      break
  }
}

/**
 * 切换状态
 */
async function handleToggleStatus(row: SharePage) {
  row.switching = true

  try {
    const newStatus = row.status === 'active' ? 'inactive' : 'active'

    // TODO: 调用 API 更新状态
    // await shareApi.updateStatus(row.id, { status: newStatus })

    // 模拟 API 调用
    await new Promise(resolve => setTimeout(resolve, 500))

    row.status = newStatus
    ElMessage.success(`已${newStatus === 'active' ? '启用' : '禁用'}`)
  } catch (error: any) {
    console.error('切换状态失败:', error)
    ElMessage.error(error.message || '操作失败，请稍后重试')
  } finally {
    row.switching = false
  }
}

/**
 * 复制链接
 */
async function handleCopyUrl(url: string) {
  try {
    await navigator.clipboard.writeText(url)
    ElMessage.success('链接已复制到剪贴板')
  } catch (error) {
    console.error('复制失败:', error)
    ElMessage.error('复制失败，请手动复制')
  }
}

/**
 * 删除分享页
 */
async function handleDelete(row: SharePage) {
  try {
    await ElMessageBox.confirm(
      `确定要删除分享页"${row.title}"吗？删除后将无法恢复。`,
      '删除确认',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'error'
      }
    )

    // TODO: 调用 API 删除
    // await shareApi.delete(row.id)

    // 模拟 API 调用
    await new Promise(resolve => setTimeout(resolve, 500))

    ElMessage.success('删除成功')
    await loadSharePages()
  } catch (error: any) {
    if (error !== 'cancel') {
      console.error('删除失败:', error)
      ElMessage.error(error.message || '删除失败，请稍后重试')
    }
  }
}

/**
 * 批量删除
 */
async function handleBatchDelete(rows: SharePage[]) {
  try {
    await ElMessageBox.confirm(
      `确定要删除选中的 ${rows.length} 个分享页吗？删除后将无法恢复。`,
      '批量删除确认',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'error'
      }
    )

    // TODO: 调用 API 批量删除
    // await shareApi.batchDelete(rows.map(r => r.id))

    // 模拟 API 调用
    await new Promise(resolve => setTimeout(resolve, 1000))

    ElMessage.success(`成功删除 ${rows.length} 个分享页`)
    await loadSharePages()
  } catch (error: any) {
    if (error !== 'cancel') {
      console.error('批量删除失败:', error)
      ElMessage.error(error.message || '批量删除失败，请稍后重试')
    }
  }
}

/**
 * 批量切换状态
 */
async function handleBatchToggleStatus(rows: SharePage[], enable: boolean) {
  try {
    const action = enable ? '启用' : '禁用'
    await ElMessageBox.confirm(
      `确定要${action}选中的 ${rows.length} 个分享页吗？`,
      `批量${action}确认`,
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )

    // TODO: 调用 API 批量更新状态
    // await shareApi.batchUpdateStatus(rows.map(r => r.id), { status: enable ? 'active' : 'inactive' })

    // 模拟 API 调用
    await new Promise(resolve => setTimeout(resolve, 1000))

    ElMessage.success(`成功${action} ${rows.length} 个分享页`)
    await loadSharePages()
  } catch (error: any) {
    if (error !== 'cancel') {
      console.error(`批量${enable ? '启用' : '禁用'}失败:`, error)
      ElMessage.error(error.message || '批量操作失败，请稍后重试')
    }
  }
}

// ==================== 工具方法 ====================

/**
 * 格式化数字
 */
function formatNumber(num: number): string {
  if (!num) return '0'
  if (num >= 10000) {
    return (num / 10000).toFixed(1) + '万'
  }
  return num.toString()
}

/**
 * 格式化日期时间
 */
function formatDateTime(dateTime: string): string {
  if (!dateTime) return '-'
  // TODO: 使用 date.ts 的格式化方法
  return dateTime
}

// ==================== 生命周期 ====================

onMounted(() => {
  loadSharePages()
})
</script>

<style scoped lang="scss">
.share-page-list-view {
  padding: 20px;
  min-height: 100vh;
  background-color: #f5f7fa;
}

/* 统计卡片 */
.stats-row {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 20px;
  margin-bottom: 20px;
}

.stat-card {
  background: white;
  border-radius: 8px;
  padding: 20px;
  display: flex;
  align-items: center;
  gap: 15px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
  transition: all 0.3s ease;

  &:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
  }

  .stat-icon {
    width: 56px;
    height: 56px;
    border-radius: 12px;
    display: flex;
    align-items: center;
    justify-content: center;
    color: white;
  }

  .stat-content {
    flex: 1;

    .stat-label {
      font-size: 14px;
      color: #909399;
      margin-bottom: 8px;
    }

    .stat-value {
      font-size: 24px;
      font-weight: 600;
      color: #303133;
    }
  }

  &.stat-card--total .stat-icon {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  }

  &.stat-card--active .stat-icon {
    background: linear-gradient(135deg, #67c23a 0%, #85ce61 100%);
  }

  &.stat-card--views .stat-icon {
    background: linear-gradient(135deg, #409eff 0%, #66b1ff 100%);
  }

  &.stat-card--today .stat-icon {
    background: linear-gradient(135deg, #e6a23c 0%, #f5b042 100%);
  }
}

/* 表格自定义单元格 */
.title-cell {
  display: flex;
  align-items: center;
  gap: 8px;

  .title-text {
    flex: 1;
    font-weight: 500;
  }
}

.url-cell {
  :deep(.el-input-group__append) {
    padding: 0;

    .el-button {
      border: none;
    }
  }
}

.access-control-cell {
  display: flex;
  flex-wrap: wrap;
  gap: 5px;
}

/* 对话框内容 */
.stats-content {
  .stats-chart {
    margin-top: 20px;
    min-height: 300px;
    display: flex;
    align-items: center;
    justify-content: center;
  }
}

.qrcode-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 20px;

  .qrcode-placeholder {
    width: 250px;
    height: 250px;
    border: 2px dashed #dcdfe6;
    border-radius: 8px;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    gap: 10px;

    p {
      margin: 0;
      color: #909399;
      font-size: 14px;
    }
  }

  .qrcode-url {
    width: 100%;
  }
}

/* 响应式设计 */
@media screen and (max-width: 1200px) {
  .stats-row {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media screen and (max-width: 768px) {
  .share-page-list-view {
    padding: 10px;
  }

  .stats-row {
    grid-template-columns: 1fr;
    gap: 15px;
  }

  .stat-card {
    padding: 15px;

    .stat-icon {
      width: 48px;
      height: 48px;

      .el-icon {
        font-size: 24px;
      }
    }

    .stat-content {
      .stat-label {
        font-size: 13px;
      }

      .stat-value {
        font-size: 20px;
      }
    }
  }

  .url-cell {
    :deep(.el-input) {
      font-size: 12px;
    }
  }
}

@media screen and (max-width: 480px) {
  .share-page-list-view {
    padding: 5px;
  }

  .stats-row {
    gap: 10px;
  }

  .stat-card {
    padding: 12px;
  }

  .qrcode-content {
    .qrcode-placeholder {
      width: 200px;
      height: 200px;

      .el-icon {
        font-size: 120px !important;
      }
    }
  }
}
</style>
