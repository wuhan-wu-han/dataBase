<template>
  <!-- 预警状态标签组件（对应后端 AlertStatus 枚举） -->
  <el-tag :type="tagType" effect="light" size="small">
    {{ statusText }}
  </el-tag>
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

// 状态文本
const statusText = computed(() => getAlertStatusText(props.status))

// Element Plus Tag 类型映射
const tagType = computed(() => {
  const map = {
    OPEN: 'danger',
    ACKNOWLEDGED: 'warning',
    RESOLVED: 'success',
    CLOSED: 'info'
  }
  return map[props.status] || 'info'
})
</script>
