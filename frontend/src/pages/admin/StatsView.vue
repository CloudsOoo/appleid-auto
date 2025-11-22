<template>
  <div class="page-container">
    <div class="page-header">
      <h1 class="page-title">统计分析</h1>
    </div>

    <el-row :gutter="20">
      <el-col :span="6">
        <el-card class="stat-card">
          <el-statistic title="今日新增用户" :value="stats.newUsers" />
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card">
          <el-statistic title="今日解锁任务" :value="stats.todayTasks" />
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card">
          <el-statistic title="成功率" :value="stats.successRate" suffix="%" />
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card">
          <el-statistic title="今日收入" :value="stats.revenue" prefix="$" />
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="20" style="margin-top: 20px;">
      <el-col :span="12">
        <el-card>
          <template #header>用户增长趋势</template>
          <div class="chart-placeholder">图表区域 - 用户增长</div>
        </el-card>
      </el-col>
      <el-col :span="12">
        <el-card>
          <template #header>任务执行趋势</template>
          <div class="chart-placeholder">图表区域 - 任务趋势</div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'

const stats = ref({
  newUsers: 0,
  todayTasks: 0,
  successRate: 0,
  revenue: 0
})

onMounted(async () => {
  // TODO: 获取统计数据
})
</script>

<style scoped lang="scss">
.stat-card {
  text-align: center;
}

.chart-placeholder {
  height: 300px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #f5f7fa;
  border-radius: 4px;
  color: #909399;
}
</style>
