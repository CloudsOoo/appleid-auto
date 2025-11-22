<template>
  <div class="package-list-view">
    <page-header title="套餐管理">
      <template #extra>
        <el-button type="primary" @click="handleAdd">新增套餐</el-button>
      </template>
    </page-header>
    <el-card>
      <el-table :data="packageList" v-loading="loading">
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="name" label="套餐名称" />
        <el-table-column prop="accountLimit" label="账号上限" />
        <el-table-column prop="duration" label="有效期(天)" />
        <el-table-column prop="price" label="价格" />
        <el-table-column label="操作" width="150">
          <template #default>
            <el-button size="small" type="primary">编辑</el-button>
            <el-button size="small" type="danger">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import PageHeader from '@/components/common/PageHeader.vue'

const loading = ref(false)
const packageList = ref([])

const handleAdd = () => {
  // TODO: Open add package dialog
}
</script>

<style scoped>
.package-list-view {
  padding: 20px;
}
</style>
