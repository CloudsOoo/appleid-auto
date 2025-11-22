<template>
  <div class="card-activate-view">
    <page-header title="卡密激活" />
    <el-card>
      <el-form :model="form" label-width="100px" style="max-width: 500px;">
        <el-form-item label="卡密">
          <el-input v-model="form.cardKey" placeholder="请输入卡密" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleActivate" :loading="loading">
            激活
          </el-button>
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
  cardKey: ''
})

const handleActivate = async () => {
  if (!form.cardKey) {
    ElMessage.warning('请输入卡密')
    return
  }
  loading.value = true
  try {
    // TODO: Call API to activate card
    ElMessage.success('激活成功')
  } catch (error) {
    ElMessage.error('激活失败')
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.card-activate-view {
  padding: 20px;
}
</style>
