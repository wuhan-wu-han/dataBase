/**
 * 格式化工具函数
 */

/**
 * 格式化日期时间为可读字符串
 */
export function formatDateTime(value) {
  if (!value) return '-'
  const date = new Date(value)
  const y = date.getFullYear()
  const m = String(date.getMonth() + 1).padStart(2, '0')
  const d = String(date.getDate()).padStart(2, '0')
  const h = String(date.getHours()).padStart(2, '0')
  const min = String(date.getMinutes()).padStart(2, '0')
  const s = String(date.getSeconds()).padStart(2, '0')
  return `${y}-${m}-${d} ${h}:${min}:${s}`
}

/**
 * 预警等级文本映射
 */
export function getAlertLevelText(level) {
  const map = {
    CRITICAL: '紧急',
    HIGH: '重要',
    MEDIUM: '一般',
    LOW: '提示'
  }
  return map[level] || level
}

/**
 * 预警状态文本映射
 */
export function getAlertStatusText(status) {
  const map = {
    TRIGGERED: '已触发',
    ACKNOWLEDGED: '已确认',
    PROCESSING: '处理中',
    RESOLVED: '已解决',
    CLOSED: '已关闭'
  }
  return map[status] || status
}
