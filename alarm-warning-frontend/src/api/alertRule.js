import request from './request'

/**
 * 获取预警规则列表
 */
export function getAlertRuleList(params) {
  return request.get('/alert-rules', { params })
}

/**
 * 创建预警规则
 */
export function createAlertRule(data) {
  return request.post('/alert-rules', data)
}

/**
 * 更新预警规则
 */
export function updateAlertRule(id, data) {
  return request.put(`/alert-rules/${id}`, data)
}

/**
 * 删除预警规则
 */
export function deleteAlertRule(id) {
  return request.delete(`/alert-rules/${id}`)
}
