/**
 * GIS 地图数据接口
 * 优先调用真实后端 API，失败时回退到 Mock 数据
 */
import { MODULE_PREFIX, createModuleHttp } from './gateway'

// ---------------------------------------------------------------------------
// Mock 数据生成器
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
      risk_level: ['低', '中', '高'][Math.floor(Math.random() * 3)],
      status: Math.random() > 0.15 ? '正常' : '告警',
      coordinates: [
        [stations[i].lon, stations[i].lat],
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
      status: '正常',
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
      id: `WPW-${String(i + 1).padStart(3, '0')}`,
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
    { level: 'blue', label: '蓝色预警', color: '#0071E3' },
    { level: 'yellow', label: '黄色预警', color: '#FFCC00' },
    { level: 'orange', label: '橙色预警', color: '#FF9500' },
    { level: 'red', label: '红色预警', color: '#FF3B30' }
  ]
  const list = []
  for (let i = 0; i < 10; i++) {
    const lvl = levels[Math.floor(Math.random() * levels.length)]
    list.push({
      id: `AL-${String(i + 1).padStart(3, '0')}`,
      warning_level: lvl.level,
      warning_label: lvl.label,
      color: lvl.color,
      description: `区域 ${['A', 'B', 'C', 'D'][i % 4]} 监测异常`,
      coordinates: [109.19 + Math.random() * 0.07, 36.53 + Math.random() * 0.05]
    })
  }
  return list
}

// ---------------------------------------------------------------------------
// API 调用函数
// ---------------------------------------------------------------------------

export async function fetchGasPipelines() {
  try {
    const http = createModuleHttp(MODULE_PREFIX.gasRisk, { silentErrors: true })
    const data = await http.get('/pipelines?page=1&page_size=100')
    const list = data?.items ?? data ?? []
    return Array.isArray(list) && list.length > 0 ? list : mockGasPipelines()
  } catch { return mockGasPipelines() }
}

export async function fetchWaterPipelines() {
  return mockWaterPipelines()
}

export async function fetchWastePipelines() {
  return mockWastePipelines()
}

export async function fetchManholes() {
  return mockManholes()
}

export async function fetchCavities() {
  try {
    const http = createModuleHttp(MODULE_PREFIX.roadHazard, { silentErrors: true })
    const data = await http.get('/cavity?page=1&page_size=100')
    const list = data?.items ?? data ?? []
    return Array.isArray(list) && list.length > 0 ? list : mockCavities()
  } catch { return mockCavities() }
}

export async function fetchAssets() {
  try {
    const http = createModuleHttp(MODULE_PREFIX.gasAsset, { silentErrors: true })
    const data = await http.get('/assets?page=1&page_size=100')
    const list = data?.items ?? data ?? []
    return Array.isArray(list) && list.length > 0 ? list : mockAssets()
  } catch { return mockAssets() }
}

export async function fetchAlerts() {
  try {
    const http = createModuleHttp(MODULE_PREFIX.alarm, { silentErrors: true })
    const data = await http.get('/alerts?page=1&page_size=100')
    const list = data?.items ?? data ?? []
    return Array.isArray(list) && list.length > 0 ? list : mockAlerts()
  } catch { return mockAlerts() }
}

// ---------------------------------------------------------------------------
// 统一加载
// ---------------------------------------------------------------------------

export async function fetchAllLayers() {
  const results = await Promise.allSettled([
    fetchGasPipelines(), fetchWaterPipelines(), fetchWastePipelines(),
    fetchManholes(), fetchCavities(), fetchAssets(), fetchAlerts()
  ])
  return {
    gasPipelines: results[0].status === 'fulfilled' ? results[0].value : [],
    waterPipelines: results[1].status === 'fulfilled' ? results[1].value : [],
    wastePipelines: results[2].status === 'fulfilled' ? results[2].value : [],
    manholes: results[3].status === 'fulfilled' ? results[3].value : [],
    cavities: results[4].status === 'fulfilled' ? results[4].value : [],
    assets: results[5].status === 'fulfilled' ? results[5].value : [],
    alerts: results[6].status === 'fulfilled' ? results[6].value : []
  }
}
