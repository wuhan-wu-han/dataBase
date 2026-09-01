<template>
  <!-- 科技仪表盘卡片 - 玻璃拟态 + 发光边框 -->
  <div class="stat-card" :style="cardStyle">
    <div class="card-glow"></div>
    <div class="card-content">
      <div class="stat-icon" :style="iconStyle">
        <el-icon :size="32"><component :is="icon" /></el-icon>
      </div>
      <div class="stat-info">
        <div class="stat-value" :style="valueStyle">
          {{ animatedValue }}
        </div>
        <div class="stat-label">{{ label }}</div>
      </div>
    </div>
    <div class="card-decoration"></div>
  </div>
</template>

<script setup>
import { computed, ref, watch, onMounted } from 'vue'

const props = defineProps({
  label: { type: String, required: true },
  value: { type: [Number, String], default: 0 },
  icon: { type: String, default: 'DataLine' },
  color: { type: String, default: '#1890ff' }
})

// 数字动画
const animatedValue = ref(0)

watch(() => props.value, (newVal) => {
  animateNumber(Number(newVal) || 0)
})

onMounted(() => {
  animateNumber(Number(props.value) || 0)
})

const animateNumber = (target) => {
  const start = animatedValue.value
  const diff = target - start
  const duration = 800
  const startTime = performance.now()

  const step = (currentTime) => {
    const elapsed = currentTime - startTime
    const progress = Math.min(elapsed / duration, 1)
    const eased = 1 - Math.pow(1 - progress, 3)
    animatedValue.value = Math.round(start + diff * eased)
    if (progress < 1) requestAnimationFrame(step)
  }
  requestAnimationFrame(step)
}

// 卡片样式
const cardStyle = computed(() => ({
  '--card-color': props.color,
  '--card-glow': props.color + '40',
  '--card-border': props.color + '60'
}))

const iconStyle = computed(() => ({
  background: `linear-gradient(135deg, ${props.color}33, ${props.color}11)`,
  color: props.color,
  boxShadow: `0 0 20px ${props.color}33`
}))

const valueStyle = computed(() => ({
  background: `linear-gradient(135deg, ${props.color}, #ffffff)`,
  WebkitBackgroundClip: 'text',
  WebkitTextFillColor: 'transparent',
  backgroundClip: 'text'
}))
</script>

<style scoped>
.stat-card {
  position: relative;
  padding: 24px;
  border-radius: 16px;
  background: linear-gradient(135deg, rgba(27, 40, 56, 0.8), rgba(13, 27, 42, 0.9));
  border: 1px solid var(--card-border, rgba(24, 144, 255, 0.3));
  backdrop-filter: blur(10px);
  overflow: hidden;
  transition: all 0.3s ease;
  cursor: pointer;
}

.stat-card:hover {
  transform: translateY(-4px);
  border-color: var(--card-color, #1890ff);
  box-shadow: 0 8px 32px var(--card-glow, rgba(24, 144, 255, 0.3));
}

.stat-card:hover .card-glow {
  opacity: 1;
}

/* 发光效果 */
.card-glow {
  position: absolute;
  top: -50%;
  left: -50%;
  width: 200%;
  height: 200%;
  background: radial-gradient(circle, var(--card-glow, rgba(24, 144, 255, 0.2)) 0%, transparent 70%);
  opacity: 0;
  transition: opacity 0.3s ease;
  pointer-events: none;
}

.card-content {
  position: relative;
  display: flex;
  align-items: center;
  gap: 20px;
  z-index: 1;
}

.stat-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 64px;
  height: 64px;
  border-radius: 16px;
  flex-shrink: 0;
}

.stat-info {
  flex: 1;
}

.stat-value {
  font-size: 40px;
  font-weight: 700;
  line-height: 1.2;
  letter-spacing: -1px;
}

.stat-label {
  font-size: 14px;
  color: #8a9bb0;
  margin-top: 8px;
  text-transform: uppercase;
  letter-spacing: 1px;
}

/* 装饰线条 */
.card-decoration {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  height: 3px;
  background: linear-gradient(90deg, transparent, var(--card-color, #1890ff), transparent);
  opacity: 0.6;
}
</style>
