<!--
  注册页面

  职责：
  - 提供用户注册功能
  - 表单验证（用户名、邮箱、密码格式）
  - 密码强度提示（弱、中、强）
  - 密码确认验证
  - 注册成功后跳转到登录页
  - 错误提示（用户名已存在、邮箱已注册等）
  - 提供登录链接

  上游依赖：
  - Vue Router（页面跳转）
  - Element Plus（表单组件、消息提示）
  - API 接口（注册接口，目前使用 Mock）

  下游调用者：
  - 登录页的注册链接
  - 用户主动访问注册页
-->

<template>
  <div class="register-view">
    <div class="register-container">
      <!-- 注册卡片 -->
      <div class="register-card">
        <!-- Logo 和标题 -->
        <div class="register-header">
          <div class="logo">
            <img src="/logo.svg" alt="Logo" class="logo-image" />
          </div>
          <h1 class="title">创建新账户</h1>
          <p class="subtitle">填写以下信息完成注册</p>
        </div>

        <!-- 注册表单 -->
        <el-form
          ref="registerFormRef"
          :model="registerForm"
          :rules="registerRules"
          class="register-form"
          size="large"
        >
          <!-- 用户名 -->
          <el-form-item prop="username">
            <el-input
              v-model="registerForm.username"
              placeholder="请输入用户名（3-20个字符）"
              :prefix-icon="User"
              clearable
              autocomplete="username"
            />
          </el-form-item>

          <!-- 邮箱 -->
          <el-form-item prop="email">
            <el-input
              v-model="registerForm.email"
              type="email"
              placeholder="请输入邮箱地址"
              :prefix-icon="Message"
              clearable
              autocomplete="email"
            />
          </el-form-item>

          <!-- 密码 -->
          <el-form-item prop="password">
            <el-input
              v-model="registerForm.password"
              type="password"
              placeholder="请输入密码（6-32个字符）"
              :prefix-icon="Lock"
              show-password
              clearable
              autocomplete="new-password"
              @input="updatePasswordStrength"
            />
          </el-form-item>

          <!-- 密码强度指示器 -->
          <div v-if="registerForm.password" class="password-strength">
            <div class="strength-label">密码强度：</div>
            <div class="strength-bar">
              <div
                class="strength-progress"
                :class="`strength-${passwordStrength.level}`"
                :style="{ width: passwordStrength.percentage + '%' }"
              ></div>
            </div>
            <div class="strength-text" :class="`text-${passwordStrength.level}`">
              {{ passwordStrength.text }}
            </div>
          </div>

          <!-- 确认密码 -->
          <el-form-item prop="confirmPassword">
            <el-input
              v-model="registerForm.confirmPassword"
              type="password"
              placeholder="请再次输入密码"
              :prefix-icon="Lock"
              show-password
              clearable
              autocomplete="new-password"
            />
          </el-form-item>

          <!-- 用户协议 -->
          <el-form-item prop="agreed">
            <el-checkbox v-model="registerForm.agreed">
              我已阅读并同意
              <el-link type="primary" :underline="false" @click="handleViewTerms">
                《用户协议》
              </el-link>
              和
              <el-link type="primary" :underline="false" @click="handleViewPrivacy">
                《隐私政策》
              </el-link>
            </el-checkbox>
          </el-form-item>

          <!-- 注册按钮 -->
          <el-form-item>
            <el-button
              type="primary"
              :loading="loading"
              class="register-button"
              @click="handleRegister"
            >
              {{ loading ? '注册中...' : '立即注册' }}
            </el-button>
          </el-form-item>
        </el-form>

        <!-- 底部链接 -->
        <div class="register-footer">
          <span class="footer-text">已有账户？</span>
          <el-link type="primary" :underline="false" @click="handleLogin">
            立即登录
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
import { ref, reactive, computed } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox, type FormInstance, type FormRules } from 'element-plus'
import { User, Lock, Message } from '@element-plus/icons-vue'

const router = useRouter()

/**
 * 注册表单类型
 */
interface RegisterForm {
  username: string
  email: string
  password: string
  confirmPassword: string
  agreed: boolean
}

/**
 * 表单引用
 */
const registerFormRef = ref<FormInstance>()

/**
 * 注册表单数据
 */
const registerForm = reactive<RegisterForm>({
  username: '',
  email: '',
  password: '',
  confirmPassword: '',
  agreed: false
})

/**
 * 加载状态
 */
const loading = ref(false)

/**
 * 密码强度
 */
const passwordStrength = reactive({
  level: 'weak' as 'weak' | 'medium' | 'strong',
  percentage: 0,
  text: '弱'
})

/**
 * 自定义验证：确认密码
 */
const validateConfirmPassword = (rule: any, value: string, callback: any) => {
  if (value === '') {
    callback(new Error('请再次输入密码'))
  } else if (value !== registerForm.password) {
    callback(new Error('两次输入的密码不一致'))
  } else {
    callback()
  }
}

/**
 * 自定义验证：用户协议
 */
const validateAgreed = (rule: any, value: boolean, callback: any) => {
  if (!value) {
    callback(new Error('请阅读并同意用户协议和隐私政策'))
  } else {
    callback()
  }
}

/**
 * 自定义验证：邮箱格式
 */
const validateEmail = (rule: any, value: string, callback: any) => {
  if (value === '') {
    callback(new Error('请输入邮箱地址'))
  } else {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
    if (!emailRegex.test(value)) {
      callback(new Error('请输入有效的邮箱地址'))
    } else {
      callback()
    }
  }
}

/**
 * 表单验证规则
 */
const registerRules: FormRules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 3, max: 20, message: '用户名长度为 3-20 个字符', trigger: 'blur' },
    {
      pattern: /^[a-zA-Z0-9_]+$/,
      message: '用户名只能包含字母、数字和下划线',
      trigger: 'blur'
    }
  ],
  email: [
    { required: true, validator: validateEmail, trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, max: 32, message: '密码长度为 6-32 个字符', trigger: 'blur' }
  ],
  confirmPassword: [
    { required: true, validator: validateConfirmPassword, trigger: 'blur' }
  ],
  agreed: [
    { required: true, validator: validateAgreed, trigger: 'change' }
  ]
}

/**
 * 计算密码强度
 */
function calculatePasswordStrength(password: string) {
  let strength = 0

  // 长度
  if (password.length >= 8) strength += 25
  if (password.length >= 12) strength += 25

  // 包含小写字母
  if (/[a-z]/.test(password)) strength += 15

  // 包含大写字母
  if (/[A-Z]/.test(password)) strength += 15

  // 包含数字
  if (/\d/.test(password)) strength += 10

  // 包含特殊字符
  if (/[!@#$%^&*(),.?":{}|<>]/.test(password)) strength += 10

  return strength
}

/**
 * 更新密码强度显示
 */
function updatePasswordStrength() {
  const strength = calculatePasswordStrength(registerForm.password)

  passwordStrength.percentage = strength

  if (strength < 40) {
    passwordStrength.level = 'weak'
    passwordStrength.text = '弱'
  } else if (strength < 70) {
    passwordStrength.level = 'medium'
    passwordStrength.text = '中'
  } else {
    passwordStrength.level = 'strong'
    passwordStrength.text = '强'
  }
}

/**
 * 注册处理
 */
async function handleRegister() {
  if (!registerFormRef.value) {
    return
  }

  try {
    // 表单验证
    await registerFormRef.value.validate()

    loading.value = true

    // TODO: 调用注册 API
    // import { registerApi } from '@/api/auth'
    // const response = await registerApi({
    //   username: registerForm.username,
    //   email: registerForm.email,
    //   password: registerForm.password
    // })

    // Mock 注册成功（临时实现）
    await new Promise(resolve => setTimeout(resolve, 1500))

    // 注册成功提示
    await ElMessageBox.alert(
      '注册成功！您现在可以使用新账户登录了。',
      '注册成功',
      {
        confirmButtonText: '去登录',
        type: 'success',
        showClose: false
      }
    )

    // 跳转到登录页
    router.push('/auth/login')
  } catch (error) {
    // 验证失败或用户取消
    if (error !== false && error !== 'cancel') {
      console.error('[RegisterView] Register error:', error)
      ElMessage.error('注册失败，请稍后重试')
    }
  } finally {
    loading.value = false
  }
}

/**
 * 跳转到登录页
 */
function handleLogin() {
  router.push('/auth/login')
}

/**
 * 查看用户协议
 */
function handleViewTerms() {
  ElMessage.info('用户协议页面即将上线')
  // TODO: 打开用户协议对话框或页面
}

/**
 * 查看隐私政策
 */
function handleViewPrivacy() {
  ElMessage.info('隐私政策页面即将上线')
  // TODO: 打开隐私政策对话框或页面
}
</script>

<style scoped lang="scss">
.register-view {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  overflow: hidden;
  padding: 40px 0;

  .register-container {
    position: relative;
    z-index: 1;
    width: 100%;
    max-width: 500px;
    padding: 20px;

    .register-card {
      background: #fff;
      border-radius: 16px;
      padding: 48px 40px;
      box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
      backdrop-filter: blur(10px);

      .register-header {
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

      .register-form {
        .password-strength {
          display: flex;
          align-items: center;
          gap: 12px;
          margin-top: -12px;
          margin-bottom: 18px;
          font-size: 13px;

          .strength-label {
            color: #606266;
            white-space: nowrap;
          }

          .strength-bar {
            flex: 1;
            height: 6px;
            background-color: #f0f0f0;
            border-radius: 3px;
            overflow: hidden;

            .strength-progress {
              height: 100%;
              transition: width 0.3s, background-color 0.3s;
              border-radius: 3px;

              &.strength-weak {
                background-color: #f56c6c;
              }

              &.strength-medium {
                background-color: #e6a23c;
              }

              &.strength-strong {
                background-color: #67c23a;
              }
            }
          }

          .strength-text {
            min-width: 24px;
            font-weight: 500;

            &.text-weak {
              color: #f56c6c;
            }

            &.text-medium {
              color: #e6a23c;
            }

            &.text-strong {
              color: #67c23a;
            }
          }
        }

        .register-button {
          width: 100%;
          height: 48px;
          font-size: 16px;
          font-weight: 500;
          border-radius: 8px;
        }
      }

      .register-footer {
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
  .register-view {
    padding: 24px 0;

    .register-container {
      max-width: 100%;
      padding: 16px;

      .register-card {
        padding: 32px 24px;
        border-radius: 12px;

        .register-header {
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
  .register-view {
    padding: 16px 0;

    .register-container {
      .register-card {
        padding: 24px 20px;

        .register-header {
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

        .register-form {
          .password-strength {
            flex-wrap: wrap;
            gap: 8px;
            margin-top: -8px;
            margin-bottom: 16px;

            .strength-label {
              width: 100%;
            }

            .strength-bar {
              flex: 1;
              min-width: 0;
            }
          }

          .register-button {
            height: 44px;
            font-size: 15px;
          }
        }

        .register-footer {
          margin-top: 24px;
          font-size: 13px;
        }
      }
    }
  }
}

// 暗色模式适配（可选）
@media (prefers-color-scheme: dark) {
  .register-view {
    .register-container {
      .register-card {
        background: rgba(255, 255, 255, 0.95);
      }
    }
  }
}
</style>
