<template>
  <div class="page-container">
    <PageHeader title="管理员面板" description="系统整体运行状态概览" />

    <!-- 统计卡片 -->
    <el-row :gutter="20" class="stats-row">
      <el-col :xs="24" :sm="12" :md="6">
        <el-card class="stat-card">
          <el-statistic title="用户总数" :value="stats.users?.total || 0">
            <template #suffix>
              <span class="stat-suffix">今日新增 {{ stats.users?.new_today || 0 }}</span>
            </template>
          </el-statistic>
        </el-card>
      </el-col>
      <el-col :xs="24" :sm="12" :md="6">
        <el-card class="stat-card">
          <el-statistic title="账号总数" :value="stats.accounts?.total || 0">
            <template #suffix>
              <span class="stat-suffix">正常 {{ stats.accounts?.normal || 0 }}</span>
            </template>
          </el-statistic>
        </el-card>
      </el-col>
      <el-col :xs="24" :sm="12" :md="6">
        <el-card class="stat-card">
          <el-statistic title="任务总数" :value="stats.tasks?.total || 0">
            <template #suffix>
              <span class="stat-suffix">成功率 {{ stats.tasks?.success_rate || 0 }}%</span>
            </template>
          </el-statistic>
        </el-card>
      </el-col>
      <el-col :xs="24" :sm="12" :md="6">
        <el-card class="stat-card">
          <el-statistic title="卡密库存" :value="stats.cards?.unused || 0">
            <template #suffix>
              <span class="stat-suffix">总数 {{ stats.cards?.total || 0 }}</span>
            </template>
          </el-statistic>
        </el-card>
      </el-col>
    </el-row>

    <!-- 系统状态 -->
    <el-row :gutter="20" class="status-row">
      <el-col :xs="24" :md="12">
        <el-card>
          <template #header>
            <span>系统组件状态</span>
          </template>
          <div class="status-list">
            <div class="status-item">
              <span class="status-label">代理池</span>
              <el-tag :type="stats.proxies?.active > 0 ? 'success' : 'danger'">
                {{ stats.proxies?.active || 0 }} / {{ stats.proxies?.total || 0 }} 在线
              </el-tag>
            </div>
            <div class="status-item">
              <span class="status-label">执行节点</span>
              <el-tag :type="stats.nodes?.online > 0 ? 'success' : 'danger'">
                {{ stats.nodes?.online || 0 }} / {{ stats.nodes?.total || 0 }} 在线
              </el-tag>
            </div>
            <div class="status-item">
              <span class="status-label">分享页</span>
              <el-tag type="info">
                {{ stats.share_pages?.active || 0 }} / {{ stats.share_pages?.total || 0 }} 启用
              </el-tag>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :xs="24" :md="12">
        <el-card>
          <template #header>
            <span>快捷操作</span>
          </template>
          <div class="quick-actions">
            <el-button type="primary" @click="$router.push('/admin/cards/generate')">
              <el-icon><Tickets /></el-icon>
              生成卡密
            </el-button>
            <el-button @click="$router.push('/admin/users')">
              <el-icon><User /></el-icon>
              用户管理
            </el-button>
            <el-button @click="$router.push('/admin/packages')">
              <el-icon><Box /></el-icon>
              套餐管理
            </el-button>
            <el-button @click="$router.push('/admin/stats')">
              <el-icon><DataAnalysis /></el-icon>
              统计分析
            </el-button>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { Tickets, User, Box, DataAnalysis } from '@element-plus/icons-vue'
import PageHeader from '@/components/common/PageHeader.vue'
import request from '@/utils/request'

const stats = ref<any>({})

// 加载统计数据
const loadStats = async () => {
  try {
    const response = await request.get('/admin/stats/overview')
    stats.value = response.data || {}
  } catch (error) {
    console.error('加载统计数据失败', error)
  }
}

onMounted(() => {
  loadStats()
})
</script>

<style scoped lang="scss">
.stats-row {
  margin-bottom: 20px;
}

.stat-card {
  .stat-suffix {
    font-size: 12px;
    color: #909399;
    margin-left: 8px;
  }
}

.status-row {
  margin-bottom: 20px;
}

.status-list {
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.status-item {
  display: flex;
  justify-content: space-between;
  align-items: center;

  .status-label {
    font-size: 14px;
    color: #606266;
  }
}

.quick-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}
</style>
