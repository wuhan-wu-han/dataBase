import axios from 'axios'
import { queryAlerts, queryAlertDetail } from '@/mock/alert'

// 预警服务(alarm-warning-service, 经网关 :8080 → :8085)专用实例。
// 与其它模块一致：后端不可用时静默兜底到 mock，不弹 500 错误提示。
const http = axios.create({
  baseURL: '/api',
  timeout: 10000
})

// 后端统一返回 { code:200, data, message }；成功时解包 data，非 200 直接 reject 交给兜底
http.interceptors.response.use(
  (response) => {
    const res = response.data
    if (res && typeof res === 'object' && 'code' in res) {
      if (res.code === 200) return res.data
      return Promise.reject(new Error(res.message || '业务错误'))
    }
    return res
  },
  (error) => Promise.reject(error)
)

// 兜底：真实请求失败时返回 mock（mockFn 支持函数以按参数生成）
const fallback = (promise, mockFn) =>
  Promise.resolve(promise).catch(() => (typeof mockFn === 'function' ? mockFn() : mockFn))

/**
 * 获取预警事件列表（分页 + 筛选）
 */
export function getAlertList(params) {
  return fallback(http.get('/alerts', { params }), () => queryAlerts(params))
}

/**
 * 获取单个预警事件详情
 */
export function getAlertDetail(id) {
  return fallback(http.get(`/alerts/${id}`), () => queryAlertDetail(id))
}

/**
 * 更新预警事件状态（确认 / 处理 / 关闭）
 */
export function updateAlertStatus(id, status) {
  return fallback(http.patch(`/alerts/${id}/status`, { status }), () => ({
    success: true,
    id,
    alertStatus: status
  }))
}
