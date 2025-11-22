<template>
  <div class="page-container">
    <div class="page-header">
      <h1 class="page-title">管理员面板</h1>
    </div>

    <el-row :gutter="20">
      <el-col :span="6">
        <el-card class="stat-card">
          <el-statistic title="总用户数" :value="stats.users" />
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card">
          <el-statistic title="总账号数" :value="stats.accounts" />
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card">
          <el-statistic title="活跃卡密" :value="stats.activeCards" />
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card">
          <el-statistic title="今日任务" :value="stats.todayTasks" />
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="20" style="margin-top: 20px;">
      <el-col :span="12">
        <el-card>
          <template #header>最近用户</template>
          <el-table :data="recentUsers" size="small">
            <el-table-column prop="username" label="用户名" />
            <el-table-column prop="email" label="邮箱" />
            <el-table-column prop="created_at" label="注册时间" />
          </el-table>
        </el-card>
      </el-col>
      <el-col :span="12">
        <el-card>
          <template #header>最近任务</template>
          <el-table :data="recentTasks" size="small">
            <el-table-column prop="id" label="ID" width="80" />
            <el-table-column prop="type" label="类型" />
            <el-table-column prop="status" label="状态" />
          </el-table>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'

const stats = ref({
  users: 0,
  accounts: 0,
  activeCards: 0,
  todayTasks: 0
})

const recentUsers = ref<any[]>([])
const recentTasks = ref<any[]>([])

onMounted(async () => {
  // TODO: 获取统计数据
})
</script>

<style scoped lang="scss">
.stat-card {
  text-align: center;
}
</style>
