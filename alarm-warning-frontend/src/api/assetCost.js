import { createModuleHttp, MODULE_PREFIX } from './gateway'
import mock from '@/mock/assetCost'

const http = createModuleHttp(MODULE_PREFIX.platform, { silentErrors: true })

const get = (url, params) => http.get(url, { params })
const send = (method, url, body, config) => http.request({ method, url, data: body, ...(config || {}) })

const fallback = (promise, mockValue) =>
  Promise.resolve(promise).catch(() => (typeof mockValue === 'function' ? mockValue() : mockValue))

const ok = () => ({ success: true, code: 200, message: 'ok' })
const pickAsset = (id) =>
  (mock.assets.items || []).find((a) => a.asset_id === id) || (mock.assets.items || [])[0]
const pickLcc = (id) => (mock.lccList || []).find((l) => l.analysis_id === id) || mock.lccDetail

// ---------- 总览 ----------
export const getOverview = () => fallback(get('/asset-cost/overview'), mock.overview)

// ---------- 资产管理 ----------
export const getAssets = (params) => fallback(get('/asset-cost/assets', params), mock.assets)
export const getAssetDetail = (id) =>
  fallback(get(`/asset-cost/assets/${id}`), () => {
    const base = mock.assetDetail
    const found = pickAsset(id)
    return found ? { ...base, asset: found } : base
  })
export const createAsset = (body) => fallback(send('post', '/asset-cost/assets', body), ok)
export const deleteAsset = (id) => fallback(send('delete', `/asset-cost/assets/${id}`), ok)
export const reviewAsset = (id, approved, comment) =>
  fallback(send('post', `/asset-cost/assets/${id}/review`, {}, { params: { approved, comment } }), ok)
export const getDepreciation = (id) => fallback(get(`/asset-cost/assets/${id}/depreciation`), mock.depreciation)

// ---------- 费用记录 ----------
export const getCostRecords = (params) => fallback(get('/asset-cost/cost-records', params), mock.costRecords)
export const createCostRecord = (body) => fallback(send('post', '/asset-cost/cost-records', body), ok)
export const deleteCostRecord = (id) => fallback(send('delete', `/asset-cost/cost-records/${id}`), ok)
export const reviewCostRecord = (id, approved) =>
  fallback(send('post', `/asset-cost/cost-records/${id}/review`, {}, { params: { approved } }), ok)

// ---------- 成本分析 ----------
export const getCostAnalysis = () => fallback(get('/asset-cost/cost-analysis'), mock.costAnalysis)

// ---------- LCC分析 ----------
export const getLccList = () => fallback(get('/asset-cost/lcc'), mock.lccList)
export const getLccDetail = (id) => fallback(get(`/asset-cost/lcc/${id}`), () => pickLcc(id))
export const runLcc = (body) => fallback(send('post', '/asset-cost/lcc', body), mock.lccDetail)

// ---------- 配置 ----------
export const getCategories = () => fallback(get('/asset-cost/config/categories'), mock.categories)
export const getMaterials = () => fallback(get('/asset-cost/config/materials'), mock.materials)
export const getRegions = () => fallback(get('/asset-cost/config/regions'), mock.regions)
export const getDeprMethods = () => fallback(get('/asset-cost/config/depr-methods'), mock.deprMethods)
