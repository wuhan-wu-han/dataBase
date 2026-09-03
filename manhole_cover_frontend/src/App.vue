<script setup lang="ts">
import { onMounted, ref } from 'vue'
import StatCards from './components/StatCards.vue'
import MonitorPanel from './components/MonitorPanel.vue'
import ArchivePanel from './components/ArchivePanel.vue'
import OrderPanel from './components/OrderPanel.vue'
import TheftPanel from './components/TheftPanel.vue'
import NetPanel from './components/NetPanel.vue'
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
      <h1>市政井盖全生命周期管控大屏</h1>
      <span class="sub">天信城市生命线管网 AI 智慧平台 · 实时监测 / 一井一档 / 隐患闭环 / 被盗追踪 / 防坠网</span>
      <span class="right">数据源：manhole_cover.db</span>
    </header>

    <div class="page-body">
      <StatCards :summary="summary" />

      <el-tabs v-model="activeTab">
        <el-tab-pane label="状态实时监测" name="monitor">
          <MonitorPanel :active="activeTab === 'monitor'" @changed="loadSummary" />
        </el-tab-pane>
        <el-tab-pane label="一井一档数字档案" name="archive">
          <ArchivePanel :active="activeTab === 'archive'" @changed="loadSummary" />
        </el-tab-pane>
        <el-tab-pane label="隐患闭环处置" name="order">
          <OrderPanel :active="activeTab === 'order'" @changed="loadSummary" />
        </el-tab-pane>
        <el-tab-pane label="被盗追踪管理" name="theft">
          <TheftPanel :active="activeTab === 'theft'" @changed="loadSummary" />
        </el-tab-pane>
        <el-tab-pane label="防坠网台账" name="net">
          <NetPanel :active="activeTab === 'net'" @changed="loadSummary" />
        </el-tab-pane>
      </el-tabs>
    </div>
  </div>
</template>
