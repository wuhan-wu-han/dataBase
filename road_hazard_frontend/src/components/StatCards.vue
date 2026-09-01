<script setup lang="ts">
import type { Summary } from '../types'

defineProps<{ summary: Summary | null }>()
</script>

<template>
  <div class="stat-cards">
    <div class="stat-card">
      <div class="label">地下空洞总数</div>
      <div class="value">{{ summary?.cavity_total ?? '-' }}</div>
      <div class="extra">未处置 {{ summary?.cavity_unhandled ?? '-' }} 处</div>
    </div>
    <div class="stat-card">
      <div class="label">高风险空洞</div>
      <div class="value danger">{{ summary?.cavity_high ?? '-' }}</div>
      <div class="extra">需优先注浆处置</div>
    </div>
    <div class="stat-card">
      <div class="label">沉降监测点</div>
      <div class="value">{{ summary?.subsidence_points ?? '-' }}</div>
      <div class="extra">累计观测 {{ summary?.subsidence_records ?? '-' }} 期</div>
    </div>
    <div class="stat-card">
      <div class="label">沉降危险点位</div>
      <div class="value danger">{{ summary?.subsidence_high ?? '-' }}</div>
      <div class="extra">塌陷风险，加密监测</div>
    </div>
    <div class="stat-card">
      <div class="label">施工评估项目</div>
      <div class="value">{{ summary?.construction_total ?? '-' }}</div>
      <div class="extra">覆盖 5 类工法</div>
    </div>
    <div class="stat-card">
      <div class="label">高风险施工项目</div>
      <div class="value danger">{{ summary?.construction_high ?? '-' }}</div>
      <div class="extra">需专项保护方案</div>
    </div>
  </div>
</template>
