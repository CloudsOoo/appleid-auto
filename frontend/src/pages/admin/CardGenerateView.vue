<!--
  管理员卡密生成页面

  职责：
  - 批量生成卡密
  - 配置卡密参数（数量、有效期、关联套餐）
  - 显示生成结果
  - 提供卡密导出功能

  上游依赖：
  - PageHeader（页面标题组件）
  - LoadingOverlay（加载遮罩组件）
  - Vue Router（页面跳转）
  - Element Plus（UI 组件）
  - card API（卡密相关接口）
  - package API（套餐相关接口）

  下游调用者：
  - 路由（/admin/cards/generate）
  - CardListView（生成卡密按钮）
  - Admin Dashboard 快捷操作

  使用的 API：
  - POST /cards/admin/generate - 生成卡密
  - GET /packages - 获取套餐列表
-->

<template>
  <div class="admin-card-generate-view">
    <!-- 页面标题 -->
    <PageHeader
      title="生成卡密"
      description="批量生成系统卡密"
      :breadcrumbs="[
        { title: '管理后台', path: '/admin' },
        { title: '卡密管理', path: '/admin/cards' },
        { title: '生成卡密' }
      ]"
    >
      <template #actions>
        <el-button @click="goBack">返回列表</el-button>
      </template>
    </PageHeader>

    <div class="generate-content">
      <el-row :gutter="24">
        <!-- 左侧：生成表单 -->
        <el-col :xs="24" :lg="12">
          <el-card class="form-card" shadow="never">
            <template #header>
              <div class="card-header">
                <el-icon><Setting /></el-icon>
                <span>生成配置</span>
              </div>
            </template>

            <el-form
              ref="formRef"
              :model="form"
              :rules="formRules"
              label-width="120px"
              size="large"
            >
              <el-form-item label="生成数量" prop="count">
                <el-input-number
                  v-model="form.count"
                  :min="1"
                  :max="1000"
                  :step="10"
                  controls-position="right"
                  style="width: 100%"
                />
                <div class="form-tip">单次最多生成 1000 个卡密</div>
              </el-form-item>

              <el-form-item label="有效期" prop="duration_days">
                <el-select v-model="form.duration_days" style="width: 100%">
                  <el-option label="7 天" :value="7" />
                  <el-option label="15 天" :value="15" />
                  <el-option label="30 天" :value="30" />
                  <el-option label="90 天" :value="90" />
                  <el-option label="180 天" :value="180" />
                  <el-option label="365 天" :value="365" />
                  <el-option label="自定义" :value="-1" />
                </el-select>
              </el-form-item>

              <el-form-item
                v-if="form.duration_days === -1"
                label="自定义天数"
                prop="custom_days"
              >
                <el-input-number
                  v-model="form.custom_days"
                  :min="1"
                  :max="3650"
                  controls-position="right"
                  style="width: 100%"
                />
                <div class="form-tip">最多 3650 天（约 10 年）</div>
              </el-form-item>

              <el-form-item label="关联套餐" prop="package_id">
                <el-select
                  v-model="form.package_id"
                  placeholder="选择套餐（可选）"
                  clearable
                  style="width: 100%"
                >
                  <el-option
                    v-for="pkg in packageList"
                    :key="pkg.id"
                    :label="pkg.name"
                    :value="pkg.id"
                  >
                    <div class="package-option">
                      <span>{{ pkg.name }}</span>
                      <span class="price">¥{{ pkg.price }}</span>
                    </div>
                  </el-option>
                </el-select>
                <div class="form-tip">不选择则生成通用卡密</div>
              </el-form-item>

              <!-- 套餐信息预览 -->
              <el-form-item v-if="selectedPackage" label="套餐详情">
                <div class="package-preview">
                  <el-descriptions :column="2" size="small" border>
                    <el-descriptions-item label="账号配额">
                      {{ selectedPackage.max_accounts }}
                    </el-descriptions-item>
                    <el-descriptions-item label="分享页配额">
                      {{ selectedPackage.max_share_pages }}
                    </el-descriptions-item>
                    <el-descriptions-item label="节点配额">
                      {{ selectedPackage.max_nodes }}
                    </el-descriptions-item>
                    <el-descriptions-item label="代理配额">
                      {{ selectedPackage.max_proxies }}
                    </el-descriptions-item>
                  </el-descriptions>
                </div>
              </el-form-item>

              <el-form-item>
                <el-button
                  type="primary"
                  size="large"
                  :icon="MagicStick"
                  :loading="generating"
                  @click="handleGenerate"
                  style="width: 100%"
                >
                  {{ generating ? '生成中...' : '开始生成' }}
                </el-button>
              </el-form-item>
            </el-form>
          </el-card>

          <!-- 生成说明 -->
          <el-card class="tips-card" shadow="never">
            <template #header>
              <div class="card-header">
                <el-icon><InfoFilled /></el-icon>
                <span>使用说明</span>
              </div>
            </template>
            <ul class="tips-list">
              <li>卡密格式为 16 位大写字母和数字组合，如：XXXX-XXXX-XXXX-XXXX</li>
              <li>生成后的卡密可以在列表页面查看、导出或作废</li>
              <li>用户激活卡密后，有效期从激活时间开始计算</li>
              <li>关联套餐后，用户激活时将自动获得对应套餐权限</li>
              <li>建议单次生成数量不超过 100 个，以避免超时</li>
            </ul>
          </el-card>
        </el-col>

        <!-- 右侧：生成结果 -->
        <el-col :xs="24" :lg="12">
          <el-card class="result-card" shadow="never">
            <template #header>
              <div class="card-header">
                <el-icon><Ticket /></el-icon>
                <span>生成结果</span>
                <div class="header-actions" v-if="generatedCards.length > 0">
                  <el-button size="small" :icon="CopyDocument" @click="copyAllCodes">
                    复制全部
                  </el-button>
                  <el-button size="small" :icon="Download" @click="exportCodes">
                    导出
                  </el-button>
                </div>
              </div>
            </template>

            <!-- 无结果状态 -->
            <div v-if="generatedCards.length === 0" class="empty-result">
              <el-empty description="暂无生成结果">
                <template #image>
                  <el-icon :size="64" color="#dcdfe6"><Ticket /></el-icon>
                </template>
              </el-empty>
            </div>

            <!-- 生成结果列表 -->
            <div v-else class="result-content">
              <div class="result-stats">
                <el-tag type="success" size="large">
                  成功生成 {{ generatedCards.length }} 个卡密
                </el-tag>
                <span class="stats-info">
                  有效期：{{ getActualDays() }} 天
                  <template v-if="selectedPackage">
                    | 套餐：{{ selectedPackage.name }}
                  </template>
                </span>
              </div>

              <el-scrollbar max-height="400px" class="code-list-scroll">
                <div class="code-list">
                  <div
                    v-for="(card, index) in generatedCards"
                    :key="card.id"
                    class="code-item"
                  >
                    <span class="code-index">{{ index + 1 }}.</span>
                    <code class="code-text">{{ card.code }}</code>
                    <el-button
                      link
                      type="primary"
                      :icon="CopyDocument"
                      @click="copyCode(card.code)"
                    />
                  </div>
                </div>
              </el-scrollbar>

              <div class="result-actions">
                <el-button type="primary" @click="goToList">
                  查看列表
                </el-button>
                <el-button @click="resetAndGenerate">
                  继续生成
                </el-button>
              </div>
            </div>
          </el-card>

          <!-- 历史生成记录（简要） -->
          <el-card class="history-card" shadow="never" v-if="generateHistory.length > 0">
            <template #header>
              <div class="card-header">
                <el-icon><Clock /></el-icon>
                <span>本次会话生成记录</span>
              </div>
            </template>
            <el-timeline>
              <el-timeline-item
                v-for="(record, index) in generateHistory"
                :key="index"
                :timestamp="record.time"
                placement="top"
              >
                <div class="history-item">
                  生成 {{ record.count }} 个卡密
                  <el-tag size="small" v-if="record.packageName">
                    {{ record.packageName }}
                  </el-tag>
                  <span class="days">{{ record.days }} 天</span>
                </div>
              </el-timeline-item>
            </el-timeline>
          </el-card>
        </el-col>
      </el-row>
    </div>

    <LoadingOverlay :visible="generating" text="正在生成卡密..." />
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, type FormInstance, type FormRules } from 'element-plus'
import {
  Setting,
  MagicStick,
  Ticket,
  CopyDocument,
  Download,
  InfoFilled,
  Clock
} from '@element-plus/icons-vue'
import PageHeader from '@/components/common/PageHeader.vue'
import LoadingOverlay from '@/components/common/LoadingOverlay.vue'
import {
  generateCardsApi,
  type Card,
  type GenerateCardsRequest
} from '@/api/card'
import { getPackageListApi, type Package } from '@/api/package'
import { formatDate } from '@/utils/date'

// ==================== 路由 ====================

const router = useRouter()

// ==================== 响应式数据 ====================

const generating = ref(false)

// 表单
const formRef = ref<FormInstance>()
const form = reactive({
  count: 10,
  duration_days: 30,
  custom_days: 30,
  package_id: null as number | null
})

// 套餐列表
const packageList = ref<Package[]>([])

// 生成结果
const generatedCards = ref<Card[]>([])

// 生成历史（本次会话）
const generateHistory = ref<{
  count: number
  days: number
  packageName: string | null
  time: string
}[]>([])

// ==================== 计算属性 ====================

const selectedPackage = computed(() => {
  if (!form.package_id) return null
  return packageList.value.find(p => p.id === form.package_id) || null
})

// ==================== 表单验证 ====================

const formRules: FormRules = {
  count: [
    { required: true, message: '请输入生成数量', trigger: 'blur' },
    { type: 'number', min: 1, max: 1000, message: '数量范围 1-1000', trigger: 'blur' }
  ],
  duration_days: [
    { required: true, message: '请选择有效期', trigger: 'change' }
  ],
  custom_days: [
    { type: 'number', min: 1, max: 3650, message: '天数范围 1-3650', trigger: 'blur' }
  ]
}

// ==================== 方法 ====================

// 获取套餐列表
async function fetchPackageList() {
  try {
    const data = await getPackageListApi()
    packageList.value = data || []
  } catch (error) {
    console.error('获取套餐列表失败:', error)
  }
}

// 获取实际天数
function getActualDays(): number {
  return form.duration_days === -1 ? form.custom_days : form.duration_days
}

// 生成卡密
async function handleGenerate() {
  if (!formRef.value) return

  try {
    await formRef.value.validate()

    generating.value = true

    const request: GenerateCardsRequest = {
      count: form.count,
      duration_days: getActualDays()
    }

    if (form.package_id) {
      request.package_id = form.package_id
    }

    const data = await generateCardsApi(request)
    generatedCards.value = data || []

    // 记录历史
    generateHistory.value.unshift({
      count: generatedCards.value.length,
      days: getActualDays(),
      packageName: selectedPackage.value?.name || null,
      time: formatDate(new Date(), 'HH:mm:ss')
    })

    // 限制历史记录数量
    if (generateHistory.value.length > 10) {
      generateHistory.value = generateHistory.value.slice(0, 10)
    }

    ElMessage.success(`成功生成 ${generatedCards.value.length} 个卡密`)
  } catch (error) {
    console.error('生成卡密失败:', error)
    ElMessage.error('生成卡密失败')
  } finally {
    generating.value = false
  }
}

// 复制单个卡密
function copyCode(code: string) {
  navigator.clipboard.writeText(code).then(() => {
    ElMessage.success('已复制')
  }).catch(() => {
    ElMessage.error('复制失败')
  })
}

// 复制全部卡密
function copyAllCodes() {
  const codes = generatedCards.value.map(c => c.code).join('\n')
  navigator.clipboard.writeText(codes).then(() => {
    ElMessage.success(`已复制 ${generatedCards.value.length} 个卡密`)
  }).catch(() => {
    ElMessage.error('复制失败')
  })
}

// 导出卡密
function exportCodes() {
  const codes = generatedCards.value.map(c => c.code).join('\n')
  const blob = new Blob([codes], { type: 'text/plain' })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = `cards_${Date.now()}.txt`
  link.click()
  URL.revokeObjectURL(url)
  ElMessage.success('导出成功')
}

// 重置并继续生成
function resetAndGenerate() {
  generatedCards.value = []
}

// 返回列表
function goBack() {
  router.push('/admin/cards')
}

// 跳转到列表
function goToList() {
  router.push('/admin/cards')
}

// ==================== 生命周期 ====================

onMounted(() => {
  fetchPackageList()
})
</script>

<style lang="scss" scoped>
.admin-card-generate-view {
  padding: 0;
}

.generate-content {
  margin-top: 0;
}

// 卡片样式
.form-card,
.result-card,
.tips-card,
.history-card {
  margin-bottom: 20px;
  border-radius: 12px;
  border: none;

  :deep(.el-card__header) {
    padding: 16px 20px;
    border-bottom: 1px solid #f0f0f0;
  }
}

.card-header {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 16px;
  font-weight: 600;
  color: #303133;

  .el-icon {
    color: #667eea;
  }

  .header-actions {
    margin-left: auto;
    display: flex;
    gap: 8px;
  }
}

// 表单提示
.form-tip {
  font-size: 12px;
  color: #909399;
  margin-top: 4px;
}

// 套餐选项
.package-option {
  display: flex;
  justify-content: space-between;
  width: 100%;

  .price {
    color: #f56c6c;
    font-weight: 500;
  }
}

// 套餐预览
.package-preview {
  width: 100%;
}

// 使用说明
.tips-list {
  margin: 0;
  padding-left: 20px;
  color: #606266;
  font-size: 14px;
  line-height: 2;

  li {
    margin-bottom: 4px;
  }
}

// 空结果
.empty-result {
  padding: 40px 0;
}

// 结果内容
.result-content {
  .result-stats {
    display: flex;
    align-items: center;
    gap: 12px;
    margin-bottom: 16px;

    .stats-info {
      font-size: 13px;
      color: #909399;
    }
  }
}

// 卡密列表
.code-list-scroll {
  margin-bottom: 16px;
}

.code-list {
  .code-item {
    display: flex;
    align-items: center;
    padding: 8px 12px;
    background: #f8f9fa;
    border-radius: 6px;
    margin-bottom: 8px;

    &:last-child {
      margin-bottom: 0;
    }

    .code-index {
      width: 30px;
      font-size: 12px;
      color: #909399;
    }

    .code-text {
      flex: 1;
      font-family: 'Consolas', 'Monaco', monospace;
      font-size: 14px;
      color: #303133;
      letter-spacing: 1px;
      background: transparent;
    }
  }
}

// 结果操作
.result-actions {
  display: flex;
  gap: 12px;
  justify-content: center;
  padding-top: 16px;
  border-top: 1px solid #f0f0f0;
}

// 历史记录
.history-card {
  :deep(.el-timeline) {
    padding-left: 0;
  }

  .history-item {
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 13px;

    .el-tag {
      margin-left: 4px;
    }

    .days {
      color: #909399;
      margin-left: auto;
    }
  }
}

// 响应式设计
@media (max-width: 992px) {
  .generate-content {
    .el-col {
      margin-bottom: 20px;
    }
  }
}

@media (max-width: 768px) {
  .card-header {
    font-size: 14px;

    .header-actions {
      flex-wrap: wrap;
    }
  }

  .result-stats {
    flex-direction: column;
    align-items: flex-start !important;
  }
}
</style>
