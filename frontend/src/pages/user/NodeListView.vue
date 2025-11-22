<template>
  <div class="page-container">
    <PageHeader title="节点管理" description="管理和监控执行节点" />

    <el-card>
      <!-- 操作栏 -->
      <div class="toolbar">
        <el-button type="primary" @click="showAddDialog">
          <el-icon><Plus /></el-icon>
          添加节点
        </el-button>
        <el-button @click="refreshList">
          <el-icon><Refresh /></el-icon>
          刷新
        </el-button>
      </div>

      <!-- 节点列表 -->
      <el-table :data="nodeList" v-loading="loading" stripe>
        <el-table-column prop="node_name" label="节点名称" width="150" />
        <el-table-column prop="node_url" label="节点地址" min-width="200" />
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)">
              {{ getStatusText(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="current_load" label="当前负载" width="150">
          <template #default="{ row }">
            <el-progress
              :percentage="(row.current_load / row.max_load) * 100 || 0"
              :status="row.current_load / row.max_load > 0.8 ? 'exception' : ''"
              :stroke-width="6"
            />
            <span class="load-text">{{ row.current_load || 0 }} / {{ row.max_load || 10 }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="last_heartbeat_at" label="最后心跳" width="180">
          <template #default="{ row }">
            {{ formatTime(row.last_heartbeat_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="150" fixed="right">
          <template #default="{ row }">
            <el-button size="small" @click="viewNodeDetail(row)">详情</el-button>
            <el-button size="small" type="danger" @click="deleteNode(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
      <div class="pagination-container">
        <el-pagination
          v-model:current-page="pagination.page"
          v-model:page-size="pagination.pageSize"
          :total="pagination.total"
          :page-sizes="[10, 20, 50]"
          layout="total, sizes, prev, pager, next"
          @size-change="loadNodeList"
          @current-change="loadNodeList"
        />
      </div>
    </el-card>

    <!-- 添加节点对话框 -->
    <el-dialog v-model="addDialogVisible" title="添加节点" width="500px">
      <el-form :model="nodeForm" label-width="100px">
        <el-form-item label="节点名称">
          <el-input v-model="nodeForm.node_name" placeholder="如: Node-01" />
        </el-form-item>
        <el-form-item label="节点地址">
          <el-input v-model="nodeForm.node_url" placeholder="http://ip:port" />
        </el-form-item>
        <el-form-item label="API密钥">
          <el-input v-model="nodeForm.api_key" placeholder="节点验证密钥" />
        </el-form-item>
        <el-form-item label="最大负载">
          <el-input-number v-model="nodeForm.max_load" :min="1" :max="100" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="addDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="addNode" :loading="submitting">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Refresh } from '@element-plus/icons-vue'
import PageHeader from '@/components/common/PageHeader.vue'
import { getNodeListApi, createNodeApi, deleteNodeApi } from '@/api/node'
import dayjs from 'dayjs'

const loading = ref(false)
const submitting = ref(false)
const addDialogVisible = ref(false)
const nodeList = ref<any[]>([])

const pagination = reactive({
  page: 1,
  pageSize: 20,
  total: 0
})

const nodeForm = reactive({
  node_name: '',
  node_url: '',
  api_key: '',
  max_load: 10
})

// 加载节点列表
const loadNodeList = async () => {
  loading.value = true
  try {
    const response = await getNodeListApi({
      page: pagination.page,
      per_page: pagination.pageSize
    })
    nodeList.value = response.data.items || []
    pagination.total = response.data.total || 0
  } catch (error: any) {
    ElMessage.error(error.response?.data?.message || '加载失败')
  } finally {
    loading.value = false
  }
}

// 刷新列表
const refreshList = () => {
  loadNodeList()
}

// 显示添加对话框
const showAddDialog = () => {
  Object.assign(nodeForm, {
    node_name: '',
    node_url: '',
    api_key: '',
    max_load: 10
  })
  addDialogVisible.value = true
}

// 添加节点
const addNode = async () => {
  if (!nodeForm.node_name || !nodeForm.node_url) {
    ElMessage.warning('请填写节点名称和地址')
    return
  }
  submitting.value = true
  try {
    await createNodeApi(nodeForm)
    ElMessage.success('添加成功')
    addDialogVisible.value = false
    loadNodeList()
  } catch (error: any) {
    ElMessage.error(error.response?.data?.message || '添加失败')
  } finally {
    submitting.value = false
  }
}

// 删除节点
const deleteNode = async (node: any) => {
  try {
    await ElMessageBox.confirm('确定要删除此节点吗？', '确认删除')
    await deleteNodeApi(node.id)
    ElMessage.success('删除成功')
    loadNodeList()
  } catch (error: any) {
    if (error !== 'cancel') {
      ElMessage.error(error.response?.data?.message || '删除失败')
    }
  }
}

// 查看节点详情
const viewNodeDetail = (node: any) => {
  ElMessage.info(`节点: ${node.node_name}`)
}

// 格式化时间
const formatTime = (time: string) => {
  if (!time) return '-'
  return dayjs(time).format('YYYY-MM-DD HH:mm:ss')
}

// 获取状态类型
const getStatusType = (status: string) => {
  const types: Record<string, string> = {
    online: 'success',
    offline: 'danger',
    error: 'warning'
  }
  return types[status] || 'info'
}

// 获取状态文本
const getStatusText = (status: string) => {
  const texts: Record<string, string> = {
    online: '在线',
    offline: '离线',
    error: '异常'
  }
  return texts[status] || status
}

onMounted(() => {
  loadNodeList()
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

.load-text {
  font-size: 12px;
  color: #909399;
  margin-left: 8px;
}
</style>
