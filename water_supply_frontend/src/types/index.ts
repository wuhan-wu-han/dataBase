export interface Summary {
  pipe_total: number
  pipe_abnormal: number
  active_alarms: number
  monitor_today: number
  avg_leakage_pct: number
  dma_abnormal: number
  quality_abnormal: number
  secondary_abnormal: number
  hydrant_total: number
  hydrant_abnormal: number
  burst_high: number
  burst_pending: number
}

export interface Pipe {
  id: number
  code: string
  name: string
  material?: string
  diameter_mm?: number
  length_m?: number
  district?: string
  road_name?: string
  terrain_elev_m?: number
  lay_date?: string
  status: string
}

export interface MonitorLatest {
  id: number
  code: string
  name: string
  district?: string
  road_name?: string
  status: string
  ts?: number
  pressure_mpa?: number
  flow_m3h?: number
  level_cm?: number
  turbidity_ntu?: number
  residual_cl?: number
  deformation_mm?: number
  is_abnormal?: number
}

export interface MonitorRecord {
  id: number
  pipe_id: number
  ts: number
  pressure_mpa?: number
  flow_m3h?: number
  level_cm?: number
  turbidity_ntu?: number
  residual_cl?: number
  deformation_mm?: number
  is_abnormal: number
}

export interface Alarm {
  id: number
  alarm_code: string
  pipe_id?: number
  source: string
  type: string
  level: string
  detail?: string
  alarm_ts: number
  status: string
  code?: string
  name?: string
  road_name?: string
  district?: string
}

export interface DmaZone {
  id: number
  code: string
  name: string
  district?: string
  pipe_count: number
  user_count: number
  avg_flow_m3h?: number
  night_min_flow_m3h?: number
  leakage_rate_pct?: number
  dark_leak_location?: string
  status: string
}

export interface DmaRecord {
  id: number
  dma_id: number
  date: string
  inflow_m3: number
  billed_m3: number
  night_min_flow_m3h?: number
  leakage_rate_pct: number
}

export interface QualityNode {
  id: number
  code: string
  name: string
  kind: string
  seq: number
  pipe_id?: number
  turbidity_ntu?: number
  residual_cl?: number
  ph?: number
  status: string
}

export interface QualityRecord {
  id: number
  node_id: number
  ts: number
  turbidity_ntu?: number
  residual_cl?: number
  ph?: number
  is_abnormal: number
}

export interface PumpStation {
  id: number
  code: string
  name: string
  district?: string
  supply_elev_m?: number
  pump_count: number
  current_pressure_mpa?: number
  rated_flow_m3h?: number
  status: string
}

export interface PressurePlan {
  id: number
  station_id: number
  period: string
  terrain_delta_m?: number
  current_pressure_mpa?: number
  target_pressure_mpa?: number
  energy_save_pct?: number
  burst_risk_reduce?: string
  status: string
  created_ts: number
  station_code?: string
  station_name?: string
}

export interface SecondaryUnit {
  id: number
  code: string
  community: string
  district?: string
  tank_count: number
  level_pct?: number
  turbidity_ntu?: number
  residual_cl?: number
  disinfect_status: string
  status: string
  last_check?: string
}

export interface Hydrant {
  id: number
  code: string
  location: string
  road_name?: string
  district?: string
  pipe_id?: number
  pressure_mpa?: number
  test_flow_ls?: number
  last_test_ts?: number
  install_date?: string
  status: string
  remark?: string
  pipe_code?: string
}

export interface HydrantEvent {
  id: number
  hydrant_id: number
  type: string
  ts: number
  detail?: string
  status: string
}

export interface BurstCase {
  id: number
  pipe_id: number
  risk_score: number
  risk_level: string
  predict_detail?: string
  affected_users: number
  affected_area?: string
  status: string
  created_ts: number
  code?: string
  name?: string
  district?: string
  road_name?: string
  diameter_mm?: number
  material?: string
  lay_date?: string
}

export interface BurstValve {
  id: number
  case_id: number
  valve_code: string
  position?: string
  order_no: number
  is_selected: number
}

export interface NV { name: string; value: number }
