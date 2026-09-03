import { http } from './base'
import type {
  Alarm, ArchiveStats, Manhole, ManholeDetail, ManholeForm, MonitorLatest,
  MonitorRecord, NetDetail, NetStats, OrderDetail, OrderStats, PoliceRecord,
  SafetyNet, Summary, TheftCase, TrackPoint
} from '../types'

export const getSummary = () => http.get<Summary>('/api/summary').then(r => r.data)

// ---- 功能1 实时监测 ----
export const collectMonitor = (form: {
  manhole_id: number; tilt_deg?: number; displacement_mm?: number
  damage?: string; water_level_cm?: number; gas_ppm?: number
}) => http.post('/api/monitor/data', form).then(r => r.data as {
  ok: boolean; id: number; is_abnormal: boolean
  alarms_created: { alarm_id: number; type: string; level: string; detail: string }[]
})
export const getLatest = (q?: { keyword?: string; only_abnormal?: boolean }) =>
  http.get('/api/monitor/latest', { params: q }).then(r => r.data as {
    total: number; items: MonitorLatest[]
  })
export const getHistory = (manholeId: number) =>
  http.get('/api/monitor/history', { params: { manhole_id: manholeId } })
    .then(r => r.data as { manhole: Manhole; records: MonitorRecord[] })
export const getAlarms = (q?: { status?: string; level?: string; type?: string; page?: number; page_size?: number }) =>
  http.get('/api/monitor/alarms', { params: q }).then(r => r.data as {
    total: number; items: Alarm[]
  })
export const getAlarmTrend = () =>
  http.get('/api/monitor/alarm-trend').then(r => r.data as {
    days: string[]; series: { name: string; data: number[] }[]
  })
export const getMonitorStats = () =>
  http.get('/api/monitor/stats').then(r => r.data as {
    by_type: NV[]; by_level: NV[]; by_status: NV[]; monitor_today: number
  })

// ---- 功能2 一井一档 ----
export interface ArchiveQuery {
  keyword?: string; district?: string; type?: string
  status?: string; owner_unit?: string; page?: number; page_size?: number
}
export const getArchives = (q: ArchiveQuery) =>
  http.get('/api/archive', { params: q }).then(r => r.data as {
    total: number; items: Manhole[]
  })
export const getArchiveOptions = () =>
  http.get('/api/archive/options').then(r => r.data as {
    districts: string[]; owners: string[]; types: string[]; statuses: string[]
  })
export const getArchiveStats = () =>
  http.get('/api/archive/stats').then(r => r.data as ArchiveStats)
export const getArchiveDetail = (id: number) =>
  http.get(`/api/archive/${id}`).then(r => r.data as ManholeDetail)
export const createArchive = (form: ManholeForm) =>
  http.post('/api/archive', form).then(r => r.data as { ok: boolean; id: number; code: string })
export const updateArchive = (id: number, form: Partial<ManholeForm> & { status?: string }) =>
  http.put(`/api/archive/${id}`, form).then(r => r.data as { ok: boolean })
export const addRepair = (id: number, form: {
  type: string; date: string; reason?: string; detail?: string
  cost?: number; operator?: string
}) => http.post(`/api/archive/${id}/repairs`, form).then(r => r.data as { ok: boolean; id: number })

// ---- 功能3 工单闭环 ----
export const getOrders = (q?: { status?: string; handle_type?: string; keyword?: string; page?: number; page_size?: number }) =>
  http.get('/api/orders', { params: q }).then(r => r.data as {
    total: number; items: OrderDetail[]
  })
export const getOrderStats = () =>
  http.get('/api/orders/stats').then(r => r.data as OrderStats)
export const dispatchOrder = (id: number, form: { assignee: string; handle_type: string }) =>
  http.post(`/api/orders/${id}/dispatch`, form).then(r => r.data)
export const reportOrder = (id: number, form: { report_info: string }) =>
  http.post(`/api/orders/${id}/report`, form).then(r => r.data)
export const verifyOrder = (id: number, form: { passed: boolean; verify_result: string }) =>
  http.post(`/api/orders/${id}/verify`, form).then(r => r.data)
export const closeOrder = (id: number) =>
  http.post(`/api/orders/${id}/close`).then(r => r.data)

// ---- 功能4 被盗追踪 ----
export const getTheftCases = () =>
  http.get('/api/theft/cases').then(r => r.data as { cases: TheftCase[]; total: number })
export const getTracks = (manholeId: number) =>
  http.get('/api/theft/tracks', { params: { manhole_id: manholeId } })
    .then(r => r.data as { manhole: any; tracks: TrackPoint[]; total: number })
export const addTrack = (form: { manhole_id: number; lat: number; lng: number; speed_kmh?: number; note?: string }) =>
  http.post('/api/theft/tracks', form).then(r => r.data)
export const locateManhole = (id: number) =>
  http.get(`/api/theft/locate/${id}`).then(r => r.data as {
    manhole_id: number; code: string; status: string; lat: number; lng: number
    ts: number | null; speed_kmh: number | null; note: string | null; source: string
  })
export const getPolice = (q?: { manhole_id?: number; status?: string }) =>
  http.get('/api/theft/police', { params: q }).then(r => r.data as {
    records: PoliceRecord[]; total: number
  })
export const addPolice = (form: {
  manhole_id: number; alarm_id?: number; police_unit: string
  contact: string; status?: string; result?: string
}) => http.post('/api/theft/police', form).then(r => r.data as { ok: boolean; id: number; case_no: string })
export const updatePolice = (id: number, status?: string, result?: string) =>
  http.put(`/api/theft/police/${id}`, null, { params: { status, result } }).then(r => r.data)

// ---- 功能5 防坠网 ----
export const getNets = (q?: { net_status?: string; district?: string; keyword?: string; page?: number; page_size?: number }) =>
  http.get('/api/safety-net', { params: q }).then(r => r.data as {
    total: number; items: SafetyNet[]
  })
export const getNetDetail = (id: number) =>
  http.get(`/api/safety-net/${id}`).then(r => r.data as NetDetail)
export const createNet = (form: {
  manhole_id: number; material?: string; load_kg?: number
  next_check?: string; remark?: string
}) => http.post('/api/safety-net', form).then(r => r.data as { ok: boolean; id: number; net_code: string })
export const maintainNet = (id: number, form: { type: string; date: string; detail?: string; operator?: string }) =>
  http.post(`/api/safety-net/${id}/maintain`, form).then(r => r.data as { ok: boolean; net_status: string })
export const getNetStats = () =>
  http.get('/api/safety-net/stats').then(r => r.data as NetStats)

export interface NV { name: string; value: number }
