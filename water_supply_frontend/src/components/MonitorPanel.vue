<script setup lang="ts">
import { nextTick, onBeforeUnmount, onMounted, reactive, ref } from 'vue'
import { ElMessage, type FormInstance } from 'element-plus'
import {
  collectMonitor, getAlarmTrend, getAlarms, getHistory, getLatest, getMonitorStats, handleAlarm
} from '../api'
import type { Alarm, MonitorLatest } from '../types'
import { barOption, historyLineOption, initChart, levelPieOption, trendStackOption } from '../utils/chart'
import { fmt, fmtTs, levelTagType, statusTagType } from '../utils/format'

const emit = defineEmits<{ (e: 'changed'): void }>()

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

async function doHandle(row: Alarm) {
  await handleAlarm(row.id)
  ElMessage.success(`告警 ${row.alarm_code} 已处理`)
  loadAlarms(); emit('changed')
}

// ---------------- 采集数据 ----------------
const pipeOptions = ref<{ id: number; code: string; name: string }[]>([])
const collectVisible = ref(false)
const collecting = ref(false)
const collectRef = ref<FormInstance>()
const collectForm = reactive({
  pipe_id: undefined as number | undefined,
  pressure_mpa: undefined as number | undefined,
  flow_m3h: undefined as number | undefined,
  level_cm: undefined as number | undefined,
  turbidity_ntu: undefined as number | undefined,
  residual_cl: undefined as number | undefined,
  deformation_mm: undefined as number | undefined
})
const collectRules = { pipe_id: [{ required: true, message: '请选择管道', trigger: 'change' }] }

function openCollect(row?: MonitorLatest) {
  Object.assign(collectForm, {
    pipe_id: row ? row.id : undefined,
    pressure_mpa: row?.pressure_mpa ?? undefined,
    flow_m3h: row?.flow_m3h ?? undefined,
    level_cm: row?.level_cm ?? undefined,
    turbidity_ntu: row?.turbidity_ntu ?? undefined,
    residual_cl: row?.residual_cl ?? undefined,
    deformation_mm: row?.deformation_mm ?? undefined
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
  historyTitle.value = `${row.code} · ${row.name}`
  historyVisible.value = true
  try {
    const d = await getHistory(row.id)
    const recs = [...d.records].reverse()
    const times = recs.map(r => fmtTs(r.ts).slice(5))
    await nextTick()
    if (historyEl.value && !historyChart) historyChart = initChart(historyEl.value)
    historyChart?.setOption(historyLineOption(times, [
      { name: '压力(MPa)', data: recs.map(r => r.pressure_mpa ?? null) },
      { name: '流量(m3/h)', data: recs.map(r => r.flow_m3h ?? null) },
      { name: '液位(cm)', data: recs.map(r => r.level_cm ?? null) },
      { name: '形变(mm)', data: recs.map(r => r.deformation_mm ?? null) }
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
  const st = await getLatest().catch(() => null)
  if (st) pipeOptions.value = st.items.map(m => ({ id: m.id, code: m.code, name: m.name }))
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
        <span class="tip">今日采集 {{ monitorToday }} 条监测数据 · 阈值：压力 0.15-0.6MPa / 形变 5mm / 浊度 1NTU / 余氯 0.05mg/L / 液位 20cm</span>
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
      <div class="panel-title">管道全时段在线监测</div>
      <div class="toolbar">
        <el-input v-model="latestQuery.keyword" placeholder="编号 / 名称 / 道路 / 区域" clearable
                  style="width:210px" @keyup.enter="loadLatest" @clear="loadLatest" />
        <el-switch v-model="latestQuery.only_abnormal" active-text="仅看异常管道" @change="loadLatest" />
        <el-button type="primary" @click="loadLatest">查询</el-button>
        <div class="spacer"></div>
        <el-button @click="refreshAll">刷新</el-button>
        <el-button type="primary" plain @click="openCollect()">+ 采集监测数据</el-button>
      </div>

      <el-table :data="latestRows" v-loading="latestLoading" size="small" border stripe>
        <el-table-column prop="code" label="管道编号" width="100" />
        <el-table-column label="名称 / 道路" min-width="200">
          <template #default="{ row }">
            {{ row.name }}<div class="cell-sub">{{ row.road_name }} · {{ row.district }}</div>
          </template>
        </el-table-column>
        <el-table-column label="压力(MPa)" width="90" align="right">
          <template #default="{ row }">
            <span :style="{ color: (row.pressure_mpa > 0.6 || row.pressure_mpa < 0.15) ? '#f56c6c' : '', fontWeight: (row.pressure_mpa > 0.6 || row.pressure_mpa < 0.15) ? 700 : 400 }">
              {{ fmt(row.pressure_mpa, 2) }}
            </span>
          </template>
        </el-table-column>
        <el-table-column label="流量(m3/h)" width="95" align="right">
          <template #default="{ row }">{{ fmt(row.flow_m3h) }}</template>
        </el-table-column>
        <el-table-column label="液位(cm)" width="85" align="right">
          <template #default="{ row }">
            <span :style="{ color: row.level_cm < 20 ? '#e6a23c' : '' }">{{ fmt(row.level_cm) }}</span>
          </template>
        </el-table-column>
        <el-table-column label="浊度(NTU)" width="90" align="right">
          <template #default="{ row }">
            <span :style="{ color: row.turbidity_ntu > 1 ? '#f56c6c' : '' }">{{ fmt(row.turbidity_ntu, 2) }}</span>
          </template>
        </el-table-column>
        <el-table-column label="余氯(mg/L)" width="95" align="right">
          <template #default="{ row }">
            <span :style="{ color: row.residual_cl < 0.05 ? '#f56c6c' : '' }">{{ fmt(row.residual_cl, 2) }}</span>
          </template>
        </el-table-column>
        <el-table-column label="形变(mm)" width="85" align="right">
          <template #default="{ row }">
            <span :style="{ color: row.deformation_mm > 5 ? '#f56c6c' : '' }">{{ fmt(row.deformation_mm) }}</span>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="80" align="center">
          <template #default="{ row }">
            <el-tag :type="statusTagType(row.status)" size="small">{{ row.status }}</el-tag>
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
      <div class="panel-title">风险告警清单<span class="tip">异常数据自动生成，含管网/DMA/水质/二供/消防栓多来源</span></div>
      <div class="toolbar">
        <el-select v-model="alarmQuery.status" placeholder="全部状态" clearable style="width:120px" @change="searchAlarms">
          <el-option label="待处理" value="待处理" />
          <el-option label="已处理" value="已处理" />
        </el-select>
        <el-select v-model="alarmQuery.level" placeholder="全部等级" clearable style="width:110px" @change="searchAlarms">
          <el-option label="高" value="高" />
          <el-option label="中" value="中" />
          <el-option label="低" value="低" />
        </el-select>
        <el-select v-model="alarmQuery.type" placeholder="全部告警类型" clearable style="width:150px" @change="searchAlarms">
          <el-option label="高压告警" value="高压告警" />
          <el-option label="低压告警" value="低压告警" />
          <el-option label="管道形变" value="管道形变" />
          <el-option label="浊度超标" value="浊度超标" />
          <el-option label="余氯不足" value="余氯不足" />
          <el-option label="漏损告警" value="漏损告警" />
          <el-option label="二供告警" value="二供告警" />
          <el-option label="消防栓告警" value="消防栓告警" />
        </el-select>
        <el-button type="primary" @click="searchAlarms">查询</el-button>
      </div>

      <el-table :data="alarmRows" v-loading="alarmLoading" size="small" border stripe>
        <el-table-column prop="alarm_code" label="告警编号" width="140" />
        <el-table-column prop="source" label="来源" width="90" align="center" />
        <el-table-column label="管道 / 位置" min-width="200">
          <template #default="{ row }">
            {{ row.code || '-' }}<div class="cell-sub">{{ row.name || row.detail }}</div>
          </template>
        </el-table-column>
        <el-table-column prop="type" label="告警类型" width="110" align="center" />
        <el-table-column label="等级" width="70" align="center">
          <template #default="{ row }">
            <el-tag :type="levelTagType(row.level)" size="small">{{ row.level }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="detail" label="告警详情" min-width="240" show-overflow-tooltip />
        <el-table-column label="告警时间" width="130">
          <template #default="{ row }">{{ fmtTs(row.alarm_ts) }}</template>
        </el-table-column>
        <el-table-column label="状态" width="90" align="center">
          <template #default="{ row }">
            <el-tag :type="row.status === '已处理' ? 'success' : 'danger'" size="small">{{ row.status }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="90" fixed="right">
          <template #default="{ row }">
            <el-button v-if="row.status === '待处理'" link type="primary" size="small" @click="doHandle(row)">处理</el-button>
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
    <el-dialog v-model="collectVisible" title="采集管道多维监测数据" width="520px" :close-on-click-modal="false">
      <el-form ref="collectRef" :model="collectForm" :rules="collectRules" label-width="110px">
        <el-form-item label="管道" prop="pipe_id">
          <el-select v-model="collectForm.pipe_id" filterable placeholder="请选择管道" style="width:100%">
            <el-option v-for="m in pipeOptions" :key="m.id" :label="`${m.code}　${m.name}`" :value="m.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="压力(MPa)">
          <el-input-number v-model="collectForm.pressure_mpa" :min="0" :max="1.2" :precision="2" :controls="false" style="width:100%" />
        </el-form-item>
        <el-form-item label="流量(m3/h)">
          <el-input-number v-model="collectForm.flow_m3h" :min="0" :precision="1" :controls="false" style="width:100%" />
        </el-form-item>
        <el-form-item label="液位(cm)">
          <el-input-number v-model="collectForm.level_cm" :min="0" :precision="1" :controls="false" style="width:100%" />
        </el-form-item>
        <el-form-item label="浊度(NTU)">
          <el-input-number v-model="collectForm.turbidity_ntu" :min="0" :precision="2" :controls="false" style="width:100%" />
        </el-form-item>
        <el-form-item label="余氯(mg/L)">
          <el-input-number v-model="collectForm.residual_cl" :min="0" :precision="2" :controls="false" style="width:100%" />
        </el-form-item>
        <el-form-item label="形变(mm)">
          <el-input-number v-model="collectForm.deformation_mm" :min="0" :precision="1" :controls="false" style="width:100%" />
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
