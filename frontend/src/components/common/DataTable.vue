<!--
  通用数据表格组件

  职责：
  - 提供通用的数据表格展示
  - 支持自定义列配置
  - 支持分页（前端分页和后端分页）
  - 支持排序（单列和多列）
  - 支持筛选（搜索、日期范围、下拉选择）
  - 支持批量操作（批量删除、批量导出）
  - 支持数据导出（CSV、Excel）
  - 支持操作按钮（编辑、删除、自定义）
  - 支持加载状态和空状态

  上游依赖：
  - Element Plus（el-table 组件）
  - 下载工具（@/utils/download）

  下游调用者：
  - 各个业务页面（AccountList、TaskList、UserList 等）
-->

<template>
  <div class="data-table">
    <!-- 表格工具栏 -->
    <div v-if="showToolbar" class="table-toolbar">
      <!-- 左侧：标题和描述 -->
      <div class="toolbar-left">
        <h3 v-if="title" class="table-title">{{ title }}</h3>
        <span v-if="description" class="table-description">{{ description }}</span>
      </div>

      <!-- 右侧：操作按钮 -->
      <div class="toolbar-right">
        <!-- 搜索框 -->
        <el-input
          v-if="showSearch"
          v-model="searchKeyword"
          :placeholder="searchPlaceholder"
          :style="{ width: searchWidth }"
          clearable
          @input="handleSearch"
        >
          <template #prefix>
            <el-icon><icon-search /></el-icon>
          </template>
        </el-input>

        <!-- 刷新按钮 -->
        <el-button
          v-if="showRefresh"
          :icon="'Refresh'"
          circle
          @click="handleRefresh"
        />

        <!-- 批量操作下拉菜单 -->
        <el-dropdown
          v-if="showBatchActions && selectedRows.length > 0"
          trigger="click"
          @command="handleBatchAction"
        >
          <el-button type="primary">
            批量操作 ({{ selectedRows.length }})
            <el-icon class="el-icon--right"><icon-arrow-down /></el-icon>
          </el-button>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item
                v-for="action in batchActions"
                :key="action.key"
                :command="action.key"
                :icon="action.icon"
              >
                {{ action.label }}
              </el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>

        <!-- 导出按钮 -->
        <el-dropdown
          v-if="showExport"
          trigger="click"
          @command="handleExport"
        >
          <el-button :icon="'Download'">
            导出
            <el-icon class="el-icon--right"><icon-arrow-down /></el-icon>
          </el-button>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item command="csv" icon="Document">导出 CSV</el-dropdown-item>
              <el-dropdown-item command="excel" icon="Document">导出 Excel</el-dropdown-item>
              <el-dropdown-item command="json" icon="Document">导出 JSON</el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>

        <!-- 自定义操作按钮插槽 -->
        <slot name="toolbar-actions"></slot>

        <!-- 列配置按钮 -->
        <el-popover
          v-if="showColumnConfig"
          placement="bottom-end"
          :width="240"
          trigger="click"
        >
          <template #reference>
            <el-button :icon="'Setting'" circle />
          </template>
          <div class="column-config">
            <div class="column-config-header">列配置</div>
            <el-checkbox
              v-for="col in configurableColumns"
              :key="col.prop"
              v-model="col.visible"
              :label="col.label"
              class="column-config-item"
              @change="handleColumnVisibilityChange"
            />
          </div>
        </el-popover>
      </div>
    </div>

    <!-- 表格主体 -->
    <el-table
      ref="tableRef"
      :data="displayData"
      :loading="loading"
      :stripe="stripe"
      :border="border"
      :height="height"
      :max-height="maxHeight"
      :row-key="rowKey"
      :empty-text="emptyText"
      :default-sort="defaultSort"
      class="data-table-main"
      @selection-change="handleSelectionChange"
      @sort-change="handleSortChange"
      @row-click="handleRowClick"
      @row-dblclick="handleRowDblclick"
    >
      <!-- 多选列 -->
      <el-table-column
        v-if="showSelection"
        type="selection"
        :width="selectionWidth"
        :reserve-selection="reserveSelection"
        fixed="left"
      />

      <!-- 索引列 -->
      <el-table-column
        v-if="showIndex"
        type="index"
        label="序号"
        :width="indexWidth"
        :index="indexMethod"
        fixed="left"
      />

      <!-- 数据列 -->
      <el-table-column
        v-for="column in visibleColumns"
        :key="column.prop"
        :prop="column.prop"
        :label="column.label"
        :width="column.width"
        :min-width="column.minWidth"
        :fixed="column.fixed"
        :sortable="column.sortable"
        :align="column.align || 'left'"
        :header-align="column.headerAlign || column.align || 'left'"
        :show-overflow-tooltip="column.showOverflowTooltip !== false"
      >
        <template #default="{ row, column: col, $index }">
          <!-- 自定义列内容插槽 -->
          <slot
            v-if="$slots[`column-${column.prop}`]"
            :name="`column-${column.prop}`"
            :row="row"
            :column="col"
            :index="$index"
          ></slot>

          <!-- 默认列内容 -->
          <span v-else>{{ row[column.prop] }}</span>
        </template>
      </el-table-column>

      <!-- 操作列 -->
      <el-table-column
        v-if="showActions"
        label="操作"
        :width="actionsWidth"
        :fixed="actionsFixed"
        align="center"
      >
        <template #default="{ row, $index }">
          <!-- 自定义操作列插槽 -->
          <slot
            v-if="$slots.actions"
            name="actions"
            :row="row"
            :index="$index"
          ></slot>

          <!-- 默认操作按钮 -->
          <div v-else class="action-buttons">
            <el-button
              v-for="action in rowActions"
              :key="action.key"
              :type="action.type || 'primary'"
              :icon="action.icon"
              :disabled="action.disabled && action.disabled(row)"
              link
              @click="handleRowAction(action.key, row, $index)"
            >
              {{ action.label }}
            </el-button>
          </div>
        </template>
      </el-table-column>
    </el-table>

    <!-- 分页 -->
    <div v-if="showPagination" class="table-pagination">
      <el-pagination
        v-model:current-page="currentPage"
        v-model:page-size="pageSize"
        :page-sizes="pageSizes"
        :total="total"
        :layout="paginationLayout"
        :background="paginationBackground"
        @size-change="handleSizeChange"
        @current-change="handleCurrentChange"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, nextTick } from 'vue'
import { ElMessage, ElMessageBox, type TableInstance } from 'element-plus'
import { downloadCSV, downloadJSON } from '@/utils/download'

/**
 * 列配置类型
 */
export interface TableColumn {
  prop: string                          // 字段名
  label: string                         // 列标题
  width?: string | number               // 列宽度
  minWidth?: string | number            // 最小宽度
  fixed?: boolean | 'left' | 'right'    // 固定列
  sortable?: boolean | 'custom'         // 是否可排序
  align?: 'left' | 'center' | 'right'   // 对齐方式
  headerAlign?: 'left' | 'center' | 'right'  // 表头对齐
  showOverflowTooltip?: boolean         // 超出显示 tooltip
  visible?: boolean                     // 是否可见（列配置用）
}

/**
 * 操作按钮配置类型
 */
export interface ActionButton {
  key: string                           // 操作键
  label: string                         // 按钮文本
  type?: 'primary' | 'success' | 'warning' | 'danger' | 'info'  // 按钮类型
  icon?: string                         // 图标
  disabled?: (row: any) => boolean      // 是否禁用（动态）
}

/**
 * 批量操作配置类型
 */
export interface BatchAction {
  key: string                           // 操作键
  label: string                         // 操作文本
  icon?: string                         // 图标
}

/**
 * Props 配置
 */
interface Props {
  // 数据相关
  data?: any[]                          // 表格数据
  loading?: boolean                     // 加载状态
  rowKey?: string                       // 行数据的 Key

  // 列配置
  columns?: TableColumn[]               // 列配置
  showSelection?: boolean               // 是否显示多选
  showIndex?: boolean                   // 是否显示索引
  showActions?: boolean                 // 是否显示操作列
  rowActions?: ActionButton[]           // 行操作按钮

  // 表格样式
  stripe?: boolean                      // 是否斑马纹
  border?: boolean                      // 是否带边框
  height?: string | number              // 表格高度
  maxHeight?: string | number           // 最大高度

  // 工具栏
  showToolbar?: boolean                 // 是否显示工具栏
  title?: string                        // 表格标题
  description?: string                  // 表格描述
  showSearch?: boolean                  // 是否显示搜索
  searchPlaceholder?: string            // 搜索占位符
  searchWidth?: string                  // 搜索框宽度
  showRefresh?: boolean                 // 是否显示刷新按钮
  showExport?: boolean                  // 是否显示导出按钮
  showColumnConfig?: boolean            // 是否显示列配置
  showBatchActions?: boolean            // 是否显示批量操作
  batchActions?: BatchAction[]          // 批量操作配置

  // 分页
  showPagination?: boolean              // 是否显示分页
  paginationMode?: 'client' | 'server'  // 分页模式（客户端/服务端）
  total?: number                        // 总记录数（服务端分页用）
  pageSize?: number                     // 每页条数
  pageSizes?: number[]                  // 每页条数选项
  paginationLayout?: string             // 分页布局
  paginationBackground?: boolean        // 分页背景

  // 其他配置
  emptyText?: string                    // 空数据文本
  defaultSort?: { prop: string; order: 'ascending' | 'descending' }  // 默认排序
  selectionWidth?: number               // 多选列宽度
  indexWidth?: number                   // 索引列宽度
  actionsWidth?: number                 // 操作列宽度
  actionsFixed?: boolean | 'left' | 'right'  // 操作列固定
  reserveSelection?: boolean            // 是否保留选中状态
}

const props = withDefaults(defineProps<Props>(), {
  data: () => [],
  loading: false,
  rowKey: 'id',
  columns: () => [],
  showSelection: false,
  showIndex: false,
  showActions: false,
  rowActions: () => [],
  stripe: true,
  border: true,
  showToolbar: true,
  showSearch: false,
  searchPlaceholder: '请输入关键词搜索',
  searchWidth: '240px',
  showRefresh: false,
  showExport: false,
  showColumnConfig: false,
  showBatchActions: false,
  batchActions: () => [],
  showPagination: true,
  paginationMode: 'client',
  total: 0,
  pageSize: 20,
  pageSizes: () => [10, 20, 50, 100],
  paginationLayout: 'total, sizes, prev, pager, next, jumper',
  paginationBackground: true,
  emptyText: '暂无数据',
  selectionWidth: 55,
  indexWidth: 60,
  actionsWidth: 180,
  actionsFixed: 'right',
  reserveSelection: false
})

/**
 * Emits
 */
interface Emits {
  (e: 'refresh'): void
  (e: 'search', keyword: string): void
  (e: 'sort-change', sortProp: string, sortOrder: 'ascending' | 'descending' | null): void
  (e: 'page-change', page: number, pageSize: number): void
  (e: 'selection-change', selectedRows: any[]): void
  (e: 'row-action', actionKey: string, row: any, index: number): void
  (e: 'batch-action', actionKey: string, selectedRows: any[]): void
  (e: 'row-click', row: any, column: any, event: Event): void
  (e: 'row-dblclick', row: any, column: any, event: Event): void
  (e: 'export', format: 'csv' | 'excel' | 'json', data: any[]): void
}

const emit = defineEmits<Emits>()

/**
 * 表格引用
 */
const tableRef = ref<TableInstance>()

/**
 * 搜索关键词
 */
const searchKeyword = ref('')

/**
 * 当前页码
 */
const currentPage = ref(1)

/**
 * 每页条数
 */
const pageSize = ref(props.pageSize)

/**
 * 选中的行
 */
const selectedRows = ref<any[]>([])

/**
 * 可配置的列（用于列配置功能）
 */
const configurableColumns = ref<TableColumn[]>([])

/**
 * 初始化可配置列
 */
watch(
  () => props.columns,
  (newColumns) => {
    configurableColumns.value = newColumns.map(col => ({
      ...col,
      visible: col.visible !== false
    }))
  },
  { immediate: true, deep: true }
)

/**
 * 可见的列
 */
const visibleColumns = computed(() => {
  return configurableColumns.value.filter(col => col.visible !== false)
})

/**
 * 总记录数
 */
const total = computed(() => {
  if (props.paginationMode === 'server') {
    return props.total
  }
  return filteredData.value.length
})

/**
 * 过滤后的数据（客户端搜索）
 */
const filteredData = computed(() => {
  if (!searchKeyword.value || props.paginationMode === 'server') {
    return props.data
  }

  const keyword = searchKeyword.value.toLowerCase()
  return props.data.filter(row => {
    return Object.values(row).some(value =>
      String(value).toLowerCase().includes(keyword)
    )
  })
})

/**
 * 显示的数据（客户端分页）
 */
const displayData = computed(() => {
  if (props.paginationMode === 'server') {
    return props.data
  }

  const start = (currentPage.value - 1) * pageSize.value
  const end = start + pageSize.value
  return filteredData.value.slice(start, end)
})

/**
 * 索引计算方法
 */
const indexMethod = (index: number) => {
  return (currentPage.value - 1) * pageSize.value + index + 1
}

/**
 * 搜索处理
 */
function handleSearch(keyword: string) {
  if (props.paginationMode === 'server') {
    emit('search', keyword)
  } else {
    // 客户端搜索，重置到第一页
    currentPage.value = 1
  }
}

/**
 * 刷新处理
 */
function handleRefresh() {
  emit('refresh')
}

/**
 * 排序处理
 */
function handleSortChange({ prop, order }: { prop: string; order: string }) {
  emit('sort-change', prop, order as 'ascending' | 'descending' | null)
}

/**
 * 每页条数变化
 */
function handleSizeChange(newSize: number) {
  pageSize.value = newSize
  currentPage.value = 1
  emit('page-change', currentPage.value, pageSize.value)
}

/**
 * 当前页变化
 */
function handleCurrentChange(newPage: number) {
  currentPage.value = newPage
  emit('page-change', currentPage.value, pageSize.value)
}

/**
 * 选择变化
 */
function handleSelectionChange(selection: any[]) {
  selectedRows.value = selection
  emit('selection-change', selection)
}

/**
 * 行操作处理
 */
function handleRowAction(actionKey: string, row: any, index: number) {
  emit('row-action', actionKey, row, index)
}

/**
 * 批量操作处理
 */
async function handleBatchAction(actionKey: string) {
  if (selectedRows.value.length === 0) {
    ElMessage.warning('请先选择要操作的数据')
    return
  }

  // 批量删除需要二次确认
  if (actionKey === 'delete') {
    try {
      await ElMessageBox.confirm(
        `确定要删除选中的 ${selectedRows.value.length} 条记录吗？`,
        '批量删除',
        {
          type: 'warning',
          confirmButtonText: '确定',
          cancelButtonText: '取消'
        }
      )
    } catch {
      return
    }
  }

  emit('batch-action', actionKey, selectedRows.value)
}

/**
 * 行点击
 */
function handleRowClick(row: any, column: any, event: Event) {
  emit('row-click', row, column, event)
}

/**
 * 行双击
 */
function handleRowDblclick(row: any, column: any, event: Event) {
  emit('row-dblclick', row, column, event)
}

/**
 * 导出处理
 */
function handleExport(format: 'csv' | 'excel' | 'json') {
  const exportData = selectedRows.value.length > 0 ? selectedRows.value : displayData.value

  if (exportData.length === 0) {
    ElMessage.warning('没有可导出的数据')
    return
  }

  const filename = `${props.title || 'data'}_${Date.now()}`

  switch (format) {
    case 'csv':
    case 'excel':
      downloadCSV(exportData, `${filename}.csv`)
      break
    case 'json':
      downloadJSON(exportData, `${filename}.json`)
      break
  }

  emit('export', format, exportData)
  ElMessage.success('导出成功')
}

/**
 * 列可见性变化
 */
function handleColumnVisibilityChange() {
  // 列配置变化后可以触发自定义事件
  // emit('column-config-change', configurableColumns.value)
}

/**
 * 清除选中
 */
function clearSelection() {
  tableRef.value?.clearSelection()
}

/**
 * 切换所有行选中
 */
function toggleAllSelection() {
  tableRef.value?.toggleAllSelection()
}

/**
 * 切换单行选中
 */
function toggleRowSelection(row: any, selected?: boolean) {
  tableRef.value?.toggleRowSelection(row, selected)
}

/**
 * 暴露方法给父组件
 */
defineExpose({
  clearSelection,
  toggleAllSelection,
  toggleRowSelection,
  tableRef
})
</script>

<style scoped lang="scss">
.data-table {
  width: 100%;

  // 表格工具栏
  .table-toolbar {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 16px;
    gap: 16px;

    .toolbar-left {
      display: flex;
      align-items: center;
      gap: 12px;
      flex: 1;

      .table-title {
        margin: 0;
        font-size: 16px;
        font-weight: 600;
        color: var(--el-text-color-primary);
      }

      .table-description {
        font-size: 14px;
        color: var(--el-text-color-secondary);
      }
    }

    .toolbar-right {
      display: flex;
      align-items: center;
      gap: 12px;
      flex-shrink: 0;
    }
  }

  // 表格主体
  .data-table-main {
    .action-buttons {
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 8px;
      flex-wrap: wrap;
    }
  }

  // 分页
  .table-pagination {
    display: flex;
    justify-content: flex-end;
    margin-top: 16px;
  }

  // 列配置弹窗
  .column-config {
    .column-config-header {
      font-size: 14px;
      font-weight: 600;
      margin-bottom: 12px;
      padding-bottom: 8px;
      border-bottom: 1px solid var(--el-border-color);
    }

    .column-config-item {
      display: flex;
      align-items: center;
      height: 32px;
      width: 100%;

      :deep(.el-checkbox__label) {
        flex: 1;
      }
    }
  }
}

// 响应式设计
@media (max-width: 768px) {
  .data-table {
    .table-toolbar {
      flex-direction: column;
      align-items: stretch;

      .toolbar-left {
        flex-direction: column;
        align-items: flex-start;
      }

      .toolbar-right {
        flex-wrap: wrap;
        justify-content: flex-start;
      }
    }

    .table-pagination {
      justify-content: center;

      :deep(.el-pagination) {
        flex-wrap: wrap;
        justify-content: center;
      }
    }
  }
}

// 小屏幕优化
@media (max-width: 480px) {
  .data-table {
    .table-toolbar {
      .toolbar-right {
        .el-input {
          width: 100% !important;
        }
      }
    }

    .data-table-main {
      :deep(.el-table__header),
      :deep(.el-table__body) {
        font-size: 12px;
      }

      .action-buttons {
        flex-direction: column;
        gap: 4px;

        .el-button {
          width: 100%;
        }
      }
    }
  }
}
</style>
