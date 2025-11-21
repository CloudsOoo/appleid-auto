<!--
  双因素认证（2FA）验证页面

  职责：
  - 提供 2FA 验证码输入功能
  - 显示 QR 码（首次启用 2FA 时）
  - 验证码倒计时（30 秒）
  - 重新发送验证码
  - 信任设备选项（30 天内不再验证）
  - 验证成功后跳转到目标页面
  - 返回登录功能

  上游依赖：
  - Vue Router（页面跳转）
  - Element Plus（输入框、按钮、消息提示）
  - userStore（验证 2FA 逻辑）

  下游调用者：
  - 登录页（开启 2FA 的用户登录后跳转）
  - 路由守卫（需要 2FA 验证时跳转）
-->

<template>
  <div class="two-factor-view">
    <div class="two-factor-container">
      <!-- 2FA 验证卡片 -->
      <div class="two-factor-card">
        <!-- 返回按钮 -->
        <div class="back-button">
          <el-button :icon="ArrowLeft" circle @click="handleBack" />
        </div>

        <!-- 标题区域 -->
        <div class="two-factor-header">
          <div class="icon">
            <el-icon :size="64" color="#409EFF">
              <Lock />
            </el-icon>
          </div>
          <h1 class="title">双因素认证</h1>
          <p class="subtitle">
            {{ isSetup ? '扫描二维码设置双因素认证' : '请输入您的验证码' }}
          </p>
        </div>

        <!-- QR 码展示（首次设置） -->
        <div v-if="isSetup" class="qr-code-section">
          <div class="qr-code-box">
            <img :src="qrCodeUrl" alt="QR Code" class="qr-code-image" />
          </div>
          <p class="qr-code-tip">
            请使用 Google Authenticator 或其他 2FA 应用扫描此二维码
          </p>
          <div class="manual-entry">
            <p class="manual-label">或手动输入密钥：</p>
            <div class="manual-key">
              <span>{{ secretKey }}</span>
              <el-button
                :icon="CopyDocument"
                size="small"
                text
                @click="handleCopySecret"
              >
                复制
              </el-button>
            </div>
          </div>
        </div>

        <!-- 验证码输入区域 -->
        <div class="verification-section">
          <div class="code-inputs">
            <el-input
              v-for="(digit, index) in verificationCode"
              :key="index"
              :ref="(el) => setInputRef(el, index)"
              v-model="verificationCode[index]"
              class="code-input"
              maxlength="1"
              :disabled="loading"
              @input="(value) => handleInput(value, index)"
              @keydown="(e) => handleKeydown(e, index)"
              @paste="handlePaste"
            />
          </div>

          <!-- 倒计时提示 -->
          <div v-if="countdown > 0" class="countdown-tip">
            验证码有效期：{{ countdown }} 秒
          </div>

          <!-- 重新发送 -->
          <div v-if="!isSetup" class="resend-section">
            <span class="resend-text">没有收到验证码？</span>
            <el-button
              type="primary"
              link
              :disabled="resendDisabled"
              @click="handleResend"
            >
              {{ resendDisabled ? `重新发送 (${resendCountdown}s)` : '重新发送' }}
            </el-button>
          </div>

          <!-- 信任设备 -->
          <div class="trust-device">
            <el-checkbox v-model="trustDevice">
              信任此设备（30 天内不再验证）
            </el-checkbox>
          </div>

          <!-- 验证按钮 -->
          <el-button
            type="primary"
            :loading="loading"
            :disabled="!isCodeComplete"
            class="verify-button"
            @click="handleVerify"
          >
            {{ loading ? '验证中...' : '验证' }}
          </el-button>
        </div>

        <!-- 底部帮助链接 -->
        <div class="footer-links">
          <el-link type="info" :underline="false" @click="handleHelp">
            <el-icon><QuestionFilled /></el-icon>
            验证码帮助
          </el-link>
          <el-link type="info" :underline="false" @click="handleBack">
            返回登录
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
import { ref, reactive, computed, onMounted, onUnmounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { ArrowLeft, Lock, CopyDocument, QuestionFilled } from '@element-plus/icons-vue'
import { useUserStore } from '@/stores/user'

const router = useRouter()
const route = useRoute()
const userStore = useUserStore()

/**
 * 验证码（6 位）
 */
const verificationCode = reactive<string[]>(Array(6).fill(''))

/**
 * 输入框引用数组
 */
const inputRefs = ref<any[]>([])

/**
 * 是否为首次设置 2FA
 */
const isSetup = ref(false)

/**
 * QR 码 URL
 */
const qrCodeUrl = ref('https://api.qrserver.com/v1/create-qr-code/?size=200x200&data=otpauth://totp/AppleID:user@example.com?secret=JBSWY3DPEHPK3PXP&issuer=AppleID')

/**
 * 密钥（用于手动输入）
 */
const secretKey = ref('JBSWY3DPEHPK3PXP')

/**
 * 加载状态
 */
const loading = ref(false)

/**
 * 验证码倒计时（秒）
 */
const countdown = ref(30)

/**
 * 倒计时定时器
 */
let countdownTimer: number | null = null

/**
 * 重新发送倒计时（秒）
 */
const resendCountdown = ref(0)

/**
 * 重新发送定时器
 */
let resendTimer: number | null = null

/**
 * 信任设备
 */
const trustDevice = ref(false)

/**
 * 验证码是否完整
 */
const isCodeComplete = computed(() => {
  return verificationCode.every(digit => digit !== '')
})

/**
 * 重新发送是否禁用
 */
const resendDisabled = computed(() => {
  return resendCountdown.value > 0
})

/**
 * 设置输入框引用
 */
function setInputRef(el: any, index: number) {
  if (el) {
    inputRefs.value[index] = el
  }
}

/**
 * 输入处理
 */
function handleInput(value: string, index: number) {
  // 只允许数字
  const sanitized = value.replace(/\D/g, '')
  verificationCode[index] = sanitized

  // 自动聚焦下一个输入框
  if (sanitized && index < 5) {
    inputRefs.value[index + 1]?.focus()
  }

  // 如果所有输入框都填满，自动验证
  if (isCodeComplete.value) {
    handleVerify()
  }
}

/**
 * 键盘事件处理
 */
function handleKeydown(e: KeyboardEvent, index: number) {
  // Backspace：删除当前并聚焦前一个
  if (e.key === 'Backspace') {
    if (!verificationCode[index] && index > 0) {
      verificationCode[index - 1] = ''
      inputRefs.value[index - 1]?.focus()
    }
  }

  // 左箭头
  if (e.key === 'ArrowLeft' && index > 0) {
    inputRefs.value[index - 1]?.focus()
  }

  // 右箭头
  if (e.key === 'ArrowRight' && index < 5) {
    inputRefs.value[index + 1]?.focus()
  }
}

/**
 * 粘贴处理
 */
function handlePaste(e: ClipboardEvent) {
  e.preventDefault()
  const pastedData = e.clipboardData?.getData('text') || ''
  const digits = pastedData.replace(/\D/g, '').slice(0, 6)

  for (let i = 0; i < digits.length; i++) {
    verificationCode[i] = digits[i]
  }

  // 聚焦到最后填充的输入框
  const lastIndex = Math.min(digits.length - 1, 5)
  inputRefs.value[lastIndex]?.focus()

  // 如果粘贴的是完整的 6 位数字，自动验证
  if (digits.length === 6) {
    handleVerify()
  }
}

/**
 * 验证处理
 */
async function handleVerify() {
  if (!isCodeComplete.value || loading.value) {
    return
  }

  const code = verificationCode.join('')

  try {
    loading.value = true

    // TODO: 调用 2FA 验证 API
    // import { verifyTwoFactorApi } from '@/api/auth'
    // const response = await verifyTwoFactorApi({ code, trust_device: trustDevice.value })

    // Mock 验证（临时实现）
    await new Promise(resolve => setTimeout(resolve, 1000))

    // 模拟验证成功（正确的验证码：123456）
    if (code === '123456') {
      ElMessage.success('验证成功！')

      // 保存信任设备状态
      if (trustDevice.value) {
        localStorage.setItem('trusted_device', Date.now().toString())
      }

      // 跳转到目标页面
      const redirect = (route.query.redirect as string) || '/dashboard'
      setTimeout(() => {
        router.push(redirect)
      }, 500)
    } else {
      ElMessage.error('验证码错误，请重试')
      // 清空验证码
      verificationCode.fill('')
      inputRefs.value[0]?.focus()
    }
  } catch (error) {
    console.error('[TwoFactorView] Verify error:', error)
    ElMessage.error('验证失败，请稍后重试')
  } finally {
    loading.value = false
  }
}

/**
 * 返回登录
 */
function handleBack() {
  router.push('/auth/login')
}

/**
 * 复制密钥
 */
function handleCopySecret() {
  navigator.clipboard.writeText(secretKey.value).then(() => {
    ElMessage.success('密钥已复制到剪贴板')
  }).catch(() => {
    ElMessage.error('复制失败，请手动复制')
  })
}

/**
 * 重新发送验证码
 */
async function handleResend() {
  if (resendDisabled.value) {
    return
  }

  try {
    // TODO: 调用重新发送 API
    // import { resendTwoFactorApi } from '@/api/auth'
    // await resendTwoFactorApi()

    ElMessage.success('验证码已重新发送')

    // 启动重新发送倒计时（60 秒）
    resendCountdown.value = 60
    resendTimer = window.setInterval(() => {
      resendCountdown.value--
      if (resendCountdown.value <= 0) {
        clearInterval(resendTimer!)
        resendTimer = null
      }
    }, 1000)

    // 重置验证码倒计时
    countdown.value = 30
  } catch (error) {
    console.error('[TwoFactorView] Resend error:', error)
    ElMessage.error('重新发送失败，请稍后重试')
  }
}

/**
 * 帮助
 */
function handleHelp() {
  ElMessageBox.alert(
    '1. 打开 Google Authenticator 或其他 2FA 应用\n' +
    '2. 扫描二维码或手动输入密钥\n' +
    '3. 输入应用中显示的 6 位验证码\n' +
    '4. 如果验证码已过期，请等待新的验证码\n\n' +
    '如仍有问题，请联系管理员',
    '验证码帮助',
    {
      confirmButtonText: '我知道了',
      type: 'info'
    }
  )
}

/**
 * 启动倒计时
 */
function startCountdown() {
  countdownTimer = window.setInterval(() => {
    countdown.value--
    if (countdown.value <= 0) {
      clearInterval(countdownTimer!)
      countdownTimer = null
      ElMessage.warning('验证码已过期，请重新获取')
    }
  }, 1000)
}

/**
 * 组件挂载
 */
onMounted(() => {
  // 检查是否为首次设置
  isSetup.value = route.query.setup === 'true'

  // 聚焦第一个输入框
  setTimeout(() => {
    inputRefs.value[0]?.focus()
  }, 100)

  // 启动倒计时
  if (!isSetup.value) {
    startCountdown()
  }

  // TODO: 如果是首次设置，调用 API 获取 QR 码和密钥
  // import { getTwoFactorSetupApi } from '@/api/auth'
  // const { qr_code_url, secret } = await getTwoFactorSetupApi()
  // qrCodeUrl.value = qr_code_url
  // secretKey.value = secret
})

/**
 * 组件卸载
 */
onUnmounted(() => {
  if (countdownTimer) {
    clearInterval(countdownTimer)
  }
  if (resendTimer) {
    clearInterval(resendTimer)
  }
})
</script>

<style scoped lang="scss">
.two-factor-view {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  overflow: hidden;
  padding: 40px 0;

  .two-factor-container {
    position: relative;
    z-index: 1;
    width: 100%;
    max-width: 520px;
    padding: 20px;

    .two-factor-card {
      position: relative;
      background: #fff;
      border-radius: 16px;
      padding: 48px 40px;
      box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);

      .back-button {
        position: absolute;
        top: 20px;
        left: 20px;
      }

      .two-factor-header {
        text-align: center;
        margin-bottom: 32px;

        .icon {
          margin-bottom: 16px;
        }

        .title {
          margin: 0 0 12px;
          font-size: 28px;
          font-weight: 600;
          color: #303133;
        }

        .subtitle {
          margin: 0;
          font-size: 14px;
          color: #909399;
        }
      }

      .qr-code-section {
        margin-bottom: 32px;
        text-align: center;

        .qr-code-box {
          display: inline-block;
          padding: 16px;
          background: #f5f7fa;
          border-radius: 8px;
          margin-bottom: 16px;

          .qr-code-image {
            width: 200px;
            height: 200px;
            display: block;
          }
        }

        .qr-code-tip {
          margin: 0 0 20px;
          font-size: 13px;
          color: #606266;
          line-height: 1.6;
        }

        .manual-entry {
          padding: 16px;
          background: #f9fafb;
          border-radius: 8px;

          .manual-label {
            margin: 0 0 8px;
            font-size: 13px;
            color: #909399;
          }

          .manual-key {
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 12px;

            span {
              font-family: 'Courier New', monospace;
              font-size: 16px;
              font-weight: 600;
              color: #409eff;
              letter-spacing: 2px;
            }
          }
        }
      }

      .verification-section {
        .code-inputs {
          display: flex;
          justify-content: center;
          gap: 12px;
          margin-bottom: 20px;

          .code-input {
            width: 50px;

            :deep(.el-input__inner) {
              text-align: center;
              font-size: 24px;
              font-weight: 600;
              padding: 12px 0;
              height: 60px;
            }
          }
        }

        .countdown-tip {
          text-align: center;
          margin-bottom: 16px;
          font-size: 13px;
          color: #e6a23c;
        }

        .resend-section {
          text-align: center;
          margin-bottom: 20px;
          font-size: 14px;

          .resend-text {
            color: #909399;
            margin-right: 8px;
          }
        }

        .trust-device {
          text-align: center;
          margin-bottom: 24px;
        }

        .verify-button {
          width: 100%;
          height: 48px;
          font-size: 16px;
          font-weight: 500;
        }
      }

      .footer-links {
        margin-top: 32px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding-top: 24px;
        border-top: 1px solid #ebeef5;

        .el-link {
          font-size: 14px;
          display: flex;
          align-items: center;
          gap: 4px;
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
  .two-factor-view {
    padding: 24px 0;

    .two-factor-container {
      max-width: 100%;
      padding: 16px;

      .two-factor-card {
        padding: 40px 24px;

        .two-factor-header {
          margin-bottom: 24px;

          .icon {
            :deep(.el-icon) {
              font-size: 56px !important;
            }
          }

          .title {
            font-size: 24px;
          }
        }

        .qr-code-section {
          .qr-code-box .qr-code-image {
            width: 180px;
            height: 180px;
          }
        }

        .verification-section {
          .code-inputs {
            gap: 8px;

            .code-input {
              width: 45px;

              :deep(.el-input__inner) {
                font-size: 20px;
                height: 54px;
              }
            }
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
  .two-factor-view {
    padding: 16px 0;

    .two-factor-container {
      .two-factor-card {
        padding: 32px 20px;

        .two-factor-header {
          .icon {
            :deep(.el-icon) {
              font-size: 48px !important;
            }
          }

          .title {
            font-size: 20px;
          }

          .subtitle {
            font-size: 13px;
          }
        }

        .qr-code-section {
          .qr-code-box .qr-code-image {
            width: 160px;
            height: 160px;
          }

          .manual-entry {
            .manual-key span {
              font-size: 14px;
              letter-spacing: 1px;
            }
          }
        }

        .verification-section {
          .code-inputs {
            gap: 6px;

            .code-input {
              width: 40px;

              :deep(.el-input__inner) {
                font-size: 18px;
                height: 50px;
                padding: 10px 0;
              }
            }
          }

          .verify-button {
            height: 44px;
            font-size: 15px;
          }
        }

        .footer-links {
          flex-direction: column;
          gap: 12px;
        }
      }
    }
  }
}
</style>
