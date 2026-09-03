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
  return [
    {
      id: 'GP-001', name: '沿河燃气主干线', pressure: '0.52', diameter: 300,
      risk_level: '低', status: '正常', is_main: true,
      coordinates: [[109.176, 36.548], [109.192, 36.552], [109.209, 36.550], [109.226, 36.556], [109.246, 36.553], [109.267, 36.558]]
    },
    {
      id: 'GP-002', name: '城北燃气支线', pressure: '0.38', diameter: 160,
      risk_level: '低', status: '正常',
      coordinates: [[109.209, 36.550], [109.207, 36.563], [109.213, 36.575], [109.211, 36.588]]
    },
    {
      id: 'GP-003', name: '城南燃气支线', pressure: '0.41', diameter: 180,
      risk_level: '中', status: '正常',
      coordinates: [[109.226, 36.556], [109.231, 36.544], [109.229, 36.532], [109.236, 36.519]]
    },
    {
      id: 'GP-004', name: '工业园燃气管段', pressure: '0.63', diameter: 250,
      risk_level: '高', status: '告警',
      coordinates: [[109.246, 36.553], [109.257, 36.548], [109.270, 36.551], [109.279, 36.546]]
    },
    {
      id: 'GP-005', name: '西片区燃气支线', pressure: '0.35', diameter: 150,
      risk_level: '低', status: '正常',
      coordinates: [[109.192, 36.552], [109.184, 36.562], [109.173, 36.568]]
    }
  ]
}

function mockWaterPipelines() {
  return [
    {
      id: 'WP-001', name: '中心城区供水主干线', diameter: 400, pressure: '0.34', status: '正常', is_main: true,
      coordinates: [[109.181, 36.536], [109.198, 36.541], [109.216, 36.540], [109.235, 36.545], [109.254, 36.541]]
    },
    {
      id: 'WP-002', name: '北片区供水支线', diameter: 180, pressure: '0.28', status: '正常',
      coordinates: [[109.216, 36.540], [109.220, 36.552], [109.218, 36.565], [109.224, 36.579]]
    },
    {
      id: 'WP-003', name: '东片区供水支线', diameter: 160, pressure: '0.26', status: '维护中',
      coordinates: [[109.235, 36.545], [109.247, 36.550], [109.260, 36.548], [109.272, 36.554]]
    },
    {
      id: 'WP-004', name: '西片区供水支线', diameter: 150, pressure: '0.25', status: '正常',
      coordinates: [[109.198, 36.541], [109.191, 36.531], [109.179, 36.525], [109.169, 36.528]]
    }
  ]
}

function mockWastePipelines() {
  return [
    {
      id: 'WW-001', name: '沿河污水主干线', flow_rate: '32.4', diameter: 350, status: '正常', is_main: true,
      coordinates: [[109.184, 36.526], [109.201, 36.530], [109.219, 36.527], [109.238, 36.533], [109.258, 36.530]]
    },
    {
      id: 'WW-002', name: '城区污水支线', flow_rate: '18.7', diameter: 180, status: '正常',
      coordinates: [[109.219, 36.527], [109.216, 36.539], [109.222, 36.550]]
    },
    {
      id: 'WW-003', name: '东南片区污水支线', flow_rate: '21.2', diameter: 200, status: '正常',
      coordinates: [[109.238, 36.533], [109.247, 36.522], [109.260, 36.516], [109.271, 36.520]]
    }
  ]
}

function mockManholes() {
  const points = [
    [109.192, 36.552], [109.209, 36.550], [109.226, 36.556], [109.246, 36.553],
    [109.198, 36.541], [109.216, 36.540], [109.235, 36.545], [109.254, 36.541],
    [109.201, 36.530], [109.219, 36.527], [109.238, 36.533], [109.258, 36.530]
  ]
  return points.map((coordinates, i) => ({
    id: `MH-${String(i + 1).padStart(3, '0')}`,
    name: `智能井盖 #${i + 1}`,
    type: ['燃气', '供水', '排水'][i % 3],
    status: i === 9 ? '异常' : '正常',
    coordinates
  }))
}

function mockCavities() {
  const rows = [
    ['低风险', '4.6', '城西支路北侧', '55', [109.185, 36.558]],
    ['低风险', '6.1', '中心街西段', '60', [109.204, 36.548]],
    ['中风险', '15.8', '中心街东段', '95', [109.229, 36.551]],
    ['低风险', '7.4', '河滨路南段', '70', [109.242, 36.529]],
    ['高风险', '31.2', '工业园入口', '145', [109.263, 36.550]],
    ['低风险', '5.2', '城北连接线', '50', [109.216, 36.571]],
    ['中风险', '18.5', '东南片区支路', '105', [109.253, 36.520]],
    ['极高风险', '43.8', '工业园东侧道路', '180', [109.274, 36.547]]
  ]
  return rows.map(([risk_level, settlement, location, impact_radius, coordinates], i) => ({
    id: `RH-${String(i + 1).padStart(3, '0')}`,
    risk_level, settlement, location, impact_radius, coordinates
  }))
}

function mockAssets() {
  const types = ['气体传感器', '摄像头', '气体探测器', '通风设备']
  const points = [
    [109.187, 36.550], [109.198, 36.552], [109.209, 36.550], [109.220, 36.553],
    [109.231, 36.554], [109.242, 36.554], [109.253, 36.550], [109.263, 36.555],
    [109.207, 36.563], [109.213, 36.575], [109.231, 36.544], [109.229, 36.532],
    [109.198, 36.541], [109.219, 36.527], [109.247, 36.522]
  ]
  return points.map((coordinates, i) => ({
    id: `AS-${String(i + 1).padStart(3, '0')}`,
    device_type: types[i % types.length],
    online_status: i === 6 ? '故障' : i === 10 ? '离线' : '在线',
    asset_status: i === 10 ? '维护中' : '正常',
    coordinates
  }))
}

function mockAlerts() {
  const levels = ['blue', 'blue', 'yellow', 'blue', 'orange', 'yellow', 'blue', 'yellow', 'orange', 'red']
  const labels = { blue: '蓝色预警', yellow: '黄色预警', orange: '橙色预警', red: '红色预警' }
  const devices = ['PRESSURE', 'TEMPERATURE', 'GAS', 'FLOW']
  const points = [
    [109.190, 36.551], [109.205, 36.550], [109.218, 36.553], [109.233, 36.554], [109.260, 36.550],
    [109.210, 36.567], [109.231, 36.538], [109.245, 36.530], [109.267, 36.552], [109.276, 36.547]
  ]
  const baseTime = Date.parse('2026-09-03T09:00:00+08:00')
  return points.map((coordinates, i) => {
    const level = levels[i]
    return {
      id: `AL-${String(i + 1).padStart(3, '0')}`,
      warning_level: level,
      warning_label: labels[level],
      device_type: devices[i % devices.length],
      area_id: `AREA-${String((i % 4) + 1).padStart(2, '0')}`,
      description: `区域 ${['A', 'B', 'C', 'D'][i % 4]} 监测异常`,
      event_time: new Date(baseTime - i * 3600_000).toISOString().slice(0, 19).replace('T', ' '),
      coordinates
    }
  })
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
