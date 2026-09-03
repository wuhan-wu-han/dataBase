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

    <!-- 仪表盘 + 历史趋势 1:1 布局 -->
    <div class="gas-risk__row">
      <!-- 左侧：实时监测仪表盘 -->
      <section class="app-card gas-risk__panel gas-risk__panel--gauge">
        <header class="card-title">
          <h3 class="card-title__text">实时监测</h3>
          <el-select v-model="curSensorId" size="small" @change="refreshAll" placeholder="选择测站">
            <el-option
              v-for="s in sensors"
              :key="s.id"
              :label="`${s.name}（${s.position_km}km）`"
              :value="s.id"
            />
          </el-select>
        </header>

        <!-- 仪表盘区域：ECharts + 外部 DOM 数值/标题 -->
        <div class="gauge-wrap">
          <div ref="gaugeRef" class="gauge-wrap__chart"></div>

          <!-- ECharts 内部 detail/title 已关闭，用外部 DOM 精准定位 -->
          <div class="gauge-wrap__center">
            <div class="gauge-wrap__label">管内压力</div>
            <div class="gauge-wrap__value">{{ gaugeData.pressure.toFixed(2) }}</div>
            <div class="gauge-wrap__unit">MPa</div>
          </div>
        </div>

        <!-- 仪表盘下方三指标卡 -->
        <div class="gauge-metrics">
          <div class="gauge-metric">
            <div class="gauge-metric__label">当前压力</div>
            <div class="gauge-metric__value">{{ gaugeData.pressure.toFixed(2) }} <span class="gauge-metric__unit">MPa</span></div>
          </div>
          <div class="gauge-metric">
            <div class="gauge-metric__label">当前浓度</div>
            <div class="gauge-metric__value">{{ gaugeData.leL.toFixed(2) }} <span class="gauge-metric__unit">%LEL</span></div>
          </div>
          <div class="gauge-metric">
            <div class="gauge-metric__label">状态等级</div>
            <el-tag :type="statusTagType" size="small" effect="light" class="gauge-metric__tag">
              {{ gaugeData.status }}
            </el-tag>
          </div>
        </div>
      </section>

      <!-- 右侧：历史趋势 -->
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
import { ref, reactive, computed, onMounted, onUnmounted, nextTick, shallowRef } from 'vue'
import { ElMessage } from 'element-plus'
import PageHeader from '@/components/PageHeader.vue'
import StatCard from '@/components/StatCard.vue'
import { useEChart } from '@/utils/chart'
import * as echarts from 'echarts/core'
import { LineChart } from 'echarts/charts'
import {
  TooltipComponent, GridComponent, LegendComponent
} from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'
import {
  fetchSensors, fetchRealtime, fetchAlarms, fetchHistory, fmtTs, fmtTime
} from '@/api/gasRisk'

// 注册历史图表所需组件（与 chart.js 中的注册互不冲突，幂等）
echarts.use([LineChart, TooltipComponent, GridComponent, LegendComponent, CanvasRenderer])

// ---------- 测站 & 状态 ----------
const sensors = ref([])
const curSensorId = ref(null)
const loading = ref(false)

// 统计卡片数据
const stats = reactive({
  sensors: 0,
  alarming: 0,
  maxLel: '0.00',
  pressureRange: '-'
})

// 仪表盘数据（驱动外部 DOM）
const gaugeData = reactive({
  pressure: 0,
  leL: 0,
  status: '正常',
  alarmLevel: 0
})

// 状态等级 → 标签类型
const statusTagType = computed(() => {
  const lv = gaugeData.alarmLevel
  if (lv >= 2) return 'danger'
  if (lv === 1) return 'warning'
  return 'success'
})

// 报警列表
const alarms = ref([])

// ---------- ECharts ----------
const gaugeRef = ref(null)
const historyRef = ref(null)
const { setOption: setGaugeOption } = useEChart(gaugeRef)

// 历史图表独立实例（绕过 useEChart，确保初始化时序可控）
const historyChart = shallowRef(null)
let historyRO = null
function ensureHistoryChart() {
  if (historyChart.value) return
  if (!historyRef.value) return
  historyChart.value = echarts.init(historyRef.value, null, { renderer: 'canvas' })
  if (typeof ResizeObserver !== 'undefined') {
    historyRO = new ResizeObserver(() => historyChart.value && historyChart.value.resize())
    historyRO.observe(historyRef.value)
  }
}

let pollTimer = null

// ---------- 数据加载 ----------
async function loadSensors() {
  sensors.value = await fetchSensors()
  if (sensors.value.length) curSensorId.value = sensors.value[0].id
}

async function refreshRealtime() {
  const r = await fetchRealtime()
  const rows = r.data || []

  // 汇总统计
  stats.sensors = rows.length
  stats.alarming = rows.filter(d => d.alarm_level > 0).length
  const maxLel = rows.length ? Math.max(...rows.map(d => d.lel_pct)) : 0
  stats.maxLel = maxLel.toFixed(2)
  const ps = rows.map(d => d.pressure_mpa)
  stats.pressureRange = ps.length
    ? `${Math.min(...ps).toFixed(2)} ~ ${Math.max(...ps).toFixed(2)}`
    : '-'

  // 当前测站仪表盘
  const cur = rows.find(d => d.sensor_id === curSensorId.value)
  if (cur) {
    gaugeData.pressure = cur.pressure_mpa
    gaugeData.leL = cur.lel_pct
    gaugeData.alarmLevel = cur.alarm_level || 0
    gaugeData.status = cur.alarm_level >= 2 ? '严重' : cur.alarm_level === 1 ? '预警' : '正常'
    renderGauge(cur.pressure_mpa)
  }
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
  await Promise.allSettled([refreshRealtime(), refreshAlarms(), refreshHistory()])
}

// 刷新历史趋势（完整配置 + notMerge，避免与初始空数据 merge 冲突）
async function refreshHistory() {
  if (!curSensorId.value) return
  try {
    const r = await fetchHistory(curSensorId.value, 10)
    const points = r.points || []
    if (!points.length) return
    // 均匀采样最多 60 个点，避免 X 轴过密
    const step = Math.max(1, Math.floor(points.length / 60))
    const sampled = points.filter((_, i) => i % step === 0)
    const labels = sampled.map(p => fmtTime(p.ts_ms))
    const lelData = sampled.map(p => +(p.lel_pct * 100).toFixed(2))
    const pressureData = sampled.map(p => +p.pressure_mpa.toFixed(3))

    // 完整配置一次性写入
    ensureHistoryChart()
    if (!historyChart.value) return
    historyChart.value.setOption({
      tooltip: {
        trigger: 'axis',
        backgroundColor: 'rgba(255,255,255,0.96)',
        borderColor: 'rgba(0,0,0,0.06)',
        borderWidth: 1,
        textStyle: { color: '#1D1D1F', fontFamily: 'Inter, -apple-system, sans-serif' }
      },
      legend: {
        data: ['浓度 %LEL', '压力 MPa'],
        top: 0,
        textStyle: { color: '#86868B', fontFamily: 'Inter, -apple-system, sans-serif' },
        itemWidth: 16, itemHeight: 3
      },
      grid: { left: 50, right: 30, top: 36, bottom: 30 },
      xAxis: {
        type: 'category',
        data: labels,
        axisLine: { lineStyle: { color: 'rgba(0,0,0,0.06)' } },
        axisTick: { show: false },
        axisLabel: { color: '#86868B', fontFamily: 'Inter, -apple-system, sans-serif' }
      },
      yAxis: {
        type: 'value',
        splitLine: { lineStyle: { color: 'rgba(0,0,0,0.04)' } },
        axisLabel: { color: '#86868B', fontFamily: 'Inter, -apple-system, sans-serif' }
      },
      series: [
        {
          name: '浓度 %LEL', type: 'line', smooth: true, showSymbol: false,
          data: lelData,
          lineStyle: { width: 2.5, color: '#FF9500' },
          itemStyle: { color: '#FF9500' },
          areaStyle: {
            color: {
              type: 'linear', x: 0, y: 0, x2: 0, y2: 1,
              colorStops: [
                { offset: 0, color: 'rgba(255,149,0,0.18)' },
                { offset: 1, color: 'rgba(255,149,0,0.00)' }
              ]
            }
          }
        },
        {
          name: '压力 MPa', type: 'line', smooth: true, showSymbol: false,
          data: pressureData,
          lineStyle: { width: 2.5, color: '#0071E3' },
          itemStyle: { color: '#0071E3' },
          areaStyle: {
            color: {
              type: 'linear', x: 0, y: 0, x2: 0, y2: 1,
              colorStops: [
                { offset: 0, color: 'rgba(0,113,227,0.18)' },
                { offset: 1, color: 'rgba(0,113,227,0.00)' }
              ]
            }
          }
        }
      ]
    }, true)  // notMerge = true
  } catch (e) { /* 历史数据拉取失败不阻塞主流程 */ }
}

// ---------- 仪表盘渲染 ----------
// 关闭 ECharts 内部 detail/title，用外部 DOM 渲染，彻底避免重叠
function renderGauge(pressure) {
  const clamped = Math.max(0, Math.min(pressure, 2.5))
  setGaugeOption({
    series: [{
      type: 'gauge',
      min: 0,
      max: 2.5,
      splitNumber: 5,
      startAngle: 210,
      endAngle: -30,
      radius: '85%',
      center: ['50%', '58%'],

      // 进度弧：Apple 风格浅灰底 + 蓝色进度
      progress: {
        show: true,
        width: 18,
        roundCap: true,
        itemStyle: {
          color: {
            type: 'linear', x: 0, y: 0, x2: 1, y2: 0,
            colorStops: [
              { offset: 0, color: '#5AC8FA' },
              { offset: 1, color: '#0071E3' }
            ]
          }
        }
      },

      // 背景弧
      axisLine: {
        lineStyle: {
          width: 18,
          color: [[1, 'rgba(0,0,0,0.04)']]
        }
      },

      // 刻度线
      axisTick: {
        show: true,
        distance: -18,
        length: 6,
        lineStyle: { color: 'rgba(0,0,0,0.12)', width: 1 }
      },
      splitLine: {
        show: true,
        distance: -18,
        length: 12,
        lineStyle: { color: 'rgba(0,0,0,0.20)', width: 2 }
      },

      // 刻度数字：外移避免与进度弧重叠
      axisLabel: {
        color: '#86868B',
        fontSize: 11,
        fontFamily: 'Inter, -apple-system, sans-serif',
        distance: 32
      },

      // 指针
      pointer: {
        show: true,
        length: '70%',
        width: 6,
        itemStyle: {
          color: '#1D1D1F',
          borderRadius: 3
        }
      },

      // 指针头部圆点
      anchor: {
        show: true,
        size: 14,
        itemStyle: {
          color: '#1D1D1F',
          borderColor: '#fff',
          borderWidth: 3
        }
      },

      // 关闭 ECharts 内部 detail/title——用外部 DOM 渲染避免重叠
      detail: { show: false },
      title: { show: false },

      data: [{ value: clamped }]
    }]
  })
}

// ---------- 历史趋势 ----------
function renderHistory() {
  setHistoryOption({
    tooltip: {
      trigger: 'axis',
      backgroundColor: 'rgba(255,255,255,0.96)',
      borderColor: 'rgba(0,0,0,0.06)',
      borderWidth: 1,
      textStyle: { color: '#1D1D1F', fontFamily: 'Inter, -apple-system, sans-serif' }
    },
    legend: {
      data: ['浓度 %LEL', '压力 MPa'],
      top: 0,
      textStyle: { color: '#86868B', fontFamily: 'Inter, -apple-system, sans-serif' },
      itemWidth: 16,
      itemHeight: 3
    },
    grid: { left: 50, right: 30, top: 36, bottom: 30 },
    xAxis: {
      type: 'category',
      axisLine: { lineStyle: { color: 'rgba(0,0,0,0.06)' } },
      axisTick: { show: false },
      axisLabel: { color: '#86868B', fontFamily: 'Inter, -apple-system, sans-serif' }
    },
    yAxis: {
      type: 'value',
      splitLine: { lineStyle: { color: 'rgba(0,0,0,0.04)' } },
      axisLabel: { color: '#86868B', fontFamily: 'Inter, -apple-system, sans-serif' }
    },
    series: [
      {
        name: '浓度 %LEL', type: 'line', smooth: true,
        showSymbol: false,
        data: [],
        lineStyle: { width: 2.5, color: '#FF9500' },
        itemStyle: { color: '#FF9500' },
        areaStyle: {
          color: {
            type: 'linear', x: 0, y: 0, x2: 0, y2: 1,
            colorStops: [
              { offset: 0, color: 'rgba(255,149,0,0.18)' },
              { offset: 1, color: 'rgba(255,149,0,0.00)' }
            ]
          }
        }
      },
      {
        name: '压力 MPa', type: 'line', smooth: true,
        showSymbol: false,
        data: [],
        lineStyle: { width: 2.5, color: '#0071E3' },
        itemStyle: { color: '#0071E3' },
        areaStyle: {
          color: {
            type: 'linear', x: 0, y: 0, x2: 0, y2: 1,
            colorStops: [
              { offset: 0, color: 'rgba(0,113,227,0.18)' },
              { offset: 1, color: 'rgba(0,113,227,0.00)' }
            ]
          }
        }
      }
    ]
  })
}

// ---------- 生命周期 ----------
onMounted(async () => {
  await nextTick()    // 确保 DOM 渲染完成，historyRef 可用
  try {
    await loadSensors()
    await refreshAll()
  } catch (e) {
    ElMessage.error('无法连接燃气风控服务：' + e.message)
  }
  pollTimer = setInterval(refreshAll, 2000)
})
onUnmounted(() => {
  if (pollTimer) clearInterval(pollTimer)
  if (historyRO) { historyRO.disconnect(); historyRO = null }
  if (historyChart.value) { historyChart.value.dispose(); historyChart.value = null }
})
</script>

<style scoped>
/* ===== 通用布局 ===== */
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
  padding: 24px 28px;
  display: flex;
  flex-direction: column;
}
.gas-risk__chart {
  width: 100%;
  height: 280px;
}

/* ===== 仪表盘专用 ===== */
.gas-risk__panel--gauge {
  gap: 0;
}

/* 图表 + 外部数值覆盖层容器 */
.gauge-wrap {
  position: relative;
  width: 100%;
  height: 420px;
  flex-shrink: 0;
}
.gauge-wrap__chart {
  width: 100%;
  height: 100%;
}

/* 仪表盘中心数值（ECharts detail 已关闭，用 DOM 渲染） */
.gauge-wrap__center {
  position: absolute;
  top: 46%;           /* 与 gauge center: ['50%','58%'] 配合，视觉居中 */
  left: 50%;
  transform: translate(-50%, -50%);
  text-align: center;
  pointer-events: none;
}
.gauge-wrap__label {
  font-size: 14px;
  font-weight: 500;
  color: #86868B;
  font-family: Inter, -apple-system, BlinkMacSystemFont, 'SF Pro Display', sans-serif;
  letter-spacing: 0.3px;
  margin-bottom: 6px;
}
.gauge-wrap__value {
  font-size: 40px;
  font-weight: 700;
  color: #1D1D1F;
  font-family: Inter, -apple-system, BlinkMacSystemFont, 'SF Pro Display', sans-serif;
  letter-spacing: -1.2px;
  line-height: 1;
}
.gauge-wrap__unit {
  font-size: 14px;
  font-weight: 500;
  color: #86868B;
  font-family: Inter, -apple-system, sans-serif;
  margin-top: 6px;
}

/* 仪表盘下方三指标卡 */
.gauge-metrics {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 12px;
  margin-top: 12px;
}
.gauge-metric {
  background: rgba(0, 0, 0, 0.02);
  border: 1px solid rgba(0, 0, 0, 0.05);
  border-radius: 14px;
  padding: 14px 16px;
  text-align: left;
  transition: background 0.2s;
}
.gauge-metric:hover {
  background: rgba(0, 0, 0, 0.04);
}
.gauge-metric__label {
  font-size: 12px;
  font-weight: 500;
  color: #86868B;
  font-family: Inter, -apple-system, sans-serif;
  margin-bottom: 6px;
  text-transform: none;
}
.gauge-metric__value {
  font-size: 20px;
  font-weight: 600;
  color: #1D1D1F;
  font-family: Inter, -apple-system, sans-serif;
  letter-spacing: -0.3px;
  line-height: 1.2;
}
.gauge-metric__unit {
  font-size: 12px;
  font-weight: 500;
  color: #86868B;
  margin-left: 2px;
}
.gauge-metric__tag {
  font-size: 13px;
  padding: 4px 12px;
}

/* ===== 响应式 ===== */
@media (max-width: 1024px) {
  .gas-risk__stats { grid-template-columns: repeat(2, 1fr); }
  .gas-risk__row { grid-template-columns: 1fr; }
  .gauge-wrap { height: 340px; }
}
@media (max-width: 640px) {
  .gas-risk__stats { grid-template-columns: 1fr; }
  .gauge-metrics { grid-template-columns: 1fr; }
}
</style>
