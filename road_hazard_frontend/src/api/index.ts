import { http } from './base'
import type {
  Cavity, CavityForm, Construction, ConstructionForm,
  PointSummary, SubsidenceRecord, SubsidenceRecordForm, Summary
} from '../types'

export const getSummary = () => http.get<Summary>('/api/summary').then(r => r.data)

// ---- 功能1 地下空洞 ----
export interface CavityQuery {
  keyword?: string; district?: string; risk_level?: string
  status?: string; page?: number; page_size?: number
}
export const getCavities = (q: CavityQuery) =>
  http.get('/api/cavity', { params: q }).then(r => r.data as {
    total: number; items: Cavity[]
  })
export const getCavityOptions = () =>
  http.get('/api/cavity/options').then(r => r.data as {
    districts: string[]; roads: string[]; risk_levels: string[]; statuses: string[]
  })
export const getCavityStats = () =>
  http.get('/api/cavity/stats').then(r => r.data as {
    by_risk: NV[]; by_district: NV[]; by_status: NV[]
  })
export const createCavity = (form: CavityForm) =>
  http.post('/api/cavity', form).then(r => r.data as {
    ok: boolean; id: number; code: string; risk_score: number; risk_level: string
  })
export const updateCavity = (id: number, form: Partial<CavityForm>) =>
  http.put(`/api/cavity/${id}`, form).then(r => r.data as {
    ok: boolean; risk_score: number; risk_level: string
  })

// ---- 功能2 道路沉降 ----
export const getSubsPoints = (q?: { district?: string; risk_level?: string; keyword?: string }) =>
  http.get('/api/subsidence/points', { params: q }).then(r => r.data as {
    total: number; items: PointSummary[]
  })
export const getSubsHistory = (pointCode: string) =>
  http.get('/api/subsidence/history', { params: { point_code: pointCode } })
    .then(r => r.data as { point_code: string; records: SubsidenceRecord[] })
export const addSubsRecord = (form: SubsidenceRecordForm) =>
  http.post('/api/subsidence/records', form).then(r => r.data as {
    ok: boolean; point_code: string; cumulative_mm: number
  })
export const getSubsOptions = () =>
  http.get('/api/subsidence/options').then(r => r.data as { districts: string[] })
export const getSubsStats = () =>
  http.get('/api/subsidence/stats').then(r => r.data as {
    by_risk: NV[]; by_district: NV[]
    monthly: { month: string; avg_delta: number; max_cum: number }[]
  })

// ---- 功能3 施工影响评估 ----
export interface ConstructionQuery {
  keyword?: string; district?: string; risk_level?: string
  work_type?: string; page?: number; page_size?: number
}
export const getConstructions = (q: ConstructionQuery) =>
  http.get('/api/construction', { params: q }).then(r => r.data as {
    total: number; items: Construction[]
  })
export const getConstructionOptions = () =>
  http.get('/api/construction/options').then(r => r.data as {
    districts: string[]; work_types: string[]; risk_levels: string[]
  })
export const getConstructionStats = () =>
  http.get('/api/construction/stats').then(r => r.data as {
    by_risk: NV[]; by_work_type: NV[]; by_district: NV[]
  })
export const createConstruction = (form: ConstructionForm) =>
  http.post('/api/construction', form).then(r => r.data as {
    ok: boolean; id: number; soil_score: number; pipe_score: number
    overall_score: number; risk_level: string
  })

export interface NV { name: string; value: number }
