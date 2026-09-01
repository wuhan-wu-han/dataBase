/**
 * 燃气风控 API 封装
 * 迁移自 gas_risk_frontend/js/api.js
 * 所有请求通过 api-gateway:8080 转发到 gas_risk_control:8003
 *
 * 网关路由：/api/gas-risk/** → 8003，StripPrefix=2
 * 示例：/api/gas-risk/api/monitoring/realtime → 8003:/api/monitoring/realtime
 */
import { createModuleHttp, MODULE_PREFIX } from './gateway'

const http = createModuleHttp(MODULE_PREFIX.gasRisk)

// ============ 公共工具函数 ============

// 毫秒时间戳 → 月-日 时:分:秒
export function fmtTs(ts) {
  if (!ts) return '-'
  const d = new Date(ts)
  const p = (n) => String(n).padStart(2, '0')
  return `${p(d.getMonth() + 1)}-${p(d.getDate())} ${p(d.getHours())}:${p(d.getMinutes())}:${p(d.getSeconds())}`
}

// 毫秒时间戳 → 时:分:秒
export function fmtTime(ts) {
  if (!ts) return '-'
  const d = new Date(ts)
  const p = (n) => String(n).padStart(2, '0')
  return `${p(d.getHours())}:${p(d.getMinutes())}:${p(d.getSeconds())}`
}

// ============ 监测大屏接口 ============

// 传感器列表
export const fetchSensors = () => http.get('/api/monitoring/sensors')

// 实时监测数据
export const fetchRealtime = () => http.get('/api/monitoring/realtime')

// 报警事件列表
export const fetchAlarms = (limit = 30) =>
  http.get('/api/monitoring/alarms', { params: { limit } })

// 模拟泄漏事件
export const simulateLeak = (sensorId, magnitude) =>
  http.post('/api/monitoring/simulate-leak', { sensor_id: sensorId, magnitude })

// 模拟干扰事件
export const simulateDisturbance = (sensorId, magnitude) =>
  http.post('/api/monitoring/simulate-disturbance', { sensor_id: sensorId, magnitude })

// 清除故障
export const clearFaults = () => http.post('/api/monitoring/clear-faults', {})

// ============ 泄漏定位接口 ============

// 演示数据
export const leakDemo = () => http.post('/api/leak/demo', {})

// 基于浓度定位
export const locateByConcentration = (body) =>
  http.post('/api/leak/locate-by-concentration', body)

// 基于压力波定位
export const locateByPressureWave = (body) =>
  http.post('/api/leak/locate-by-pressure-wave', body)

// 泄漏记录
export const fetchLeakRecords = (limit = 15) =>
  http.get('/api/leak/records', { params: { limit } })

// ============ 扩散仿真接口 ============

// 扩散仿真
export const simulateDiffusion = (body) =>
  http.post('/api/diffusion/simulate', body)

// 爆炸范围
export const calculateExplosionRange = (body) =>
  http.post('/api/diffusion/explosion-range', body)

// ============ 第三方破坏接口 ============

// 预警列表
export const fetchThirdPartyWarnings = (limit = 100) =>
  http.get('/api/third-party/warnings', { params: { limit } })

// 事件处理
export const handleThirdPartyEvent = (body) =>
  http.post('/api/third-party/event', body)

// 模拟事件
export const simulateThirdParty = () =>
  http.post('/api/third-party/simulate', {})

// ============ 用户用气安全接口 ============

// 用户列表
export const fetchUsers = () => http.get('/api/user-safety/users')

// 扫描
export const scanUsers = () => http.post('/api/user-safety/scan', {})

// 模拟异常
export const simulateAnomaly = (body) =>
  http.post('/api/user-safety/simulate-anomaly', body)

// ============ 占压隐患接口 ============

// 记录列表
export const fetchOccupationRecords = (params) =>
  http.get('/api/occupation/records', { params })

// 统计
export const fetchOccupationStats = () => http.get('/api/occupation/stats')

// 新增记录
export const createOccupationRecord = (body) =>
  http.post('/api/occupation/records', body)

// ============ 阴极保护接口 ============

// 实时数据
export const fetchCathodicRealtime = () => http.get('/api/cathodic/realtime')

// 评估
export const evaluateCathodic = () => http.get('/api/cathodic/evaluate')

// 模拟数据
export const simulateCathodicData = () =>
  http.post('/api/cathodic/simulate-data', {})

// 录入数据
export const createCathodicData = (body) =>
  http.post('/api/cathodic/data', body)

// ============ 应急联动接口 ============

// 阀门列表
export const fetchValves = () => http.get('/api/emergency/valves')

// 触发应急
export const triggerEmergency = (body) =>
  http.post('/api/emergency/trigger', body)

// 应急事件列表
export const fetchEmergencyEvents = (limit = 20) =>
  http.get('/api/emergency/events', { params: { limit } })
