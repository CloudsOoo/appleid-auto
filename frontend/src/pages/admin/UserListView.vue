<template>
  <div class="page-container">
    <PageHeader title="用户管理" description="管理系统用户" />

    <el-card>
      <!-- 搜索栏 -->
      <div class="search-bar">
        <el-input
          v-model="searchQuery"
          placeholder="搜索用户名或邮箱"
          clearable
          style="width: 250px"
          @keyup.enter="searchUsers"
        >
          <template #prefix>
            <el-icon><Search /></el-icon>
          </template>
        </el-input>
        <el-select v-model="roleFilter" placeholder="角色筛选" clearable style="width: 120px">
          <el-option label="管理员" value="admin" />
          <el-option label="普通用户" value="user" />
        </el-select>
        <el-select v-model="statusFilter" placeholder="状态筛选" clearable style="width: 120px">
          <el-option label="已激活" :value="true" />
          <el-option label="已禁用" :value="false" />
        </el-select>
        <el-button type="primary" @click="searchUsers">搜索</el-button>
        <el-button @click="resetSearch">重置</el-button>
      </div>

      <!-- 用户列表 -->
      <el-table :data="userList" v-loading="loading" stripe>
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="username" label="用户名" width="150" />
        <el-table-column prop="email" label="邮箱" min-width="200" />
        <el-table-column prop="role" label="角色" width="100">
          <template #default="{ row }">
            <el-tag :type="row.role === 'admin' ? 'danger' : 'info'">
              {{ row.role === 'admin' ? '管理员' : '用户' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="is_active" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="row.is_active ? 'success' : 'info'">
              {{ row.is_active ? '已激活' : '已禁用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="注册时间" width="180">
          <template #default="{ row }">
            {{ formatDate(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <el-button size="small" @click="viewUser(row)">详情</el-button>
            <el-button
              size="small"
              :type="row.is_active ? 'warning' : 'success'"
              @click="toggleUserStatus(row)"
            >
              {{ row.is_active ? '禁用' : '启用' }}
            </el-button>
            <el-button size="small" type="danger" @click="deleteUser(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
      <div class="pagination-container">
        <el-pagination
          v-model:current-page="pagination.page"
          v-model:page-size="pagination.pageSize"
          :total="pagination.total"
          :page-sizes="[10, 20, 50, 100]"
          layout="total, sizes, prev, pager, next"
          @size-change="loadUserList"
          @current-change="loadUserList"
        />
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Search } from '@element-plus/icons-vue'
import PageHeader from '@/components/common/PageHeader.vue'
import request from '@/utils/request'
import dayjs from 'dayjs'

const loading = ref(false)
const userList = ref<any[]>([])
const searchQuery = ref('')
const roleFilter = ref('')
const statusFilter = ref<boolean | ''>('')

const pagination = reactive({
  page: 1,
  pageSize: 20,
  total: 0
})

// 加载用户列表
const loadUserList = async () => {
  loading.value = true
  try {
    const response = await request.get('/users', {
      params: {
        page: pagination.page,
        per_page: pagination.pageSize,
        search: searchQuery.value || undefined,
        role: roleFilter.value || undefined,
        is_active: statusFilter.value !== '' ? statusFilter.value : undefined
      }
    })
    userList.value = response.data.items || []
    pagination.total = response.data.total || 0
  } catch (error: any) {
    ElMessage.error(error.response?.data?.message || '加载失败')
  } finally {
    loading.value = false
  }
}

// 搜索用户
const searchUsers = () => {
  pagination.page = 1
  loadUserList()
}

// 重置搜索
const resetSearch = () => {
  searchQuery.value = ''
  roleFilter.value = ''
  statusFilter.value = ''
  pagination.page = 1
  loadUserList()
}

// 查看用户详情
const viewUser = (user: any) => {
  ElMessage.info(`用户: ${user.username}`)
}

// 切换用户状态
const toggleUserStatus = async (user: any) => {
  const action = user.is_active ? '禁用' : '启用'
  try {
    await ElMessageBox.confirm(`确定要${action}用户 ${user.username} 吗？`, `确认${action}`)
    await request.patch(`/users/${user.id}/status`, null, {
      params: { is_active: !user.is_active }
    })
    ElMessage.success(`用户已${action}`)
    loadUserList()
  } catch (error: any) {
    if (error !== 'cancel') {
      ElMessage.error(error.response?.data?.message || '操作失败')
    }
  }
}

// 删除用户
const deleteUser = async (user: any) => {
  try {
    await ElMessageBox.confirm(`确定要删除用户 ${user.username} 吗？此操作不可恢复！`, '确认删除', {
      type: 'warning'
    })
    await request.delete(`/users/${user.id}`)
    ElMessage.success('用户已删除')
    loadUserList()
  } catch (error: any) {
    if (error !== 'cancel') {
      ElMessage.error(error.response?.data?.message || '删除失败')
    }
  }
}

// 格式化日期
const formatDate = (date: string) => {
  if (!date) return '-'
  return dayjs(date).format('YYYY-MM-DD HH:mm')
}

onMounted(() => {
  loadUserList()
})
</script>

<style scoped lang="scss">
.search-bar {
  display: flex;
  gap: 12px;
  margin-bottom: 16px;
  flex-wrap: wrap;
}

.pagination-container {
  display: flex;
  justify-content: flex-end;
  margin-top: 16px;
}
</style>
