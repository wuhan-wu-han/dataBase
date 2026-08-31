<template>
  <!-- 预警等级标签组件 -->
  <span class="alert-level-tag" :class="levelClass">
    {{ levelText }}
  </span>
</template>

<script setup>
import { computed } from 'vue'
import { getAlertLevelText } from '@/utils/format'

const props = defineProps({
  level: {
    type: String,
    required: true
  }
})

const levelText = computed(() => getAlertLevelText(props.level))

const levelClass = computed(() => {
  const map = {
    CRITICAL: 'level-critical',
    HIGH: 'level-high',
    MEDIUM: 'level-medium',
    LOW: 'level-low'
  }
  return map[props.level] || ''
})
</script>

<style scoped>
.alert-level-tag {
  display: inline-block;
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: bold;
}
.level-critical { background: #ff4d4f; color: #fff; }
.level-high     { background: #fa8c16; color: #fff; }
.level-medium   { background: #fadb14; color: #333; }
.level-low      { background: #52c41a; color: #fff; }
</style>
