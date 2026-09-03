// 告警等级（高 / 中 / 低）→ Element Plus 标签类型
export const levelTagType = (level?: string) => {
  if (level === '高') return 'danger'
  if (level === '中') return 'warning'
  return 'success'
}

// 井盖状态：正常 / 告警 / 处置中 / 被盗 / 维修中
export const manholeStatusTag = (status?: string) => {
  if (status === '告警' || status === '被盗') return 'danger'
  if (status === '处置中') return 'warning'
  if (status === '维修中') return 'primary'
  return 'success'
}

// 告警与工单共用的流转状态：待派发 / 已派发 / 处置中 / 待核验 / 已核验 / 已闭环
export const flowStatusTag = (status?: string) => {
  if (status === '已闭环') return 'success'
  if (status === '已核验') return 'primary'
  if (status === '待核验') return 'warning'
  if (status === '处置中' || status === '已派发') return 'warning'
  return 'info'
}

// 井盖破损程度：完好 / 轻微裂缝 / 破损
export const damageTagType = (damage?: string) => {
  if (damage === '破损') return 'danger'
  if (damage === '轻微裂缝') return 'warning'
  return 'success'
}

// 防坠网状态：已安装 / 破损 / 已维修 / 已更换
export const netStatusTag = (status?: string) => {
  if (status === '破损') return 'danger'
  if (status === '已维修') return 'primary'
  if (status === '已更换') return 'info'
  return 'success'
}

// 公安联动状态：已报案 / 已立案 / 侦破中 / 已追回
export const policeStatusTag = (status?: string) => {
  if (status === '已追回') return 'success'
  if (status === '侦破中') return 'primary'
  if (status === '已立案') return 'warning'
  return 'info'
}

export const fmt = (v?: number | null, digits = 1) =>
  v === null || v === undefined || Number.isNaN(v) ? '-' : Number(v).toFixed(digits)

export const fmtTs = (ts?: number | null) => {
  if (!ts) return '-'
  const d = new Date(ts)
  const p = (n: number) => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${p(d.getMonth() + 1)}-${p(d.getDate())} ${p(d.getHours())}:${p(d.getMinutes())}`
}

export const fmtDate = (ts?: number | null) => {
  if (!ts) return '-'
  const d = new Date(ts)
  const p = (n: number) => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${p(d.getMonth() + 1)}-${p(d.getDate())}`
}

export const today = () => {
  const d = new Date()
  const p = (n: number) => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${p(d.getMonth() + 1)}-${p(d.getDate())}`
}
