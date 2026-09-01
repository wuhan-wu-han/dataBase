/**
 * 燃气资产管理 API 封装
 * 迁移自 gas_asset_frontend/src/api/index.ts
 * 所有请求通过 api-gateway:8080 转发到 gas_asset_manage:8001
 *
 * 网关路由：/api/gas-asset/** → 8001，StripPrefix=2
 */
import { createModuleHttp, MODULE_PREFIX } from './gateway'

const http = createModuleHttp(MODULE_PREFIX.gasAsset)

// 统一封装：GET
async function get(url, params) {
  const { data } = await http.get(url, { params })
  return data
}

// 统一封装：POST/PUT
async function send(method, url, body) {
  const { data } = await http.request({ method, url, data: body })
  return data
}

export const EXPORT_URL = `${MODULE_PREFIX.gasAsset}/api/assets/export`

// ---------- 功能 1：资产全景台账 ----------
export const fetchSummary = () => get('/api/assets/summary')
export const fetchStats = () => get('/api/assets/stats')
export const fetchOptions = () => get('/api/assets/options')
export const fetchAssets = (params) => get('/api/assets', params)
export const fetchAssetDetail = (id) => get(`/api/assets/${id}`)

// ---------- 功能 2：全生命周期档案 ----------
export const fetchLifecycleStages = () => get('/api/lifecycle/stages')
export const fetchLifecycleTimeline = (assetId) => get(`/api/lifecycle/${assetId}`)
export const fetchLifecycleRecords = (params) => get('/api/lifecycle', params)
export const createLifecycle = (body) => send('post', '/api/lifecycle', body)
export const updateLifecycle = (id, body) => send('put', `/api/lifecycle/${id}`, body)

// ---------- 功能 3：资产盘点 ----------
export const fetchInventoryStats = () => get('/api/inventory/stats')
export const fetchInventoryTasks = () => get('/api/inventory/tasks')
export const createInventoryTask = (body) => send('post', '/api/inventory/tasks', body)
export const scanCheck = (taskId, asset_code) =>
  send('post', `/api/inventory/tasks/${taskId}/scan`, { asset_code })
export const patrolCheck = (taskId) =>
  send('post', `/api/inventory/tasks/${taskId}/patrol`)
export const handleDiffItem = (itemId, handle_status, remark) =>
  send('put', `/api/inventory/items/${itemId}`, { handle_status, remark })
export const finishInventoryTask = (taskId) =>
  send('post', `/api/inventory/tasks/${taskId}/finish`)
export const fetchDiffList = (params) => get('/api/inventory/diff', params)

// ---------- 功能 4：资产权属管理 ----------
export const fetchOwnershipStats = () => get('/api/ownership/stats')
export const fetchOwnershipMatrix = () => get('/api/ownership/matrix')
export const fetchUnclearAssets = () => get('/api/ownership/unclear')
export const fetchOwnership = (assetId) => get(`/api/ownership/${assetId}`)
export const updateOwnership = (assetId, body) =>
  send('put', `/api/ownership/${assetId}`, body)
