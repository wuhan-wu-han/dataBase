import request from './request'

/**
 * 获取预警事件列表（分页 + 筛选）
 */
export function getAlertList(params) {
  return request.get('/alerts', { params })
}

/**
 * 获取单个预警事件详情
 */
export function getAlertDetail(id) {
  return request.get(`/alerts/${id}`)
}

/**
 * 更新预警事件状态（确认 / 处理 / 关闭）
 */
export function updateAlertStatus(id, status) {
  return request.patch(`/alerts/${id}/status`, { status })
}
