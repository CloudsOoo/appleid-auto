<!--
  分享页访问页面

  职责：
  - 公开分享页展示（无需登录）
  - 密码保护验证
  - 访问日志记录（自动）
  - HTML 自定义内容渲染
  - 账号信息展示（Apple ID / 密码）
  - 复制功能

  上游依赖：
  - accessSharePageApi（公开访问接口）
  - Vue Router（获取 slug 参数）
  - Element Plus（表单组件、消息提示）

  下游调用者：
  - 用户通过分享链接访问
  - 路由：/share/:slug
-->

<template>
  <div class="share-view">
    <!-- 加载状态 -->
    <div v-if="loading" class="share-loading">
      <div class="loading-spinner">
        <div class="spinner"></div>
        <p class="loading-text">正在加载分享页...</p>
      </div>
    </div>

    <!-- 密码验证页面 -->
    <div v-else-if="needPassword" class="share-password">
      <div class="password-card">
        <div class="password-header">
          <div class="lock-icon">
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <rect x="3" y="11" width="18" height="11" rx="2" ry="2"></rect>
              <path d="M7 11V7a5 5 0 0 1 10 0v4"></path>
            </svg>
          </div>
          <h1 class="password-title">访问受保护的内容</h1>
          <p class="password-subtitle">此分享页已设置密码保护，请输入密码访问</p>
        </div>

        <el-form
          ref="passwordFormRef"
          :model="passwordForm"
          :rules="passwordRules"
          class="password-form"
          @submit.prevent="handlePasswordSubmit"
        >
          <el-form-item prop="password">
            <el-input
              v-model="passwordForm.password"
              type="password"
              placeholder="请输入访问密码"
              size="large"
              show-password
              @keyup.enter="handlePasswordSubmit"
            >
              <template #prefix>
                <el-icon><Lock /></el-icon>
              </template>
            </el-input>
          </el-form-item>

          <el-form-item>
            <el-button
              type="primary"
              size="large"
              class="submit-btn"
              :loading="verifying"
              @click="handlePasswordSubmit"
            >
              {{ verifying ? '验证中...' : '验证密码' }}
            </el-button>
          </el-form-item>
        </el-form>

        <p v-if="passwordError" class="password-error">
          <el-icon><CircleClose /></el-icon>
          {{ passwordError }}
        </p>
      </div>
    </div>

    <!-- 错误页面 -->
    <div v-else-if="error" class="share-error">
      <div class="error-card">
        <div class="error-icon">
          <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <circle cx="12" cy="12" r="10"></circle>
            <line x1="12" y1="8" x2="12" y2="12"></line>
            <line x1="12" y1="16" x2="12.01" y2="16"></line>
          </svg>
        </div>
        <h1 class="error-title">{{ errorTitle }}</h1>
        <p class="error-message">{{ errorMessage }}</p>
        <el-button type="primary" @click="handleRetry">
          重新加载
        </el-button>
      </div>
    </div>

    <!-- 分享内容页面 -->
    <div v-else-if="shareData" class="share-content">
      <!-- 自定义头部 HTML -->
      <div
        v-if="shareData.custom_html?.header"
        class="custom-header"
        v-html="shareData.custom_html.header"
      ></div>

      <!-- 主内容区域 -->
      <div class="content-wrapper">
        <!-- 标题区域 -->
        <div class="content-header">
          <h1 class="content-title">{{ shareData.title }}</h1>
          <p v-if="shareData.description" class="content-description">
            {{ shareData.description }}
          </p>
        </div>

        <!-- 账号信息卡片 -->
        <div v-if="shareData.account" class="account-card">
          <div class="card-header">
            <div class="card-icon">
              <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M18.36 6.64a9 9 0 1 1-12.73 0"></path>
                <line x1="12" y1="2" x2="12" y2="12"></line>
              </svg>
            </div>
            <span class="card-title">Apple ID 账号信息</span>
          </div>

          <div class="account-info">
            <!-- Apple ID -->
            <div class="info-row">
              <div class="info-label">
                <el-icon><User /></el-icon>
                <span>Apple ID</span>
              </div>
              <div class="info-value">
                <span class="value-text">{{ shareData.account.apple_id }}</span>
                <el-button
                  type="primary"
                  size="small"
                  text
                  @click="handleCopy(shareData.account.apple_id, 'Apple ID')"
                >
                  <el-icon><DocumentCopy /></el-icon>
                  复制
                </el-button>
              </div>
            </div>

            <!-- 密码 -->
            <div class="info-row">
              <div class="info-label">
                <el-icon><Lock /></el-icon>
                <span>密码</span>
              </div>
              <div class="info-value">
                <span class="value-text password-value">
                  {{ showPassword ? shareData.account.password : '••••••••' }}
                </span>
                <el-button
                  type="info"
                  size="small"
                  text
                  @click="showPassword = !showPassword"
                >
                  <el-icon>
                    <View v-if="!showPassword" />
                    <Hide v-else />
                  </el-icon>
                  {{ showPassword ? '隐藏' : '显示' }}
                </el-button>
                <el-button
                  type="primary"
                  size="small"
                  text
                  @click="handleCopy(shareData.account.password, '密码')"
                >
                  <el-icon><DocumentCopy /></el-icon>
                  复制
                </el-button>
              </div>
            </div>
          </div>

          <!-- 快速复制按钮 -->
          <div class="quick-copy">
            <el-button
              type="primary"
              size="large"
              @click="handleCopyAll"
            >
              <el-icon><DocumentCopy /></el-icon>
              一键复制全部
            </el-button>
          </div>
        </div>

        <!-- 自定义内容区域 -->
        <div
          v-if="shareData.custom_html?.body"
          class="custom-body"
          v-html="shareData.custom_html.body"
        ></div>

        <!-- 使用说明 -->
        <div class="usage-tips">
          <h3 class="tips-title">
            <el-icon><InfoFilled /></el-icon>
            使用说明
          </h3>
          <ul class="tips-list">
            <li>请在 iOS 设备上使用 App Store 登录此账号</li>
            <li>登录后可下载该账号已购买的应用程序</li>
            <li>请勿在 iCloud 设置中登录此账号</li>
            <li>使用完成后请及时退出登录</li>
            <li>如遇到账号问题请联系分享者</li>
          </ul>
        </div>
      </div>

      <!-- 自定义底部 HTML -->
      <div
        v-if="shareData.custom_html?.footer"
        class="custom-footer"
        v-html="shareData.custom_html.footer"
      ></div>

      <!-- 默认页脚 -->
      <div class="page-footer">
        <p class="footer-text">
          Powered by Apple ID 自动解锁系统
        </p>
        <p class="view-count" v-if="shareData.view_count">
          <el-icon><View /></el-icon>
          已被访问 {{ shareData.view_count }} 次
        </p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, computed } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage, type FormInstance, type FormRules } from 'element-plus'
import {
  Lock,
  User,
  View,
  Hide,
  DocumentCopy,
  InfoFilled,
  CircleClose
} from '@element-plus/icons-vue'
import { accessSharePageApi } from '@/api/share'

/**
 * 分享页数据类型
 */
interface SharePageData {
  title: string
  description?: string
  account?: {
    apple_id: string
    password: string
  }
  custom_html?: {
    header?: string
    body?: string
    footer?: string
  }
  view_count?: number
}

// 路由
const route = useRoute()
const slug = computed(() => route.params.slug as string)

// 状态
const loading = ref(true)
const error = ref(false)
const errorTitle = ref('')
const errorMessage = ref('')
const needPassword = ref(false)
const verifying = ref(false)
const passwordError = ref('')
const showPassword = ref(false)
const shareData = ref<SharePageData | null>(null)

// 密码表单
const passwordFormRef = ref<FormInstance>()
const passwordForm = reactive({
  password: ''
})
const passwordRules: FormRules = {
  password: [
    { required: true, message: '请输入访问密码', trigger: 'blur' }
  ]
}

/**
 * 加载分享页数据
 */
async function loadSharePage(password?: string) {
  try {
    loading.value = true
    error.value = false
    passwordError.value = ''

    const response = await accessSharePageApi(slug.value, password)

    // 检查响应
    if (response.code === 200 && response.data) {
      shareData.value = response.data
      needPassword.value = false
    } else if (response.code === 401 || response.code === 403) {
      // 需要密码
      needPassword.value = true
      if (password) {
        passwordError.value = '密码错误，请重新输入'
      }
    } else {
      throw new Error(response.message || '加载失败')
    }
  } catch (err: any) {
    // 检查是否需要密码
    if (err.response?.status === 401 || err.response?.status === 403) {
      needPassword.value = true
      if (password) {
        passwordError.value = '密码错误，请重新输入'
      }
    } else if (err.response?.status === 404) {
      error.value = true
      errorTitle.value = '页面不存在'
      errorMessage.value = '您访问的分享页不存在或已被删除'
    } else if (err.response?.status === 410) {
      error.value = true
      errorTitle.value = '页面已过期'
      errorMessage.value = '此分享页已过期，无法继续访问'
    } else {
      error.value = true
      errorTitle.value = '加载失败'
      errorMessage.value = err.message || '网络错误，请稍后重试'
    }
  } finally {
    loading.value = false
  }
}

/**
 * 提交密码验证
 */
async function handlePasswordSubmit() {
  if (!passwordFormRef.value) return

  try {
    await passwordFormRef.value.validate()
    verifying.value = true
    await loadSharePage(passwordForm.password)
  } catch {
    // 表单验证失败
  } finally {
    verifying.value = false
  }
}

/**
 * 复制到剪贴板
 */
async function handleCopy(text: string, label: string) {
  try {
    await navigator.clipboard.writeText(text)
    ElMessage.success(`${label}已复制到剪贴板`)
  } catch {
    // 降级方案：使用旧的 execCommand
    const textarea = document.createElement('textarea')
    textarea.value = text
    textarea.style.position = 'fixed'
    textarea.style.opacity = '0'
    document.body.appendChild(textarea)
    textarea.select()
    document.execCommand('copy')
    document.body.removeChild(textarea)
    ElMessage.success(`${label}已复制到剪贴板`)
  }
}

/**
 * 一键复制全部
 */
function handleCopyAll() {
  if (!shareData.value?.account) return

  const text = `Apple ID: ${shareData.value.account.apple_id}\n密码: ${shareData.value.account.password}`
  handleCopy(text, '账号信息')
}

/**
 * 重试加载
 */
function handleRetry() {
  error.value = false
  loadSharePage()
}

// 组件挂载时加载数据
onMounted(() => {
  loadSharePage()
})
</script>

<style lang="scss" scoped>
.share-view {
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

// 加载状态
.share-loading {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 100vh;

  .loading-spinner {
    text-align: center;
  }

  .spinner {
    width: 48px;
    height: 48px;
    border: 4px solid rgba(255, 255, 255, 0.3);
    border-top-color: #fff;
    border-radius: 50%;
    animation: spin 1s linear infinite;
    margin: 0 auto 16px;
  }

  .loading-text {
    color: #fff;
    font-size: 16px;
  }
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

// 密码验证页面
.share-password {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 100vh;
  padding: 20px;
}

.password-card {
  background: #fff;
  border-radius: 16px;
  padding: 40px;
  max-width: 400px;
  width: 100%;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.2);
}

.password-header {
  text-align: center;
  margin-bottom: 32px;

  .lock-icon {
    width: 64px;
    height: 64px;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    margin: 0 auto 20px;

    svg {
      width: 32px;
      height: 32px;
      color: #fff;
    }
  }

  .password-title {
    font-size: 24px;
    font-weight: 600;
    color: #1a1a2e;
    margin: 0 0 8px;
  }

  .password-subtitle {
    font-size: 14px;
    color: #6c757d;
    margin: 0;
  }
}

.password-form {
  .submit-btn {
    width: 100%;
  }
}

.password-error {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  color: #f56c6c;
  font-size: 14px;
  margin-top: 16px;
}

// 错误页面
.share-error {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 100vh;
  padding: 20px;
}

.error-card {
  background: #fff;
  border-radius: 16px;
  padding: 48px;
  max-width: 400px;
  width: 100%;
  text-align: center;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.2);

  .error-icon {
    width: 80px;
    height: 80px;
    background: #fef0f0;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    margin: 0 auto 24px;

    svg {
      width: 40px;
      height: 40px;
      color: #f56c6c;
    }
  }

  .error-title {
    font-size: 24px;
    font-weight: 600;
    color: #1a1a2e;
    margin: 0 0 12px;
  }

  .error-message {
    font-size: 14px;
    color: #6c757d;
    margin: 0 0 24px;
  }
}

// 分享内容页面
.share-content {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

.custom-header {
  // 自定义头部样式由用户 HTML 决定
}

.content-wrapper {
  flex: 1;
  max-width: 600px;
  width: 100%;
  margin: 0 auto;
  padding: 40px 20px;
}

.content-header {
  text-align: center;
  margin-bottom: 32px;

  .content-title {
    font-size: 28px;
    font-weight: 700;
    color: #fff;
    margin: 0 0 12px;
    text-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  }

  .content-description {
    font-size: 16px;
    color: rgba(255, 255, 255, 0.9);
    margin: 0;
  }
}

// 账号信息卡片
.account-card {
  background: #fff;
  border-radius: 16px;
  padding: 24px;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.15);
  margin-bottom: 24px;

  .card-header {
    display: flex;
    align-items: center;
    gap: 12px;
    padding-bottom: 16px;
    border-bottom: 1px solid #eee;
    margin-bottom: 20px;

    .card-icon {
      width: 40px;
      height: 40px;
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
      border-radius: 10px;
      display: flex;
      align-items: center;
      justify-content: center;

      svg {
        width: 20px;
        height: 20px;
        color: #fff;
      }
    }

    .card-title {
      font-size: 18px;
      font-weight: 600;
      color: #1a1a2e;
    }
  }
}

.account-info {
  .info-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 16px 0;

    &:not(:last-child) {
      border-bottom: 1px solid #f0f0f0;
    }
  }

  .info-label {
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 14px;
    color: #6c757d;

    .el-icon {
      font-size: 18px;
    }
  }

  .info-value {
    display: flex;
    align-items: center;
    gap: 8px;

    .value-text {
      font-size: 15px;
      font-weight: 500;
      color: #1a1a2e;
      font-family: 'SF Mono', 'Monaco', 'Inconsolata', monospace;

      &.password-value {
        letter-spacing: 1px;
      }
    }
  }
}

.quick-copy {
  margin-top: 24px;
  text-align: center;

  .el-button {
    width: 100%;
    max-width: 280px;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    border: none;
    font-size: 16px;
    padding: 12px 24px;
    height: auto;

    &:hover {
      opacity: 0.9;
    }
  }
}

// 自定义内容区域
.custom-body {
  background: #fff;
  border-radius: 16px;
  padding: 24px;
  margin-bottom: 24px;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.15);

  // 允许用户自定义样式
  :deep(*) {
    max-width: 100%;
  }

  :deep(img) {
    max-width: 100%;
    height: auto;
    border-radius: 8px;
  }

  :deep(a) {
    color: #667eea;
    text-decoration: none;

    &:hover {
      text-decoration: underline;
    }
  }
}

// 使用说明
.usage-tips {
  background: rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(10px);
  border-radius: 16px;
  padding: 24px;
  margin-bottom: 24px;

  .tips-title {
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 16px;
    font-weight: 600;
    color: #fff;
    margin: 0 0 16px;
  }

  .tips-list {
    margin: 0;
    padding-left: 20px;

    li {
      font-size: 14px;
      color: rgba(255, 255, 255, 0.9);
      line-height: 2;
    }
  }
}

// 自定义底部
.custom-footer {
  // 自定义底部样式由用户 HTML 决定
}

// 默认页脚
.page-footer {
  text-align: center;
  padding: 24px 20px;
  border-top: 1px solid rgba(255, 255, 255, 0.1);

  .footer-text {
    font-size: 14px;
    color: rgba(255, 255, 255, 0.7);
    margin: 0 0 8px;
  }

  .view-count {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 6px;
    font-size: 13px;
    color: rgba(255, 255, 255, 0.5);
    margin: 0;
  }
}

// 响应式适配
@media (max-width: 480px) {
  .password-card,
  .error-card {
    padding: 24px;
  }

  .password-header {
    .password-title {
      font-size: 20px;
    }

    .lock-icon {
      width: 56px;
      height: 56px;

      svg {
        width: 28px;
        height: 28px;
      }
    }
  }

  .content-wrapper {
    padding: 24px 16px;
  }

  .content-header {
    .content-title {
      font-size: 22px;
    }

    .content-description {
      font-size: 14px;
    }
  }

  .account-card {
    padding: 16px;

    .card-header {
      .card-title {
        font-size: 16px;
      }
    }
  }

  .account-info {
    .info-row {
      flex-direction: column;
      align-items: flex-start;
      gap: 8px;
    }

    .info-value {
      width: 100%;
      flex-wrap: wrap;

      .value-text {
        flex: 1;
        word-break: break-all;
      }
    }
  }

  .quick-copy {
    .el-button {
      width: 100%;
      max-width: none;
    }
  }
}
</style>
