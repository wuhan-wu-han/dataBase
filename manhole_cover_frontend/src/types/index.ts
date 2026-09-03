export interface Summary {
  manhole_total: number
  manhole_abnormal: number
  active_alarms: number
  orders_pending: number
  close_rate_pct: number
  theft_cases: number
  police_records: number
  net_total: number
  net_broken: number
}

export interface Manhole {
  id: number
  code: string
  location: string
  road_name: string
  district: string
  type: string
  owner_unit: string
  material?: string
  install_date?: string
  lat?: number
  lng?: number
  status: string
  remark?: string
  repairs?: number
  alarms?: number
}

export interface ManholeForm {
  location: string
  road_name: string
  district: string
  type: string
  owner_unit: string
  material?: string
  install_date?: string
  lat?: number
  lng?: number
  remark?: string
}

export interface RepairRecord {
  id: number
  manhole_id: number
  type: string
  date: string
  reason?: string
  detail?: string
  cost?: number
  operator?: string
}

export interface MonitorRecord {
  id: number
  manhole_id: number
  ts: number
  tilt_deg?: number
  displacement_mm?: number
  damage: string
  water_level_cm?: number
  gas_ppm?: number
  is_abnormal: number
}

export interface MonitorLatest {
  id: number
  code: string
  location: string
  road_name: string
  district: string
  type: string
  status: string
  ts?: number
  tilt_deg?: number
  displacement_mm?: number
  damage?: string
  water_level_cm?: number
  gas_ppm?: number
  is_abnormal?: number
}

export interface Alarm {
  id: number
  alarm_code: string
  manhole_id: number
  type: string
  level: string
  detail?: string
  alarm_ts: number
  status: string
  code?: string
  location?: string
  road_name?: string
  district?: string
}

export interface ManholeDetail {
  item: Manhole
  repairs: RepairRecord[]
  alarms: Alarm[]
  net: SafetyNet | null
  latest_monitor: MonitorRecord | null
}

export interface OrderDetail {
  id: number
  order_code: string
  alarm_id?: number
  manhole_id: number
  handle_type?: string
  assignee?: string
  dispatch_ts?: number
  status: string
  report_info?: string
  report_ts?: number
  verify_result?: string
  verify_ts?: number
  close_ts?: number
  created_ts: number
  alarm_code?: string
  alarm_type?: string
  alarm_level?: string
  alarm_detail?: string
  code?: string
  location?: string
  road_name?: string
  district?: string
}

export interface OrderStats {
  by_status: { name: string; value: number }[]
  total: number
  closed: number
  close_rate_pct: number
  avg_close_hours: number
}

export interface ArchiveStats {
  by_district: { name: string; value: number }[]
  by_type: { name: string; value: number }[]
  by_status: { name: string; value: number }[]
  by_owner: { name: string; value: number }[]
}

export interface TheftCase {
  alarm_id: number
  alarm_code: string
  alarm_ts: number
  alarm_status: string
  manhole_id: number
  code: string
  location: string
  road_name: string
  district: string
  status: string
  track_points: number
  case_no?: string
  police_status?: string
}

export interface TrackPoint {
  id: number
  manhole_id: number
  ts: number
  lat: number
  lng: number
  speed_kmh?: number
  note?: string
}

export interface PoliceRecord {
  id: number
  case_no: string
  manhole_id: number
  alarm_id?: number
  police_unit: string
  contact: string
  report_ts: number
  status: string
  result?: string
  code?: string
  location?: string
  road_name?: string
}

export interface SafetyNet {
  id: number
  net_code: string
  manhole_id: number
  install_date?: string
  material?: string
  load_kg?: number
  net_status: string
  last_check?: string
  next_check?: string
  repair_count: number
  remark?: string
  manhole_code?: string
  location?: string
  road_name?: string
  district?: string
}

export interface NetMaintain {
  id: number
  net_id: number
  type: string
  date: string
  detail?: string
  operator?: string
}

export interface NetDetail {
  item: SafetyNet
  maintains: NetMaintain[]
  manhole: { code: string; location: string; road_name: string; district: string } | null
}

export interface NetStats {
  by_status: { name: string; value: number }[]
  overdue_check: number
  maintain_total: number
  cover_rate_pct: number
}
