/**
 * 道路塌陷 API 封装
 * 迁移自 road_hazard_frontend/src/api/index.ts
 * 所有请求通过 api-gateway:8080 转发到 road_hazard_control:8002
 *
 * 网关路由：/api/road-hazard/** → 8002，StripPrefix=2
 *
 * 注意：后端是 FastAPI，直接返回业务 JSON，无 { code:200, data:... } 包裹层。
 * gateway.js 拦截器已返回 response.data（即后端原始 JSON），
 * 此处直接 return http 调用结果，不再额外解包。
 */
import { createModuleHttp, MODULE_PREFIX } from './gateway'

const http = createModuleHttp(MODULE_PREFIX.roadHazard)

// 统一封装：GET（直接返回后端 JSON，不再解包 .data）
const get = (url, params) => http.get(url, { params })

// 统一封装：POST/PUT（直接返回后端 JSON，不再解包 .data）
const send = (method, url, body) =>
  http.request({ method, url, data: body })

// ---------- 概览 ----------
export const getSummary = () => get('/api/summary')

// ---- 功能1 地下空洞 ----
export const getCavities = (q) => get('/api/cavity', q)
export const getCavityOptions = () => get('/api/cavity/options')
export const getCavityStats = () => get('/api/cavity/stats')
export const createCavity = (form) => send('post', '/api/cavity', form)
export const updateCavity = (id, form) => send('put', `/api/cavity/${id}`, form)

// ---- 功能2 道路沉降 ----
export const getSubsPoints = (q) => get('/api/subsidence/points', q)
export const getSubsHistory = (pointCode) =>
  get('/api/subsidence/history', { point_code: pointCode })
export const addSubsRecord = (form) => send('post', '/api/subsidence/records', form)
export const getSubsOptions = () => get('/api/subsidence/options')
export const getSubsStats = () => get('/api/subsidence/stats')

// ---- 功能3 施工影响评估 ----
export const getConstructions = (q) => get('/api/construction', q)
export const getConstructionOptions = () => get('/api/construction/options')
export const getConstructionStats = () => get('/api/construction/stats')
export const createConstruction = (form) => send('post', '/api/construction', form)
