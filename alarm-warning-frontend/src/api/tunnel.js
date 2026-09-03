import { createModuleHttp, MODULE_PREFIX } from './gateway'
import mock from '@/mock/tunnel'

const http = createModuleHttp(MODULE_PREFIX.platform, { silentErrors: true })

const get = (url, params) => http.get(url, { params })
const send = (method, url, body) => http.request({ method, url, data: body })

const fallback = (promise, mockValue) =>
  Promise.resolve(promise).catch(() => (typeof mockValue === 'function' ? mockValue() : mockValue))

const ok = () => ({ success: true, code: 200, message: 'ok' })

// ---------- 总览 ----------
export const getOverview = () => fallback(get('/tunnel/overview'), mock.overview)
export const getCabins = () => fallback(get('/tunnel/cabins'), mock.cabins)

// ---------- 环境监测 ----------
export const getEnvRealtime = (params) => fallback(get('/tunnel/env/realtime', params), mock.envRealtime)
export const getEnvTrend = (sensorId, points) =>
  fallback(get('/tunnel/env/trend', { sensor_id: sensorId, points }), () => ({
    sensor_id: sensorId,
    points: Array.from({ length: points || 24 }, (_, i) => ({ time: `${String(i).padStart(2, '0')}:00`, value: 20 + Math.round(Math.sin(i / 3) * 50) / 10 })),
  }))
export const getEnvThresholds = () =>
  fallback(get('/tunnel/env/thresholds'), { thresholds: [] })

// ---------- 告警管理 ----------
export const getAlarms = (params) => fallback(get('/tunnel/alarms', params), mock.alarms)
export const getAlarmStats = () => fallback(get('/tunnel/alarms/stats'), mock.overview)
export const ackAlarm = (alarmId) =>
  fallback(send('post', `/tunnel/alarms/${alarmId}/ack`, {}), () => ({ ...mock.ackAlarm, alarm_id: alarmId }))

// ---------- 管线管理 ----------
export const getPipelines = (params) => fallback(get('/tunnel/pipelines', params), mock.pipelines)
export const createPipeline = (body) => fallback(send('post', '/tunnel/pipelines', body), ok)
export const updatePipeline = (id, body) => fallback(send('put', `/tunnel/pipelines/${id}`, body), ok)
export const getConflicts = () => fallback(get('/tunnel/pipelines/conflicts'), { conflicts: [], total: 0 })
export const precheckConflict = (body) => fallback(send('post', '/tunnel/pipelines/conflicts/precheck', body), { conflicts: [], compliant: true })

// ---------- 安防管理 ----------
export const getSecurityOverview = () => fallback(get('/tunnel/security/overview'), mock.securityOverview)
export const getAccessRecords = (limit) => fallback(get('/tunnel/security/access', { limit }), mock.accessRecords)
export const createAccessRecord = (body) => fallback(send('post', '/tunnel/security/access', body), ok)
export const getIntrusions = (limit) => fallback(get('/tunnel/security/intrusions', { limit }), mock.intrusions)
export const getBroadcast = () => fallback(get('/tunnel/security/broadcast'), { broadcasts: [] })
export const testBroadcast = () => fallback(send('post', '/tunnel/security/broadcast/test', {}), ok)

// ---------- 工作流 ----------
export const getWorkflowStatus = () => fallback(get('/tunnel/workflow/status'), { status: 'idle', steps: [] })
export const runWorkflow = (count) => fallback(send('post', '/tunnel/workflow/run', { count }), ok)
