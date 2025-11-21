<!--
  登录页面

  职责：
  - 提供用户名/密码登录功能
  - 表单验证（用户名、密码格式）
  - 记住我功能（保存用户名到 localStorage）
  - 登录成功后跳转到指定页面
  - 错误提示（账号不存在、密码错误等）
  - 提供注册和忘记密码链接

  上游依赖：
  - userStore（登录逻辑）
  - Vue Router（页面跳转）
  - Element Plus（表单组件、消息提示）

  下游调用者：
  - 路由守卫（未登录时自动跳转到登录页）
  - 用户主动访问登录页
-->

<template>
  <div class="login-view">
    <div class="login-container">
      <!-- 登录卡片 -->
      <div class="login-card">
        <!-- Logo 和标题 -->
        <div class="login-header">
          <div class="logo">
            <img src="/logo.svg" alt="Logo" class="logo-image" />
          </div>
          <h1 class="title">Apple ID 自动解锁系统</h1>
          <p class="subtitle">欢迎回来，请登录您的账户</p>
        </div>

        <!-- 登录表单 -->
        <el-form
          ref="loginFormRef"
          :model="loginForm"
          :rules="loginRules"
          class="login-form"
          size="large"
          @keyup.enter="handleLogin"
        >
          <!-- 用户名 -->
          <el-form-item prop="username">
            <el-input
              v-model="loginForm.username"
              placeholder="请输入用户名或邮箱"
              :prefix-icon="User"
              clearable
              autocomplete="username"
            />
          </el-form-item>

          <!-- 密码 -->
          <el-form-item prop="password">
            <el-input
              v-model="loginForm.password"
              type="password"
              placeholder="请输入密码"
              :prefix-icon="Lock"
              show-password
              clearable
              autocomplete="current-password"
            />
          </el-form-item>

          <!-- 记住我 & 忘记密码 -->
          <div class="form-options">
            <el-checkbox v-model="loginForm.remember">记住我</el-checkbox>
            <el-link type="primary" :underline="false" @click="handleForgotPassword">
              忘记密码？
            </el-link>
          </div>

          <!-- 登录按钮 -->
          <el-form-item>
            <el-button
              type="primary"
              :loading="loading"
              class="login-button"
              @click="handleLogin"
            >
              {{ loading ? '登录中...' : '登 录' }}
            </el-button>
          </el-form-item>
        </el-form>

        <!-- 底部链接 -->
        <div class="login-footer">
          <span class="footer-text">还没有账户？</span>
          <el-link type="primary" :underline="false" @click="handleRegister">
            立即注册
          </el-link>
        </div>
      </div>

      <!-- 页脚信息 -->
      <div class="page-footer">
        <p>&copy; 2025 Apple ID 自动解锁系统. All rights reserved.</p>
      </div>
    </div>

    <!-- 背景装饰 -->
    <div class="background-decoration">
      <div class="decoration-circle circle-1"></div>
      <div class="decoration-circle circle-2"></div>
      <div class="decoration-circle circle-3"></div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage, type FormInstance, type FormRules } from 'element-plus'
import { User, Lock } from '@element-plus/icons-vue'
import { useUserStore } from '@/stores/user'
import type { LoginCredentials } from '@/stores/user'

const router = useRouter()
const route = useRoute()
const userStore = useUserStore()

/**
 * 表单引用
 */
const loginFormRef = ref<FormInstance>()

/**
 * 登录表单数据
 */
const loginForm = reactive<LoginCredentials & { remember: boolean }>({
  username: '',
  password: '',
  remember: false
})

/**
 * 加载状态
 */
const loading = ref(false)

/**
 * 表单验证规则
 */
const loginRules: FormRules = {
  username: [
    { required: true, message: '请输入用户名或邮箱', trigger: 'blur' },
    { min: 3, max: 50, message: '用户名长度为 3-50 个字符', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, max: 32, message: '密码长度为 6-32 个字符', trigger: 'blur' }
  ]
}

/**
 * 登录处理
 */
async function handleLogin() {
  if (!loginFormRef.value) {
    return
  }

  try {
    // 表单验证
    await loginFormRef.value.validate()

    loading.value = true

    // 调用登录接口
    const success = await userStore.login({
      username: loginForm.username,
      password: loginForm.password
    })

    if (success) {
      // 保存"记住我"状态
      if (loginForm.remember) {
        localStorage.setItem('remembered_username', loginForm.username)
      } else {
        localStorage.removeItem('remembered_username')
      }

      ElMessage.success('登录成功！')

      // 获取重定向路径（如果有）
      const redirect = (route.query.redirect as string) || '/dashboard'

      // 延迟跳转，让用户看到成功提示
      setTimeout(() => {
        router.push(redirect)
      }, 500)
    } else {
      ElMessage.error('用户名或密码错误')
    }
  } catch (error) {
    // 验证失败
    if (error !== false) {
      console.error('[LoginView] Login error:', error)
      ElMessage.error('登录失败，请稍后重试')
    }
  } finally {
    loading.value = false
  }
}

/**
 * 跳转到注册页
 */
function handleRegister() {
  router.push('/auth/register')
}

/**
 * 忘记密码处理
 */
function handleForgotPassword() {
  ElMessage.info('密码重置功能即将上线，请联系管理员')
  // TODO: 实现忘记密码功能
  // router.push('/auth/forgot-password')
}

/**
 * 组件挂载时恢复"记住我"的用户名
 */
onMounted(() => {
  const rememberedUsername = localStorage.getItem('remembered_username')
  if (rememberedUsername) {
    loginForm.username = rememberedUsername
    loginForm.remember = true
  }

  // 如果已经登录，直接跳转到 dashboard
  if (userStore.isLoggedIn) {
    router.push('/dashboard')
  }
})
</script>

<style scoped lang="scss">
.login-view {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  overflow: hidden;

  .login-container {
    position: relative;
    z-index: 1;
    width: 100%;
    max-width: 450px;
    padding: 20px;

    .login-card {
      background: #fff;
      border-radius: 16px;
      padding: 48px 40px;
      box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
      backdrop-filter: blur(10px);

      .login-header {
        text-align: center;
        margin-bottom: 40px;

        .logo {
          margin-bottom: 20px;

          .logo-image {
            width: 80px;
            height: 80px;
            border-radius: 16px;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
          }
        }

        .title {
          margin: 0 0 12px;
          font-size: 28px;
          font-weight: 600;
          color: #303133;
          line-height: 1.2;
        }

        .subtitle {
          margin: 0;
          font-size: 14px;
          color: #909399;
          line-height: 1.5;
        }
      }

      .login-form {
        .form-options {
          display: flex;
          align-items: center;
          justify-content: space-between;
          margin-bottom: 24px;
        }

        .login-button {
          width: 100%;
          height: 48px;
          font-size: 16px;
          font-weight: 500;
          border-radius: 8px;
        }
      }

      .login-footer {
        margin-top: 32px;
        text-align: center;
        font-size: 14px;
        color: #606266;

        .footer-text {
          margin-right: 8px;
        }
      }
    }

    .page-footer {
      margin-top: 32px;
      text-align: center;
      color: rgba(255, 255, 255, 0.8);
      font-size: 13px;

      p {
        margin: 0;
      }
    }
  }

  .background-decoration {
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    pointer-events: none;
    overflow: hidden;

    .decoration-circle {
      position: absolute;
      border-radius: 50%;
      background: rgba(255, 255, 255, 0.1);
      animation: float 20s infinite ease-in-out;

      &.circle-1 {
        width: 300px;
        height: 300px;
        top: -150px;
        right: -150px;
        animation-delay: 0s;
      }

      &.circle-2 {
        width: 200px;
        height: 200px;
        bottom: -100px;
        left: -100px;
        animation-delay: 5s;
      }

      &.circle-3 {
        width: 150px;
        height: 150px;
        top: 50%;
        left: -75px;
        animation-delay: 10s;
      }
    }
  }
}

@keyframes float {
  0%, 100% {
    transform: translateY(0) rotate(0deg);
  }
  50% {
    transform: translateY(-20px) rotate(180deg);
  }
}

// 响应式设计
@media (max-width: 768px) {
  .login-view {
    .login-container {
      max-width: 100%;
      padding: 16px;

      .login-card {
        padding: 32px 24px;
        border-radius: 12px;

        .login-header {
          margin-bottom: 32px;

          .logo .logo-image {
            width: 64px;
            height: 64px;
          }

          .title {
            font-size: 24px;
          }
        }
      }

      .page-footer {
        margin-top: 24px;
        font-size: 12px;
      }
    }
  }
}

@media (max-width: 480px) {
  .login-view {
    .login-container {
      .login-card {
        padding: 24px 20px;

        .login-header {
          margin-bottom: 24px;

          .logo .logo-image {
            width: 56px;
            height: 56px;
          }

          .title {
            font-size: 20px;
          }

          .subtitle {
            font-size: 13px;
          }
        }

        .login-form {
          .form-options {
            flex-direction: column;
            align-items: flex-start;
            gap: 12px;
            margin-bottom: 20px;
          }

          .login-button {
            height: 44px;
            font-size: 15px;
          }
        }

        .login-footer {
          margin-top: 24px;
          font-size: 13px;
        }
      }
    }
  }
}

// 暗色模式适配（可选）
@media (prefers-color-scheme: dark) {
  .login-view {
    .login-container {
      .login-card {
        background: rgba(255, 255, 255, 0.95);
      }
    }
  }
}
</style>
