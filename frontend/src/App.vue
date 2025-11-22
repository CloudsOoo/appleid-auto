<template>
  <el-config-provider :locale="zhCn">
    <router-view />
  </el-config-provider>
</template>

<script setup lang="ts">
import { onMounted } from 'vue'
import zhCn from 'element-plus/dist/locale/zh-cn.mjs'
import { useUserStore } from '@/stores'

const userStore = useUserStore()

onMounted(() => {
  // 恢复用户状态
  userStore.restoreFromStorage()
})
</script>

<style>
/* 全局样式重置 */
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

html,
body,
#app {
  width: 100%;
  height: 100%;
}

body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial,
    'Noto Sans', sans-serif, 'Apple Color Emoji', 'Segoe UI Emoji', 'Segoe UI Symbol',
    'Noto Color Emoji';
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

/* Element Plus 样式覆盖 */
.el-button--primary {
  --el-button-bg-color: #409eff;
  --el-button-border-color: #409eff;
  --el-button-hover-bg-color: #66b1ff;
  --el-button-hover-border-color: #66b1ff;
}
</style>
