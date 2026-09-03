<script setup lang="ts">
import type { Summary } from '../types'

defineProps<{ summary: Summary | null }>()
</script>

<template>
  <div class="stat-cards">
    <div class="stat-card">
      <div class="label">在册井盖总数</div>
      <div class="value">{{ summary?.manhole_total ?? '-' }}</div>
      <div class="extra">一井一档电子台账</div>
    </div>
    <div class="stat-card">
      <div class="label">异常状态井盖</div>
      <div class="value danger">{{ summary?.manhole_abnormal ?? '-' }}</div>
      <div class="extra">告警 / 处置中 / 被盗 / 维修中</div>
    </div>
    <div class="stat-card">
      <div class="label">未闭环告警</div>
      <div class="value warn">{{ summary?.active_alarms ?? '-' }}</div>
      <div class="extra">多维监测自动产生</div>
    </div>
    <div class="stat-card">
      <div class="label">在途处置工单</div>
      <div class="value">{{ summary?.orders_pending ?? '-' }}</div>
      <div class="extra">闭环率 {{ summary?.close_rate_pct ?? '-' }}%</div>
    </div>
    <div class="stat-card">
      <div class="label">被盗追踪案件</div>
      <div class="value danger">{{ summary?.theft_cases ?? '-' }}</div>
      <div class="extra">公安联动 {{ summary?.police_records ?? '-' }} 条</div>
    </div>
    <div class="stat-card">
      <div class="label">防坠网台账</div>
      <div class="value">{{ summary?.net_total ?? '-' }}</div>
      <div class="extra">破损待修 {{ summary?.net_broken ?? '-' }} 张</div>
    </div>
  </div>
</template>
