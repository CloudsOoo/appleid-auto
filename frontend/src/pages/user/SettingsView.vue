<template>
  <div class="page-container">
    <PageHeader title="用户设置" description="管理您的个人信息和账户安全" />

    <div class="settings-container">
      <!-- 基本信息 -->
      <el-card class="settings-card">
        <template #header>
          <div class="card-header">
            <span>基本信息</span>
          </div>
        </template>

        <el-form :model="profileForm" label-width="100px">
          <el-form-item label="用户名">
            <el-input v-model="profileForm.username" disabled />
          </el-form-item>
          <el-form-item label="邮箱">
            <el-input v-model="profileForm.email" disabled />
          </el-form-item>
          <el-form-item label="全名">
            <el-input v-model="profileForm.full_name" placeholder="请输入您的全名" />
          </el-form-item>
          <el-form-item label="手机号">
            <el-input v-model="profileForm.phone" placeholder="请输入手机号" />
          </el-form-item>
          <el-form-item>
            <el-button type="primary" @click="updateProfile" :loading="profileLoading">
              保存修改
            </el-button>
          </el-form-item>
        </el-form>
      </el-card>

      <!-- 修改密码 -->
      <el-card class="settings-card">
        <template #header>
          <div class="card-header">
            <span>修改密码</span>
          </div>
        </template>

        <el-form :model="passwordForm" label-width="100px" :rules="passwordRules" ref="passwordFormRef">
          <el-form-item label="当前密码" prop="old_password">
            <el-input v-model="passwordForm.old_password" type="password" show-password />
          </el-form-item>
          <el-form-item label="新密码" prop="new_password">
            <el-input v-model="passwordForm.new_password" type="password" show-password />
          </el-form-item>
          <el-form-item label="确认密码" prop="confirm_password">
            <el-input v-model="passwordForm.confirm_password" type="password" show-password />
          </el-form-item>
          <el-form-item>
            <el-button type="primary" @click="changePassword" :loading="passwordLoading">
              修改密码
            </el-button>
          </el-form-item>
        </el-form>
      </el-card>

      <!-- 双因素认证 -->
      <el-card class="settings-card">
        <template #header>
          <div class="card-header">
            <span>双因素认证 (2FA)</span>
            <el-tag v-if="twoFactorEnabled" type="success">已启用</el-tag>
            <el-tag v-else type="info">未启用</el-tag>
          </div>
        </template>

        <p class="section-desc">
          启用双因素认证可以大大增强您的账户安全性。启用后，登录时需要输入验证码。
        </p>

        <el-button
          v-if="!twoFactorEnabled"
          type="primary"
          @click="enable2FA"
          :loading="twoFactorLoading"
        >
          启用双因素认证
        </el-button>
        <el-button
          v-else
          type="danger"
          @click="disable2FA"
          :loading="twoFactorLoading"
        >
          关闭双因素认证
        </el-button>
      </el-card>

      <!-- API 密钥 -->
      <el-card class="settings-card">
        <template #header>
          <div class="card-header">
            <span>API 密钥</span>
          </div>
        </template>

        <p class="section-desc">
          API 密钥用于通过 API 访问您的账户数据。请妥善保管您的密钥。
        </p>

        <div v-if="apiKey" class="api-key-display">
          <el-input v-model="apiKey" readonly>
            <template #append>
              <el-button @click="copyApiKey">复制</el-button>
            </template>
          </el-input>
        </div>

        <div class="button-group">
          <el-button type="primary" @click="generateApiKey" :loading="apiKeyLoading">
            {{ apiKey ? '重新生成' : '生成 API 密钥' }}
          </el-button>
        </div>
      </el-card>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import type { FormInstance, FormRules } from 'element-plus'
import PageHeader from '@/components/common/PageHeader.vue'
import { getCurrentUserApi, updateUserApi, changePasswordApi } from '@/api/user'

const profileLoading = ref(false)
const passwordLoading = ref(false)
const twoFactorLoading = ref(false)
const apiKeyLoading = ref(false)
const twoFactorEnabled = ref(false)
const apiKey = ref('')
const passwordFormRef = ref<FormInstance>()

const profileForm = reactive({
  username: '',
  email: '',
  full_name: '',
  phone: ''
})

const passwordForm = reactive({
  old_password: '',
  new_password: '',
  confirm_password: ''
})

// 密码表单验证规则
const validateConfirmPassword = (rule: any, value: string, callback: any) => {
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
    { min: 8, message: '密码长度至少 8 位', trigger: 'blur' }
  ],
  confirm_password: [
    { required: true, message: '请确认新密码', trigger: 'blur' },
    { validator: validateConfirmPassword, trigger: 'blur' }
  ]
}

// 加载用户信息
const loadUserInfo = async () => {
  try {
    const response = await getCurrentUserApi()
    const user = response.data
    profileForm.username = user.username
    profileForm.email = user.email
    profileForm.full_name = user.full_name || ''
    profileForm.phone = user.phone || ''
    twoFactorEnabled.value = user.two_factor_enabled
  } catch (error) {
    console.error('加载用户信息失败', error)
  }
}

// 更新个人信息
const updateProfile = async () => {
  profileLoading.value = true
  try {
    await updateUserApi({
      full_name: profileForm.full_name,
      phone: profileForm.phone
    })
    ElMessage.success('个人信息已更新')
  } catch (error: any) {
    ElMessage.error(error.response?.data?.message || '更新失败')
  } finally {
    profileLoading.value = false
  }
}

// 修改密码
const changePassword = async () => {
  const valid = await passwordFormRef.value?.validate()
  if (!valid) return

  passwordLoading.value = true
  try {
    await changePasswordApi({
      old_password: passwordForm.old_password,
      new_password: passwordForm.new_password
    })
    ElMessage.success('密码已修改')
    passwordForm.old_password = ''
    passwordForm.new_password = ''
    passwordForm.confirm_password = ''
  } catch (error: any) {
    ElMessage.error(error.response?.data?.message || '修改失败')
  } finally {
    passwordLoading.value = false
  }
}

// 启用 2FA
const enable2FA = async () => {
  ElMessage.info('双因素认证功能开发中')
}

// 关闭 2FA
const disable2FA = async () => {
  try {
    await ElMessageBox.confirm('确定要关闭双因素认证吗？这将降低账户安全性。', '确认关闭')
    ElMessage.info('双因素认证功能开发中')
  } catch {
    // 取消操作
  }
}

// 生成 API 密钥
const generateApiKey = async () => {
  apiKeyLoading.value = true
  try {
    // TODO: 实现 API 密钥生成
    apiKey.value = 'ak_' + Math.random().toString(36).substring(2, 34)
    ElMessage.success('API 密钥已生成')
  } finally {
    apiKeyLoading.value = false
  }
}

// 复制 API 密钥
const copyApiKey = async () => {
  try {
    await navigator.clipboard.writeText(apiKey.value)
    ElMessage.success('已复制到剪贴板')
  } catch {
    ElMessage.error('复制失败')
  }
}

onMounted(() => {
  loadUserInfo()
})
</script>

<style scoped lang="scss">
.settings-container {
  max-width: 800px;
  margin: 0 auto;
}

.settings-card {
  margin-bottom: 20px;

  .card-header {
    display: flex;
    align-items: center;
    gap: 10px;
  }
}

.section-desc {
  color: #909399;
  font-size: 14px;
  margin-bottom: 20px;
}

.api-key-display {
  margin-bottom: 15px;
}

.button-group {
  display: flex;
  gap: 10px;
}
</style>
