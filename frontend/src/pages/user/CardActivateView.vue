<template>
  <div class="page-container">
    <div class="page-header">
      <h1 class="page-title">卡密激活</h1>
    </div>
    <el-card class="activate-card">
      <el-form :model="form" :rules="rules" ref="formRef" label-width="100px">
        <el-form-item label="卡密" prop="code">
          <el-input
            v-model="form.code"
            placeholder="请输入卡密"
            maxlength="50"
            show-word-limit
          />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :loading="loading" @click="handleActivate">
            激活
          </el-button>
        </el-form-item>
      </el-form>

      <el-divider>当前套餐状态</el-divider>

      <el-descriptions :column="2" border>
        <el-descriptions-item label="套餐类型">{{ packageInfo.name || '-' }}</el-descriptions-item>
        <el-descriptions-item label="到期时间">{{ packageInfo.expires_at || '-' }}</el-descriptions-item>
        <el-descriptions-item label="账号配额">{{ packageInfo.max_accounts || 0 }}</el-descriptions-item>
        <el-descriptions-item label="已使用">{{ packageInfo.used_accounts || 0 }}</el-descriptions-item>
      </el-descriptions>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import type { FormInstance } from 'element-plus'

const formRef = ref<FormInstance>()
const loading = ref(false)
const form = reactive({
  code: ''
})

const rules = {
  code: [
    { required: true, message: '请输入卡密', trigger: 'blur' },
    { min: 8, max: 50, message: '卡密长度为 8-50 个字符', trigger: 'blur' }
  ]
}

const packageInfo = ref({
  name: '',
  expires_at: '',
  max_accounts: 0,
  used_accounts: 0
})

const handleActivate = async () => {
  if (!formRef.value) return
  await formRef.value.validate(async (valid) => {
    if (valid) {
      loading.value = true
      try {
        // TODO: 调用激活 API
        await new Promise(resolve => setTimeout(resolve, 1000))
        ElMessage.success('激活成功')
        form.code = ''
      } catch (error: any) {
        ElMessage.error(error.message || '激活失败')
      } finally {
        loading.value = false
      }
    }
  })
}

onMounted(async () => {
  // TODO: 获取当前套餐信息
})
</script>

<style scoped lang="scss">
.activate-card {
  max-width: 600px;
}
</style>
