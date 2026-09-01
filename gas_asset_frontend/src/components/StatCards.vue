<script setup lang="ts">
import type { Summary } from '../types'

defineProps<{ summary: Summary | null }>()

const CARDS = [
  { key: 'total_assets', label: '资产总数', unit: '项', color: '#3d7eff', icon: '总' },
  { key: 'total_length_km', label: '管网总长度', unit: 'km', color: '#269a99', icon: '长' },
  { key: 'in_service', label: '在役资产', unit: '项', color: '#52b788', icon: '役' },
  { key: 'pending_disposal', label: '待报废资产', unit: '项', color: '#e86452', icon: '废' },
  { key: 'inventory_completion_rate', label: '盘点完成率', unit: '%', color: '#f6a609', icon: '盘' },
  { key: 'ownership_clear_rate', label: '权属清晰率', unit: '%', color: '#945fb9', icon: '权' }
] as const

function valueOf(s: Summary | null, key: string): string {
  if (!s) return '--'
  return String((s as any)[key])
}
</script>

<template>
  <div class="stat-row">
    <div v-for="c in CARDS" :key="c.key" class="stat-card">
      <div class="stat-icon" :style="{ background: `linear-gradient(135deg, ${c.color}, ${c.color}cc)` }">
        {{ c.icon }}
      </div>
      <div class="stat-info">
        <div class="stat-label">{{ c.label }}</div>
        <div class="stat-value">
          {{ valueOf(summary, c.key) }}<span class="unit">{{ c.unit }}</span>
        </div>
        <div v-if="summary && c.key === 'total_assets'" class="stat-extra">
          停用 {{ summary.suspended }} 项 · 任务完成 {{ summary.task_finished }}/{{ summary.task_count }}
        </div>
        <div v-else-if="summary && c.key === 'ownership_clear_rate'" class="stat-extra">
          权属清晰 {{ summary.ownership_clear }} 项
        </div>
      </div>
    </div>
  </div>
</template>
