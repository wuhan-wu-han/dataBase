import { createModuleHttp, MODULE_PREFIX } from './gateway'
import mock from '@/mock/riskAnalysis'

const http = createModuleHttp(MODULE_PREFIX.platform, { silentErrors: true })

const get = (url, params) => http.get(url, { params })
const send = (method, url, body) => http.request({ method, url, data: body })

const fallback = (promise, mockValue) =>
  Promise.resolve(promise).catch(() => (typeof mockValue === 'function' ? mockValue() : mockValue))

const ok = () => ({ success: true, code: 200, message: 'ok' })

// ---------- 总览 ----------
export const getOverview = () => fallback(get('/governance/overview'), mock.overview)

// ---------- 主数据管理 ----------
export const getMasterStats = () => fallback(get('/governance/master/stats'), mock.masterStats)
export const getMasterList = (dataType, params) => fallback(get(`/governance/master/${dataType}`, params), mock.masterList)
export const getMasterItem = (dataType, itemId) =>
  fallback(get(`/governance/master/${dataType}/${itemId}`), () => (mock.masterList.data || [])[0])

// ---------- 数据标准 ----------
export const getStandards = () => fallback(get('/governance/standards'), mock.standards)
export const getStandard = (code) => fallback(get(`/governance/standards/${code}`), () => (mock.standards.standards || [])[0])
export const getCompliance = () => fallback(get('/governance/compliance'), mock.compliance)

// ---------- 数据质量 ----------
export const getQualityReport = () => fallback(get('/governance/quality/report'), mock.qualityReport)
export const runQualityCheck = (body) => fallback(send('post', '/governance/quality/check', body), mock.qualityCheckResult)
export const getQualityAlert = () => fallback(get('/governance/quality/alerts'), { alerts: [] })

// ---------- 时空分析 ----------
export const spatialAnalyze = (body) => fallback(send('post', '/governance/spatial/analyze', body), { results: [] })
export const getTopology = (zone) => fallback(get('/governance/spatial/topology', { zone }), { nodes: [], edges: [] })
export const getPathAnalysis = (zone) => fallback(get('/governance/spatial/path', { zone }), { paths: [] })
export const getBufferAnalysis = (zone, radius_m) => fallback(get('/governance/spatial/buffer', { zone, radius_m }), { results: [] })

// ---------- 统一API服务 ----------
export const getApiServices = (domain) => fallback(get('/governance/api/services', { domain }), mock.apiServices)
export const getApiService = (apiId) =>
  fallback(get(`/governance/api/services/${apiId}`), () => (mock.apiServices.services || [])[0])
export const getApiStats = () => fallback(get('/governance/api/stats'), mock.apiStats)
export const getApiAudit = (limit) => fallback(get('/governance/api/audit', { limit }), { records: [], total: 0 })
