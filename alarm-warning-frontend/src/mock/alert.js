// 预警事件 mock 数据 + 查询函数
// 用途：首页监控大屏 / AI预警中心 在 Java 预警服务(alarm-warning-service)未启动时兜底，
// 保证页面不弹 500、图表与列表有演示数据。返回结构与真实后端一致：{ total, records }。

// 固定种子伪随机，保证每次刷新数据稳定
let _seed = 20260903
function rand() {
  _seed = (_seed * 1103515245 + 12345) & 0x7fffffff
  return _seed / 0x7fffffff
}
function pick(arr) {
  return arr[Math.floor(rand() * arr.length)]
}
function randInt(min, max) {
  return Math.floor(rand() * (max - min + 1)) + min
}

// 设备类型 → 典型监测指标（metricKey / 单位 / 阈值区间）
const DEVICE_METRICS = {
  燃气: { key: 'gas_concentration', unit: '%LEL', th: [20, 50] },
  供水: { key: 'pipe_pressure', unit: 'MPa', th: [0.2, 0.6] },
  排水: { key: 'water_level', unit: 'm', th: [1.5, 3.0] },
  热力: { key: 'supply_temp', unit: '℃', th: [90, 130] },
  电力: { key: 'cable_temp', unit: '℃', th: [70, 110] },
  综合管廊: { key: 'o2_concentration', unit: '%', th: [18, 22] }
}
const DEVICE_TYPES = Object.keys(DEVICE_METRICS)
const AREAS = ['城北片区', '城南片区', '开发区', '高新区', '老城区']
const LEVELS = ['RED', 'ORANGE', 'YELLOW', 'BLUE']
const LEVEL_WEIGHTS = [0.08, 0.17, 0.35, 0.4] // 红少蓝多，贴近真实分布
const STATUSES = ['OPEN', 'ACKNOWLEDGED', 'RESOLVED', 'CLOSED']
const STATUS_WEIGHTS = [0.3, 0.2, 0.3, 0.2]

function weightedPick(items, weights) {
  const r = rand()
  let acc = 0
  for (let i = 0; i < items.length; i++) {
    acc += weights[i]
    if (r <= acc) return items[i]
  }
  return items[items.length - 1]
}

// 生成近 7 天的预警事件（越近越多，制造趋势）
function buildAlerts() {
  const list = []
  const now = Date.now()
  let seq = 1
  for (let dayOffset = 6; dayOffset >= 0; dayOffset--) {
    // 距今越近，事件越多：3~14 条/天
    const count = randInt(3, 6) + (6 - dayOffset)
    for (let i = 0; i < count; i++) {
      const dayStart = new Date(now - dayOffset * 86400000)
      dayStart.setHours(0, 0, 0, 0)
      const ts = dayStart.getTime() + randInt(0, 86399) * 1000
      const deviceType = pick(DEVICE_TYPES)
      const metric = DEVICE_METRICS[deviceType]
      const level = weightedPick(LEVELS, LEVEL_WEIGHTS)
      const threshold = +(rand() * (metric.th[1] - metric.th[0]) + metric.th[0]).toFixed(2)
      // 高等级 → 实测值明显超阈值
      const overFactor = level === 'RED' ? 1.6 : level === 'ORANGE' ? 1.35 : level === 'YELLOW' ? 1.15 : 1.05
      const value = +(threshold * overFactor * (0.9 + rand() * 0.2)).toFixed(2)
      list.push({
        id: seq,
        alertEventCode: `AL-2026-${String(seq).padStart(4, '0')}`,
        deviceType,
        deviceId: `${deviceType === '综合管廊' ? 'GL' : deviceType}-DEV-${randInt(1000, 9999)}`,
        areaId: pick(AREAS),
        metricKey: metric.key,
        metricValue: value,
        thresholdValue: threshold,
        unit: metric.unit,
        priorityScore: randInt(level === 'RED' ? 85 : level === 'ORANGE' ? 65 : level === 'YELLOW' ? 40 : 10, 100),
        alertLevel: level,
        alertStatus: weightedPick(STATUSES, STATUS_WEIGHTS),
        eventTimestamp: new Date(ts).toISOString(),
        description: `${deviceType}监测点 ${metric.key} 实测 ${value}${metric.unit}，阈值 ${threshold}${metric.unit}`
      })
      seq++
    }
  }
  // 按时间倒序（最新在前）
  list.sort((a, b) => new Date(b.eventTimestamp) - new Date(a.eventTimestamp))
  return list
}

const ALERTS = buildAlerts()

/**
 * 模拟后端分页 + 筛选查询
 * @param {Object} params { page, size, alertLevel, status, deviceType }
 * @returns {{ total:number, records:Array, page:number, size:number }}
 */
export function queryAlerts(params = {}) {
  const page = Number(params.page) || 1
  const size = Number(params.size) || 10
  let rows = ALERTS.slice()

  if (params.alertLevel) rows = rows.filter((r) => r.alertLevel === params.alertLevel)
  // 后端筛选状态用的参数名是 status，对应记录的 alertStatus
  const statusFilter = params.status || params.alertStatus
  if (statusFilter) rows = rows.filter((r) => r.alertStatus === statusFilter)
  if (params.deviceType) {
    const kw = String(params.deviceType).toLowerCase()
    rows = rows.filter((r) => (r.deviceType || '').toLowerCase().includes(kw))
  }

  const total = rows.length
  const start = (page - 1) * size
  const records = rows.slice(start, start + size)
  return { total, records, page, size }
}

/** 按 id 取单条详情（找不到则返回最新一条） */
export function queryAlertDetail(id) {
  return ALERTS.find((r) => String(r.id) === String(id)) || ALERTS[0]
}

export default {
  list: ALERTS,
  queryAlerts,
  queryAlertDetail
}
