<template>
  <div class="card-generate-view">
    <page-header title="生成卡密" />
    <el-card>
      <el-form :model="form" label-width="120px" style="max-width: 500px;">
        <el-form-item label="套餐">
          <el-select v-model="form.packageId" placeholder="选择套餐">
            <el-option label="基础套餐" :value="1" />
            <el-option label="高级套餐" :value="2" />
          </el-select>
        </el-form-item>
        <el-form-item label="生成数量">
          <el-input-number v-model="form.count" :min="1" :max="100" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleGenerate" :loading="loading">
            生成
          </el-button>
          <el-button @click="$router.back()">返回</el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { ElMessage } from 'element-plus'
import PageHeader from '@/components/common/PageHeader.vue'

const loading = ref(false)
const form = reactive({
  packageId: null as number | null,
  count: 10
})

const handleGenerate = async () => {
  if (!form.packageId) {
    ElMessage.warning('请选择套餐')
    return
  }
  loading.value = true
  try {
    // TODO: Call API to generate cards
    ElMessage.success('卡密生成成功')
  } catch (error) {
    ElMessage.error('生成失败')
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.card-generate-view {
  padding: 20px;
}
</style>
