<script setup lang="ts">
import type { Summary } from '../types'

defineProps<{ summary: Summary | null }>()
</script>

<template>
  <div class="stat-cards">
    <div class="stat-card">
      <div class="label">在册管道总数</div>
      <div class="value">{{ summary?.pipe_total ?? '-' }}</div>
      <div class="extra">异常 {{ summary?.pipe_abnormal ?? 0 }} 条 · 今日监测 {{ summary?.monitor_today ?? 0 }} 条</div>
    </div>
    <div class="stat-card">
      <div class="label">未处理告警</div>
      <div class="value danger">{{ summary?.active_alarms ?? '-' }}</div>
      <div class="extra">多维监测自动产生</div>
    </div>
    <div class="stat-card">
      <div class="label">平均漏损率</div>
      <div class="value warn">{{ summary?.avg_leakage_pct ?? '-' }}%</div>
      <div class="extra">DMA 异常分区 {{ summary?.dma_abnormal ?? 0 }} 个</div>
    </div>
    <div class="stat-card">
      <div class="label">水质异常节点</div>
      <div class="value warn">{{ summary?.quality_abnormal ?? '-' }}</div>
      <div class="extra">二供异常 {{ summary?.secondary_abnormal ?? 0 }} 处</div>
    </div>
    <div class="stat-card">
      <div class="label">消防栓台账</div>
      <div class="value">{{ summary?.hydrant_total ?? '-' }}</div>
      <div class="extra">异常 {{ summary?.hydrant_abnormal ?? 0 }} 处</div>
    </div>
    <div class="stat-card">
      <div class="label">爆管高风险</div>
      <div class="value danger">{{ summary?.burst_high ?? '-' }}</div>
      <div class="extra">在途处置 {{ summary?.burst_pending ?? 0 }} 起</div>
    </div>
  </div>
</template>
