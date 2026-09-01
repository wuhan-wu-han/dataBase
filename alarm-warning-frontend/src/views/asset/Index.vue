<template>
  <div class="asset-view">
    <PageHeader title="资产管理" subtitle="Gas Asset Management" />

    <!-- 数据卡片：苹果风 4 张 -->
    <div class="asset-view__stats">
      <StatCard label="资产总数" :value="summary?.total_assets ?? 0" icon="OfficeBuilding" color="#0071E3" />
      <StatCard label="管网总长度" :value="totalLengthKm" icon="DataLine" color="#34C759" />
      <StatCard label="在役资产" :value="summary?.in_service ?? 0" icon="CircleCheck" color="#5856D6" />
      <StatCard label="盘点完成率" :value="inventoryRate" icon="TrendCharts" color="#FF9500" />
    </div>

    <!-- 资产分类图表 -->
    <div class="asset-view__row">
      <section class="app-card asset-view__panel">
        <header class="card-title">
          <h3 class="card-title__text">按口径分布</h3>
        </header>
        <div ref="byDiameterRef" class="asset-view__chart"></div>
      </section>
      <section class="app-card asset-view__panel">
        <header class="card-title">
          <h3 class="card-title__text">按材质分布</h3>
        </header>
        <div ref="byMaterialRef" class="asset-view__chart"></div>
      </section>
    </div>

    <!-- 资产列表 -->
    <section class="app-card">
      <header class="card-title">
        <h3 class="card-title__text">资产台账</h3>
        <el-button size="small" @click="loadData">刷新</el-button>
      </header>
      <el-table
        :data="assets"
        v-loading="loading"
        class="app-table"
        empty-text="暂无资产数据"
      >
        <el-table-column prop="asset_code" label="资产编号" min-width="160" />
        <el-table-column prop="segment_name" label="管段名称" min-width="180" show-overflow-tooltip />
        <el-table-column prop="diameter" label="口径" width="100" />
        <el-table-column prop="material" label="材质" width="100" />
        <el-table-column prop="region" label="区域" width="120" />
        <el-table-column prop="length_m" label="长度(m)" width="100" align="right" />
        <el-table-column prop="status" label="状态" width="100" align="center">
          <template #default="{ row }">
            <el-tag :type="row.status === '在役' ? 'success' : 'info'" size="small">
              {{ row.status }}
            </el-tag>
          </template>
        </el-table-column>
      </el-table>
    </section>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import PageHeader from '@/components/PageHeader.vue'
import StatCard from '@/components/StatCard.vue'
import { useEChart } from '@/utils/chart'
import { fetchSummary, fetchStats, fetchAssets } from '@/api/gasAsset'

const summary = ref(null)
const stats = ref(null)
const assets = ref([])
const loading = ref(false)

// 计算属性
const totalLengthKm = computed(() => {
  const v = summary.value?.total_length_km ?? 0
  return typeof v === 'number' ? v.toFixed(2) : '0.00'
})
const inventoryRate = computed(() => {
  const v = summary.value?.inventory_completion_rate ?? 0
  return `${Number(v).toFixed(1)}%`
})

// ECharts
const byDiameterRef = ref(null)
const byMaterialRef = ref(null)
const { setOption: setDiameterOption } = useEChart(byDiameterRef)
const { setOption: setMaterialOption } = useEChart(byMaterialRef)

async function loadData() {
  loading.value = true
  try {
    const [s, g, list] = await Promise.all([
      fetchSummary(),
      fetchStats(),
      fetchAssets({ page: 1, page_size: 20 })
    ])
    summary.value = s
    stats.value = g
    assets.value = list.items || []
    renderCharts()
  } catch (e) {
    ElMessage.error('无法连接资产管理服务：' + e.message)
  } finally {
    loading.value = false
  }
}

function renderCharts() {
  if (!stats.value) return
  // 按口径分布
  setDiameterOption(buildBarOption(stats.value.by_diameter, '#0071E3'))
  setMaterialOption(buildBarOption(stats.value.by_material, '#5856D6'))
}

function buildBarOption(stat, color) {
  const items = stat || []
  return {
    tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
    grid: { left: 80, right: 30, top: 20, bottom: 20 },
    xAxis: { type: 'value', axisLine: { show: false }, axisTick: { show: false }, axisLabel: { color: '#86868B' }, splitLine: { lineStyle: { color: 'rgba(0,0,0,0.04)' } } },
    yAxis: {
      type: 'category',
      data: items.map(i => i.name),
      axisLine: { show: false }, axisTick: { show: false },
      axisLabel: { color: '#424245', fontSize: 12 }
    },
    series: [{
      type: 'bar',
      data: items.map(i => ({
        value: i.value,
        itemStyle: {
          color: { type: 'linear', x: 0, y: 0, x2: 1, y2: 0, colorStops: [{ offset: 0, color: color + '66' }, { offset: 1, color }] },
          borderRadius: [0, 6, 6, 0]
        }
      })),
      barWidth: 18
    }]
  }
}

onMounted(loadData)
</script>

<style scoped>
.asset-view__stats {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
  margin-bottom: 16px;
}
.asset-view__row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
  margin-bottom: 16px;
}
.asset-view__panel {
  padding: 20px 24px;
}
.asset-view__chart {
  width: 100%;
  height: 280px;
}
@media (max-width: 1024px) {
  .asset-view__stats { grid-template-columns: repeat(2, 1fr); }
  .asset-view__row { grid-template-columns: 1fr; }
}
</style>
