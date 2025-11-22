<template>
  <div class="admin-dashboard">
    <page-header title="管理员面板" />
    <el-row :gutter="20">
      <el-col :span="6">
        <el-card shadow="hover">
          <el-statistic title="总用户数" :value="stats.totalUsers" />
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover">
          <el-statistic title="总账号数" :value="stats.totalAccounts" />
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover">
          <el-statistic title="今日任务" :value="stats.todayTasks" />
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover">
          <el-statistic title="卡密数量" :value="stats.totalCards" />
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { reactive } from 'vue'
import PageHeader from '@/components/common/PageHeader.vue'

const stats = reactive({
  totalUsers: 0,
  totalAccounts: 0,
  todayTasks: 0,
  totalCards: 0
})
</script>

<style scoped>
.admin-dashboard {
  padding: 20px;
}

.el-row {
  margin-top: 20px;
}
</style>
