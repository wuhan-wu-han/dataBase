import { createModuleHttp, MODULE_PREFIX } from './gateway'

// 智能助手走 Python 综合服务(:8000)，与其余 platform 模块同前缀。
// silentErrors=true：助手自身错误由组件内联展示，不弹全局 ElMessage，避免打断对话。
// 大模型可能需要两轮 tool-calling；使用独立超时，避免被平台通用 15 秒限制提前中断。
const http = createModuleHttp(MODULE_PREFIX.platform, { silentErrors: true, timeoutMs: 90000 })

/**
 * 发送一轮对话
 * @param {string} message 用户自然语言提问
 * @param {Array<{role:string,content:string}>} history 最近若干轮上下文
 * @returns {Promise<{success:boolean,answer:string,action:object|null,tool_results:Array,model:string,error?:string}>}
 */
export function sendChat(message, conversationId, history = []) {
  return http.post('/assistant/chat', { message, conversation_id: conversationId, history })
}

export function createConversation() {
  return http.post('/assistant/conversations')
}

export function getConversation(conversationId) {
  return http.get(`/assistant/conversations/${conversationId}`)
}

export function clearConversationMemory(conversationId) {
  return http.delete(`/assistant/conversations/${conversationId}/memory`)
}

/** 助手配置状态（是否已配置大模型密钥） */
export function getAssistantStatus() {
  return http.get('/assistant/status')
}

/** 助手能力清单（工具 + 可跳转模块） */
export function getAssistantTools() {
  return http.get('/assistant/tools')
}
