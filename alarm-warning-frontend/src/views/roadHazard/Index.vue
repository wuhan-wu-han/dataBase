<template>
  <div class="road-hazard">
    <PageHeader title="道路塌陷" subtitle="Road Hazard Control" />

    <!-- 数据卡片 -->
    <div class="road-hazard__stats">
      <StatCard label="空洞隐患" :value="summary?.cavity_count ?? 0" icon="Warning" color="#FF3B30" />
      <StatCard label="沉降监测点" :value="summary?.subsidence_point_count ?? 0" icon="MapLocation" color="#0071E3" />
      <StatCard label="施工影响" :value="summary?.construction_count ?? 0" icon="Setup" color="#FF9500" />
      <StatCard label="高风险点" :value="summary?.high_risk_count ?? 0" icon="WarningFilled" color="#FF3B30" />
    </div>

    <!-- 风险分布图 -->
    <div class="road-hazard__row">
      <section class="app-card road-hazard__panel">
        <header class="card-title">
          <h3 class="card-title__text">空洞风险等级分布</h3>
        </header>
        <div ref="cavityPieRef" class="road-hazard__chart"></div>
      </section>
      <section class="app-card road-hazard__panel">
        <header class="card-title">
          <h3 class="card-title__text">沉降监测点分布</h3>
        </header>
        <div ref="subsBarRef" class="road-hazard__chart"></div>
      </section>
    </div>

    <!-- 空洞隐患列表 -->
    <section class="app-card">
      <header class="card-title">
        <h3 class="card-title__text">空洞隐患台账</h3>
        <el-button size="small" @click="loadData">刷新</el-button>
      </header>
      <el-table
        :data="cavities"
        v-loading="loading"
        class="app-table"
        empty-text="暂无数据"
      >
        <el-table-column prop="code" label="编号" width="140" />
        <el-table-column prop="road" label="道路" min-width="160" show-overflow-tooltip />
        <el-table-column prop="district" label="区域" width="120" />
        <el-table-column prop="depth_m" label="深度(m)" width="100" align="right" />
        <el-table-column prop="volume_m3" label="体积(m³)" width="110" align="right" />
        <el-table-column label="风险等级" width="110" align="center">
          <template #default="{ row }">
            <el-tag :type="riskTag(row.risk_level)" size="small">{{ row.risk_level }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="100" align="center">
          <template #default="{ row }">
            <el-tag :type="row.status === '已处置' ? 'success' : 'warning'" size="small">
              {{ row.status }}
            </el-tag>
          </template>
        </el-table-column>
      </el-table>
    </section>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import PageHeader from '@/components/PageHeader.vue'
import StatCard from '@/components/StatCard.vue'
import { useEChart } from '@/utils/chart'
import { getSummary, getCavities, getCavityStats } from '@/api/roadHazard'

const summary = ref(null)
const cavities = ref([])
const loading = ref(false)

// ECharts
const cavityPieRef = ref(null)
const subsBarRef = ref(null)
const { setOption: setCavityPieOption } = useEChart(cavityPieRef)
const { setOption: setSubsBarOption } = useEChart(subsBarRef)

// 风险等级标签类型
function riskTag(level) {
  const map = { '高': 'danger', '中': 'warning', '低': 'success' }
  return map[level] || 'info'
}

async function loadData() {
  loading.value = true
  try {
    const [s, list, stats] = await Promise.all([
      getSummary(),
      getCavities({ page: 1, page_size: 20 }),
      getCavityStats()
    ])
    summary.value = s
    cavities.value = list.items || []
    renderCavityPie(stats.by_risk || [])
    renderSubsBar()
  } catch (e) {
    ElMessage.error('无法连接道路塌陷服务：' + e.message)
  } finally {
    loading.value = false
  }
}

// 空洞风险等级环形图
function renderCavityPie(byRisk) {
  const colorMap = { '高': '#FF3B30', '中': '#FF9500', '低': '#34C759' }
  const total = byRisk.reduce((sum, i) => sum + i.value, 0)
  setCavityPieOption({
    tooltip: { trigger: 'item', formatter: '{b}: {c} ({d}%)' },
    legend: { bottom: 0, icon: 'circle', textStyle: { color: '#6E6E73' } },
    series: [{
      type: 'pie',
      radius: ['62%', '78%'],
      itemStyle: { borderColor: '#fff', borderWidth: 3 },
      label: { show: false },
      data: byRisk.map(i => ({ name: i.name, value: i.value, itemStyle: { color: colorMap[i.name] || '#0071E3' } }))
    }, {
      type: 'pie', radius: ['0%', '0%'], silent: true,
      label: {
        show: true, position: 'center',
        formatter: () => `{total|${total}}\n{label|空洞总数}`,
        rich: {
          total: { fontSize: 28, fontWeight: 700, color: '#1D1D1F', lineHeight: 36 },
          label: { fontSize: 12, color: '#86868B', lineHeight: 18 }
        }
      },
      data: [{ value: 0 }]
    }]
  })
}

// 沉降分布柱状图（占位，无数据时显示空轴）
function renderSubsBar() {
  setSubsBarOption({
    tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
    grid: { left: 60, right: 30, top: 20, bottom: 20 },
    xAxis: { type: 'category', data: [], axisLine: { lineStyle: { color: 'rgba(0,0,0,0.06)' } }, axisLabel: { color: '#86868B' } },
    yAxis: { type: 'value', splitLine: { lineStyle: { color: 'rgba(0,0,0,0.04)' } }, axisLabel: { color: '#86868B' } },
    series: [{ type: 'bar', data: [], itemStyle: { color: '#0071E3', borderRadius: [4, 4, 0, 0] } }]
  })
}

onMounted(loadData)
</script>

<style scoped>
.road-hazard__stats {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
  margin-bottom: 16px;
}
.road-hazard__row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
  margin-bottom: 16px;
}
.road-hazard__panel {
  padding: 20px 24px;
}
.road-hazard__chart {
  width: 100%;
  height: 280px;
}
@media (max-width: 1024px) {
  .road-hazard__stats { grid-template-columns: repeat(2, 1fr); }
  .road-hazard__row { grid-template-columns: 1fr; }
}
</style>
