<template>
  <div class="page-container">
    <div class="page-header">
      <h1 class="page-title">用户设置</h1>
    </div>

    <el-tabs v-model="activeTab">
      <el-tab-pane label="基本信息" name="profile">
        <el-card>
          <el-form :model="profileForm" label-width="100px">
            <el-form-item label="用户名">
              <el-input v-model="profileForm.username" disabled />
            </el-form-item>
            <el-form-item label="邮箱">
              <el-input v-model="profileForm.email" disabled />
            </el-form-item>
            <el-form-item label="全名">
              <el-input v-model="profileForm.full_name" placeholder="请输入全名" />
            </el-form-item>
            <el-form-item label="手机号">
              <el-input v-model="profileForm.phone" placeholder="请输入手机号" />
            </el-form-item>
            <el-form-item>
              <el-button type="primary" @click="handleSaveProfile">保存</el-button>
            </el-form-item>
          </el-form>
        </el-card>
      </el-tab-pane>

      <el-tab-pane label="修改密码" name="password">
        <el-card>
          <el-form :model="passwordForm" label-width="100px">
            <el-form-item label="当前密码">
              <el-input v-model="passwordForm.old_password" type="password" show-password />
            </el-form-item>
            <el-form-item label="新密码">
              <el-input v-model="passwordForm.new_password" type="password" show-password />
            </el-form-item>
            <el-form-item label="确认密码">
              <el-input v-model="passwordForm.confirm_password" type="password" show-password />
            </el-form-item>
            <el-form-item>
              <el-button type="primary" @click="handleChangePassword">修改密码</el-button>
            </el-form-item>
          </el-form>
        </el-card>
      </el-tab-pane>

      <el-tab-pane label="双因素认证" name="2fa">
        <el-card>
          <el-alert
            :title="is2FAEnabled ? '双因素认证已启用' : '双因素认证未启用'"
            :type="is2FAEnabled ? 'success' : 'warning'"
            :closable="false"
            show-icon
          />
          <div style="margin-top: 20px;">
            <el-button v-if="!is2FAEnabled" type="primary" @click="handleEnable2FA">
              启用 2FA
            </el-button>
            <el-button v-else type="danger" @click="handleDisable2FA">
              关闭 2FA
            </el-button>
          </div>
        </el-card>
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { useUserStore } from '@/stores/user'

const userStore = useUserStore()
const activeTab = ref('profile')
const is2FAEnabled = ref(false)

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

const handleSaveProfile = () => {
  ElMessage.success('保存成功')
}

const handleChangePassword = () => {
  if (passwordForm.new_password !== passwordForm.confirm_password) {
    ElMessage.error('两次输入的密码不一致')
    return
  }
  ElMessage.success('密码修改成功')
}

const handleEnable2FA = () => {
  ElMessage.info('2FA 功能开发中')
}

const handleDisable2FA = () => {
  ElMessage.info('2FA 功能开发中')
}

onMounted(() => {
  const user = userStore.user
  if (user) {
    profileForm.username = user.username || ''
    profileForm.email = user.email || ''
    profileForm.full_name = user.full_name || ''
    profileForm.phone = user.phone || ''
    is2FAEnabled.value = user.two_factor_enabled || false
  }
})
</script>
