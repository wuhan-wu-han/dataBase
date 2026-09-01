<template>
  <!-- 智慧管廊智能预警驾驶舱 -->
  <div class="dashboard-container">
    <!-- 背景粒子效果 -->
    <div class="bg-particles">
      <div v-for="i in 20" :key="i" class="particle" :style="particleStyle(i)"></div>
    </div>

    <!-- 顶部标题栏 -->
    <header class="dashboard-header">
      <div class="header-left">
        <div class="system-status">
          <span class="status-item" v-for="s in systemStatus" :key="s.name">
            <span class="status-dot" :class="{ online: s.online }"></span>
            {{ s.name }}
          </span>
        </div>
      </div>
      <div class="header-center">
        <div class="header-decor left-decor">
          <span class="decor-line"></span>
          <span class="decor-diamond"></span>
          <span class="decor-line"></span>
        </div>
        <div class="header-title-group">
          <h1 class="header-title">智慧管廊智能预警驾驶舱</h1>
          <p class="header-subtitle">INTELLIGENT PIPELINE WARNING CENTER</p>
        </div>
        <div class="header-decor right-decor">
          <span class="decor-line"></span>
          <span class="decor-diamond"></span>
          <span class="decor-line"></span>
        </div>
      </div>
      <div class="header-right">
        <div class="realtime-clock">{{ currentTime }}</div>
        <div class="realtime-date">{{ currentDate }}</div>
      </div>
    </header>

    <!-- 主体内容 -->
    <main class="dashboard-main">
      <!-- 统计卡片区域 -->
      <section class="stat-section">
        <StatCard label="预警总数" :value="totalAlerts" icon="Warning" color="#1890ff" />
        <StatCard label="待处理预警" :value="openAlerts" icon="Bell" color="#fa8c16" />
        <StatCard label="红色预警" :value="redAlerts" icon="CircleClose" color="#ff4d4f" />
        <StatCard label="监控区域" :value="areaCount" icon="Location" color="#13c2c2" />
      </section>

      <!-- 图表区域 -->
      <section class="chart-section">
        <!-- 左：预警等级分布环形图 -->
        <div class="chart-panel">
          <div class="panel-header">
            <span class="panel-icon">&#9670;</span>
            <span class="panel-title">预警等级分布</span>
          </div>
          <div ref="pieChartRef" class="chart-container"></div>
        </div>

        <!-- 中：今日事件趋势折线图 -->
        <div class="chart-panel">
          <div class="panel-header">
            <span class="panel-icon">&#9670;</span>
            <span class="panel-title">24小时预警趋势</span>
          </div>
          <div ref="lineChartRef" class="chart-container"></div>
        </div>

        <!-- 右：区域风险排行 -->
        <div class="chart-panel">
          <div class="panel-header">
            <span class="panel-icon">&#9670;</span>
            <span class="panel-title">区域风险排行</span>
          </div>
          <div ref="barChartRef" class="chart-container"></div>
        </div>
      </section>

      <!-- 最新预警列表 -->
      <section class="alert-section">
        <div class="panel-header">
          <span class="panel-icon">&#9670;</span>
          <span class="panel-title">最新预警事件</span>
          <span class="panel-badge">{{ recentAlerts.length }} 条</span>
        </div>
        <div class="alert-list" v-loading="tableLoading" element-loading-background="rgba(0,0,0,0.3)">
          <div
            v-for="alert in recentAlerts"
            :key="alert.id"
            class="alert-row"
            :class="'level-' + (alert.alertLevel || '').toLowerCase()"
          >
            <!-- 左侧等级颜色条 -->
            <div class="alert-level-bar"></div>
            <!-- 等级标签 -->
            <div class="alert-level-cell">
              <AlertLevelTag :level="alert.alertLevel" />
            </div>
            <!-- 预警编码 -->
            <div class="alert-code">{{ alert.alertEventCode }}</div>
            <!-- 设备 -->
            <div class="alert-device">
              <span class="cell-label">设备</span>
              <span>{{ alert.deviceId }}</span>
            </div>
            <!-- 设备类型 -->
            <div class="alert-type">{{ alert.deviceType }}</div>
            <!-- 区域 -->
            <div class="alert-area">
              <span class="cell-label">区域</span>
              <span>{{ alert.areaId }}</span>
            </div>
            <!-- 状态 -->
            <div class="alert-status-cell">
              <AlertStatusTag :status="alert.alertStatus" />
            </div>
            <!-- 优先级 -->
            <div class="alert-priority">
              <span class="cell-label">优先级</span>
              <span class="priority-value">{{ alert.priorityScore }}</span>
            </div>
            <!-- 时间 -->
            <div class="alert-time">{{ formatDateTime(alert.eventTimestamp) }}</div>
          </div>
          <!-- 空状态 -->
          <div v-if="!tableLoading && recentAlerts.length === 0" class="alert-empty">
            暂无预警数据
          </div>
        </div>
      </section>
    </main>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import * as echarts from 'echarts'
import { ElMessage } from 'element-plus'
import StatCard from '@/components/StatCard.vue'
import AlertLevelTag from '@/components/AlertLevelTag.vue'
import AlertStatusTag from '@/components/AlertStatusTag.vue'
import { getAlertList } from '@/api/alert'
import { getAreaPriorityList } from '@/api/areaPriority'
import { formatDateTime } from '@/utils/format'

// ==================== 数据状态 ====================
const totalAlerts = ref(0)
const openAlerts = ref(0)
const redAlerts = ref(0)
const areaCount = ref(0)
const recentAlerts = ref([])
const tableLoading = ref(false)

// ==================== 系统状态（模拟） ====================
const systemStatus = ref([
  { name: 'Kafka', online: true },
  { name: 'Redis', online: true },
  { name: 'MySQL', online: true }
])

// ==================== 实时时钟 ====================
const currentTime = ref('')
const currentDate = ref('')
let clockTimer = null

const updateClock = () => {
  const now = new Date()
  const h = String(now.getHours()).padStart(2, '0')
  const m = String(now.getMinutes()).padStart(2, '0')
  const s = String(now.getSeconds()).padStart(2, '0')
  currentTime.value = `${h}:${m}:${s}`

  const y = now.getFullYear()
  const mo = String(now.getMonth() + 1).padStart(2, '0')
  const d = String(now.getDate()).padStart(2, '0')
  const weekDays = ['星期日', '星期一', '星期二', '星期三', '星期四', '星期五', '星期六']
  currentDate.value = `${y}-${mo}-${d} ${weekDays[now.getDay()]}`
}

// ==================== 粒子效果 ====================
const particleStyle = (i) => ({
  left: `${Math.random() * 100}%`,
  top: `${Math.random() * 100}%`,
  animationDelay: `${Math.random() * 6}s`,
  animationDuration: `${4 + Math.random() * 6}s`,
  width: `${2 + Math.random() * 3}px`,
  height: `${2 + Math.random() * 3}px`,
  opacity: 0.2 + Math.random() * 0.4
})

// ==================== 图表实例 ====================
const pieChartRef = ref(null)
const barChartRef = ref(null)
const lineChartRef = ref(null)
let pieChart = null
let barChart = null
let lineChart = null

// ==================== 数据加载 ====================
const loadStats = async () => {
  try {
    const totalRes = await getAlertList({ page: 1, size: 1 })
    totalAlerts.value = totalRes?.total || 0

    const openRes = await getAlertList({ status: 'OPEN', page: 1, size: 1 })
    openAlerts.value = openRes?.total || 0

    const redRes = await getAlertList({ alertLevel: 'RED', page: 1, size: 1 })
    redAlerts.value = redRes?.total || 0

    const areaRes = await getAreaPriorityList()
    areaCount.value = Array.isArray(areaRes) ? areaRes.length : 0
  } catch (error) {
    console.error('加载统计数据失败:', error)
  }
}

const loadRecentAlerts = async () => {
  tableLoading.value = true
  try {
    const res = await getAlertList({ page: 1, size: 10 })
    recentAlerts.value = res?.records || []
  } catch (error) {
    ElMessage.error('加载预警列表失败')
    console.error('加载预警列表失败:', error)
  } finally {
    tableLoading.value = false
  }
}

// ==================== ECharts 配置 ====================

// 预警等级分布 - 环形仪表盘
const initPieChart = async () => {
  try {
    const res = await getAlertList({ page: 1, size: 100 })
    const records = res?.records || []

    const levelCount = { BLUE: 0, YELLOW: 0, ORANGE: 0, RED: 0 }
    records.forEach(item => {
      if (levelCount[item.alertLevel] !== undefined) levelCount[item.alertLevel]++
    })
    const total = records.length

    if (!pieChartRef.value) return
    pieChart = echarts.init(pieChartRef.value)

    const option = {
      backgroundColor: 'transparent',
      tooltip: {
        trigger: 'item',
        backgroundColor: 'rgba(13, 27, 42, 0.9)',
        borderColor: '#1890ff44',
        textStyle: { color: '#e0e6ed' },
        formatter: '{b}: {c} ({d}%)'
      },
      legend: {
        orient: 'vertical',
        right: 16,
        top: 'center',
        itemWidth: 12,
        itemHeight: 12,
        itemGap: 16,
        textStyle: { color: '#8a9bb0', fontSize: 12 }
      },
      series: [
        // 外层装饰环
        {
          type: 'pie',
          radius: ['72%', '74%'],
          center: ['40%', '50%'],
          silent: true,
          label: { show: false },
          data: [{ value: 1, itemStyle: { color: 'rgba(24, 144, 255, 0.15)' } }]
        },
        // 主环形图
        {
          name: '预警等级',
          type: 'pie',
          radius: ['45%', '70%'],
          center: ['40%', '50%'],
          avoidLabelOverlap: false,
          startAngle: 90,
          itemStyle: {
            borderRadius: 6,
            borderColor: '#0a1628',
            borderWidth: 3,
            shadowBlur: 20,
            shadowColor: 'rgba(24, 144, 255, 0.3)'
          },
          label: {
            show: true,
            position: 'outside',
            color: '#e0e6ed',
            fontSize: 12,
            formatter: '{b}\n{c}件'
          },
          labelLine: {
            lineStyle: { color: '#2a3a4a' }
          },
          emphasis: {
            scaleSize: 8,
            itemStyle: { shadowBlur: 30, shadowColor: 'rgba(24, 144, 255, 0.5)' }
          },
          data: [
            { value: levelCount.BLUE, name: '蓝色预警', itemStyle: { color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [{ offset: 0, color: '#36cfe9' }, { offset: 1, color: '#1890ff' }]) } },
            { value: levelCount.YELLOW, name: '黄色预警', itemStyle: { color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [{ offset: 0, color: '#ffe066' }, { offset: 1, color: '#fadb14' }]) } },
            { value: levelCount.ORANGE, name: '橙色预警', itemStyle: { color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [{ offset: 0, color: '#ffc069' }, { offset: 1, color: '#fa8c16' }]) } },
            { value: levelCount.RED, name: '红色预警', itemStyle: { color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [{ offset: 0, color: '#ff7875' }, { offset: 1, color: '#ff4d4f' }]) } }
          ]
        },
        // 中心文字
        {
          type: 'pie',
          radius: ['0%', '0%'],
          center: ['40%', '50%'],
          label: {
            show: true,
            position: 'center',
            formatter: () => `{total|${total}}\n{label|预警总数}`,
            rich: {
              total: {
                fontSize: 32,
                fontWeight: 700,
                color: '#e0e6ed',
                lineHeight: 40
              },
              label: {
                fontSize: 12,
                color: '#8a9bb0',
                lineHeight: 20
              }
            }
          },
          data: [{ value: 0 }]
        }
      ]
    }
    pieChart.setOption(option)
  } catch (error) {
    console.error('初始化饼图失败:', error)
  }
}

// 区域风险排行 - 科技横向柱状图
const initBarChart = async () => {
  try {
    const areaRes = await getAreaPriorityList()
    const areas = Array.isArray(areaRes) ? areaRes : []
    areas.sort((a, b) => a.importance - b.importance)

    if (!barChartRef.value) return
    barChart = echarts.init(barChartRef.value)

    const option = {
      backgroundColor: 'transparent',
      tooltip: {
        trigger: 'axis',
        axisPointer: { type: 'shadow' },
        backgroundColor: 'rgba(13, 27, 42, 0.9)',
        borderColor: '#1890ff44',
        textStyle: { color: '#e0e6ed' }
      },
      grid: { left: '3%', right: '15%', bottom: '3%', top: '8%', containLabel: true },
      xAxis: {
        type: 'value',
        axisLabel: { color: '#5a6f86' },
        axisLine: { show: false },
        splitLine: { lineStyle: { color: 'rgba(42, 58, 74, 0.4)', type: 'dashed' } }
      },
      yAxis: {
        type: 'category',
        data: areas.map(a => a.areaName),
        axisLabel: { color: '#e0e6ed', fontSize: 12 },
        axisLine: { lineStyle: { color: '#2a3a4a' } },
        axisTick: { show: false }
      },
      series: [{
        name: '重要度',
        type: 'bar',
        data: areas.map(a => a.importance),
        barWidth: 16,
        itemStyle: {
          borderRadius: [0, 8, 8, 0],
          color: new echarts.graphic.LinearGradient(0, 0, 1, 0, [
            { offset: 0, color: 'rgba(24, 144, 255, 0.3)' },
            { offset: 0.5, color: '#1890ff' },
            { offset: 1, color: '#36cfe9' }
          ]),
          shadowBlur: 12,
          shadowColor: 'rgba(24, 144, 255, 0.4)'
        },
        label: {
          show: true,
          position: 'right',
          color: '#36cfe9',
          fontSize: 13,
          fontWeight: 700,
          formatter: '{c}'
        },
        emphasis: {
          itemStyle: {
            shadowBlur: 20,
            shadowColor: 'rgba(24, 144, 255, 0.6)'
          }
        }
      }]
    }
    barChart.setOption(option)
  } catch (error) {
    console.error('初始化柱状图失败:', error)
  }
}

// 24小时预警趋势折线图
const initLineChart = async () => {
  try {
    if (!lineChartRef.value) return
    lineChart = echarts.init(lineChartRef.value)

    // 从已有数据生成24小时分布
    const res = await getAlertList({ page: 1, size: 100 })
    const records = res?.records || []

    const hourCounts = new Array(24).fill(0)
    records.forEach(item => {
      if (item.eventTimestamp) {
        const hour = new Date(item.eventTimestamp).getHours()
        hourCounts[hour]++
      }
    })

    const hours = Array.from({ length: 24 }, (_, i) => `${String(i).padStart(2, '0')}:00`)

    const option = {
      backgroundColor: 'transparent',
      tooltip: {
        trigger: 'axis',
        backgroundColor: 'rgba(13, 27, 42, 0.9)',
        borderColor: '#1890ff44',
        textStyle: { color: '#e0e6ed' }
      },
      grid: { left: '3%', right: '5%', bottom: '3%', top: '10%', containLabel: true },
      xAxis: {
        type: 'category',
        data: hours,
        boundaryGap: false,
        axisLabel: { color: '#5a6f86', fontSize: 10, interval: 3 },
        axisLine: { lineStyle: { color: '#2a3a4a' } },
        axisTick: { show: false }
      },
      yAxis: {
        type: 'value',
        minInterval: 1,
        axisLabel: { color: '#5a6f86' },
        axisLine: { show: false },
        splitLine: { lineStyle: { color: 'rgba(42, 58, 74, 0.4)', type: 'dashed' } }
      },
      series: [{
        name: '预警数',
        type: 'line',
        data: hourCounts,
        smooth: true,
        symbol: 'circle',
        symbolSize: 6,
        lineStyle: {
          width: 3,
          color: new echarts.graphic.LinearGradient(0, 0, 1, 0, [
            { offset: 0, color: '#1890ff' },
            { offset: 1, color: '#36cfe9' }
          ]),
          shadowBlur: 10,
          shadowColor: 'rgba(24, 144, 255, 0.4)'
        },
        itemStyle: {
          color: '#36cfe9',
          borderColor: '#0a1628',
          borderWidth: 2
        },
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: 'rgba(24, 144, 255, 0.3)' },
            { offset: 0.5, color: 'rgba(24, 144, 255, 0.1)' },
            { offset: 1, color: 'rgba(24, 144, 255, 0)' }
          ])
        }
      }]
    }
    lineChart.setOption(option)
  } catch (error) {
    console.error('初始化趋势图失败:', error)
  }
}

// ==================== 窗口自适应 ====================
const handleResize = () => {
  pieChart?.resize()
  barChart?.resize()
  lineChart?.resize()
}

// ==================== 生命周期 ====================
onMounted(() => {
  updateClock()
  clockTimer = setInterval(updateClock, 1000)
  loadStats()
  loadRecentAlerts()
  initPieChart()
  initBarChart()
  initLineChart()
  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  clearInterval(clockTimer)
  window.removeEventListener('resize', handleResize)
  pieChart?.dispose()
  barChart?.dispose()
  lineChart?.dispose()
})
</script>

<style scoped>
/* ==================== 容器 ==================== */
.dashboard-container {
  min-height: 100vh;
  position: relative;
  overflow: hidden;
}

/* ==================== 背景粒子 ==================== */
.bg-particles {
  position: fixed;
  top: 0; left: 0; right: 0; bottom: 0;
  pointer-events: none;
  z-index: 0;
}

.particle {
  position: absolute;
  background: #1890ff;
  border-radius: 50%;
  animation: particleFloat 6s ease-in-out infinite;
}

@keyframes particleFloat {
  0%, 100% { transform: translateY(0) scale(1); opacity: 0.2; }
  50% { transform: translateY(-30px) scale(1.5); opacity: 0.6; }
}

/* ==================== 顶部标题栏 ==================== */
.dashboard-header {
  position: relative;
  z-index: 10;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 40px;
  background: linear-gradient(180deg, rgba(10, 22, 40, 0.95) 0%, rgba(10, 22, 40, 0.7) 100%);
  border-bottom: 1px solid rgba(24, 144, 255, 0.2);
  backdrop-filter: blur(12px);
}

/* 左侧系统状态 */
.header-left {
  flex: 1;
}

.system-status {
  display: flex;
  gap: 16px;
}

.status-item {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: #8a9bb0;
}

.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #5a6f86;
}

.status-dot.online {
  background: #52c41a;
  box-shadow: 0 0 8px rgba(82, 196, 26, 0.6);
  animation: statusPulse 2s ease-in-out infinite;
}

@keyframes statusPulse {
  0%, 100% { box-shadow: 0 0 8px rgba(82, 196, 26, 0.6); }
  50% { box-shadow: 0 0 16px rgba(82, 196, 26, 0.9); }
}

/* 中间标题 */
.header-center {
  display: flex;
  align-items: center;
  gap: 24px;
  flex-shrink: 0;
}

.header-decor {
  display: flex;
  align-items: center;
  gap: 4px;
}

.decor-line {
  display: block;
  width: 60px;
  height: 2px;
  background: linear-gradient(90deg, transparent, #1890ff);
}

.right-decor .decor-line {
  background: linear-gradient(90deg, #1890ff, transparent);
}

.decor-diamond {
  display: block;
  width: 8px;
  height: 8px;
  background: #1890ff;
  transform: rotate(45deg);
  box-shadow: 0 0 10px rgba(24, 144, 255, 0.6);
}

.header-title-group {
  text-align: center;
}

.header-title {
  font-size: 28px;
  font-weight: 700;
  margin: 0;
  letter-spacing: 6px;
  background: linear-gradient(90deg, #36cfe9, #1890ff, #36cfe9);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  text-shadow: none;
  filter: drop-shadow(0 0 12px rgba(24, 144, 255, 0.4));
}

.header-subtitle {
  font-size: 11px;
  color: #5a7a9a;
  margin: 6px 0 0 0;
  letter-spacing: 4px;
  text-transform: uppercase;
}

/* 右侧时钟 */
.header-right {
  flex: 1;
  text-align: right;
}

.realtime-clock {
  font-size: 24px;
  font-weight: 700;
  color: #36cfe9;
  font-family: 'Courier New', monospace;
  letter-spacing: 2px;
  text-shadow: 0 0 10px rgba(54, 207, 233, 0.4);
}

.realtime-date {
  font-size: 12px;
  color: #5a7a9a;
  margin-top: 2px;
}

/* ==================== 主体内容 ==================== */
.dashboard-main {
  position: relative;
  z-index: 1;
  padding: 20px 40px;
}

/* ==================== 统计卡片 ==================== */
.stat-section {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 20px;
  margin-bottom: 20px;
}

/* ==================== 图表面板 ==================== */
.chart-section {
  display: grid;
  grid-template-columns: 1fr 1fr 1fr;
  gap: 20px;
  margin-bottom: 20px;
}

.chart-panel {
  background: linear-gradient(135deg, rgba(27, 40, 56, 0.7), rgba(13, 27, 42, 0.8));
  border-radius: 12px;
  padding: 20px;
  border: 1px solid rgba(42, 58, 74, 0.6);
  backdrop-filter: blur(8px);
  transition: all 0.3s ease;
}

.chart-panel:hover {
  border-color: rgba(24, 144, 255, 0.3);
  box-shadow: 0 4px 24px rgba(24, 144, 255, 0.1);
}

.panel-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 16px;
}

.panel-icon {
  color: #1890ff;
  font-size: 10px;
}

.panel-title {
  font-size: 15px;
  font-weight: 600;
  color: #e0e6ed;
  letter-spacing: 1px;
}

.panel-badge {
  margin-left: auto;
  font-size: 12px;
  color: #1890ff;
  background: rgba(24, 144, 255, 0.1);
  padding: 2px 10px;
  border-radius: 10px;
  border: 1px solid rgba(24, 144, 255, 0.2);
}

.chart-container {
  height: 280px;
  width: 100%;
}

/* ==================== 预警列表 ==================== */
.alert-section {
  background: linear-gradient(135deg, rgba(27, 40, 56, 0.7), rgba(13, 27, 42, 0.8));
  border-radius: 12px;
  padding: 20px;
  border: 1px solid rgba(42, 58, 74, 0.6);
  backdrop-filter: blur(8px);
}

.alert-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
  max-height: 400px;
  overflow-y: auto;
}

.alert-row {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 12px 16px;
  border-radius: 8px;
  background: rgba(13, 27, 42, 0.6);
  border: 1px solid rgba(42, 58, 74, 0.4);
  transition: all 0.25s ease;
  position: relative;
  overflow: hidden;
}

.alert-row:hover {
  background: rgba(24, 144, 255, 0.06);
  border-color: rgba(24, 144, 255, 0.2);
  box-shadow: 0 0 20px rgba(24, 144, 255, 0.08);
  transform: translateX(4px);
}

/* 左侧等级颜色条 */
.alert-level-bar {
  width: 4px;
  height: 100%;
  position: absolute;
  left: 0;
  top: 0;
  bottom: 0;
  border-radius: 4px 0 0 4px;
}

.level-red .alert-level-bar { background: linear-gradient(180deg, #ff7875, #ff4d4f); box-shadow: 0 0 8px rgba(255, 77, 79, 0.5); }
.level-orange .alert-level-bar { background: linear-gradient(180deg, #ffc069, #fa8c16); box-shadow: 0 0 8px rgba(250, 140, 22, 0.5); }
.level-yellow .alert-level-bar { background: linear-gradient(180deg, #ffe066, #fadb14); box-shadow: 0 0 8px rgba(250, 219, 20, 0.5); }
.level-blue .alert-level-bar { background: linear-gradient(180deg, #69c0ff, #1890ff); box-shadow: 0 0 8px rgba(24, 144, 255, 0.5); }

.alert-level-cell { flex-shrink: 0; width: 80px; }
.alert-code { flex: 1; font-family: 'Courier New', monospace; font-size: 13px; color: #e0e6ed; min-width: 180px; }
.alert-device { width: 160px; font-size: 13px; color: #b0bec5; }
.alert-type { width: 100px; font-size: 13px; color: #8a9bb0; }
.alert-area { width: 100px; font-size: 13px; color: #b0bec5; }
.alert-status-cell { flex-shrink: 0; width: 80px; }
.alert-priority { width: 100px; font-size: 13px; color: #8a9bb0; }
.alert-time { width: 170px; font-size: 13px; color: #5a7a9a; font-family: 'Courier New', monospace; text-align: right; }

.cell-label {
  display: block;
  font-size: 10px;
  color: #5a6f86;
  margin-bottom: 2px;
  text-transform: uppercase;
}

.priority-value {
  font-weight: 700;
  color: #36cfe9;
  font-size: 16px;
}

.alert-empty {
  text-align: center;
  padding: 40px;
  color: #5a6f86;
  font-size: 14px;
}

/* ==================== 适配 ==================== */
@media (max-width: 1400px) {
  .chart-section {
    grid-template-columns: 1fr 1fr;
  }
  .chart-section .chart-panel:last-child {
    grid-column: span 2;
  }
}

@media (max-width: 1024px) {
  .stat-section {
    grid-template-columns: repeat(2, 1fr);
  }
  .chart-section {
    grid-template-columns: 1fr;
  }
  .chart-section .chart-panel:last-child {
    grid-column: span 1;
  }
}
</style>
