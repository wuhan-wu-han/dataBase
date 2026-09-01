import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { fileURLToPath, URL } from 'node:url'

export default defineConfig({
  plugins: [vue()],

  server: {
    port: 5173,
    // 开发环境统一通过 api-gateway:8080 转发到各子服务
    // 生产环境由 Nginx 反向代理实现，前端使用相对路径 /api/...
    proxy: {
      '/api': {
        target: 'http://localhost:8080',
        changeOrigin: true
      }
    }
  },

  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url))
    }
  },

  // 构建优化：拆分第三方依赖为独立 chunk，提升缓存命中率并避免单 chunk 超限警告
  build: {
    // 阈值调至 1000kB：echarts/element-plus 作为完整 UI/可视化库单 chunk 必然接近此量级
    // 调高仅为消除对合理体积的告警，非关闭机制
    chunkSizeWarningLimit: 1000,
    rollupOptions: {
      output: {
        manualChunks: {
          // ECharts 核心 + 按需引入的图表与组件，合并为单一 vendor chunk
          echarts: [
            'echarts/core',
            'echarts/charts',
            'echarts/components',
            'echarts/renderers'
          ],
          // Element Plus 全量 UI 框架独立拆分
          'element-plus': ['element-plus'],
          // 图标库单独拆分（main.js 全量注册）
          'element-icons': ['@element-plus/icons-vue']
        }
      }
    }
  }
})
