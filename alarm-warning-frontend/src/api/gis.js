/**
 * GIS 地图数据接口。
 *
 * 职责：把 4 个后端服务的原始业务数据统一转换为标准 GeoJSON FeatureCollection，
 * 并在 properties 上注入前端筛选/展示所需的派生字段（_title / _area / _status / _search）。
 * 地图组件只消费 FeatureCollection，不接触后端原始结构。
 *
 * 每个 fetch 函数返回 { items, mock }：接口不可用或返回数据缺少可用坐标时降级为演示数据，
 * mock=true 用于在工具栏标注数据来源。
 */
import { MODULE_PREFIX, createModuleHttp } from './gateway'
import { GIS_LAYERS, LAYER_MAP, areaOf } from '@/config/gisLayers'

// ---------------------------------------------------------------------------
// 演示数据生成器（安塞区范围内）
// ---------------------------------------------------------------------------

function mockGasPipelines() {
  const stations = [
    { name: '测站A', lon: 109.20, lat: 36.54 },
    { name: '测站B', lon: 109.22, lat: 36.55 },
    { name: '测站C', lon: 109.24, lat: 36.56 },
    { name: '测站D', lon: 109.21, lat: 36.57 },
    { name: '测站E', lon: 109.25, lat: 36.53 }
  ]
  const list = []
  for (let i = 0; i < stations.length - 1; i++) {
    list.push({
      id: `GP-${String(i + 1).padStart(3, '0')}`,
      name: `${stations[i].name}-${stations[i + 1].name}管线`,
      pressure: (0.3 + Math.random() * 0.5).toFixed(2),
      diameter: [150, 200, 300][i % 3],
      risk_level: ['低', '中', '高'][Math.floor(Math.random() * 3)],
      status: Math.random() > 0.15 ? '正常' : '告警',
      coordinates: [
        [stations[i].lon, stations[i].lat],
        [(stations[i].lon + stations[i + 1].lon) / 2, (stations[i].lat + stations[i + 1].lat) / 2 + 0.004],
        [stations[i + 1].lon, stations[i + 1].lat]
      ]
    })
  }
  return list
}

function mockWaterPipelines() {
  const pts = [
    { lon: 109.19, lat: 36.52 }, { lon: 109.22, lat: 36.54 },
    { lon: 109.25, lat: 36.56 }, { lon: 109.23, lat: 36.58 },
    { lon: 109.20, lat: 36.60 }
  ]
  const list = []
  for (let i = 0; i < pts.length - 1; i++) {
    list.push({
      id: `WP-${String(i + 1).padStart(3, '0')}`,
      name: `供水管线 ${i + 1}`,
      diameter: (100 + Math.random() * 300).toFixed(0),
      pressure: (0.2 + Math.random() * 0.3).toFixed(2),
      status: Math.random() > 0.1 ? '正常' : '维护中',
      coordinates: [[pts[i].lon, pts[i].lat], [pts[i + 1].lon, pts[i + 1].lat]]
    })
  }
  return list
}

function mockWastePipelines() {
  const pts = [
    { lon: 109.21, lat: 36.51 }, { lon: 109.23, lat: 36.53 },
    { lon: 109.26, lat: 36.55 }, { lon: 109.24, lat: 36.57 }
  ]
  const list = []
  for (let i = 0; i < pts.length - 1; i++) {
    list.push({
      id: `WW-${String(i + 1).padStart(3, '0')}`,
      name: `废水管线 ${i + 1}`,
      flow_rate: (Math.random() * 50).toFixed(1),
      status: '正常',
      coordinates: [[pts[i].lon, pts[i].lat], [pts[i + 1].lon, pts[i + 1].lat]]
    })
  }
  return list
}

function mockManholes() {
  const list = []
  for (let i = 0; i < 12; i++) {
    list.push({
      id: `MH-${String(i + 1).padStart(3, '0')}`,
      name: `智能井盖 #${i + 1}`,
      type: ['燃气', '供水', '排水'][i % 3],
      status: Math.random() > 0.2 ? '正常' : '异常',
      coordinates: [109.19 + Math.random() * 0.08, 36.50 + Math.random() * 0.08]
    })
  }
  return list
}

function mockCavities() {
  const list = []
  for (let i = 0; i < 8; i++) {
    list.push({
      id: `RH-${String(i + 1).padStart(3, '0')}`,
      risk_level: ['低风险', '中风险', '高风险', '极高风险'][Math.floor(Math.random() * 4)],
      settlement: (Math.random() * 50).toFixed(1),
      location: `安塞路 ${i + 1} #${['北', '南', '东', '西'][i % 4]}`,
      impact_radius: (50 + Math.random() * 200).toFixed(0),
      coordinates: [109.19 + Math.random() * 0.07, 36.53 + Math.random() * 0.05]
    })
  }
  return list
}

function mockAssets() {
  const types = ['气体传感器', '摄像头', '气体探测器', '通风设备']
  const statuses = ['在线', '离线', '故障']
  const list = []
  for (let i = 0; i < 15; i++) {
    list.push({
      id: `AS-${String(i + 1).padStart(3, '0')}`,
      device_type: types[i % types.length],
      online_status: statuses[i % statuses.length],
      asset_status: ['正常', '维护中', '报废'][Math.floor(Math.random() * 3)],
      coordinates: [109.19 + Math.random() * 0.07, 36.53 + Math.random() * 0.05]
    })
  }
  return list
}

function mockAlerts() {
  const levels = [
    { level: 'blue', label: '蓝色预警' },
    { level: 'yellow', label: '黄色预警' },
    { level: 'orange', label: '橙色预警' },
    { level: 'red', label: '红色预警' }
  ]
  const devices = ['PRESSURE', 'TEMPERATURE', 'GAS', 'FLOW']
  const list = []
  for (let i = 0; i < 10; i++) {
    const lvl = levels[Math.floor(Math.random() * levels.length)]
    list.push({
      id: `AL-${String(i + 1).padStart(3, '0')}`,
      warning_level: lvl.level,
      warning_label: lvl.label,
      device_type: devices[i % devices.length],
      area_id: `AREA-${String((i % 4) + 1).padStart(2, '0')}`,
      description: `区域 ${['A', 'B', 'C', 'D'][i % 4]} 监测异常`,
      event_time: new Date(Date.now() - i * 3600_000).toISOString().slice(0, 19).replace('T', ' '),
      coordinates: [109.19 + Math.random() * 0.07, 36.53 + Math.random() * 0.05]
    })
  }
  return list
}

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
  const properties = {
    ...item,
    _key: cfg.key,
    _title: cfg.titleOf(item),
    _status: status,
    _area: areaOf(refCoord),
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
 * 请求真实接口；失败、为空或全部缺少可用坐标时降级为演示数据。
 * @returns {Promise<{items: Array, mock: boolean}>}
 */
async function loadLayer(cfg, prefix, path, mockFn) {
  const fallback = { items: mockFn(), mock: true }
  if (!prefix) return fallback
  try {
    const http = createModuleHttp(prefix, { silentErrors: true })
    const payload = await http.get(path)
    const items = unwrap(payload)
    if (items.length === 0) return fallback
    // 有数据但没有一条能定位到地图上时，仍然降级，避免图层全空
    const fc = toFeatureCollection(cfg, items)
    if (fc.features.length === 0) return fallback
    return { items, mock: false }
  } catch {
    return fallback
  }
}

// ---------------------------------------------------------------------------
// 各图层数据源
// ---------------------------------------------------------------------------

const LAYER_SOURCE = {
  gas: { prefix: MODULE_PREFIX.gasRisk, path: '/pipelines?page=1&page_size=200', mock: mockGasPipelines },
  water: { prefix: null, path: null, mock: mockWaterPipelines },
  waste: { prefix: null, path: null, mock: mockWastePipelines },
  manhole: { prefix: null, path: null, mock: mockManholes },
  hazard: { prefix: MODULE_PREFIX.roadHazard, path: '/cavity?page=1&page_size=200', mock: mockCavities },
  asset: { prefix: MODULE_PREFIX.gasAsset, path: '/assets?page=1&page_size=200', mock: mockAssets },
  alert: { prefix: MODULE_PREFIX.alarm, path: '/alerts?page=1&size=200', mock: mockAlerts }
}

async function fetchLayer(key) {
  const cfg = LAYER_MAP[key]
  const src = LAYER_SOURCE[key]
  return loadLayer(cfg, src.prefix, src.path, src.mock)
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
 * @returns {Promise<{
 *   collections: Record<string, GeoJSON.FeatureCollection>,
 *   sources: Record<string, {label:string, mock:boolean, total:number, usable:number}>,
 *   loadedAt: number,
 *   failed: string[]
 * }>}
 */
export async function fetchAllLayers() {
  const keys = GIS_LAYERS.map((l) => l.key)
  const results = await Promise.allSettled(keys.map((k) => fetchLayer(k)))

  const collections = {}
  const sources = {}
  const failed = []

  results.forEach((res, i) => {
    const key = keys[i]
    const cfg = LAYER_MAP[key]
    if (res.status !== 'fulfilled') {
      failed.push(cfg.label)
      collections[key] = { type: 'FeatureCollection', features: [] }
      sources[key] = { label: cfg.label, mock: true, total: 0, usable: 0 }
      return
    }
    const { items, mock } = res.value
    const fc = toFeatureCollection(cfg, items)
    collections[key] = fc
    sources[key] = { label: cfg.label, mock, total: items.length, usable: fc.features.length }
  })

  return { collections, sources, loadedAt: Date.now(), failed }
}
