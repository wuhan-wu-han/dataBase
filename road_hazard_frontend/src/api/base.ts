import axios from 'axios'

export const API_BASE = 'http://localhost:8002'

export const http = axios.create({ baseURL: API_BASE, timeout: 15000 })
