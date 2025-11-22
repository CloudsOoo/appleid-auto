<!--
  管理员套餐管理页面

  职责：
  - 显示套餐列表
  - 创建/编辑/删除套餐
  - 套餐配置（13项配额）
  - 功能权限设置
  - 启用/禁用套餐

  上游依赖：
  - PageHeader（页面标题组件）
  - DataTable（表格组件）
  - StatusTag（状态标签组件）
  - LoadingOverlay（加载遮罩组件）
  - Vue Router（页面跳转）
  - Element Plus（UI 组件）
  - package API（套餐相关接口）

  下游调用者：
  - 路由（/admin/packages）
  - AdminLayout 侧边栏导航
  - Admin Dashboard 快捷操作

  使用的 API：
  - GET /admin/packages - 获取套餐列表
  - GET /admin/packages/:id - 获取套餐详情
  - POST /admin/packages - 创建套餐
  - PUT /admin/packages/:id - 更新套餐
  - DELETE /admin/packages/:id - 删除套餐
-->

<template>
  <div class="admin-package-list-view">
    <!-- 页面标题 -->
    <PageHeader
      title="套餐管理"
      description="管理系统套餐、配额和权限"
      :breadcrumbs="[
        { title: '管理后台', path: '/admin' },
        { title: '套餐管理' }
      ]"
    >
      <template #actions>
        <el-button type="primary" :icon="Plus" @click="showCreateDialog">
          新建套餐
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
            <el-icon><GoodsFilled /></el-icon>
          </div>
          <div class="stat-content">
            <div class="stat-value">{{ stats.total }}</div>
            <div class="stat-label">套餐总数</div>
          </div>
        </div>
      </el-col>
      <el-col :xs="12" :sm="6">
        <div class="stat-card stat-active">
          <div class="stat-icon">
            <el-icon><CircleCheck /></el-icon>
          </div>
          <div class="stat-content">
            <div class="stat-value">{{ stats.active }}</div>
            <div class="stat-label">已启用</div>
          </div>
        </div>
      </el-col>
      <el-col :xs="12" :sm="6">
        <div class="stat-card stat-inactive">
          <div class="stat-icon">
            <el-icon><CircleClose /></el-icon>
          </div>
          <div class="stat-content">
            <div class="stat-value">{{ stats.inactive }}</div>
            <div class="stat-label">已禁用</div>
          </div>
        </div>
      </el-col>
      <el-col :xs="12" :sm="6">
        <div class="stat-card stat-price">
          <div class="stat-icon">
            <el-icon><Money /></el-icon>
          </div>
          <div class="stat-content">
            <div class="stat-value">¥{{ stats.avgPrice }}</div>
            <div class="stat-label">平均价格</div>
          </div>
        </div>
      </el-col>
    </el-row>

    <!-- 套餐列表 -->
    <DataTable
      :data="packageList"
      :columns="columns"
      :loading="loading"
      :show-index="true"
      :show-actions="true"
      :row-actions="rowActions"
      pagination-mode="server"
      :total="pagination.total"
      :page-size="pagination.pageSize"
      @page-change="handlePageChange"
      @row-action="handleRowAction"
    >
      <!-- 套餐名称列 -->
      <template #column-name="{ row }">
        <div class="package-name">
          <span class="name">{{ row.name }}</span>
          <span class="description">{{ row.description }}</span>
        </div>
      </template>

      <!-- 价格列 -->
      <template #column-price="{ row }">
        <span class="price-tag">¥{{ row.price }}</span>
      </template>

      <!-- 配额列 -->
      <template #column-quotas="{ row }">
        <div class="quota-tags">
          <el-tooltip content="账号配额">
            <el-tag size="small">账号: {{ row.max_accounts }}</el-tag>
          </el-tooltip>
          <el-tooltip content="分享页配额">
            <el-tag size="small" type="success">分享: {{ row.max_share_pages }}</el-tag>
          </el-tooltip>
          <el-tooltip content="节点配额">
            <el-tag size="small" type="warning">节点: {{ row.max_nodes }}</el-tag>
          </el-tooltip>
        </div>
      </template>

      <!-- 功能权限列 -->
      <template #column-features="{ row }">
        <div class="feature-icons">
          <el-tooltip content="自定义HTML" v-if="row.allow_custom_html">
            <el-icon color="#67c23a"><Check /></el-icon>
          </el-tooltip>
          <el-tooltip content="API访问" v-if="row.allow_api_access">
            <el-icon color="#67c23a"><Connection /></el-icon>
          </el-tooltip>
          <el-tooltip content="批量导入" v-if="row.allow_batch_import">
            <el-icon color="#67c23a"><Upload /></el-icon>
          </el-tooltip>
          <el-tooltip content="密码历史" v-if="row.allow_view_password_history">
            <el-icon color="#67c23a"><View /></el-icon>
          </el-tooltip>
          <span v-if="!hasAnyFeature(row)" class="text-muted">无</span>
        </div>
      </template>

      <!-- 状态列 -->
      <template #column-is_active="{ row }">
        <el-switch
          :model-value="row.is_active"
          :loading="row._statusLoading"
          @change="(val: boolean) => handleStatusChange(row, val)"
        />
      </template>

      <!-- 排序列 -->
      <template #column-sort_order="{ row }">
        <el-tag type="info" size="small">{{ row.sort_order }}</el-tag>
      </template>

      <!-- 创建时间列 -->
      <template #column-created_at="{ row }">
        {{ formatTime(row.created_at) }}
      </template>
    </DataTable>

    <!-- 创建/编辑对话框 -->
    <el-dialog
      v-model="dialogVisible"
      :title="isEdit ? '编辑套餐' : '创建套餐'"
      width="750px"
      :close-on-click-modal="false"
      destroy-on-close
    >
      <el-form
        ref="formRef"
        :model="form"
        :rules="formRules"
        label-width="120px"
        class="package-form"
      >
        <!-- 基本信息 -->
        <el-divider content-position="left">基本信息</el-divider>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="套餐名称" prop="name">
              <el-input v-model="form.name" placeholder="请输入套餐名称" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="价格" prop="price">
              <el-input-number
                v-model="form.price"
                :min="0"
                :precision="2"
                controls-position="right"
                style="width: 100%"
              />
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item label="描述" prop="description">
          <el-input
            v-model="form.description"
            type="textarea"
            :rows="2"
            placeholder="请输入套餐描述"
          />
        </el-form-item>

        <!-- 配额设置 -->
        <el-divider content-position="left">配额设置</el-divider>
        <el-row :gutter="20">
          <el-col :span="8">
            <el-form-item label="账号配额" prop="max_accounts">
              <el-input-number v-model="form.max_accounts" :min="0" :max="99999" style="width: 100%" />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="分享页配额" prop="max_share_pages">
              <el-input-number v-model="form.max_share_pages" :min="0" :max="99999" style="width: 100%" />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="节点配额" prop="max_nodes">
              <el-input-number v-model="form.max_nodes" :min="0" :max="99999" style="width: 100%" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="20">
          <el-col :span="8">
            <el-form-item label="代理配额" prop="max_proxies">
              <el-input-number v-model="form.max_proxies" :min="0" :max="99999" style="width: 100%" />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="并发任务" prop="max_concurrent_tasks">
              <el-input-number v-model="form.max_concurrent_tasks" :min="1" :max="100" style="width: 100%" />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="每日解锁" prop="max_unlock_per_day">
              <el-input-number v-model="form.max_unlock_per_day" :min="0" :max="99999" style="width: 100%" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="20">
          <el-col :span="8">
            <el-form-item label="解锁间隔(分)" prop="min_unlock_interval">
              <el-input-number v-model="form.min_unlock_interval" :min="1" :max="1440" style="width: 100%" />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="单次导入" prop="max_import_per_time">
              <el-input-number v-model="form.max_import_per_time" :min="0" :max="10000" style="width: 100%" />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="排序权重" prop="sort_order">
              <el-input-number v-model="form.sort_order" :min="0" :max="999" style="width: 100%" />
            </el-form-item>
          </el-col>
        </el-row>

        <!-- 功能权限 -->
        <el-divider content-position="left">功能权限</el-divider>
        <el-row :gutter="20">
          <el-col :span="6">
            <el-form-item label="自定义HTML">
              <el-switch v-model="form.allow_custom_html" />
            </el-form-item>
          </el-col>
          <el-col :span="6">
            <el-form-item label="API访问">
              <el-switch v-model="form.allow_api_access" />
            </el-form-item>
          </el-col>
          <el-col :span="6">
            <el-form-item label="批量导入">
              <el-switch v-model="form.allow_batch_import" />
            </el-form-item>
          </el-col>
          <el-col :span="6">
            <el-form-item label="密码历史">
              <el-switch v-model="form.allow_view_password_history" />
            </el-form-item>
          </el-col>
        </el-row>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSubmit" :loading="submitLoading">
          {{ isEdit ? '保存' : '创建' }}
        </el-button>
      </template>
    </el-dialog>

    <!-- 详情对话框 -->
    <el-dialog
      v-model="detailDialogVisible"
      title="套餐详情"
      width="600px"
    >
      <el-descriptions :column="2" border v-if="currentPackage">
        <el-descriptions-item label="套餐 ID">{{ currentPackage.id }}</el-descriptions-item>
        <el-descriptions-item label="套餐名称">{{ currentPackage.name }}</el-descriptions-item>
        <el-descriptions-item label="价格">¥{{ currentPackage.price }}</el-descriptions-item>
        <el-descriptions-item label="状态">
          <StatusTag
            :status="currentPackage.is_active ? 'success' : 'danger'"
            :text="currentPackage.is_active ? '已启用' : '已禁用'"
          />
        </el-descriptions-item>
        <el-descriptions-item label="描述" :span="2">{{ currentPackage.description || '-' }}</el-descriptions-item>
      </el-descriptions>

      <div class="detail-section" v-if="currentPackage">
        <h4>配额设置</h4>
        <el-descriptions :column="3" border size="small">
          <el-descriptions-item label="账号">{{ currentPackage.max_accounts }}</el-descriptions-item>
          <el-descriptions-item label="分享页">{{ currentPackage.max_share_pages }}</el-descriptions-item>
          <el-descriptions-item label="节点">{{ currentPackage.max_nodes }}</el-descriptions-item>
          <el-descriptions-item label="代理">{{ currentPackage.max_proxies }}</el-descriptions-item>
          <el-descriptions-item label="并发任务">{{ currentPackage.max_concurrent_tasks }}</el-descriptions-item>
          <el-descriptions-item label="每日解锁">{{ currentPackage.max_unlock_per_day }}</el-descriptions-item>
          <el-descriptions-item label="解锁间隔">{{ currentPackage.min_unlock_interval }} 分钟</el-descriptions-item>
          <el-descriptions-item label="单次导入">{{ currentPackage.max_import_per_time }}</el-descriptions-item>
          <el-descriptions-item label="排序权重">{{ currentPackage.sort_order }}</el-descriptions-item>
        </el-descriptions>
      </div>

      <div class="detail-section" v-if="currentPackage">
        <h4>功能权限</h4>
        <div class="feature-list">
          <el-tag :type="currentPackage.allow_custom_html ? 'success' : 'info'" size="small">
            自定义HTML: {{ currentPackage.allow_custom_html ? '是' : '否' }}
          </el-tag>
          <el-tag :type="currentPackage.allow_api_access ? 'success' : 'info'" size="small">
            API访问: {{ currentPackage.allow_api_access ? '是' : '否' }}
          </el-tag>
          <el-tag :type="currentPackage.allow_batch_import ? 'success' : 'info'" size="small">
            批量导入: {{ currentPackage.allow_batch_import ? '是' : '否' }}
          </el-tag>
          <el-tag :type="currentPackage.allow_view_password_history ? 'success' : 'info'" size="small">
            密码历史: {{ currentPackage.allow_view_password_history ? '是' : '否' }}
          </el-tag>
        </div>
      </div>

      <template #footer>
        <el-button @click="detailDialogVisible = false">关闭</el-button>
        <el-button type="primary" @click="showEditDialog(currentPackage!)">编辑</el-button>
      </template>
    </el-dialog>

    <LoadingOverlay :visible="pageLoading" text="处理中..." />
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox, type FormInstance, type FormRules } from 'element-plus'
import {
  Refresh,
  Plus,
  GoodsFilled,
  CircleCheck,
  CircleClose,
  Money,
  Check,
  Connection,
  Upload,
  View
} from '@element-plus/icons-vue'
import PageHeader from '@/components/common/PageHeader.vue'
import DataTable from '@/components/common/DataTable.vue'
import StatusTag from '@/components/common/StatusTag.vue'
import LoadingOverlay from '@/components/common/LoadingOverlay.vue'
import type { TableColumn, ActionButton } from '@/components/common/DataTable.vue'
import {
  getAdminPackageListApi,
  createPackageApi,
  updatePackageApi,
  deletePackageApi,
  type Package,
  type CreatePackageRequest,
  type UpdatePackageRequest
} from '@/api/package'
import { formatDate } from '@/utils/date'

// ==================== 响应式数据 ====================

const loading = ref(false)
const pageLoading = ref(false)
const submitLoading = ref(false)

// 统计数据
const stats = reactive({
  total: 0,
  active: 0,
  inactive: 0,
  avgPrice: 0
})

// 套餐列表
const packageList = ref<(Package & { _statusLoading?: boolean })[]>([])

// 分页
const pagination = reactive({
  page: 1,
  pageSize: 20,
  total: 0
})

// 当前套餐
const currentPackage = ref<Package | null>(null)

// 对话框
const dialogVisible = ref(false)
const detailDialogVisible = ref(false)
const isEdit = ref(false)

// 表单
const formRef = ref<FormInstance>()
const form = reactive<CreatePackageRequest>({
  name: '',
  description: '',
  price: 0,
  max_accounts: 10,
  max_share_pages: 5,
  max_nodes: 3,
  max_proxies: 10,
  max_concurrent_tasks: 3,
  min_unlock_interval: 60,
  max_unlock_per_day: 100,
  max_import_per_time: 100,
  allow_custom_html: false,
  allow_api_access: false,
  allow_batch_import: false,
  allow_view_password_history: false,
  sort_order: 0
})

// ==================== 表格配置 ====================

const columns: TableColumn[] = [
  { prop: 'id', label: 'ID', width: 70 },
  { prop: 'name', label: '套餐名称', minWidth: 180 },
  { prop: 'price', label: '价格', width: 100 },
  { prop: 'quotas', label: '配额', minWidth: 200 },
  { prop: 'features', label: '功能', width: 120 },
  { prop: 'is_active', label: '状态', width: 80 },
  { prop: 'sort_order', label: '排序', width: 70 },
  { prop: 'created_at', label: '创建时间', width: 150 }
]

const rowActions: ActionButton[] = [
  { key: 'view', label: '详情', type: 'primary' },
  { key: 'edit', label: '编辑', type: 'warning' },
  { key: 'delete', label: '删除', type: 'danger' }
]

// ==================== 表单验证 ====================

const formRules: FormRules = {
  name: [
    { required: true, message: '请输入套餐名称', trigger: 'blur' },
    { min: 2, max: 50, message: '名称长度 2-50 个字符', trigger: 'blur' }
  ],
  price: [
    { required: true, message: '请输入价格', trigger: 'blur' }
  ],
  max_accounts: [
    { required: true, message: '请输入账号配额', trigger: 'blur' }
  ],
  max_share_pages: [
    { required: true, message: '请输入分享页配额', trigger: 'blur' }
  ],
  max_nodes: [
    { required: true, message: '请输入节点配额', trigger: 'blur' }
  ],
  min_unlock_interval: [
    { required: true, message: '请输入解锁间隔', trigger: 'blur' }
  ],
  max_unlock_per_day: [
    { required: true, message: '请输入每日解锁次数', trigger: 'blur' }
  ],
  max_import_per_time: [
    { required: true, message: '请输入单次导入数量', trigger: 'blur' }
  ]
}

// ==================== 方法 ====================

// 获取套餐列表
async function fetchPackageList() {
  loading.value = true
  try {
    const data = await getAdminPackageListApi({
      page: pagination.page,
      per_page: pagination.pageSize,
      include_inactive: true
    })
    packageList.value = data.items || []
    pagination.total = data.total || 0

    // 计算统计数据
    calculateStats()
  } catch (error) {
    console.error('获取套餐列表失败:', error)
    ElMessage.error('获取套餐列表失败')
  } finally {
    loading.value = false
  }
}

// 计算统计数据
function calculateStats() {
  stats.total = pagination.total
  stats.active = packageList.value.filter(p => p.is_active).length
  stats.inactive = packageList.value.filter(p => !p.is_active).length
  const totalPrice = packageList.value.reduce((sum, p) => sum + p.price, 0)
  stats.avgPrice = packageList.value.length > 0 ? Math.round(totalPrice / packageList.value.length) : 0
}

// 刷新
function handleRefresh() {
  pagination.page = 1
  fetchPackageList()
}

// 分页变化
function handlePageChange({ page, pageSize }: { page: number; pageSize: number }) {
  pagination.page = page
  pagination.pageSize = pageSize
  fetchPackageList()
}

// 行操作
async function handleRowAction({ action, row }: { action: string; row: Package }) {
  currentPackage.value = row

  switch (action) {
    case 'view':
      detailDialogVisible.value = true
      break
    case 'edit':
      showEditDialog(row)
      break
    case 'delete':
      await handleDelete(row)
      break
  }
}

// 显示创建对话框
function showCreateDialog() {
  isEdit.value = false
  resetForm()
  dialogVisible.value = true
}

// 显示编辑对话框
function showEditDialog(pkg: Package) {
  isEdit.value = true
  currentPackage.value = pkg
  Object.assign(form, {
    name: pkg.name,
    description: pkg.description,
    price: pkg.price,
    max_accounts: pkg.max_accounts,
    max_share_pages: pkg.max_share_pages,
    max_nodes: pkg.max_nodes,
    max_proxies: pkg.max_proxies,
    max_concurrent_tasks: pkg.max_concurrent_tasks,
    min_unlock_interval: pkg.min_unlock_interval,
    max_unlock_per_day: pkg.max_unlock_per_day,
    max_import_per_time: pkg.max_import_per_time,
    allow_custom_html: pkg.allow_custom_html,
    allow_api_access: pkg.allow_api_access,
    allow_batch_import: pkg.allow_batch_import,
    allow_view_password_history: pkg.allow_view_password_history,
    sort_order: pkg.sort_order
  })
  detailDialogVisible.value = false
  dialogVisible.value = true
}

// 重置表单
function resetForm() {
  Object.assign(form, {
    name: '',
    description: '',
    price: 0,
    max_accounts: 10,
    max_share_pages: 5,
    max_nodes: 3,
    max_proxies: 10,
    max_concurrent_tasks: 3,
    min_unlock_interval: 60,
    max_unlock_per_day: 100,
    max_import_per_time: 100,
    allow_custom_html: false,
    allow_api_access: false,
    allow_batch_import: false,
    allow_view_password_history: false,
    sort_order: 0
  })
}

// 提交表单
async function handleSubmit() {
  if (!formRef.value) return

  try {
    await formRef.value.validate()
    submitLoading.value = true

    if (isEdit.value && currentPackage.value) {
      await updatePackageApi(currentPackage.value.id, form as UpdatePackageRequest)
      ElMessage.success('套餐更新成功')
    } else {
      await createPackageApi(form)
      ElMessage.success('套餐创建成功')
    }

    dialogVisible.value = false
    fetchPackageList()
  } catch (error) {
    console.error('提交失败:', error)
    ElMessage.error(isEdit.value ? '更新失败' : '创建失败')
  } finally {
    submitLoading.value = false
  }
}

// 状态切换
async function handleStatusChange(pkg: Package & { _statusLoading?: boolean }, active: boolean) {
  pkg._statusLoading = true
  try {
    await updatePackageApi(pkg.id, { is_active: active })
    pkg.is_active = active
    ElMessage.success(active ? '套餐已启用' : '套餐已禁用')
    calculateStats()
  } catch (error) {
    console.error('状态更新失败:', error)
    ElMessage.error('状态更新失败')
  } finally {
    pkg._statusLoading = false
  }
}

// 删除套餐
async function handleDelete(pkg: Package) {
  try {
    await ElMessageBox.confirm(
      `确定要删除套餐 "${pkg.name}" 吗？此操作不可恢复！\n如果有关联的卡密或用户权限，建议禁用而不是删除。`,
      '删除确认',
      { type: 'warning' }
    )

    pageLoading.value = true
    await deletePackageApi(pkg.id)
    ElMessage.success('删除成功')
    fetchPackageList()
  } catch (error: any) {
    if (error !== 'cancel') {
      console.error('删除失败:', error)
      ElMessage.error('删除失败')
    }
  } finally {
    pageLoading.value = false
  }
}

// 格式化时间
function formatTime(time: string): string {
  return formatDate(time, 'YYYY-MM-DD HH:mm')
}

// 检查是否有任何功能权限
function hasAnyFeature(pkg: Package): boolean {
  return pkg.allow_custom_html || pkg.allow_api_access || pkg.allow_batch_import || pkg.allow_view_password_history
}

// ==================== 生命周期 ====================

onMounted(() => {
  fetchPackageList()
})
</script>

<style lang="scss" scoped>
.admin-package-list-view {
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
    .stat-value {
      font-size: 28px;
      font-weight: 700;
      color: #303133;
    }
    .stat-label {
      font-size: 13px;
      color: #909399;
      margin-top: 4px;
    }
  }

  &.stat-total .stat-icon { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); }
  &.stat-active .stat-icon { background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%); }
  &.stat-inactive .stat-icon { background: linear-gradient(135deg, #bdc3c7 0%, #95a5a6 100%); }
  &.stat-price .stat-icon { background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); }
}

// 套餐名称
.package-name {
  display: flex;
  flex-direction: column;
  .name {
    font-weight: 500;
    color: #303133;
  }
  .description {
    font-size: 12px;
    color: #909399;
    margin-top: 2px;
    max-width: 200px;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }
}

// 价格标签
.price-tag {
  font-weight: 600;
  color: #f56c6c;
  font-size: 16px;
}

// 配额标签
.quota-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
}

// 功能图标
.feature-icons {
  display: flex;
  gap: 8px;
  .el-icon {
    font-size: 18px;
  }
}

// 详情部分
.detail-section {
  margin-top: 20px;
  h4 {
    font-size: 14px;
    font-weight: 600;
    color: #303133;
    margin: 0 0 12px 0;
  }
}

.feature-list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

// 文本样式
.text-muted {
  color: #909399;
  font-size: 12px;
}

// 表单样式
.package-form {
  :deep(.el-divider__text) {
    font-weight: 500;
    color: #606266;
  }
}

// 响应式
@media (max-width: 768px) {
  .stat-card {
    padding: 16px;
    .stat-icon {
      width: 40px;
      height: 40px;
      margin-right: 12px;
      .el-icon { font-size: 20px; }
    }
    .stat-content {
      .stat-value { font-size: 24px; }
      .stat-label { font-size: 12px; }
    }
  }
}
</style>
