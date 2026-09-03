// 告警等级（高/中/低）→ Element Plus 标签类型
export const levelTagType = (level?: string) => {
  if (level === '高') return 'danger'
  if (level === '中') return 'warning'
  return 'success'
}

// 管道/设备状态
export const statusTagType = (status?: string) => {
  if (status === '告警' || status === '漏损偏高' || status === '暗漏定位' || status === '异常') return 'danger'
  if (status === '处置中' || status === '风险预警' || status === '已关阀') return 'warning'
  if (status === '已修复' || status === '已执行') return 'success'
  return 'success'
}

// 爆管风险等级
export const riskTagType = (level?: string) => {
  if (level === '高') return 'danger'
  if (level === '中') return 'warning'
  return 'success'
}

export const fmt = (v?: number | null, digits = 1) =>
  v === null || v === undefined || Number.isNaN(v) ? '-' : Number(v).toFixed(digits)

export const fmtTs = (ts?: number | null) => {
  if (!ts) return '-'
  const d = new Date(ts)
  const p = (n: number) => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${p(d.getMonth() + 1)}-${p(d.getDate())} ${p(d.getHours())}:${p(d.getMinutes())}`
}

export const today = () => {
  const d = new Date()
  const p = (n: number) => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${p(d.getMonth() + 1)}-${p(d.getDate())}`
}
