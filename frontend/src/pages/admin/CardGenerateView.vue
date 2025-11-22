<template>
  <div class="page-container">
    <div class="page-header">
      <h1 class="page-title">生成卡密</h1>
    </div>

    <el-card style="max-width: 600px;">
      <el-form :model="form" :rules="rules" ref="formRef" label-width="100px">
        <el-form-item label="套餐" prop="package_id">
          <el-select v-model="form.package_id" placeholder="选择套餐" style="width: 100%;">
            <el-option
              v-for="pkg in packages"
              :key="pkg.id"
              :label="pkg.name"
              :value="pkg.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="数量" prop="count">
          <el-input-number v-model="form.count" :min="1" :max="100" />
        </el-form-item>
        <el-form-item label="有效天数" prop="valid_days">
          <el-input-number v-model="form.valid_days" :min="1" :max="3650" />
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="form.remark" type="textarea" :rows="2" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :loading="loading" @click="handleGenerate">
            生成
          </el-button>
          <el-button @click="$router.back()">返回</el-button>
        </el-form-item>
      </el-form>

      <el-divider v-if="generatedCards.length > 0">生成结果</el-divider>

      <div v-if="generatedCards.length > 0">
        <el-button type="primary" size="small" @click="handleCopy">复制全部</el-button>
        <el-input
          type="textarea"
          :value="generatedCards.join('\n')"
          :rows="10"
          readonly
          style="margin-top: 10px;"
        />
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import type { FormInstance } from 'element-plus'

const formRef = ref<FormInstance>()
const loading = ref(false)
const packages = ref<any[]>([])
const generatedCards = ref<string[]>([])

const form = reactive({
  package_id: undefined as number | undefined,
  count: 10,
  valid_days: 30,
  remark: ''
})

const rules = {
  package_id: [{ required: true, message: '请选择套餐', trigger: 'change' }],
  count: [{ required: true, message: '请输入数量', trigger: 'change' }],
  valid_days: [{ required: true, message: '请输入有效天数', trigger: 'change' }]
}

const handleGenerate = async () => {
  if (!formRef.value) return
  await formRef.value.validate(async (valid) => {
    if (valid) {
      loading.value = true
      try {
        // TODO: 调用生成 API
        await new Promise(resolve => setTimeout(resolve, 1000))
        generatedCards.value = Array.from({ length: form.count }, (_, i) =>
          `CARD-${Date.now()}-${i.toString().padStart(4, '0')}`
        )
        ElMessage.success('生成成功')
      } catch (error: any) {
        ElMessage.error(error.message || '生成失败')
      } finally {
        loading.value = false
      }
    }
  })
}

const handleCopy = () => {
  navigator.clipboard.writeText(generatedCards.value.join('\n'))
  ElMessage.success('已复制到剪贴板')
}

onMounted(async () => {
  // TODO: 加载套餐列表
  packages.value = [
    { id: 1, name: '基础版' },
    { id: 2, name: '专业版' },
    { id: 3, name: '企业版' }
  ]
})
</script>
