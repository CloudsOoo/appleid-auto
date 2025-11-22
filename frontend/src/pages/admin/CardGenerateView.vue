<template>
  <div class="page-container">
    <PageHeader title="生成卡密" description="批量生成卡密" />

    <el-row :gutter="20">
      <el-col :xs="24" :md="12">
        <el-card>
          <template #header>
            <span>生成设置</span>
          </template>

          <el-form :model="form" label-width="100px" :rules="rules" ref="formRef">
            <el-form-item label="选择套餐" prop="package_id">
              <el-select v-model="form.package_id" placeholder="请选择套餐" style="width: 100%">
                <el-option
                  v-for="pkg in packageList"
                  :key="pkg.id"
                  :label="`${pkg.name} (${pkg.duration_days}天)`"
                  :value="pkg.id"
                />
              </el-select>
            </el-form-item>

            <el-form-item label="生成数量" prop="count">
              <el-input-number
                v-model="form.count"
                :min="1"
                :max="1000"
                style="width: 100%"
              />
            </el-form-item>

            <el-form-item label="前缀">
              <el-input v-model="form.prefix" placeholder="可选，如 VIP-" maxlength="10" />
            </el-form-item>

            <el-form-item label="备注">
              <el-input
                v-model="form.remark"
                type="textarea"
                placeholder="可选备注信息"
                :rows="3"
              />
            </el-form-item>

            <el-form-item>
              <el-button type="primary" @click="generateCards" :loading="generating">
                生成卡密
              </el-button>
              <el-button @click="resetForm">重置</el-button>
            </el-form-item>
          </el-form>
        </el-card>
      </el-col>

      <el-col :xs="24" :md="12">
        <el-card v-if="generatedCards.length > 0">
          <template #header>
            <div class="result-header">
              <span>生成结果 ({{ generatedCards.length }} 个)</span>
              <div>
                <el-button size="small" @click="copyAllCards">复制全部</el-button>
                <el-button size="small" type="primary" @click="downloadCards">下载</el-button>
              </div>
            </div>
          </template>

          <el-scrollbar height="400px">
            <div class="card-list">
              <div v-for="(card, index) in generatedCards" :key="index" class="card-item">
                <span class="card-code">{{ card }}</span>
                <el-button link size="small" @click="copyCard(card)">
                  <el-icon><CopyDocument /></el-icon>
                </el-button>
              </div>
            </div>
          </el-scrollbar>
        </el-card>

        <el-card v-else>
          <el-empty description="暂无生成的卡密" />
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { CopyDocument } from '@element-plus/icons-vue'
import type { FormInstance, FormRules } from 'element-plus'
import PageHeader from '@/components/common/PageHeader.vue'
import { generateCardsApi } from '@/api/card'
import { getPackageListApi } from '@/api/package'

const formRef = ref<FormInstance>()
const generating = ref(false)
const packageList = ref<any[]>([])
const generatedCards = ref<string[]>([])

const form = reactive({
  package_id: null as number | null,
  count: 10,
  prefix: '',
  remark: ''
})

const rules: FormRules = {
  package_id: [
    { required: true, message: '请选择套餐', trigger: 'change' }
  ],
  count: [
    { required: true, message: '请输入数量', trigger: 'blur' }
  ]
}

// 加载套餐列表
const loadPackageList = async () => {
  try {
    const response = await getPackageListApi()
    packageList.value = response.data.items || response.data || []
  } catch (error) {
    console.error('加载套餐失败', error)
  }
}

// 生成卡密
const generateCards = async () => {
  const valid = await formRef.value?.validate()
  if (!valid) return

  generating.value = true
  try {
    const response = await generateCardsApi({
      package_id: form.package_id!,
      count: form.count,
      prefix: form.prefix || undefined,
      remark: form.remark || undefined
    })
    generatedCards.value = response.data.cards || []
    ElMessage.success(`成功生成 ${generatedCards.value.length} 个卡密`)
  } catch (error: any) {
    ElMessage.error(error.response?.data?.message || '生成失败')
  } finally {
    generating.value = false
  }
}

// 重置表单
const resetForm = () => {
  formRef.value?.resetFields()
  generatedCards.value = []
}

// 复制单个卡密
const copyCard = async (code: string) => {
  try {
    await navigator.clipboard.writeText(code)
    ElMessage.success('已复制')
  } catch {
    ElMessage.error('复制失败')
  }
}

// 复制全部卡密
const copyAllCards = async () => {
  try {
    await navigator.clipboard.writeText(generatedCards.value.join('\n'))
    ElMessage.success('已复制全部卡密')
  } catch {
    ElMessage.error('复制失败')
  }
}

// 下载卡密
const downloadCards = () => {
  const content = generatedCards.value.join('\n')
  const blob = new Blob([content], { type: 'text/plain' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `cards_${Date.now()}.txt`
  a.click()
  URL.revokeObjectURL(url)
  ElMessage.success('下载成功')
}

onMounted(() => {
  loadPackageList()
})
</script>

<style scoped lang="scss">
.result-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.card-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.card-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 12px;
  background: #f5f7fa;
  border-radius: 4px;

  .card-code {
    font-family: monospace;
    font-size: 13px;
  }
}
</style>
