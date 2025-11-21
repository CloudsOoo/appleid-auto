<template>
  <div class="account-import-view">
    <PageHeader
      title="批量导入账号"
      :show-back="true"
      @back="handleBack"
    >
      <template #description>
        支持批量导入 Apple ID 账号，支持 CSV、TXT、Excel 格式
      </template>
    </PageHeader>

    <div class="import-container">
      <!-- 导入步骤 -->
      <el-card class="steps-card">
        <el-steps :active="currentStep" finish-status="success" align-center>
          <el-step title="上传文件" :icon="Upload" />
          <el-step title="数据预览" :icon="View" />
          <el-step title="开始导入" :icon="Upload" />
          <el-step title="导入完成" :icon="Check" />
        </el-steps>
      </el-card>

      <!-- 步骤 1: 上传文件 -->
      <el-card v-show="currentStep === 0" class="content-card">
        <template #header>
          <div class="card-header">
            <span>步骤 1: 上传文件</span>
          </div>
        </template>

        <div class="upload-section">
          <el-upload
            ref="uploadRef"
            class="upload-dragger"
            drag
            :action="uploadAction"
            :before-upload="handleBeforeUpload"
            :on-success="handleUploadSuccess"
            :on-error="handleUploadError"
            :auto-upload="false"
            :limit="1"
            :accept="acceptFileTypes"
            :file-list="fileList"
            :on-change="handleFileChange"
            :on-remove="handleFileRemove"
          >
            <el-icon class="el-icon--upload"><UploadFilled /></el-icon>
            <div class="el-upload__text">
              将文件拖到此处，或<em>点击上传</em>
            </div>
            <template #tip>
              <div class="el-upload__tip">
                支持 .csv / .txt / .xlsx / .xls 格式，文件大小不超过 10MB
              </div>
            </template>
          </el-upload>

          <div class="upload-actions" v-if="fileList.length > 0">
            <el-button type="primary" :icon="Right" @click="handleParseFile">
              下一步：数据预览
            </el-button>
          </div>
        </div>

        <!-- 格式说明 -->
        <el-divider content-position="left">文件格式说明</el-divider>

        <el-collapse v-model="activeFormats">
          <el-collapse-item title="CSV / TXT 格式" name="csv">
            <div class="format-description">
              <p class="format-title">文件格式要求：</p>
              <ul>
                <li>第一行为表头（可选）：<code>Apple ID,密码,安全问题,恢复密钥,备注</code></li>
                <li>每行一个账号，使用逗号分隔字段</li>
                <li>Apple ID 和密码为必填字段</li>
                <li>其他字段可选</li>
              </ul>

              <p class="format-title">示例：</p>
              <pre class="format-example">Apple ID,密码,安全问题,恢复密钥,备注
test1@example.com,Pass1234,Q1:颜色?A1:蓝色,ABCD-1234,测试账号1
test2@example.com,Pass5678,Q1:宠物?A1:小白,EFGH-5678,测试账号2</pre>

              <el-button
                type="primary"
                link
                :icon="Download"
                @click="downloadTemplate('csv')"
              >
                下载 CSV 模板
              </el-button>
            </div>
          </el-collapse-item>

          <el-collapse-item title="Excel 格式" name="excel">
            <div class="format-description">
              <p class="format-title">文件格式要求：</p>
              <ul>
                <li>第一行为表头（必填）：<code>Apple ID | 密码 | 安全问题 | 恢复密钥 | 备注</code></li>
                <li>每行一个账号</li>
                <li>Apple ID 和密码为必填字段</li>
                <li>其他字段可选</li>
              </ul>

              <p class="format-title">表格示例：</p>
              <el-table :data="exampleData" border style="margin: 10px 0;">
                <el-table-column prop="apple_id" label="Apple ID" width="180" />
                <el-table-column prop="password" label="密码" width="120" />
                <el-table-column prop="security_questions" label="安全问题" width="150" />
                <el-table-column prop="recovery_key" label="恢复密钥" width="120" />
                <el-table-column prop="note" label="备注" />
              </el-table>

              <el-button
                type="primary"
                link
                :icon="Download"
                @click="downloadTemplate('excel')"
              >
                下载 Excel 模板
              </el-button>
            </div>
          </el-collapse-item>
        </el-collapse>
      </el-card>

      <!-- 步骤 2: 数据预览 -->
      <el-card v-show="currentStep === 1" class="content-card">
        <template #header>
          <div class="card-header">
            <span>步骤 2: 数据预览</span>
            <div class="header-actions">
              <span class="preview-stats">
                共 <strong>{{ previewData.length }}</strong> 条记录，
                有效 <strong>{{ validCount }}</strong> 条，
                无效 <strong>{{ invalidCount }}</strong> 条
              </span>
            </div>
          </div>
        </template>

        <DataTable
          :data="previewData"
          :columns="previewColumns"
          :loading="parseLoading"
          :show-selection="true"
          :show-index="true"
          :show-pagination="true"
          :show-toolbar="true"
          :show-search="false"
          :show-refresh="false"
          :show-export="false"
          title="数据预览"
          description="请检查导入数据是否正确"
          row-key="index"
          @selection-change="handleSelectionChange"
        >
          <!-- 自定义列：Apple ID -->
          <template #column-apple_id="{ row }">
            <div class="cell-with-status">
              <span>{{ row.apple_id }}</span>
              <el-icon v-if="row.errors && row.errors.includes('apple_id')" color="#f56c6c">
                <WarningFilled />
              </el-icon>
            </div>
          </template>

          <!-- 自定义列：密码 -->
          <template #column-password="{ row }">
            <div class="cell-with-status">
              <span>{{ row.password ? '••••••' : '-' }}</span>
              <el-icon v-if="row.errors && row.errors.includes('password')" color="#f56c6c">
                <WarningFilled />
              </el-icon>
            </div>
          </template>

          <!-- 自定义列：状态 -->
          <template #column-status="{ row }">
            <StatusTag
              :type="row.valid ? 'success' : 'danger'"
              :text="row.valid ? '有效' : '无效'"
            />
          </template>

          <!-- 自定义列：错误信息 -->
          <template #column-error_message="{ row }">
            <el-tooltip
              v-if="row.error_message"
              :content="row.error_message"
              placement="top"
            >
              <el-text type="danger" size="small">{{ row.error_message }}</el-text>
            </el-tooltip>
            <span v-else>-</span>
          </template>
        </DataTable>

        <div class="preview-actions">
          <el-button :icon="Back" @click="currentStep = 0">
            上一步
          </el-button>
          <el-button
            type="primary"
            :icon="Right"
            :disabled="validCount === 0"
            @click="currentStep = 2"
          >
            下一步：开始导入
          </el-button>
        </div>
      </el-card>

      <!-- 步骤 3: 开始导入 -->
      <el-card v-show="currentStep === 2" class="content-card">
        <template #header>
          <div class="card-header">
            <span>步骤 3: 开始导入</span>
          </div>
        </template>

        <div class="import-config">
          <el-form :model="importConfig" label-width="140px">
            <el-form-item label="导入模式">
              <el-radio-group v-model="importConfig.mode">
                <el-radio value="all">导入所有记录（{{ previewData.length }} 条）</el-radio>
                <el-radio value="valid">仅导入有效记录（{{ validCount }} 条）</el-radio>
                <el-radio value="selected">仅导入选中记录（{{ selectedRows.length }} 条）</el-radio>
              </el-radio-group>
            </el-form-item>

            <el-form-item label="重复处理">
              <el-radio-group v-model="importConfig.duplicateHandling">
                <el-radio value="skip">跳过重复记录</el-radio>
                <el-radio value="update">更新重复记录</el-radio>
                <el-radio value="rename">重命名重复记录</el-radio>
              </el-radio-group>
              <div class="form-item-hint">
                如果 Apple ID 已存在，将按照选择的方式处理
              </div>
            </el-form-item>

            <el-form-item label="导入后操作">
              <el-checkbox-group v-model="importConfig.postActions">
                <el-checkbox value="check">自动检测账号状态</el-checkbox>
                <el-checkbox value="notify">完成后发送通知</el-checkbox>
              </el-checkbox-group>
            </el-form-item>
          </el-form>
        </div>

        <el-divider />

        <div class="import-summary">
          <el-alert
            type="info"
            :closable="false"
            show-icon
          >
            <template #title>
              <div class="summary-content">
                <p>即将导入 <strong>{{ getImportCount() }}</strong> 条账号记录</p>
                <p>重复处理策略：<strong>{{ getDuplicateHandlingText() }}</strong></p>
                <p v-if="importConfig.postActions.includes('check')">导入后将自动检测账号状态</p>
              </div>
            </template>
          </el-alert>
        </div>

        <div class="import-actions">
          <el-button :icon="Back" @click="currentStep = 1">
            上一步
          </el-button>
          <el-button
            type="primary"
            :icon="Upload"
            :loading="importLoading"
            @click="handleStartImport"
          >
            开始导入
          </el-button>
        </div>
      </el-card>

      <!-- 步骤 4: 导入完成 -->
      <el-card v-show="currentStep === 3" class="content-card">
        <template #header>
          <div class="card-header">
            <span>步骤 4: 导入完成</span>
          </div>
        </template>

        <el-result
          :icon="importResult.success ? 'success' : 'error'"
          :title="importResult.title"
          :sub-title="importResult.subTitle"
        >
          <template #extra>
            <div class="result-stats">
              <div class="stat-item stat-item--success">
                <div class="stat-label">成功</div>
                <div class="stat-value">{{ importResult.successCount }}</div>
              </div>
              <div class="stat-item stat-item--error">
                <div class="stat-label">失败</div>
                <div class="stat-value">{{ importResult.failedCount }}</div>
              </div>
              <div class="stat-item stat-item--skip">
                <div class="stat-label">跳过</div>
                <div class="stat-value">{{ importResult.skippedCount }}</div>
              </div>
            </div>

            <!-- 失败记录列表 -->
            <div v-if="importResult.failedRecords.length > 0" class="failed-records">
              <el-divider content-position="left">失败记录</el-divider>
              <el-table
                :data="importResult.failedRecords"
                border
                max-height="300"
              >
                <el-table-column type="index" label="#" width="50" />
                <el-table-column prop="apple_id" label="Apple ID" width="200" />
                <el-table-column prop="error" label="失败原因" />
              </el-table>
            </div>

            <div class="result-actions">
              <el-button type="primary" @click="handleViewAccounts">
                查看账号列表
              </el-button>
              <el-button @click="handleResetImport">
                继续导入
              </el-button>
            </div>
          </template>
        </el-result>
      </el-card>

      <!-- 导入进度对话框 -->
      <el-dialog
        v-model="progressDialogVisible"
        title="正在导入"
        :close-on-click-modal="false"
        :close-on-press-escape="false"
        :show-close="false"
        width="500px"
      >
        <div class="progress-content">
          <el-progress
            :percentage="importProgress"
            :status="importProgress === 100 ? 'success' : undefined"
          />
          <p class="progress-text">
            已导入 {{ importedCount }} / {{ totalImportCount }} 条记录
          </p>
          <p class="progress-hint">
            请勿关闭此窗口，导入过程可能需要几分钟...
          </p>
        </div>
      </el-dialog>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed } from 'vue'
import { useRouter } from 'vue-router'
import {
  ElMessage,
  ElMessageBox,
  type UploadProps,
  type UploadUserFile,
  type UploadInstance
} from 'element-plus'
import {
  Upload,
  UploadFilled,
  View,
  Check,
  Download,
  Right,
  Back,
  WarningFilled
} from '@element-plus/icons-vue'
import PageHeader from '@/components/common/PageHeader.vue'
import DataTable from '@/components/common/DataTable.vue'
import StatusTag from '@/components/common/StatusTag.vue'
import type { TableColumn } from '@/components/common/DataTable.vue'

// ==================== 类型定义 ====================

interface PreviewDataItem {
  index: number
  apple_id: string
  password: string
  security_questions: string
  recovery_key: string
  note: string
  valid: boolean
  errors?: string[]
  error_message?: string
}

interface ImportConfig {
  mode: 'all' | 'valid' | 'selected'
  duplicateHandling: 'skip' | 'update' | 'rename'
  postActions: string[]
}

interface ImportResult {
  success: boolean
  title: string
  subTitle: string
  successCount: number
  failedCount: number
  skippedCount: number
  failedRecords: Array<{ apple_id: string; error: string }>
}

// ==================== 路由 ====================

const router = useRouter()

// ==================== 步骤控制 ====================

const currentStep = ref(0)

// ==================== 文件上传 ====================

const uploadRef = ref<UploadInstance>()
const fileList = ref<UploadUserFile[]>([])
const uploadAction = ref('#')
const acceptFileTypes = ref('.csv,.txt,.xlsx,.xls')
const parseLoading = ref(false)

// 文件变化
const handleFileChange: UploadProps['onChange'] = (file) => {
  fileList.value = [file]
}

// 文件移除
const handleFileRemove: UploadProps['onRemove'] = () => {
  fileList.value = []
}

// 上传前验证
const handleBeforeUpload: UploadProps['beforeUpload'] = (file) => {
  const isValidType = /\.(csv|txt|xlsx|xls)$/.test(file.name.toLowerCase())
  if (!isValidType) {
    ElMessage.error('只能上传 CSV、TXT、Excel 格式的文件')
    return false
  }

  const isLt10M = file.size / 1024 / 1024 < 10
  if (!isLt10M) {
    ElMessage.error('文件大小不能超过 10MB')
    return false
  }

  return true
}

// 上传成功
const handleUploadSuccess: UploadProps['onSuccess'] = () => {
  ElMessage.success('文件上传成功')
}

// 上传失败
const handleUploadError: UploadProps['onError'] = () => {
  ElMessage.error('文件上传失败')
}

// 解析文件
async function handleParseFile() {
  if (fileList.value.length === 0) {
    ElMessage.warning('请先上传文件')
    return
  }

  parseLoading.value = true

  try {
    // TODO: 调用 API 解析文件
    // const formData = new FormData()
    // formData.append('file', fileList.value[0].raw!)
    // const { data } = await accountApi.parseImportFile(formData)

    // 模拟 API 调用
    await new Promise(resolve => setTimeout(resolve, 1500))

    // 模拟解析结果
    const mockData: PreviewDataItem[] = [
      {
        index: 1,
        apple_id: 'test1@example.com',
        password: 'Pass1234',
        security_questions: 'Q1:颜色?A1:蓝色',
        recovery_key: 'ABCD-1234',
        note: '测试账号1',
        valid: true
      },
      {
        index: 2,
        apple_id: 'test2@example.com',
        password: 'Pass5678',
        security_questions: 'Q1:宠物?A1:小白',
        recovery_key: 'EFGH-5678',
        note: '测试账号2',
        valid: true
      },
      {
        index: 3,
        apple_id: 'invalid-email',
        password: '123',
        security_questions: '',
        recovery_key: '',
        note: '',
        valid: false,
        errors: ['apple_id', 'password'],
        error_message: 'Apple ID 格式错误；密码长度不足'
      },
      {
        index: 4,
        apple_id: 'test3@example.com',
        password: 'Pass9999',
        security_questions: '',
        recovery_key: '',
        note: '测试账号3',
        valid: true
      }
    ]

    previewData.value = mockData

    ElMessage.success('文件解析成功')
    currentStep.value = 1
  } catch (error: any) {
    console.error('文件解析失败:', error)
    ElMessage.error(error.message || '文件解析失败，请检查文件格式')
  } finally {
    parseLoading.value = false
  }
}

// ==================== 数据预览 ====================

const previewData = ref<PreviewDataItem[]>([])
const selectedRows = ref<PreviewDataItem[]>([])

const previewColumns: TableColumn[] = [
  { prop: 'apple_id', label: 'Apple ID', minWidth: 180 },
  { prop: 'password', label: '密码', width: 100 },
  { prop: 'security_questions', label: '安全问题', width: 150, showOverflowTooltip: true },
  { prop: 'recovery_key', label: '恢复密钥', width: 120 },
  { prop: 'note', label: '备注', width: 150, showOverflowTooltip: true },
  { prop: 'status', label: '状态', width: 80 },
  { prop: 'error_message', label: '错误信息', minWidth: 200 }
]

const validCount = computed(() => previewData.value.filter(item => item.valid).length)
const invalidCount = computed(() => previewData.value.filter(item => !item.valid).length)

// 选择变化
function handleSelectionChange(rows: PreviewDataItem[]) {
  selectedRows.value = rows
}

// ==================== 导入配置 ====================

const importConfig = reactive<ImportConfig>({
  mode: 'valid',
  duplicateHandling: 'skip',
  postActions: ['check']
})

// 获取导入数量
function getImportCount(): number {
  if (importConfig.mode === 'all') {
    return previewData.value.length
  } else if (importConfig.mode === 'valid') {
    return validCount.value
  } else {
    return selectedRows.value.length
  }
}

// 获取重复处理文本
function getDuplicateHandlingText(): string {
  const map: Record<string, string> = {
    skip: '跳过',
    update: '更新',
    rename: '重命名'
  }
  return map[importConfig.duplicateHandling] || '-'
}

// ==================== 导入执行 ====================

const importLoading = ref(false)
const progressDialogVisible = ref(false)
const importProgress = ref(0)
const importedCount = ref(0)
const totalImportCount = ref(0)

const importResult = reactive<ImportResult>({
  success: true,
  title: '',
  subTitle: '',
  successCount: 0,
  failedCount: 0,
  skippedCount: 0,
  failedRecords: []
})

// 开始导入
async function handleStartImport() {
  const importCount = getImportCount()

  if (importCount === 0) {
    ElMessage.warning('没有可导入的记录')
    return
  }

  try {
    await ElMessageBox.confirm(
      `确定要导入 ${importCount} 条记录吗？`,
      '确认导入',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
  } catch {
    return
  }

  importLoading.value = true
  progressDialogVisible.value = true
  importProgress.value = 0
  importedCount.value = 0
  totalImportCount.value = importCount

  try {
    // 获取要导入的数据
    let dataToImport: PreviewDataItem[] = []
    if (importConfig.mode === 'all') {
      dataToImport = previewData.value
    } else if (importConfig.mode === 'valid') {
      dataToImport = previewData.value.filter(item => item.valid)
    } else {
      dataToImport = selectedRows.value
    }

    // TODO: 调用 API 批量导入
    // const { data } = await accountApi.batchImport({
    //   accounts: dataToImport,
    //   duplicate_handling: importConfig.duplicateHandling,
    //   auto_check: importConfig.postActions.includes('check')
    // })

    // 模拟导入过程
    for (let i = 0; i < dataToImport.length; i++) {
      await new Promise(resolve => setTimeout(resolve, 200))
      importedCount.value = i + 1
      importProgress.value = Math.round((i + 1) / dataToImport.length * 100)
    }

    // 模拟导入结果
    const successCount = dataToImport.filter(item => item.valid).length
    const failedCount = dataToImport.filter(item => !item.valid).length

    importResult.success = failedCount === 0
    importResult.title = importResult.success ? '导入成功' : '导入完成（部分失败）'
    importResult.subTitle = `成功导入 ${successCount} 条账号记录`
    importResult.successCount = successCount
    importResult.failedCount = failedCount
    importResult.skippedCount = 0
    importResult.failedRecords = dataToImport
      .filter(item => !item.valid)
      .map(item => ({
        apple_id: item.apple_id,
        error: item.error_message || '未知错误'
      }))

    // 关闭进度对话框
    progressDialogVisible.value = false

    // 显示结果
    currentStep.value = 3

    ElMessage.success('导入完成')
  } catch (error: any) {
    console.error('导入失败:', error)
    ElMessage.error(error.message || '导入失败，请稍后重试')
    progressDialogVisible.value = false
  } finally {
    importLoading.value = false
  }
}

// ==================== 导入结果操作 ====================

// 查看账号列表
function handleViewAccounts() {
  router.push('/accounts')
}

// 重置导入
function handleResetImport() {
  currentStep.value = 0
  fileList.value = []
  previewData.value = []
  selectedRows.value = []
  importConfig.mode = 'valid'
  importConfig.duplicateHandling = 'skip'
  importConfig.postActions = ['check']
}

// ==================== 格式说明 ====================

const activeFormats = ref(['csv'])

const exampleData = [
  {
    apple_id: 'test1@example.com',
    password: 'Pass1234',
    security_questions: 'Q1:颜色?A1:蓝色',
    recovery_key: 'ABCD-1234',
    note: '测试账号1'
  },
  {
    apple_id: 'test2@example.com',
    password: 'Pass5678',
    security_questions: 'Q1:宠物?A1:小白',
    recovery_key: 'EFGH-5678',
    note: '测试账号2'
  }
]

// 下载模板
function downloadTemplate(type: 'csv' | 'excel') {
  const headers = ['Apple ID', '密码', '安全问题', '恢复密钥', '备注']
  const exampleRows = [
    ['test1@example.com', 'Pass1234', 'Q1:颜色?A1:蓝色', 'ABCD-1234', '测试账号1'],
    ['test2@example.com', 'Pass5678', 'Q1:宠物?A1:小白', 'EFGH-5678', '测试账号2']
  ]

  if (type === 'csv') {
    // 生成 CSV
    const csv = [headers, ...exampleRows]
      .map(row => row.join(','))
      .join('\n')

    // 下载 CSV
    const blob = new Blob(['\ufeff' + csv], { type: 'text/csv;charset=utf-8;' })
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = '账号导入模板.csv'
    link.click()
    URL.revokeObjectURL(url)

    ElMessage.success('CSV 模板下载成功')
  } else {
    // Excel 模板下载需要库支持，这里简化为 CSV
    ElMessage.info('Excel 模板功能开发中，请先使用 CSV 模板')
  }
}

// ==================== 页面操作 ====================

function handleBack() {
  router.push('/accounts')
}
</script>

<style scoped lang="scss">
.account-import-view {
  padding: 20px;
  min-height: 100vh;
  background-color: #f5f7fa;
}

.import-container {
  max-width: 1400px;
  margin: 0 auto;
}

.steps-card {
  margin-bottom: 20px;

  :deep(.el-card__body) {
    padding: 30px;
  }
}

.content-card {
  margin-bottom: 20px;

  .card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    font-size: 16px;
    font-weight: 500;

    .header-actions {
      font-size: 14px;
      font-weight: normal;
      color: #606266;

      strong {
        color: #409eff;
        font-weight: 600;
      }
    }
  }
}

/* 上传区域 */
.upload-section {
  padding: 20px 0;

  .upload-dragger {
    width: 100%;

    :deep(.el-upload) {
      width: 100%;
    }

    :deep(.el-upload-dragger) {
      width: 100%;
      height: 200px;
    }
  }

  .upload-actions {
    display: flex;
    justify-content: center;
    margin-top: 20px;
  }
}

/* 格式说明 */
.format-description {
  padding: 10px;

  .format-title {
    font-weight: 600;
    color: #303133;
    margin: 15px 0 10px 0;
  }

  ul {
    padding-left: 20px;
    margin: 10px 0;

    li {
      line-height: 1.8;
      color: #606266;

      code {
        background-color: #f4f4f5;
        padding: 2px 6px;
        border-radius: 3px;
        font-family: 'Courier New', monospace;
        font-size: 13px;
        color: #e6a23c;
      }
    }
  }

  .format-example {
    background-color: #f4f4f5;
    padding: 15px;
    border-radius: 4px;
    border-left: 3px solid #409eff;
    font-family: 'Courier New', monospace;
    font-size: 13px;
    line-height: 1.6;
    color: #303133;
    overflow-x: auto;
    margin: 10px 0;
  }
}

/* 数据预览 */
.cell-with-status {
  display: flex;
  align-items: center;
  gap: 8px;
}

.preview-actions {
  display: flex;
  justify-content: center;
  gap: 12px;
  margin-top: 20px;
}

/* 导入配置 */
.import-config {
  padding: 20px 0;

  .form-item-hint {
    font-size: 13px;
    color: #909399;
    margin-top: 5px;
  }

  :deep(.el-radio-group) {
    display: flex;
    flex-direction: column;
    gap: 10px;
  }

  :deep(.el-checkbox-group) {
    display: flex;
    flex-direction: column;
    gap: 10px;
  }
}

.import-summary {
  margin: 20px 0;

  .summary-content {
    p {
      margin: 8px 0;
      font-size: 14px;
      line-height: 1.6;

      strong {
        color: #409eff;
        font-weight: 600;
      }
    }
  }
}

.import-actions {
  display: flex;
  justify-content: center;
  gap: 12px;
  margin-top: 20px;
}

/* 导入进度 */
.progress-content {
  padding: 20px 0;

  .progress-text {
    text-align: center;
    font-size: 16px;
    font-weight: 500;
    margin: 20px 0 10px 0;
    color: #303133;
  }

  .progress-hint {
    text-align: center;
    font-size: 14px;
    color: #909399;
    margin: 10px 0;
  }
}

/* 导入结果 */
.result-stats {
  display: flex;
  justify-content: center;
  gap: 40px;
  margin: 30px 0;

  .stat-item {
    text-align: center;
    padding: 20px 30px;
    border-radius: 8px;
    background: linear-gradient(135deg, #f5f7fa 0%, #e8eaf0 100%);

    &.stat-item--success {
      background: linear-gradient(135deg, #e8f5e9 0%, #c8e6c9 100%);
    }

    &.stat-item--error {
      background: linear-gradient(135deg, #ffebee 0%, #ffcdd2 100%);
    }

    &.stat-item--skip {
      background: linear-gradient(135deg, #fff3e0 0%, #ffe0b2 100%);
    }

    .stat-label {
      font-size: 14px;
      color: #606266;
      margin-bottom: 8px;
    }

    .stat-value {
      font-size: 32px;
      font-weight: 600;
      color: #303133;
    }
  }
}

.failed-records {
  margin: 30px 0;
  text-align: left;
}

.result-actions {
  display: flex;
  justify-content: center;
  gap: 12px;
  margin-top: 30px;
}

/* 响应式设计 */
@media screen and (max-width: 1200px) {
  .import-container {
    padding: 0 10px;
  }
}

@media screen and (max-width: 768px) {
  .account-import-view {
    padding: 10px;
  }

  .steps-card {
    :deep(.el-card__body) {
      padding: 20px 10px;
    }

    :deep(.el-step__title) {
      font-size: 13px;
    }
  }

  .card-header {
    flex-direction: column;
    align-items: flex-start !important;
    gap: 10px;

    .header-actions {
      width: 100%;
    }
  }

  .result-stats {
    flex-direction: column;
    gap: 15px;

    .stat-item {
      padding: 15px 20px;
    }
  }

  .preview-actions,
  .import-actions,
  .result-actions {
    flex-direction: column;

    .el-button {
      width: 100%;
    }
  }
}

@media screen and (max-width: 480px) {
  .account-import-view {
    padding: 5px;
  }

  .format-description {
    font-size: 13px;

    .format-example {
      font-size: 11px;
    }
  }

  .preview-stats {
    font-size: 12px;
  }
}
</style>
