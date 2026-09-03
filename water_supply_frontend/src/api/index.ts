import { http } from './base'
import type {
  Alarm, BurstCase, BurstValve, DmaRecord, DmaZone, Hydrant, HydrantEvent,
  MonitorLatest, MonitorRecord, NV, PressurePlan, PumpStation, QualityNode,
  QualityRecord, SecondaryUnit, Summary
} from '../types'

export const getSummary = () => http.get<Summary>('/api/summary').then(r => r.data)

// ---- 功能1 实时运行监测 ----
export const collectMonitor = (form: {
  pipe_id: number; pressure_mpa?: number; flow_m3h?: number; level_cm?: number
  turbidity_ntu?: number; residual_cl?: number; deformation_mm?: number
}) => http.post('/api/monitor/data', form).then(r => r.data as {
  ok: boolean; id: number; is_abnormal: boolean
  alarms_created: { type: string; level: string; detail: string }[]
})
export const getLatest = (q?: { keyword?: string; only_abnormal?: boolean }) =>
  http.get('/api/monitor/latest', { params: q }).then(r => r.data as {
    total: number; items: MonitorLatest[]
  })
export const getHistory = (pipeId: number) =>
  http.get('/api/monitor/history', { params: { pipe_id: pipeId } })
    .then(r => r.data as { pipe: any; records: MonitorRecord[] })
export const getAlarms = (q?: { status?: string; level?: string; type?: string; source?: string; page?: number; page_size?: number }) =>
  http.get('/api/monitor/alarms', { params: q }).then(r => r.data as {
    total: number; items: Alarm[]
  })
export const handleAlarm = (id: number, status = '已处理') =>
  http.post(`/api/monitor/alarms/${id}/handle`, null, { params: { status } }).then(r => r.data)
export const getAlarmTrend = () =>
  http.get('/api/monitor/alarm-trend').then(r => r.data as {
    days: string[]; series: { name: string; data: number[] }[]
  })
export const getMonitorStats = () =>
  http.get('/api/monitor/stats').then(r => r.data as {
    by_type: NV[]; by_level: NV[]; monitor_today: number
  })

// ---- 功能2 DMA 分区漏损 ----
export const getDmaZones = (q?: { keyword?: string; status?: string }) =>
  http.get('/api/dma/zones', { params: q }).then(r => r.data as {
    total: number; items: DmaZone[]
  })
export const getDmaRecords = (dmaId: number, days = 7) =>
  http.get('/api/dma/records', { params: { dma_id: dmaId, days } })
    .then(r => r.data as { zone: DmaZone | null; records: DmaRecord[] })
export const addDmaRecord = (form: {
  dma_id: number; date: string; inflow_m3: number; billed_m3: number; night_min_flow_m3h?: number
}) => http.post('/api/dma/records', form).then(r => r.data as {
  ok: boolean; id: number; leakage_rate_pct: number; alerts: [string, string][]
})
export const getDmaStats = () =>
  http.get('/api/dma/stats').then(r => r.data as {
    by_rate: NV[]; night: NV[]; total_users: number; avg_rate: number
    dark_leaks: { code: string; name: string; dark_leak_location: string }[]
  })
export const locateDarkLeak = (zoneId: number, location: string) =>
  http.post(`/api/dma/zones/${zoneId}/locate`, null, { params: { location } }).then(r => r.data)

// ---- 功能3 水质溯源 ----
export const getQualityChain = () =>
  http.get('/api/quality/chain').then(r => r.data as { nodes: QualityNode[] })
export const getQualityRecords = (nodeId: number, limit = 30) =>
  http.get('/api/quality/records', { params: { node_id: nodeId, limit } })
    .then(r => r.data as { node: QualityNode | null; records: QualityRecord[] })
export const collectQuality = (form: {
  node_id: number; turbidity_ntu?: number; residual_cl?: number; ph?: number
}) => http.post('/api/quality/data', form).then(r => r.data as {
  ok: boolean; is_abnormal: boolean
  suspect_pipe: { code: string; name: string } | null
  alarms: { type: string; level: string; detail: string }[]
})
export const getQualityStats = () =>
  http.get('/api/quality/stats').then(r => r.data as { by_kind: NV[]; abnormal_nodes: number })

// ---- 功能4 智能压力调度 ----
export const getStations = () =>
  http.get('/api/pressure/stations').then(r => r.data as { total: number; items: PumpStation[] })
export const makePlan = (form: { station_id: number; period: string; terrain_delta_m?: number }) =>
  http.post('/api/pressure/plan', form).then(r => r.data as {
    ok: boolean; id: number; target_pressure_mpa: number; energy_save_pct: number; burst_risk: string
  })
export const getPlans = (stationId = 0) =>
  http.get('/api/pressure/plans', { params: stationId ? { station_id: stationId } : {} })
    .then(r => r.data as { total: number; items: PressurePlan[] })
export const applyPlan = (id: number) =>
  http.post(`/api/pressure/plans/${id}/apply`).then(r => r.data)
export const getPressureStats = () =>
  http.get('/api/pressure/stats').then(r => r.data as {
    by_period: NV[]; avg_energy_save_pct: number
  })

// ---- 功能5 二次供水 ----
export const getSecondaryUnits = (q?: { keyword?: string; status?: string }) =>
  http.get('/api/secondary/units', { params: q }).then(r => r.data as {
    total: number; items: SecondaryUnit[]
  })
export const collectSecondary = (form: {
  unit_id: number; level_pct?: number; turbidity_ntu?: number; residual_cl?: number; disinfect_status?: string
}) => http.post('/api/secondary/data', form).then(r => r.data as {
  ok: boolean; is_abnormal: boolean; alarms: { level: string; detail: string }[]
})
export const getSecondaryStats = () =>
  http.get('/api/secondary/stats').then(r => r.data as { by_status: NV[]; abnormal: number })

// ---- 功能6 消防栓 ----
export const getHydrants = (q?: { keyword?: string; status?: string; district?: string; page?: number; page_size?: number }) =>
  http.get('/api/hydrant/list', { params: q }).then(r => r.data as {
    total: number; items: Hydrant[]
  })
export const getHydrantOptions = () =>
  http.get('/api/hydrant/options').then(r => r.data as {
    districts: string[]; pipes: { id: number; code: string; name: string }[]
  })
export const createHydrant = (form: any) =>
  http.post('/api/hydrant', form).then(r => r.data as { ok: boolean; id: number; code: string })
export const updateHydrant = (id: number, form: any) =>
  http.put(`/api/hydrant/${id}`, form).then(r => r.data)
export const testHydrant = (id: number, form: { pressure_mpa?: number; test_flow_ls?: number; note?: string }) =>
  http.post(`/api/hydrant/${id}/test`, form).then(r => r.data as {
    ok: boolean; is_abnormal: boolean; alarms: { level: string; detail: string }[]
  })
export const getHydrantEvents = (id: number) =>
  http.get(`/api/hydrant/${id}/events`).then(r => r.data as { total: number; items: HydrantEvent[] })
export const getHydrantStats = () =>
  http.get('/api/hydrant/stats/summary').then(r => r.data as { by_status: NV[]; by_district: NV[] })

// ---- 功能7 爆管影响分析 ----
export const getBurstCases = (status = '') =>
  http.get('/api/burst/cases', { params: status ? { status } : {} })
    .then(r => r.data as { total: number; items: BurstCase[] })
export const predictBurst = (pipeId: number) =>
  http.post('/api/burst/predict', null, { params: { pipe_id: pipeId } }).then(r => r.data as {
    ok: boolean; case_id: number; risk_score: number; risk_level: string
    affected_users: number; valves: BurstValve[]
  })
export const getBurstValves = (caseId: number) =>
  http.get(`/api/burst/${caseId}/valves`).then(r => r.data as { total: number; items: BurstValve[] })
export const handleBurst = (caseId: number, status: string) =>
  http.post(`/api/burst/${caseId}/handle`, { status }).then(r => r.data)
export const getBurstStats = () =>
  http.get('/api/burst/stats/summary').then(r => r.data as { by_level: NV[]; by_status: NV[] })
