/**
 * 统一网关配置
 * 所有子模块 API 通过 api-gateway:8080 转发，避免直连后端端口
 *
 * 网关路由规则（application.yml）：
 *   /api/alert/**        → 8085  alarm-warning-service
 *   /api/gas-risk/**     → 8003  gas_risk_control
 *   /api/gas-asset/**    → 8001  gas_asset_manage
 *   /api/road-hazard/**  → 8002  road_hazard_control
 *
 * StripPrefix=2 剥掉前两段 /api/{服务名}，后端原路径保持不变
 */
import axios from 'axios'
import { ElMessage } from 'element-plus'
import { authState, clearSession } from '@/stores/auth'

// 网关基础地址（开发环境通过 Vite Proxy 代理到 8080）
export const GATEWAY_BASE = '/api'

// 各子模块网关前缀
export const MODULE_PREFIX = {
  alarm: '/api/alert',          // 主平台预警服务
  gasRisk: '/api/gas-risk',     // 燃气风控
  gasAsset: '/api/gas-asset',   // 资产管理
  roadHazard: '/api/road-hazard', // 道路塌陷
  platform: '/api/platform'     // Python 综合服务（治理/危化品/管廊/预案/成本/工单）
}

/**
 * 创建带统一拦截器的 axios 实例
 * @param {string} prefix - 模块前缀（见 MODULE_PREFIX）
 * @param {{ silentErrors?: boolean }} options - silentErrors=true 时不弹出全局错误提示，
 *        由调用方（API 层）自行降级到 Mock 数据，避免页面出现"系统内部错误/AxiosError"
 * @returns {import('axios').AxiosInstance}
 */
export function createModuleHttp(prefix, options = {}) {
  const silentErrors = !!options.silentErrors
  const instance = axios.create({
    baseURL: prefix,
    timeout: 15000
  })

  // 请求拦截器：可在此注入 token 等
  instance.interceptors.request.use(
    (config) => { if (authState.token) config.headers.Authorization = `Bearer ${authState.token}`; return config },
    (error) => Promise.reject(error)
  )

  // 响应拦截器：统一错误提示
  instance.interceptors.response.use(
    (response) => response.data,
    (error) => {
      if (error.response?.status === 401) { clearSession(); if (window.location.pathname !== '/login') window.location.assign('/login') }
      if (!silentErrors) {
        const message = error.response?.data?.detail
          || error.response?.data?.message
          || error.message
          || '请求失败'
        ElMessage.error(message)
      }
      // 始终 reject，交由 API 层 catch 后降级为 Mock 数据
      return Promise.reject(error)
    }
  )

  return instance
}
