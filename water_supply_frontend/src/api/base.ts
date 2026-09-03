import axios from 'axios'

export const http = axios.create({ baseURL: '', timeout: 10000 })

http.interceptors.response.use(
  r => r,
  e => {
    const detail = e?.response?.data?.detail
    if (detail) e.message = detail
    return Promise.reject(e)
  }
)
