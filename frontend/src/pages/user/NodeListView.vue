<template>
  <div class="page-container">
    <div class="page-header">
      <h1 class="page-title">节点管理</h1>
      <div class="page-actions">
        <el-button type="primary" :icon="Plus" @click="handleAdd">添加节点</el-button>
      </div>
    </div>
    <el-card>
      <el-table :data="nodeList" v-loading="loading">
        <el-table-column prop="name" label="节点名称" min-width="150" />
        <el-table-column prop="url" label="地址" min-width="200" />
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="row.is_online ? 'success' : 'danger'">
              {{ row.is_online ? '在线' : '离线' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="last_heartbeat" label="最后心跳" width="180" />
        <el-table-column label="操作" width="150" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" link @click="handleEdit(row)">编辑</el-button>
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
const nodeList = ref<any[]>([])

const handleAdd = () => {
  ElMessage.info('功能开发中')
}

const handleEdit = (row: any) => {
  ElMessage.info(`编辑节点: ${row.name}`)
}

const handleDelete = (row: any) => {
  ElMessage.info(`删除节点: ${row.id}`)
}

onMounted(async () => {
  // TODO: 加载节点列表
})
</script>
