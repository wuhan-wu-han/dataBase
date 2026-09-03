import { createModuleHttp, MODULE_PREFIX } from './gateway'

const http = createModuleHttp(MODULE_PREFIX.platform, { silentErrors: true })

const get = (url, params) => http.get(url, { params })
const send = (method, url, body) => http.request({ method, url, data: body })

// 本模块已接入 SQLite 持久化（新增/编辑/删除/分页均真实落库），
// 因此不再回退演示数据：接口异常时由页面 catch 提示，避免把 Mock 当成真实数据。
// 页面对 500/网络错误的兜底展示仍保留（空表格提示"暂无预案数据"），不会出现白屏。

// ---------- 总览 ----------
export const getOverview = () => get('/plan/overview')
export const getCategories = () => get('/plan/categories')

// ---------- 预案 CRUD ----------
export const getPlans = (params) => get('/plan/plans', params)
export const createPlan = (body) => send('post', '/plan/plans', body)
export const getPlanDetail = (planId) => get(`/plan/plans/${planId}`)
export const updatePlan = (planId, body) => send('put', `/plan/plans/${planId}`, body)
export const deletePlan = (planId) => send('delete', `/plan/plans/${planId}`)

// ---------- 流程节点 ----------
export const addNode = (planId, body) => send('post', `/plan/plans/${planId}/nodes`, body)
export const updateNode = (planId, nodeId, body) => send('put', `/plan/plans/${planId}/nodes/${nodeId}`, body)
export const deleteNode = (planId, nodeId) => send('delete', `/plan/plans/${planId}/nodes/${nodeId}`)

// ---------- 智能匹配 ----------
export const matchPlans = (body) => send('post', '/plan/match', body)
export const getLiveMatches = (limit) => get('/plan/match/live', { limit })

// ---------- 演练与激活 ----------
export const runDrill = (body) => send('post', '/plan/drill', body)
export const activatePlan = (body) => send('post', '/plan/activate', body)
export const getActivations = (params) => get('/plan/activations', params)
export const markNodeDone = (activationId, nodeId) =>
  send('post', `/plan/activations/${activationId}/nodes/${nodeId}/done`, {})
export const finishActivation = (activationId) =>
  send('post', `/plan/activations/${activationId}/finish`, {})
