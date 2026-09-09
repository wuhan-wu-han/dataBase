/**
 * 临时 GIS 演示数据。
 *
 * 仅在 VITE_GIS_DEMO_MODE=true 时使用。所有 DEMO 数据集中维护在本文件中，
 * 真实接口完成联调后可以通过环境变量一次性关闭，禁止把本文件数据当作生产数据。
 */

function demoClock(hour, minute, second = 0) {
  const value = new Date()
  value.setHours(hour, minute, second, 0)
  const pad = (part) => String(part).padStart(2, '0')
  return {
    timestamp: value.getTime(),
    text: `${value.getFullYear()}-${pad(value.getMonth() + 1)}-${pad(value.getDate())} ${pad(hour)}:${pad(minute)}:${pad(second)}`
  }
}

const DEMO_DAY_CODE = (() => {
  const value = new Date()
  const pad = (part) => String(part).padStart(2, '0')
  return `${value.getFullYear()}${pad(value.getMonth() + 1)}${pad(value.getDate())}`
})()

const DEVICE_POINTS = [
  ['GAS-001', '燃气浓度探测器', '中心城区', 109.2308, 36.5752, '在线'],
  ['GAS-002', '燃气泄漏探测器', '中心城区', 109.2127, 36.5598, '在线'],
  ['GAS-003', '燃气压力传感器', '东南片区', 109.2642, 36.5385, '在线'],
  ['WTR-001', '供水压力传感器', '东北片区', 109.2471, 36.5584, '在线'],
  ['WTR-002', '供水遥测终端', '东北片区', 109.2733, 36.5768, '在线'],
  ['SEN-003', '环境监测传感器', '西北片区', 109.1974, 36.5892, '在线'],
  ['SEN-004', '管网通讯终端', '西北片区', 109.1838, 36.5815, '离线'],
  ['CAM-001', '道路监控摄像机', '西南片区', 109.1987, 36.5446, '在线']
]

const MANHOLE_POINTS = [
  ['MH-001', '真武洞街道智能井盖', '中心城区', 109.2378, 36.5279, '异常'],
  ['MH-002', '金明街道智能井盖', '中心城区', 109.2214, 36.5428, '正常'],
  ['MH-003', '沿河湾镇智能井盖', '东北片区', 109.2756, 36.5961, '正常'],
  ['MH-004', '白坪街道智能井盖', '西南片区', 109.1898, 36.5217, '正常']
]

export const DEMO_DEVICES = [
  ...DEVICE_POINTS.map(([asset_code, device_type, area_name, longitude, latitude, online_status], index) => ({
    id: `AST-${String(index + 1).padStart(3, '0')}`,
    asset_code,
    device_id: asset_code,
    segment_name: `${area_name}监测点`,
    device_type,
    area_name,
    longitude,
    latitude,
    online_status,
    asset_status: online_status === '离线' ? '异常' : '正常',
    location: `${area_name}基础设施监测点`,
    length_m: index < 3 ? [18600, 14200, 11700][index] : 0,
    _demoLayer: 'asset'
  })),
  ...MANHOLE_POINTS.map(([code, location, area_name, longitude, latitude], index) => ({
    id: `MHC-${String(index + 1).padStart(3, '0')}`,
    code,
    device_id: code,
    name: location,
    location,
    road_name: location.replace('智能井盖', ''),
    type: index === 0 ? '燃气井盖' : index === 2 ? '供水井盖' : '排水井盖',
    area_name,
    longitude,
    latitude,
    status: index === 0 ? '异常' : '正常',
    online_status: '在线',
    _demoLayer: 'manhole'
  }))
]

// 风险点与配对设备保持约 1.5 公里间距：演示进入页面的缩放级别下两类点位才不会叠成一团。
const RISK_POINTS = [
  ['RSK-001', '燃气浓度异常风险', '高风险', 91, '中心城区', 109.2186, 36.5850, '待处理', 0.8],
  ['RSK-002', '燃气管段泄漏风险', '高风险', 88, '中心城区', 109.2266, 36.5502, '处理中', 1.1],
  ['RSK-003', '供水压力异常风险', '较高风险', 76, '东北片区', 109.2596, 36.5681, '待处理', 0.5],
  ['RSK-004', '管网压力波动风险', '较高风险', 72, '东南片区', 109.2758, 36.5283, '处理中', 0.4],
  ['RSK-005', '道路沉降异常风险', '中风险', 61, '西南片区', 109.1868, 36.5341, '待处理', 1.6],
  ['RSK-006', '井盖状态异常风险', '中风险', 58, '中心城区', 109.2430, 36.5405, '处理中', 0.3],
  ['RSK-007', '设备通讯异常风险', '低风险', 36, '西北片区', 109.1721, 36.5912, '待处理', 0.2]
]

export const DEMO_RISKS = RISK_POINTS.map(([
  code, name, risk_level, risk_score, area_name, longitude, latitude, status, depth_m
]) => ({
  id: code,
  code,
  name,
  location: name,
  road_name: `${area_name}道路`,
  risk_level,
  risk_score,
  area_name,
  longitude,
  latitude,
  status,
  depth_m
}))

// 告警点与上报它的设备错开约 580 米：完全重合时设备图标会被告警图标整个盖住，
// 地图上就看不到"资产设备"这一层的点位了。错开后两类点位都能单独点击。
const ALERT_ROWS = [
  ['001', '燃气浓度异常', 'RED', '高风险', 'GAS-001', '燃气浓度探测器', '中心城区', 109.2352, 36.5790, '待处理', '8.6%', 20, 45, 32],
  ['002', '燃气泄漏预警', 'RED', '高风险', 'GAS-002', '燃气泄漏探测器', '中心城区', 109.2082, 36.5560, '处理中', '4.2%LEL', 20, 43, 18],
  ['003', '供水压力异常', 'ORANGE', '较高风险', 'WTR-001', '供水压力传感器', '东北片区', 109.2515, 36.5546, '待处理', '0.18MPa', 20, 42, 6],
  ['004', '管网压力异常', 'ORANGE', '较高风险', 'GAS-003', '燃气压力传感器', '东南片区', 109.2688, 36.5423, '处理中', '0.31MPa', 20, 40, 24],
  ['005', '道路沉降异常', 'YELLOW', '中风险', 'CAM-001', '道路监控摄像机', '西南片区', 109.1941, 36.5484, '待处理', '18mm', 20, 38, 11],
  ['006', '井盖状态异常', 'YELLOW', '中风险', 'MH-001', '智能井盖', '中心城区', 109.2422, 36.5241, '处理中', '倾角 12°', 20, 36, 45],
  ['007', '设备通讯异常', 'BLUE', '低风险', 'SEN-004', '管网通讯终端', '西北片区', 109.1793, 36.5777, '待处理', '中断 3min', 20, 35, 20],
  ['008', '供水遥测信号波动', 'BLUE', '低风险', 'WTR-002', '供水遥测终端', '东北片区', 109.2778, 36.5730, '已处理', '丢包率 6%', 20, 32, 8]
]

export const DEMO_ALERTS = ALERT_ROWS.map(([
  serial, description, alertLevel, warning_label, device_id, device_type, area_name,
  longitude, latitude, alertStatus, monitor_value, hour, minute, second
]) => {
  const clock = demoClock(hour, minute, second)
  return {
    id: `ALM-${DEMO_DAY_CODE}-${serial}`,
    alertEventCode: `ALM-${DEMO_DAY_CODE}-${serial}`,
    description,
    alertContent: description,
    alertLevel,
    warning_level: alertLevel,
    warning_label,
    risk_level: warning_label,
    device_id,
    device_type,
    area_name,
    area_id: area_name,
    longitude,
    latitude,
    alertStatus,
    status: alertStatus,
    monitor_value,
    eventTime: clock.text,
    eventTimestamp: clock.timestamp
  }
})

export const DEMO_PIPELINES = {
  gas: [
    {
      id: 'GAS-PL-001', name: '安塞城区燃气主干线', pipeline_level: 'main', diameter: 300,
      pressure: 0.36, risk_level: '低风险', status: '正常',
      coordinates: [[109.1802, 36.5687], [109.1981, 36.5650], [109.2154, 36.5702], [109.2336, 36.5638], [109.2549, 36.5567], [109.2751, 36.5612]]
    },
    {
      id: 'GAS-PL-002', name: '真武洞燃气支线', pipeline_level: 'branch', diameter: 160,
      pressure: 0.29, risk_level: '中风险', status: '预警',
      coordinates: [[109.2148, 36.5700], [109.2197, 36.5574], [109.2286, 36.5457], [109.2380, 36.5281]]
    }
  ],
  water: [
    {
      id: 'WTR-PL-001', name: '安塞供水主干线', pipeline_level: 'main', diameter: 400,
      pressure: 0.42, status: '正常',
      coordinates: [[109.1728, 36.5320], [109.1935, 36.5404], [109.2158, 36.5472], [109.2390, 36.5531], [109.2621, 36.5663], [109.2827, 36.5792]]
    },
    {
      id: 'WTR-PL-002', name: '金明供水支线', pipeline_level: 'branch', diameter: 180,
      pressure: 0.34, status: '正常',
      coordinates: [[109.2158, 36.5472], [109.2282, 36.5371], [109.2426, 36.5310], [109.2550, 36.5226]]
    }
  ],
  waste: [
    {
      id: 'WST-PL-001', name: '城区污水输送主线', pipeline_level: 'main', diameter: 500,
      flow_rate: 126, status: '正常',
      coordinates: [[109.1831, 36.5944], [109.1976, 36.5790], [109.2124, 36.5613], [109.2267, 36.5446], [109.2413, 36.5268], [109.2568, 36.5102]]
    },
    {
      id: 'WST-PL-002', name: '白坪污水支线', pipeline_level: 'branch', diameter: 220,
      flow_rate: 58, status: '正常',
      coordinates: [[109.1902, 36.5208], [109.2024, 36.5315], [109.2149, 36.5410], [109.2267, 36.5446]]
    }
  ]
}

export const GIS_DEMO_DATA = {
  gas: DEMO_PIPELINES.gas,
  water: DEMO_PIPELINES.water,
  waste: DEMO_PIPELINES.waste,
  asset: DEMO_DEVICES.filter((item) => item._demoLayer === 'asset'),
  manhole: DEMO_DEVICES.filter((item) => item._demoLayer === 'manhole'),
  hazard: DEMO_RISKS,
  alert: DEMO_ALERTS,
  summary: {
    deviceOnline: 1274,
    deviceTotal: 1287,
    todayWorkOrders: 6,
    processingWorkOrders: 3
  }
}
