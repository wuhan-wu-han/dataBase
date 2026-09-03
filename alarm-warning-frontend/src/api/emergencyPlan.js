import { createModuleHttp, MODULE_PREFIX } from './gateway'
import mock from '@/mock/emergencyPlan'

const http = createModuleHttp(MODULE_PREFIX.platform, { silentErrors: true })

const get = (url, params) => http.get(url, { params })
const send = (method, url, body) => http.request({ method, url, data: body })

const fallback = (promise, mockValue) =>
  Promise.resolve(promise).catch(() => (typeof mockValue === 'function' ? mockValue() : mockValue))

const ok = () => ({ success: true, code: 200, message: 'ok' })
const pickPlan = (id) => (mock.plans.plans || []).find((p) => p.plan_id === id) || mock.planDetail

// ---------- 总览 ----------
export const getOverview = () => fallback(get('/plan/overview'), mock.overview)
export const getCategories = () => fallback(get('/plan/categories'), mock.categories)

// ---------- 预案 CRUD ----------
export const getPlans = (params) => fallback(get('/plan/plans', params), mock.plans)
export const createPlan = (body) => fallback(send('post', '/plan/plans', body), ok)
export const getPlanDetail = (planId) => fallback(get(`/plan/plans/${planId}`), () => pickPlan(planId))
export const updatePlan = (planId, body) => fallback(send('put', `/plan/plans/${planId}`, body), ok)
export const deletePlan = (planId) => fallback(send('delete', `/plan/plans/${planId}`), ok)

// ---------- 流程节点 ----------
export const addNode = (planId, body) => fallback(send('post', `/plan/plans/${planId}/nodes`, body), ok)
export const updateNode = (planId, nodeId, body) => fallback(send('put', `/plan/plans/${planId}/nodes/${nodeId}`, body), ok)
export const deleteNode = (planId, nodeId) => fallback(send('delete', `/plan/plans/${planId}/nodes/${nodeId}`), ok)

// ---------- 智能匹配 ----------
export const matchPlans = (body) => fallback(send('post', '/plan/match', body), mock.matchResult)
export const getLiveMatches = (limit) => fallback(get('/plan/match/live', { limit }), mock.liveMatches)

// ---------- 演练与激活 ----------
export const runDrill = (body) => fallback(send('post', '/plan/drill', body), mock.drillResult)
export const activatePlan = (body) => fallback(send('post', '/plan/activate', body), ok)
export const getActivations = (params) => fallback(get('/plan/activations', params), mock.activations)
export const markNodeDone = (activationId, nodeId) =>
  fallback(send('post', `/plan/activations/${activationId}/nodes/${nodeId}/done`, {}), { progress: 100, success: true })
export const finishActivation = (activationId) => fallback(send('post', `/plan/activations/${activationId}/finish`, {}), ok)
