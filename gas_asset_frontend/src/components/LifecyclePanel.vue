<script setup lang="ts">
import { nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import * as echarts from 'echarts'
import { fetchLifecycleRecords, fetchLifecycleStages } from '../api'
import { AXIS_STYLE, PALETTE } from '../utils/chart'
import { fmtCost, STAGE_TAG } from '../utils/format'
import type { LifecycleRecord } from '../types'

const records = ref<LifecycleRecord[]>([])
const stages = ref<string[]>([])
const elChart = ref<HTMLDivElement>()
let chart: echarts.ECharts | null = null

const onResize = () => chart?.resize()

async function load() {
  const [st, rc] = await Promise.all([
    fetchLifecycleStages(),
    fetchLifecycleRecords({ limit: 1000 })
  ])
  stages.value = st.stages
  records.value = rc.records
}

function renderChart() {
  if (!elChart.value) return
  if (!chart) chart = echarts.init(elChart.value)
  const counts = stages.value.map(
    (s) => records.value.filter((r) => r.stage === s).length
  )
  chart.setOption({
    color: PALETTE,
    grid: { left: 8, right: 14, top: 24, bottom: 4, containLabel: true },
    tooltip: { trigger: 'axis' },
    xAxis: { type: 'category', data: stages.value, ...AXIS_STYLE, axisTick: { show: false } },
    yAxis: { type: 'value', ...AXIS_STYLE, name: '记录数' },
    series: [{
      type: 'bar',
      data: counts,
      barMaxWidth: 26,
      itemStyle: { borderRadius: [4, 4, 0, 0] },
      label: { show: true, position: 'top', color: '#5a6b84', fontSize: 11 }
    }]
  }, true)
}

onMounted(async () => {
  await load()
  await nextTick()
  renderChart()
  window.addEventListener('resize', onResize)
})

watch(records, async () => {
  await nextTick()
  renderChart()
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', onResize)
  chart?.dispose()
  chart = null
})
</script>

<template>
  <div class="panel">
    <div class="panel-title">全生命周期档案</div>
    <div ref="elChart" class="panel-chart-box"></div>
    <el-table :data="records.slice(0, 6)" size="small" height="186" class="mt8">
      <el-table-column prop="occurred_at" label="时间" width="92" />
      <el-table-column prop="asset_code" label="资产编号" min-width="128" show-overflow-tooltip />
      <el-table-column label="阶段" width="70" align="center">
        <template #default="{ row }">
          <el-tag size="small" :type="STAGE_TAG[row.stage] || 'info'">{{ row.stage }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="费用" width="92" align="right">
        <template #default="{ row }">{{ fmtCost(row.cost) }}</template>
      </el-table-column>
    </el-table>
    <div class="muted mt8" style="font-size: 12px;">
      近 6 条阶段记录 · 共 {{ records.length }} 条 ｜ 在资产明细中可查看完整时间线并新增/编辑记录
    </div>
  </div>
</template>
