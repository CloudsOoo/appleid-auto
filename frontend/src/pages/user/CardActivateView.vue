<template>
  <div class="page-container">
    <PageHeader title="卡密激活" description="使用卡密激活或续费您的套餐" />

    <div class="activate-container">
      <el-card class="activate-card">
        <h3>输入卡密</h3>
        <p class="tips">请输入您购买的卡密来激活套餐</p>

        <el-form :model="form" @submit.prevent="activateCard">
          <el-form-item>
            <el-input
              v-model="form.cardCode"
              placeholder="请输入卡密"
              size="large"
              clearable
              maxlength="32"
            >
              <template #prefix>
                <el-icon><Key /></el-icon>
              </template>
            </el-input>
          </el-form-item>

          <el-form-item>
            <el-button
              type="primary"
              size="large"
              :loading="loading"
              @click="activateCard"
              style="width: 100%"
            >
              激活卡密
            </el-button>
          </el-form-item>
        </el-form>

        <!-- 激活结果 -->
        <div v-if="activateResult" class="result-card" :class="activateResult.success ? 'success' : 'error'">
          <el-icon v-if="activateResult.success" class="result-icon"><CircleCheck /></el-icon>
          <el-icon v-else class="result-icon"><CircleClose /></el-icon>
          <h4>{{ activateResult.success ? '激活成功' : '激活失败' }}</h4>
          <p>{{ activateResult.message }}</p>
          <div v-if="activateResult.success && activateResult.package" class="package-info">
            <p><strong>套餐:</strong> {{ activateResult.package.name }}</p>
            <p><strong>有效期:</strong> {{ activateResult.package.duration_days }} 天</p>
          </div>
        </div>
      </el-card>

      <!-- 当前套餐信息 -->
      <el-card class="info-card">
        <h3>当前套餐</h3>
        <div v-if="currentPackage" class="package-detail">
          <el-descriptions :column="1" border>
            <el-descriptions-item label="套餐名称">{{ currentPackage.name || '未激活' }}</el-descriptions-item>
            <el-descriptions-item label="到期时间">{{ formatDate(currentPackage.expires_at) }}</el-descriptions-item>
            <el-descriptions-item label="账号配额">{{ currentPackage.accounts_count || 0 }} / {{ currentPackage.max_accounts || 0 }}</el-descriptions-item>
            <el-descriptions-item label="分享页配额">{{ currentPackage.share_pages_count || 0 }} / {{ currentPackage.max_share_pages || 0 }}</el-descriptions-item>
            <el-descriptions-item label="每日解锁次数">{{ currentPackage.unlock_count_today || 0 }} / {{ currentPackage.max_unlock_per_day || 0 }}</el-descriptions-item>
          </el-descriptions>
        </div>
        <el-empty v-else description="暂无套餐信息" />
      </el-card>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Key, CircleCheck, CircleClose } from '@element-plus/icons-vue'
import PageHeader from '@/components/common/PageHeader.vue'
import { activateCardApi } from '@/api/card'
import { getCurrentUserApi } from '@/api/user'
import dayjs from 'dayjs'

const loading = ref(false)
const form = reactive({
  cardCode: ''
})

const activateResult = ref<any>(null)
const currentPackage = ref<any>(null)

// 激活卡密
const activateCard = async () => {
  if (!form.cardCode.trim()) {
    ElMessage.warning('请输入卡密')
    return
  }

  loading.value = true
  activateResult.value = null

  try {
    const response = await activateCardApi(form.cardCode.trim())
    activateResult.value = {
      success: true,
      message: response.data.message || '激活成功',
      package: response.data.package
    }
    form.cardCode = ''
    loadCurrentPackage()
  } catch (error: any) {
    activateResult.value = {
      success: false,
      message: error.response?.data?.message || '激活失败，请检查卡密是否正确'
    }
  } finally {
    loading.value = false
  }
}

// 加载当前套餐信息
const loadCurrentPackage = async () => {
  try {
    const response = await getCurrentUserApi()
    currentPackage.value = response.data.permissions || null
  } catch (error) {
    console.error('加载套餐信息失败', error)
  }
}

// 格式化日期
const formatDate = (date: string) => {
  if (!date) return '未激活'
  return dayjs(date).format('YYYY-MM-DD HH:mm')
}

onMounted(() => {
  loadCurrentPackage()
})
</script>

<style scoped lang="scss">
.activate-container {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
  max-width: 1000px;
  margin: 0 auto;

  @media (max-width: 768px) {
    grid-template-columns: 1fr;
  }
}

.activate-card,
.info-card {
  h3 {
    margin: 0 0 8px;
    font-size: 18px;
    color: #303133;
  }

  .tips {
    color: #909399;
    font-size: 14px;
    margin-bottom: 20px;
  }
}

.result-card {
  margin-top: 20px;
  padding: 20px;
  border-radius: 8px;
  text-align: center;

  &.success {
    background-color: #f0f9eb;
    border: 1px solid #67c23a;

    .result-icon {
      color: #67c23a;
    }
  }

  &.error {
    background-color: #fef0f0;
    border: 1px solid #f56c6c;

    .result-icon {
      color: #f56c6c;
    }
  }

  .result-icon {
    font-size: 48px;
    margin-bottom: 10px;
  }

  h4 {
    margin: 0 0 8px;
    font-size: 16px;
  }

  p {
    margin: 0;
    color: #606266;
    font-size: 14px;
  }

  .package-info {
    margin-top: 15px;
    padding-top: 15px;
    border-top: 1px dashed #dcdfe6;
    text-align: left;

    p {
      margin: 5px 0;
    }
  }
}

.package-detail {
  margin-top: 10px;
}
</style>
