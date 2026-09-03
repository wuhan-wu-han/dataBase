import { createModuleHttp, MODULE_PREFIX } from './gateway'

const http = createModuleHttp(MODULE_PREFIX.platform, { silentErrors: true })

const get = (url, params) => http.get(url, { params })
const send = (method, url, body, config) => http.request({ method, url, data: body, ...(config || {}) })

// 本模块已接入 SQLite 持久化（新增/编辑/删除/分页均真实落库），
// 因此不再回退演示数据：接口异常时由页面 catch 提示，避免把 Mock 当成真实数据。
// 页面对 500/网络错误的兜底展示仍保留（表格显示"暂无工单数据"），不会出现白屏。

// ---------- 总览 ----------
export const getOverview = () => get('/workorder/overview')

// ---------- 工单管理 ----------
export const getOrders = (params) => get('/workorder/orders', params)
export const getOrderStats = () => get('/workorder/orders/stats')
export const getChannels = () => get('/workorder/orders/channels')
export const createOrder = (body) => send('post', '/workorder/orders', body)
export const deleteOrder = (id) => send('delete', `/workorder/orders/${id}`)
export const getOrderDetail = (id) => get(`/workorder/orders/${id}`)

// ---------- 智能派单 ----------
export const getDispatchRecommend = (params) => get('/workorder/dispatch/recommend', params)
export const assignOrder = (body) => send('post', '/workorder/dispatch/assign', body)
export const getDispatchLogs = (limit) => get('/workorder/dispatch/logs', { limit })

// ---------- 运维人员 ----------
export const getStaff = (params) => get('/workorder/staff', params)
export const getStaffWorkload = () => get('/workorder/staff/workload')
export const getStaffDetail = (id) => get(`/workorder/staff/${id}`)

// ---------- 过程跟踪 ----------
export const getProcess = (orderId) => get(`/workorder/process/${orderId}`)
export const advanceProcess = (body) => send('post', '/workorder/process/advance', body)

// ---------- SLA管控 ----------
export const getSlaRules = () => get('/workorder/sla/rules')
export const getSlaMonitor = () => get('/workorder/sla/monitor')
export const escalateOrder = (orderId) =>
  send('post', '/workorder/sla/escalate', {}, { params: { order_id: orderId } })
