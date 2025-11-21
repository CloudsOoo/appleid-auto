<template>
  <div class="html-editor">
    <div class="editor-toolbar">
      <div class="toolbar-left">
        <el-button-group>
          <el-button
            :icon="FullScreen"
            size="small"
            @click="toggleFullscreen"
          >
            {{ isFullscreen ? '退出全屏' : '全屏' }}
          </el-button>
          <el-button
            :icon="DocumentCopy"
            size="small"
            @click="formatCode"
          >
            格式化
          </el-button>
          <el-button
            :icon="CopyDocument"
            size="small"
            @click="copyCode"
          >
            复制
          </el-button>
        </el-button-group>
      </div>

      <div class="toolbar-right">
        <el-tag size="small">
          行数: {{ lineCount }}
        </el-tag>
        <el-tag size="small" type="info">
          字符数: {{ charCount }}
        </el-tag>
      </div>
    </div>

    <div
      class="editor-container"
      :class="{ 'is-fullscreen': isFullscreen }"
    >
      <div class="editor-wrapper">
        <!-- 行号 -->
        <div class="line-numbers" ref="lineNumbersRef">
          <div
            v-for="line in lineCount"
            :key="line"
            class="line-number"
          >
            {{ line }}
          </div>
        </div>

        <!-- 编辑区域 -->
        <textarea
          ref="textareaRef"
          v-model="localValue"
          class="editor-textarea"
          :style="{ height: editorHeight }"
          :placeholder="placeholder"
          spellcheck="false"
          @input="handleInput"
          @scroll="handleScroll"
          @keydown.tab.prevent="handleTab"
        />
      </div>

      <!-- 底部状态栏 -->
      <div class="editor-statusbar">
        <span class="status-item">
          <el-icon><Document /></el-icon>
          HTML 编辑器
        </span>
        <span class="status-item">
          光标位置: {{ cursorPosition.line }}:{{ cursorPosition.column }}
        </span>
        <span class="status-item">
          {{ encoding }}
        </span>
      </div>
    </div>

    <!-- 格式化提示 -->
    <el-dialog
      v-model="formatDialogVisible"
      title="代码格式化"
      width="400px"
      :close-on-click-modal="false"
    >
      <p>代码格式化功能需要集成专业的代码编辑器库（如 Monaco Editor 或 CodeMirror）。</p>
      <p>当前版本提供基础的编辑功能，建议在后续版本中集成完整的编辑器。</p>
      <template #footer>
        <el-button type="primary" @click="formatDialogVisible = false">
          知道了
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, nextTick, onMounted, onUnmounted } from 'vue'
import { ElMessage } from 'element-plus'
import {
  FullScreen,
  DocumentCopy,
  CopyDocument,
  Document
} from '@element-plus/icons-vue'

// ==================== Props 和 Emits ====================

interface Props {
  modelValue: string
  height?: number | string
  placeholder?: string
  readonly?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  modelValue: '',
  height: 400,
  placeholder: '请输入 HTML 代码...',
  readonly: false
})

const emit = defineEmits<{
  'update:modelValue': [value: string]
  'change': [value: string]
}>()

// ==================== 状态 ====================

const localValue = ref(props.modelValue)
const textareaRef = ref<HTMLTextAreaElement>()
const lineNumbersRef = ref<HTMLDivElement>()
const isFullscreen = ref(false)
const formatDialogVisible = ref(false)
const encoding = ref('UTF-8')

// 光标位置
const cursorPosition = ref({
  line: 1,
  column: 1
})

// ==================== 计算属性 ====================

// 行数
const lineCount = computed(() => {
  return localValue.value ? localValue.value.split('\n').length : 1
})

// 字符数
const charCount = computed(() => {
  return localValue.value.length
})

// 编辑器高度
const editorHeight = computed(() => {
  if (isFullscreen.value) {
    return 'calc(100vh - 100px)'
  }
  if (typeof props.height === 'number') {
    return `${props.height}px`
  }
  return props.height
})

// ==================== 方法 ====================

/**
 * 处理输入
 */
function handleInput() {
  emit('update:modelValue', localValue.value)
  emit('change', localValue.value)
  updateCursorPosition()
}

/**
 * 处理滚动同步
 */
function handleScroll() {
  if (textareaRef.value && lineNumbersRef.value) {
    lineNumbersRef.value.scrollTop = textareaRef.value.scrollTop
  }
}

/**
 * 处理 Tab 键
 */
function handleTab(event: KeyboardEvent) {
  if (!textareaRef.value) return

  const textarea = textareaRef.value
  const start = textarea.selectionStart
  const end = textarea.selectionEnd

  // 插入两个空格（或制表符）
  const spaces = '  '
  localValue.value =
    localValue.value.substring(0, start) +
    spaces +
    localValue.value.substring(end)

  // 恢复光标位置
  nextTick(() => {
    textarea.selectionStart = textarea.selectionEnd = start + spaces.length
    handleInput()
  })
}

/**
 * 更新光标位置
 */
function updateCursorPosition() {
  if (!textareaRef.value) return

  const textarea = textareaRef.value
  const position = textarea.selectionStart
  const text = localValue.value.substring(0, position)
  const lines = text.split('\n')

  cursorPosition.value = {
    line: lines.length,
    column: lines[lines.length - 1].length + 1
  }
}

/**
 * 切换全屏
 */
function toggleFullscreen() {
  isFullscreen.value = !isFullscreen.value

  if (isFullscreen.value) {
    document.body.style.overflow = 'hidden'
  } else {
    document.body.style.overflow = ''
  }
}

/**
 * 格式化代码
 */
function formatCode() {
  formatDialogVisible.value = true

  // TODO: 集成代码格式化库（如 prettier）
  // 简单的格式化示例（仅供演示）
  try {
    // 这里可以集成真实的 HTML 格式化库
    ElMessage.info('代码格式化功能待集成专业编辑器库')
  } catch (error) {
    ElMessage.error('格式化失败')
  }
}

/**
 * 复制代码
 */
async function copyCode() {
  if (!localValue.value) {
    ElMessage.warning('没有可复制的内容')
    return
  }

  try {
    await navigator.clipboard.writeText(localValue.value)
    ElMessage.success('代码已复制到剪贴板')
  } catch (error) {
    console.error('复制失败:', error)
    ElMessage.error('复制失败，请手动复制')
  }
}

/**
 * 监听 modelValue 变化
 */
watch(
  () => props.modelValue,
  (newValue) => {
    if (newValue !== localValue.value) {
      localValue.value = newValue
    }
  }
)

// ==================== 生命周期 ====================

onMounted(() => {
  // 监听点击事件，更新光标位置
  if (textareaRef.value) {
    textareaRef.value.addEventListener('click', updateCursorPosition)
    textareaRef.value.addEventListener('keyup', updateCursorPosition)
  }
})

onUnmounted(() => {
  // 清理全屏状态
  if (isFullscreen.value) {
    document.body.style.overflow = ''
  }

  // 移除事件监听
  if (textareaRef.value) {
    textareaRef.value.removeEventListener('click', updateCursorPosition)
    textareaRef.value.removeEventListener('keyup', updateCursorPosition)
  }
})
</script>

<style scoped lang="scss">
.html-editor {
  border: 1px solid #dcdfe6;
  border-radius: 4px;
  background-color: white;
  overflow: hidden;
}

/* 工具栏 */
.editor-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 15px;
  background-color: #f5f7fa;
  border-bottom: 1px solid #dcdfe6;

  .toolbar-left {
    display: flex;
    gap: 10px;
  }

  .toolbar-right {
    display: flex;
    gap: 10px;
  }
}

/* 编辑器容器 */
.editor-container {
  position: relative;
  background-color: #282c34;

  &.is-fullscreen {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    z-index: 9999;
    background-color: #282c34;
  }
}

/* 编辑器包装 */
.editor-wrapper {
  display: flex;
  position: relative;
  overflow: hidden;
}

/* 行号 */
.line-numbers {
  flex-shrink: 0;
  width: 50px;
  background-color: #21252b;
  color: #5c6370;
  font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
  font-size: 14px;
  line-height: 1.6;
  text-align: right;
  padding: 10px 10px 10px 5px;
  user-select: none;
  overflow: hidden;

  .line-number {
    height: 22.4px;
    padding-right: 5px;
  }
}

/* 文本编辑区 */
.editor-textarea {
  flex: 1;
  width: 100%;
  padding: 10px;
  border: none;
  outline: none;
  resize: none;
  background-color: #282c34;
  color: #abb2bf;
  font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
  font-size: 14px;
  line-height: 1.6;
  tab-size: 2;
  white-space: pre;
  overflow-wrap: normal;
  overflow-x: auto;

  &::-webkit-scrollbar {
    width: 10px;
    height: 10px;
  }

  &::-webkit-scrollbar-track {
    background-color: #21252b;
  }

  &::-webkit-scrollbar-thumb {
    background-color: #4e5561;
    border-radius: 5px;

    &:hover {
      background-color: #5c6370;
    }
  }

  &::placeholder {
    color: #5c6370;
  }
}

/* 状态栏 */
.editor-statusbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 5px 15px;
  background-color: #21252b;
  border-top: 1px solid #181a1f;
  font-size: 12px;
  color: #5c6370;

  .status-item {
    display: flex;
    align-items: center;
    gap: 5px;
  }
}

/* 响应式设计 */
@media screen and (max-width: 768px) {
  .editor-toolbar {
    padding: 8px 10px;

    .toolbar-right {
      display: none;
    }
  }

  .line-numbers {
    width: 40px;
    font-size: 12px;
  }

  .editor-textarea {
    font-size: 13px;
  }

  .editor-statusbar {
    flex-direction: column;
    align-items: flex-start;
    gap: 5px;
  }
}

@media screen and (max-width: 480px) {
  .editor-toolbar {
    padding: 5px 8px;

    .el-button {
      padding: 5px 8px;
    }

    .el-button span {
      display: none;
    }
  }

  .line-numbers {
    width: 35px;
    font-size: 11px;
  }

  .editor-textarea {
    font-size: 12px;
    padding: 8px;
  }
}
</style>
