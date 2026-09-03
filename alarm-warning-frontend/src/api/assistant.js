import { createModuleHttp, MODULE_PREFIX } from './gateway'

// 智能助手走 Python 综合服务(:8000)，与其余 platform 模块同前缀。
// silentErrors=true：助手自身错误由组件内联展示，不弹全局 ElMessage，避免打断对话。
const http = createModuleHttp(MODULE_PREFIX.platform, { silentErrors: true })

/**
 * 发送一轮对话
 * @param {string} message 用户自然语言提问
 * @param {Array<{role:string,content:string}>} history 最近若干轮上下文
 * @returns {Promise<{success:boolean,answer:string,action:object|null,tool_results:Array,model:string,error?:string}>}
 */
export function sendChat(message, history = []) {
  return http.post('/assistant/chat', { message, history })
}

/** 助手配置状态（是否已配置大模型密钥） */
export function getAssistantStatus() {
  return http.get('/assistant/status')
}

/** 助手能力清单（工具 + 可跳转模块） */
export function getAssistantTools() {
  return http.get('/assistant/tools')
}
