<script setup lang="ts">
import { nextTick, onBeforeUnmount, onMounted, reactive, ref, watch } from 'vue'
import { ElMessage, type FormInstance } from 'element-plus'
import {
  collectMonitor, getAlarmTrend, getAlarms, getArchives, getHistory, getLatest, getMonitorStats
} from '../api'
import type { Alarm, MonitorLatest } from '../types'
import { barOption, historyLineOption, initChart, levelPieOption, trendStackOption } from '../utils/chart'
import { damageTagType, flowStatusTag, fmt, fmtTs, levelTagType, manholeStatusTag } from '../utils/format'

const emit = defineEmits<{ (e: 'changed'): void }>()
const props = defineProps<{ active?: boolean }>()

// 切换到本页签时重新拉取，避免其它页签写入后数据陈旧
watch(() => props.active, v => { if (v) refreshAll() })

// ---------------- 图表 ----------------
const trendEl = ref<HTMLElement>()
const levelEl = ref<HTMLElement>()
const typeEl = ref<HTMLElement>()
let trendChart: ReturnType<typeof initChart> | null = null
let levelChart: ReturnType<typeof initChart> | null = null
let typeChart: ReturnType<typeof initChart> | null = null
const monitorToday = ref(0)

async function loadCharts() {
  try {
    const [trend, stats] = await Promise.all([getAlarmTrend(), getMonitorStats()])
    monitorToday.value = stats.monitor_today
    await nextTick()
    if (trendEl.value && !trendChart) trendChart = initChart(trendEl.value)
    if (levelEl.value && !levelChart) levelChart = initChart(levelEl.value)
    if (typeEl.value && !typeChart) typeChart = initChart(typeEl.value)
    trendChart?.setOption(trendStackOption(trend.days, trend.series), true)
    levelChart?.setOption(levelPieOption(stats.by_level, '告警等级分布'), true)
    typeChart?.setOption(barOption(stats.by_type, '#409eff', true), true)
  } catch (e) {
    console.error('监测统计加载失败', e)
  }
}

function onResize() { trendChart?.resize(); levelChart?.resize(); typeChart?.resize() }

// ---------------- 实时监测列表 ----------------
const latestQuery = reactive({ keyword: '', only_abnormal: false })
const latestRows = ref<MonitorLatest[]>([])
const latestLoading = ref(false)

async function loadLatest() {
  latestLoading.value = true
  try {
    const d = await getLatest({
      keyword: latestQuery.keyword || undefined,
      only_abnormal: latestQuery.only_abnormal || undefined
    })
    latestRows.value = d.items
  } catch (e: any) {
    ElMessage.error('实时监测加载失败：' + (e?.message || e))
  } finally {
    latestLoading.value = false
  }
}

// ---------------- 告警列表 ----------------
const alarmQuery = reactive({ status: '', level: '', type: '', page: 1, page_size: 8 })
const alarmTotal = ref(0)
const alarmRows = ref<Alarm[]>([])
const alarmLoading = ref(false)

async function loadAlarms() {
  alarmLoading.value = true
  try {
    const d = await getAlarms({
      status: alarmQuery.status || undefined, level: alarmQuery.level || undefined,
      type: alarmQuery.type || undefined, page: alarmQuery.page, page_size: alarmQuery.page_size
    })
    alarmRows.value = d.items
    alarmTotal.value = d.total
  } catch (e: any) {
    ElMessage.error('告警列表加载失败：' + (e?.message || e))
  } finally {
    alarmLoading.value = false
  }
}

function searchAlarms() { alarmQuery.page = 1; loadAlarms() }
function resetAlarms() { alarmQuery.status = ''; alarmQuery.level = ''; alarmQuery.type = ''; searchAlarms() }

// ---------------- 采集数据 ----------------
const manholeOptions = ref<{ id: number; code: string; location: string }[]>([])
const collectVisible = ref(false)
const collecting = ref(false)
const collectRef = ref<FormInstance>()
const collectForm = reactive({
  manhole_id: undefined as number | undefined,
  tilt_deg: undefined as number | undefined,
  displacement_mm: undefined as number | undefined,
  damage: '完好',
  water_level_cm: undefined as number | undefined,
  gas_ppm: undefined as number | undefined
})
const collectRules = { manhole_id: [{ required: true, message: '请选择井盖', trigger: 'change' }] }

function openCollect(row?: MonitorLatest) {
  Object.assign(collectForm, {
    manhole_id: row ? row.id : undefined, tilt_deg: row?.tilt_deg ?? undefined,
    displacement_mm: row?.displacement_mm ?? undefined, damage: row?.damage || '完好',
    water_level_cm: row?.water_level_cm ?? undefined, gas_ppm: row?.gas_ppm ?? undefined
  })
  collectVisible.value = true
}

async function submitCollect() {
  if (!collectRef.value) return
  await collectRef.value.validate(async valid => {
    if (!valid) return
    collecting.value = true
    try {
      const payload: any = { ...collectForm }
      Object.keys(payload).forEach(k => { if (payload[k] === '' || payload[k] === undefined) delete payload[k] })
      const r = await collectMonitor(payload)
      if (r.alarms_created?.length) {
        ElMessage.warning(`采集成功，自动产生 ${r.alarms_created.length} 条告警：` +
          r.alarms_created.map(a => `${a.type}（${a.level}）`).join('、'))
      } else {
        ElMessage.success('采集成功，各项指标正常')
      }
      collectVisible.value = false
      loadLatest(); loadAlarms(); loadCharts(); emit('changed')
    } catch (e: any) {
      ElMessage.error(e?.response?.data?.detail || e?.message || '采集失败')
    } finally {
      collecting.value = false
    }
  })
}

// ---------------- 历史曲线 ----------------
const historyVisible = ref(false)
const historyTitle = ref('')
const historyEl = ref<HTMLElement>()
let historyChart: ReturnType<typeof initChart> | null = null

async function openHistory(row: MonitorLatest) {
  historyTitle.value = `${row.code} · ${row.location || row.road_name}`
  historyVisible.value = true
  try {
    const d = await getHistory(row.id)
    const recs = [...d.records].reverse()
    const times = recs.map(r => fmtTs(r.ts).slice(5))
    await nextTick()
    if (historyEl.value && !historyChart) historyChart = initChart(historyEl.value)
    historyChart?.setOption(historyLineOption(times, [
      { name: '倾角(°)', data: recs.map(r => r.tilt_deg ?? null) },
      { name: '位移(mm)', data: recs.map(r => r.displacement_mm ?? null) },
      { name: '水位(cm)', data: recs.map(r => r.water_level_cm ?? null) },
      { name: '气体(ppm)', data: recs.map(r => r.gas_ppm ?? null) }
    ]), true)
    historyChart?.resize()
  } catch (e: any) {
    ElMessage.error('历史数据加载失败：' + (e?.message || e))
  }
}

function closeHistory() {
  historyChart?.dispose()
  historyChart = null
}

function refreshAll() { loadLatest(); loadAlarms(); loadCharts() }

onMounted(async () => {
  loadLatest()
  loadAlarms()
  loadCharts()
  window.addEventListener('resize', onResize)
  const arc = await getArchives({ page: 1, page_size: 100 }).catch(() => null)
  if (arc) manholeOptions.value = arc.items.map(m => ({ id: m.id, code: m.code, location: m.location }))
})
onBeforeUnmount(() => {
  window.removeEventListener('resize', onResize)
  trendChart?.dispose(); levelChart?.dispose(); typeChart?.dispose(); historyChart?.dispose()
})
</script>

<template>
  <div>
    <div class="panel">
      <div class="panel-title">告警态势
        <span class="tip">今日采集 {{ monitorToday }} 条监测数据 · 阈值：倾角 15° / 位移 10mm / 被盗异动 30mm / 水位 80cm / 气体 10ppm</span>
      </div>
      <div class="chart-row three">
        <div>
          <div class="chart-caption">近 7 日告警趋势（按等级）</div>
          <div ref="trendEl" class="chart-box"></div>
        </div>
        <div>
          <div ref="levelEl" class="chart-box"></div>
        </div>
        <div>
          <div class="chart-caption">告警类型分布（条）</div>
          <div ref="typeEl" class="chart-box"></div>
        </div>
      </div>
    </div>

    <div class="panel">
      <div class="panel-title">井盖多维状态实时监测</div>
      <div class="toolbar">
        <el-input v-model="latestQuery.keyword" placeholder="编号 / 位置 / 道路" clearable
                  style="width:210px" @keyup.enter="loadLatest" @clear="loadLatest" />
        <el-switch v-model="latestQuery.only_abnormal" active-text="仅看异常井盖" @change="loadLatest" />
        <el-button type="primary" @click="loadLatest">查询</el-button>
        <div class="spacer"></div>
        <el-button @click="refreshAll">刷新</el-button>
        <el-button type="primary" plain @click="openCollect()">+ 采集监测数据</el-button>
      </div>

      <el-table :data="latestRows" v-loading="latestLoading" size="small" border stripe>
        <el-table-column prop="code" label="井盖编号" width="110" />
        <el-table-column label="位置 / 道路" min-width="200">
          <template #default="{ row }">
            {{ row.location }}<div class="cell-sub">{{ row.road_name }} · {{ row.district }}</div>
          </template>
        </el-table-column>
        <el-table-column prop="type" label="类型" width="70" align="center" />
        <el-table-column label="倾角(°)" width="85" align="right">
          <template #default="{ row }">
            <span :style="{ color: row.tilt_deg >= 15 ? '#f56c6c' : '', fontWeight: row.tilt_deg >= 15 ? 700 : 400 }">
              {{ fmt(row.tilt_deg) }}
            </span>
          </template>
        </el-table-column>
        <el-table-column label="位移(mm)" width="90" align="right">
          <template #default="{ row }">
            <span :style="{ color: row.displacement_mm >= 10 ? '#f56c6c' : '', fontWeight: row.displacement_mm >= 10 ? 700 : 400 }">
              {{ fmt(row.displacement_mm) }}
            </span>
          </template>
        </el-table-column>
        <el-table-column label="破损状态" width="95" align="center">
          <template #default="{ row }">
            <el-tag :type="damageTagType(row.damage)" size="small">{{ row.damage || '完好' }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="水位(cm)" width="85" align="right">
          <template #default="{ row }">
            <span :style="{ color: row.water_level_cm >= 80 ? '#e6a23c' : '' }">{{ fmt(row.water_level_cm) }}</span>
          </template>
        </el-table-column>
        <el-table-column label="气体(ppm)" width="90" align="right">
          <template #default="{ row }">
            <span :style="{ color: row.gas_ppm >= 10 ? '#f56c6c' : '' }">{{ fmt(row.gas_ppm) }}</span>
          </template>
        </el-table-column>
        <el-table-column label="井盖状态" width="90" align="center">
          <template #default="{ row }">
            <el-tag :type="manholeStatusTag(row.status)" size="small">{{ row.status }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="采集时间" width="130">
          <template #default="{ row }">{{ fmtTs(row.ts) }}</template>
        </el-table-column>
        <el-table-column label="操作" width="150" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" size="small" @click="openCollect(row)">采集</el-button>
            <el-button link type="primary" size="small" @click="openHistory(row)">历史曲线</el-button>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <div class="panel">
      <div class="panel-title">风险告警清单<span class="tip">异常数据自动生成，同步派发处置工单</span></div>
      <div class="toolbar">
        <el-select v-model="alarmQuery.status" placeholder="全部处理状态" clearable style="width:140px" @change="searchAlarms">
          <el-option label="待派发" value="待派发" />
          <el-option label="已派发" value="已派发" />
          <el-option label="处置中" value="处置中" />
          <el-option label="已核验" value="已核验" />
          <el-option label="已闭环" value="已闭环" />
        </el-select>
        <el-select v-model="alarmQuery.level" placeholder="全部等级" clearable style="width:110px" @change="searchAlarms">
          <el-option label="高" value="高" />
          <el-option label="中" value="中" />
          <el-option label="低" value="低" />
        </el-select>
        <el-select v-model="alarmQuery.type" placeholder="全部告警类型" clearable style="width:150px" @change="searchAlarms">
          <el-option label="被盗异动" value="被盗异动" />
          <el-option label="位移异常" value="位移异常" />
          <el-option label="倾角异常" value="倾角异常" />
          <el-option label="井盖破损" value="井盖破损" />
          <el-option label="轻微裂缝" value="轻微裂缝" />
          <el-option label="水位告警" value="水位告警" />
          <el-option label="有毒气体告警" value="有毒气体告警" />
        </el-select>
        <el-button type="primary" @click="searchAlarms">查询</el-button>
        <el-button @click="resetAlarms">重置</el-button>
      </div>

      <el-table :data="alarmRows" v-loading="alarmLoading" size="small" border stripe>
        <el-table-column prop="alarm_code" label="告警编号" width="150" />
        <el-table-column label="井盖 / 位置" min-width="220">
          <template #default="{ row }">
            {{ row.code }}<div class="cell-sub">{{ row.location }}</div>
          </template>
        </el-table-column>
        <el-table-column prop="type" label="告警类型" width="110" align="center" />
        <el-table-column label="等级" width="70" align="center">
          <template #default="{ row }">
            <el-tag :type="levelTagType(row.level)" size="small">{{ row.level }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="detail" label="告警详情" min-width="230" show-overflow-tooltip />
        <el-table-column label="告警时间" width="130">
          <template #default="{ row }">{{ fmtTs(row.alarm_ts) }}</template>
        </el-table-column>
        <el-table-column label="处理状态" width="95" align="center">
          <template #default="{ row }">
            <el-tag :type="flowStatusTag(row.status)" size="small">{{ row.status }}</el-tag>
          </template>
        </el-table-column>
      </el-table>

      <div style="margin-top:12px;display:flex;justify-content:flex-end">
        <el-pagination v-model:current-page="alarmQuery.page" v-model:page-size="alarmQuery.page_size"
                       :total="alarmTotal" :page-sizes="[8, 15, 30]" layout="total, sizes, prev, pager, next"
                       @current-change="loadAlarms" @size-change="searchAlarms" />
      </div>
    </div>

    <!-- 采集监测数据 -->
    <el-dialog v-model="collectVisible" title="采集井盖多维监测数据" width="520px" :close-on-click-modal="false">
      <el-form ref="collectRef" :model="collectForm" :rules="collectRules" label-width="110px">
        <el-form-item label="井盖" prop="manhole_id">
          <el-select v-model="collectForm.manhole_id" filterable placeholder="请选择井盖" style="width:100%">
            <el-option v-for="m in manholeOptions" :key="m.id" :label="`${m.code}　${m.location}`" :value="m.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="倾角(°)">
          <el-input-number v-model="collectForm.tilt_deg" :min="0" :max="90" :precision="1" :controls="false" style="width:100%" />
        </el-form-item>
        <el-form-item label="位移(mm)">
          <el-input-number v-model="collectForm.displacement_mm" :min="0" :precision="1" :controls="false" style="width:100%" />
        </el-form-item>
        <el-form-item label="破损状态">
          <el-radio-group v-model="collectForm.damage">
            <el-radio value="完好">完好</el-radio>
            <el-radio value="轻微裂缝">轻微裂缝</el-radio>
            <el-radio value="破损">破损</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="井下水位(cm)">
          <el-input-number v-model="collectForm.water_level_cm" :min="0" :precision="1" :controls="false" style="width:100%" />
        </el-form-item>
        <el-form-item label="有毒气体(ppm)">
          <el-input-number v-model="collectForm.gas_ppm" :min="0" :precision="1" :controls="false" style="width:100%" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="collectVisible = false">取消</el-button>
        <el-button type="primary" :loading="collecting" @click="submitCollect">提交并自动研判</el-button>
      </template>
    </el-dialog>

    <!-- 历史曲线 -->
    <el-dialog v-model="historyVisible" :title="`监测历史曲线 · ${historyTitle}`" width="760px"
               @closed="closeHistory">
      <div ref="historyEl" class="chart-box tall"></div>
    </el-dialog>
  </div>
</template>
