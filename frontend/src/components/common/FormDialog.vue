<!--
  表单对话框组件

  职责：
  - 提供通用的表单对话框功能
  - 支持动态表单生成（基于配置）
  - 支持表单验证（Element Plus 规则）
  - 支持提交处理（loading 状态）
  - 支持取消/关闭（可配置是否二次确认）
  - 支持自定义表单项渲染（插槽）

  上游依赖：
  - Element Plus（el-dialog, el-form, el-form-item, 各类输入组件）
  - Vue 3（Composition API）

  下游调用者：
  - AccountList（添加/编辑账号）
  - TaskList（创建任务）
  - UserManagement（添加/编辑用户）
  - PackageManagement（添加/编辑套餐）
  - 其他需要表单对话框的页面
-->

<template>
  <el-dialog
    v-model="dialogVisible"
    :title="title"
    :width="width"
    :close-on-click-modal="false"
    :close-on-press-escape="closeOnEscape"
    :before-close="handleBeforeClose"
    :destroy-on-close="destroyOnClose"
    :draggable="draggable"
    class="form-dialog"
  >
    <!-- 表单主体 -->
    <el-form
      ref="formRef"
      :model="formData"
      :rules="formRules"
      :label-width="labelWidth"
      :label-position="labelPosition"
      :size="size"
      :disabled="formDisabled"
      class="dialog-form"
    >
      <!-- 动态表单项 -->
      <template v-for="field in visibleFields" :key="field.prop">
        <!-- 使用自定义插槽 -->
        <el-form-item
          v-if="$slots[`field-${field.prop}`]"
          :label="field.label"
          :prop="field.prop"
          :required="field.required"
        >
          <slot :name="`field-${field.prop}`" :field="field" :form-data="formData"></slot>
        </el-form-item>

        <!-- 文本输入框 -->
        <el-form-item
          v-else-if="field.type === 'text' || field.type === 'password' || field.type === 'email' || field.type === 'url'"
          :label="field.label"
          :prop="field.prop"
          :required="field.required"
        >
          <el-input
            v-model="formData[field.prop]"
            :type="field.type"
            :placeholder="field.placeholder || `请输入${field.label}`"
            :maxlength="field.maxlength"
            :show-word-limit="field.showWordLimit"
            :show-password="field.type === 'password'"
            :disabled="field.disabled"
            :clearable="field.clearable !== false"
            :prefix-icon="field.prefixIcon"
            :suffix-icon="field.suffixIcon"
          />
        </el-form-item>

        <!-- 数字输入框 -->
        <el-form-item
          v-else-if="field.type === 'number'"
          :label="field.label"
          :prop="field.prop"
          :required="field.required"
        >
          <el-input-number
            v-model="formData[field.prop]"
            :placeholder="field.placeholder || `请输入${field.label}`"
            :min="field.min"
            :max="field.max"
            :step="field.step"
            :precision="field.precision"
            :disabled="field.disabled"
            :controls-position="field.controlsPosition || 'right'"
            style="width: 100%"
          />
        </el-form-item>

        <!-- 文本域 -->
        <el-form-item
          v-else-if="field.type === 'textarea'"
          :label="field.label"
          :prop="field.prop"
          :required="field.required"
        >
          <el-input
            v-model="formData[field.prop]"
            type="textarea"
            :placeholder="field.placeholder || `请输入${field.label}`"
            :rows="field.rows || 4"
            :maxlength="field.maxlength"
            :show-word-limit="field.showWordLimit"
            :disabled="field.disabled"
          />
        </el-form-item>

        <!-- 下拉选择 -->
        <el-form-item
          v-else-if="field.type === 'select'"
          :label="field.label"
          :prop="field.prop"
          :required="field.required"
        >
          <el-select
            v-model="formData[field.prop]"
            :placeholder="field.placeholder || `请选择${field.label}`"
            :multiple="field.multiple"
            :disabled="field.disabled"
            :clearable="field.clearable !== false"
            :filterable="field.filterable"
            style="width: 100%"
          >
            <el-option
              v-for="option in field.options"
              :key="option.value"
              :label="option.label"
              :value="option.value"
              :disabled="option.disabled"
            />
          </el-select>
        </el-form-item>

        <!-- 单选框 -->
        <el-form-item
          v-else-if="field.type === 'radio'"
          :label="field.label"
          :prop="field.prop"
          :required="field.required"
        >
          <el-radio-group v-model="formData[field.prop]" :disabled="field.disabled">
            <el-radio
              v-for="option in field.options"
              :key="option.value"
              :label="option.value"
              :disabled="option.disabled"
            >
              {{ option.label }}
            </el-radio>
          </el-radio-group>
        </el-form-item>

        <!-- 多选框 -->
        <el-form-item
          v-else-if="field.type === 'checkbox'"
          :label="field.label"
          :prop="field.prop"
          :required="field.required"
        >
          <el-checkbox-group v-model="formData[field.prop]" :disabled="field.disabled">
            <el-checkbox
              v-for="option in field.options"
              :key="option.value"
              :label="option.value"
              :disabled="option.disabled"
            >
              {{ option.label }}
            </el-checkbox>
          </el-checkbox-group>
        </el-form-item>

        <!-- 开关 -->
        <el-form-item
          v-else-if="field.type === 'switch'"
          :label="field.label"
          :prop="field.prop"
          :required="field.required"
        >
          <el-switch
            v-model="formData[field.prop]"
            :disabled="field.disabled"
            :active-text="field.activeText"
            :inactive-text="field.inactiveText"
            :active-value="field.activeValue ?? true"
            :inactive-value="field.inactiveValue ?? false"
          />
        </el-form-item>

        <!-- 日期选择 -->
        <el-form-item
          v-else-if="field.type === 'date' || field.type === 'datetime'"
          :label="field.label"
          :prop="field.prop"
          :required="field.required"
        >
          <el-date-picker
            v-model="formData[field.prop]"
            :type="field.type === 'datetime' ? 'datetime' : 'date'"
            :placeholder="field.placeholder || `请选择${field.label}`"
            :disabled="field.disabled"
            :clearable="field.clearable !== false"
            :format="field.format"
            :value-format="field.valueFormat"
            style="width: 100%"
          />
        </el-form-item>

        <!-- 日期范围选择 -->
        <el-form-item
          v-else-if="field.type === 'daterange'"
          :label="field.label"
          :prop="field.prop"
          :required="field.required"
        >
          <el-date-picker
            v-model="formData[field.prop]"
            type="daterange"
            :range-separator="field.rangeSeparator || '至'"
            :start-placeholder="field.startPlaceholder || '开始日期'"
            :end-placeholder="field.endPlaceholder || '结束日期'"
            :disabled="field.disabled"
            :clearable="field.clearable !== false"
            :format="field.format"
            :value-format="field.valueFormat"
            style="width: 100%"
          />
        </el-form-item>

        <!-- 时间选择 -->
        <el-form-item
          v-else-if="field.type === 'time'"
          :label="field.label"
          :prop="field.prop"
          :required="field.required"
        >
          <el-time-picker
            v-model="formData[field.prop]"
            :placeholder="field.placeholder || `请选择${field.label}`"
            :disabled="field.disabled"
            :clearable="field.clearable !== false"
            :format="field.format"
            :value-format="field.valueFormat"
            style="width: 100%"
          />
        </el-form-item>

        <!-- 上传（单文件） -->
        <el-form-item
          v-else-if="field.type === 'upload'"
          :label="field.label"
          :prop="field.prop"
          :required="field.required"
        >
          <el-upload
            :action="field.action || '#'"
            :accept="field.accept"
            :limit="field.limit || 1"
            :file-list="formData[field.prop] || []"
            :disabled="field.disabled"
            :on-success="(response, file, fileList) => handleUploadSuccess(field.prop, response, file, fileList)"
            :on-remove="(file, fileList) => handleUploadRemove(field.prop, file, fileList)"
            :before-upload="field.beforeUpload"
          >
            <el-button type="primary">{{ field.buttonText || '点击上传' }}</el-button>
            <template v-if="field.tip" #tip>
              <div class="el-upload__tip">{{ field.tip }}</div>
            </template>
          </el-upload>
        </el-form-item>

        <!-- 级联选择 -->
        <el-form-item
          v-else-if="field.type === 'cascader'"
          :label="field.label"
          :prop="field.prop"
          :required="field.required"
        >
          <el-cascader
            v-model="formData[field.prop]"
            :options="field.options"
            :props="field.cascaderProps"
            :placeholder="field.placeholder || `请选择${field.label}`"
            :disabled="field.disabled"
            :clearable="field.clearable !== false"
            :filterable="field.filterable"
            style="width: 100%"
          />
        </el-form-item>

        <!-- 自定义内容（使用默认插槽） -->
        <el-form-item
          v-else-if="field.type === 'custom'"
          :label="field.label"
          :prop="field.prop"
          :required="field.required"
        >
          <slot :name="`custom-${field.prop}`" :field="field" :form-data="formData">
            <div class="custom-placeholder">请使用插槽 custom-{{ field.prop }} 渲染内容</div>
          </slot>
        </el-form-item>
      </template>

      <!-- 额外的表单插槽（在所有字段之后） -->
      <slot name="extra-fields" :form-data="formData"></slot>
    </el-form>

    <!-- 对话框底部按钮 -->
    <template #footer>
      <div class="dialog-footer">
        <!-- 自定义底部插槽 -->
        <slot name="footer" :form-data="formData" :loading="submitLoading">
          <el-button @click="handleCancel" :disabled="submitLoading">
            {{ cancelText }}
          </el-button>
          <el-button
            type="primary"
            :loading="submitLoading"
            @click="handleSubmit"
          >
            {{ submitText }}
          </el-button>
        </slot>
      </div>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { ElMessage, ElMessageBox, type FormInstance, type FormRules } from 'element-plus'

/**
 * 表单字段类型定义
 */
export interface FormField {
  prop: string                    // 字段属性名（对应 formData 的 key）
  label: string                   // 字段标签
  type: 'text' | 'password' | 'email' | 'url' | 'number' | 'textarea' |
        'select' | 'radio' | 'checkbox' | 'switch' |
        'date' | 'datetime' | 'daterange' | 'time' |
        'upload' | 'cascader' | 'custom'  // 字段类型
  required?: boolean              // 是否必填
  placeholder?: string            // 占位符
  disabled?: boolean              // 是否禁用
  visible?: boolean               // 是否可见（默认 true）

  // 文本输入框
  maxlength?: number
  showWordLimit?: boolean
  clearable?: boolean
  prefixIcon?: string
  suffixIcon?: string

  // 数字输入框
  min?: number
  max?: number
  step?: number
  precision?: number
  controlsPosition?: 'right' | ''

  // 文本域
  rows?: number

  // 下拉选择、单选、多选、级联
  options?: Array<{ label: string; value: any; disabled?: boolean }>
  multiple?: boolean
  filterable?: boolean
  cascaderProps?: any

  // 开关
  activeText?: string
  inactiveText?: string
  activeValue?: any
  inactiveValue?: any

  // 日期
  format?: string
  valueFormat?: string
  rangeSeparator?: string
  startPlaceholder?: string
  endPlaceholder?: string

  // 上传
  action?: string
  accept?: string
  limit?: number
  buttonText?: string
  tip?: string
  beforeUpload?: (file: any) => boolean | Promise<any>
}

/**
 * Props 配置
 */
interface Props {
  // 对话框基础配置
  modelValue: boolean             // 对话框显示状态（v-model）
  title?: string                  // 对话框标题（默认 "表单"）
  width?: string | number         // 对话框宽度（默认 "600px"）
  closeOnEscape?: boolean         // 按 ESC 关闭（默认 true）
  destroyOnClose?: boolean        // 关闭时销毁内容（默认 false）
  draggable?: boolean             // 是否可拖拽（默认 false）

  // 表单配置
  fields: FormField[]             // 表单字段配置
  initialData?: Record<string, any>  // 初始数据（用于编辑模式）
  rules?: FormRules               // 表单验证规则（Element Plus 格式）
  labelWidth?: string | number    // 标签宽度（默认 "100px"）
  labelPosition?: 'left' | 'right' | 'top'  // 标签位置（默认 "right"）
  size?: 'large' | 'default' | 'small'  // 表单大小（默认 "default"）

  // 提交配置
  submitText?: string             // 提交按钮文本（默认 "确定"）
  cancelText?: string             // 取消按钮文本（默认 "取消"）
  confirmClose?: boolean          // 关闭时是否二次确认（默认 false）
  confirmCloseMessage?: string    // 关闭确认提示文本

  // 其他配置
  disabled?: boolean              // 是否禁用整个表单（默认 false）
}

const props = withDefaults(defineProps<Props>(), {
  title: '表单',
  width: '600px',
  closeOnEscape: true,
  destroyOnClose: false,
  draggable: false,
  initialData: () => ({}),
  labelWidth: '100px',
  labelPosition: 'right',
  size: 'default',
  submitText: '确定',
  cancelText: '取消',
  confirmClose: false,
  confirmCloseMessage: '表单尚未保存，确定要关闭吗？',
  disabled: false
})

/**
 * Emits
 */
interface Emits {
  (e: 'update:modelValue', visible: boolean): void
  (e: 'submit', data: Record<string, any>): void | Promise<void>
  (e: 'cancel'): void
  (e: 'close'): void
}

const emit = defineEmits<Emits>()

/**
 * 对话框显示状态
 */
const dialogVisible = computed({
  get: () => props.modelValue,
  set: (value) => emit('update:modelValue', value)
})

/**
 * 表单引用和数据
 */
const formRef = ref<FormInstance>()
const formData = ref<Record<string, any>>({})
const submitLoading = ref(false)

/**
 * 表单验证规则
 */
const formRules = computed(() => {
  if (props.rules) {
    return props.rules
  }

  // 自动生成必填规则
  const rules: FormRules = {}
  props.fields.forEach(field => {
    if (field.required) {
      rules[field.prop] = [
        { required: true, message: `${field.label}不能为空`, trigger: 'blur' }
      ]
    }
  })

  return rules
})

/**
 * 可见字段列表
 */
const visibleFields = computed(() => {
  return props.fields.filter(field => field.visible !== false)
})

/**
 * 表单禁用状态
 */
const formDisabled = computed(() => {
  return props.disabled || submitLoading.value
})

/**
 * 初始化表单数据
 */
function initFormData() {
  const data: Record<string, any> = {}

  props.fields.forEach(field => {
    // 优先使用 initialData 中的值
    if (props.initialData && field.prop in props.initialData) {
      data[field.prop] = props.initialData[field.prop]
    } else {
      // 设置默认值
      switch (field.type) {
        case 'checkbox':
          data[field.prop] = []
          break
        case 'switch':
          data[field.prop] = field.inactiveValue ?? false
          break
        case 'number':
          data[field.prop] = field.min ?? 0
          break
        default:
          data[field.prop] = ''
      }
    }
  })

  formData.value = data
}

/**
 * 重置表单
 */
function resetForm() {
  formRef.value?.resetFields()
  initFormData()
}

/**
 * 表单提交处理
 */
async function handleSubmit() {
  if (!formRef.value) {
    return
  }

  try {
    // 表单验证
    await formRef.value.validate()

    // 提交数据
    submitLoading.value = true
    await emit('submit', formData.value)

    // 提交成功，关闭对话框
    ElMessage.success('操作成功')
    dialogVisible.value = false
  } catch (error) {
    // 验证失败或提交失败
    if (error !== false) {
      console.error('[FormDialog] Submit error:', error)
      ElMessage.error('操作失败，请检查表单')
    }
  } finally {
    submitLoading.value = false
  }
}

/**
 * 取消按钮处理
 */
function handleCancel() {
  if (props.confirmClose) {
    ElMessageBox.confirm(props.confirmCloseMessage, '提示', {
      type: 'warning',
      confirmButtonText: '确定',
      cancelButtonText: '取消'
    }).then(() => {
      dialogVisible.value = false
      emit('cancel')
    }).catch(() => {
      // 用户取消关闭
    })
  } else {
    dialogVisible.value = false
    emit('cancel')
  }
}

/**
 * 对话框关闭前处理
 */
function handleBeforeClose(done: () => void) {
  if (props.confirmClose && !submitLoading.value) {
    ElMessageBox.confirm(props.confirmCloseMessage, '提示', {
      type: 'warning',
      confirmButtonText: '确定',
      cancelButtonText: '取消'
    }).then(() => {
      done()
      emit('close')
    }).catch(() => {
      // 用户取消关闭
    })
  } else {
    done()
    emit('close')
  }
}

/**
 * 上传成功处理
 */
function handleUploadSuccess(prop: string, response: any, file: any, fileList: any[]) {
  formData.value[prop] = fileList
}

/**
 * 上传移除处理
 */
function handleUploadRemove(prop: string, file: any, fileList: any[]) {
  formData.value[prop] = fileList
}

/**
 * 监听对话框打开，初始化表单数据
 */
watch(
  () => props.modelValue,
  (visible) => {
    if (visible) {
      initFormData()
    } else {
      // 对话框关闭时重置表单（如果启用了 destroyOnClose，这里可以省略）
      if (!props.destroyOnClose) {
        resetForm()
      }
    }
  },
  { immediate: true }
)

/**
 * 暴露方法（供父组件调用）
 */
defineExpose({
  formRef,
  formData,
  resetForm,
  validate: () => formRef.value?.validate(),
  clearValidate: () => formRef.value?.clearValidate()
})
</script>

<style scoped lang="scss">
.form-dialog {
  :deep(.el-dialog__body) {
    padding: 20px 20px 10px;
    max-height: 60vh;
    overflow-y: auto;
  }

  .dialog-form {
    .custom-placeholder {
      padding: 20px;
      text-align: center;
      color: var(--el-text-color-secondary);
      background-color: var(--el-fill-color-light);
      border: 1px dashed var(--el-border-color);
      border-radius: 4px;
    }
  }

  .dialog-footer {
    display: flex;
    align-items: center;
    justify-content: flex-end;
    gap: 10px;
  }
}

// 响应式设计
@media (max-width: 768px) {
  .form-dialog {
    :deep(.el-dialog) {
      width: 90% !important;
      margin: 0 auto;
    }

    :deep(.el-dialog__body) {
      padding: 15px 15px 10px;
      max-height: 50vh;
    }

    .dialog-form {
      :deep(.el-form-item__label) {
        font-size: 13px;
      }

      :deep(.el-input),
      :deep(.el-select),
      :deep(.el-date-picker) {
        font-size: 14px;
      }
    }
  }
}

// 小屏幕优化
@media (max-width: 480px) {
  .form-dialog {
    :deep(.el-dialog) {
      width: 95% !important;
    }

    :deep(.el-dialog__body) {
      padding: 10px 10px 5px;
    }

    .dialog-form {
      :deep(.el-form-item) {
        margin-bottom: 18px;
      }
    }

    .dialog-footer {
      flex-direction: column-reverse;
      gap: 8px;

      .el-button {
        width: 100%;
      }
    }
  }
}
</style>
