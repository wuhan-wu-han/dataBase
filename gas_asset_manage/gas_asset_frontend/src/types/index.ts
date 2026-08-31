// 与后端 gas_asset_manage 接口对应的数据类型定义

export interface Asset {
  id: number
  asset_code: string
  segment_name: string
  diameter: string
  material: string
  build_year: number
  owner_unit: string
  region: string
  length_m: number
  pressure_level: string
  status: string
  location: string
  longitude: number
  latitude: number
}

export interface AssetOptions {
  diameters: string[]
  materials: string[]
  regions: string[]
  owner_units: string[]
  statuses: string[]
  pressure_levels: string[]
}

/** 分类统计单元：数量 + 长度 */
export interface GroupStat {
  name: string
  value: number
  length_km: number
}

export interface AssetStats {
  by_diameter: GroupStat[]
  by_material: GroupStat[]
  by_decade: GroupStat[]
  by_owner: GroupStat[]
  by_region: GroupStat[]
  by_pressure: GroupStat[]
  by_status: GroupStat[]
}

/** 大屏顶部指标 */
export interface Summary {
  total_assets: number
  total_length_km: number
  in_service: number
  suspended: number
  pending_disposal: number
  task_count: number
  task_finished: number
  inventory_completion_rate: number
  ownership_clear: number
  ownership_clear_rate: number
}

export interface AssetDetail {
  asset: Asset
  ownership: Ownership | null
  lifecycle_summary: { stage: string; count: number; cost: number }[]
}

export interface LifecycleRecord {
  id: number
  asset_id: number
  stage: string
  occurred_at: string
  responsible: string
  description: string
  attachment: string
  cost: number
  asset_code?: string
  segment_name?: string
}

export interface LifecycleCreateReq {
  asset_id: number
  stage: string
  occurred_at: string
  responsible: string
  description: string
  attachment?: string
  cost?: number
}

export interface InventoryTask {
  id: number
  task_code: string
  method: string
  scope: string
  operator: string
  started_ts: number
  finished_ts: number | null
  status: string
  matched_count: number | null
  diff_count: number | null
}

/** 盘点差异项 */
export interface DiffItem {
  id: number
  task_id: number
  asset_id: number | null
  asset_code: string
  check_result: string
  handle_status: string
  remark: string | null
  task_code: string
  method: string
  operator: string
  segment_name: string | null
  region: string | null
  asset_status: string | null
}

export interface InventoryStats {
  by_handle_status: { name: string; value: number }[]
  by_check_result: { name: string; value: number }[]
  recent_tasks: InventoryTask[]
  match_rate_pct: number
}

export interface Ownership {
  asset_id: number
  property_unit: string
  property_nature: string
  property_cert_no: string
  operation_unit: string
  operation_contract_no: string
  supervision_unit: string
  responsibility_boundary: string
  handover_at: string
  asset_code?: string
  segment_name?: string
  region?: string
  asset_status?: string
  is_clear?: boolean
  missing?: string[]
  missing_text?: string
}

/** 责任矩阵：行=单位 列=区域 values=[列序号, 行序号, 数量] */
export interface MatrixData {
  rows: string[]
  columns: string[]
  values: number[][]
}

export interface OwnershipStats {
  total: number
  clear: number
  unclear: number
  clear_rate_pct: number
  by_nature: { name: string; value: number }[]
  property_units: { name: string; value: number }[]
  operation_units: { name: string; value: number }[]
  supervision_units: { name: string; value: number }[]
}

export interface PageResult<T> {
  total: number
  page: number
  page_size: number
  items: T[]
}
