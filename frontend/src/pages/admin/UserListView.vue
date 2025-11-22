<template>
  <div class="user-list-view">
    <page-header title="用户管理" />
    <el-card>
      <el-table :data="userList" v-loading="loading">
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="username" label="用户名" />
        <el-table-column prop="email" label="邮箱" />
        <el-table-column prop="role" label="角色" />
        <el-table-column prop="createdAt" label="注册时间" />
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
const userList = ref([])
</script>

<style scoped>
.user-list-view {
  padding: 20px;
}
</style>
