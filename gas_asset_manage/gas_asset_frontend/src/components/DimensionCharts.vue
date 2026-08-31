<script setup lang="ts">
import { nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import * as echarts from 'echarts'
import { AXIS_STYLE, PALETTE } from '../utils/chart'
import type { AssetStats, GroupStat } from '../types'

const props = defineProps<{ stats: AssetStats }>()

const elDiameter = ref<HTMLDivElement>()
const elMaterial = ref<HTMLDivElement>()
const elDecade = ref<HTMLDivElement>()
const elOwner = ref<HTMLDivElement>()
const elRegion = ref<HTMLDivElement>()

let charts: echarts.ECharts[] = []

const onResize = () => charts.forEach((c) => c.resize())

function tooltip() {
  return {
    trigger: 'item',
    formatter: (p: any) => {
      const g: GroupStat | undefined = p.data?._raw
      const len = g ? `<br/>长度：${g.length_km} km` : ''
      return `${p.name}：${p.value} 项${len}`
    }
  }
}

function markData(groups: GroupStat[]) {
  return groups.map((g) => ({ name: g.name, value: g.value, _raw: g }))
}

function barOption(groups: GroupStat[], color: string, horizontal = false): echarts.EChartsOption {
  const data = markData(groups)
  const cat = { type: 'category' as const, data: data.map((d) => d.name), ...AXIS_STYLE, axisTick: { show: false } }
  const val = { type: 'value' as const, ...AXIS_STYLE, name: '项' }
  return {
    color: [color],
    grid: { left: 8, right: 14, top: 24, bottom: 4, containLabel: true },
    tooltip: tooltip(),
    xAxis: horizontal ? val : cat,
    yAxis: horizontal ? cat : val,
    series: [{
      type: 'bar',
      data,
      barMaxWidth: 22,
      itemStyle: { borderRadius: horizontal ? [0, 4, 4, 0] : [4, 4, 0, 0] },
      label: { show: true, position: horizontal ? 'right' : 'top', color: '#5a6b84', fontSize: 11 }
    }]
  }
}

function pieOption(groups: GroupStat[]): echarts.EChartsOption {
  return {
    color: PALETTE,
    tooltip: tooltip(),
    legend: { bottom: 0, textStyle: { color: '#5a6b84', fontSize: 11 }, itemWidth: 10, itemHeight: 10 },
    series: [{
      type: 'pie',
      radius: ['38%', '62%'],
      center: ['50%', '44%'],
      data: markData(groups),
      itemStyle: { borderRadius: 4, borderColor: '#fff', borderWidth: 2 },
      label: { color: '#5a6b84', fontSize: 11, formatter: '{b}\n{c} 项' }
    }]
  }
}

function sortByNum(groups: GroupStat[]): GroupStat[] {
  return [...groups].sort((a, b) => parseInt(a.name.replace(/\D/g, '')) - parseInt(b.name.replace(/\D/g, '')))
}

function renderAll() {
  const s = props.stats
  const pairs: [HTMLElement | undefined, echarts.EChartsOption][] = [
    [elDiameter.value, barOption(sortByNum(s.by_diameter), '#5b8ff9')],
    [elMaterial.value, pieOption(s.by_material)],
    [elDecade.value, barOption([...s.by_decade].sort((a, b) => a.name.localeCompare(b.name)), '#5ad8a6')],
    [elOwner.value, barOption(s.by_owner, '#f6bd16', true)],
    [elRegion.value, barOption(s.by_region, '#6dc8ec')]
  ]
  charts.forEach((c) => c.dispose())
  charts = []
  pairs.forEach(([el, option]) => {
    if (!el) return
    const c = echarts.init(el)
    c.setOption(option)
    charts.push(c)
  })
}

onMounted(async () => {
  await nextTick()
  renderAll()
  window.addEventListener('resize', onResize)
})

watch(() => props.stats, async () => {
  await nextTick()
  renderAll()
}, { deep: true })

onBeforeUnmount(() => {
  window.removeEventListener('resize', onResize)
  charts.forEach((c) => c.dispose())
  charts = []
})
</script>

<template>
  <div class="grid-charts">
    <div class="panel">
      <div class="panel-title">管径分布</div>
      <div ref="elDiameter" class="chart-box"></div>
    </div>
    <div class="panel">
      <div class="panel-title">材质分布</div>
      <div ref="elMaterial" class="chart-box"></div>
    </div>
    <div class="panel">
      <div class="panel-title">建设年代分布</div>
      <div ref="elDecade" class="chart-box"></div>
    </div>
    <div class="panel">
      <div class="panel-title">权属单位分布</div>
      <div ref="elOwner" class="chart-box"></div>
    </div>
    <div class="panel">
      <div class="panel-title">所属区域分布</div>
      <div ref="elRegion" class="chart-box"></div>
    </div>
  </div>
</template>
