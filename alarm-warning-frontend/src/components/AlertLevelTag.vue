<template>
  <!-- 预警等级标签组件（对应后端 AlertLevel 枚举） -->
  <el-tag :type="tagType" effect="light" size="small">
    {{ levelText }}
  </el-tag>
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

// 等级文本
const levelText = computed(() => getAlertLevelText(props.level))

// Element Plus Tag 类型映射
const tagType = computed(() => {
  const map = {
    BLUE: 'info',
    YELLOW: 'warning',
    ORANGE: 'warning',
    RED: 'danger'
  }
  return map[props.level] || 'info'
})
</script>
