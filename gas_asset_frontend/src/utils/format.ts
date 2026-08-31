// 通用展示辅助：时间格式化与标签配色

/** 毫秒时间戳 → yyyy-MM-dd HH:mm */
export function fmtTime(ts: number | null | undefined): string {
  if (!ts) return '-'
  const d = new Date(ts)
  const p = (n: number) => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${p(d.getMonth() + 1)}-${p(d.getDate())} ${p(d.getHours())}:${p(d.getMinutes())}`
}

/** 金额（元）→ 万元字符串 */
export function fmtCost(cost: number | null | undefined): string {
  if (cost == null) return '-'
  return cost >= 10000 ? `${(cost / 10000).toFixed(1)} 万元` : `${cost} 元`
}

export type TagType = 'success' | 'info' | 'warning' | 'danger' | 'primary'

export const ASSET_STATUS_TAG: Record<string, TagType> = {
  在役: 'success',
  停用: 'info',
  待报废: 'danger'
}

export const TASK_STATUS_TAG: Record<string, TagType> = {
  执行中: 'primary',
  差异处理中: 'warning',
  已完成: 'success'
}

export const STAGE_TAG: Record<string, TagType> = {
  采购: 'primary',
  施工: 'warning',
  运维: 'success',
  改造: 'info',
  报废: 'danger'
}

export const CHECK_RESULT_TAG: Record<string, TagType> = {
  一致: 'success',
  状态不符: 'warning',
  盘亏: 'danger',
  盘盈: 'primary'
}

export const HANDLE_TAG: Record<string, TagType> = {
  无差异: 'success',
  待处理: 'warning',
  补录: 'primary',
  修正: 'info',
  报废: 'danger',
  待核对: 'info'
}
