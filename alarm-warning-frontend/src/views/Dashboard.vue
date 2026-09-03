<template>
  <div class="dashboard">
    <!-- 页面级标题 -->
    <PageHeader title="监控大屏" subtitle="Monitor Dashboard" />

    <!-- 第一行：4 个 Apple 数据卡 -->
    <div class="dashboard__row dashboard__row--stats">
      <StatCard label="今日预警" :value="stats.today" icon="Bell" color="#0071E3" />
      <StatCard label="高风险预警" :value="stats.highRisk" icon="Warning" color="#FF3B30" />
      <StatCard label="处理中事件" :value="stats.processing" icon="Clock" color="#FF9500" />
      <StatCard label="设备在线率" :value="stats.deviceOnlineRate" icon="Monitor" color="#34C759" />
    </div>

    <!-- 第二行：GIS 地图（全宽，高度 600px+） -->
    <section class="app-card dashboard__map-card">
      <header class="card-title">
        <h3 class="card-title__text">GIS 一张图</h3>
        <span class="card-title__badge">实时监测</span>
      </header>
      <GISMap />
    </section>

    <!-- 第三行：风险趋势 + 预警等级 + 最新预警 -->
    <div class="dashboard__row dashboard__row--bottom">
      <section class="app-card dashboard__chart-card dashboard__chart-card--line">
        <header class="card-title">
          <h3 class="card-title__text">预警趋势</h3>
          <span class="card-title__badge">近 7 天</span>
        </header>
        <div ref="lineRef" class="dashboard__chart-canvas"></div>
      </section>
      <section class="app-card dashboard__chart-card dashboard__chart-card--pie">
        <header class="card-title">
          <h3 class="card-title__text">预警等级</h3>
        </header>
        <div ref="pieRef" class="dashboard__chart-canvas"></div>
      </section>
      <section class="app-card dashboard__latest">
        <header class="card-title">
          <h3 class="card-title__text">最新预警事件</h3>
          <router-link to="/alerts" class="dashboard__link">查看全部</router-link>
        </header>
        <el-table
          :data="latestAlerts"
          v-loading="loading"
          class="app-table"
          row-class-name="clickable-row"
          @row-click="goDetail"
        >
          <el-table-column prop="alertEventCode" label="预警编号" min-width="180" />
          <el-table-column prop="deviceType" label="设备" min-width="120" />
          <el-table-column prop="areaId" label="区域" width="120" />
          <el-table-column label="等级" width="110" align="center">
            <template #default="{ row }"><AlertLevelTag :level="row.alertLevel" /></template>
          </el-table-column>
          <el-table-column label="状态" width="110" align="center">
            <template #default="{ row }"><AlertStatusTag :status="row.alertStatus" /></template>
          </el-table-column>
          <el-table-column label="时间" width="170">
            <template #default="{ row }">{{ formatDateTime(row.eventTimestamp) }}</template>
          </el-table-column>
          <el-table-column label="操作" width="100" align="center" fixed="right">
            <template #default="{ row }">
              <el-button link type="primary" size="small" @click.stop="goDetail(row)">详情</el-button>
            </template>
          </el-table-column>
        </el-table>
      </section>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import PageHeader from '@/components/PageHeader.vue'
import StatCard from '@/components/StatCard.vue'
import AlertLevelTag from '@/components/AlertLevelTag.vue'
import AlertStatusTag from '@/components/AlertStatusTag.vue'
import GISMap from '@/views/gis/GISMap.vue'
import { useEChart } from '@/utils/chart'
import { getAlertList } from '@/api/alert'
import { formatDateTime } from '@/utils/format'

const router = useRouter()
const loading = ref(false)

// ===== 统计数据 =====
const stats = ref({
  today: 0,
  highRisk: 0,
  processing: 0,
  deviceOnlineRate: '98.6%'
})

// ===== 趋势 / 分布 / 最新列表 =====
const trendData = ref([])
const distribution = ref([])
const latestAlerts = ref([])

// ===== ECharts 实例 =====
const lineRef = ref(null)
const pieRef = ref(null)
const { setOption: setLineOption } = useEChart(lineRef)
const { setOption: setPieOption } = useEChart(pieRef)

// 加载统计
async function loadStats() {
  const [today, high, proc] = await Promise.all([
    getAlertList({ page: 1, size: 1 }),
    getAlertList({ alertLevel: 'RED', page: 1, size: 1 }),
    getAlertList({ status: 'OPEN', page: 1, size: 1 })
  ])
  stats.value = {
    today: today?.total || 0,
    highRisk: high?.total || 0,
    processing: proc?.total || 0,
    deviceOnlineRate: stats.value.deviceOnlineRate
  }
}

// 加载近 7 天趋势
async function loadTrend() {
  const res = await getAlertList({ page: 1, size: 100 })
  const records = res?.records || []
  const buckets = buildLast7Days()
  for (const r of records) {
    const ts = new Date(r.eventTimestamp).getTime()
    if (isNaN(ts)) continue
    for (const b of buckets) {
      if (ts >= b.start && ts < b.start + 86400000) { b.count++; break }
    }
  }
  trendData.value = buckets
}

function buildLast7Days() {
  const today = new Date()
  today.setHours(0, 0, 0, 0)
  const buckets = []
  for (let i = 6; i >= 0; i--) {
    const start = today.getTime() - i * 86400000
    const d = new Date(start)
    buckets.push({
      start,
      label: `${d.getMonth() + 1}/${d.getDate()}`,
      count: 0
    })
  }
  return buckets
}

// 加载等级分布
async function loadDistribution() {
  const [blue, yellow, orange, red] = await Promise.all([
    getAlertList({ alertLevel: 'BLUE', page: 1, size: 1 }),
    getAlertList({ alertLevel: 'YELLOW', page: 1, size: 1 }),
    getAlertList({ alertLevel: 'ORANGE', page: 1, size: 1 }),
    getAlertList({ alertLevel: 'RED', page: 1, size: 1 })
  ])
  distribution.value = [
    { name: '蓝色', value: blue?.total || 0, color: '#0071E3' },
    { name: '黄色', value: yellow?.total || 0, color: '#FFCC00' },
    { name: '橙色', value: orange?.total || 0, color: '#FF9500' },
    { name: '红色', value: red?.total || 0, color: '#FF3B30' }
  ]
}

// 加载最新 5 条预警
async function loadLatestAlerts() {
  loading.value = true
  try {
    const res = await getAlertList({ page: 1, size: 5 })
    latestAlerts.value = res?.records || []
  } finally {
    loading.value = false
  }
}

function goDetail(row) {
  router.push(`/alerts/${row.id}`)
}

onMounted(async () => {
  try {
    await Promise.all([loadStats(), loadTrend(), loadDistribution(), loadLatestAlerts()])
  } catch (e) {
    console.error('Dashboard 数据加载失败:', e)
  }
  renderLineChart()
  renderPieChart()
})

// 平滑曲线 + 面积渐变
function renderLineChart() {
  setLineOption({
    tooltip: { trigger: 'axis' },
    grid: { left: 36, right: 24, top: 24, bottom: 28 },
    xAxis: {
      type: 'category',
      boundaryGap: false,
      data: trendData.value.map(d => d.label),
      axisLine: { lineStyle: { color: 'rgba(0,0,0,0.06)' } },
      axisTick: { show: false },
      axisLabel: { color: '#86868B', fontSize: 12 }
    },
    yAxis: {
      type: 'value',
      splitLine: { lineStyle: { color: 'rgba(0,0,0,0.04)' } },
      axisLabel: { color: '#86868B', fontSize: 12 }
    },
    series: [{
      name: '预警数',
      type: 'line',
      smooth: true,
      symbol: 'circle',
      symbolSize: 8,
      data: trendData.value.map(d => d.count),
      itemStyle: { color: '#0071E3' },
      lineStyle: { width: 2.5, color: '#0071E3' },
      areaStyle: {
        color: {
          type: 'linear', x: 0, y: 0, x2: 0, y2: 1,
          colorStops: [
            { offset: 0, color: 'rgba(0,113,227,0.3)' },
            { offset: 1, color: 'rgba(0,113,227,0)' }
          ]
        }
      }
    }]
  })
}

// 环形图：中心显示总预警数
function renderPieChart() {
  const total = distribution.value.reduce((sum, d) => sum + d.value, 0)
  setPieOption({
    tooltip: { trigger: 'item', formatter: '{b}: {c} ({d}%)' },
    legend: { bottom: 0, icon: 'circle', textStyle: { color: '#6E6E73', fontSize: 12 } },
    series: [{
      type: 'pie',
      radius: ['62%', '78%'],
      avoidLabelOverlap: false,
      itemStyle: { borderColor: '#fff', borderWidth: 3 },
      label: { show: false },
      data: distribution.value.map(d => ({
        name: d.name,
        value: d.value,
        itemStyle: { color: d.color }
      }))
    }, {
      type: 'pie',
      radius: ['0%', '0%'],
      silent: true,
      label: {
        show: true,
        position: 'center',
        formatter: () => `{total|${total}}\n{label|总预警数}`,
        rich: {
          total: { fontSize: 28, fontWeight: 700, color: '#1D1D1F', lineHeight: 36, fontFamily: 'SF Pro Display, sans-serif' },
          label: { fontSize: 12, color: '#86868B', lineHeight: 18 }
        }
      },
      data: [{ value: 0 }]
    }]
  })
}
</script>

<style scoped>
.dashboard__row {
  display: grid;
  gap: 16px;
  margin-bottom: 16px;
}
.dashboard__row--stats {
  grid-template-columns: repeat(4, 1fr);
}
.dashboard__row--bottom {
  grid-template-columns: 1fr 1fr 1.5fr;
}

/* 图表卡片 */
.dashboard__chart-card,
.dashboard__latest {
  padding: 20px 24px;
}
.dashboard__chart-card {
  display: flex;
  flex-direction: column;
}
.dashboard__chart-canvas {
  width: 100%;
  height: 280px;
}
.dashboard__link {
  font-size: 13px;
  color: var(--app-primary);
  text-decoration: none;
  font-weight: 500;
}
.dashboard__link:hover {
  opacity: 0.75;
}
.dashboard__latest :deep(.clickable-row) {
  cursor: pointer;
}

/* GIS 地图卡片 */
.dashboard__map-card {
  padding: 20px 24px;
  margin-bottom: 16px;
}
.dashboard__map-card :deep(.gis-map) {
  height: 600px;
}

@media (max-width: 1200px) {
  .dashboard__row--bottom {
    grid-template-columns: 1fr 1fr;
  }
  .dashboard__row--bottom > :last-child {
    grid-column: 1 / -1;
  }
}

@media (max-width: 768px) {
  .dashboard__row--stats { grid-template-columns: repeat(2, 1fr); }
  .dashboard__row--bottom { grid-template-columns: 1fr; }
}
</style>
