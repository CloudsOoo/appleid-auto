<template>
  <div class="share-page">
    <div v-if="loading" class="loading-container">
      <el-skeleton :rows="10" animated />
    </div>

    <div v-else-if="error" class="error-container">
      <el-empty :description="error">
        <el-button type="primary" @click="goHome">返回首页</el-button>
      </el-empty>
    </div>

    <div v-else class="share-content">
      <!-- 页面标题 -->
      <div class="share-header">
        <h1>{{ pageData?.title || '分享页' }}</h1>
      </div>

      <!-- 自定义 HTML 内容 -->
      <div
        v-if="pageData?.custom_html"
        class="custom-content"
        v-html="pageData.custom_html"
      ></div>

      <!-- 账号列表 -->
      <div v-if="pageData?.accounts?.length" class="account-list">
        <el-table :data="pageData.accounts" stripe>
          <el-table-column prop="apple_id" label="Apple ID" />
          <el-table-column prop="status" label="状态">
            <template #default="{ row }">
              <el-tag :type="row.status === 'normal' ? 'success' : 'danger'">
                {{ row.status === 'normal' ? '正常' : '异常' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column
            v-if="pageData.show_password"
            prop="password"
            label="密码"
          />
          <el-table-column label="操作" width="120">
            <template #default="{ row }">
              <el-button
                v-if="pageData.show_password"
                type="primary"
                size="small"
                @click="copyAccount(row)"
              >
                复制
              </el-button>
            </template>
          </el-table-column>
        </el-table>
      </div>

      <!-- 页脚 -->
      <div class="share-footer">
        <p>访问次数：{{ pageData?.view_count || 0 }}</p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { getSharePagePublicApi } from '@/api/share'

const route = useRoute()
const router = useRouter()

const loading = ref(true)
const error = ref('')
const pageData = ref<any>(null)

// 加载分享页数据
const loadPageData = async () => {
  const slug = route.params.slug as string
  if (!slug) {
    error.value = '无效的分享链接'
    loading.value = false
    return
  }

  try {
    const response = await getSharePagePublicApi(slug)
    pageData.value = response.data
  } catch (err: any) {
    error.value = err.response?.data?.message || '分享页不存在或已过期'
  } finally {
    loading.value = false
  }
}

// 复制账号信息
const copyAccount = async (account: any) => {
  const text = `Apple ID: ${account.apple_id}\n密码: ${account.password || '***'}`
  try {
    await navigator.clipboard.writeText(text)
    ElMessage.success('已复制到剪贴板')
  } catch {
    ElMessage.error('复制失败')
  }
}

// 返回首页
const goHome = () => {
  router.push('/')
}

onMounted(() => {
  loadPageData()
})
</script>

<style scoped lang="scss">
.share-page {
  min-height: 100vh;
  background-color: #f5f7fa;
  padding: 20px;
}

.loading-container,
.error-container {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 400px;
}

.share-content {
  max-width: 1000px;
  margin: 0 auto;
}

.share-header {
  text-align: center;
  padding: 40px 20px;

  h1 {
    font-size: 28px;
    color: #303133;
    margin: 0;
  }
}

.custom-content {
  background: #fff;
  border-radius: 8px;
  padding: 20px;
  margin-bottom: 20px;
}

.account-list {
  background: #fff;
  border-radius: 8px;
  padding: 20px;
}

.share-footer {
  text-align: center;
  padding: 20px;
  color: #909399;
  font-size: 14px;
}
</style>
