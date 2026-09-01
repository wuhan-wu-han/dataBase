// 风险等级 → Element Plus 标签类型
export const riskTagType = (level?: string) => {
  if (level === '高风险') return 'danger'
  if (level === '中风险') return 'warning'
  return 'success'
}

export const statusTagType = (status?: string) => {
  if (status === '已处置') return 'success'
  if (status === '处置中') return 'warning'
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
