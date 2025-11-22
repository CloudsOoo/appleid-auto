<!--
  管理员统计分析页面

  职责：
  - 显示系统整体统计数据
  - 展示各模块趋势图表
  - 支持时间范围筛选
  - 多维度数据分析

  上游依赖：
  - PageHeader（页面标题组件）
  - LoadingOverlay（加载遮罩组件）
  - Vue Router（页面跳转）
  - Element Plus（UI 组件）
  - stats API（统计相关接口）

  下游调用者：
  - 路由（/admin/stats）
  - AdminLayout 侧边栏导航
  - Admin Dashboard 快捷操作

  使用的 API：
  - GET /stats/admin/overview - 获取管理员统计概览
  - GET /stats/admin/accounts - 获取账号统计趋势
  - GET /stats/admin/tasks - 获取任务统计趋势
  - GET /stats/admin/users/growth - 获取用户增长统计
  - GET /stats/admin/cards - 获取卡密使用统计
-->

<template>
  <div class="admin-stats-view">
    <!-- 页面标题 -->
    <PageHeader
      title="数据统计"
      description="系统运营数据分析与统计"
      :breadcrumbs="[
        { title: '管理后台', path: '/admin' },
        { title: '数据统计' }
      ]"
    >
      <template #actions>
        <el-date-picker
          v-model="dateRange"
          type="daterange"
          range-separator="至"
          start-placeholder="开始日期"
          end-placeholder="结束日期"
          value-format="YYYY-MM-DD"
          :shortcuts="dateShortcuts"
          @change="handleDateChange"
          style="width: 260px"
        />
        <el-button :icon="Refresh" @click="handleRefresh" :loading="loading">
          刷新
        </el-button>
      </template>
    </PageHeader>

    <!-- 概览统计卡片 -->
    <el-row :gutter="20" class="stats-row">
      <el-col :xs="12" :sm="6" :lg="3">
        <div class="stat-card stat-users">
          <div class="stat-icon"><el-icon><User /></el-icon></div>
          <div class="stat-content">
            <div class="stat-value">{{ overview.users?.total || 0 }}</div>
            <div class="stat-label">用户总数</div>
            <div class="stat-extra">
              <span class="success">+{{ overview.users?.today_new || 0 }} 今日</span>
            </div>
          </div>
        </div>
      </el-col>
      <el-col :xs="12" :sm="6" :lg="3">
        <div class="stat-card stat-accounts">
          <div class="stat-icon"><el-icon><UserFilled /></el-icon></div>
          <div class="stat-content">
            <div class="stat-value">{{ overview.accounts?.total || 0 }}</div>
            <div class="stat-label">账号总数</div>
            <div class="stat-extra">
              <span class="warning">{{ overview.accounts?.locked || 0 }} 锁定</span>
            </div>
          </div>
        </div>
      </el-col>
      <el-col :xs="12" :sm="6" :lg="3">
        <div class="stat-card stat-tasks">
          <div class="stat-icon"><el-icon><List /></el-icon></div>
          <div class="stat-content">
            <div class="stat-value">{{ overview.tasks?.total || 0 }}</div>
            <div class="stat-label">任务总数</div>
            <div class="stat-extra">
              <span class="success">{{ (overview.tasks?.success_rate || 0).toFixed(1) }}% 成功</span>
            </div>
          </div>
        </div>
      </el-col>
      <el-col :xs="12" :sm="6" :lg="3">
        <div class="stat-card stat-cards">
          <div class="stat-icon"><el-icon><Ticket /></el-icon></div>
          <div class="stat-content">
            <div class="stat-value">{{ overview.cards?.total || 0 }}</div>
            <div class="stat-label">卡密总数</div>
            <div class="stat-extra">
              <span class="success">{{ overview.cards?.unused || 0 }} 未使用</span>
            </div>
          </div>
        </div>
      </el-col>
      <el-col :xs="12" :sm="6" :lg="3">
        <div class="stat-card stat-shares">
          <div class="stat-icon"><el-icon><Share /></el-icon></div>
          <div class="stat-content">
            <div class="stat-value">{{ overview.share_pages?.total || 0 }}</div>
            <div class="stat-label">分享页数</div>
            <div class="stat-extra">
              <span class="info">{{ formatNumber(overview.share_pages?.total_views) }} 访问</span>
            </div>
          </div>
        </div>
      </el-col>
      <el-col :xs="12" :sm="6" :lg="3">
        <div class="stat-card stat-nodes">
          <div class="stat-icon"><el-icon><Monitor /></el-icon></div>
          <div class="stat-content">
            <div class="stat-value">{{ overview.nodes?.total || 0 }}</div>
            <div class="stat-label">节点总数</div>
            <div class="stat-extra">
              <span :class="overview.nodes?.online ? 'success' : 'danger'">
                {{ overview.nodes?.online || 0 }} 在线
              </span>
            </div>
          </div>
        </div>
      </el-col>
      <el-col :xs="12" :sm="6" :lg="3">
        <div class="stat-card stat-proxies">
          <div class="stat-icon"><el-icon><Connection /></el-icon></div>
          <div class="stat-content">
            <div class="stat-value">{{ overview.proxies?.total || 0 }}</div>
            <div class="stat-label">代理总数</div>
            <div class="stat-extra">
              <span :class="overview.proxies?.available ? 'success' : 'danger'">
                {{ overview.proxies?.available || 0 }} 可用
              </span>
            </div>
          </div>
        </div>
      </el-col>
      <el-col :xs="12" :sm="6" :lg="3">
        <div class="stat-card stat-active">
          <div class="stat-icon"><el-icon><CircleCheck /></el-icon></div>
          <div class="stat-content">
            <div class="stat-value">{{ overview.users?.active || 0 }}</div>
            <div class="stat-label">活跃用户</div>
            <div class="stat-extra">
              <span class="danger">{{ overview.users?.inactive || 0 }} 禁用</span>
            </div>
          </div>
        </div>
      </el-col>
    </el-row>

    <!-- 图表区域 -->
    <el-row :gutter="20" class="charts-row">
      <!-- 任务趋势图 -->
      <el-col :xs="24" :lg="12">
        <el-card class="chart-card" shadow="never">
          <template #header>
            <div class="chart-header">
              <span class="title">任务趋势</span>
              <el-radio-group v-model="taskChartPeriod" size="small" @change="fetchTaskStats">
                <el-radio-button value="day">日</el-radio-button>
                <el-radio-button value="week">周</el-radio-button>
                <el-radio-button value="month">月</el-radio-button>
              </el-radio-group>
            </div>
          </template>
          <div class="chart-container" ref="taskChartRef">
            <div v-if="taskStats.length === 0" class="chart-empty">
              <el-empty description="暂无数据" />
            </div>
            <div v-else class="chart-bars">
              <div v-for="item in taskStats" :key="item.date" class="bar-item">
                <div class="bar-label">{{ formatChartDate(item.date) }}</div>
                <div class="bar-group">
                  <div class="bar success" :style="{ height: getBarHeight(item.success, maxTaskCount) }">
                    <span class="bar-value" v-if="item.success">{{ item.success }}</span>
                  </div>
                  <div class="bar danger" :style="{ height: getBarHeight(item.failed, maxTaskCount) }">
                    <span class="bar-value" v-if="item.failed">{{ item.failed }}</span>
                  </div>
                </div>
              </div>
            </div>
            <div class="chart-legend">
              <span class="legend-item"><i class="dot success"></i>成功</span>
              <span class="legend-item"><i class="dot danger"></i>失败</span>
            </div>
          </div>
        </el-card>
      </el-col>

      <!-- 账号趋势图 -->
      <el-col :xs="24" :lg="12">
        <el-card class="chart-card" shadow="never">
          <template #header>
            <div class="chart-header">
              <span class="title">账号趋势</span>
              <el-radio-group v-model="accountChartPeriod" size="small" @change="fetchAccountStats">
                <el-radio-button value="day">日</el-radio-button>
                <el-radio-button value="week">周</el-radio-button>
                <el-radio-button value="month">月</el-radio-button>
              </el-radio-group>
            </div>
          </template>
          <div class="chart-container">
            <div v-if="accountStats.length === 0" class="chart-empty">
              <el-empty description="暂无数据" />
            </div>
            <div v-else class="chart-bars">
              <div v-for="item in accountStats" :key="item.date" class="bar-item">
                <div class="bar-label">{{ formatChartDate(item.date) }}</div>
                <div class="bar-group">
                  <div class="bar primary" :style="{ height: getBarHeight(item.normal, maxAccountCount) }">
                    <span class="bar-value" v-if="item.normal">{{ item.normal }}</span>
                  </div>
                  <div class="bar warning" :style="{ height: getBarHeight(item.locked, maxAccountCount) }">
                    <span class="bar-value" v-if="item.locked">{{ item.locked }}</span>
                  </div>
                </div>
              </div>
            </div>
            <div class="chart-legend">
              <span class="legend-item"><i class="dot primary"></i>正常</span>
              <span class="legend-item"><i class="dot warning"></i>锁定</span>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 数据表格区域 -->
    <el-row :gutter="20" class="tables-row">
      <!-- 任务状态分布 -->
      <el-col :xs="24" :lg="8">
        <el-card class="data-card" shadow="never">
          <template #header>
            <span class="card-title">任务状态分布</span>
          </template>
          <div class="distribution-list">
            <div class="dist-item">
              <span class="dist-label">待处理</span>
              <el-progress
                :percentage="getPercentage(overview.tasks?.pending, overview.tasks?.total)"
                :stroke-width="10"
                status="warning"
              />
              <span class="dist-value">{{ overview.tasks?.pending || 0 }}</span>
            </div>
            <div class="dist-item">
              <span class="dist-label">进行中</span>
              <el-progress
                :percentage="getPercentage(overview.tasks?.in_progress, overview.tasks?.total)"
                :stroke-width="10"
              />
              <span class="dist-value">{{ overview.tasks?.in_progress || 0 }}</span>
            </div>
            <div class="dist-item">
              <span class="dist-label">已完成</span>
              <el-progress
                :percentage="getPercentage(overview.tasks?.completed, overview.tasks?.total)"
                :stroke-width="10"
                status="success"
              />
              <span class="dist-value">{{ overview.tasks?.completed || 0 }}</span>
            </div>
            <div class="dist-item">
              <span class="dist-label">失败</span>
              <el-progress
                :percentage="getPercentage(overview.tasks?.failed, overview.tasks?.total)"
                :stroke-width="10"
                status="exception"
              />
              <span class="dist-value">{{ overview.tasks?.failed || 0 }}</span>
            </div>
          </div>
        </el-card>
      </el-col>

      <!-- 卡密状态分布 -->
      <el-col :xs="24" :lg="8">
        <el-card class="data-card" shadow="never">
          <template #header>
            <span class="card-title">卡密状态分布</span>
          </template>
          <div class="distribution-list">
            <div class="dist-item">
              <span class="dist-label">未使用</span>
              <el-progress
                :percentage="getPercentage(overview.cards?.unused, overview.cards?.total)"
                :stroke-width="10"
                status="success"
              />
              <span class="dist-value">{{ overview.cards?.unused || 0 }}</span>
            </div>
            <div class="dist-item">
              <span class="dist-label">已激活</span>
              <el-progress
                :percentage="getPercentage(overview.cards?.activated, overview.cards?.total)"
                :stroke-width="10"
              />
              <span class="dist-value">{{ overview.cards?.activated || 0 }}</span>
            </div>
            <div class="dist-item">
              <span class="dist-label">已作废</span>
              <el-progress
                :percentage="getPercentage(overview.cards?.revoked, overview.cards?.total)"
                :stroke-width="10"
                status="exception"
              />
              <span class="dist-value">{{ overview.cards?.revoked || 0 }}</span>
            </div>
          </div>
        </el-card>
      </el-col>

      <!-- 基础设施状态 -->
      <el-col :xs="24" :lg="8">
        <el-card class="data-card" shadow="never">
          <template #header>
            <span class="card-title">基础设施状态</span>
          </template>
          <div class="infra-list">
            <div class="infra-item">
              <div class="infra-icon nodes">
                <el-icon><Monitor /></el-icon>
              </div>
              <div class="infra-info">
                <span class="infra-label">节点</span>
                <div class="infra-bar">
                  <el-progress
                    :percentage="getPercentage(overview.nodes?.online, overview.nodes?.total)"
                    :stroke-width="8"
                    :show-text="false"
                    status="success"
                  />
                </div>
                <span class="infra-value">
                  {{ overview.nodes?.online || 0 }} / {{ overview.nodes?.total || 0 }}
                </span>
              </div>
            </div>
            <div class="infra-item">
              <div class="infra-icon proxies">
                <el-icon><Connection /></el-icon>
              </div>
              <div class="infra-info">
                <span class="infra-label">代理</span>
                <div class="infra-bar">
                  <el-progress
                    :percentage="getPercentage(overview.proxies?.available, overview.proxies?.total)"
                    :stroke-width="8"
                    :show-text="false"
                    status="success"
                  />
                </div>
                <span class="infra-value">
                  {{ overview.proxies?.available || 0 }} / {{ overview.proxies?.total || 0 }}
                </span>
              </div>
            </div>
            <div class="infra-item">
              <div class="infra-icon accounts">
                <el-icon><UserFilled /></el-icon>
              </div>
              <div class="infra-info">
                <span class="infra-label">账号正常率</span>
                <div class="infra-bar">
                  <el-progress
                    :percentage="getPercentage(overview.accounts?.normal, overview.accounts?.total)"
                    :stroke-width="8"
                    :show-text="false"
                    status="success"
                  />
                </div>
                <span class="infra-value">
                  {{ overview.accounts?.normal || 0 }} / {{ overview.accounts?.total || 0 }}
                </span>
              </div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <LoadingOverlay :visible="loading" text="加载统计数据..." />
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import {
  Refresh,
  User,
  UserFilled,
  List,
  Ticket,
  Share,
  Monitor,
  Connection,
  CircleCheck
} from '@element-plus/icons-vue'
import PageHeader from '@/components/common/PageHeader.vue'
import LoadingOverlay from '@/components/common/LoadingOverlay.vue'
import {
  getAdminStatsOverviewApi,
  getAdminTaskStatsApi,
  getAdminAccountStatsApi,
  type AdminStatsOverview,
  type TaskStats,
  type AccountStats
} from '@/api/stats'
import { formatDate } from '@/utils/date'

// ==================== 响应式数据 ====================

const loading = ref(false)

// 日期范围
const dateRange = ref<[string, string] | null>(null)

// 日期快捷选项
const dateShortcuts = [
  { text: '最近7天', value: () => getDateRange(7) },
  { text: '最近30天', value: () => getDateRange(30) },
  { text: '最近90天', value: () => getDateRange(90) },
  { text: '本月', value: () => getMonthRange() }
]

// 概览数据
const overview = ref<Partial<AdminStatsOverview>>({})

// 任务统计
const taskStats = ref<TaskStats[]>([])
const taskChartPeriod = ref<'day' | 'week' | 'month'>('day')

// 账号统计
const accountStats = ref<AccountStats[]>([])
const accountChartPeriod = ref<'day' | 'week' | 'month'>('day')

// ==================== 计算属性 ====================

const maxTaskCount = computed(() => {
  if (taskStats.value.length === 0) return 100
  const max = Math.max(...taskStats.value.map(t => Math.max(t.success, t.failed)))
  return max || 100
})

const maxAccountCount = computed(() => {
  if (accountStats.value.length === 0) return 100
  const max = Math.max(...accountStats.value.map(a => Math.max(a.normal, a.locked)))
  return max || 100
})

// ==================== 方法 ====================

// 获取日期范围
function getDateRange(days: number): [Date, Date] {
  const end = new Date()
  const start = new Date()
  start.setDate(start.getDate() - days)
  return [start, end]
}

// 获取本月范围
function getMonthRange(): [Date, Date] {
  const now = new Date()
  const start = new Date(now.getFullYear(), now.getMonth(), 1)
  return [start, now]
}

// 获取概览数据
async function fetchOverview() {
  try {
    const data = await getAdminStatsOverviewApi()
    overview.value = data
  } catch (error) {
    console.error('获取概览数据失败:', error)
  }
}

// 获取任务统计
async function fetchTaskStats() {
  try {
    const params: any = { period: taskChartPeriod.value }
    if (dateRange.value) {
      params.start_date = dateRange.value[0]
      params.end_date = dateRange.value[1]
    }
    const data = await getAdminTaskStatsApi(params)
    taskStats.value = data || []
  } catch (error) {
    console.error('获取任务统计失败:', error)
    taskStats.value = []
  }
}

// 获取账号统计
async function fetchAccountStats() {
  try {
    const params: any = { period: accountChartPeriod.value }
    if (dateRange.value) {
      params.start_date = dateRange.value[0]
      params.end_date = dateRange.value[1]
    }
    const data = await getAdminAccountStatsApi(params)
    accountStats.value = data || []
  } catch (error) {
    console.error('获取账号统计失败:', error)
    accountStats.value = []
  }
}

// 加载所有数据
async function fetchAllData() {
  loading.value = true
  try {
    await Promise.all([
      fetchOverview(),
      fetchTaskStats(),
      fetchAccountStats()
    ])
  } finally {
    loading.value = false
  }
}

// 刷新
function handleRefresh() {
  fetchAllData()
}

// 日期变化
function handleDateChange() {
  fetchTaskStats()
  fetchAccountStats()
}

// 格式化数字
function formatNumber(num: number | undefined): string {
  if (!num) return '0'
  if (num >= 10000) {
    return (num / 10000).toFixed(1) + '万'
  }
  return num.toString()
}

// 格式化图表日期
function formatChartDate(date: string): string {
  return formatDate(date, 'MM-DD')
}

// 计算百分比
function getPercentage(value: number | undefined, total: number | undefined): number {
  if (!value || !total || total === 0) return 0
  return Math.round((value / total) * 100)
}

// 计算柱状图高度
function getBarHeight(value: number, max: number): string {
  if (!value || !max) return '0%'
  const percentage = Math.max((value / max) * 100, 5)
  return `${percentage}%`
}

// ==================== 生命周期 ====================

onMounted(() => {
  // 默认最近7天
  dateRange.value = [
    formatDate(getDateRange(7)[0], 'YYYY-MM-DD'),
    formatDate(getDateRange(7)[1], 'YYYY-MM-DD')
  ]
  fetchAllData()
})
</script>

<style lang="scss" scoped>
.admin-stats-view {
  padding: 0;
}

// 统计卡片
.stats-row {
  margin-bottom: 20px;
}

.stat-card {
  display: flex;
  align-items: center;
  padding: 16px;
  border-radius: 12px;
  background: white;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.05);
  margin-bottom: 16px;
  transition: all 0.3s ease;

  &:hover {
    transform: translateY(-2px);
    box-shadow: 0 6px 20px rgba(0, 0, 0, 0.1);
  }

  .stat-icon {
    width: 44px;
    height: 44px;
    border-radius: 10px;
    display: flex;
    align-items: center;
    justify-content: center;
    margin-right: 12px;
    .el-icon {
      font-size: 22px;
      color: white;
    }
  }

  .stat-content {
    flex: 1;
    min-width: 0;
    .stat-value {
      font-size: 22px;
      font-weight: 700;
      color: #303133;
      line-height: 1.2;
    }
    .stat-label {
      font-size: 12px;
      color: #909399;
      margin-top: 2px;
    }
    .stat-extra {
      font-size: 11px;
      margin-top: 4px;
      .success { color: #67c23a; }
      .warning { color: #e6a23c; }
      .danger { color: #f56c6c; }
      .info { color: #909399; }
    }
  }

  &.stat-users .stat-icon { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); }
  &.stat-accounts .stat-icon { background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); }
  &.stat-tasks .stat-icon { background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%); }
  &.stat-cards .stat-icon { background: linear-gradient(135deg, #fa709a 0%, #fee140 100%); }
  &.stat-shares .stat-icon { background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%); }
  &.stat-nodes .stat-icon { background: linear-gradient(135deg, #a18cd1 0%, #fbc2eb 100%); }
  &.stat-proxies .stat-icon { background: linear-gradient(135deg, #ff9a9e 0%, #fecfef 100%); }
  &.stat-active .stat-icon { background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%); }
}

// 图表区域
.charts-row {
  margin-bottom: 20px;
}

.chart-card {
  border-radius: 12px;
  border: none;
  margin-bottom: 20px;

  .chart-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    .title {
      font-size: 16px;
      font-weight: 600;
      color: #303133;
    }
  }
}

.chart-container {
  min-height: 250px;
  display: flex;
  flex-direction: column;
}

.chart-empty {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
}

.chart-bars {
  flex: 1;
  display: flex;
  align-items: flex-end;
  justify-content: space-around;
  padding: 20px 0;
  min-height: 200px;

  .bar-item {
    display: flex;
    flex-direction: column;
    align-items: center;
    flex: 1;
    max-width: 60px;

    .bar-label {
      font-size: 11px;
      color: #909399;
      margin-top: 8px;
    }

    .bar-group {
      display: flex;
      gap: 4px;
      height: 150px;
      align-items: flex-end;
    }

    .bar {
      width: 20px;
      min-height: 4px;
      border-radius: 4px 4px 0 0;
      position: relative;
      transition: height 0.3s ease;

      &.success { background: linear-gradient(180deg, #67c23a 0%, #95d475 100%); }
      &.danger { background: linear-gradient(180deg, #f56c6c 0%, #fab6b6 100%); }
      &.primary { background: linear-gradient(180deg, #409eff 0%, #79bbff 100%); }
      &.warning { background: linear-gradient(180deg, #e6a23c 0%, #f3d19e 100%); }

      .bar-value {
        position: absolute;
        top: -18px;
        left: 50%;
        transform: translateX(-50%);
        font-size: 10px;
        color: #606266;
        white-space: nowrap;
      }
    }
  }
}

.chart-legend {
  display: flex;
  justify-content: center;
  gap: 20px;
  padding-top: 10px;
  border-top: 1px solid #f0f0f0;

  .legend-item {
    display: flex;
    align-items: center;
    font-size: 12px;
    color: #606266;

    .dot {
      width: 10px;
      height: 10px;
      border-radius: 50%;
      margin-right: 6px;

      &.success { background: #67c23a; }
      &.danger { background: #f56c6c; }
      &.primary { background: #409eff; }
      &.warning { background: #e6a23c; }
    }
  }
}

// 数据卡片
.tables-row {
  margin-bottom: 20px;
}

.data-card {
  border-radius: 12px;
  border: none;
  margin-bottom: 20px;

  .card-title {
    font-size: 16px;
    font-weight: 600;
    color: #303133;
  }
}

.distribution-list {
  .dist-item {
    display: flex;
    align-items: center;
    margin-bottom: 16px;

    &:last-child {
      margin-bottom: 0;
    }

    .dist-label {
      width: 60px;
      font-size: 13px;
      color: #606266;
    }

    .el-progress {
      flex: 1;
      margin: 0 12px;
    }

    .dist-value {
      width: 40px;
      text-align: right;
      font-size: 13px;
      font-weight: 500;
      color: #303133;
    }
  }
}

.infra-list {
  .infra-item {
    display: flex;
    align-items: center;
    padding: 12px 0;
    border-bottom: 1px solid #f5f5f5;

    &:last-child {
      border-bottom: none;
    }

    .infra-icon {
      width: 40px;
      height: 40px;
      border-radius: 8px;
      display: flex;
      align-items: center;
      justify-content: center;
      margin-right: 12px;

      .el-icon {
        font-size: 20px;
        color: white;
      }

      &.nodes { background: linear-gradient(135deg, #a18cd1 0%, #fbc2eb 100%); }
      &.proxies { background: linear-gradient(135deg, #ff9a9e 0%, #fecfef 100%); }
      &.accounts { background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%); }
    }

    .infra-info {
      flex: 1;

      .infra-label {
        font-size: 12px;
        color: #909399;
      }

      .infra-bar {
        margin: 4px 0;
      }

      .infra-value {
        font-size: 13px;
        font-weight: 500;
        color: #303133;
      }
    }
  }
}

// 响应式
@media (max-width: 768px) {
  .stat-card {
    padding: 12px;

    .stat-icon {
      width: 36px;
      height: 36px;
      margin-right: 10px;
      .el-icon { font-size: 18px; }
    }

    .stat-content {
      .stat-value { font-size: 18px; }
      .stat-label { font-size: 11px; }
    }
  }

  .chart-bars .bar-item {
    .bar-group { height: 100px; }
    .bar { width: 14px; }
  }
}
</style>
