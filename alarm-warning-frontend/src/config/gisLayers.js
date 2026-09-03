/**
 * GIS 图层集中配置。
 *
 * api/gis.js 与 views/gis/GISMap.vue 共用此文件，避免颜色、名称、字段在多处重复定义。
 * 配置里只放「静态知识」：图层叫什么、什么颜色、多少缩放级别显示、详情抽屉展示哪些字段、
 * 点击后跳哪个业务模块、如何把后端原始状态归一化成三态。
 */

// ---------------------------------------------------------------------------
// 安塞区地理范围
// ---------------------------------------------------------------------------

/** Leaflet 使用 [lat, lon] */
export const ANSAI_CENTER = [36.55, 109.22]

export const ANSAI_BOUNDS = {
  west: 109.15,
  east: 109.30,
  south: 36.48,
  north: 36.62
}

const MID_LON = (ANSAI_BOUNDS.west + ANSAI_BOUNDS.east) / 2
const MID_LAT = (ANSAI_BOUNDS.south + ANSAI_BOUNDS.north) / 2
const CORE_TOLERANCE = 0.02

/** 区域筛选项 */
export const AREAS = ['中心城区', '东北片区', '西北片区', '东南片区', '西南片区']

/**
 * [lon, lat] → 片区名称。
 * 后端各服务没有统一的行政区字段，用坐标象限推导，保证真实数据与演示数据都能被筛选。
 */
export function areaOf(coords) {
  if (!Array.isArray(coords) || coords.length < 2) return AREAS[0]
  const [lon, lat] = coords
  if (Math.abs(lon - MID_LON) <= CORE_TOLERANCE && Math.abs(lat - MID_LAT) <= CORE_TOLERANCE) {
    return '中心城区'
  }
  const ns = lat >= MID_LAT ? '东北' : '东南'
  const ew = lon >= MID_LON ? ns : (lat >= MID_LAT ? '西北' : '西南')
  return `${ew}片区`
}

// ---------------------------------------------------------------------------
// 状态归一化
// ---------------------------------------------------------------------------

export const STATUS = {
  normal: { key: 'normal', label: '正常', color: '#34C759' },
  warning: { key: 'warning', label: '预警', color: '#FF9500' },
  danger: { key: 'danger', label: '高风险', color: '#FF3B30' }
}

export const STATUS_OPTIONS = [
  { value: 'normal', label: '正常' },
  { value: 'warning', label: '预警' },
  { value: 'danger', label: '高风险' }
]

const ALERT_LEVEL_STATUS = {
  red: 'danger',
  orange: 'danger',
  yellow: 'warning',
  blue: 'normal'
}

/** 预警等级（RED/ORANGE/YELLOW/BLUE，大小写不敏感）→ 三态 */
export function alertStatusOf(level) {
  if (!level) return 'normal'
  const key = String(level).toLowerCase()
  return ALERT_LEVEL_STATUS[key] || 'normal'
}

/** 风险等级文案（低风险/中风险/高风险/极高风险，或 低/中/高）→ 三态 */
export function riskStatusOf(level) {
  const text = String(level || '')
  if (text.includes('极高') || text.includes('高')) return 'danger'
  if (text.includes('中')) return 'warning'
  return 'normal'
}

/** 运行/在线状态文案 → 三态 */
export function runStatusOf(status) {
  const text = String(status || '')
  if (text.includes('告警') || text.includes('故障') || text.includes('异常') || text.includes('离线')) return 'danger'
  if (text.includes('维护') || text.includes('预警')) return 'warning'
  return 'normal'
}

// ---------------------------------------------------------------------------
// 详情字段着色
// ---------------------------------------------------------------------------

const TONE_COLOR = {
  // 状态类文案
  正常: '#34C759', 在线: '#34C759', 低风险: '#34C759', 低: '#34C759', 蓝色预警: '#0071E3',
  维护中: '#FF9500', 中风险: '#FF9500', 中: '#FF9500', 黄色预警: '#FFCC00',
  告警: '#FF3B30', 异常: '#FF3B30', 故障: '#FF3B30', 离线: '#8E8E93', 报废: '#8E8E93',
  高风险: '#FF3B30', 高: '#FF3B30', 极高风险: '#FF3B30', 橙色预警: '#FF9500', 红色预警: '#FF3B30'
}

/**
 * tone 为 'tone' 的字段按文案取色，取不到则返回 null（详情抽屉渲染为默认文字色）。
 */
export function toneColor(value) {
  if (value === null || value === undefined) return null
  return TONE_COLOR[String(value).trim()] || null
}

// ---------------------------------------------------------------------------
// 图层配置（7 个）
// ---------------------------------------------------------------------------

/**
 * @typedef {Object} GisLayerConfig
 * @property {string} key        图层唯一键
 * @property {string} label      中文名
 * @property {string} group      图层树分组名
 * @property {'line'|'point'} geometry
 * @property {string} color      主色
 * @property {number} weight     管线基础线宽
 * @property {number} minZoom    低于此缩放级别隐藏
 * @property {number} labelZoom  达到此缩放级别显示常驻标签（99 表示不显示）
 * @property {string} route      详情抽屉跳转的业务模块
 * @property {string} routeLabel 跳转按钮文案
 * @property {Array}  fields     详情抽屉字段
 * @property {(p:Object)=>string} titleOf
 * @property {(p:Object)=>string} statusOf
 * @property {(p:Object)=>string} [iconKindOf] 点位图标分类（返回固定白名单字符串）
 * @property {boolean} [pulse]   高风险时是否使用脉冲动画
 */

/** @type {GisLayerConfig[]} */
export const GIS_LAYERS = [
  {
    key: 'gas',
    label: '燃气管网',
    group: '管网管线',
    geometry: 'line',
    color: '#FF3B30',
    weight: 3,
    minZoom: 10,
    labelZoom: 99,
    route: '/gas-risk',
    routeLabel: '燃气风控详情',
    fields: [
      { label: '管线编号', prop: ['id', 'pipeline_id', 'pipelineId'] },
      { label: '管线名称', prop: ['name', 'pipeline_name'] },
      { label: '管内压力', prop: ['pressure'], unit: 'MPa', tone: true },
      { label: '管径', prop: ['diameter'], unit: 'mm' },
      { label: '风险等级', prop: ['risk_level', 'riskLevel'], tone: true },
      { label: '运行状态', prop: ['status'], tone: true }
    ],
    titleOf: (p) => p.name || p.id || '燃气管线',
    statusOf: (p) => {
      if (runStatusOf(p.status) === 'danger') return 'danger'
      const risk = riskStatusOf(p.risk_level ?? p.riskLevel)
      return risk === 'normal' ? runStatusOf(p.status) : risk
    }
  },
  {
    key: 'water',
    label: '供水管网',
    group: '管网管线',
    geometry: 'line',
    color: '#0071E3',
    weight: 3,
    minZoom: 10,
    labelZoom: 99,
    route: '/utility-tunnel',
    routeLabel: '综合管廊详情',
    fields: [
      { label: '管线编号', prop: ['id'] },
      { label: '管线名称', prop: ['name'] },
      { label: '管径', prop: ['diameter'], unit: 'mm' },
      { label: '压力', prop: ['pressure'], unit: 'MPa' },
      { label: '运行状态', prop: ['status'], tone: true }
    ],
    titleOf: (p) => p.name || p.id || '供水管线',
    statusOf: (p) => runStatusOf(p.status)
  },
  {
    key: 'waste',
    label: '废水管网',
    group: '管网管线',
    geometry: 'line',
    color: '#30C0C0',
    weight: 3,
    minZoom: 10,
    labelZoom: 99,
    route: '/utility-tunnel',
    routeLabel: '综合管廊详情',
    fields: [
      { label: '管线编号', prop: ['id'] },
      { label: '管线名称', prop: ['name'] },
      { label: '流量', prop: ['flow_rate', 'flowRate'], unit: 'm³/h' },
      { label: '运行状态', prop: ['status'], tone: true }
    ],
    titleOf: (p) => p.name || p.id || '废水管线',
    statusOf: (p) => runStatusOf(p.status)
  },
  {
    key: 'manhole',
    label: '智能井盖',
    group: '设施点位',
    geometry: 'point',
    color: '#8E8E93',
    minZoom: 14,
    labelZoom: 16,
    route: '/utility-tunnel',
    routeLabel: '综合管廊详情',
    fields: [
      { label: '井盖编号', prop: ['id'] },
      { label: '井盖名称', prop: ['name'] },
      { label: '所属类型', prop: ['type'] },
      { label: '运行状态', prop: ['status'], tone: true }
    ],
    titleOf: (p) => p.name || p.id || '智能井盖',
    statusOf: (p) => runStatusOf(p.status),
    iconKindOf: (p) => {
      const t = String(p.type || '')
      if (t.includes('燃气')) return 'gas'
      if (t.includes('供水') || t.includes('给水')) return 'water'
      if (t.includes('排水') || t.includes('污水') || t.includes('废水')) return 'drain'
      return 'default'
    },
    pulse: true
  },
  {
    key: 'hazard',
    label: '道路塌陷',
    group: '风险预警',
    geometry: 'point',
    color: '#FF9500',
    minZoom: 11,
    labelZoom: 15,
    route: '/road-hazard',
    routeLabel: '道路塌陷详情',
    fields: [
      { label: '风险点编号', prop: ['id'] },
      { label: '位置描述', prop: ['location', 'address'] },
      { label: '风险等级', prop: ['risk_level', 'riskLevel'], tone: true },
      { label: '沉降值', prop: ['settlement'], unit: 'mm' },
      { label: '影响半径', prop: ['impact_radius', 'impactRadius'], unit: 'm' }
    ],
    titleOf: (p) => p.location || p.address || p.id || '塌陷风险点',
    statusOf: (p) => riskStatusOf(p.risk_level ?? p.riskLevel),
    pulse: true
  },
  {
    key: 'asset',
    label: '资产设备',
    group: '设施点位',
    geometry: 'point',
    color: '#34C759',
    minZoom: 12,
    labelZoom: 16,
    route: '/asset',
    routeLabel: '资产管理详情',
    fields: [
      { label: '资产编号', prop: ['id', 'asset_id', 'assetId'] },
      { label: '设备类型', prop: ['device_type', 'deviceType'] },
      { label: '在线状态', prop: ['online_status', 'onlineStatus'], tone: true },
      { label: '资产状态', prop: ['asset_status', 'assetStatus'], tone: true }
    ],
    titleOf: (p) => {
      const type = p.device_type || p.deviceType
      const id = p.id || p.asset_id || p.assetId
      return type && id ? `${type} · ${id}` : (type || id || '资产设备')
    },
    statusOf: (p) => runStatusOf(p.online_status ?? p.onlineStatus),
    iconKindOf: (p) => {
      const t = String(p.device_type || p.deviceType || '')
      if (t.includes('摄像')) return 'camera'
      if (t.includes('探测')) return 'detector'
      if (t.includes('通风') || t.includes('风机')) return 'fan'
      if (t.includes('传感')) return 'sensor'
      return 'default'
    },
    pulse: true
  },
  {
    key: 'alert',
    label: '预警事件',
    group: '风险预警',
    geometry: 'point',
    color: '#5856D6',
    minZoom: 10,
    labelZoom: 15,
    route: '/alerts',
    routeLabel: '预警中心详情',
    fields: [
      { label: '预警编号', prop: ['id', 'alertEventCode', 'alert_event_code'] },
      { label: '预警级别', prop: ['warning_label', 'warningLabel', 'alertLevel'], tone: true },
      { label: '设备类型', prop: ['device_type', 'deviceType'] },
      { label: '所属区域', prop: ['area_id', 'areaId'] },
      { label: '事件描述', prop: ['description', 'alertContent'] },
      { label: '发生时间', prop: ['event_time', 'eventTime', 'eventTimestamp'] }
    ],
    titleOf: (p) => p.warning_label || p.warningLabel || p.description || p.id || '预警事件',
    statusOf: (p) => alertStatusOf(p.warning_level ?? p.warningLevel ?? p.alertLevel),
    iconKindOf: (p) => {
      const lv = String(p.warning_level ?? p.warningLevel ?? p.alertLevel ?? '').toLowerCase()
      if (lv.includes('red') || lv.includes('红')) return 'red'
      if (lv.includes('orange') || lv.includes('橙')) return 'orange'
      if (lv.includes('yellow') || lv.includes('黄')) return 'yellow'
      return 'blue'
    },
    pulse: true
  }
]

/** 图层树分组顺序 */
export const LAYER_GROUPS = ['管网管线', '设施点位', '风险预警']

export const LAYER_MAP = Object.fromEntries(GIS_LAYERS.map((l) => [l.key, l]))
