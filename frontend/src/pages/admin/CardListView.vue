<template>
  <div class="page-container">
    <PageHeader title="卡密管理" description="管理系统卡密" />

    <el-card>
      <!-- 操作栏 -->
      <div class="toolbar">
        <el-button type="primary" @click="$router.push('/admin/cards/generate')">
          <el-icon><Plus /></el-icon>
          生成卡密
        </el-button>
        <el-select v-model="statusFilter" placeholder="状态筛选" clearable style="width: 120px" @change="loadCardList">
          <el-option label="未使用" value="unused" />
          <el-option label="已使用" value="used" />
          <el-option label="已禁用" value="disabled" />
        </el-select>
        <el-button @click="refreshList">
          <el-icon><Refresh /></el-icon>
          刷新
        </el-button>
      </div>

      <!-- 卡密列表 -->
      <el-table :data="cardList" v-loading="loading" stripe>
        <el-table-column prop="card_code" label="卡密" min-width="200">
          <template #default="{ row }">
            <span class="card-code">{{ row.card_code }}</span>
            <el-button link size="small" @click="copyCode(row.card_code)">
              <el-icon><CopyDocument /></el-icon>
            </el-button>
          </template>
        </el-table-column>
        <el-table-column prop="package_name" label="套餐" width="120" />
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)">
              {{ getStatusText(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="used_by_username" label="使用者" width="120">
          <template #default="{ row }">
            {{ row.used_by_username || '-' }}
          </template>
        </el-table-column>
        <el-table-column prop="used_at" label="使用时间" width="180">
          <template #default="{ row }">
            {{ row.used_at ? formatDate(row.used_at) : '-' }}
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="180">
          <template #default="{ row }">
            {{ formatDate(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="150" fixed="right">
          <template #default="{ row }">
            <el-button
              v-if="row.status === 'unused'"
              size="small"
              type="warning"
              @click="disableCard(row)"
            >
              禁用
            </el-button>
            <el-button size="small" type="danger" @click="deleteCard(row)">删除</el-button>
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
          @size-change="loadCardList"
          @current-change="loadCardList"
        />
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Refresh, CopyDocument } from '@element-plus/icons-vue'
import PageHeader from '@/components/common/PageHeader.vue'
import { getCardListApi, deleteCardApi, updateCardApi } from '@/api/card'
import dayjs from 'dayjs'

const loading = ref(false)
const cardList = ref<any[]>([])
const statusFilter = ref('')

const pagination = reactive({
  page: 1,
  pageSize: 20,
  total: 0
})

// 加载卡密列表
const loadCardList = async () => {
  loading.value = true
  try {
    const response = await getCardListApi({
      page: pagination.page,
      per_page: pagination.pageSize,
      status: statusFilter.value || undefined
    })
    cardList.value = response.data.items || []
    pagination.total = response.data.total || 0
  } catch (error: any) {
    ElMessage.error(error.response?.data?.message || '加载失败')
  } finally {
    loading.value = false
  }
}

// 刷新列表
const refreshList = () => {
  loadCardList()
}

// 复制卡密
const copyCode = async (code: string) => {
  try {
    await navigator.clipboard.writeText(code)
    ElMessage.success('已复制到剪贴板')
  } catch {
    ElMessage.error('复制失败')
  }
}

// 禁用卡密
const disableCard = async (card: any) => {
  try {
    await ElMessageBox.confirm('确定要禁用此卡密吗？', '确认禁用')
    await updateCardApi(card.id, { status: 'disabled' })
    ElMessage.success('卡密已禁用')
    loadCardList()
  } catch (error: any) {
    if (error !== 'cancel') {
      ElMessage.error(error.response?.data?.message || '操作失败')
    }
  }
}

// 删除卡密
const deleteCard = async (card: any) => {
  try {
    await ElMessageBox.confirm('确定要删除此卡密吗？', '确认删除', { type: 'warning' })
    await deleteCardApi(card.id)
    ElMessage.success('卡密已删除')
    loadCardList()
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

// 获取状态类型
const getStatusType = (status: string) => {
  const types: Record<string, string> = {
    unused: 'success',
    used: 'info',
    disabled: 'danger'
  }
  return types[status] || 'info'
}

// 获取状态文本
const getStatusText = (status: string) => {
  const texts: Record<string, string> = {
    unused: '未使用',
    used: '已使用',
    disabled: '已禁用'
  }
  return texts[status] || status
}

onMounted(() => {
  loadCardList()
})
</script>

<style scoped lang="scss">
.toolbar {
  display: flex;
  gap: 12px;
  margin-bottom: 16px;
}

.card-code {
  font-family: monospace;
  font-size: 13px;
}

.pagination-container {
  display: flex;
  justify-content: flex-end;
  margin-top: 16px;
}
</style>
