<script setup lang="ts">
import { onMounted, ref } from 'vue'
import StatCards from './components/StatCards.vue'
import MonitorPanel from './components/MonitorPanel.vue'
import DmaPanel from './components/DmaPanel.vue'
import QualityPanel from './components/QualityPanel.vue'
import PressurePanel from './components/PressurePanel.vue'
import SecondaryPanel from './components/SecondaryPanel.vue'
import HydrantPanel from './components/HydrantPanel.vue'
import BurstPanel from './components/BurstPanel.vue'
import { getSummary } from './api'
import type { Summary } from './types'

const summary = ref<Summary | null>(null)
const activeTab = ref('monitor')

async function loadSummary() {
  try {
    summary.value = await getSummary()
  } catch (e) {
    console.error('汇总加载失败', e)
  }
}

onMounted(loadSummary)
</script>

<template>
  <div>
    <header class="app-header">
      <h1>供水管网精细化管控大屏</h1>
      <span class="sub">城市生命线管网 AI 智慧平台 · 实时监测 / DMA漏损 / 水质溯源 / 压力调度 / 二次供水 / 消防栓 / 爆管分析</span>
      <span class="right">数据源：water_supply.db</span>
    </header>

    <div class="page-body">
      <StatCards :summary="summary" />

      <el-tabs v-model="activeTab">
        <el-tab-pane label="实时运行监测" name="monitor" lazy>
          <MonitorPanel @changed="loadSummary" />
        </el-tab-pane>
        <el-tab-pane label="DMA分区漏损" name="dma" lazy>
          <DmaPanel @changed="loadSummary" />
        </el-tab-pane>
        <el-tab-pane label="水质全流程溯源" name="quality" lazy>
          <QualityPanel @changed="loadSummary" />
        </el-tab-pane>
        <el-tab-pane label="智能压力调度" name="pressure" lazy>
          <PressurePanel @changed="loadSummary" />
        </el-tab-pane>
        <el-tab-pane label="二次供水管控" name="secondary" lazy>
          <SecondaryPanel @changed="loadSummary" />
        </el-tab-pane>
        <el-tab-pane label="消防栓专项管理" name="hydrant" lazy>
          <HydrantPanel @changed="loadSummary" />
        </el-tab-pane>
        <el-tab-pane label="爆管影响分析" name="burst" lazy>
          <BurstPanel @changed="loadSummary" />
        </el-tab-pane>
      </el-tabs>
    </div>
  </div>
</template>