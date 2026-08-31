<template>
  <!-- 统计卡片组件 -->
  <div class="stat-card">
    <div class="stat-icon" :style="{ backgroundColor: iconBg }">
      <el-icon :size="28"><component :is="icon" /></el-icon>
    </div>
    <div class="stat-info">
      <div class="stat-value">{{ value }}</div>
      <div class="stat-label">{{ label }}</div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  label: { type: String, required: true },
  value: { type: [Number, String], default: 0 },
  icon: { type: String, default: 'DataLine' },
  color: { type: String, default: '#1890ff' }
})

const iconBg = computed(() => props.color + '22')
</script>

<style scoped>
.stat-card {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 20px;
  background: #1b2838;
  border-radius: 8px;
  border: 1px solid #2a3a4a;
}
.stat-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 56px;
  height: 56px;
  border-radius: 12px;
}
.stat-value {
  font-size: 28px;
  font-weight: bold;
  color: #e0e6ed;
}
.stat-label {
  font-size: 14px;
  color: #8a9bb0;
  margin-top: 4px;
}
</style>
