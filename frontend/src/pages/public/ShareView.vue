<template>
  <div class="share-view">
    <el-card v-loading="loading">
      <template #header>
        <div class="card-header">
          <span>{{ shareData?.title || '分享页' }}</span>
        </div>
      </template>
      <div v-if="shareData" class="share-content" v-html="shareData.content"></div>
      <el-empty v-else-if="!loading" description="分享页不存在或已过期" />
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'

const route = useRoute()
const loading = ref(true)
const shareData = ref<{ title: string; content: string } | null>(null)

onMounted(async () => {
  const slug = route.params.slug as string
  try {
    // TODO: Fetch share page data from API
    // const response = await api.getSharePage(slug)
    // shareData.value = response.data
    loading.value = false
  } catch (error) {
    ElMessage.error('加载分享页失败')
    loading.value = false
  }
})
</script>

<style scoped>
.share-view {
  min-height: 100vh;
  padding: 40px 20px;
  background: #f5f7fa;
}

.share-view .el-card {
  max-width: 800px;
  margin: 0 auto;
}

.card-header {
  font-size: 18px;
  font-weight: 600;
}

.share-content {
  line-height: 1.8;
}
</style>
