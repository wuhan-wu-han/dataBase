<template>
  <!-- 预警状态标签组件 -->
  <span class="alert-status-tag" :class="statusClass">
    {{ statusText }}
  </span>
</template>

<script setup>
import { computed } from 'vue'
import { getAlertStatusText } from '@/utils/format'

const props = defineProps({
  status: {
    type: String,
    required: true
  }
})

const statusText = computed(() => getAlertStatusText(props.status))

const statusClass = computed(() => {
  const map = {
    TRIGGERED: 'status-triggered',
    ACKNOWLEDGED: 'status-acknowledged',
    PROCESSING: 'status-processing',
    RESOLVED: 'status-resolved',
    CLOSED: 'status-closed'
  }
  return map[props.status] || ''
})
</script>

<style scoped>
.alert-status-tag {
  display: inline-block;
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 12px;
}
.status-triggered    { background: #ff4d4f; color: #fff; }
.status-acknowledged { background: #fa8c16; color: #fff; }
.status-processing   { background: #1890ff; color: #fff; }
.status-resolved     { background: #52c41a; color: #fff; }
.status-closed       { background: #8c8c8c; color: #fff; }
</style>
