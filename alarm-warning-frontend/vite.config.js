import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { fileURLToPath, URL } from 'node:url'

export default defineConfig({
  plugins: [vue()],

  server: {
    host: '0.0.0.0',
    port: 5173,
    // 开发环境统一通过 api-gateway:8080 转发到各子服务
    // 生产环境由 Nginx 反向代理实现，前端使用相对路径 /api/...
    proxy: {
      // 认证服务独立开发端口；容器部署时由 Nginx 转发至 platform-api:8000
      '/auth': {
        target: process.env.VITE_AUTH_TARGET || 'http://127.0.0.1:18001',
        changeOrigin: true
      },
      // 本地开发：/api/platform/** 直连 Python 综合服务(:8000)，
      // 后端已注册 /api/platform 前缀，Vite 代理直接透传，无需 rewrite
      '/api/platform': {
        target: 'http://localhost:8000',
        changeOrigin: true
      },
      // 市政井盖管控：直连 8005，去掉 /api/manhole-cover 前缀
      '/api/manhole-cover': {
        target: 'http://localhost:8005',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api\/manhole-cover/, '')
      },
      // 供水管网管控：直连 8004，去掉 /api/water-supply 前缀
      '/api/water-supply': {
        target: 'http://localhost:8004',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api\/water-supply/, '')
      },
      // 队友子服务直连（跳过 Java 网关 :8080），StripPrefix=2 去掉 /api/{服务名} 前缀
      '/api/gas-asset': {
        target: 'http://localhost:8001',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api\/gas-asset/, '')
      },
      '/api/road-hazard': {
        target: 'http://localhost:8002',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api\/road-hazard/, '')
      },
      '/api/gas-risk': {
        target: 'http://localhost:8003',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api\/gas-risk/, '')
      },
      '/api/water-supply': {
        target: 'http://localhost:8004',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api\/water-supply/, '')
      },
      // 其余 /api/**（预警等）仍走网关 :8080
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
