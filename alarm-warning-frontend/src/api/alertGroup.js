import request from './request'

/**
 * 获取预警聚合分组列表
 */
export function getAlertGroupList(params) {
  return request.get('/alert-groups', { params })
}

/**
 * 获取单个聚合分组详情
 */
export function getAlertGroupDetail(id) {
  return request.get(`/alert-groups/${id}`)
}
