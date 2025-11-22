<!--
  管理员仪表盘页面

  职责：
  - 显示系统全局统计数据
  - 显示用户、账号、任务、卡密等各模块统计
  - 显示最近用户注册列表
  - 显示最近卡密激活记录
  - 系统状态监控概览

  上游依赖：
  - PageHeader（页面标题组件）
  - StatusTag（状态标签组件）
  - DataTable（表格组件）
  - LoadingOverlay（加载遮罩组件）
  - Vue Router（页面跳转）
  - Element Plus（UI 组件）
  - stats API（统计相关接口）
  - user API（用户相关接口）

  下游调用者：
  - 路由（/admin/dashboard）
  - AdminLayout 侧边栏导航

  使用的 API：
  - GET /stats/admin/overview - 获取管理员统计概览
  - GET /admin/users - 获取最近注册用户
-->

<template>
  <div class="admin-dashboard-view">
    <!-- 页面标题 -->
    <PageHeader
      title="管理控制台"
      description="系统运营数据概览和监控"
      :breadcrumbs="[
        { title: '管理后台', path: '/admin' },
        { title: '仪表盘' }
      ]"
    >
      <template #actions>
        <el-button :icon="Refresh" @click="handleRefresh" :loading="loading">
          刷新数据
        </el-button>
      </template>
    </PageHeader>

    <LoadingOverlay :visible="loading" text="加载统计数据..." />

    <!-- 统计卡片区域 -->
    <el-row :gutter="20" class="stats-row">
      <!-- 用户统计 -->
      <el-col :xs="12" :sm="8" :md="6" :lg="4" :xl="3">
        <div class="stat-card stat-card-users" @click="goToPage('/admin/users')">
          <div class="stat-icon">
            <el-icon><User /></el-icon>
          </div>
          <div class="stat-content">
            <div class="stat-value">{{ stats.users?.total || 0 }}</div>
            <div class="stat-label">总用户数</div>
            <div class="stat-extra">
              <span class="success">+{{ stats.users?.today_new || 0 }} 今日</span>
            </div>
          </div>
        </div>
      </el-col>

      <!-- 账号统计 -->
      <el-col :xs="12" :sm="8" :md="6" :lg="4" :xl="3">
        <div class="stat-card stat-card-accounts" @click="goToPage('/admin/accounts')">
          <div class="stat-icon">
            <el-icon><UserFilled /></el-icon>
          </div>
          <div class="stat-content">
            <div class="stat-value">{{ stats.accounts?.total || 0 }}</div>
            <div class="stat-label">总账号数</div>
            <div class="stat-extra">
              <span class="warning">{{ stats.accounts?.locked || 0 }} 已锁定</span>
            </div>
          </div>
        </div>
      </el-col>

      <!-- 任务统计 -->
      <el-col :xs="12" :sm="8" :md="6" :lg="4" :xl="3">
        <div class="stat-card stat-card-tasks" @click="goToPage('/admin/tasks')">
          <div class="stat-icon">
            <el-icon><List /></el-icon>
          </div>
          <div class="stat-content">
            <div class="stat-value">{{ stats.tasks?.total || 0 }}</div>
            <div class="stat-label">总任务数</div>
            <div class="stat-extra">
              <span class="success">{{ stats.tasks?.success_rate?.toFixed(1) || 0 }}% 成功率</span>
            </div>
          </div>
        </div>
      </el-col>

      <!-- 分享页统计 -->
      <el-col :xs="12" :sm="8" :md="6" :lg="4" :xl="3">
        <div class="stat-card stat-card-shares" @click="goToPage('/admin/share-pages')">
          <div class="stat-icon">
            <el-icon><Share /></el-icon>
          </div>
          <div class="stat-content">
            <div class="stat-value">{{ stats.share_pages?.total || 0 }}</div>
            <div class="stat-label">分享页数</div>
            <div class="stat-extra">
              <span class="info">{{ formatNumber(stats.share_pages?.total_views) }} 访问</span>
            </div>
          </div>
        </div>
      </el-col>

      <!-- 卡密统计 -->
      <el-col :xs="12" :sm="8" :md="6" :lg="4" :xl="3">
        <div class="stat-card stat-card-cards" @click="goToPage('/admin/cards')">
          <div class="stat-icon">
            <el-icon><Ticket /></el-icon>
          </div>
          <div class="stat-content">
            <div class="stat-value">{{ stats.cards?.total || 0 }}</div>
            <div class="stat-label">卡密总数</div>
            <div class="stat-extra">
              <span class="success">{{ stats.cards?.unused || 0 }} 未使用</span>
            </div>
          </div>
        </div>
      </el-col>

      <!-- 节点统计 -->
      <el-col :xs="12" :sm="8" :md="6" :lg="4" :xl="3">
        <div class="stat-card stat-card-nodes" @click="goToPage('/admin/nodes')">
          <div class="stat-icon">
            <el-icon><Monitor /></el-icon>
          </div>
          <div class="stat-content">
            <div class="stat-value">{{ stats.nodes?.total || 0 }}</div>
            <div class="stat-label">节点总数</div>
            <div class="stat-extra">
              <span :class="stats.nodes?.online > 0 ? 'success' : 'danger'">
                {{ stats.nodes?.online || 0 }} 在线
              </span>
            </div>
          </div>
        </div>
      </el-col>

      <!-- 代理统计 -->
      <el-col :xs="12" :sm="8" :md="6" :lg="4" :xl="3">
        <div class="stat-card stat-card-proxies" @click="goToPage('/admin/proxies')">
          <div class="stat-icon">
            <el-icon><Connection /></el-icon>
          </div>
          <div class="stat-content">
            <div class="stat-value">{{ stats.proxies?.total || 0 }}</div>
            <div class="stat-label">代理总数</div>
            <div class="stat-extra">
              <span :class="stats.proxies?.available > 0 ? 'success' : 'danger'">
                {{ stats.proxies?.available || 0 }} 可用
              </span>
            </div>
          </div>
        </div>
      </el-col>

      <!-- 活跃用户 -->
      <el-col :xs="12" :sm="8" :md="6" :lg="4" :xl="3">
        <div class="stat-card stat-card-active">
          <div class="stat-icon">
            <el-icon><CircleCheck /></el-icon>
          </div>
          <div class="stat-content">
            <div class="stat-value">{{ stats.users?.active || 0 }}</div>
            <div class="stat-label">活跃用户</div>
            <div class="stat-extra">
              <span class="danger">{{ stats.users?.inactive || 0 }} 已禁用</span>
            </div>
          </div>
        </div>
      </el-col>
    </el-row>

    <!-- 数据展示区域 -->
    <el-row :gutter="20" class="data-row">
      <!-- 最近注册用户 -->
      <el-col :xs="24" :lg="12">
        <div class="data-card">
          <div class="card-header">
            <h3>最近注册用户</h3>
            <el-button text type="primary" @click="goToPage('/admin/users')">
              查看全部
            </el-button>
          </div>
          <div class="card-content">
            <el-table
              :data="recentUsers"
              :loading="usersLoading"
              size="small"
              max-height="320"
            >
              <el-table-column prop="id" label="ID" width="60" />
              <el-table-column prop="username" label="用户名" min-width="100">
                <template #default="{ row }">
                  <div class="user-cell">
                    <el-avatar :size="28" :style="{ background: getAvatarColor(row.role) }">
                      {{ row.username.charAt(0).toUpperCase() }}
                    </el-avatar>
                    <span>{{ row.username }}</span>
                  </div>
                </template>
              </el-table-column>
              <el-table-column prop="email" label="邮箱" min-width="150" show-overflow-tooltip />
              <el-table-column prop="role" label="角色" width="80">
                <template #default="{ row }">
                  <el-tag :type="row.role === 'admin' ? 'danger' : 'primary'" size="small">
                    {{ row.role === 'admin' ? '管理员' : '用户' }}
                  </el-tag>
                </template>
              </el-table-column>
              <el-table-column prop="is_active" label="状态" width="80">
                <template #default="{ row }">
                  <StatusTag
                    :status="row.is_active ? 'success' : 'danger'"
                    :text="row.is_active ? '正常' : '禁用'"
                  />
                </template>
              </el-table-column>
              <el-table-column prop="created_at" label="注册时间" width="140">
                <template #default="{ row }">
                  {{ formatTime(row.created_at) }}
                </template>
              </el-table-column>
            </el-table>
          </div>
        </div>
      </el-col>

      <!-- 系统状态概览 -->
      <el-col :xs="24" :lg="12">
        <div class="data-card">
          <div class="card-header">
            <h3>系统状态概览</h3>
            <el-tag type="success" effect="dark" size="small">
              <span class="status-dot"></span>
              运行正常
            </el-tag>
          </div>
          <div class="card-content">
            <!-- 任务状态分布 -->
            <div class="status-section">
              <h4>任务状态分布</h4>
              <div class="status-bars">
                <div class="status-bar-item">
                  <div class="bar-label">
                    <span>待处理</span>
                    <span>{{ stats.tasks?.pending || 0 }}</span>
                  </div>
                  <el-progress
                    :percentage="getPercentage(stats.tasks?.pending, stats.tasks?.total)"
                    :stroke-width="8"
                    :show-text="false"
                    status="warning"
                  />
                </div>
                <div class="status-bar-item">
                  <div class="bar-label">
                    <span>进行中</span>
                    <span>{{ stats.tasks?.in_progress || 0 }}</span>
                  </div>
                  <el-progress
                    :percentage="getPercentage(stats.tasks?.in_progress, stats.tasks?.total)"
                    :stroke-width="8"
                    :show-text="false"
                  />
                </div>
                <div class="status-bar-item">
                  <div class="bar-label">
                    <span>已完成</span>
                    <span>{{ stats.tasks?.completed || 0 }}</span>
                  </div>
                  <el-progress
                    :percentage="getPercentage(stats.tasks?.completed, stats.tasks?.total)"
                    :stroke-width="8"
                    :show-text="false"
                    status="success"
                  />
                </div>
                <div class="status-bar-item">
                  <div class="bar-label">
                    <span>失败</span>
                    <span>{{ stats.tasks?.failed || 0 }}</span>
                  </div>
                  <el-progress
                    :percentage="getPercentage(stats.tasks?.failed, stats.tasks?.total)"
                    :stroke-width="8"
                    :show-text="false"
                    status="exception"
                  />
                </div>
              </div>
            </div>

            <!-- 卡密状态分布 -->
            <div class="status-section">
              <h4>卡密状态分布</h4>
              <div class="status-bars">
                <div class="status-bar-item">
                  <div class="bar-label">
                    <span>未使用</span>
                    <span>{{ stats.cards?.unused || 0 }}</span>
                  </div>
                  <el-progress
                    :percentage="getPercentage(stats.cards?.unused, stats.cards?.total)"
                    :stroke-width="8"
                    :show-text="false"
                    status="success"
                  />
                </div>
                <div class="status-bar-item">
                  <div class="bar-label">
                    <span>已激活</span>
                    <span>{{ stats.cards?.activated || 0 }}</span>
                  </div>
                  <el-progress
                    :percentage="getPercentage(stats.cards?.activated, stats.cards?.total)"
                    :stroke-width="8"
                    :show-text="false"
                  />
                </div>
                <div class="status-bar-item">
                  <div class="bar-label">
                    <span>已作废</span>
                    <span>{{ stats.cards?.revoked || 0 }}</span>
                  </div>
                  <el-progress
                    :percentage="getPercentage(stats.cards?.revoked, stats.cards?.total)"
                    :stroke-width="8"
                    :show-text="false"
                    status="exception"
                  />
                </div>
              </div>
            </div>

            <!-- 节点/代理状态 -->
            <div class="status-section">
              <h4>基础设施状态</h4>
              <div class="infra-status">
                <div class="infra-item">
                  <div class="infra-icon nodes">
                    <el-icon><Monitor /></el-icon>
                  </div>
                  <div class="infra-info">
                    <span class="infra-label">节点</span>
                    <span class="infra-value">
                      <span class="online">{{ stats.nodes?.online || 0 }}</span>
                      /
                      <span class="total">{{ stats.nodes?.total || 0 }}</span>
                    </span>
                  </div>
                </div>
                <div class="infra-item">
                  <div class="infra-icon proxies">
                    <el-icon><Connection /></el-icon>
                  </div>
                  <div class="infra-info">
                    <span class="infra-label">代理</span>
                    <span class="infra-value">
                      <span class="online">{{ stats.proxies?.available || 0 }}</span>
                      /
                      <span class="total">{{ stats.proxies?.total || 0 }}</span>
                    </span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </el-col>
    </el-row>

    <!-- 快捷操作区域 -->
    <div class="quick-actions">
      <h3>快捷操作</h3>
      <el-row :gutter="16">
        <el-col :xs="12" :sm="8" :md="6" :lg="4">
          <div class="action-card" @click="goToPage('/admin/users')">
            <el-icon><User /></el-icon>
            <span>用户管理</span>
          </div>
        </el-col>
        <el-col :xs="12" :sm="8" :md="6" :lg="4">
          <div class="action-card" @click="goToPage('/admin/cards/generate')">
            <el-icon><Ticket /></el-icon>
            <span>生成卡密</span>
          </div>
        </el-col>
        <el-col :xs="12" :sm="8" :md="6" :lg="4">
          <div class="action-card" @click="goToPage('/admin/packages')">
            <el-icon><GoodsFilled /></el-icon>
            <span>套餐管理</span>
          </div>
        </el-col>
        <el-col :xs="12" :sm="8" :md="6" :lg="4">
          <div class="action-card" @click="goToPage('/admin/stats')">
            <el-icon><DataAnalysis /></el-icon>
            <span>数据统计</span>
          </div>
        </el-col>
      </el-row>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import {
  Refresh,
  User,
  UserFilled,
  List,
  Share,
  Ticket,
  Monitor,
  Connection,
  CircleCheck,
  GoodsFilled,
  DataAnalysis
} from '@element-plus/icons-vue'
import PageHeader from '@/components/common/PageHeader.vue'
import StatusTag from '@/components/common/StatusTag.vue'
import LoadingOverlay from '@/components/common/LoadingOverlay.vue'
import {
  getAdminStatsOverviewApi,
  type AdminStatsOverview
} from '@/api/stats'
import {
  getUserListApi,
  type User as UserType
} from '@/api/user'
import { formatDate } from '@/utils/date'

// ==================== 路由 ====================

const router = useRouter()

// ==================== 响应式数据 ====================

const loading = ref(false)
const usersLoading = ref(false)

// 统计数据
const stats = ref<Partial<AdminStatsOverview>>({})

// 最近用户
const recentUsers = ref<UserType[]>([])

// ==================== 方法 ====================

// 获取统计数据
async function fetchStats() {
  loading.value = true
  try {
    const data = await getAdminStatsOverviewApi()
    stats.value = data
  } catch (error) {
    console.error('获取统计数据失败:', error)
    ElMessage.error('获取统计数据失败')
  } finally {
    loading.value = false
  }
}

// 获取最近用户
async function fetchRecentUsers() {
  usersLoading.value = true
  try {
    const data = await getUserListApi({ page: 1, per_page: 10 })
    recentUsers.value = data.items || []
  } catch (error) {
    console.error('获取用户列表失败:', error)
  } finally {
    usersLoading.value = false
  }
}

// 刷新数据
function handleRefresh() {
  fetchStats()
  fetchRecentUsers()
}

// 跳转页面
function goToPage(path: string) {
  router.push(path)
}

// 格式化时间
function formatTime(time: string): string {
  return formatDate(time, 'MM-DD HH:mm')
}

// 格式化数字
function formatNumber(num: number | undefined): string {
  if (!num) return '0'
  if (num >= 10000) {
    return (num / 10000).toFixed(1) + '万'
  }
  return num.toString()
}

// 计算百分比
function getPercentage(value: number | undefined, total: number | undefined): number {
  if (!value || !total || total === 0) return 0
  return Math.round((value / total) * 100)
}

// 获取头像颜色
function getAvatarColor(role: string): string {
  return role === 'admin' ? '#f56c6c' : '#409eff'
}

// ==================== 生命周期 ====================

onMounted(() => {
  fetchStats()
  fetchRecentUsers()
})
</script>

<style lang="scss" scoped>
.admin-dashboard-view {
  padding: 0;
}

// 统计卡片
.stats-row {
  margin-bottom: 20px;
}

.stat-card {
  display: flex;
  align-items: center;
  padding: 20px;
  border-radius: 12px;
  background: white;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.05);
  cursor: pointer;
  transition: all 0.3s ease;
  margin-bottom: 16px;

  &:hover {
    transform: translateY(-4px);
    box-shadow: 0 8px 24px rgba(0, 0, 0, 0.12);
  }

  .stat-icon {
    width: 50px;
    height: 50px;
    border-radius: 12px;
    display: flex;
    align-items: center;
    justify-content: center;
    margin-right: 16px;

    .el-icon {
      font-size: 24px;
      color: white;
    }
  }

  .stat-content {
    flex: 1;

    .stat-value {
      font-size: 24px;
      font-weight: 700;
      color: #303133;
      line-height: 1.2;
    }

    .stat-label {
      font-size: 13px;
      color: #909399;
      margin-top: 4px;
    }

    .stat-extra {
      font-size: 12px;
      margin-top: 6px;

      .success { color: #67c23a; }
      .warning { color: #e6a23c; }
      .danger { color: #f56c6c; }
      .info { color: #909399; }
    }
  }

  &.stat-card-users .stat-icon { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); }
  &.stat-card-accounts .stat-icon { background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); }
  &.stat-card-tasks .stat-icon { background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%); }
  &.stat-card-shares .stat-icon { background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%); }
  &.stat-card-cards .stat-icon { background: linear-gradient(135deg, #fa709a 0%, #fee140 100%); }
  &.stat-card-nodes .stat-icon { background: linear-gradient(135deg, #a18cd1 0%, #fbc2eb 100%); }
  &.stat-card-proxies .stat-icon { background: linear-gradient(135deg, #ff9a9e 0%, #fecfef 100%); }
  &.stat-card-active .stat-icon { background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%); }
}

// 数据卡片
.data-row {
  margin-bottom: 20px;
}

.data-card {
  background: white;
  border-radius: 12px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.05);
  margin-bottom: 20px;

  .card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 16px 20px;
    border-bottom: 1px solid #f0f0f0;

    h3 {
      font-size: 16px;
      font-weight: 600;
      color: #303133;
      margin: 0;
    }

    .status-dot {
      display: inline-block;
      width: 6px;
      height: 6px;
      border-radius: 50%;
      background: #fff;
      margin-right: 6px;
      animation: pulse 2s infinite;
    }
  }

  .card-content {
    padding: 16px 20px;
  }
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

// 用户单元格
.user-cell {
  display: flex;
  align-items: center;
  gap: 8px;
}

// 状态分布
.status-section {
  margin-bottom: 20px;

  &:last-child {
    margin-bottom: 0;
  }

  h4 {
    font-size: 14px;
    font-weight: 500;
    color: #606266;
    margin: 0 0 12px 0;
  }
}

.status-bars {
  .status-bar-item {
    margin-bottom: 12px;

    &:last-child {
      margin-bottom: 0;
    }

    .bar-label {
      display: flex;
      justify-content: space-between;
      font-size: 12px;
      color: #909399;
      margin-bottom: 6px;
    }
  }
}

// 基础设施状态
.infra-status {
  display: flex;
  gap: 24px;

  .infra-item {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 12px 16px;
    background: #f8f9fa;
    border-radius: 8px;
    flex: 1;

    .infra-icon {
      width: 40px;
      height: 40px;
      border-radius: 8px;
      display: flex;
      align-items: center;
      justify-content: center;

      .el-icon {
        font-size: 20px;
        color: white;
      }

      &.nodes {
        background: linear-gradient(135deg, #a18cd1 0%, #fbc2eb 100%);
      }

      &.proxies {
        background: linear-gradient(135deg, #ff9a9e 0%, #fecfef 100%);
      }
    }

    .infra-info {
      .infra-label {
        display: block;
        font-size: 12px;
        color: #909399;
      }

      .infra-value {
        font-size: 16px;
        font-weight: 600;

        .online { color: #67c23a; }
        .total { color: #606266; }
      }
    }
  }
}

// 快捷操作
.quick-actions {
  background: white;
  border-radius: 12px;
  padding: 20px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.05);

  h3 {
    font-size: 16px;
    font-weight: 600;
    color: #303133;
    margin: 0 0 16px 0;
  }

  .action-card {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: 20px;
    background: #f8f9fa;
    border-radius: 12px;
    cursor: pointer;
    transition: all 0.3s ease;

    &:hover {
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
      color: white;

      .el-icon {
        color: white;
      }
    }

    .el-icon {
      font-size: 28px;
      color: #667eea;
      margin-bottom: 8px;
    }

    span {
      font-size: 14px;
      font-weight: 500;
    }
  }
}

// 响应式设计
@media (max-width: 768px) {
  .stat-card {
    padding: 16px;

    .stat-icon {
      width: 40px;
      height: 40px;
      margin-right: 12px;

      .el-icon {
        font-size: 20px;
      }
    }

    .stat-content {
      .stat-value {
        font-size: 20px;
      }

      .stat-label {
        font-size: 12px;
      }
    }
  }

  .infra-status {
    flex-direction: column;
    gap: 12px;
  }
}
</style>
