<script setup lang="ts">
import { onMounted, ref } from 'vue'
import StatCards from './components/StatCards.vue'
import CavityPanel from './components/CavityPanel.vue'
import SubsidencePanel from './components/SubsidencePanel.vue'
import ConstructionPanel from './components/ConstructionPanel.vue'
import { getSummary } from './api'
import type { Summary } from './types'

const summary = ref<Summary | null>(null)
const activeTab = ref('cavity')

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
      <h1>道路地下隐患防控大屏</h1>
      <span class="sub">天信城市生命线管网 AI 智慧平台 · 地下空洞 / 道路沉降 / 施工影响</span>
    </header>

    <div class="page-body">
      <StatCards :summary="summary" />

      <el-tabs v-model="activeTab">
        <el-tab-pane label="地下空洞风险评估" name="cavity">
          <CavityPanel @changed="loadSummary" />
        </el-tab-pane>
        <el-tab-pane label="道路沉降监测" name="subsidence">
          <SubsidencePanel @changed="loadSummary" />
        </el-tab-pane>
        <el-tab-pane label="施工影响评估" name="construction">
          <ConstructionPanel @changed="loadSummary" />
        </el-tab-pane>
      </el-tabs>
    </div>
  </div>
</template>
