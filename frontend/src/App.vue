<template>
  <el-config-provider :locale="zhCn">
    <router-view />
  </el-config-provider>
</template>

<script setup lang="ts">
/**
 * 根组件
 *
 * 功能：
 * - 提供 Element Plus 全局配置（语言、主题等）
 * - 渲染路由视图
 * - 全局状态初始化
 */
import { onMounted } from 'vue'
import { ElConfigProvider } from 'element-plus'
import zhCn from 'element-plus/es/locale/lang/zh-cn'
import { useUserStore } from '@/stores/user'

// 获取用户状态管理
const userStore = useUserStore()

/**
 * 应用初始化
 * - 检查用户登录状态
 * - 恢复用户会话
 */
onMounted(async () => {
  // 尝试恢复用户会话
  const token = localStorage.getItem(import.meta.env.VITE_TOKEN_KEY || 'appleid_access_token')
  if (token) {
    try {
      // 如果有 token，尝试获取用户信息
      await userStore.getUserInfo()
    } catch (error) {
      // 如果获取失败，清除本地存储的 token
      localStorage.removeItem(import.meta.env.VITE_TOKEN_KEY || 'appleid_access_token')
      localStorage.removeItem(import.meta.env.VITE_REFRESH_TOKEN_KEY || 'appleid_refresh_token')
    }
  }
})
</script>

<style lang="scss">
/* 全局样式重置 */
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

html,
body,
#app {
  height: 100%;
  width: 100%;
  font-family: 'Helvetica Neue', Helvetica, 'PingFang SC', 'Hiragino Sans GB',
    'Microsoft YaHei', '微软雅黑', Arial, sans-serif;
}

/* 滚动条样式 */
::-webkit-scrollbar {
  width: 8px;
  height: 8px;
}

::-webkit-scrollbar-track {
  background: #f1f1f1;
  border-radius: 4px;
}

::-webkit-scrollbar-thumb {
  background: #c1c1c1;
  border-radius: 4px;
}

::-webkit-scrollbar-thumb:hover {
  background: #a8a8a8;
}

/* 链接样式 */
a {
  color: inherit;
  text-decoration: none;
}
</style>
