<template>
  <div class="share-page-form-view">
    <PageHeader
      :title="isEditMode ? '编辑分享页' : '创建分享页'"
      :show-back="true"
      @back="handleBack"
    >
      <template #description>
        {{ isEditMode ? '修改分享页信息和内容' : '创建新的分享页面' }}
      </template>
    </PageHeader>

    <LoadingOverlay :loading="loading" text="加载分享页详情..." />

    <div v-if="!loading" class="form-container">
      <el-form
        ref="formRef"
        :model="formData"
        :rules="formRules"
        label-width="120px"
        label-position="right"
      >
        <el-card class="form-section" shadow="never">
          <template #header>
            <div class="section-header">
              <el-icon :size="18"><Document /></el-icon>
              <span>基本信息</span>
            </div>
          </template>

          <!-- 标题 -->
          <el-form-item label="标题" prop="title">
            <el-input
              v-model="formData.title"
              placeholder="请输入分享页标题"
              maxlength="100"
              show-word-limit
              clearable
              @input="handleTitleChange"
            />
            <div class="field-hint">
              分享页的标题，将显示在页面顶部
            </div>
          </el-form-item>

          <!-- Slug -->
          <el-form-item label="Slug" prop="slug">
            <el-input
              v-model="formData.slug"
              placeholder="自动生成或手动输入"
              maxlength="50"
              clearable
            >
              <template #append>
                <el-button :icon="Refresh" @click="generateSlug">
                  自动生成
                </el-button>
              </template>
            </el-input>
            <div class="field-hint">
              分享页的唯一标识，用于生成访问链接：{{ getShareUrl() }}
            </div>
          </el-form-item>

          <!-- 描述 -->
          <el-form-item label="描述" prop="description">
            <el-input
              v-model="formData.description"
              type="textarea"
              :rows="3"
              placeholder="请输入分享页描述（可选）"
              maxlength="500"
              show-word-limit
            />
          </el-form-item>
        </el-card>

        <el-card class="form-section" shadow="never">
          <template #header>
            <div class="section-header">
              <el-icon :size="18"><Edit /></el-icon>
              <span>页面内容</span>
            </div>
          </template>

          <!-- HTML 编辑器 -->
          <el-form-item label="HTML 内容" prop="html_content">
            <HtmlEditor
              v-model="formData.html_content"
              :height="400"
              @change="handleContentChange"
            />
            <div class="field-hint">
              自定义 HTML 内容，支持完整的 HTML/CSS/JS 代码
            </div>
          </el-form-item>

          <!-- 预览按钮 -->
          <el-form-item label=" ">
            <el-button :icon="View" @click="handlePreview">
              预览效果
            </el-button>
          </el-form-item>
        </el-card>

        <el-card class="form-section" shadow="never">
          <template #header>
            <div class="section-header">
              <el-icon :size="18"><Lock /></el-icon>
              <span>访问控制</span>
            </div>
          </template>

          <!-- 密码保护 -->
          <el-form-item label="密码保护">
            <el-switch
              v-model="formData.password_protected"
              @change="handlePasswordProtectedChange"
            />
            <span class="switch-label">启用密码保护</span>
          </el-form-item>

          <el-form-item
            v-if="formData.password_protected"
            label="访问密码"
            prop="password"
          >
            <el-input
              v-model="formData.password"
              type="password"
              placeholder="请输入访问密码（至少 6 位）"
              show-password
              clearable
            />
          </el-form-item>

          <!-- IP 白名单 -->
          <el-form-item label="IP 白名单">
            <el-switch
              v-model="ipWhitelistEnabled"
              @change="handleIpWhitelistChange"
            />
            <span class="switch-label">启用 IP 白名单</span>
          </el-form-item>

          <el-form-item
            v-if="ipWhitelistEnabled"
            label="IP 地址"
            prop="ip_whitelist"
          >
            <el-select
              v-model="formData.ip_whitelist"
              multiple
              filterable
              allow-create
              placeholder="请输入 IP 地址，支持 CIDR 格式"
              style="width: 100%"
            >
              <el-option
                v-for="ip in commonIps"
                :key="ip"
                :label="ip"
                :value="ip"
              />
            </el-select>
            <div class="field-hint">
              支持单个 IP（192.168.1.1）或 CIDR 格式（192.168.1.0/24）
            </div>
          </el-form-item>

          <!-- 过期时间 -->
          <el-form-item label="限时访问">
            <el-switch
              v-model="expireEnabled"
              @change="handleExpireChange"
            />
            <span class="switch-label">启用限时访问</span>
          </el-form-item>

          <el-form-item
            v-if="expireEnabled"
            label="过期时间"
            prop="expire_at"
          >
            <el-date-picker
              v-model="formData.expire_at"
              type="datetime"
              placeholder="选择过期时间"
              :disabled-date="disabledDate"
              format="YYYY-MM-DD HH:mm:ss"
              value-format="YYYY-MM-DD HH:mm:ss"
            />
          </el-form-item>
        </el-card>

        <el-card class="form-section" shadow="never">
          <template #header>
            <div class="section-header">
              <el-icon :size="18"><Setting /></el-icon>
              <span>其他设置</span>
            </div>
          </template>

          <!-- 状态 -->
          <el-form-item label="状态">
            <el-radio-group v-model="formData.status">
              <el-radio value="active">启用</el-radio>
              <el-radio value="inactive">禁用</el-radio>
            </el-radio-group>
            <div class="field-hint">
              禁用后，访问者将无法访问该分享页
            </div>
          </el-form-item>

          <!-- 显示模式 -->
          <el-form-item label="显示模式">
            <el-radio-group v-model="formData.display_mode">
              <el-radio value="list">列表模式</el-radio>
              <el-radio value="card">卡片模式</el-radio>
              <el-radio value="custom">自定义模式</el-radio>
            </el-radio-group>
          </el-form-item>

          <!-- 排序权重 -->
          <el-form-item label="排序权重" prop="sort_order">
            <el-input-number
              v-model="formData.sort_order"
              :min="0"
              :max="999"
              :step="1"
            />
            <div class="field-hint">
              数字越大，排序越靠前（0-999）
            </div>
          </el-form-item>
        </el-card>

        <!-- 操作按钮 -->
        <div class="form-actions">
          <el-button
            type="primary"
            :loading="submitLoading"
            :icon="Check"
            size="large"
            @click="handleSubmit"
          >
            {{ isEditMode ? '保存修改' : '创建分享页' }}
          </el-button>
          <el-button
            :icon="Close"
            size="large"
            @click="handleCancel"
          >
            取消
          </el-button>
          <el-button
            v-if="isEditMode"
            :icon="Refresh"
            size="large"
            @click="handleReset"
          >
            重置表单
          </el-button>
        </div>
      </el-form>
    </div>

    <!-- 预览对话框 -->
    <el-dialog
      v-model="previewDialogVisible"
      title="预览效果"
      width="90%"
      :close-on-click-modal="false"
      fullscreen
    >
      <div class="preview-container">
        <iframe
          ref="previewIframe"
          class="preview-iframe"
          sandbox="allow-scripts"
          :srcdoc="formData.html_content"
        />
      </div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage, ElMessageBox, type FormInstance, type FormRules } from 'element-plus'
import {
  Document,
  Edit,
  Lock,
  Setting,
  View,
  Check,
  Close,
  Refresh
} from '@element-plus/icons-vue'
import PageHeader from '@/components/common/PageHeader.vue'
import LoadingOverlay from '@/components/common/LoadingOverlay.vue'
import HtmlEditor from '@/components/user/HtmlEditor.vue'

// ==================== 类型定义 ====================

interface SharePageFormData {
  title: string
  slug: string
  description: string
  html_content: string
  password_protected: boolean
  password: string
  ip_whitelist: string[]
  expire_at: string
  status: 'active' | 'inactive'
  display_mode: 'list' | 'card' | 'custom'
  sort_order: number
}

// ==================== 路由和状态 ====================

const router = useRouter()
const route = useRoute()

// 编辑模式判断
const isEditMode = computed(() => !!route.params.id)
const sharePageId = computed(() => route.params.id as string)

// ==================== 表单相关 ====================

const formRef = ref<FormInstance>()
const loading = ref(false)
const submitLoading = ref(false)
const previewDialogVisible = ref(false)
const previewIframe = ref<HTMLIFrameElement>()

// 辅助状态
const ipWhitelistEnabled = ref(false)
const expireEnabled = ref(false)

// 表单数据
const formData = reactive<SharePageFormData>({
  title: '',
  slug: '',
  description: '',
  html_content: '',
  password_protected: false,
  password: '',
  ip_whitelist: [],
  expire_at: '',
  status: 'active',
  display_mode: 'list',
  sort_order: 0
})

// 常用 IP 列表
const commonIps = ref<string[]>([
  '127.0.0.1',
  '192.168.1.0/24',
  '10.0.0.0/8'
])

// 表单验证规则
const formRules: FormRules = {
  title: [
    { required: true, message: '请输入标题', trigger: 'blur' },
    { min: 2, max: 100, message: '长度在 2 到 100 个字符', trigger: 'blur' }
  ],
  slug: [
    { required: true, message: '请输入或生成 Slug', trigger: 'blur' },
    { min: 2, max: 50, message: '长度在 2 到 50 个字符', trigger: 'blur' },
    { pattern: /^[a-z0-9-]+$/, message: '只能包含小写字母、数字和连字符', trigger: 'blur' }
  ],
  html_content: [
    { required: true, message: '请输入 HTML 内容', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请输入访问密码', trigger: 'blur' },
    { min: 6, max: 32, message: '密码长度在 6 到 32 个字符', trigger: 'blur' }
  ],
  sort_order: [
    { type: 'number', min: 0, max: 999, message: '排序权重在 0 到 999 之间', trigger: 'blur' }
  ]
}

// ==================== 工具方法 ====================

/**
 * 生成 Slug
 */
function generateSlug() {
  if (!formData.title) {
    ElMessage.warning('请先输入标题')
    return
  }

  // 简单的 Slug 生成逻辑：转小写、替换空格为连字符、移除特殊字符
  let slug = formData.title
    .toLowerCase()
    .trim()
    .replace(/\s+/g, '-')
    .replace(/[^a-z0-9-]/g, '')
    .replace(/-+/g, '-')
    .replace(/^-|-$/g, '')

  // 如果是中文等非 ASCII 字符，使用拼音转换（简化版：使用时间戳）
  if (!/^[a-z0-9-]+$/.test(slug)) {
    slug = 'share-' + Date.now()
  }

  formData.slug = slug
  ElMessage.success('Slug 已生成')
}

/**
 * 获取分享 URL
 */
function getShareUrl(): string {
  if (!formData.slug) {
    return 'https://example.com/s/[slug]'
  }
  return `https://example.com/s/${formData.slug}`
}

/**
 * 禁用过去的日期
 */
function disabledDate(time: Date): boolean {
  return time.getTime() < Date.now()
}

/**
 * 标题变化处理
 */
function handleTitleChange() {
  // 如果是新建模式且 slug 为空，自动生成
  if (!isEditMode.value && !formData.slug && formData.title) {
    // 延迟生成，避免频繁触发
    setTimeout(() => {
      if (formData.title && !formData.slug) {
        generateSlug()
      }
    }, 1000)
  }
}

/**
 * 内容变化处理
 */
function handleContentChange(content: string) {
  formData.html_content = content
}

/**
 * 密码保护变化
 */
function handlePasswordProtectedChange(value: boolean) {
  if (!value) {
    formData.password = ''
  }
}

/**
 * IP 白名单变化
 */
function handleIpWhitelistChange(value: boolean) {
  if (!value) {
    formData.ip_whitelist = []
  }
}

/**
 * 过期时间变化
 */
function handleExpireChange(value: boolean) {
  if (!value) {
    formData.expire_at = ''
  }
}

/**
 * 预览效果
 */
function handlePreview() {
  if (!formData.html_content) {
    ElMessage.warning('请先输入 HTML 内容')
    return
  }

  previewDialogVisible.value = true
}

/**
 * 加载分享页详情（编辑模式）
 */
async function loadSharePageDetail() {
  if (!isEditMode.value) return

  loading.value = true

  try {
    // TODO: 调用 API 获取分享页详情
    // const { data } = await shareApi.getDetail(sharePageId.value)

    // 模拟 API 调用
    await new Promise(resolve => setTimeout(resolve, 500))

    // 模拟数据
    const mockData = {
      title: '官方 Apple ID 分享',
      slug: 'official-apple-id',
      description: '这是一个测试分享页',
      html_content: '<h1>Hello World</h1><p>This is a test page.</p>',
      password_protected: true,
      password: 'test123',
      ip_whitelist: ['192.168.1.100', '10.0.0.0/8'],
      expire_at: '2025-12-31 23:59:59',
      status: 'active',
      display_mode: 'list',
      sort_order: 10
    }

    // 填充表单数据
    Object.assign(formData, mockData)

    // 设置辅助状态
    ipWhitelistEnabled.value = mockData.ip_whitelist.length > 0
    expireEnabled.value = !!mockData.expire_at
  } catch (error: any) {
    console.error('加载分享页详情失败:', error)
    ElMessage.error(error.message || '加载失败，请稍后重试')
    // 加载失败，返回列表页
    router.push('/share-pages')
  } finally {
    loading.value = false
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
    // 准备提交数据
    const submitData = {
      ...formData,
      ip_whitelist: ipWhitelistEnabled.value ? formData.ip_whitelist : [],
      expire_at: expireEnabled.value ? formData.expire_at : null,
      password: formData.password_protected ? formData.password : null
    }

    if (isEditMode.value) {
      // TODO: 调用 API 更新分享页
      // await shareApi.update(sharePageId.value, submitData)

      // 模拟 API 调用
      await new Promise(resolve => setTimeout(resolve, 1000))

      ElMessage.success('分享页修改成功')
    } else {
      // TODO: 调用 API 创建分享页
      // await shareApi.create(submitData)

      // 模拟 API 调用
      await new Promise(resolve => setTimeout(resolve, 1000))

      ElMessage.success('分享页创建成功')
    }

    // 返回列表页
    router.push('/share-pages')
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
  const hasChanges = formData.title || formData.slug || formData.html_content

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
  router.push('/share-pages')
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
      // 编辑模式：重新加载分享页详情
      await loadSharePageDetail()
    } else {
      // 添加模式：清空表单
      formRef.value?.resetFields()
      ipWhitelistEnabled.value = false
      expireEnabled.value = false
    }

    ElMessage.success('表单已重置')
  } catch {
    // 用户取消
  }
}

// ==================== 生命周期 ====================

onMounted(() => {
  // 编辑模式：加载分享页详情
  if (isEditMode.value) {
    loadSharePageDetail()
  }
})
</script>

<style scoped lang="scss">
.share-page-form-view {
  padding: 20px;
  min-height: 100vh;
  background-color: #f5f7fa;
}

.form-container {
  max-width: 1200px;
  margin: 0 auto;
}

.form-section {
  margin-bottom: 20px;
  border-radius: 8px;

  :deep(.el-card__header) {
    background-color: #fafafa;
    border-bottom: 1px solid #e8e8e8;
  }
}

.section-header {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 16px;
  font-weight: 500;
  color: #303133;
}

.field-hint {
  font-size: 13px;
  color: #909399;
  margin-top: 5px;
  line-height: 1.5;
}

.switch-label {
  margin-left: 10px;
  font-size: 14px;
  color: #606266;
}

.form-actions {
  display: flex;
  justify-content: center;
  gap: 15px;
  margin-top: 30px;
  padding: 20px;
  background-color: white;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
}

/* 预览对话框 */
.preview-container {
  width: 100%;
  height: calc(100vh - 120px);
  background-color: white;
}

.preview-iframe {
  width: 100%;
  height: 100%;
  border: 1px solid #dcdfe6;
  border-radius: 4px;
}

/* 响应式设计 */
@media screen and (max-width: 768px) {
  .share-page-form-view {
    padding: 10px;
  }

  .form-container {
    padding: 0;
  }

  :deep(.el-form-item__label) {
    text-align: left;
  }

  .form-actions {
    flex-direction: column;

    .el-button {
      width: 100%;
    }
  }
}

@media screen and (max-width: 480px) {
  .share-page-form-view {
    padding: 5px;
  }

  .field-hint {
    font-size: 12px;
  }

  .section-header {
    font-size: 15px;
  }
}
</style>
