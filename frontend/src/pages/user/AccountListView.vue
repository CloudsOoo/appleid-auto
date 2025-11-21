<!--
  账号列表页面

  职责：
  - 显示用户的 Apple ID 账号列表
  - 支持搜索和筛选（状态、创建时间）
  - 支持添加/编辑/删除账号
  - 支持批量删除
  - 支持手动检测账号状态
  - 支持导出账号数据
  - 查看密码历史记录

  上游依赖：
  - PageHeader（页面标题组件）
  - DataTable（表格组件）
  - StatusTag（状态标签组件）
  - FormDialog（表单对话框组件）
  - Vue Router（页面跳转）
  - Element Plus（UI 组件）

  下游调用者：
  - 路由（/accounts）
  - Dashboard（查看全部账号链接）
  - 侧边栏导航
-->

<template>
  <div class="account-list-view">
    <!-- 页面标题 -->
    <PageHeader
      title="账号管理"
      description="管理您的 Apple ID 账号"
      :breadcrumbs="[
        { title: '首页', path: '/' },
        { title: '账号管理' }
      ]"
    >
      <template #actions>
        <el-button type="primary" :icon="Plus" @click="handleAdd">
          添加账号
        </el-button>
        <el-button :icon="Upload" @click="handleImport">批量导入</el-button>
        <el-button :icon="Download" @click="handleExport">导出</el-button>
      </template>
    </PageHeader>

    <!-- 数据表格 -->
    <div class="table-card">
      <DataTable
        :data="accountList"
        :columns="tableColumns"
        :loading="loading"
        :total="total"
        :current-page="currentPage"
        :page-size="pageSize"
        :show-selection="true"
        :show-toolbar="true"
        :show-search="true"
        :show-refresh="true"
        :show-export="false"
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
        <!-- 自定义列：Apple ID -->
        <template #column-apple_id="{ row }">
          <div class="apple-id-cell">
            <el-icon class="account-icon"><UserFilled /></el-icon>
            <span>{{ row.apple_id }}</span>
          </div>
        </template>

        <!-- 自定义列：状态 -->
        <template #column-status="{ row }">
          <StatusTag :status="row.status" :text="row.statusText" />
        </template>

        <!-- 工具栏自定义操作 -->
        <template #toolbar-actions>
          <el-select
            v-model="filterStatus"
            placeholder="筛选状态"
            clearable
            style="width: 150px"
            @change="handleFilterChange"
          >
            <el-option label="全部" value="" />
            <el-option label="正常" value="unlocked" />
            <el-option label="已锁定" value="locked" />
            <el-option label="待验证" value="pending" />
          </el-select>
        </template>
      </DataTable>
    </div>

    <!-- 添加/编辑账号对话框 -->
    <FormDialog
      v-model="dialogVisible"
      :title="dialogTitle"
      :fields="formFields"
      :initial-data="currentAccount"
      :rules="formRules"
      @submit="handleSubmit"
      @cancel="handleCancel"
    />

    <!-- 密码历史对话框 -->
    <el-dialog
      v-model="passwordHistoryVisible"
      title="密码历史记录"
      width="600px"
      :close-on-click-modal="false"
    >
      <el-timeline>
        <el-timeline-item
          v-for="(record, index) in passwordHistory"
          :key="index"
          :timestamp="record.updated_at"
          placement="top"
        >
          <div class="password-record">
            <div class="password-text">
              <el-icon><Lock /></el-icon>
              {{ record.password }}
            </div>
            <div class="password-note" v-if="record.note">
              备注：{{ record.note }}
            </div>
          </div>
        </el-timeline-item>
      </el-timeline>

      <el-empty v-if="passwordHistory.length === 0" description="暂无密码历史记录" />

      <template #footer>
        <el-button @click="passwordHistoryVisible = false">关闭</el-button>
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
  Upload,
  Download,
  UserFilled,
  Lock,
  Edit,
  Delete,
  View,
  Refresh as RefreshIcon,
  History
} from '@element-plus/icons-vue'
import PageHeader from '@/components/common/PageHeader.vue'
import DataTable from '@/components/common/DataTable.vue'
import StatusTag from '@/components/common/StatusTag.vue'
import FormDialog from '@/components/common/FormDialog.vue'
import type { TableColumn, ActionButton, BatchAction } from '@/components/common/DataTable.vue'
import type { FormField } from '@/components/common/FormDialog.vue'

const router = useRouter()

/**
 * 表格列配置
 */
const tableColumns: TableColumn[] = [
  { prop: 'id', label: 'ID', width: '80', sortable: true },
  { prop: 'apple_id', label: 'Apple ID', minWidth: '220', sortable: true },
  { prop: 'password', label: '密码', minWidth: '150', showOverflowTooltip: true },
  { prop: 'status', label: '状态', width: '120' },
  { prop: 'last_check_time', label: '最后检测', width: '180', sortable: true },
  { prop: 'created_at', label: '创建时间', width: '180', sortable: true },
  { prop: 'updated_at', label: '更新时间', width: '180', sortable: true }
]

/**
 * 操作按钮配置
 */
const actionButtons: ActionButton[] = [
  { key: 'edit', label: '编辑', type: 'primary', icon: 'Edit' },
  { key: 'check', label: '检测', type: 'warning', icon: 'Refresh' },
  { key: 'history', label: '历史', type: 'info', icon: 'Clock' },
  { key: 'delete', label: '删除', type: 'danger', icon: 'Delete' }
]

/**
 * 批量操作配置
 */
const batchActions: BatchAction[] = [
  { key: 'delete', label: '批量删除', icon: 'Delete' },
  { key: 'check', label: '批量检测', icon: 'Refresh' },
  { key: 'export', label: '导出选中', icon: 'Download' }
]

/**
 * 表单字段配置
 */
const formFields: FormField[] = [
  {
    prop: 'apple_id',
    label: 'Apple ID',
    type: 'email',
    required: true,
    placeholder: '请输入 Apple ID（邮箱格式）',
    prefixIcon: 'Message'
  },
  {
    prop: 'password',
    label: '密码',
    type: 'password',
    required: true,
    placeholder: '请输入密码',
    prefixIcon: 'Lock',
    showWordLimit: false
  },
  {
    prop: 'security_questions',
    label: '安全问题',
    type: 'textarea',
    required: false,
    placeholder: '请输入安全问题及答案（可选）',
    rows: 3
  },
  {
    prop: 'recovery_key',
    label: '恢复密钥',
    type: 'text',
    required: false,
    placeholder: '请输入恢复密钥（可选）'
  },
  {
    prop: 'note',
    label: '备注',
    type: 'textarea',
    required: false,
    placeholder: '请输入备注信息（可选）',
    rows: 2
  }
]

/**
 * 表单验证规则
 */
const formRules: FormRules = {
  apple_id: [
    { required: true, message: '请输入 Apple ID', trigger: 'blur' },
    { type: 'email', message: '请输入有效的邮箱地址', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, message: '密码长度至少 6 位', trigger: 'blur' }
  ]
}

/**
 * 账号列表数据
 */
const accountList = ref<any[]>([])

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
 * 对话框可见性
 */
const dialogVisible = ref(false)

/**
 * 对话框标题
 */
const dialogTitle = computed(() => {
  return currentAccount.value?.id ? '编辑账号' : '添加账号'
})

/**
 * 当前编辑的账号
 */
const currentAccount = ref<any>(null)

/**
 * 密码历史对话框可见性
 */
const passwordHistoryVisible = ref(false)

/**
 * 密码历史记录
 */
const passwordHistory = ref<any[]>([])

/**
 * 加载账号列表
 */
async function loadAccountList() {
  try {
    loading.value = true

    // TODO: 调用 API 获取账号列表
    // import { getAccountListApi } from '@/api/accounts'
    // const response = await getAccountListApi({
    //   page: currentPage.value,
    //   page_size: pageSize.value,
    //   keyword: searchKeyword.value,
    //   status: filterStatus.value
    // })
    // accountList.value = response.items
    // total.value = response.total

    // Mock 数据（临时实现）
    await new Promise(resolve => setTimeout(resolve, 500))

    const mockAccounts = [
      {
        id: 1,
        apple_id: 'user1@icloud.com',
        password: 'Password@123',
        status: 'unlocked',
        statusText: '正常',
        last_check_time: '2025-11-21 14:30:00',
        created_at: '2025-11-15 10:00:00',
        updated_at: '2025-11-21 14:30:00'
      },
      {
        id: 2,
        apple_id: 'user2@icloud.com',
        password: 'MySecret@456',
        status: 'locked',
        statusText: '已锁定',
        last_check_time: '2025-11-21 12:15:00',
        created_at: '2025-11-16 11:20:00',
        updated_at: '2025-11-21 12:15:00'
      },
      {
        id: 3,
        apple_id: 'user3@icloud.com',
        password: 'Test@789',
        status: 'pending',
        statusText: '待验证',
        last_check_time: '2025-11-20 18:45:00',
        created_at: '2025-11-18 15:30:00',
        updated_at: '2025-11-20 18:45:00'
      },
      {
        id: 4,
        apple_id: 'user4@icloud.com',
        password: 'Secure@2024',
        status: 'unlocked',
        statusText: '正常',
        last_check_time: '2025-11-21 16:00:00',
        created_at: '2025-11-19 09:10:00',
        updated_at: '2025-11-21 16:00:00'
      }
    ]

    // 应用筛选
    let filteredAccounts = mockAccounts
    if (filterStatus.value) {
      filteredAccounts = mockAccounts.filter(acc => acc.status === filterStatus.value)
    }
    if (searchKeyword.value) {
      filteredAccounts = filteredAccounts.filter(acc =>
        acc.apple_id.toLowerCase().includes(searchKeyword.value.toLowerCase())
      )
    }

    accountList.value = filteredAccounts
    total.value = filteredAccounts.length
  } catch (error) {
    console.error('[AccountListView] Load accounts error:', error)
    ElMessage.error('加载账号列表失败')
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
  loadAccountList()
}

/**
 * 刷新处理
 */
function handleRefresh() {
  currentPage.value = 1
  searchKeyword.value = ''
  filterStatus.value = ''
  loadAccountList()
}

/**
 * 分页变化
 */
function handlePageChange(page: number) {
  currentPage.value = page
  loadAccountList()
}

/**
 * 每页大小变化
 */
function handleSizeChange(size: number) {
  pageSize.value = size
  currentPage.value = 1
  loadAccountList()
}

/**
 * 筛选变化
 */
function handleFilterChange() {
  currentPage.value = 1
  loadAccountList()
}

/**
 * 添加账号
 */
function handleAdd() {
  currentAccount.value = null
  dialogVisible.value = true
}

/**
 * 导入账号
 */
function handleImport() {
  router.push('/accounts/import')
}

/**
 * 导出账号
 */
function handleExport() {
  ElMessage.success('导出功能开发中...')
  // TODO: 实现导出功能
}

/**
 * 批量操作
 */
async function handleBatchAction(actionKey: string, rows: any[]) {
  switch (actionKey) {
    case 'delete':
      await handleBatchDelete(rows)
      break
    case 'check':
      await handleBatchCheck(rows)
      break
    case 'export':
      ElMessage.success('导出选中账号功能开发中...')
      break
  }
}

/**
 * 批量删除
 */
async function handleBatchDelete(rows: any[]) {
  try {
    await ElMessageBox.confirm(
      `确定要删除选中的 ${rows.length} 个账号吗？此操作不可恢复。`,
      '批量删除',
      {
        type: 'warning',
        confirmButtonText: '确定删除',
        cancelButtonText: '取消'
      }
    )

    // TODO: 调用批量删除 API
    // import { batchDeleteAccountsApi } from '@/api/accounts'
    // await batchDeleteAccountsApi({ ids: rows.map(r => r.id) })

    ElMessage.success('删除成功')
    loadAccountList()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('[AccountListView] Batch delete error:', error)
      ElMessage.error('删除失败')
    }
  }
}

/**
 * 批量检测
 */
async function handleBatchCheck(rows: any[]) {
  try {
    ElMessage.info(`正在检测 ${rows.length} 个账号...`)

    // TODO: 调用批量检测 API
    // import { batchCheckAccountsApi } from '@/api/accounts'
    // await batchCheckAccountsApi({ ids: rows.map(r => r.id) })

    await new Promise(resolve => setTimeout(resolve, 2000))

    ElMessage.success('检测完成')
    loadAccountList()
  } catch (error) {
    console.error('[AccountListView] Batch check error:', error)
    ElMessage.error('检测失败')
  }
}

/**
 * 行操作
 */
async function handleRowAction(actionKey: string, row: any) {
  switch (actionKey) {
    case 'edit':
      handleEdit(row)
      break
    case 'check':
      await handleCheck(row)
      break
    case 'history':
      await handlePasswordHistory(row)
      break
    case 'delete':
      await handleDelete(row)
      break
  }
}

/**
 * 编辑账号
 */
function handleEdit(row: any) {
  currentAccount.value = { ...row }
  dialogVisible.value = true
}

/**
 * 检测账号
 */
async function handleCheck(row: any) {
  try {
    ElMessage.info(`正在检测账号 ${row.apple_id}...`)

    // TODO: 调用检测 API
    // import { checkAccountApi } from '@/api/accounts'
    // await checkAccountApi(row.id)

    await new Promise(resolve => setTimeout(resolve, 1500))

    ElMessage.success('检测完成')
    loadAccountList()
  } catch (error) {
    console.error('[AccountListView] Check account error:', error)
    ElMessage.error('检测失败')
  }
}

/**
 * 查看密码历史
 */
async function handlePasswordHistory(row: any) {
  try {
    // TODO: 调用 API 获取密码历史
    // import { getPasswordHistoryApi } from '@/api/accounts'
    // passwordHistory.value = await getPasswordHistoryApi(row.id)

    // Mock 数据
    passwordHistory.value = [
      {
        password: 'NewPassword@2024',
        updated_at: '2025-11-21 10:30:00',
        note: '定期更新密码'
      },
      {
        password: 'OldPassword@2023',
        updated_at: '2025-08-15 14:20:00',
        note: '初始密码'
      }
    ]

    passwordHistoryVisible.value = true
  } catch (error) {
    console.error('[AccountListView] Get password history error:', error)
    ElMessage.error('获取密码历史失败')
  }
}

/**
 * 删除账号
 */
async function handleDelete(row: any) {
  try {
    await ElMessageBox.confirm(
      `确定要删除账号 ${row.apple_id} 吗？此操作不可恢复。`,
      '删除账号',
      {
        type: 'warning',
        confirmButtonText: '确定删除',
        cancelButtonText: '取消'
      }
    )

    // TODO: 调用删除 API
    // import { deleteAccountApi } from '@/api/accounts'
    // await deleteAccountApi(row.id)

    ElMessage.success('删除成功')
    loadAccountList()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('[AccountListView] Delete account error:', error)
      ElMessage.error('删除失败')
    }
  }
}

/**
 * 行点击
 */
function handleRowClick(row: any) {
  // 可选：点击行查看详情
  // router.push(`/accounts/${row.id}`)
}

/**
 * 表单提交
 */
async function handleSubmit(data: any) {
  try {
    if (currentAccount.value?.id) {
      // 编辑
      // TODO: 调用编辑 API
      // import { updateAccountApi } from '@/api/accounts'
      // await updateAccountApi(currentAccount.value.id, data)

      ElMessage.success('账号更新成功')
    } else {
      // 添加
      // TODO: 调用添加 API
      // import { createAccountApi } from '@/api/accounts'
      // await createAccountApi(data)

      ElMessage.success('账号添加成功')
    }

    dialogVisible.value = false
    loadAccountList()
  } catch (error) {
    console.error('[AccountListView] Submit error:', error)
    throw error // 让 FormDialog 显示错误
  }
}

/**
 * 取消对话框
 */
function handleCancel() {
  dialogVisible.value = false
  currentAccount.value = null
}

/**
 * 组件挂载
 */
onMounted(() => {
  loadAccountList()
})
</script>

<style scoped lang="scss">
.account-list-view {
  padding: 20px;

  .table-card {
    background: #fff;
    border-radius: 8px;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
    padding: 16px;
  }

  .apple-id-cell {
    display: flex;
    align-items: center;
    gap: 8px;

    .account-icon {
      color: #409eff;
      font-size: 16px;
    }
  }

  .password-record {
    .password-text {
      display: flex;
      align-items: center;
      gap: 8px;
      font-size: 14px;
      font-weight: 500;
      color: #303133;
      margin-bottom: 4px;
    }

    .password-note {
      font-size: 13px;
      color: #909399;
    }
  }
}

// 响应式设计
@media (max-width: 768px) {
  .account-list-view {
    padding: 16px;
  }
}

@media (max-width: 480px) {
  .account-list-view {
    padding: 12px;

    .table-card {
      padding: 12px;
    }
  }
}
</style>
