<template>
  <div class="share-page">
    <el-card class="share-card">
      <template #header>
        <h2>Apple ID 分享</h2>
      </template>
      <div v-if="loading" class="loading">
        <el-skeleton :rows="5" animated />
      </div>
      <div v-else-if="error" class="error">
        <el-result icon="error" :title="error" />
      </div>
      <div v-else class="share-content">
        <p>{{ shareData?.title || '分享页面' }}</p>
        <p>Slug: {{ $route.params.slug }}</p>
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'

const route = useRoute()
const loading = ref(true)
const error = ref('')
const shareData = ref<any>(null)

onMounted(async () => {
  try {
    // TODO: 调用 API 获取分享页数据
    await new Promise(resolve => setTimeout(resolve, 500))
    shareData.value = { title: '分享页面' }
  } catch (e: any) {
    error.value = e.message || '加载失败'
  } finally {
    loading.value = false
  }
})
</script>

<style scoped lang="scss">
.share-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: 20px;
}

.share-card {
  width: 100%;
  max-width: 600px;
}
</style>
