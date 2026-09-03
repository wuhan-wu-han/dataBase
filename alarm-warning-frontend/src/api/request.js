import axios from 'axios'
import { ElMessage } from 'element-plus'
import { authState, clearSession } from '@/stores/auth'

// 创建 axios 实例
const request = axios.create({
  baseURL: '/api',
  timeout: 10000
})

// 请求拦截器
request.interceptors.request.use(
  (config) => {
    if (authState.token) config.headers.Authorization = `Bearer ${authState.token}`
    return config
  },
  (error) => {
    if (error.response?.status === 401) {
      clearSession()
      if (window.location.pathname !== '/login') window.location.assign('/login')
    }
    return Promise.reject(error)
  }
)

// 响应拦截器
request.interceptors.response.use(
  (response) => {
    const res = response.data

    // 后端统一返回格式：{ code: 200, data: ..., message: ... }
    if (res.code === 200) {
      return res.data
    }

    // 非 200 业务码，弹出错误提示
    ElMessage.error(res.message || '请求失败')
    return Promise.reject(new Error(res.message || '请求失败'))
  },
  (error) => {
    // 网络错误或超时
    const message = error.response?.data?.message || error.message || '网络异常'
    ElMessage.error(message)
    return Promise.reject(error)
  }
)

export default request
