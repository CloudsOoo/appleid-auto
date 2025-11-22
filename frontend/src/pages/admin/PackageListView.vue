<template>
  <div class="page-container">
    <PageHeader title="套餐管理" description="管理系统套餐" />

    <el-card>
      <!-- 操作栏 -->
      <div class="toolbar">
        <el-button type="primary" @click="showAddDialog">
          <el-icon><Plus /></el-icon>
          添加套餐
        </el-button>
        <el-button @click="refreshList">
          <el-icon><Refresh /></el-icon>
          刷新
        </el-button>
      </div>

      <!-- 套餐列表 -->
      <el-table :data="packageList" v-loading="loading" stripe>
        <el-table-column prop="name" label="套餐名称" width="150" />
        <el-table-column prop="price" label="价格" width="100">
          <template #default="{ row }">
            ¥{{ row.price }}
          </template>
        </el-table-column>
        <el-table-column prop="duration_days" label="有效期" width="100">
          <template #default="{ row }">
            {{ row.duration_days }} 天
          </template>
        </el-table-column>
        <el-table-column prop="max_accounts" label="账号限制" width="100" />
        <el-table-column prop="max_share_pages" label="分享页限制" width="100" />
        <el-table-column prop="max_unlock_per_day" label="日解锁次数" width="100" />
        <el-table-column prop="is_active" label="状态" width="80">
          <template #default="{ row }">
            <el-tag :type="row.is_active ? 'success' : 'info'">
              {{ row.is_active ? '启用' : '禁用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="150" fixed="right">
          <template #default="{ row }">
            <el-button size="small" @click="editPackage(row)">编辑</el-button>
            <el-button size="small" type="danger" @click="deletePackage(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 添加/编辑套餐对话框 -->
    <el-dialog v-model="dialogVisible" :title="isEdit ? '编辑套餐' : '添加套餐'" width="600px">
      <el-form :model="packageForm" label-width="120px">
        <el-form-item label="套餐名称">
          <el-input v-model="packageForm.name" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="packageForm.description" type="textarea" />
        </el-form-item>
        <el-form-item label="价格 (元)">
          <el-input-number v-model="packageForm.price" :min="0" :precision="2" />
        </el-form-item>
        <el-form-item label="有效期 (天)">
          <el-input-number v-model="packageForm.duration_days" :min="1" />
        </el-form-item>
        <el-form-item label="账号上限">
          <el-input-number v-model="packageForm.max_accounts" :min="0" />
        </el-form-item>
        <el-form-item label="分享页上限">
          <el-input-number v-model="packageForm.max_share_pages" :min="0" />
        </el-form-item>
        <el-form-item label="每日解锁次数">
          <el-input-number v-model="packageForm.max_unlock_per_day" :min="0" />
        </el-form-item>
        <el-form-item label="允许自定义HTML">
          <el-switch v-model="packageForm.allow_custom_html" />
        </el-form-item>
        <el-form-item label="允许批量导入">
          <el-switch v-model="packageForm.allow_batch_import" />
        </el-form-item>
        <el-form-item label="启用状态">
          <el-switch v-model="packageForm.is_active" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="savePackage" :loading="saving">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Refresh } from '@element-plus/icons-vue'
import PageHeader from '@/components/common/PageHeader.vue'
import { getPackageListApi, createPackageApi, updatePackageApi, deletePackageApi } from '@/api/package'

const loading = ref(false)
const saving = ref(false)
const dialogVisible = ref(false)
const isEdit = ref(false)
const packageList = ref<any[]>([])

const defaultForm = {
  id: null as number | null,
  name: '',
  description: '',
  price: 0,
  duration_days: 30,
  max_accounts: 10,
  max_share_pages: 3,
  max_unlock_per_day: 50,
  allow_custom_html: false,
  allow_batch_import: false,
  is_active: true
}

const packageForm = reactive({ ...defaultForm })

// 加载套餐列表
const loadPackageList = async () => {
  loading.value = true
  try {
    const response = await getPackageListApi()
    packageList.value = response.data.items || response.data || []
  } catch (error: any) {
    ElMessage.error(error.response?.data?.message || '加载失败')
  } finally {
    loading.value = false
  }
}

// 刷新列表
const refreshList = () => {
  loadPackageList()
}

// 显示添加对话框
const showAddDialog = () => {
  Object.assign(packageForm, defaultForm)
  isEdit.value = false
  dialogVisible.value = true
}

// 编辑套餐
const editPackage = (pkg: any) => {
  Object.assign(packageForm, pkg)
  isEdit.value = true
  dialogVisible.value = true
}

// 保存套餐
const savePackage = async () => {
  saving.value = true
  try {
    if (isEdit.value && packageForm.id) {
      await updatePackageApi(packageForm.id, packageForm)
      ElMessage.success('套餐已更新')
    } else {
      await createPackageApi(packageForm)
      ElMessage.success('套餐已创建')
    }
    dialogVisible.value = false
    loadPackageList()
  } catch (error: any) {
    ElMessage.error(error.response?.data?.message || '保存失败')
  } finally {
    saving.value = false
  }
}

// 删除套餐
const deletePackage = async (pkg: any) => {
  try {
    await ElMessageBox.confirm(`确定要删除套餐 "${pkg.name}" 吗？`, '确认删除', { type: 'warning' })
    await deletePackageApi(pkg.id)
    ElMessage.success('套餐已删除')
    loadPackageList()
  } catch (error: any) {
    if (error !== 'cancel') {
      ElMessage.error(error.response?.data?.message || '删除失败')
    }
  }
}

onMounted(() => {
  loadPackageList()
})
</script>

<style scoped lang="scss">
.toolbar {
  display: flex;
  gap: 12px;
  margin-bottom: 16px;
}
</style>
