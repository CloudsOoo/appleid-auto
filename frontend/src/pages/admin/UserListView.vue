<!--
  管理员用户管理页面

  职责：
  - 显示用户列表（分页、搜索、筛选）
  - 用户状态管理（启用/禁用）
  - 用户角色管理
  - 用户权限管理
  - 用户删除

  上游依赖：
  - PageHeader（页面标题组件）
  - DataTable（表格组件）
  - StatusTag（状态标签组件）
  - FormDialog（表单对话框组件）
  - LoadingOverlay（加载遮罩组件）
  - Vue Router（页面跳转）
  - Element Plus（UI 组件）
  - user API（用户相关接口）

  下游调用者：
  - 路由（/admin/users）
  - AdminLayout 侧边栏导航
  - Admin Dashboard 快捷操作

  使用的 API：
  - GET /admin/users - 获取用户列表
  - GET /admin/users/:id - 获取用户详情
  - PUT /admin/users/:id - 更新用户信息
  - DELETE /admin/users/:id - 删除用户
  - GET /admin/users/:id/permission - 获取用户权限
  - PUT /admin/users/:id/permission - 更新用户权限
  - POST /admin/users/:id/enable - 启用用户
  - POST /admin/users/:id/disable - 禁用用户
-->

<template>
  <div class="admin-user-list-view">
    <!-- 页面标题 -->
    <PageHeader
      title="用户管理"
      description="管理系统用户、权限和状态"
      :breadcrumbs="[
        { title: '管理后台', path: '/admin' },
        { title: '用户管理' }
      ]"
    >
      <template #actions>
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
            <el-icon><User /></el-icon>
          </div>
          <div class="stat-content">
            <div class="stat-value">{{ stats.total }}</div>
            <div class="stat-label">用户总数</div>
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
            <div class="stat-label">活跃用户</div>
          </div>
        </div>
      </el-col>
      <el-col :xs="12" :sm="6">
        <div class="stat-card stat-admin">
          <div class="stat-icon">
            <el-icon><UserFilled /></el-icon>
          </div>
          <div class="stat-content">
            <div class="stat-value">{{ stats.admins }}</div>
            <div class="stat-label">管理员</div>
          </div>
        </div>
      </el-col>
      <el-col :xs="12" :sm="6">
        <div class="stat-card stat-disabled">
          <div class="stat-icon">
            <el-icon><CircleClose /></el-icon>
          </div>
          <div class="stat-content">
            <div class="stat-value">{{ stats.disabled }}</div>
            <div class="stat-label">已禁用</div>
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
            placeholder="搜索用户名/邮箱"
            clearable
            :prefix-icon="Search"
            @input="handleSearchDebounce"
          />
        </el-col>
        <el-col :xs="12" :sm="6" :md="4">
          <el-select
            v-model="filterRole"
            placeholder="角色"
            clearable
            @change="handleFilter"
          >
            <el-option label="全部" value="" />
            <el-option label="用户" value="user" />
            <el-option label="管理员" value="admin" />
          </el-select>
        </el-col>
        <el-col :xs="12" :sm="6" :md="4">
          <el-select
            v-model="filterStatus"
            placeholder="状态"
            clearable
            @change="handleFilter"
          >
            <el-option label="全部" value="" />
            <el-option label="正常" value="active" />
            <el-option label="禁用" value="disabled" />
          </el-select>
        </el-col>
      </el-row>
    </div>

    <!-- 用户列表 -->
    <DataTable
      :data="userList"
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
      <!-- 用户名列 -->
      <template #column-username="{ row }">
        <div class="user-cell">
          <el-avatar :size="32" :style="{ background: getAvatarColor(row.role) }">
            {{ row.username.charAt(0).toUpperCase() }}
          </el-avatar>
          <div class="user-info">
            <span class="user-name">{{ row.username }}</span>
            <span class="user-email">{{ row.email }}</span>
          </div>
        </div>
      </template>

      <!-- 角色列 -->
      <template #column-role="{ row }">
        <el-tag :type="row.role === 'admin' ? 'danger' : 'primary'" size="small">
          {{ row.role === 'admin' ? '管理员' : '普通用户' }}
        </el-tag>
      </template>

      <!-- 状态列 -->
      <template #column-is_active="{ row }">
        <el-switch
          :model-value="row.is_active"
          :loading="row._statusLoading"
          @change="(val: boolean) => handleStatusChange(row, val)"
          :disabled="row.role === 'admin'"
        />
      </template>

      <!-- 2FA 列 -->
      <template #column-two_factor_enabled="{ row }">
        <StatusTag
          :status="row.two_factor_enabled ? 'success' : 'info'"
          :text="row.two_factor_enabled ? '已启用' : '未启用'"
        />
      </template>

      <!-- 验证状态列 -->
      <template #column-is_verified="{ row }">
        <StatusTag
          :status="row.is_verified ? 'success' : 'warning'"
          :text="row.is_verified ? '已验证' : '未验证'"
        />
      </template>

      <!-- 注册时间列 -->
      <template #column-created_at="{ row }">
        {{ formatTime(row.created_at) }}
      </template>
    </DataTable>

    <!-- 用户详情对话框 -->
    <el-dialog
      v-model="detailDialogVisible"
      title="用户详情"
      width="600px"
      :close-on-click-modal="false"
    >
      <el-descriptions :column="2" border v-if="currentUser">
        <el-descriptions-item label="用户 ID">{{ currentUser.id }}</el-descriptions-item>
        <el-descriptions-item label="用户名">{{ currentUser.username }}</el-descriptions-item>
        <el-descriptions-item label="邮箱">{{ currentUser.email }}</el-descriptions-item>
        <el-descriptions-item label="角色">
          <el-tag :type="currentUser.role === 'admin' ? 'danger' : 'primary'" size="small">
            {{ currentUser.role === 'admin' ? '管理员' : '普通用户' }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="账号状态">
          <StatusTag
            :status="currentUser.is_active ? 'success' : 'danger'"
            :text="currentUser.is_active ? '正常' : '禁用'"
          />
        </el-descriptions-item>
        <el-descriptions-item label="邮箱验证">
          <StatusTag
            :status="currentUser.is_verified ? 'success' : 'warning'"
            :text="currentUser.is_verified ? '已验证' : '未验证'"
          />
        </el-descriptions-item>
        <el-descriptions-item label="2FA 状态">
          <StatusTag
            :status="currentUser.two_factor_enabled ? 'success' : 'info'"
            :text="currentUser.two_factor_enabled ? '已启用' : '未启用'"
          />
        </el-descriptions-item>
        <el-descriptions-item label="注册时间">{{ formatTime(currentUser.created_at) }}</el-descriptions-item>
        <el-descriptions-item label="更新时间" :span="2">{{ formatTime(currentUser.updated_at) }}</el-descriptions-item>
      </el-descriptions>

      <!-- 用户权限信息 -->
      <div class="permission-section" v-if="currentUserPermission">
        <h4>权限配置</h4>
        <el-descriptions :column="2" border size="small">
          <el-descriptions-item label="套餐">
            {{ currentUserPermission.package_id ? `套餐 #${currentUserPermission.package_id}` : '无套餐' }}
          </el-descriptions-item>
          <el-descriptions-item label="到期时间">
            {{ currentUserPermission.expires_at ? formatTime(currentUserPermission.expires_at) : '永久' }}
          </el-descriptions-item>
          <el-descriptions-item label="账号配额">{{ currentUserPermission.max_accounts }}</el-descriptions-item>
          <el-descriptions-item label="分享页配额">{{ currentUserPermission.max_share_pages }}</el-descriptions-item>
          <el-descriptions-item label="节点配额">{{ currentUserPermission.max_nodes }}</el-descriptions-item>
          <el-descriptions-item label="代理配额">{{ currentUserPermission.max_proxies }}</el-descriptions-item>
          <el-descriptions-item label="并发任务">{{ currentUserPermission.max_concurrent_tasks }}</el-descriptions-item>
          <el-descriptions-item label="检测间隔">{{ currentUserPermission.check_interval }} 分钟</el-descriptions-item>
        </el-descriptions>

        <div class="permission-features">
          <el-tag type="success" v-if="currentUserPermission.allow_custom_html">自定义HTML</el-tag>
          <el-tag type="success" v-if="currentUserPermission.allow_api_access">API访问</el-tag>
          <el-tag type="success" v-if="currentUserPermission.allow_export">数据导出</el-tag>
          <el-tag type="success" v-if="currentUserPermission.allow_batch_import">批量导入</el-tag>
        </div>
      </div>

      <template #footer>
        <el-button @click="detailDialogVisible = false">关闭</el-button>
        <el-button type="primary" @click="handleEditPermission" v-if="currentUser?.role !== 'admin'">
          编辑权限
        </el-button>
      </template>
    </el-dialog>

    <!-- 编辑用户对话框 -->
    <el-dialog
      v-model="editDialogVisible"
      title="编辑用户"
      width="500px"
      :close-on-click-modal="false"
    >
      <el-form
        ref="editFormRef"
        :model="editForm"
        :rules="editFormRules"
        label-width="100px"
      >
        <el-form-item label="用户名" prop="username">
          <el-input v-model="editForm.username" placeholder="请输入用户名" />
        </el-form-item>
        <el-form-item label="邮箱" prop="email">
          <el-input v-model="editForm.email" placeholder="请输入邮箱" />
        </el-form-item>
        <el-form-item label="角色" prop="role">
          <el-select v-model="editForm.role" placeholder="请选择角色">
            <el-option label="普通用户" value="user" />
            <el-option label="管理员" value="admin" />
          </el-select>
        </el-form-item>
        <el-form-item label="邮箱验证">
          <el-switch v-model="editForm.is_verified" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="editDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleEditSubmit" :loading="editLoading">
          保存
        </el-button>
      </template>
    </el-dialog>

    <!-- 权限编辑对话框 -->
    <el-dialog
      v-model="permissionDialogVisible"
      title="编辑用户权限"
      width="650px"
      :close-on-click-modal="false"
    >
      <el-form
        ref="permissionFormRef"
        :model="permissionForm"
        :rules="permissionFormRules"
        label-width="120px"
      >
        <el-divider content-position="left">配额设置</el-divider>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="账号配额" prop="max_accounts">
              <el-input-number v-model="permissionForm.max_accounts" :min="0" :max="9999" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="分享页配额" prop="max_share_pages">
              <el-input-number v-model="permissionForm.max_share_pages" :min="0" :max="9999" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="节点配额" prop="max_nodes">
              <el-input-number v-model="permissionForm.max_nodes" :min="0" :max="9999" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="代理配额" prop="max_proxies">
              <el-input-number v-model="permissionForm.max_proxies" :min="0" :max="9999" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="并发任务数" prop="max_concurrent_tasks">
              <el-input-number v-model="permissionForm.max_concurrent_tasks" :min="1" :max="100" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="检测间隔(分)" prop="check_interval">
              <el-input-number v-model="permissionForm.check_interval" :min="1" :max="1440" />
            </el-form-item>
          </el-col>
        </el-row>

        <el-divider content-position="left">功能权限</el-divider>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="自定义HTML">
              <el-switch v-model="permissionForm.allow_custom_html" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="API访问">
              <el-switch v-model="permissionForm.allow_api_access" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="数据导出">
              <el-switch v-model="permissionForm.allow_export" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="批量导入">
              <el-switch v-model="permissionForm.allow_batch_import" />
            </el-form-item>
          </el-col>
        </el-row>

        <el-divider content-position="left">有效期</el-divider>
        <el-form-item label="到期时间" prop="expires_at">
          <el-date-picker
            v-model="permissionForm.expires_at"
            type="datetime"
            placeholder="选择到期时间（不选则永久）"
            value-format="YYYY-MM-DDTHH:mm:ss"
            style="width: 100%"
          />
        </el-form-item>
        <el-form-item label="权限状态">
          <el-switch
            v-model="permissionForm.is_active"
            active-text="启用"
            inactive-text="禁用"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="permissionDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handlePermissionSubmit" :loading="permissionLoading">
          保存
        </el-button>
      </template>
    </el-dialog>

    <LoadingOverlay :visible="pageLoading" text="加载中..." />
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, computed } from 'vue'
import { ElMessage, ElMessageBox, type FormInstance, type FormRules } from 'element-plus'
import {
  Refresh,
  Search,
  User,
  UserFilled,
  CircleCheck,
  CircleClose
} from '@element-plus/icons-vue'
import PageHeader from '@/components/common/PageHeader.vue'
import DataTable from '@/components/common/DataTable.vue'
import StatusTag from '@/components/common/StatusTag.vue'
import LoadingOverlay from '@/components/common/LoadingOverlay.vue'
import type { TableColumn, ActionButton, BatchAction } from '@/components/common/DataTable.vue'
import {
  getUserListApi,
  getUserDetailApi,
  updateUserApi,
  deleteUserApi,
  getUserPermissionApi,
  updateUserPermissionApi,
  enableUserApi,
  disableUserApi,
  type User as UserType,
  type UserPermission,
  type UpdateUserRequest,
  type UpdateUserPermissionRequest
} from '@/api/user'
import { formatDate } from '@/utils/date'

// ==================== 响应式数据 ====================

const loading = ref(false)
const pageLoading = ref(false)

// 统计数据
const stats = reactive({
  total: 0,
  active: 0,
  admins: 0,
  disabled: 0
})

// 用户列表
const userList = ref<(UserType & { _statusLoading?: boolean })[]>([])

// 分页
const pagination = reactive({
  page: 1,
  pageSize: 20,
  total: 0
})

// 筛选
const searchKeyword = ref('')
const filterRole = ref('')
const filterStatus = ref('')
let searchTimer: ReturnType<typeof setTimeout> | null = null

// 选中的用户
const selectedUsers = ref<UserType[]>([])

// 当前用户详情
const currentUser = ref<UserType | null>(null)
const currentUserPermission = ref<UserPermission | null>(null)

// 对话框
const detailDialogVisible = ref(false)
const editDialogVisible = ref(false)
const permissionDialogVisible = ref(false)

// 编辑表单
const editFormRef = ref<FormInstance>()
const editForm = reactive<UpdateUserRequest>({
  username: '',
  email: '',
  role: 'user',
  is_verified: false
})
const editLoading = ref(false)

// 权限表单
const permissionFormRef = ref<FormInstance>()
const permissionForm = reactive<UpdateUserPermissionRequest>({
  max_accounts: 10,
  max_share_pages: 5,
  max_nodes: 3,
  max_proxies: 10,
  max_concurrent_tasks: 3,
  check_interval: 60,
  allow_custom_html: false,
  allow_api_access: false,
  allow_export: false,
  allow_batch_import: false,
  expires_at: null,
  is_active: true
})
const permissionLoading = ref(false)

// ==================== 表格配置 ====================

const columns: TableColumn[] = [
  { prop: 'id', label: 'ID', width: 70 },
  { prop: 'username', label: '用户信息', minWidth: 200 },
  { prop: 'role', label: '角色', width: 100 },
  { prop: 'is_active', label: '状态', width: 80 },
  { prop: 'two_factor_enabled', label: '2FA', width: 90 },
  { prop: 'is_verified', label: '验证', width: 90 },
  { prop: 'created_at', label: '注册时间', width: 160 }
]

const rowActions: ActionButton[] = [
  { key: 'view', label: '详情', type: 'primary' },
  { key: 'edit', label: '编辑', type: 'warning' },
  { key: 'delete', label: '删除', type: 'danger' }
]

const batchActions: BatchAction[] = [
  { key: 'enable', label: '批量启用', type: 'success' },
  { key: 'disable', label: '批量禁用', type: 'warning' },
  { key: 'delete', label: '批量删除', type: 'danger', confirmText: '确定要删除选中的用户吗？此操作不可恢复！' }
]

// ==================== 表单验证 ====================

const editFormRules: FormRules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 3, max: 50, message: '用户名长度 3-50 个字符', trigger: 'blur' }
  ],
  email: [
    { required: true, message: '请输入邮箱', trigger: 'blur' },
    { type: 'email', message: '请输入正确的邮箱格式', trigger: 'blur' }
  ],
  role: [
    { required: true, message: '请选择角色', trigger: 'change' }
  ]
}

const permissionFormRules: FormRules = {
  max_accounts: [{ required: true, message: '请输入账号配额', trigger: 'blur' }],
  max_share_pages: [{ required: true, message: '请输入分享页配额', trigger: 'blur' }]
}

// ==================== 方法 ====================

// 获取用户列表
async function fetchUserList() {
  loading.value = true
  try {
    const params: any = {
      page: pagination.page,
      per_page: pagination.pageSize
    }
    if (searchKeyword.value) {
      params.search = searchKeyword.value
    }
    if (filterRole.value) {
      params.role = filterRole.value
    }
    if (filterStatus.value) {
      params.is_active = filterStatus.value === 'active'
    }

    const data = await getUserListApi(params)
    userList.value = data.items || []
    pagination.total = data.total || 0

    // 计算统计数据
    calculateStats()
  } catch (error) {
    console.error('获取用户列表失败:', error)
    ElMessage.error('获取用户列表失败')
  } finally {
    loading.value = false
  }
}

// 计算统计数据
function calculateStats() {
  // 这里可以从 API 获取统计数据，暂时从列表计算
  stats.total = pagination.total
  stats.active = userList.value.filter(u => u.is_active).length
  stats.admins = userList.value.filter(u => u.role === 'admin').length
  stats.disabled = userList.value.filter(u => !u.is_active).length
}

// 刷新
function handleRefresh() {
  pagination.page = 1
  fetchUserList()
}

// 搜索防抖
function handleSearchDebounce() {
  if (searchTimer) {
    clearTimeout(searchTimer)
  }
  searchTimer = setTimeout(() => {
    pagination.page = 1
    fetchUserList()
  }, 300)
}

// 筛选
function handleFilter() {
  pagination.page = 1
  fetchUserList()
}

// 分页变化
function handlePageChange({ page, pageSize }: { page: number; pageSize: number }) {
  pagination.page = page
  pagination.pageSize = pageSize
  fetchUserList()
}

// 选择变化
function handleSelectionChange(selection: UserType[]) {
  selectedUsers.value = selection
}

// 行操作
async function handleRowAction({ action, row }: { action: string; row: UserType }) {
  switch (action) {
    case 'view':
      await showUserDetail(row)
      break
    case 'edit':
      showEditDialog(row)
      break
    case 'delete':
      await handleDelete(row)
      break
  }
}

// 批量操作
async function handleBatchAction({ action }: { action: string }) {
  if (selectedUsers.value.length === 0) {
    ElMessage.warning('请先选择用户')
    return
  }

  switch (action) {
    case 'enable':
      await batchUpdateStatus(true)
      break
    case 'disable':
      await batchUpdateStatus(false)
      break
    case 'delete':
      await batchDelete()
      break
  }
}

// 显示用户详情
async function showUserDetail(user: UserType) {
  pageLoading.value = true
  try {
    const [userDetail, permission] = await Promise.all([
      getUserDetailApi(user.id),
      getUserPermissionApi(user.id).catch(() => null)
    ])
    currentUser.value = userDetail
    currentUserPermission.value = permission
    detailDialogVisible.value = true
  } catch (error) {
    console.error('获取用户详情失败:', error)
    ElMessage.error('获取用户详情失败')
  } finally {
    pageLoading.value = false
  }
}

// 显示编辑对话框
function showEditDialog(user: UserType) {
  currentUser.value = user
  editForm.username = user.username
  editForm.email = user.email
  editForm.role = user.role
  editForm.is_verified = user.is_verified
  editDialogVisible.value = true
}

// 提交编辑
async function handleEditSubmit() {
  if (!editFormRef.value || !currentUser.value) return

  try {
    await editFormRef.value.validate()
    editLoading.value = true

    await updateUserApi(currentUser.value.id, editForm)
    ElMessage.success('更新成功')
    editDialogVisible.value = false
    fetchUserList()
  } catch (error) {
    console.error('更新用户失败:', error)
    ElMessage.error('更新用户失败')
  } finally {
    editLoading.value = false
  }
}

// 编辑权限
async function handleEditPermission() {
  if (!currentUser.value) return

  // 填充表单
  if (currentUserPermission.value) {
    Object.assign(permissionForm, {
      max_accounts: currentUserPermission.value.max_accounts,
      max_share_pages: currentUserPermission.value.max_share_pages,
      max_nodes: currentUserPermission.value.max_nodes,
      max_proxies: currentUserPermission.value.max_proxies,
      max_concurrent_tasks: currentUserPermission.value.max_concurrent_tasks,
      check_interval: currentUserPermission.value.check_interval,
      allow_custom_html: currentUserPermission.value.allow_custom_html,
      allow_api_access: currentUserPermission.value.allow_api_access,
      allow_export: currentUserPermission.value.allow_export,
      allow_batch_import: currentUserPermission.value.allow_batch_import,
      expires_at: currentUserPermission.value.expires_at,
      is_active: currentUserPermission.value.is_active
    })
  }

  detailDialogVisible.value = false
  permissionDialogVisible.value = true
}

// 提交权限
async function handlePermissionSubmit() {
  if (!permissionFormRef.value || !currentUser.value) return

  try {
    await permissionFormRef.value.validate()
    permissionLoading.value = true

    await updateUserPermissionApi(currentUser.value.id, permissionForm)
    ElMessage.success('权限更新成功')
    permissionDialogVisible.value = false
    fetchUserList()
  } catch (error) {
    console.error('更新权限失败:', error)
    ElMessage.error('更新权限失败')
  } finally {
    permissionLoading.value = false
  }
}

// 状态切换
async function handleStatusChange(user: UserType & { _statusLoading?: boolean }, active: boolean) {
  user._statusLoading = true
  try {
    if (active) {
      await enableUserApi(user.id)
      ElMessage.success('用户已启用')
    } else {
      await disableUserApi(user.id)
      ElMessage.success('用户已禁用')
    }
    user.is_active = active
    calculateStats()
  } catch (error) {
    console.error('状态更新失败:', error)
    ElMessage.error('状态更新失败')
  } finally {
    user._statusLoading = false
  }
}

// 删除用户
async function handleDelete(user: UserType) {
  if (user.role === 'admin') {
    ElMessage.warning('不能删除管理员账号')
    return
  }

  try {
    await ElMessageBox.confirm(
      `确定要删除用户 "${user.username}" 吗？此操作不可恢复！`,
      '删除确认',
      { type: 'warning' }
    )

    await deleteUserApi(user.id)
    ElMessage.success('删除成功')
    fetchUserList()
  } catch (error: any) {
    if (error !== 'cancel') {
      console.error('删除用户失败:', error)
      ElMessage.error('删除用户失败')
    }
  }
}

// 批量更新状态
async function batchUpdateStatus(active: boolean) {
  const users = selectedUsers.value.filter(u => u.role !== 'admin')
  if (users.length === 0) {
    ElMessage.warning('没有可操作的用户（管理员不可批量操作）')
    return
  }

  try {
    await ElMessageBox.confirm(
      `确定要${active ? '启用' : '禁用'}选中的 ${users.length} 个用户吗？`,
      '批量操作确认',
      { type: 'warning' }
    )

    pageLoading.value = true
    const promises = users.map(u => active ? enableUserApi(u.id) : disableUserApi(u.id))
    await Promise.all(promises)

    ElMessage.success(`已${active ? '启用' : '禁用'} ${users.length} 个用户`)
    fetchUserList()
  } catch (error: any) {
    if (error !== 'cancel') {
      console.error('批量操作失败:', error)
      ElMessage.error('批量操作失败')
    }
  } finally {
    pageLoading.value = false
  }
}

// 批量删除
async function batchDelete() {
  const users = selectedUsers.value.filter(u => u.role !== 'admin')
  if (users.length === 0) {
    ElMessage.warning('没有可删除的用户（管理员不可删除）')
    return
  }

  try {
    pageLoading.value = true
    const promises = users.map(u => deleteUserApi(u.id))
    await Promise.all(promises)

    ElMessage.success(`已删除 ${users.length} 个用户`)
    fetchUserList()
  } catch (error) {
    console.error('批量删除失败:', error)
    ElMessage.error('批量删除失败')
  } finally {
    pageLoading.value = false
  }
}

// 格式化时间
function formatTime(time: string): string {
  return formatDate(time, 'YYYY-MM-DD HH:mm')
}

// 获取头像颜色
function getAvatarColor(role: string): string {
  return role === 'admin' ? '#f56c6c' : '#409eff'
}

// ==================== 生命周期 ====================

onMounted(() => {
  fetchUserList()
})
</script>

<style lang="scss" scoped>
.admin-user-list-view {
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

  &.stat-active .stat-icon {
    background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
  }

  &.stat-admin .stat-icon {
    background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
  }

  &.stat-disabled .stat-icon {
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

// 用户单元格
.user-cell {
  display: flex;
  align-items: center;
  gap: 12px;

  .user-info {
    display: flex;
    flex-direction: column;

    .user-name {
      font-weight: 500;
      color: #303133;
    }

    .user-email {
      font-size: 12px;
      color: #909399;
    }
  }
}

// 权限部分
.permission-section {
  margin-top: 24px;
  padding-top: 16px;
  border-top: 1px solid #ebeef5;

  h4 {
    font-size: 15px;
    font-weight: 600;
    color: #303133;
    margin: 0 0 16px 0;
  }
}

.permission-features {
  margin-top: 16px;
  display: flex;
  gap: 8px;
  flex-wrap: wrap;

  .el-tag {
    border-radius: 6px;
  }
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

  .user-cell {
    .user-info {
      .user-email {
        max-width: 120px;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
      }
    }
  }
}
</style>
