<script setup lang="ts">
import { onMounted, onBeforeUnmount, ref } from 'vue'
import { fetchStats, fetchSummary } from './api'
import type { AssetStats, Summary } from './types'
import StatCards from './components/StatCards.vue'
import DimensionCharts from './components/DimensionCharts.vue'
import LifecyclePanel from './components/LifecyclePanel.vue'
import InventoryPanel from './components/InventoryPanel.vue'
import OwnershipPanel from './components/OwnershipPanel.vue'
import AssetTable from './components/AssetTable.vue'

const summary = ref<Summary | null>(null)
const stats = ref<AssetStats | null>(null)
const now = ref('')
let timer: number | undefined

function tick() {
  const d = new Date()
  const p = (n: number) => String(n).padStart(2, '0')
  now.value = `${d.getFullYear()}-${p(d.getMonth() + 1)}-${p(d.getDate())} ${p(d.getHours())}:${p(d.getMinutes())}:${p(d.getSeconds())}`
}

async function loadHeader() {
  const [s, g] = await Promise.all([fetchSummary(), fetchStats()])
  summary.value = s
  stats.value = g
}

/** 子面板发生数据变更（盘点处理、权属补录等）后刷新顶部指标 */
function onChanged() {
  loadHeader()
}

onMounted(() => {
  tick()
  timer = window.setInterval(tick, 1000)
  loadHeader()
})

onBeforeUnmount(() => {
  if (timer) window.clearInterval(timer)
})
</script>

<template>
  <div class="screen">
    <header class="screen-header">
      <span class="sub-title">天信城市生命线管网 AI 智慧平台</span>
      <h1>资产数字化台账大屏</h1>
      <span class="clock">
        <span>{{ now }}</span>
        <el-button size="small" round @click="loadHeader">刷新数据</el-button>
      </span>
    </header>

    <StatCards :summary="summary" />
    <DimensionCharts v-if="stats" :stats="stats" />

    <div class="grid-panels">
      <LifecyclePanel />
      <InventoryPanel @changed="onChanged" />
      <OwnershipPanel @changed="onChanged" />
    </div>

    <AssetTable @changed="onChanged" />
  </div>
</template>
