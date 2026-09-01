<template>
  <div class="gas-risk">
    <PageHeader title="燃气风控" subtitle="Gas Risk Control" />

    <!-- 统计卡片 -->
    <div class="gas-risk__stats">
      <StatCard label="监测测站" :value="stats.sensors" icon="Aim" color="#0071E3" />
      <StatCard label="告警测站" :value="stats.alarming" icon="Warning" color="#FF3B30" />
      <StatCard label="最大浓度 %LEL" :value="stats.maxLel" icon="DataLine" color="#FF9500" />
      <StatCard label="压力范围 MPa" :value="stats.pressureRange" icon="Monitor" color="#34C759" />
    </div>

    <!-- 仪表盘 + 历史 -->
    <div class="gas-risk__row">
      <section class="app-card gas-risk__panel">
        <header class="card-title">
          <h3 class="card-title__text">实时监测</h3>
          <el-select v-model="curSensorId" size="small" @change="refreshAll" placeholder="选择测站">
            <el-option v-for="s in sensors" :key="s.id" :label="`${s.name}（${s.position_km}km）`" :value="s.id" />
          </el-select>
        </header>
        <div ref="gaugeRef" class="gas-risk__chart"></div>
      </section>
      <section class="app-card gas-risk__panel">
        <header class="card-title">
          <h3 class="card-title__text">历史趋势（10 分钟）</h3>
        </header>
        <div ref="historyRef" class="gas-risk__chart"></div>
      </section>
    </div>

    <!-- 报警列表 -->
    <section class="app-card">
      <header class="card-title">
        <h3 class="card-title__text">报警事件</h3>
        <el-button size="small" @click="refreshAll">刷新</el-button>
      </header>
      <el-table :data="alarms" class="app-table" v-loading="loading" empty-text="暂无报警，工况正常">
        <el-table-column label="时间" width="170">
          <template #default="{ row }">{{ fmtTs(row.ts_ms) }}</template>
        </el-table-column>
        <el-table-column prop="sensor_name" label="测站" min-width="140" />
        <el-table-column label="等级" width="100" align="center">
          <template #default="{ row }">
            <el-tag :type="row.level === 2 ? 'danger' : 'warning'" size="small">
              {{ row.level === 2 ? '严重' : '预警' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="content" label="内容" min-width="280" show-overflow-tooltip />
      </el-table>
    </section>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, onUnmounted } from 'vue'
import { ElMessage } from 'element-plus'
import PageHeader from '@/components/PageHeader.vue'
import StatCard from '@/components/StatCard.vue'
import { useEChart } from '@/utils/chart'
import {
  fetchSensors, fetchRealtime, fetchAlarms, fmtTs
} from '@/api/gasRisk'

// 测站列表
const sensors = ref([])
const curSensorId = ref(null)
const loading = ref(false)

// 统计
const stats = reactive({
  sensors: 0,
  alarming: 0,
  maxLel: '0.00',
  pressureRange: '-'
})

// 报警
const alarms = ref([])

// ECharts
const gaugeRef = ref(null)
const historyRef = ref(null)
const { setOption: setGaugeOption } = useEChart(gaugeRef)
const { setOption: setHistoryOption } = useEChart(historyRef)

let pollTimer = null

async function loadSensors() {
  sensors.value = await fetchSensors()
  if (sensors.value.length) curSensorId.value = sensors.value[0].id
}

async function refreshRealtime() {
  const r = await fetchRealtime()
  const rows = r.data || []
  stats.sensors = rows.length
  stats.alarming = rows.filter(d => d.alarm_level > 0).length
  const maxLel = rows.length ? Math.max(...rows.map(d => d.lel_pct)) : 0
  stats.maxLel = maxLel.toFixed(2)
  const ps = rows.map(d => d.pressure_mpa)
  stats.pressureRange = ps.length ? `${Math.min(...ps).toFixed(2)} ~ ${Math.max(...ps).toFixed(2)}` : '-'
  renderGauge(rows.find(d => d.sensor_id === curSensorId.value))
}

async function refreshAlarms() {
  loading.value = true
  try {
    const r = await fetchAlarms(30)
    alarms.value = r.alarms || []
  } finally {
    loading.value = false
  }
}

async function refreshAll() {
  await Promise.allSettled([refreshRealtime(), refreshAlarms()])
}

// 仪表盘渲染：浓度 / 压力 / 流量
function renderGauge(cur) {
  if (!cur) return
  setGaugeOption({
    tooltip: { formatter: '{b}: {c}' },
    series: [
      buildGaugeSeries('燃气浓度 %LEL', Math.min(cur.lel_pct, 100), 100, cur.lel_pct >= 25 ? '#FF3B30' : cur.lel_pct >= 5 ? '#FF9500' : '#34C759'),
      buildGaugeSeries('管内压力 MPa', cur.pressure_mpa, 2.5, '#0071E3')
    ],
    grid: { top: 20, bottom: 20 }
  })
}

function buildGaugeSeries(name, value, max, color) {
  return {
    name, type: 'gauge', min: 0, max,
    progress: { show: true, width: 12, itemStyle: { color } },
    axisLine: { lineStyle: { width: 12, color: [[1, 'rgba(0,0,0,0.06)']] } },
    axisTick: { show: false },
    splitLine: { show: false },
    axisLabel: { color: '#86868B', fontSize: 10, distance: 14 },
    pointer: { width: 4, itemStyle: { color } },
    detail: {
      offsetCenter: [0, '40%'], fontSize: 18, color: '#1D1D1F',
      formatter: (v) => v.toFixed(2)
    },
    data: [{ value, name }]
  }
}

// 历史趋势渲染（简化：单条浓度曲线）
function renderHistory() {
  setHistoryOption({
    tooltip: { trigger: 'axis' },
    legend: { data: ['浓度 %LEL', '压力 MPa'], top: 0, textStyle: { color: '#86868B' } },
    grid: { left: 50, right: 30, top: 36, bottom: 30 },
    xAxis: { type: 'category', axisLine: { lineStyle: { color: 'rgba(0,0,0,0.06)' } }, axisLabel: { color: '#86868B' } },
    yAxis: { type: 'value', splitLine: { lineStyle: { color: 'rgba(0,0,0,0.04)' } }, axisLabel: { color: '#86868B' } },
    series: [
      { name: '浓度 %LEL', type: 'line', smooth: true, data: [], itemStyle: { color: '#FF9500' } },
      { name: '压力 MPa', type: 'line', smooth: true, data: [], itemStyle: { color: '#0071E3' } }
    ]
  })
}

onMounted(async () => {
  renderHistory()
  try {
    await loadSensors()
    await refreshAll()
  } catch (e) {
    ElMessage.error('无法连接燃气风控服务：' + e.message)
  }
  // 2 秒轮询
  pollTimer = setInterval(refreshAll, 2000)
})
onUnmounted(() => {
  if (pollTimer) clearInterval(pollTimer)
})
</script>

<style scoped>
.gas-risk__stats {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
  margin-bottom: 16px;
}
.gas-risk__row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
  margin-bottom: 16px;
}
.gas-risk__panel {
  padding: 20px 24px;
  display: flex;
  flex-direction: column;
}
.gas-risk__chart {
  width: 100%;
  height: 280px;
}
@media (max-width: 1024px) {
  .gas-risk__stats { grid-template-columns: repeat(2, 1fr); }
  .gas-risk__row { grid-template-columns: 1fr; }
}
</style>
