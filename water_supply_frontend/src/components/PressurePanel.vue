<script setup lang="ts">
import { nextTick, onBeforeUnmount, onMounted, reactive, ref } from 'vue'
import { ElMessage, type FormInstance } from 'element-plus'
import { applyPlan, getPlans, getPressureStats, getStations, makePlan } from '../api'
import type { PressurePlan, PumpStation } from '../types'
import { barOption, initChart, pieOption } from '../utils/chart'
import { fmt, fmtTs } from '../utils/format'

const emit = defineEmits<{ (e: 'changed'): void }>()

// ---------------- 图表 ----------------
const periodEl = ref<HTMLElement>()
let periodChart: ReturnType<typeof initChart> | null = null
const avgSave = ref(0)

async function loadCharts() {
  try {
    const s = await getPressureStats()
    avgSave.value = s.avg_energy_save_pct
    await nextTick()
    if (periodEl.value && !periodChart) periodChart = initChart(periodEl.value)
    periodChart?.setOption(pieOption(s.by_period, '调度方案时段分布'), true)
  } catch (e) {
    console.error('压力统计加载失败', e)
  }
}

function onResize() { periodChart?.resize() }

// ---------------- 泵站列表 ----------------
const stations = ref<PumpStation[]>([])

async function loadStations() {
  try {
    const d = await getStations()
    stations.value = d.items
  } catch (e: any) {
    ElMessage.error('泵站加载失败：' + (e?.message || e))
  }
}

// ---------------- 生成调度方案 ----------------
const planVisible = ref(false)
const planTarget = ref<PumpStation | null>(null)
const planRef = ref<FormInstance>()
const planning = ref(false)
const planForm = reactive({
  period: '夜间低谷',
  terrain_delta_m: undefined as number | undefined
})
const planRules = { period: [{ required: true, message: '请选择时段', trigger: 'change' }] }

function openPlan(row: PumpStation) {
  planTarget.value = row
  Object.assign(planForm, { period: '夜间低谷', terrain_delta_m: undefined })
  planVisible.value = true
}

async function submitPlan() {
  if (!planRef.value || !planTarget.value) return
  await planRef.value.validate(async valid => {
    if (!valid) return
    planning.value = true
    try {
      const r = await makePlan({ station_id: planTarget.value!.id, ...planForm })
      ElMessage.success(`方案已生成：目标压力 ${r.target_pressure_mpa}MPa，节能 ${r.energy_save_pct}%，爆管风险${r.burst_risk}`)
      planVisible.value = false
      loadStations(); loadPlans(); loadCharts(); emit('changed')
    } catch (e: any) {
      ElMessage.error(e?.response?.data?.detail || e?.message || '生成失败')
    } finally {
      planning.value = false
    }
  })
}

// ---------------- 方案列表 ----------------
const plans = ref<PressurePlan[]>([])
const planLoading = ref(false)

async function loadPlans() {
  planLoading.value = true
  try {
    const d = await getPlans()
    plans.value = d.items
  } catch (e: any) {
    ElMessage.error('方案列表加载失败：' + (e?.message || e))
  } finally {
    planLoading.value = false
  }
}

async function doApply(row: PressurePlan) {
  await applyPlan(row.id)
  ElMessage.success(`方案已执行：${row.station_name} 调压至 ${row.target_pressure_mpa}MPa`)
  loadPlans(); loadStations(); emit('changed')
}

onMounted(() => {
  loadStations()
  loadPlans()
  loadCharts()
  window.addEventListener('resize', onResize)
})
onBeforeUnmount(() => {
  window.removeEventListener('resize', onResize)
  periodChart?.dispose()
})
</script>

<template>
  <div>
    <div class="panel">
      <div class="panel-title">智能压力调度
        <span class="tip">平均节能 {{ avgSave }}% · 依据用水峰谷时段与地形高差自动计算泵站调节方案，节能降压、降低爆管隐患</span>
      </div>
      <div class="chart-row">
        <div>
          <div ref="periodEl" class="chart-box"></div>
        </div>
        <div>
          <div class="sub-title">泵站运行状态</div>
          <el-table :data="stations" size="small" border>
            <el-table-column prop="code" label="泵站编号" width="90" />
            <el-table-column prop="name" label="名称" min-width="140" />
            <el-table-column prop="district" label="区域" width="80" align="center" />
            <el-table-column label="供水高程(m)" width="100" align="right">
              <template #default="{ row }">{{ fmt(row.supply_elev_m) }}</template>
            </el-table-column>
            <el-table-column label="当前压力(MPa)" width="115" align="right">
              <template #default="{ row }">
                <span :style="{ color: row.current_pressure_mpa > 0.5 ? '#f56c6c' : '' }">{{ fmt(row.current_pressure_mpa, 2) }}</span>
              </template>
            </el-table-column>
            <el-table-column label="额定流量(m3/h)" width="115" align="right">
              <template #default="{ row }">{{ fmt(row.rated_flow_m3h, 0) }}</template>
            </el-table-column>
            <el-table-column label="操作" width="110" fixed="right">
              <template #default="{ row }">
                <el-button link type="primary" size="small" @click="openPlan(row)">生成方案</el-button>
              </template>
            </el-table-column>
          </el-table>
        </div>
      </div>
    </div>

    <div class="panel">
      <div class="panel-title">调度方案档案<span class="tip">峰谷时段 + 地形高差 → 目标压力 / 节能率 / 爆管风险降幅</span></div>
      <el-table :data="plans" v-loading="planLoading" size="small" border stripe>
        <el-table-column prop="station_code" label="泵站" width="90" />
        <el-table-column prop="station_name" label="泵站名称" min-width="140" />
        <el-table-column prop="period" label="时段" width="90" align="center" />
        <el-table-column label="地形高差(m)" width="100" align="right">
          <template #default="{ row }">{{ fmt(row.terrain_delta_m) }}</template>
        </el-table-column>
        <el-table-column label="当前压力(MPa)" width="115" align="right">
          <template #default="{ row }">{{ fmt(row.current_pressure_mpa, 2) }}</template>
        </el-table-column>
        <el-table-column label="目标压力(MPa)" width="115" align="right">
          <template #default="{ row }">
            <span style="color:#409eff;font-weight:700">{{ fmt(row.target_pressure_mpa, 2) }}</span>
          </template>
        </el-table-column>
        <el-table-column label="节能率(%)" width="90" align="right">
          <template #default="{ row }">{{ fmt(row.energy_save_pct) }}</template>
        </el-table-column>
        <el-table-column prop="burst_risk_reduce" label="爆管风险变化" min-width="120" />
        <el-table-column label="状态" width="85" align="center">
          <template #default="{ row }">
            <el-tag :type="row.status === '已执行' ? 'success' : 'warning'" size="small">{{ row.status }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="生成时间" width="130">
          <template #default="{ row }">{{ fmtTs(row.created_ts) }}</template>
        </el-table-column>
        <el-table-column label="操作" width="90" fixed="right">
          <template #default="{ row }">
            <el-button v-if="row.status === '已生成'" link type="primary" size="small" @click="doApply(row)">执行</el-button>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <!-- 生成方案 -->
    <el-dialog v-model="planVisible" :title="`智能调度方案 · ${planTarget?.name ?? ''}`" width="480px" :close-on-click-modal="false">
      <el-form ref="planRef" :model="planForm" :rules="planRules" label-width="120px">
        <el-form-item label="用水时段" prop="period">
          <el-select v-model="planForm.period" style="width:100%">
            <el-option label="早高峰" value="早高峰" />
            <el-option label="晚高峰" value="晚高峰" />
            <el-option label="日间平峰" value="日间平峰" />
            <el-option label="夜间低谷" value="夜间低谷" />
          </el-select>
        </el-form-item>
        <el-form-item label="地形高差(m)">
          <el-input-number v-model="planForm.terrain_delta_m" :min="0" :precision="1" :controls="false" style="width:100%"
                           :placeholder="`默认按供水高程估算 ${fmt((planTarget?.supply_elev_m ?? 0) * 0.2)}`" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="planVisible = false">取消</el-button>
        <el-button type="primary" :loading="planning" @click="submitPlan">自动计算调节方案</el-button>
      </template>
    </el-dialog>
  </div>
</template>
