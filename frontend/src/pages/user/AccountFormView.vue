<template>
  <div class="account-form-view">
    <PageHeader
      :title="isEditMode ? '编辑账号' : '添加账号'"
      :show-back="true"
      @back="handleBack"
    >
      <template #description>
        {{ isEditMode ? '修改账号信息' : '添加新的 Apple ID 账号' }}
      </template>
    </PageHeader>

    <div class="form-container">
      <el-card class="form-card">
        <el-form
          ref="formRef"
          :model="formData"
          :rules="formRules"
          label-width="120px"
          label-position="right"
        >
          <!-- Apple ID -->
          <el-form-item label="Apple ID" prop="apple_id">
            <el-input
              v-model="formData.apple_id"
              placeholder="请输入 Apple ID（邮箱格式）"
              :prefix-icon="Message"
              clearable
            >
              <template #append>
                <el-button :icon="Check" @click="checkAppleIdAvailability">
                  检查可用性
                </el-button>
              </template>
            </el-input>
            <div class="field-hint">
              请输入有效的 Apple ID 邮箱地址
            </div>
          </el-form-item>

          <!-- 密码 -->
          <el-form-item label="密码" prop="password">
            <el-input
              v-model="formData.password"
              type="password"
              placeholder="请输入密码（至少 6 位）"
              :prefix-icon="Lock"
              show-password
              clearable
            >
              <template #append>
                <el-button :icon="Refresh" @click="generateRandomPassword">
                  生成密码
                </el-button>
              </template>
            </el-input>
            <div class="field-hint">
              密码长度至少 6 位，建议使用复杂密码
            </div>
          </el-form-item>

          <!-- 密码强度提示 -->
          <el-form-item label=" " v-if="formData.password">
            <div class="password-strength">
              <div class="strength-label">密码强度：</div>
              <div class="strength-bar">
                <div
                  class="strength-progress"
                  :class="passwordStrength.level"
                  :style="{ width: passwordStrength.percentage + '%' }"
                ></div>
              </div>
              <div class="strength-text" :class="passwordStrength.level">
                {{ passwordStrength.text }}
              </div>
            </div>
          </el-form-item>

          <!-- 安全问题 -->
          <el-form-item label="安全问题" prop="security_questions">
            <el-input
              v-model="formData.security_questions"
              type="textarea"
              :rows="4"
              placeholder="请输入安全问题及答案（可选）&#10;格式示例：&#10;Q1: 你最喜欢的颜色？ A1: 蓝色&#10;Q2: 你的宠物名字？ A2: 小白"
            />
            <div class="field-hint">
              安全问题和答案，可以帮助您在忘记密码时恢复账号
            </div>
          </el-form-item>

          <!-- 恢复密钥 -->
          <el-form-item label="恢复密钥" prop="recovery_key">
            <el-input
              v-model="formData.recovery_key"
              placeholder="请输入恢复密钥（可选）"
              :prefix-icon="Key"
              clearable
            />
            <div class="field-hint">
              Apple ID 恢复密钥，通常是一串随机字符
            </div>
          </el-form-item>

          <!-- 备注 -->
          <el-form-item label="备注" prop="note">
            <el-input
              v-model="formData.note"
              type="textarea"
              :rows="3"
              placeholder="请输入备注信息（可选）"
              maxlength="500"
              show-word-limit
            />
            <div class="field-hint">
              可以添加任何您认为有用的备注信息
            </div>
          </el-form-item>

          <!-- 操作按钮 -->
          <el-form-item label=" ">
            <div class="form-actions">
              <el-button
                type="primary"
                :loading="submitLoading"
                :icon="Check"
                @click="handleSubmit"
                size="large"
              >
                {{ isEditMode ? '保存修改' : '添加账号' }}
              </el-button>
              <el-button
                :icon="Close"
                @click="handleCancel"
                size="large"
              >
                取消
              </el-button>
              <el-button
                v-if="isEditMode"
                :icon="Refresh"
                @click="handleReset"
                size="large"
              >
                重置表单
              </el-button>
            </div>
          </el-form-item>
        </el-form>
      </el-card>

      <!-- 操作提示卡片 -->
      <el-card class="tips-card">
        <template #header>
          <div class="card-header">
            <el-icon :size="18"><InfoFilled /></el-icon>
            <span>操作提示</span>
          </div>
        </template>
        <ul class="tips-list">
          <li>
            <el-icon><Check /></el-icon>
            <span>Apple ID 必须是有效的邮箱地址</span>
          </li>
          <li>
            <el-icon><Check /></el-icon>
            <span>密码长度至少 6 位，建议使用复杂密码以提高安全性</span>
          </li>
          <li>
            <el-icon><Check /></el-icon>
            <span>安全问题和恢复密钥可以帮助您在忘记密码时恢复账号</span>
          </li>
          <li>
            <el-icon><Check /></el-icon>
            <span>备注信息仅用于您自己管理账号，不会被其他人看到</span>
          </li>
          <li>
            <el-icon><Check /></el-icon>
            <span>保存后，系统会自动检测账号状态</span>
          </li>
        </ul>
      </el-card>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage, ElMessageBox, type FormInstance, type FormRules } from 'element-plus'
import {
  Message,
  Lock,
  Key,
  Check,
  Close,
  Refresh,
  InfoFilled
} from '@element-plus/icons-vue'
import PageHeader from '@/components/common/PageHeader.vue'

// ==================== 类型定义 ====================

interface AccountFormData {
  apple_id: string
  password: string
  security_questions: string
  recovery_key: string
  note: string
}

interface PasswordStrength {
  level: 'weak' | 'medium' | 'strong'
  percentage: number
  text: string
}

// ==================== 路由和状态 ====================

const router = useRouter()
const route = useRoute()

// 编辑模式判断
const isEditMode = computed(() => !!route.params.id)
const accountId = computed(() => route.params.id as string)

// ==================== 表单相关 ====================

const formRef = ref<FormInstance>()
const submitLoading = ref(false)

// 表单数据
const formData = reactive<AccountFormData>({
  apple_id: '',
  password: '',
  security_questions: '',
  recovery_key: '',
  note: ''
})

// 表单验证规则
const formRules: FormRules = {
  apple_id: [
    { required: true, message: '请输入 Apple ID', trigger: 'blur' },
    { type: 'email', message: '请输入有效的邮箱地址', trigger: 'blur' },
    { min: 3, max: 100, message: '长度在 3 到 100 个字符', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, max: 32, message: '密码长度在 6 到 32 个字符', trigger: 'blur' }
  ],
  security_questions: [
    { max: 1000, message: '安全问题长度不能超过 1000 个字符', trigger: 'blur' }
  ],
  recovery_key: [
    { max: 100, message: '恢复密钥长度不能超过 100 个字符', trigger: 'blur' }
  ],
  note: [
    { max: 500, message: '备注长度不能超过 500 个字符', trigger: 'blur' }
  ]
}

// ==================== 密码强度计算 ====================

const passwordStrength = computed<PasswordStrength>(() => {
  const password = formData.password
  if (!password) {
    return { level: 'weak', percentage: 0, text: '' }
  }

  let strength = 0

  // 长度评分（最多 30 分）
  if (password.length >= 6) strength += 10
  if (password.length >= 10) strength += 10
  if (password.length >= 14) strength += 10

  // 包含小写字母（10 分）
  if (/[a-z]/.test(password)) strength += 10

  // 包含大写字母（10 分）
  if (/[A-Z]/.test(password)) strength += 10

  // 包含数字（10 分）
  if (/\d/.test(password)) strength += 10

  // 包含特殊字符（20 分）
  if (/[!@#$%^&*()_+\-=\[\]{};':"\\|,.<>\/?]/.test(password)) strength += 20

  // 字符种类多样性（20 分）
  const charTypes = [
    /[a-z]/.test(password),
    /[A-Z]/.test(password),
    /\d/.test(password),
    /[^a-zA-Z0-9]/.test(password)
  ].filter(Boolean).length
  if (charTypes >= 3) strength += 10
  if (charTypes >= 4) strength += 10

  // 根据评分返回等级
  if (strength < 40) {
    return { level: 'weak', percentage: strength, text: '弱' }
  } else if (strength < 70) {
    return { level: 'medium', percentage: strength, text: '中等' }
  } else {
    return { level: 'strong', percentage: Math.min(strength, 100), text: '强' }
  }
})

// ==================== 工具方法 ====================

/**
 * 生成随机密码
 */
function generateRandomPassword() {
  const lowercase = 'abcdefghijklmnopqrstuvwxyz'
  const uppercase = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
  const numbers = '0123456789'
  const special = '!@#$%^&*'
  const all = lowercase + uppercase + numbers + special

  let password = ''
  // 确保每种字符类型至少有一个
  password += lowercase[Math.floor(Math.random() * lowercase.length)]
  password += uppercase[Math.floor(Math.random() * uppercase.length)]
  password += numbers[Math.floor(Math.random() * numbers.length)]
  password += special[Math.floor(Math.random() * special.length)]

  // 剩余字符随机生成
  for (let i = password.length; i < 12; i++) {
    password += all[Math.floor(Math.random() * all.length)]
  }

  // 打乱密码
  password = password.split('').sort(() => Math.random() - 0.5).join('')

  formData.password = password
  ElMessage.success('已生成随机密码')
}

/**
 * 检查 Apple ID 可用性
 */
async function checkAppleIdAvailability() {
  if (!formData.apple_id) {
    ElMessage.warning('请先输入 Apple ID')
    return
  }

  // 验证邮箱格式
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
  if (!emailRegex.test(formData.apple_id)) {
    ElMessage.warning('请输入有效的邮箱地址')
    return
  }

  try {
    // TODO: 调用 API 检查 Apple ID 是否已存在
    // const { data } = await accountApi.checkAvailability({ apple_id: formData.apple_id })

    // 模拟 API 调用
    await new Promise(resolve => setTimeout(resolve, 500))

    // 模拟检查结果（编辑模式或随机结果）
    const isAvailable = isEditMode.value || Math.random() > 0.3

    if (isAvailable) {
      ElMessage.success('该 Apple ID 可用')
    } else {
      ElMessage.warning('该 Apple ID 已存在')
    }
  } catch (error: any) {
    console.error('检查 Apple ID 可用性失败:', error)
    ElMessage.error(error.message || '检查失败，请稍后重试')
  }
}

/**
 * 加载账号详情（编辑模式）
 */
async function loadAccountDetail() {
  if (!isEditMode.value) return

  submitLoading.value = true

  try {
    // TODO: 调用 API 获取账号详情
    // const { data } = await accountApi.getDetail(accountId.value)

    // 模拟 API 调用
    await new Promise(resolve => setTimeout(resolve, 500))

    // 模拟账号数据
    const mockData = {
      apple_id: 'test@example.com',
      password: 'Test1234!',
      security_questions: 'Q1: 你最喜欢的颜色？ A1: 蓝色\nQ2: 你的宠物名字？ A2: 小白',
      recovery_key: 'ABCD-EFGH-IJKL-MNOP',
      note: '测试账号，请勿删除'
    }

    // 填充表单数据
    Object.assign(formData, mockData)
  } catch (error: any) {
    console.error('加载账号详情失败:', error)
    ElMessage.error(error.message || '加载失败，请稍后重试')
    // 加载失败，返回列表页
    router.push('/accounts')
  } finally {
    submitLoading.value = false
  }
}

// ==================== 表单操作 ====================

/**
 * 提交表单
 */
async function handleSubmit() {
  if (!formRef.value) return

  // 验证表单
  try {
    await formRef.value.validate()
  } catch (error) {
    ElMessage.warning('请填写必填项并检查格式')
    return
  }

  submitLoading.value = true

  try {
    if (isEditMode.value) {
      // TODO: 调用 API 更新账号
      // await accountApi.update(accountId.value, formData)

      // 模拟 API 调用
      await new Promise(resolve => setTimeout(resolve, 1000))

      ElMessage.success('账号修改成功')
    } else {
      // TODO: 调用 API 创建账号
      // await accountApi.create(formData)

      // 模拟 API 调用
      await new Promise(resolve => setTimeout(resolve, 1000))

      ElMessage.success('账号添加成功')
    }

    // 返回列表页
    router.push('/accounts')
  } catch (error: any) {
    console.error('提交失败:', error)
    ElMessage.error(error.message || '操作失败，请稍后重试')
  } finally {
    submitLoading.value = false
  }
}

/**
 * 取消操作
 */
async function handleCancel() {
  // 检查表单是否有修改
  const hasChanges = formData.apple_id || formData.password ||
                     formData.security_questions || formData.recovery_key ||
                     formData.note

  if (hasChanges) {
    try {
      await ElMessageBox.confirm(
        '表单内容尚未保存，确定要取消吗？',
        '提示',
        {
          confirmButtonText: '确定',
          cancelButtonText: '继续编辑',
          type: 'warning'
        }
      )
      handleBack()
    } catch {
      // 用户取消
    }
  } else {
    handleBack()
  }
}

/**
 * 返回上一页
 */
function handleBack() {
  router.push('/accounts')
}

/**
 * 重置表单
 */
async function handleReset() {
  try {
    await ElMessageBox.confirm(
      '确定要重置表单吗？此操作将恢复到初始状态。',
      '提示',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )

    if (isEditMode.value) {
      // 编辑模式：重新加载账号详情
      await loadAccountDetail()
    } else {
      // 添加模式：清空表单
      formRef.value?.resetFields()
    }

    ElMessage.success('表单已重置')
  } catch {
    // 用户取消
  }
}

// ==================== 生命周期 ====================

onMounted(() => {
  // 编辑模式：加载账号详情
  if (isEditMode.value) {
    loadAccountDetail()
  }
})
</script>

<style scoped lang="scss">
.account-form-view {
  padding: 20px;
  min-height: 100vh;
  background-color: #f5f7fa;
}

.form-container {
  display: grid;
  grid-template-columns: 1fr 350px;
  gap: 20px;
  max-width: 1400px;
  margin: 0 auto;
}

.form-card {
  .el-form {
    max-width: 800px;
    margin: 0 auto;
    padding: 20px 0;
  }
}

.field-hint {
  font-size: 13px;
  color: #909399;
  margin-top: 5px;
  line-height: 1.5;
}

/* 密码强度指示器 */
.password-strength {
  display: flex;
  align-items: center;
  gap: 12px;
  width: 100%;

  .strength-label {
    font-size: 14px;
    color: #606266;
    white-space: nowrap;
  }

  .strength-bar {
    flex: 1;
    height: 8px;
    background-color: #e4e7ed;
    border-radius: 4px;
    overflow: hidden;
  }

  .strength-progress {
    height: 100%;
    border-radius: 4px;
    transition: all 0.3s ease;

    &.weak {
      background: linear-gradient(90deg, #f56c6c 0%, #ff7a7a 100%);
    }

    &.medium {
      background: linear-gradient(90deg, #e6a23c 0%, #f5b042 100%);
    }

    &.strong {
      background: linear-gradient(90deg, #67c23a 0%, #85ce61 100%);
    }
  }

  .strength-text {
    font-size: 14px;
    font-weight: 500;
    white-space: nowrap;

    &.weak {
      color: #f56c6c;
    }

    &.medium {
      color: #e6a23c;
    }

    &.strong {
      color: #67c23a;
    }
  }
}

/* 表单操作按钮 */
.form-actions {
  display: flex;
  gap: 12px;
}

/* 提示卡片 */
.tips-card {
  height: fit-content;

  .card-header {
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 16px;
    font-weight: 500;
    color: #303133;
  }

  .tips-list {
    list-style: none;
    padding: 0;
    margin: 0;

    li {
      display: flex;
      align-items: flex-start;
      gap: 10px;
      padding: 12px 0;
      font-size: 14px;
      color: #606266;
      line-height: 1.6;
      border-bottom: 1px solid #f0f0f0;

      &:last-child {
        border-bottom: none;
      }

      .el-icon {
        color: #67c23a;
        font-size: 16px;
        margin-top: 2px;
        flex-shrink: 0;
      }

      span {
        flex: 1;
      }
    }
  }
}

/* 响应式设计 */
@media screen and (max-width: 1200px) {
  .form-container {
    grid-template-columns: 1fr;
  }

  .tips-card {
    order: -1;
  }
}

@media screen and (max-width: 768px) {
  .account-form-view {
    padding: 10px;
  }

  .form-card {
    .el-form {
      padding: 10px 0;
    }

    :deep(.el-form-item__label) {
      text-align: left;
    }
  }

  .form-actions {
    flex-direction: column;

    .el-button {
      width: 100%;
    }
  }

  .password-strength {
    flex-wrap: wrap;

    .strength-label {
      width: 100%;
      margin-bottom: 5px;
    }

    .strength-bar {
      flex: 1;
      min-width: 150px;
    }
  }
}

@media screen and (max-width: 480px) {
  .account-form-view {
    padding: 5px;
  }

  .field-hint {
    font-size: 12px;
  }

  .tips-list li {
    font-size: 13px;
  }
}
</style>
