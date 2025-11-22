<template>
  <div class="settings-view">
    <page-header title="用户设置" />
    <el-card>
      <el-tabs v-model="activeTab">
        <el-tab-pane label="个人信息" name="profile">
          <el-form :model="profileForm" label-width="100px" style="max-width: 500px;">
            <el-form-item label="用户名">
              <el-input v-model="profileForm.username" disabled />
            </el-form-item>
            <el-form-item label="邮箱">
              <el-input v-model="profileForm.email" />
            </el-form-item>
            <el-form-item>
              <el-button type="primary">保存</el-button>
            </el-form-item>
          </el-form>
        </el-tab-pane>
        <el-tab-pane label="修改密码" name="password">
          <el-form :model="passwordForm" label-width="100px" style="max-width: 500px;">
            <el-form-item label="当前密码">
              <el-input v-model="passwordForm.oldPassword" type="password" />
            </el-form-item>
            <el-form-item label="新密码">
              <el-input v-model="passwordForm.newPassword" type="password" />
            </el-form-item>
            <el-form-item label="确认密码">
              <el-input v-model="passwordForm.confirmPassword" type="password" />
            </el-form-item>
            <el-form-item>
              <el-button type="primary">修改密码</el-button>
            </el-form-item>
          </el-form>
        </el-tab-pane>
      </el-tabs>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import PageHeader from '@/components/common/PageHeader.vue'

const activeTab = ref('profile')

const profileForm = reactive({
  username: '',
  email: ''
})

const passwordForm = reactive({
  oldPassword: '',
  newPassword: '',
  confirmPassword: ''
})
</script>

<style scoped>
.settings-view {
  padding: 20px;
}
</style>
