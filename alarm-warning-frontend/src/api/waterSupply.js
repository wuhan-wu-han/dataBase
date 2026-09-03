/**
 * 供水管网精细化管控 API 封装
 * 后端：water_supply_control (FastAPI + SQLite, 端口 8004)
 *
 * 网关路由：/api/water-supply/** → 8004，StripPrefix=2
 * Vite 代理：/api/water-supply/** → 8004 (开发环境直连)
 *
 * 后端直接返回业务 JSON，无 { code:200, data:... } 包裹层。
 * 使用 createModuleHttp（gateway.js），拦截器已直接返回 response.data。
 */
import { createModuleHttp, MODULE_PREFIX } from './gateway'

const http = createModuleHttp(MODULE_PREFIX.waterSupply)

const get = (url, params) => http.get(url, { params })
const send = (method, url, body) =>
  http.request({ method, url, data: body })

// ---------- 大屏汇总 ----------
export const fetchSummary = () => get('/api/summary')

// ============================================================================
// 功能 1：实时运行监测 /api/monitor
// ============================================================================

// 采集监测数据
export const collectMonitorData = (body) => send('post', '/api/monitor/data', body)

// 全部管网实时监测指标
export const fetchMonitorLatest = (params = {}) =>
  get('/api/monitor/latest', params)

// 单管段监测历史
export const fetchMonitorHistory = (pipeId) =>
  get('/api/monitor/history', { pipe_id: pipeId })

// 管网告警列表（分页）
export const fetchMonitorAlarms = (params = {}) =>
  get('/api/monitor/alarms', params)

// 告警处理
export const handleAlarm = (alarmId, status = '已处理') =>
  send('post', `/api/monitor/alarms/${alarmId}/handle`, null)

// 告警趋势（近 7 日）
export const fetchAlarmTrend = () => get('/api/monitor/alarm-trend')

// 监测统计
export const fetchMonitorStats = () => get('/api/monitor/stats')

// ============================================================================
// 功能 2：DMA 分区漏损管理 /api/dma
// ============================================================================

// DMA 分区列表
export const fetchDmaZones = (params = {}) =>
  get('/api/dma/zones', params)

// 分区计量历史记录
export const fetchDmaRecords = (dmaId, days = 7) =>
  get('/api/dma/records', { dma_id: dmaId, days })

// 录入分区计量数据（自动核算漏损率）
export const createDmaRecord = (body) =>
  send('post', '/api/dma/records', body)

// DMA 统计
export const fetchDmaStats = () => get('/api/dma/stats')

// 暗漏点位精准定位
export const locateDarkLeak = (zoneId, location) =>
  send('post', `/api/dma/zones/${zoneId}/locate`, { location })

// ============================================================================
// 功能 3：水质全流程溯源 /api/quality
// ============================================================================

// 全链路节点及最新水质
export const fetchQualityChain = () => get('/api/quality/chain')

// 节点水质历史记录
export const fetchQualityRecords = (nodeId, limit = 30) =>
  get('/api/quality/records', { node_id: nodeId, limit })

// 录入节点水质
export const collectQualityData = (body) =>
  send('post', '/api/quality/data', body)

// 水质统计
export const fetchQualityStats = () => get('/api/quality/stats')

// ============================================================================
// 功能 4：智能压力调度 /api/pressure
// ============================================================================

// 泵站列表
export const fetchPressureStations = () => get('/api/pressure/stations')

// 生成压力调度方案
export const createPressurePlan = (body) =>
  send('post', '/api/pressure/plan', body)

// 调度方案历史
export const fetchPressurePlans = (stationId = 0) =>
  get('/api/pressure/plans', { station_id: stationId })

// 执行调度方案
export const applyPressurePlan = (planId) =>
  send('post', `/api/pressure/plans/${planId}/apply`)

// 压力调度统计
export const fetchPressureStats = () => get('/api/pressure/stats')

// ============================================================================
// 功能 5：二次供水管控 /api/secondary
// ============================================================================

// 二次供水单元列表
export const fetchSecondaryUnits = (params = {}) =>
  get('/api/secondary/units', params)

// 上报二次供水实时数据
export const collectSecondaryData = (body) =>
  send('post', '/api/secondary/data', body)

// 二次供水统计
export const fetchSecondaryStats = () => get('/api/secondary/stats')

// ============================================================================
// 功能 6：消防栓专项管理 /api/hydrant
// ============================================================================

// 消防栓列表（分页）
export const fetchHydrants = (params = {}) =>
  get('/api/hydrant/list', params)

// 消防栓下拉选项
export const fetchHydrantOptions = () => get('/api/hydrant/options')

// 新增消防栓
export const createHydrant = (body) => send('post', '/api/hydrant', body)

// 编辑消防栓
export const updateHydrant = (hydrantId, body) =>
  send('put', `/api/hydrant/${hydrantId}`, body)

// 出水测试
export const testHydrant = (hydrantId, body) =>
  send('post', `/api/hydrant/${hydrantId}/test`, body)

// 消防栓事件记录
export const fetchHydrantEvents = (hydrantId) =>
  get(`/api/hydrant/${hydrantId}/events`)

// 消防栓统计
export const fetchHydrantStats = () => get('/api/hydrant/stats/summary')

// ============================================================================
// 功能 7：爆管影响分析 /api/burst
// ============================================================================

// 爆管案例列表
export const fetchBurstCases = (params = {}) =>
  get('/api/burst/cases', params)

// 爆管风险预判（自动生成关阀方案）
export const predictBurst = (pipeId) =>
  send('post', '/api/burst/predict', null)

// 关阀方案详情
export const fetchBurstValves = (caseId) =>
  get(`/api/burst/${caseId}/valves`)

// 爆管处置状态流转
export const handleBurst = (caseId, body) =>
  send('post', `/api/burst/${caseId}/handle`, body)

// 爆管统计
export const fetchBurstStats = () => get('/api/burst/stats/summary')
