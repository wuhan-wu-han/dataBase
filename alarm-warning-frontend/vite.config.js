import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { fileURLToPath, URL } from 'node:url'

export default defineConfig({
  plugins: [vue()],

  server: {
    host: '0.0.0.0',
    port: 5173,
    // 微信回复里的模块导航链接经 cpolar 隧道(*.cpolar.top)回访前端；
    // vite 默认拒绝非 localhost 的 Host 头(403)，这里放行自有隧道域的子域通配
    allowedHosts: ['.cpolar.top'],
    // 开发环境统一通过 api-gateway:8080 转发到各子服务
    // 生产环境由 Nginx 反向代理实现，前端使用相对路径 /api/...
    proxy: {
      // 认证路由由 Python 综合服务(:8000)提供；容器部署时由 Nginx 转发至 platform-api:8000
      '/auth': {
        target: process.env.VITE_AUTH_TARGET || 'http://127.0.0.1:8000',
        changeOrigin: true
      },
      // baidu 路由是 :8000 上唯一挂在 /api/platform 前缀下的，直接透传
      '/api/platform/baidu': {
        target: 'http://localhost:8000',
        changeOrigin: true
      },
      // 本地开发：/api/platform/** 直连 Python 综合服务(:8000)。
      // 除 baidu 外该服务的路由都挂在根路径（/hazmat、/governance、/asset-cost…），
      // 与网关 StripPrefix=2 一致，这里同样剥掉 /api/platform 前缀再转发。
      '/api/platform': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api\/platform/, '')
      },
      // 市政井盖管控：直连 8005。后端路由自带 /api 前缀。
      // 两种调用风格都要兼容：GIS(gis.js) 用单前缀 /api/manhole-cover/archive，
      // 模块 api(manholeCover.js，baseURL=/api/manhole-cover) 每调用再拼 /api → /api/manhole-cover/api/archive。
      // 把服务名后多余的 /api 设为可选段，两种都归一到后端的 /api/archive。
      '/api/manhole-cover': {
        target: 'http://localhost:8005',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api\/manhole-cover(\/api)?/, '/api')
      },
      // 供水管网管控：直连 8004，兼容单/双 /api 前缀两种调用风格
      '/api/water-supply': {
        target: 'http://localhost:8004',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api\/water-supply(\/api)?/, '/api')
      },
      // 队友子服务直连（跳过 Java 网关 :8080）。后端路由均带 /api 前缀。
      // rewrite 用可选 (\/api)? 段同时兼容两种前端调用：
      //   单前缀(GIS)：/api/gas-asset/assets  → /api/assets
      //   双前缀(模块 api，baseURL 已含 /api/{服务})：/api/gas-asset/api/assets/summary → /api/assets/summary
      // 此前只剥服务名段会把双前缀变成 /api/api/... 导致 404。
      '/api/gas-asset': {
        target: 'http://localhost:8001',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api\/gas-asset(\/api)?/, '/api')
      },
      '/api/road-hazard': {
        target: 'http://localhost:8002',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api\/road-hazard(\/api)?/, '/api')
      },
      '/api/gas-risk': {
        target: 'http://localhost:8003',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api\/gas-risk(\/api)?/, '/api')
      },
      // 故障预报与寿命预测：由 Python 综合服务(:8000)提供（Java alarm-warning-service 从不启动）。
      // 后端路由自带 /api/failure-predictions 前缀，直接透传、不改写。
      '/api/failure-predictions': {
        target: 'http://localhost:8000',
        changeOrigin: true
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
