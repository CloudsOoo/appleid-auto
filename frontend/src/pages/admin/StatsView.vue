<template>
  <div class="page-container">
    <PageHeader title="统计分析" description="系统数据统计与分析" />

    <!-- 概览统计 -->
    <el-row :gutter="20" class="stats-row">
      <el-col :xs="12" :sm="6">
        <el-card class="stat-card">
          <el-statistic title="用户总数" :value="overview.users?.total || 0" />
        </el-card>
      </el-col>
      <el-col :xs="12" :sm="6">
        <el-card class="stat-card">
          <el-statistic title="账号总数" :value="overview.accounts?.total || 0" />
        </el-card>
      </el-col>
      <el-col :xs="12" :sm="6">
        <el-card class="stat-card">
          <el-statistic title="任务总数" :value="overview.tasks?.total || 0" />
        </el-card>
      </el-col>
      <el-col :xs="12" :sm="6">
        <el-card class="stat-card">
          <el-statistic title="任务成功率" :value="overview.tasks?.success_rate || 0" suffix="%" />
        </el-card>
      </el-col>
    </el-row>

    <!-- 时间范围选择 -->
    <el-card class="chart-card">
      <template #header>
        <div class="chart-header">
          <span>趋势分析</span>
          <el-radio-group v-model="days" @change="loadDailyStats">
            <el-radio-button :label="7">近7天</el-radio-button>
            <el-radio-button :label="14">近14天</el-radio-button>
            <el-radio-button :label="30">近30天</el-radio-button>
          </el-radio-group>
        </div>
      </template>

      <!-- 每日统计表格 -->
      <el-table :data="dailyStats" v-loading="loading" stripe>
        <el-table-column prop="date" label="日期" width="120" />
        <el-table-column prop="new_users" label="新增用户" width="100" />
        <el-table-column prop="new_accounts" label="新增账号" width="100" />
        <el-table-column prop="total_tasks" label="任务总数" width="100" />
        <el-table-column prop="success_tasks" label="成功任务" width="100" />
        <el-table-column label="成功率" width="120">
          <template #default="{ row }">
            <el-progress
              :percentage="row.total_tasks > 0 ? Math.round((row.success_tasks / row.total_tasks) * 100) : 0"
              :stroke-width="10"
              :status="row.success_tasks / row.total_tasks >= 0.8 ? 'success' : ''"
            />
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import PageHeader from '@/components/common/PageHeader.vue'
import request from '@/utils/request'

const loading = ref(false)
const days = ref(7)
const overview = ref<any>({})
const dailyStats = ref<any[]>([])

// 加载概览统计
const loadOverview = async () => {
  try {
    const response = await request.get('/admin/stats/overview')
    overview.value = response.data || {}
  } catch (error: any) {
    ElMessage.error(error.response?.data?.message || '加载失败')
  }
}

// 加载每日统计
const loadDailyStats = async () => {
  loading.value = true
  try {
    const response = await request.get('/admin/stats/daily', {
      params: { days: days.value }
    })
    dailyStats.value = response.data.stats || []
  } catch (error: any) {
    ElMessage.error(error.response?.data?.message || '加载失败')
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  loadOverview()
  loadDailyStats()
})
</script>

<style scoped lang="scss">
.stats-row {
  margin-bottom: 20px;
}

.stat-card {
  text-align: center;
}

.chart-card {
  .chart-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
  }
}
</style>
