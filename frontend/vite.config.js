import { defineConfig, loadEnv } from 'vite'
import vue from '@vitejs/plugin-vue'
import path from 'path'

// https://vitejs.dev/config/
export default defineConfig(({ mode }) => {
  // 加载环境变量
  const env = loadEnv(mode, process.cwd(), '')

  return {
    plugins: [vue()],

    // 路径别名配置
    resolve: {
      alias: {
        '@': path.resolve(__dirname, 'src'),
        '@components': path.resolve(__dirname, 'src/components'),
        '@views': path.resolve(__dirname, 'src/pages'),
        '@layouts': path.resolve(__dirname, 'src/layouts'),
        '@api': path.resolve(__dirname, 'src/api'),
        '@utils': path.resolve(__dirname, 'src/utils'),
        '@stores': path.resolve(__dirname, 'src/stores'),
        '@types': path.resolve(__dirname, 'src/types'),
        '@assets': path.resolve(__dirname, 'src/assets'),
        '@styles': path.resolve(__dirname, 'src/styles'),
      }
    },

    // 开发服务器配置
    server: {
      host: '0.0.0.0',
      port: 3000,
      open: true, // 自动打开浏览器
      cors: true, // 允许跨域

      // API 代理配置
      proxy: {
        '/api': {
          target: env.VITE_API_BASE_URL || 'http://localhost:8000',
          changeOrigin: true,
          secure: false,
          // rewrite: (path) => path.replace(/^\/api/, '')
        }
      }
    },

    // 构建配置
    build: {
      outDir: 'dist',
      assetsDir: 'assets',
      sourcemap: mode === 'development', // 开发环境生成 sourcemap

      // 代码分割策略
      rollupOptions: {
        output: {
          // 手动分割代码块
          manualChunks: {
            // Vue 核心库
            'vue-vendor': ['vue', 'vue-router', 'pinia'],
            // Element Plus 组件库
            'element-plus': ['element-plus', '@element-plus/icons-vue'],
            // 工具库
            'utils': ['axios', 'dayjs', 'qrcode'],
          },
          // 分块命名
          chunkFileNames: 'js/[name]-[hash].js',
          entryFileNames: 'js/[name]-[hash].js',
          assetFileNames: '[ext]/[name]-[hash].[ext]',
        }
      },

      // 压缩配置
      minify: 'terser',
      terserOptions: {
        compress: {
          // 生产环境移除 console
          drop_console: mode === 'production',
          drop_debugger: mode === 'production',
        }
      },

      // chunk 大小警告限制（KB）
      chunkSizeWarningLimit: 1000,
    },

    // CSS 配置
    css: {
      preprocessorOptions: {
        scss: {
          additionalData: `@import "@/styles/variables.scss";`,
          javascriptEnabled: true,
        }
      }
    },

    // 依赖优化
    optimizeDeps: {
      include: [
        'vue',
        'vue-router',
        'pinia',
        'element-plus',
        '@element-plus/icons-vue',
        'axios',
        'dayjs',
        'qrcode',
      ]
    },

    // 环境变量前缀
    envPrefix: 'VITE_',
  }
})
