<template>
  <div class="card-list-view">
    <page-header title="卡密管理">
      <template #extra>
        <el-button type="primary" @click="$router.push('/admin/cards/generate')">
          生成卡密
        </el-button>
      </template>
    </page-header>
    <el-card>
      <el-table :data="cardList" v-loading="loading">
        <el-table-column prop="code" label="卡密" />
        <el-table-column prop="packageName" label="套餐" />
        <el-table-column prop="status" label="状态" />
        <el-table-column prop="usedBy" label="使用者" />
        <el-table-column prop="createdAt" label="创建时间" />
      </el-table>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import PageHeader from '@/components/common/PageHeader.vue'

const loading = ref(false)
const cardList = ref([])
</script>

<style scoped>
.card-list-view {
  padding: 20px;
}
</style>
