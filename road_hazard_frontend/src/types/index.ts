export interface Summary {
  cavity_total: number
  cavity_high: number
  cavity_unhandled: number
  cavity_by_status: { name: string; value: number }[]
  subsidence_points: number
  subsidence_high: number
  subsidence_records: number
  construction_total: number
  construction_high: number
}

export interface Cavity {
  id: number
  code: string
  road_name: string
  district: string
  location?: string
  radar_velocity?: number
  radar_area: number
  leakage_index: number
  cavity_volume: number
  depth_m?: number
  risk_score: number
  risk_level: string
  status: string
  found_at?: string
  remark?: string
}

export interface CavityForm {
  road_name: string
  district: string
  location?: string
  radar_velocity?: number
  radar_area: number
  leakage_index: number
  cavity_volume: number
  depth_m?: number
  status?: string
  found_at?: string
  remark?: string
}

export interface PointSummary {
  point_code: string
  road_name: string
  district: string
  record_count: number
  first_measured: string
  latest_measured: string
  cumulative_mm: number
  rate_mm_month: number
  accelerating: boolean
  risk_level: string
  trend: string
}

export interface SubsidenceRecord {
  id: number
  point_code: string
  road_name: string
  district: string
  measured_at: string
  delta_mm: number
  cumulative_mm: number
  source: string
}

export interface SubsidenceRecordForm {
  point_code: string
  road_name?: string
  district?: string
  measured_at: string
  delta_mm: number
  source?: string
}

export interface Construction {
  id: number
  project_name: string
  construction_unit: string
  road_name: string
  district: string
  work_type: string
  excavation_depth: number
  distance_to_pipe: number
  start_date?: string
  plan_days?: number
  soil_score: number
  pipe_score: number
  overall_score: number
  risk_level: string
  measures?: string
  assessor?: string
  assessed_at?: string
}

export interface ConstructionForm {
  project_name: string
  construction_unit: string
  road_name: string
  district: string
  work_type: string
  excavation_depth: number
  distance_to_pipe: number
  start_date?: string
  plan_days?: number
  measures?: string
  assessor?: string
  assessed_at?: string
}
