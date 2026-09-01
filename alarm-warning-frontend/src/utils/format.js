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
 * 预警等级文本映射（对应后端 AlertLevel 枚举）
 */
export function getAlertLevelText(level) {
  const map = {
    BLUE: '蓝色预警',
    YELLOW: '黄色预警',
    ORANGE: '橙色预警',
    RED: '红色预警'
  }
  return map[level] || level
}

/**
 * 预警状态文本映射（对应后端 AlertStatus 枚举）
 */
export function getAlertStatusText(status) {
  const map = {
    OPEN: '待处理',
    ACKNOWLEDGED: '已确认',
    RESOLVED: '已解决',
    CLOSED: '已关闭'
  }
  return map[status] || status
}
