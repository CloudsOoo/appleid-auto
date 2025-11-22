<template>
  <div class="page-container">
    <div class="page-header">
      <h1 class="page-title">套餐管理</h1>
      <div class="page-actions">
        <el-button type="primary" :icon="Plus" @click="handleAdd">添加套餐</el-button>
      </div>
    </div>

    <el-card>
      <el-table :data="packageList" v-loading="loading">
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="name" label="套餐名称" min-width="150" />
        <el-table-column prop="price" label="价格" width="100">
          <template #default="{ row }">
            {{ row.price }} 元
          </template>
        </el-table-column>
        <el-table-column prop="max_accounts" label="账号配额" width="100" />
        <el-table-column prop="max_share_pages" label="分享页配额" width="100" />
        <el-table-column prop="duration_days" label="有效天数" width="100" />
        <el-table-column prop="is_active" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="row.is_active ? 'success' : 'danger'">
              {{ row.is_active ? '启用' : '禁用' }}
            </el-tag>
          </template>
        </el-table-column>
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
const packageList = ref<any[]>([])

const handleAdd = () => {
  ElMessage.info('功能开发中')
}

const handleEdit = (row: any) => {
  ElMessage.info(`编辑套餐: ${row.name}`)
}

const handleDelete = (row: any) => {
  ElMessage.info(`删除套餐: ${row.name}`)
}

onMounted(async () => {
  // TODO: 加载套餐列表
})
</script>
