<template>
  <!-- Apple 官网数据卡风格：玻璃背景 + 大字体数值 + 悬停上浮 -->
  <div class="stat-card">
    <div class="stat-card__icon" :style="iconStyle">
      <el-icon :size="24"><component :is="icon" /></el-icon>
    </div>
    <div class="stat-card__body">
      <div class="stat-card__value">{{ displayValue }}</div>
      <div class="stat-card__label">{{ label }}</div>
    </div>
  </div>
</template>

<script setup>
import { computed, ref, watch, onMounted } from 'vue'

const props = defineProps({
  label: { type: String, required: true },
  value: { type: [Number, String], default: 0 },
  icon: { type: String, default: 'DataLine' },
  color: { type: String, default: '#0071E3' }
})

// 数字动画值（仅数值类型参与动画）
const animatedValue = ref(0)

// 是否为纯数值（用于决定是否启用数字滚动动画）
// 注意：百分比字符串（如 "98.6%"）也按数值处理，动画期间只滚动数字部分
const isNumeric = computed(() => {
  if (typeof props.value === 'number') return true
  if (typeof props.value === 'string') {
    const cleaned = props.value.replace(/[^\d.]/g, '')
    return cleaned !== '' && !isNaN(Number(cleaned))
  }
  return false
})

// 提取数值部分
const numericValue = computed(() => {
  if (typeof props.value === 'number') return props.value
  if (typeof props.value === 'string') {
    const cleaned = props.value.replace(/[^\d.]/g, '')
    return Number(cleaned) || 0
  }
  return 0
})

// 提取非数字前后缀（如 %、月）
const suffix = computed(() => {
  if (typeof props.value !== 'string') return ''
  const match = props.value.match(/[^\d.]+$/)
  return match ? match[0] : ''
})

// 展示值：非数值原样返回，数值显示动画过渡后的整数 + 后缀
const displayValue = computed(() => {
  if (!isNumeric.value) return props.value
  return formatNumber(animatedValue.value) + suffix.value
})

onMounted(() => {
  if (isNumeric.value) animateNumber(numericValue.value)
})

watch(() => props.value, () => {
  if (isNumeric.value) animateNumber(numericValue.value)
})

// 数字滚动动画（cubic ease-out）
function animateNumber(target) {
  const start = animatedValue.value
  const diff = target - start
  const duration = 800
  const startTime = performance.now()
  const step = (currentTime) => {
    const elapsed = currentTime - startTime
    const progress = Math.min(elapsed / duration, 1)
    const eased = 1 - Math.pow(1 - progress, 3)
    animatedValue.value = start + diff * eased
    if (progress < 1) requestAnimationFrame(step)
  }
  requestAnimationFrame(step)
}

// 数值格式化：千分位
function formatNumber(n) {
  return Math.round(n).toLocaleString('en-US')
}

// 图标方块样式：Apple 系统色浅色背景
const iconStyle = computed(() => ({
  backgroundColor: hexToRgba(props.color, 0.12),
  color: props.color
}))

// 将 #RRGGBB 转为 rgba(r,g,b,a)；输入异常时回退到 Apple 蓝
function hexToRgba(hex, alpha) {
  const fallback = `rgba(0, 113, 227, ${alpha})`
  if (typeof hex !== 'string') return fallback
  const m = hex.replace('#', '').match(/^([0-9a-fA-F]{6})$/)
  if (!m) return fallback
  const r = parseInt(m[1].slice(0, 2), 16)
  const g = parseInt(m[1].slice(2, 4), 16)
  const b = parseInt(m[1].slice(4, 6), 16)
  return `rgba(${r}, ${g}, ${b}, ${alpha})`
}
</script>

<style scoped>
.stat-card {
  display: flex;
  align-items: center;
  gap: 16px;
  /* Apple 玻璃卡片 */
  background-color: var(--app-card);
  -webkit-backdrop-filter: blur(var(--app-glass-blur)) saturate(var(--app-glass-saturate));
  backdrop-filter: blur(var(--app-glass-blur)) saturate(var(--app-glass-saturate));
  border-radius: var(--app-radius-card);
  border: 1px solid rgba(255, 255, 255, 0.6);
  box-shadow: var(--app-shadow-card);
  padding: 24px 28px;
  box-sizing: border-box;
  transition: transform 0.3s cubic-bezier(0.4, 0, 0.2, 1),
              box-shadow 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}
/* Apple 官网数据卡：悬停上浮 4px */
.stat-card:hover {
  transform: translateY(-4px);
  box-shadow: var(--app-shadow-hover);
}

/* 48px 圆角图标方块 */
.stat-card__icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 48px;
  height: 48px;
  border-radius: 14px;
  flex-shrink: 0;
}

.stat-card__body {
  min-width: 0;
  flex: 1;
}

/* Apple 官网风格：42px 大数字 */
.stat-card__value {
  font-size: 42px;
  font-weight: 600;
  color: var(--app-text-1);
  line-height: 1.1;
  font-variant-numeric: tabular-nums;
  font-family: var(--app-font-number);
  letter-spacing: -0.03em;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.stat-card__label {
  margin-top: 6px;
  font-size: 13px;
  color: var(--app-text-3);
  letter-spacing: 0.01em;
}
</style>
