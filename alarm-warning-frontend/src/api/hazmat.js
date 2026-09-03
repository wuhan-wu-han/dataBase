import { createModuleHttp, MODULE_PREFIX } from './gateway'
import { createMockFallback } from '@/utils/mockMode'
import mock from '@/mock/hazmat'

const http = createModuleHttp(MODULE_PREFIX.platform, { silentErrors: true })

const get = (url, params) => http.get(url, { params })
const send = (method, url, body) => http.request({ method, url, data: body })

// TODO(第二阶段): 后端接入真实数据库后删除 fallback 与 @/mock/hazmat
const fallback = createMockFallback('hazmat', '危化品运输安全')

const ok = () => ({ success: true, code: 200, message: 'ok' })
const pick = (arr, id, key = 'id') =>
  (arr || []).find((x) => x[key] === id) || (arr || [])[0]

// ---------- 总览 ----------
export const getOverview = () => fallback(get('/hazmat/overview'), mock.overview)

// ---------- 介质监测 ----------
export const getMedia = (params) => fallback(get('/hazmat/media', params), mock.media)
export const getMediaDetail = (id) =>
  fallback(get(`/hazmat/media/${id}`), () => ({ ...mock.mediaDetail, ...(pick(mock.media.media, id, 'media_id') || {}) }))
export const getMediaAlerts = () =>
  fallback(get('/hazmat/media/alerts'), () => ({ media: (mock.media.media || []).filter((m) => m.status !== 'normal'), total: (mock.media.media || []).filter((m) => m.status !== 'normal').length }))
export const getMediaStats = () => fallback(get('/hazmat/media/stats'), mock.overview)

// ---------- 路径合规 ----------
export const getRoutes = (params) => fallback(get('/hazmat/routes', params), mock.routes)
export const getRouteDetail = (id) =>
  fallback(get(`/hazmat/routes/${id}`), () => ({ ...mock.routeDetail, ...(pick(mock.routes.routes, id, 'route_id') || {}) }))
export const checkRoute = (body) => fallback(send('post', '/hazmat/routes/check', body), mock.routeCheck)
export const getRouteStats = () => fallback(get('/hazmat/routes/stats'), mock.overview)

// ---------- 溯源管理 ----------
export const getTraces = (params) => fallback(get('/hazmat/trace', params), mock.traces)
export const getTraceDetail = (id) =>
  fallback(get(`/hazmat/trace/${id}`), () => ({ ...mock.traceDetail, ...(pick(mock.traces.traces, id, 'trace_id') || {}) }))
export const getTraceChain = (id) =>
  fallback(get(`/hazmat/trace/${id}/chain`), () => ({ ...mock.traceChain, trace_id: id || mock.traceChain.trace_id }))
export const getTraceStats = () => fallback(get('/hazmat/trace/stats'), mock.overview)

// ---------- 腐蚀评估 ----------
export const getSegments = (params) => fallback(get('/hazmat/segments', params), mock.segments)
export const getSegmentDetail = (id) =>
  fallback(get(`/hazmat/segments/${id}`), () => ({ ...mock.corrosionEval, segment_id: id || mock.corrosionEval.segment_id }))
export const evaluateCorrosion = (body) => fallback(send('post', '/hazmat/segments/evaluate', body), mock.corrosionEval)
export const getCorrosionStats = () => fallback(get('/hazmat/segments/stats'), mock.overview)

// ---------- 合规台账 ----------
export const getLedger = (params) => fallback(get('/hazmat/ledger', params), mock.ledger)
export const getLedgerStats = () => fallback(get('/hazmat/ledger/stats'), mock.overview)
export const generateReport = (body) => fallback(send('post', '/hazmat/ledger/report', body), ok)

// ---------- 应急阀门 ----------
export const getValves = (params) => fallback(get('/hazmat/valves', params), mock.valves)
export const getValveDetail = (id) =>
  fallback(get(`/hazmat/valves/${id}`), () => pick(mock.valves.valves, id, 'valve_id'))
export const emergencyShutdown = (body) => fallback(send('post', '/hazmat/emergency/shutdown', body), ok)
export const getEmergencyStats = () => fallback(get('/hazmat/emergency/stats'), mock.overview)
