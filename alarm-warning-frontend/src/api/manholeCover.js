/**
 * 市政井盖全生命周期管控 API 封装
 * 后端：manhole_cover_control (FastAPI + SQLite, 端口 8005)
 *
 * 网关路由：/api/manhole-cover/** → 8005，StripPrefix=2
 * Vite 代理：/api/manhole-cover/** → 8005 (开发环境直连)
 *
 * 后端直接返回业务 JSON，无 { code:200, data:... } 包裹层。
 * 使用 createModuleHttp（gateway.js），拦截器已直接返回 response.data。
 */
import { createModuleHttp, MODULE_PREFIX } from './gateway'

const http = createModuleHttp(MODULE_PREFIX.manholeCover)

const get = (url, params) => http.get(url, { params })
const send = (method, url, body) =>
  http.request({ method, url, data: body })

// ---------- 大屏汇总 ----------
export const fetchSummary = () => get('/api/summary')

// ============================================================================
// 功能 1：状态实时监测 /api/monitor
// ============================================================================

// 全部井盖实时监测指标
export const fetchMonitorLatest = (params = {}) =>
  get('/api/monitor/latest', params)

// 单井盖监测历史曲线
export const fetchMonitorHistory = (manholeId, limit = 100) =>
  get('/api/monitor/history', { manhole_id: manholeId, limit })

// 风险告警记录列表（分页）
export const fetchMonitorAlarms = (params = {}) =>
  get('/api/monitor/alarms', params)

// 告警趋势（近 7 日 × 等级）
export const fetchAlarmTrend = () => get('/api/monitor/alarm-trend')

// 监测与告警统计
export const fetchMonitorStats = () => get('/api/monitor/stats')

// 采集监测数据（异常自动告警）
export const collectMonitorData = (body) => send('post', '/api/monitor/data', body)

// ============================================================================
// 功能 2：一井一档数字档案 /api/archive
// ============================================================================

// 井盖档案列表（分页 + 多条件查询）
export const fetchManholes = (params = {}) => get('/api/archive', params)

// 下拉选项
export const fetchArchiveOptions = () => get('/api/archive/options')

// 档案统计
export const fetchArchiveStats = () => get('/api/archive/stats')

// 井盖档案详情（含履历）
export const fetchManholeDetail = (manholeId) =>
  get(`/api/archive/${manholeId}`)

// 新增井盖档案
export const createManhole = (body) => send('post', '/api/archive', body)

// 编辑井盖档案
export const updateManhole = (manholeId, body) =>
  send('put', `/api/archive/${manholeId}`, body)

// 登记维修/更换履历
export const addRepairRecord = (manholeId, body) =>
  send('post', `/api/archive/${manholeId}/repairs`, body)

// ============================================================================
// 功能 3：隐患闭环处置 /api/orders
// ============================================================================

// 运维工单列表（分页）
export const fetchOrders = (params = {}) => get('/api/orders', params)

// 工单统计与闭环率
export const fetchOrderStats = () => get('/api/orders/stats')

// 工单详情
export const fetchOrderDetail = (orderId) => get(`/api/orders/${orderId}`)

// 派发工单
export const dispatchOrder = (orderId, body) =>
  send('post', `/api/orders/${orderId}/dispatch`, body)

// 现场处置信息上报
export const reportOrder = (orderId, body) =>
  send('post', `/api/orders/${orderId}/report`, body)

// 整改结果核验
export const verifyOrder = (orderId, body) =>
  send('post', `/api/orders/${orderId}/verify`, body)

// 隐患闭环销号归档
export const closeOrder = (orderId) =>
  send('post', `/api/orders/${orderId}/close`)

// ============================================================================
// 功能 4：被盗追踪管理 /api/theft
// ============================================================================

// 被盗案件列表
export const fetchTheftCases = () => get('/api/theft/cases')

// 异动轨迹回放
export const fetchTheftTracks = (manholeId) =>
  get('/api/theft/tracks', { manhole_id: manholeId })

// 上报异动轨迹点
export const addTheftTrack = (body) => send('post', '/api/theft/tracks', body)

// 最新位置定位追踪
export const locateManhole = (manholeId) =>
  get(`/api/theft/locate/${manholeId}`)

// 公安联动处置记录列表
export const fetchPoliceRecords = (params = {}) =>
  get('/api/theft/police', params)

// 新增公安联动记录
export const createPoliceRecord = (body) =>
  send('post', '/api/theft/police', body)

// 更新公安处置进展
export const updatePoliceRecord = (recordId, params = {}) =>
  http.put(`/api/theft/police/${recordId}`, null, { params })

// ============================================================================
// 功能 5：防坠网台账管理 /api/safety-net
// ============================================================================

// 防坠网台账列表（分页）
export const fetchSafetyNets = (params = {}) =>
  get('/api/safety-net', params)

// 防坠网统计
export const fetchSafetyNetStats = () => get('/api/safety-net/stats')

// 防坠网详情
export const fetchSafetyNetDetail = (netId) =>
  get(`/api/safety-net/${netId}`)

// 防坠网安装登记
export const createSafetyNet = (body) =>
  send('post', '/api/safety-net', body)

// 登记运维记录（破损/维修/更换）
export const maintainSafetyNet = (netId, body) =>
  send('post', `/api/safety-net/${netId}/maintain`, body)
