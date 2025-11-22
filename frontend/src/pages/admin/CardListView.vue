<template>
  <div class="page-container">
    <div class="page-header">
      <h1 class="page-title">卡密管理</h1>
      <div class="page-actions">
        <el-button type="primary" @click="$router.push('/admin/cards/generate')">
          生成卡密
        </el-button>
      </div>
    </div>

    <el-card>
      <el-table :data="cardList" v-loading="loading">
        <el-table-column prop="code" label="卡密" min-width="200" />
        <el-table-column prop="package_name" label="套餐" width="120" />
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)">
              {{ getStatusText(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="used_by" label="使用者" width="120" />
        <el-table-column prop="expires_at" label="过期时间" width="180" />
        <el-table-column label="操作" width="150" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" link @click="handleView(row)">详情</el-button>
            <el-button type="danger" link @click="handleRevoke(row)" :disabled="row.status !== 'unused'">
              作废
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <el-pagination
        v-model:current-page="pagination.page"
        v-model:page-size="pagination.per_page"
        :total="pagination.total"
        layout="total, prev, pager, next"
        style="margin-top: 20px; justify-content: flex-end;"
        @current-change="loadCards"
      />
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'

const loading = ref(false)
const cardList = ref<any[]>([])

const pagination = reactive({
  page: 1,
  per_page: 20,
  total: 0
})

const getStatusType = (status: string) => {
  const types: Record<string, string> = {
    unused: 'info',
    active: 'success',
    expired: 'warning',
    revoked: 'danger'
  }
  return types[status] || 'info'
}

const getStatusText = (status: string) => {
  const texts: Record<string, string> = {
    unused: '未使用',
    active: '已激活',
    expired: '已过期',
    revoked: '已作废'
  }
  return texts[status] || status
}

const loadCards = async () => {
  // TODO: 加载卡密列表
}

const handleView = (row: any) => {
  ElMessage.info(`查看卡密: ${row.code}`)
}

const handleRevoke = (row: any) => {
  ElMessage.info(`作废卡密: ${row.code}`)
}

onMounted(() => {
  loadCards()
})
</script>
