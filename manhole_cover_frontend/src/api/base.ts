import axios from 'axios'

export const API_BASE = 'http://localhost:8003'

export const http = axios.create({ baseURL: API_BASE, timeout: 15000 })
