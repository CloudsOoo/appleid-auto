<template>
  <div class="page-container">
    <PageHeader title="代理池管理" description="管理和监控代理服务器" />

    <el-card>
      <!-- 操作栏 -->
      <div class="toolbar">
        <el-button type="primary" @click="showAddDialog">
          <el-icon><Plus /></el-icon>
          添加代理
        </el-button>
        <el-button @click="refreshList">
          <el-icon><Refresh /></el-icon>
          刷新
        </el-button>
        <el-button @click="testAllProxies" :loading="testing">
          测试全部
        </el-button>
      </div>

      <!-- 代理列表 -->
      <el-table :data="proxyList" v-loading="loading" stripe>
        <el-table-column prop="host" label="主机" width="180" />
        <el-table-column prop="port" label="端口" width="80" />
        <el-table-column prop="proxy_type" label="类型" width="100">
          <template #default="{ row }">
            <el-tag size="small">{{ row.proxy_type?.toUpperCase() }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)">
              {{ getStatusText(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="success_rate" label="成功率" width="100">
          <template #default="{ row }">
            <el-progress
              :percentage="row.success_rate || 0"
              :status="row.success_rate >= 80 ? 'success' : row.success_rate >= 50 ? 'warning' : 'exception'"
              :stroke-width="6"
            />
          </template>
        </el-table-column>
        <el-table-column prop="avg_response_time" label="响应时间" width="100">
          <template #default="{ row }">
            {{ row.avg_response_time ? `${row.avg_response_time}ms` : '-' }}
          </template>
        </el-table-column>
        <el-table-column prop="is_active" label="启用" width="80">
          <template #default="{ row }">
            <el-switch v-model="row.is_active" @change="toggleProxy(row)" />
          </template>
        </el-table-column>
        <el-table-column label="操作" width="150" fixed="right">
          <template #default="{ row }">
            <el-button size="small" @click="testProxy(row)">测试</el-button>
            <el-button size="small" type="danger" @click="deleteProxy(row)">删除</el-button>
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
          @size-change="loadProxyList"
          @current-change="loadProxyList"
        />
      </div>
    </el-card>

    <!-- 添加代理对话框 -->
    <el-dialog v-model="addDialogVisible" title="添加代理" width="500px">
      <el-form :model="proxyForm" label-width="80px">
        <el-form-item label="主机">
          <el-input v-model="proxyForm.host" placeholder="IP 或域名" />
        </el-form-item>
        <el-form-item label="端口">
          <el-input-number v-model="proxyForm.port" :min="1" :max="65535" />
        </el-form-item>
        <el-form-item label="类型">
          <el-select v-model="proxyForm.proxy_type">
            <el-option label="HTTP" value="http" />
            <el-option label="HTTPS" value="https" />
            <el-option label="SOCKS5" value="socks5" />
          </el-select>
        </el-form-item>
        <el-form-item label="用户名">
          <el-input v-model="proxyForm.username" placeholder="可选" />
        </el-form-item>
        <el-form-item label="密码">
          <el-input v-model="proxyForm.password" type="password" placeholder="可选" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="addDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="addProxy" :loading="submitting">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Refresh } from '@element-plus/icons-vue'
import PageHeader from '@/components/common/PageHeader.vue'
import {
  getProxyListApi,
  createProxyApi,
  deleteProxyApi,
  testProxyApi,
  updateProxyApi
} from '@/api/proxy'

const loading = ref(false)
const testing = ref(false)
const submitting = ref(false)
const addDialogVisible = ref(false)
const proxyList = ref<any[]>([])

const pagination = reactive({
  page: 1,
  pageSize: 20,
  total: 0
})

const proxyForm = reactive({
  host: '',
  port: 8080,
  proxy_type: 'http',
  username: '',
  password: ''
})

// 加载代理列表
const loadProxyList = async () => {
  loading.value = true
  try {
    const response = await getProxyListApi({
      page: pagination.page,
      per_page: pagination.pageSize
    })
    proxyList.value = response.data.items || []
    pagination.total = response.data.total || 0
  } catch (error: any) {
    ElMessage.error(error.response?.data?.message || '加载失败')
  } finally {
    loading.value = false
  }
}

// 刷新列表
const refreshList = () => {
  loadProxyList()
}

// 显示添加对话框
const showAddDialog = () => {
  Object.assign(proxyForm, {
    host: '',
    port: 8080,
    proxy_type: 'http',
    username: '',
    password: ''
  })
  addDialogVisible.value = true
}

// 添加代理
const addProxy = async () => {
  if (!proxyForm.host) {
    ElMessage.warning('请输入代理主机')
    return
  }
  submitting.value = true
  try {
    await createProxyApi(proxyForm)
    ElMessage.success('添加成功')
    addDialogVisible.value = false
    loadProxyList()
  } catch (error: any) {
    ElMessage.error(error.response?.data?.message || '添加失败')
  } finally {
    submitting.value = false
  }
}

// 删除代理
const deleteProxy = async (proxy: any) => {
  try {
    await ElMessageBox.confirm('确定要删除此代理吗？', '确认删除')
    await deleteProxyApi(proxy.id)
    ElMessage.success('删除成功')
    loadProxyList()
  } catch (error: any) {
    if (error !== 'cancel') {
      ElMessage.error(error.response?.data?.message || '删除失败')
    }
  }
}

// 测试代理
const testProxy = async (proxy: any) => {
  try {
    await testProxyApi(proxy.id)
    ElMessage.success('测试完成')
    loadProxyList()
  } catch (error: any) {
    ElMessage.error(error.response?.data?.message || '测试失败')
  }
}

// 测试全部代理
const testAllProxies = async () => {
  testing.value = true
  try {
    // TODO: 实现批量测试
    ElMessage.info('正在测试所有代理...')
    await loadProxyList()
  } finally {
    testing.value = false
  }
}

// 切换代理状态
const toggleProxy = async (proxy: any) => {
  try {
    await updateProxyApi(proxy.id, { is_active: proxy.is_active })
    ElMessage.success(`代理已${proxy.is_active ? '启用' : '禁用'}`)
  } catch (error: any) {
    proxy.is_active = !proxy.is_active
    ElMessage.error(error.response?.data?.message || '操作失败')
  }
}

// 获取状态类型
const getStatusType = (status: string) => {
  const types: Record<string, string> = {
    active: 'success',
    failed: 'danger',
    unknown: 'info'
  }
  return types[status] || 'info'
}

// 获取状态文本
const getStatusText = (status: string) => {
  const texts: Record<string, string> = {
    active: '正常',
    failed: '失败',
    unknown: '未知'
  }
  return texts[status] || status
}

onMounted(() => {
  loadProxyList()
})
</script>

<style scoped lang="scss">
.toolbar {
  display: flex;
  gap: 12px;
  margin-bottom: 16px;
}

.pagination-container {
  display: flex;
  justify-content: flex-end;
  margin-top: 16px;
}
</style>
