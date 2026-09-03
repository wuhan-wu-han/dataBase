import axios from 'axios'

// 默认使用同源 /auth：开发环境由 Vite 代理，容器部署由 Nginx 代理。
const authHttp = axios.create({
  baseURL: import.meta.env.VITE_AUTH_BASE_URL || '/auth',
  timeout: 10000
})

export async function login(credentials) {
  const { data } = await authHttp.post('/login', credentials)
  return data
}

export async function getCurrentUser(token) {
  const { data } = await authHttp.get('/me', { headers: { Authorization: `Bearer ${token}` } })
  return data
}

function authHeaders() {
  const token = sessionStorage.getItem('rbac_access_token')
  return { Authorization: `Bearer ${token}` }
}

export const changePassword = async (body) => (await authHttp.post('/change-password', body, { headers: authHeaders() })).data
export const getUsers = async () => (await authHttp.get('/users', { headers: authHeaders() })).data
export const getRoles = async () => (await authHttp.get('/roles', { headers: authHeaders() })).data
export const createUser = async (body) => (await authHttp.post('/users', body, { headers: authHeaders() })).data
export const updateUser = async (id, body) => (await authHttp.put(`/users/${id}`, body, { headers: authHeaders() })).data
export const resetUserPassword = async (id, newPassword) => (await authHttp.put(`/users/${id}/password`, { newPassword }, { headers: authHeaders() })).data
