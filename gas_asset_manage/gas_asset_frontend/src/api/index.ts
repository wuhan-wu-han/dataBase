import axios from 'axios'
import { API_BASE } from './base'
import type {
  Asset, AssetDetail, AssetOptions, AssetStats, DiffItem, InventoryStats,
  InventoryTask, LifecycleCreateReq, LifecycleRecord, MatrixData,
  Ownership, OwnershipStats, PageResult, Summary
} from '../types'

const http = axios.create({ baseURL: API_BASE, timeout: 15000 })

async function get<T>(url: string, params?: Record<string, any>): Promise<T> {
  const { data } = await http.get<T>(url, { params })
  return data
}

async function send<T>(method: 'post' | 'put', url: string, body?: any): Promise<T> {
  const { data } = await http.request<T>({ method, url, data: body })
  return data
}

export const EXPORT_URL = `${API_BASE}/api/assets/export`

// ---------- 功能 1：资产全景台账 ----------
export const fetchSummary = () => get<Summary>('/api/assets/summary')
export const fetchStats = () => get<AssetStats>('/api/assets/stats')
export const fetchOptions = () => get<AssetOptions>('/api/assets/options')
export const fetchAssets = (params: Record<string, any>) =>
  get<PageResult<Asset>>('/api/assets', params)
export const fetchAssetDetail = (id: number) => get<AssetDetail>(`/api/assets/${id}`)

// ---------- 功能 2：全生命周期档案 ----------
export const fetchLifecycleStages = () => get<{ stages: string[] }>('/api/lifecycle/stages')
export const fetchLifecycleTimeline = (assetId: number) =>
  get<{ asset: Partial<Asset>; records: LifecycleRecord[]; record_count: number; total_cost: number }>(
    `/api/lifecycle/${assetId}`)
export const fetchLifecycleRecords = (params?: Record<string, any>) =>
  get<{ records: LifecycleRecord[] }>('/api/lifecycle', params)
export const createLifecycle = (body: LifecycleCreateReq) =>
  send<{ ok: boolean; id: number }>('post', '/api/lifecycle', body)
export const updateLifecycle = (id: number, body: Partial<LifecycleCreateReq>) =>
  send<{ ok: boolean }>('put', `/api/lifecycle/${id}`, body)

// ---------- 功能 3：资产盘点 ----------
export const fetchInventoryStats = () => get<InventoryStats>('/api/inventory/stats')
export const fetchInventoryTasks = () => get<{ tasks: InventoryTask[] }>('/api/inventory/tasks')
export const createInventoryTask = (body: { method: string; scope: string; scope_region?: string; operator: string }) =>
  send<{ ok: boolean; task_id: number; item_count: number }>('post', '/api/inventory/tasks', body)
export const scanCheck = (taskId: number, asset_code: string) =>
  send<{ ok: boolean; asset_code: string; check_result: string }>('post', `/api/inventory/tasks/${taskId}/scan`, { asset_code })
export const patrolCheck = (taskId: number) =>
  send<{ ok: boolean; checked: number; results: Record<string, number> }>('post', `/api/inventory/tasks/${taskId}/patrol`)
export const handleDiffItem = (itemId: number, handle_status: string, remark?: string) =>
  send<{ ok: boolean }>('put', `/api/inventory/items/${itemId}`, { handle_status, remark })
export const finishInventoryTask = (taskId: number) =>
  send<{ ok: boolean; matched_count: number; diff_count: number }>('post', `/api/inventory/tasks/${taskId}/finish`)
export const fetchDiffList = (params?: Record<string, any>) =>
  get<{ diffs: DiffItem[]; total: number }>('/api/inventory/diff', params)

// ---------- 功能 4：资产权属管理 ----------
export const fetchOwnershipStats = () => get<OwnershipStats>('/api/ownership/stats')
export const fetchOwnershipMatrix = () => get<{ property: MatrixData; operation: MatrixData; supervision: MatrixData }>('/api/ownership/matrix')
export const fetchUnclearAssets = () => get<{ total: number; items: Ownership[] }>('/api/ownership/unclear')
export const fetchOwnership = (assetId: number) => get<Ownership>(`/api/ownership/${assetId}`)
export const updateOwnership = (assetId: number, body: Partial<Ownership>) =>
  send<{ ok: boolean }>('put', `/api/ownership/${assetId}`, body)
