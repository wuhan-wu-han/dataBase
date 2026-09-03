/**
 * GIS 地图数据接口。
 *
 * 职责：把 4 个后端服务的原始业务数据统一转换为标准 GeoJSON FeatureCollection，
 * 并在 properties 上注入前端筛选/展示所需的派生字段（_title / _area / _status / _search）。
 * 地图组件只消费 FeatureCollection，不接触后端原始结构。
 *
 * 数据通道由 VITE_GIS_DEMO_MODE 决定：开启时返回 src/data/gisDemoData.js 中集中维护的
 * 演示数据，关闭后完整恢复真实接口。两条通道共用同一套归一化逻辑，输出结构完全一致。
 *
 * 没有坐标的业务记录仍保留在 records 中供侧栏统计/列表使用，
 * 只有拥有可用坐标的记录才会进入 GeoJSON。
 */
import { MODULE_PREFIX, createModuleHttp } from './gateway'
import { GIS_LAYERS, LAYER_MAP, areaOf, riskLevelOf } from '@/config/gisLayers'
import { GIS_DEMO_DATA } from '@/data/gisDemoData'

/** 临时演示开关：关闭后完整恢复真实 API 数据通道。 */
export const GIS_DEMO_MODE = String(import.meta.env.VITE_GIS_DEMO_MODE || '').trim().toLowerCase() === 'true'

// ---------------------------------------------------------------------------
// 后端响应解包 & 坐标读取
// ---------------------------------------------------------------------------

/** 兼容 {code,data} / {items} / 裸数组 三种返回结构 */
function unwrap(payload) {
  if (Array.isArray(payload)) return payload
  const inner = payload?.data ?? payload
  if (Array.isArray(inner)) return inner
  if (Array.isArray(inner?.items)) return inner.items
  if (Array.isArray(inner?.records)) return inner.records
  if (Array.isArray(inner?.list)) return inner.list
  return []
}

function isLonLat(v) {
  return Array.isArray(v) && v.length >= 2
    && Number.isFinite(Number(v[0])) && Number.isFinite(Number(v[1]))
}

/** 读取点坐标，兼容 coordinates / longitude+latitude / lng+lat 等写法，返回 [lon, lat] */
function readPoint(item) {
  const c = item?.coordinates ?? item?.coord ?? item?.location
  if (isLonLat(c) && !Array.isArray(c[0])) return [Number(c[0]), Number(c[1])]
  if (Array.isArray(c) && isLonLat(c[0])) return [Number(c[0][0]), Number(c[0][1])]
  const lon = Number(item?.longitude ?? item?.lng ?? item?.lon ?? item?.x)
  const lat = Number(item?.latitude ?? item?.lat ?? item?.y)
  if (Number.isFinite(lon) && Number.isFinite(lat)) return [lon, lat]
  return null
}

/** 读取线坐标，返回 [[lon,lat], ...]（至少 2 个点），无有效坐标时返回 null */
function readLine(item) {
  const raw = item?.coordinates ?? item?.points ?? item?.path ?? item?.geometry?.coordinates
  if (!Array.isArray(raw)) return null
  const pts = raw.filter(isLonLat).map((p) => [Number(p[0]), Number(p[1])])
  return pts.length >= 2 ? pts : null
}

// ---------------------------------------------------------------------------
// GeoJSON 归一化
// ---------------------------------------------------------------------------

function buildSearch(props) {
  const parts = []
  for (const value of Object.values(props)) {
    if (value === null || value === undefined) continue
    if (typeof value === 'string' || typeof value === 'number') parts.push(String(value))
  }
  return parts.join(' ').toLowerCase()
}

function makeFeature(cfg, item, geometry, refCoord) {
  const status = cfg.statusOf(item) || 'normal'
  const explicitArea = item.area_name ?? item.areaName ?? item.district ?? item.region ?? item.area_id ?? item.areaId
  const properties = {
    ...item,
    _key: cfg.key,
    _title: cfg.titleOf(item),
    _status: status,
    _risk: riskLevelOf(item, status),
    _area: explicitArea || areaOf(refCoord),
    _coords: refCoord,
    _iconKind: cfg.iconKindOf ? cfg.iconKindOf(item) : 'default'
  }
  properties._search = `${buildSearch(properties)} ${properties._title} ${properties._area}`.toLowerCase()
  return { type: 'Feature', geometry, properties }
}

function toFeatureCollection(cfg, items) {
  const features = []
  for (const item of items) {
    if (!item || typeof item !== 'object') continue
    if (cfg.geometry === 'line') {
      const coords = readLine(item)
      if (!coords) continue
      features.push(makeFeature(cfg, item, { type: 'LineString', coordinates: coords }, coords[Math.floor(coords.length / 2)]))
    } else {
      const coord = readPoint(item)
      if (!coord) continue
      features.push(makeFeature(cfg, item, { type: 'Point', coordinates: coord }, coord))
    }
  }
  return { type: 'FeatureCollection', features }
}

/**
 * 请求真实接口。没有坐标的记录会原样保留，GeoJSON 生成阶段会自然忽略它们。
 * @returns {Promise<{items: Array, available: boolean, error: string}>}
 */
async function loadLayer(prefix, path) {
  if (!prefix || !path) {
    return { items: [], available: false, error: '暂未配置真实数据接口' }
  }
  try {
    const http = createModuleHttp(prefix, { silentErrors: true })
    const payload = await http.get(path)
    const items = unwrap(payload)
    return { items, available: true, error: '' }
  } catch (error) {
    return {
      items: [],
      available: false,
      error: error?.response?.data?.message || error?.response?.data?.detail || error?.message || '接口请求失败'
    }
  }
}

/**
 * 告警本身没有坐标时，仅允许通过完全一致的真实设备编号关联已有点位坐标。
 * 不按区域、标题或序号猜测，避免把告警放到错误位置。
 */
function attachVerifiedAlertCoordinates(alerts, allRecords) {
  const deviceCoords = new Map()
  for (const key of ['asset', 'manhole']) {
    for (const item of allRecords[key] || []) {
      const coord = readPoint(item)
      if (!coord) continue
      const identifiers = [item.asset_code, item.assetCode, item.code, item.device_id, item.deviceId]
      for (const id of identifiers) {
        if (id !== undefined && id !== null && String(id).trim()) deviceCoords.set(String(id).trim(), coord)
      }
    }
  }

  return (alerts || []).map((item) => {
    if (readPoint(item)) return item
    const deviceId = item.device_id ?? item.deviceId
    const coord = deviceId !== undefined && deviceId !== null
      ? deviceCoords.get(String(deviceId).trim())
      : null
    return coord ? { ...item, coordinates: coord, _coordinateSource: 'device' } : item
  })
}

// ---------------------------------------------------------------------------
// 各图层数据源
// ---------------------------------------------------------------------------

const LAYER_SOURCE = {
  // 三类管网服务当前没有返回 LineString/坐标序列的接口，保留图层能力但不伪造线段。
  gas: { prefix: MODULE_PREFIX.gasRisk, path: '/pipelines?page=1&page_size=200' },
  water: { prefix: null, path: null },
  waste: { prefix: null, path: null },
  manhole: { prefix: MODULE_PREFIX.manholeCover, path: '/archive?page=1&page_size=100' },
  hazard: { prefix: MODULE_PREFIX.roadHazard, path: '/cavity?page=1&page_size=100' },
  asset: { prefix: MODULE_PREFIX.gasAsset, path: '/assets?page=1&page_size=200' },
  alert: { prefix: MODULE_PREFIX.alarm, path: '/alerts?page=1&size=200' }
}

async function fetchLayer(key) {
  const cfg = LAYER_MAP[key]
  const src = LAYER_SOURCE[key]
  return loadLayer(src.prefix, src.path)
}

export const fetchGasPipelines = () => fetchLayer('gas')
export const fetchWaterPipelines = () => fetchLayer('water')
export const fetchWastePipelines = () => fetchLayer('waste')
export const fetchManholes = () => fetchLayer('manhole')
export const fetchCavities = () => fetchLayer('hazard')
export const fetchAssets = () => fetchLayer('asset')
export const fetchAlerts = () => fetchLayer('alert')

// ---------------------------------------------------------------------------
// 统一加载：返回 7 个 FeatureCollection + 数据来源元信息
// ---------------------------------------------------------------------------

/**
 * DEMO 通道：不发起任何后端请求，直接把本地演示数据走一遍与真实接口相同的归一化流程，
 * 保证两条通道的输出结构（collections / records / sources）完全一致，
 * 关闭 VITE_GIS_DEMO_MODE 后上层组件无需任何改动。
 */
function buildDemoResult() {
  const collections = {}
  const records = {}
  const sources = {}

  for (const cfg of GIS_LAYERS) {
    const items = Array.isArray(GIS_DEMO_DATA[cfg.key]) ? GIS_DEMO_DATA[cfg.key] : []
    const fc = toFeatureCollection(cfg, items)
    collections[cfg.key] = fc
    records[cfg.key] = items
    sources[cfg.key] = { label: cfg.label, available: true, total: items.length, usable: fc.features.length, error: '' }
  }

  return {
    collections,
    records,
    sources,
    loadedAt: Date.now(),
    failed: [],
    summary: GIS_DEMO_DATA.summary || null
  }
}

/**
 * @returns {Promise<{
 *   collections: Record<string, GeoJSON.FeatureCollection>,
 *   records: Record<string, Array>,
 *   sources: Record<string, {label:string, available:boolean, total:number, usable:number, error:string}>,
 *   loadedAt: number,
 *   failed: string[],
 *   summary?: Object|null
 * }>}
 */
export async function fetchAllLayers() {
  if (GIS_DEMO_MODE) return buildDemoResult()

  const keys = GIS_LAYERS.map((l) => l.key)
  const results = await Promise.allSettled(keys.map((k) => fetchLayer(k)))

  const collections = {}
  const records = {}
  const sources = {}
  const failed = []

  results.forEach((res, i) => {
    const key = keys[i]
    const cfg = LAYER_MAP[key]
    if (res.status !== 'fulfilled') {
      failed.push(cfg.label)
      collections[key] = { type: 'FeatureCollection', features: [] }
      records[key] = []
      sources[key] = { label: cfg.label, available: false, total: 0, usable: 0, error: '接口请求失败' }
      return
    }
    const { items, available, error } = res.value
    const fc = toFeatureCollection(cfg, items)
    collections[key] = fc
    records[key] = items
    sources[key] = { label: cfg.label, available, total: items.length, usable: fc.features.length, error }
    if (!available && srcConfigured(key)) failed.push(cfg.label)
  })

  // 主预警服务目前可能只给设备编号；若编号能与真实设备点位精确匹配，则继承该坐标。
  records.alert = attachVerifiedAlertCoordinates(records.alert, records)
  collections.alert = toFeatureCollection(LAYER_MAP.alert, records.alert)
  if (sources.alert) sources.alert.usable = collections.alert.features.length

  return { collections, records, sources, loadedAt: Date.now(), failed, summary: null }
}

function srcConfigured(key) {
  const src = LAYER_SOURCE[key]
  return !!(src?.prefix && src?.path)
}
