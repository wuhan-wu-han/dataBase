import request from './request'

/**
 * 获取区域优先级配置列表
 */
export function getAreaPriorityList() {
  return request.get('/area-priority')
}
