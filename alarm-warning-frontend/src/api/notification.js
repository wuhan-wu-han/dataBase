import axios from 'axios'

const http = axios.create({
  baseURL: '/api/platform/notifications',
  timeout: 15000
})

http.interceptors.request.use((config) => {
  const token = sessionStorage.getItem('rbac_access_token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

export const getNotificationRecipients = async () => (await http.get('/recipients')).data
export const sendNotification = async (body) => (await http.post('/send', body)).data
export const sendConfiguredEmail = async (body) => (await http.post('/send-configured-email', body)).data
export const getNotifications = async (params) => (await http.get('', { params })).data
export const retryNotification = async (id) => (await http.post(`/${id}/retry`)).data
