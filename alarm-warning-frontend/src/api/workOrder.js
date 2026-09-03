import { createModuleHttp, MODULE_PREFIX } from './gateway'
import mock from '@/mock/workorder'

const http = createModuleHttp(MODULE_PREFIX.platform, { silentErrors: true })

const get = (url, params) => http.get(url, { params })
const send = (method, url, body, config) => http.request({ method, url, data: body, ...(config || {}) })

// 降级封装：接口异常（后端服务不存在 / 500 / 网络错误）时返回 Mock 数据
const fallback = (promise, mockValue) =>
  Promise.resolve(promise).catch(() => (typeof mockValue === 'function' ? mockValue() : mockValue))

const ok = () => ({ success: true, code: 200, message: 'ok' })
const pickOrder = (id) => (mock.orders || []).find((o) => o.order_id === id) || (mock.orders || [])[0]

// ---------- 总览 ----------
export const getOverview = () => fallback(get('/workorder/overview'), mock.overview)

// ---------- 工单管理 ----------
export const getOrders = (params) => fallback(get('/workorder/orders', params), mock.orders)
export const getOrderStats = () => fallback(get('/workorder/orders/stats'), {})
export const getChannels = () => fallback(get('/workorder/orders/channels'), mock.channels)
export const createOrder = (body) => fallback(send('post', '/workorder/orders', body), ok)
export const deleteOrder = (id) => fallback(send('delete', `/workorder/orders/${id}`), ok)
export const getOrderDetail = (id) => fallback(get(`/workorder/orders/${id}`), () => pickOrder(id))

// ---------- 智能派单 ----------
export const getDispatchRecommend = (params) =>
  fallback(get('/workorder/dispatch/recommend', params), mock.dispatchRecommend)
export const assignOrder = (body) => fallback(send('post', '/workorder/dispatch/assign', body), ok)
export const getDispatchLogs = (limit) =>
  fallback(get('/workorder/dispatch/logs', { limit }), { logs: [] })

// ---------- 运维人员 ----------
export const getStaff = (params) => fallback(get('/workorder/staff', params), mock.staff)
export const getStaffWorkload = () => fallback(get('/workorder/staff/workload'), mock.staffWorkload)
export const getStaffDetail = (id) =>
  fallback(get(`/workorder/staff/${id}`), () => (mock.staff.staff || []).find((s) => s.staff_id === id) || (mock.staff.staff || [])[0])

// ---------- 过程跟踪 ----------
export const getProcess = (orderId) => fallback(get(`/workorder/process/${orderId}`), mock.process)
export const advanceProcess = (body) => fallback(send('post', '/workorder/process/advance', body), ok)

// ---------- SLA管控 ----------
export const getSlaRules = () => fallback(get('/workorder/sla/rules'), mock.slaRules)
export const getSlaMonitor = () => fallback(get('/workorder/sla/monitor'), mock.slaMonitor)
export const escalateOrder = (orderId) =>
  fallback(send('post', '/workorder/sla/escalate', {}, { params: { order_id: orderId } }), ok)
