<!--
  用户设置页面

  职责：
  - 显示和编辑用户个人信息
  - 修改密码
  - 管理 2FA（启用/禁用双因素认证）
  - 显示权限信息和套餐状态

  上游依赖：
  - PageHeader（页面标题组件）
  - StatusTag（状态标签组件）
  - LoadingOverlay（加载遮罩组件）
  - Vue Router（页面跳转）
  - Element Plus（UI 组件）
  - auth API（认证相关接口）
  - user API（用户相关接口）
  - userStore（用户状态管理）

  下游调用者：
  - 路由（/settings）
  - 顶部导航栏用户菜单
  - 侧边栏导航

  使用的 API：
  - GET /users/me - 获取当前用户信息
  - PUT /users/me - 更新当前用户信息
  - GET /users/me/permission - 获取当前用户权限
  - POST /auth/change-password - 修改密码
  - POST /auth/2fa/enable - 启用 2FA
  - POST /auth/2fa/verify - 验证 2FA
  - POST /auth/2fa/disable - 禁用 2FA
-->

<template>
  <div class="settings-view">
    <!-- 页面标题 -->
    <PageHeader
      title="个人设置"
      description="管理您的账户信息和安全设置"
      :breadcrumbs="[
        { title: '首页', path: '/' },
        { title: '个人设置' }
      ]"
    />

    <LoadingOverlay :visible="pageLoading" text="加载中..." />

    <el-row :gutter="20">
      <!-- 左侧：设置菜单 -->
      <el-col :xs="24" :sm="24" :md="6" :lg="5">
        <div class="settings-menu">
          <el-menu
            :default-active="activeTab"
            @select="handleTabSelect"
          >
            <el-menu-item index="profile">
              <el-icon><User /></el-icon>
              <span>个人信息</span>
            </el-menu-item>
            <el-menu-item index="security">
              <el-icon><Lock /></el-icon>
              <span>安全设置</span>
            </el-menu-item>
            <el-menu-item index="permission">
              <el-icon><Key /></el-icon>
              <span>权限信息</span>
            </el-menu-item>
          </el-menu>
        </div>
      </el-col>

      <!-- 右侧：设置内容 -->
      <el-col :xs="24" :sm="24" :md="18" :lg="19">
        <div class="settings-content">
          <!-- 个人信息 -->
          <div v-show="activeTab === 'profile'" class="settings-section">
            <div class="section-header">
              <h3>个人信息</h3>
              <p>更新您的账户基本信息</p>
            </div>

            <el-form
              ref="profileFormRef"
              :model="profileForm"
              :rules="profileRules"
              label-width="100px"
              class="settings-form"
            >
              <el-form-item label="用户名" prop="username">
                <el-input
                  v-model="profileForm.username"
                  placeholder="请输入用户名"
                  maxlength="50"
                  show-word-limit
                />
              </el-form-item>

              <el-form-item label="邮箱" prop="email">
                <el-input
                  v-model="profileForm.email"
                  placeholder="请输入邮箱"
                  type="email"
                />
              </el-form-item>

              <el-form-item label="用户角色">
                <el-tag :type="userInfo?.role === 'admin' ? 'danger' : 'primary'">
                  {{ userInfo?.role === 'admin' ? '管理员' : '普通用户' }}
                </el-tag>
              </el-form-item>

              <el-form-item label="注册时间">
                <span class="info-text">{{ formatTime(userInfo?.created_at) }}</span>
              </el-form-item>

              <el-form-item label="账号状态">
                <StatusTag
                  :status="userInfo?.is_active ? 'success' : 'danger'"
                  :text="userInfo?.is_active ? '正常' : '已禁用'"
                />
              </el-form-item>

              <el-form-item>
                <el-button
                  type="primary"
                  :loading="profileLoading"
                  @click="handleUpdateProfile"
                >
                  保存修改
                </el-button>
                <el-button @click="resetProfileForm">重置</el-button>
              </el-form-item>
            </el-form>
          </div>

          <!-- 安全设置 -->
          <div v-show="activeTab === 'security'" class="settings-section">
            <div class="section-header">
              <h3>安全设置</h3>
              <p>管理您的密码和双因素认证</p>
            </div>

            <!-- 修改密码 -->
            <div class="security-card">
              <div class="card-header">
                <div class="card-title">
                  <el-icon><Lock /></el-icon>
                  <span>修改密码</span>
                </div>
                <el-tag type="info" size="small">建议定期更换</el-tag>
              </div>

              <el-form
                ref="passwordFormRef"
                :model="passwordForm"
                :rules="passwordRules"
                label-width="100px"
                class="password-form"
              >
                <el-form-item label="当前密码" prop="old_password">
                  <el-input
                    v-model="passwordForm.old_password"
                    type="password"
                    placeholder="请输入当前密码"
                    show-password
                  />
                </el-form-item>

                <el-form-item label="新密码" prop="new_password">
                  <el-input
                    v-model="passwordForm.new_password"
                    type="password"
                    placeholder="请输入新密码（至少6位）"
                    show-password
                  />
                  <div class="password-strength">
                    <span>密码强度：</span>
                    <el-progress
                      :percentage="passwordStrength.percentage"
                      :status="passwordStrength.status"
                      :stroke-width="6"
                      :show-text="false"
                      style="width: 100px; display: inline-block; margin: 0 8px;"
                    />
                    <span :class="['strength-text', passwordStrength.class]">
                      {{ passwordStrength.text }}
                    </span>
                  </div>
                </el-form-item>

                <el-form-item label="确认密码" prop="confirm_password">
                  <el-input
                    v-model="passwordForm.confirm_password"
                    type="password"
                    placeholder="请再次输入新密码"
                    show-password
                  />
                </el-form-item>

                <el-form-item>
                  <el-button
                    type="primary"
                    :loading="passwordLoading"
                    @click="handleChangePassword"
                  >
                    修改密码
                  </el-button>
                </el-form-item>
              </el-form>
            </div>

            <!-- 双因素认证 -->
            <div class="security-card">
              <div class="card-header">
                <div class="card-title">
                  <el-icon><Iphone /></el-icon>
                  <span>双因素认证 (2FA)</span>
                </div>
                <el-tag
                  :type="userInfo?.two_factor_enabled ? 'success' : 'info'"
                  size="small"
                >
                  {{ userInfo?.two_factor_enabled ? '已启用' : '未启用' }}
                </el-tag>
              </div>

              <div class="twofa-content">
                <p class="twofa-description">
                  双因素认证可以为您的账户提供额外的安全保护。
                  启用后，登录时需要输入手机验证器生成的动态验证码。
                </p>

                <div v-if="!userInfo?.two_factor_enabled" class="twofa-actions">
                  <el-button type="primary" @click="handleEnable2FA">
                    <el-icon><CirclePlus /></el-icon>
                    启用双因素认证
                  </el-button>
                </div>

                <div v-else class="twofa-actions">
                  <el-button type="danger" @click="handleDisable2FADialog">
                    <el-icon><CircleClose /></el-icon>
                    禁用双因素认证
                  </el-button>
                </div>
              </div>
            </div>
          </div>

          <!-- 权限信息 -->
          <div v-show="activeTab === 'permission'" class="settings-section">
            <div class="section-header">
              <h3>权限信息</h3>
              <p>查看您当前的套餐和配额使用情况</p>
            </div>

            <div class="permission-card">
              <!-- 套餐状态 -->
              <div class="permission-header">
                <div class="package-info">
                  <span class="package-label">当前套餐</span>
                  <el-tag type="primary" size="large">
                    {{ permission?.package_id ? `套餐 #${permission.package_id}` : '免费版' }}
                  </el-tag>
                </div>
                <div class="expire-info">
                  <span class="expire-label">到期时间</span>
                  <span :class="['expire-value', { 'expire-warning': isExpiringSoon, 'expire-danger': isExpired }]">
                    {{ permission?.expires_at ? formatTime(permission.expires_at) : '永久有效' }}
                  </span>
                  <el-tag v-if="isExpired" type="danger" size="small">已过期</el-tag>
                  <el-tag v-else-if="isExpiringSoon" type="warning" size="small">即将到期</el-tag>
                </div>
              </div>

              <!-- 配额使用情况 -->
              <el-divider content-position="left">配额使用</el-divider>

              <el-descriptions :column="2" border>
                <el-descriptions-item label="最大账号数">
                  {{ permission?.max_accounts || 0 }} 个
                </el-descriptions-item>
                <el-descriptions-item label="最大分享页数">
                  {{ permission?.max_share_pages || 0 }} 个
                </el-descriptions-item>
                <el-descriptions-item label="最大节点数">
                  {{ permission?.max_nodes || 0 }} 个
                </el-descriptions-item>
                <el-descriptions-item label="最大代理数">
                  {{ permission?.max_proxies || 0 }} 个
                </el-descriptions-item>
                <el-descriptions-item label="最大并发任务">
                  {{ permission?.max_concurrent_tasks || 0 }} 个
                </el-descriptions-item>
                <el-descriptions-item label="检测间隔">
                  {{ formatInterval(permission?.check_interval) }}
                </el-descriptions-item>
              </el-descriptions>

              <!-- 功能权限 -->
              <el-divider content-position="left">功能权限</el-divider>

              <div class="permission-features">
                <div class="feature-item">
                  <el-icon :class="permission?.allow_custom_html ? 'feature-enabled' : 'feature-disabled'">
                    <component :is="permission?.allow_custom_html ? 'Select' : 'CloseBold'" />
                  </el-icon>
                  <span>自定义 HTML</span>
                </div>
                <div class="feature-item">
                  <el-icon :class="permission?.allow_api_access ? 'feature-enabled' : 'feature-disabled'">
                    <component :is="permission?.allow_api_access ? 'Select' : 'CloseBold'" />
                  </el-icon>
                  <span>API 访问</span>
                </div>
                <div class="feature-item">
                  <el-icon :class="permission?.allow_export ? 'feature-enabled' : 'feature-disabled'">
                    <component :is="permission?.allow_export ? 'Select' : 'CloseBold'" />
                  </el-icon>
                  <span>数据导出</span>
                </div>
                <div class="feature-item">
                  <el-icon :class="permission?.allow_batch_import ? 'feature-enabled' : 'feature-disabled'">
                    <component :is="permission?.allow_batch_import ? 'Select' : 'CloseBold'" />
                  </el-icon>
                  <span>批量导入</span>
                </div>
              </div>

              <!-- 升级提示 -->
              <div class="upgrade-tip">
                <el-alert
                  title="想要更多功能？"
                  type="info"
                  :closable="false"
                  show-icon
                >
                  <template #default>
                    <span>使用卡密激活更高级的套餐，解锁更多配额和功能。</span>
                    <el-link type="primary" @click="goToActivate">立即激活</el-link>
                  </template>
                </el-alert>
              </div>
            </div>
          </div>
        </div>
      </el-col>
    </el-row>

    <!-- 启用 2FA 对话框 -->
    <el-dialog
      v-model="enable2FADialogVisible"
      title="启用双因素认证"
      width="500px"
      :close-on-click-modal="false"
    >
      <div v-if="twoFAData" class="twofa-setup">
        <div class="setup-steps">
          <p class="step-title">请按照以下步骤操作：</p>
          <ol>
            <li>在手机上下载 Google Authenticator 或其他 TOTP 验证器应用</li>
            <li>使用验证器扫描下方二维码</li>
            <li>输入验证器显示的 6 位验证码完成绑定</li>
          </ol>
        </div>

        <div class="qr-code-container">
          <img :src="twoFAData.qr_code" alt="2FA QR Code" class="qr-code" />
        </div>

        <div class="secret-key">
          <span class="key-label">手动输入密钥：</span>
          <el-input
            v-model="twoFAData.secret"
            readonly
            class="key-input"
          >
            <template #append>
              <el-button :icon="CopyDocument" @click="copySecret">复制</el-button>
            </template>
          </el-input>
        </div>

        <el-form class="verify-form">
          <el-form-item label="验证码">
            <el-input
              v-model="verifyCode"
              placeholder="请输入 6 位验证码"
              maxlength="6"
            />
          </el-form-item>
        </el-form>
      </div>

      <template #footer>
        <el-button @click="enable2FADialogVisible = false">取消</el-button>
        <el-button
          type="primary"
          :loading="verify2FALoading"
          @click="handleVerify2FA"
        >
          验证并启用
        </el-button>
      </template>
    </el-dialog>

    <!-- 禁用 2FA 对话框 -->
    <el-dialog
      v-model="disable2FADialogVisible"
      title="禁用双因素认证"
      width="400px"
      :close-on-click-modal="false"
    >
      <el-alert
        title="安全提示"
        type="warning"
        :closable="false"
        show-icon
        style="margin-bottom: 20px;"
      >
        禁用双因素认证会降低账户安全性，请谨慎操作。
      </el-alert>

      <el-form>
        <el-form-item label="验证码">
          <el-input
            v-model="disableVerifyCode"
            placeholder="请输入当前验证器的 6 位验证码"
            maxlength="6"
          />
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="disable2FADialogVisible = false">取消</el-button>
        <el-button
          type="danger"
          :loading="disable2FALoading"
          @click="handleDisable2FA"
        >
          确认禁用
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, type FormInstance, type FormRules } from 'element-plus'
import {
  User,
  Lock,
  Key,
  Iphone,
  CirclePlus,
  CircleClose,
  CopyDocument,
  Select,
  CloseBold
} from '@element-plus/icons-vue'
import PageHeader from '@/components/common/PageHeader.vue'
import StatusTag from '@/components/common/StatusTag.vue'
import LoadingOverlay from '@/components/common/LoadingOverlay.vue'
import { useUserStore } from '@/stores/user'
import {
  getCurrentUserApi,
  updateCurrentUserApi,
  getCurrentUserPermissionApi,
  type User as UserType,
  type UserPermission
} from '@/api/user'
import {
  changePasswordApi,
  enable2FAApi,
  verify2FAApi,
  disable2FAApi,
  type Enable2FAResponse
} from '@/api/auth'
import { formatDate } from '@/utils/date'

// ==================== 路由和状态 ====================

const router = useRouter()
const userStore = useUserStore()

// ==================== 响应式数据 ====================

// 加载状态
const pageLoading = ref(false)
const profileLoading = ref(false)
const passwordLoading = ref(false)
const verify2FALoading = ref(false)
const disable2FALoading = ref(false)

// 当前 Tab
const activeTab = ref('profile')

// 用户信息
const userInfo = ref<UserType | null>(null)
const permission = ref<UserPermission | null>(null)

// 表单引用
const profileFormRef = ref<FormInstance>()
const passwordFormRef = ref<FormInstance>()

// 个人信息表单
const profileForm = reactive({
  username: '',
  email: ''
})

// 密码表单
const passwordForm = reactive({
  old_password: '',
  new_password: '',
  confirm_password: ''
})

// 2FA 相关
const enable2FADialogVisible = ref(false)
const disable2FADialogVisible = ref(false)
const twoFAData = ref<Enable2FAResponse | null>(null)
const verifyCode = ref('')
const disableVerifyCode = ref('')

// ==================== 表单验证规则 ====================

const profileRules: FormRules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 3, max: 50, message: '用户名长度在 3-50 字符', trigger: 'blur' }
  ],
  email: [
    { required: true, message: '请输入邮箱', trigger: 'blur' },
    { type: 'email', message: '请输入正确的邮箱格式', trigger: 'blur' }
  ]
}

// 确认密码验证器
const validateConfirmPassword = (_rule: unknown, value: string, callback: (error?: Error) => void) => {
  if (value !== passwordForm.new_password) {
    callback(new Error('两次输入的密码不一致'))
  } else {
    callback()
  }
}

const passwordRules: FormRules = {
  old_password: [
    { required: true, message: '请输入当前密码', trigger: 'blur' }
  ],
  new_password: [
    { required: true, message: '请输入新密码', trigger: 'blur' },
    { min: 6, max: 32, message: '密码长度在 6-32 字符', trigger: 'blur' }
  ],
  confirm_password: [
    { required: true, message: '请确认新密码', trigger: 'blur' },
    { validator: validateConfirmPassword, trigger: 'blur' }
  ]
}

// ==================== 计算属性 ====================

// 密码强度
const passwordStrength = computed(() => {
  const pwd = passwordForm.new_password
  if (!pwd) {
    return { percentage: 0, status: '', text: '', class: '' }
  }

  let score = 0
  if (pwd.length >= 6) score += 20
  if (pwd.length >= 10) score += 20
  if (/[a-z]/.test(pwd) && /[A-Z]/.test(pwd)) score += 20
  if (/\d/.test(pwd)) score += 20
  if (/[!@#$%^&*(),.?":{}|<>]/.test(pwd)) score += 20

  if (score <= 40) {
    return { percentage: score, status: 'exception', text: '弱', class: 'strength-weak' }
  } else if (score <= 60) {
    return { percentage: score, status: 'warning', text: '中', class: 'strength-medium' }
  } else {
    return { percentage: score, status: 'success', text: '强', class: 'strength-strong' }
  }
})

// 是否即将过期（7天内）
const isExpiringSoon = computed(() => {
  if (!permission.value?.expires_at) return false
  const expiresAt = new Date(permission.value.expires_at).getTime()
  const now = Date.now()
  const sevenDays = 7 * 24 * 60 * 60 * 1000
  return expiresAt > now && expiresAt - now < sevenDays
})

// 是否已过期
const isExpired = computed(() => {
  if (!permission.value?.expires_at) return false
  return new Date(permission.value.expires_at).getTime() < Date.now()
})

// ==================== 方法 ====================

// 获取用户信息
async function fetchUserInfo() {
  pageLoading.value = true
  try {
    const [user, perm] = await Promise.all([
      getCurrentUserApi(),
      getCurrentUserPermissionApi()
    ])
    userInfo.value = user
    permission.value = perm

    // 填充表单
    profileForm.username = user.username
    profileForm.email = user.email
  } catch (error) {
    console.error('获取用户信息失败:', error)
    ElMessage.error('获取用户信息失败')
  } finally {
    pageLoading.value = false
  }
}

// 格式化时间
function formatTime(time: string | undefined): string {
  if (!time) return '-'
  return formatDate(time, 'YYYY-MM-DD HH:mm:ss')
}

// 格式化检测间隔
function formatInterval(seconds: number | undefined): string {
  if (!seconds) return '-'
  if (seconds < 60) return `${seconds} 秒`
  if (seconds < 3600) return `${Math.floor(seconds / 60)} 分钟`
  return `${Math.floor(seconds / 3600)} 小时`
}

// 处理 Tab 切换
function handleTabSelect(index: string) {
  activeTab.value = index
}

// 更新个人信息
async function handleUpdateProfile() {
  if (!profileFormRef.value) return

  try {
    await profileFormRef.value.validate()
    profileLoading.value = true

    await updateCurrentUserApi({
      username: profileForm.username,
      email: profileForm.email
    })

    // 更新本地状态
    if (userInfo.value) {
      userInfo.value.username = profileForm.username
      userInfo.value.email = profileForm.email
    }

    // 更新 store
    userStore.updateUserInfo({
      username: profileForm.username,
      email: profileForm.email
    })

    ElMessage.success('个人信息更新成功')
  } catch (error) {
    if (error !== false) {
      console.error('更新个人信息失败:', error)
      ElMessage.error('更新个人信息失败')
    }
  } finally {
    profileLoading.value = false
  }
}

// 重置个人信息表单
function resetProfileForm() {
  if (userInfo.value) {
    profileForm.username = userInfo.value.username
    profileForm.email = userInfo.value.email
  }
}

// 修改密码
async function handleChangePassword() {
  if (!passwordFormRef.value) return

  try {
    await passwordFormRef.value.validate()
    passwordLoading.value = true

    await changePasswordApi({
      old_password: passwordForm.old_password,
      new_password: passwordForm.new_password
    })

    ElMessage.success('密码修改成功，请重新登录')

    // 清空表单
    passwordForm.old_password = ''
    passwordForm.new_password = ''
    passwordForm.confirm_password = ''

    // 登出
    setTimeout(() => {
      userStore.logout()
      router.push('/login')
    }, 1500)
  } catch (error) {
    if (error !== false) {
      console.error('修改密码失败:', error)
      ElMessage.error('修改密码失败，请检查当前密码是否正确')
    }
  } finally {
    passwordLoading.value = false
  }
}

// 启用 2FA
async function handleEnable2FA() {
  try {
    const res = await enable2FAApi()
    twoFAData.value = res
    verifyCode.value = ''
    enable2FADialogVisible.value = true
  } catch (error) {
    console.error('获取 2FA 信息失败:', error)
    ElMessage.error('获取 2FA 信息失败')
  }
}

// 复制密钥
async function copySecret() {
  if (!twoFAData.value) return
  try {
    await navigator.clipboard.writeText(twoFAData.value.secret)
    ElMessage.success('密钥已复制到剪贴板')
  } catch {
    ElMessage.error('复制失败，请手动复制')
  }
}

// 验证并启用 2FA
async function handleVerify2FA() {
  if (!verifyCode.value || verifyCode.value.length !== 6) {
    ElMessage.warning('请输入 6 位验证码')
    return
  }

  verify2FALoading.value = true
  try {
    await verify2FAApi({ code: verifyCode.value })

    // 更新本地状态
    if (userInfo.value) {
      userInfo.value.two_factor_enabled = true
    }

    enable2FADialogVisible.value = false
    ElMessage.success('双因素认证已启用')
  } catch (error) {
    console.error('验证 2FA 失败:', error)
    ElMessage.error('验证码错误，请重新输入')
  } finally {
    verify2FALoading.value = false
  }
}

// 打开禁用 2FA 对话框
function handleDisable2FADialog() {
  disableVerifyCode.value = ''
  disable2FADialogVisible.value = true
}

// 禁用 2FA
async function handleDisable2FA() {
  if (!disableVerifyCode.value || disableVerifyCode.value.length !== 6) {
    ElMessage.warning('请输入 6 位验证码')
    return
  }

  disable2FALoading.value = true
  try {
    await disable2FAApi({ code: disableVerifyCode.value })

    // 更新本地状态
    if (userInfo.value) {
      userInfo.value.two_factor_enabled = false
    }

    disable2FADialogVisible.value = false
    ElMessage.success('双因素认证已禁用')
  } catch (error) {
    console.error('禁用 2FA 失败:', error)
    ElMessage.error('验证码错误，请重新输入')
  } finally {
    disable2FALoading.value = false
  }
}

// 跳转到卡密激活页面
function goToActivate() {
  router.push('/card/activate')
}

// ==================== 生命周期 ====================

onMounted(() => {
  fetchUserInfo()
})
</script>

<style lang="scss" scoped>
.settings-view {
  padding: 0;
}

// 设置菜单
.settings-menu {
  background: white;
  border-radius: 12px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.05);
  overflow: hidden;
  margin-bottom: 20px;

  :deep(.el-menu) {
    border-right: none;

    .el-menu-item {
      height: 50px;
      line-height: 50px;

      &.is-active {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;

        .el-icon {
          color: white;
        }
      }

      .el-icon {
        margin-right: 8px;
      }
    }
  }
}

// 设置内容
.settings-content {
  background: white;
  border-radius: 12px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.05);
  padding: 24px;
  min-height: 500px;
}

.settings-section {
  .section-header {
    margin-bottom: 24px;

    h3 {
      font-size: 18px;
      font-weight: 600;
      color: #303133;
      margin: 0 0 8px 0;
    }

    p {
      font-size: 14px;
      color: #909399;
      margin: 0;
    }
  }
}

.settings-form {
  max-width: 500px;
}

.info-text {
  color: #606266;
}

// 安全设置卡片
.security-card {
  background: #f8f9fa;
  border-radius: 8px;
  padding: 20px;
  margin-bottom: 20px;

  .card-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 16px;

    .card-title {
      display: flex;
      align-items: center;
      gap: 8px;
      font-size: 16px;
      font-weight: 500;
      color: #303133;

      .el-icon {
        font-size: 20px;
        color: #667eea;
      }
    }
  }
}

.password-form {
  max-width: 400px;
}

.password-strength {
  display: flex;
  align-items: center;
  margin-top: 8px;
  font-size: 12px;
  color: #909399;

  .strength-text {
    font-weight: 500;

    &.strength-weak {
      color: #f56c6c;
    }

    &.strength-medium {
      color: #e6a23c;
    }

    &.strength-strong {
      color: #67c23a;
    }
  }
}

.twofa-content {
  .twofa-description {
    color: #606266;
    font-size: 14px;
    margin-bottom: 16px;
    line-height: 1.6;
  }

  .twofa-actions {
    margin-top: 16px;
  }
}

// 权限信息卡片
.permission-card {
  .permission-header {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    margin-bottom: 20px;
    padding: 20px;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    border-radius: 12px;
    color: white;

    .package-info,
    .expire-info {
      display: flex;
      flex-direction: column;
      gap: 8px;
    }

    .package-label,
    .expire-label {
      font-size: 12px;
      opacity: 0.8;
    }

    .expire-value {
      font-size: 14px;

      &.expire-warning {
        color: #ffc107;
      }

      &.expire-danger {
        color: #ff6b6b;
      }
    }
  }

  .permission-features {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
    gap: 16px;
    margin-top: 16px;

    .feature-item {
      display: flex;
      align-items: center;
      gap: 8px;
      padding: 12px;
      background: #f8f9fa;
      border-radius: 8px;

      .el-icon {
        font-size: 18px;

        &.feature-enabled {
          color: #67c23a;
        }

        &.feature-disabled {
          color: #c0c4cc;
        }
      }

      span {
        font-size: 14px;
        color: #606266;
      }
    }
  }

  .upgrade-tip {
    margin-top: 24px;

    .el-link {
      margin-left: 8px;
    }
  }
}

// 2FA 设置对话框
.twofa-setup {
  .setup-steps {
    margin-bottom: 20px;

    .step-title {
      font-weight: 500;
      color: #303133;
      margin-bottom: 12px;
    }

    ol {
      padding-left: 20px;
      color: #606266;

      li {
        margin-bottom: 8px;
        line-height: 1.6;
      }
    }
  }

  .qr-code-container {
    display: flex;
    justify-content: center;
    padding: 20px;
    background: #f8f9fa;
    border-radius: 8px;
    margin-bottom: 20px;

    .qr-code {
      width: 200px;
      height: 200px;
    }
  }

  .secret-key {
    margin-bottom: 20px;

    .key-label {
      display: block;
      font-size: 14px;
      color: #606266;
      margin-bottom: 8px;
    }

    .key-input {
      :deep(.el-input__wrapper) {
        font-family: 'SF Mono', Monaco, Consolas, monospace;
      }
    }
  }

  .verify-form {
    margin-top: 20px;
  }
}

// 响应式设计
@media (max-width: 768px) {
  .settings-content {
    padding: 16px;
  }

  .settings-form {
    max-width: 100%;
  }

  .password-form {
    max-width: 100%;
  }

  .permission-card {
    .permission-header {
      flex-direction: column;
      gap: 16px;
    }

    .permission-features {
      grid-template-columns: repeat(2, 1fr);
    }
  }
}
</style>
