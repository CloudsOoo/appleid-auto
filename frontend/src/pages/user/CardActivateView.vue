<!--
  卡密激活页面

  职责：
  - 输入卡密进行激活
  - 显示卡密验证状态
  - 展示激活结果和权限信息

  上游依赖：
  - PageHeader（页面标题组件）
  - StatusTag（状态标签组件）
  - LoadingOverlay（加载遮罩组件）
  - Vue Router（页面跳转）
  - Element Plus（UI 组件）
  - card API（卡密相关接口）
  - userStore（用户状态管理）

  下游调用者：
  - 路由（/card/activate）
  - 用户设置页面（升级提示）
  - 侧边栏导航

  使用的 API：
  - POST /cards/activate - 激活卡密
  - GET /cards/status - 查询卡密状态
-->

<template>
  <div class="card-activate-view">
    <!-- 页面标题 -->
    <PageHeader
      title="卡密激活"
      description="输入卡密激活套餐，解锁更多功能和配额"
      :breadcrumbs="[
        { title: '首页', path: '/' },
        { title: '卡密激活' }
      ]"
    />

    <div class="activate-container">
      <el-row :gutter="24">
        <!-- 左侧：激活表单 -->
        <el-col :xs="24" :sm="24" :md="14" :lg="12">
          <div class="activate-card">
            <div class="card-icon">
              <el-icon><Ticket /></el-icon>
            </div>

            <h2 class="card-title">输入卡密</h2>
            <p class="card-description">
              请输入您获得的卡密代码，格式为 XXXX-XXXX-XXXX-XXXX
            </p>

            <!-- 卡密输入 -->
            <div class="card-input-container">
              <div class="card-input-group">
                <el-input
                  v-model="cardSegments[0]"
                  class="card-segment"
                  maxlength="4"
                  placeholder="XXXX"
                  @input="(val) => handleSegmentInput(0, val)"
                  @paste="handlePaste"
                  ref="segment0Ref"
                />
                <span class="separator">-</span>
                <el-input
                  v-model="cardSegments[1]"
                  class="card-segment"
                  maxlength="4"
                  placeholder="XXXX"
                  @input="(val) => handleSegmentInput(1, val)"
                  ref="segment1Ref"
                />
                <span class="separator">-</span>
                <el-input
                  v-model="cardSegments[2]"
                  class="card-segment"
                  maxlength="4"
                  placeholder="XXXX"
                  @input="(val) => handleSegmentInput(2, val)"
                  ref="segment2Ref"
                />
                <span class="separator">-</span>
                <el-input
                  v-model="cardSegments[3]"
                  class="card-segment"
                  maxlength="4"
                  placeholder="XXXX"
                  @input="(val) => handleSegmentInput(3, val)"
                  ref="segment3Ref"
                />
              </div>

              <div class="card-full-input">
                <el-input
                  v-model="fullCardCode"
                  placeholder="或直接粘贴完整卡密"
                  clearable
                  @input="handleFullInput"
                >
                  <template #prefix>
                    <el-icon><Key /></el-icon>
                  </template>
                </el-input>
              </div>
            </div>

            <!-- 操作按钮 -->
            <div class="action-buttons">
              <el-button
                type="primary"
                size="large"
                :loading="activating"
                :disabled="!isCardValid"
                @click="handleActivate"
              >
                <el-icon><CircleCheck /></el-icon>
                激活卡密
              </el-button>
              <el-button
                size="large"
                :loading="querying"
                :disabled="!isCardValid"
                @click="handleQuery"
              >
                <el-icon><Search /></el-icon>
                查询状态
              </el-button>
            </div>

            <!-- 提示信息 -->
            <div class="tips">
              <el-alert
                title="使用提示"
                type="info"
                :closable="false"
                show-icon
              >
                <template #default>
                  <ul class="tip-list">
                    <li>卡密格式为 16 位字符，用短横线分隔</li>
                    <li>每个卡密只能激活一次</li>
                    <li>激活后权限立即生效</li>
                    <li>如有问题请联系管理员</li>
                  </ul>
                </template>
              </el-alert>
            </div>
          </div>
        </el-col>

        <!-- 右侧：结果展示 -->
        <el-col :xs="24" :sm="24" :md="10" :lg="12">
          <!-- 查询结果 -->
          <div v-if="queryResult" class="result-card">
            <div class="result-header">
              <el-icon><InfoFilled /></el-icon>
              <span>卡密信息</span>
            </div>

            <el-descriptions :column="1" border>
              <el-descriptions-item label="卡密代码">
                <span class="code-text">{{ maskCardCode(queryResult.code) }}</span>
              </el-descriptions-item>
              <el-descriptions-item label="状态">
                <el-tag :type="getStatusTagType(queryResult.status)">
                  {{ getStatusText(queryResult.status) }}
                </el-tag>
              </el-descriptions-item>
              <el-descriptions-item label="有效期">
                {{ queryResult.duration_days }} 天
              </el-descriptions-item>
              <el-descriptions-item v-if="queryResult.used_at" label="激活时间">
                {{ formatTime(queryResult.used_at) }}
              </el-descriptions-item>
              <el-descriptions-item v-if="queryResult.expires_at" label="到期时间">
                {{ formatTime(queryResult.expires_at) }}
              </el-descriptions-item>
              <el-descriptions-item label="创建时间">
                {{ formatTime(queryResult.created_at) }}
              </el-descriptions-item>
            </el-descriptions>
          </div>

          <!-- 激活成功结果 -->
          <div v-if="activateResult" class="result-card success-card">
            <el-result
              icon="success"
              title="激活成功"
              sub-title="您的套餐已更新，新权限立即生效"
            >
              <template #extra>
                <div class="success-details">
                  <div class="detail-item">
                    <span class="detail-label">有效期</span>
                    <span class="detail-value">{{ activateResult.duration_days }} 天</span>
                  </div>
                  <div class="detail-item">
                    <span class="detail-label">到期时间</span>
                    <span class="detail-value">{{ formatTime(activateResult.expires_at) }}</span>
                  </div>
                </div>

                <div class="success-actions">
                  <el-button type="primary" @click="goToSettings">
                    查看权限
                  </el-button>
                  <el-button @click="resetForm">
                    继续激活
                  </el-button>
                </div>
              </template>
            </el-result>
          </div>

          <!-- 激活失败结果 -->
          <div v-if="activateError" class="result-card error-card">
            <el-result
              icon="error"
              title="激活失败"
              :sub-title="activateError"
            >
              <template #extra>
                <el-button type="primary" @click="resetForm">
                  重新输入
                </el-button>
              </template>
            </el-result>
          </div>

          <!-- 默认提示 -->
          <div v-if="!queryResult && !activateResult && !activateError" class="default-tip">
            <div class="tip-icon">
              <el-icon><Present /></el-icon>
            </div>
            <h3>升级您的套餐</h3>
            <p>激活卡密可以获得：</p>
            <ul class="benefit-list">
              <li>
                <el-icon><CircleCheck /></el-icon>
                <span>更多账号配额</span>
              </li>
              <li>
                <el-icon><CircleCheck /></el-icon>
                <span>更多分享页数量</span>
              </li>
              <li>
                <el-icon><CircleCheck /></el-icon>
                <span>更多节点和代理</span>
              </li>
              <li>
                <el-icon><CircleCheck /></el-icon>
                <span>自定义 HTML 功能</span>
              </li>
              <li>
                <el-icon><CircleCheck /></el-icon>
                <span>API 访问权限</span>
              </li>
              <li>
                <el-icon><CircleCheck /></el-icon>
                <span>批量导入导出</span>
              </li>
            </ul>
          </div>
        </el-col>
      </el-row>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import {
  Ticket,
  Key,
  CircleCheck,
  Search,
  InfoFilled,
  Present
} from '@element-plus/icons-vue'
import PageHeader from '@/components/common/PageHeader.vue'
import { useUserStore } from '@/stores/user'
import {
  activateCardApi,
  getCardStatusApi,
  type Card
} from '@/api/card'
import { formatDate } from '@/utils/date'

// ==================== 路由和状态 ====================

const router = useRouter()
const userStore = useUserStore()

// ==================== 响应式数据 ====================

// 加载状态
const activating = ref(false)
const querying = ref(false)

// 卡密输入
const cardSegments = ref(['', '', '', ''])
const fullCardCode = ref('')

// 输入框引用
const segment0Ref = ref()
const segment1Ref = ref()
const segment2Ref = ref()
const segment3Ref = ref()

// 结果状态
const queryResult = ref<Card | null>(null)
const activateResult = ref<{ duration_days: number; expires_at: string } | null>(null)
const activateError = ref('')

// ==================== 计算属性 ====================

// 组合卡密
const combinedCardCode = computed(() => {
  return cardSegments.value.join('-').toUpperCase()
})

// 卡密是否有效
const isCardValid = computed(() => {
  const code = fullCardCode.value || combinedCardCode.value
  // 移除分隔符后检查长度
  const cleanCode = code.replace(/-/g, '')
  return cleanCode.length === 16
})

// ==================== 方法 ====================

// 获取输入框引用
function getSegmentRef(index: number) {
  const refs = [segment0Ref, segment1Ref, segment2Ref, segment3Ref]
  return refs[index]
}

// 处理单个输入框输入
function handleSegmentInput(index: number, value: string) {
  // 转大写并过滤非字母数字
  const cleanValue = value.toUpperCase().replace(/[^A-Z0-9]/g, '')
  cardSegments.value[index] = cleanValue

  // 自动跳转到下一个输入框
  if (cleanValue.length === 4 && index < 3) {
    const nextRef = getSegmentRef(index + 1)
    if (nextRef.value) {
      nextRef.value.focus()
    }
  }

  // 同步到完整输入
  fullCardCode.value = combinedCardCode.value
}

// 处理粘贴
function handlePaste(event: ClipboardEvent) {
  event.preventDefault()
  const pastedText = event.clipboardData?.getData('text') || ''
  parseAndFillCard(pastedText)
}

// 处理完整输入
function handleFullInput(value: string) {
  parseAndFillCard(value)
}

// 解析并填充卡密
function parseAndFillCard(text: string) {
  // 清理输入，只保留字母数字
  const cleanText = text.toUpperCase().replace(/[^A-Z0-9]/g, '')

  if (cleanText.length >= 16) {
    // 分割成4段
    cardSegments.value = [
      cleanText.substring(0, 4),
      cleanText.substring(4, 8),
      cleanText.substring(8, 12),
      cleanText.substring(12, 16)
    ]
    fullCardCode.value = combinedCardCode.value
  } else if (cleanText.length > 0) {
    // 部分填充
    let remaining = cleanText
    for (let i = 0; i < 4; i++) {
      cardSegments.value[i] = remaining.substring(0, 4)
      remaining = remaining.substring(4)
    }
    fullCardCode.value = combinedCardCode.value
  }
}

// 格式化时间
function formatTime(time: string | null): string {
  if (!time) return '-'
  return formatDate(time, 'YYYY-MM-DD HH:mm:ss')
}

// 遮蔽卡密
function maskCardCode(code: string): string {
  if (!code) return ''
  // 只显示前4位和后4位
  const parts = code.split('-')
  if (parts.length === 4) {
    return `${parts[0]}-****-****-${parts[3]}`
  }
  return code.substring(0, 4) + '****' + code.substring(code.length - 4)
}

// 获取状态标签类型
function getStatusTagType(status: string): string {
  const map: Record<string, string> = {
    unused: 'success',
    used: 'info',
    expired: 'warning',
    revoked: 'danger'
  }
  return map[status] || 'info'
}

// 获取状态文本
function getStatusText(status: string): string {
  const map: Record<string, string> = {
    unused: '未使用',
    used: '已使用',
    expired: '已过期',
    revoked: '已作废'
  }
  return map[status] || '未知'
}

// 查询卡密状态
async function handleQuery() {
  const code = fullCardCode.value || combinedCardCode.value
  if (!code) {
    ElMessage.warning('请输入卡密')
    return
  }

  querying.value = true
  queryResult.value = null
  activateResult.value = null
  activateError.value = ''

  try {
    const result = await getCardStatusApi(code)
    queryResult.value = result
  } catch (error) {
    console.error('查询卡密失败:', error)
    ElMessage.error('卡密不存在或查询失败')
  } finally {
    querying.value = false
  }
}

// 激活卡密
async function handleActivate() {
  const code = fullCardCode.value || combinedCardCode.value
  if (!code) {
    ElMessage.warning('请输入卡密')
    return
  }

  activating.value = true
  queryResult.value = null
  activateResult.value = null
  activateError.value = ''

  try {
    const result = await activateCardApi({ code })

    // 假设返回包含 duration_days 和 expires_at
    activateResult.value = {
      duration_days: (result as any).duration_days || 30,
      expires_at: (result as any).expires_at || new Date(Date.now() + 30 * 24 * 60 * 60 * 1000).toISOString()
    }

    ElMessage.success('卡密激活成功！')

    // 刷新用户权限信息
    await userStore.fetchPermission()
  } catch (error: any) {
    console.error('激活卡密失败:', error)
    activateError.value = error?.message || '激活失败，卡密可能已被使用或已过期'
  } finally {
    activating.value = false
  }
}

// 重置表单
function resetForm() {
  cardSegments.value = ['', '', '', '']
  fullCardCode.value = ''
  queryResult.value = null
  activateResult.value = null
  activateError.value = ''

  // 聚焦第一个输入框
  if (segment0Ref.value) {
    segment0Ref.value.focus()
  }
}

// 跳转到设置页面
function goToSettings() {
  router.push('/settings')
}
</script>

<style lang="scss" scoped>
.card-activate-view {
  padding: 0;
}

.activate-container {
  margin-top: 20px;
}

// 激活卡片
.activate-card {
  background: white;
  border-radius: 16px;
  padding: 40px;
  box-shadow: 0 4px 24px rgba(0, 0, 0, 0.06);
  text-align: center;

  .card-icon {
    width: 80px;
    height: 80px;
    margin: 0 auto 24px;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;

    .el-icon {
      font-size: 40px;
      color: white;
    }
  }

  .card-title {
    font-size: 24px;
    font-weight: 600;
    color: #303133;
    margin: 0 0 12px 0;
  }

  .card-description {
    font-size: 14px;
    color: #909399;
    margin: 0 0 32px 0;
  }
}

// 卡密输入
.card-input-container {
  margin-bottom: 32px;
}

.card-input-group {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  margin-bottom: 16px;

  .card-segment {
    width: 80px;

    :deep(.el-input__wrapper) {
      text-align: center;
      font-family: 'SF Mono', Monaco, Consolas, monospace;
      font-size: 18px;
      font-weight: 600;
      letter-spacing: 2px;
    }

    :deep(.el-input__inner) {
      text-transform: uppercase;
    }
  }

  .separator {
    font-size: 24px;
    font-weight: bold;
    color: #909399;
  }
}

.card-full-input {
  max-width: 400px;
  margin: 0 auto;

  :deep(.el-input__wrapper) {
    font-family: 'SF Mono', Monaco, Consolas, monospace;
  }

  :deep(.el-input__inner) {
    text-transform: uppercase;
  }
}

// 操作按钮
.action-buttons {
  display: flex;
  justify-content: center;
  gap: 16px;
  margin-bottom: 32px;

  .el-button {
    min-width: 140px;
  }
}

// 提示信息
.tips {
  text-align: left;

  .tip-list {
    margin: 8px 0 0 0;
    padding-left: 20px;
    color: #606266;
    font-size: 13px;

    li {
      margin-bottom: 4px;
    }
  }
}

// 结果卡片
.result-card {
  background: white;
  border-radius: 16px;
  padding: 24px;
  box-shadow: 0 4px 24px rgba(0, 0, 0, 0.06);
  margin-bottom: 20px;

  .result-header {
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 16px;
    font-weight: 500;
    color: #303133;
    margin-bottom: 16px;

    .el-icon {
      color: #409eff;
    }
  }

  .code-text {
    font-family: 'SF Mono', Monaco, Consolas, monospace;
    font-weight: 500;
  }
}

.success-card {
  .success-details {
    display: flex;
    justify-content: center;
    gap: 40px;
    margin-bottom: 24px;

    .detail-item {
      text-align: center;

      .detail-label {
        display: block;
        font-size: 12px;
        color: #909399;
        margin-bottom: 4px;
      }

      .detail-value {
        font-size: 16px;
        font-weight: 600;
        color: #303133;
      }
    }
  }

  .success-actions {
    display: flex;
    justify-content: center;
    gap: 12px;
  }
}

// 默认提示
.default-tip {
  background: white;
  border-radius: 16px;
  padding: 40px;
  box-shadow: 0 4px 24px rgba(0, 0, 0, 0.06);
  text-align: center;

  .tip-icon {
    width: 64px;
    height: 64px;
    margin: 0 auto 20px;
    background: linear-gradient(135deg, #ff9a9e 0%, #fecfef 100%);
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;

    .el-icon {
      font-size: 32px;
      color: white;
    }
  }

  h3 {
    font-size: 20px;
    font-weight: 600;
    color: #303133;
    margin: 0 0 12px 0;
  }

  p {
    font-size: 14px;
    color: #909399;
    margin: 0 0 20px 0;
  }

  .benefit-list {
    list-style: none;
    padding: 0;
    margin: 0;
    text-align: left;
    max-width: 250px;
    margin: 0 auto;

    li {
      display: flex;
      align-items: center;
      gap: 8px;
      padding: 10px 0;
      border-bottom: 1px solid #f0f0f0;

      &:last-child {
        border-bottom: none;
      }

      .el-icon {
        color: #67c23a;
        font-size: 16px;
      }

      span {
        font-size: 14px;
        color: #606266;
      }
    }
  }
}

// 响应式设计
@media (max-width: 768px) {
  .activate-card {
    padding: 24px;
  }

  .card-input-group {
    flex-wrap: wrap;

    .card-segment {
      width: 60px;

      :deep(.el-input__wrapper) {
        font-size: 14px;
      }
    }

    .separator {
      font-size: 18px;
    }
  }

  .action-buttons {
    flex-direction: column;

    .el-button {
      width: 100%;
    }
  }

  .default-tip {
    padding: 24px;
  }

  .success-card {
    .success-details {
      flex-direction: column;
      gap: 16px;
    }
  }
}
</style>
