<template>
  <div class="page-container">
    <div class="page-header">
      <h1 class="page-title">代理池管理</h1>
      <div class="page-actions">
        <el-button type="primary" :icon="Plus" @click="handleAdd">添加代理</el-button>
      </div>
    </div>
    <el-card>
      <el-table :data="proxyList" v-loading="loading">
        <el-table-column prop="host" label="主机" min-width="150" />
        <el-table-column prop="port" label="端口" width="100" />
        <el-table-column prop="type" label="类型" width="100" />
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="row.is_active ? 'success' : 'danger'">
              {{ row.is_active ? '正常' : '异常' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="150" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" link @click="handleTest(row)">测试</el-button>
            <el-button type="danger" link @click="handleDelete(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { Plus } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'

const loading = ref(false)
const proxyList = ref<any[]>([])

const handleAdd = () => {
  ElMessage.info('功能开发中')
}

const handleTest = (row: any) => {
  ElMessage.info(`测试代理: ${row.host}:${row.port}`)
}

const handleDelete = (row: any) => {
  ElMessage.info(`删除代理: ${row.id}`)
}

onMounted(async () => {
  // TODO: 加载代理列表
})
</script>
