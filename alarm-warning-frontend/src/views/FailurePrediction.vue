<template>
  <div class="prediction-container">
    <!-- 背景粒子效果 -->
    <div class="bg-particles">
      <div v-for="i in 20" :key="i" class="particle" :style="particleStyle(i)"></div>
    </div>

    <!-- 顶部标题栏 -->
    <header class="page-header">
      <div class="header-left">
        <span class="back-btn" @click="$router.push('/')">
          <el-icon><ArrowLeft /></el-icon> 返回大屏
        </span>
      </div>
      <div class="header-center">
        <div class="header-decor left-decor">
          <span class="decor-line"></span>
          <span class="decor-diamond"></span>
          <span class="decor-line"></span>
        </div>
        <div class="header-title-group">
          <h1 class="header-title">故障预报与寿命预测</h1>
          <p class="header-subtitle">FAILURE PREDICTION & LIFETIME ANALYSIS</p>
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
    <main class="page-main">
      <!-- 统计卡片 -->
      <section class="stat-section">
        <div class="stat-card" style="--card-color: #1890ff;">
          <div class="card-glow"></div>
          <div class="card-content">
            <div class="stat-icon" style="background: linear-gradient(135deg, #1890ff33, #1890ff11); color: #1890ff;">
              <el-icon :size="32"><Monitor /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value" style="background: linear-gradient(135deg, #1890ff, #fff); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">{{ stats.totalDevices }}</div>
              <div class="stat-label">设备总数</div>
            </div>
          </div>
          <div class="card-decoration"></div>
        </div>

        <div class="stat-card" style="--card-color: #ff4d4f;">
          <div class="card-glow"></div>
          <div class="card-content">
            <div class="stat-icon" style="background: linear-gradient(135deg, #ff4d4f33, #ff4d4f11); color: #ff4d4f;">
              <el-icon :size="32"><Warning /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value" style="background: linear-gradient(135deg, #ff4d4f, #fff); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">{{ stats.highRiskCount }}</div>
              <div class="stat-label">高风险设备</div>
            </div>
          </div>
          <div class="card-decoration"></div>
        </div>

        <div class="stat-card" style="--card-color: #52c41a;">
          <div class="card-glow"></div>
          <div class="card-content">
            <div class="stat-icon" style="background: linear-gradient(135deg, #52c41a33, #52c41a11); color: #52c41a;">
              <el-icon :size="32"><CircleCheck /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value" style="background: linear-gradient(135deg, #52c41a, #fff); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">{{ stats.avgHealthScore }}</div>
              <div class="stat-label">平均健康度</div>
            </div>
          </div>
          <div class="card-decoration"></div>
        </div>

        <div class="stat-card" style="--card-color: #fa8c16;">
          <div class="card-glow"></div>
          <div class="card-content">
            <div class="stat-icon" style="background: linear-gradient(135deg, #fa8c1633, #fa8c1611); color: #fa8c16;">
              <el-icon :size="32"><Timer /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value" style="background: linear-gradient(135deg, #fa8c16, #fff); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">{{ stats.avgRemainingLifeMonth }}</div>
              <div class="stat-label">平均剩余寿命(月)</div>
            </div>
          </div>
          <div class="card-decoration"></div>
        </div>
      </section>

      <!-- 中间区域：饼图 + 操作 -->
      <section class="middle-section">
        <div class="chart-panel">
          <div class="panel-header">
            <span class="panel-icon">&#9670;</span>
            <span class="panel-title">风险等级分布</span>
          </div>
          <div ref="pieChartRef" class="chart-container"></div>
        </div>

        <div class="action-panel">
          <div class="panel-header">
            <span class="panel-icon">&#9670;</span>
            <span class="panel-title">预测操作</span>
          </div>
          <div class="action-content">
            <p class="action-desc">基于当前预警事件数据，对所有设备进行健康评估、故障概率计算和剩余寿命预测。</p>
            <el-button type="primary" size="large" :loading="generating" @click="handleGenerate" class="generate-btn">
              <el-icon><Cpu /></el-icon>
              生成预测
            </el-button>
            <div v-if="generateResult" class="generate-result">
              <div class="result-item">
                <span class="result-label">设备</span>
                <span class="result-value">{{ generateResult.deviceId }}</span>
              </div>
              <div class="result-item">
                <span class="result-label">健康度</span>
                <span class="result-value">{{ generateResult.healthScore }}</span>
              </div>
              <div class="result-item">
                <span class="result-label">故障概率</span>
                <span class="result-value">{{ generateResult.failureProbability }}%</span>
              </div>
              <div class="result-item">
                <span class="result-label">剩余寿命</span>
                <span class="result-value">{{ generateResult.remainingLifeMonth }} 月</span>
              </div>
              <div class="result-item">
                <span class="result-label">预测等级</span>
                <span class="result-value">
                  <span class="level-badge" :class="'level-' + generateResult.predictionLevel?.toLowerCase()">
                    {{ levelText(generateResult.predictionLevel) }}
                  </span>
                </span>
              </div>
            </div>
          </div>
        </div>
      </section>

      <!-- 下方：预测列表 -->
      <section class="table-section">
        <div class="panel-header">
          <span class="panel-icon">&#9670;</span>
          <span class="panel-title">预测记录列表</span>
          <span class="panel-badge">{{ total }} 条</span>
        </div>

        <!-- 筛选栏 -->
        <div class="filter-bar">
          <el-select v-model="query.predictionLevel" placeholder="预测等级" clearable class="filter-select">
            <el-option label="全部" value="" />
            <el-option label="低风险" value="LOW" />
            <el-option label="中风险" value="MEDIUM" />
            <el-option label="高风险" value="HIGH" />
            <el-option label="危急" value="CRITICAL" />
          </el-select>
          <el-button type="primary" @click="loadData" class="filter-btn">
            <el-icon><Search /></el-icon> 查询
          </el-button>
          <el-button @click="resetQuery" class="filter-btn">重置</el-button>
        </div>

        <!-- 表格 -->
        <el-table
          :data="tableData"
          v-loading="tableLoading"
          element-loading-background="rgba(0,0,0,0.3)"
          class="prediction-table"
          :header-cell-style="{ background: 'rgba(13, 27, 42, 0.8)', color: '#8a9bb0', borderColor: 'rgba(42, 58, 74, 0.6)' }"
          :cell-style="{ background: 'rgba(13, 27, 42, 0.4)', color: '#e0e6ed', borderColor: 'rgba(42, 58, 74, 0.4)' }"
        >
          <el-table-column prop="deviceId" label="设备ID" min-width="140" />
          <el-table-column prop="deviceType" label="设备类型" width="120" />
          <el-table-column prop="areaId" label="区域" width="120" />
          <el-table-column label="健康度" width="100" align="center">
            <template #default="{ row }">
              <span :class="healthClass(row.healthScore)">{{ row.healthScore }}</span>
            </template>
          </el-table-column>
          <el-table-column label="风险分" width="100" align="center">
            <template #default="{ row }">
              <span :class="riskClass(row.riskScore)">{{ row.riskScore }}</span>
            </template>
          </el-table-column>
          <el-table-column label="故障概率" width="110" align="center">
            <template #default="{ row }">
              <span :class="probClass(row.failureProbability)">{{ row.failureProbability }}%</span>
            </template>
          </el-table-column>
          <el-table-column label="剩余寿命" width="110" align="center">
            <template #default="{ row }">
              <span class="life-value">{{ row.remainingLifeMonth }} 月</span>
            </template>
          </el-table-column>
          <el-table-column label="预测等级" width="110" align="center">
            <template #default="{ row }">
              <span class="level-badge" :class="'level-' + row.predictionLevel?.toLowerCase()">
                {{ levelText(row.predictionLevel) }}
              </span>
            </template>
          </el-table-column>
          <el-table-column prop="predictionTime" label="预测时间" width="170">
            <template #default="{ row }">
              <span class="time-cell">{{ formatTime(row.predictionTime) }}</span>
            </template>
          </el-table-column>
        </el-table>

        <!-- 分页 -->
        <div class="pagination-bar">
          <el-pagination
            v-model:current-page="query.page"
            v-model:page-size="query.size"
            :total="total"
            :page-sizes="[10, 20, 50]"
            layout="total, sizes, prev, pager, next"
            @size-change="loadData"
            @current-change="loadData"
          />
        </div>
      </section>
    </main>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import * as echarts from 'echarts'
import { ElMessage } from 'element-plus'
import { ArrowLeft, Monitor, Warning, CircleCheck, Timer, Cpu, Search } from '@element-plus/icons-vue'
import { getPredictionList, generatePrediction, getPredictionStatistics } from '@/api/failurePrediction'

// ==================== 时钟 ====================
const currentTime = ref('')
const currentDate = ref('')
let clockTimer = null

const updateClock = () => {
  const now = new Date()
  currentTime.value = `${String(now.getHours()).padStart(2, '0')}:${String(now.getMinutes()).padStart(2, '0')}:${String(now.getSeconds()).padStart(2, '0')}`
  const y = now.getFullYear()
  const mo = String(now.getMonth() + 1).padStart(2, '0')
  const d = String(now.getDate()).padStart(2, '0')
  const weekDays = ['星期日', '星期一', '星期二', '星期三', '星期四', '星期五', '星期六']
  currentDate.value = `${y}-${mo}-${d} ${weekDays[now.getDay()]}`
}

// ==================== 粒子 ====================
const particleStyle = (i) => ({
  left: `${Math.random() * 100}%`,
  top: `${Math.random() * 100}%`,
  animationDelay: `${Math.random() * 6}s`,
  animationDuration: `${4 + Math.random() * 6}s`,
  width: `${2 + Math.random() * 3}px`,
  height: `${2 + Math.random() * 3}px`,
  opacity: 0.2 + Math.random() * 0.4
})

// ==================== 统计数据 ====================
const stats = ref({
  totalDevices: 0,
  highRiskCount: 0,
  mediumRiskCount: 0,
  lowRiskCount: 0,
  avgHealthScore: '0.00',
  avgRemainingLifeMonth: '0.00'
})

const loadStats = async () => {
  try {
    const res = await getPredictionStatistics()
    if (res) {
      stats.value = res
    }
  } catch (e) {
    console.error('加载统计数据失败:', e)
  }
}

// ==================== 表格 ====================
const query = ref({ page: 1, size: 10, predictionLevel: '' })
const tableData = ref([])
const total = ref(0)
const tableLoading = ref(false)

const loadData = async () => {
  tableLoading.value = true
  try {
    const params = { page: query.value.page, size: query.value.size }
    if (query.value.predictionLevel) {
      params.predictionLevel = query.value.predictionLevel
    }
    const res = await getPredictionList(params)
    tableData.value = res?.records || []
    total.value = res?.total || 0
  } catch (e) {
    ElMessage.error('加载预测列表失败')
    console.error('加载预测列表失败:', e)
  } finally {
    tableLoading.value = false
  }
}

const resetQuery = () => {
  query.value = { page: 1, size: 10, predictionLevel: '' }
  loadData()
}

// ==================== 生成预测 ====================
const generating = ref(false)
const generateResult = ref(null)

const handleGenerate = async () => {
  generating.value = true
  try {
    const res = await generatePrediction()
    generateResult.value = res
    if (res) {
      ElMessage.success('预测生成成功')
      loadData()
      loadStats()
      initPieChart()
    } else {
      ElMessage.warning('无预警事件数据，无法生成预测')
    }
  } catch (e) {
    ElMessage.error('生成预测失败')
    console.error('生成预测失败:', e)
  } finally {
    generating.value = false
  }
}

// ==================== ECharts ====================
const pieChartRef = ref(null)
let pieChart = null

const initPieChart = async () => {
  try {
    const res = await getPredictionList({ page: 1, size: 200 })
    const records = res?.records || []

    const levelCount = { LOW: 0, MEDIUM: 0, HIGH: 0, CRITICAL: 0 }
    records.forEach(item => {
      if (levelCount[item.predictionLevel] !== undefined) levelCount[item.predictionLevel]++
    })

    if (!pieChartRef.value) return
    if (pieChart) pieChart.dispose()
    pieChart = echarts.init(pieChartRef.value)

    const option = {
      backgroundColor: 'transparent',
      tooltip: {
        trigger: 'item',
        backgroundColor: 'rgba(13, 27, 42, 0.9)',
        borderColor: '#1890ff44',
        textStyle: { color: '#e0e6ed' },
        formatter: '{b}: {c}台 ({d}%)'
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
        {
          type: 'pie',
          radius: ['72%', '74%'],
          center: ['40%', '50%'],
          silent: true,
          label: { show: false },
          data: [{ value: 1, itemStyle: { color: 'rgba(24, 144, 255, 0.15)' } }]
        },
        {
          name: '风险等级',
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
            formatter: '{b}\n{c}台'
          },
          labelLine: { lineStyle: { color: '#2a3a4a' } },
          emphasis: {
            scaleSize: 8,
            itemStyle: { shadowBlur: 30, shadowColor: 'rgba(24, 144, 255, 0.5)' }
          },
          data: [
            { value: levelCount.LOW, name: '低风险', itemStyle: { color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [{ offset: 0, color: '#69c0ff' }, { offset: 1, color: '#1890ff' }]) } },
            { value: levelCount.MEDIUM, name: '中风险', itemStyle: { color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [{ offset: 0, color: '#ffe066' }, { offset: 1, color: '#fadb14' }]) } },
            { value: levelCount.HIGH, name: '高风险', itemStyle: { color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [{ offset: 0, color: '#ffc069' }, { offset: 1, color: '#fa8c16' }]) } },
            { value: levelCount.CRITICAL, name: '危急', itemStyle: { color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [{ offset: 0, color: '#ff7875' }, { offset: 1, color: '#ff4d4f' }]) } }
          ]
        },
        {
          type: 'pie',
          radius: ['0%', '0%'],
          center: ['40%', '50%'],
          label: {
            show: true,
            position: 'center',
            formatter: () => `{total|${stats.value.totalDevices}}\n{label|设备总数}`,
            rich: {
              total: { fontSize: 32, fontWeight: 700, color: '#e0e6ed', lineHeight: 40 },
              label: { fontSize: 12, color: '#8a9bb0', lineHeight: 20 }
            }
          },
          data: [{ value: 0 }]
        }
      ]
    }
    pieChart.setOption(option)
  } catch (e) {
    console.error('初始化饼图失败:', e)
  }
}

const handleResize = () => { pieChart?.resize() }

// ==================== 辅助方法 ====================
const levelText = (level) => {
  const map = { LOW: '低风险', MEDIUM: '中风险', HIGH: '高风险', CRITICAL: '危急' }
  return map[level] || level
}

const healthClass = (score) => {
  if (score >= 80) return 'value-good'
  if (score >= 60) return 'value-normal'
  if (score >= 40) return 'value-warn'
  return 'value-danger'
}

const riskClass = (score) => {
  if (score < 30) return 'value-good'
  if (score < 50) return 'value-normal'
  if (score < 70) return 'value-warn'
  return 'value-danger'
}

const probClass = (prob) => {
  if (prob < 20) return 'value-good'
  if (prob < 40) return 'value-normal'
  if (prob < 60) return 'value-warn'
  return 'value-danger'
}

const formatTime = (t) => {
  if (!t) return '-'
  return t.replace('T', ' ').substring(0, 19)
}

// ==================== 生命周期 ====================
onMounted(() => {
  updateClock()
  clockTimer = setInterval(updateClock, 1000)
  loadStats()
  loadData()
  initPieChart()
  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  clearInterval(clockTimer)
  window.removeEventListener('resize', handleResize)
  pieChart?.dispose()
})
</script>

<style scoped>
/* ==================== 容器 ==================== */
.prediction-container {
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
.page-header {
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

.header-left { flex: 1; }

.back-btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  color: #8a9bb0;
  font-size: 13px;
  cursor: pointer;
  transition: color 0.2s;
}
.back-btn:hover { color: #1890ff; }

.header-center {
  display: flex;
  align-items: center;
  gap: 24px;
  flex-shrink: 0;
}

.header-decor { display: flex; align-items: center; gap: 4px; }
.decor-line { display: block; width: 60px; height: 2px; background: linear-gradient(90deg, transparent, #1890ff); }
.right-decor .decor-line { background: linear-gradient(90deg, #1890ff, transparent); }
.decor-diamond { display: block; width: 8px; height: 8px; background: #1890ff; transform: rotate(45deg); box-shadow: 0 0 10px rgba(24, 144, 255, 0.6); }

.header-title-group { text-align: center; }
.header-title {
  font-size: 26px;
  font-weight: 700;
  margin: 0;
  letter-spacing: 6px;
  background: linear-gradient(90deg, #36cfe9, #1890ff, #36cfe9);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  filter: drop-shadow(0 0 12px rgba(24, 144, 255, 0.4));
}
.header-subtitle {
  font-size: 11px;
  color: #5a7a9a;
  margin: 6px 0 0 0;
  letter-spacing: 4px;
  text-transform: uppercase;
}

.header-right { flex: 1; text-align: right; }
.realtime-clock {
  font-size: 24px;
  font-weight: 700;
  color: #36cfe9;
  font-family: 'Courier New', monospace;
  letter-spacing: 2px;
  text-shadow: 0 0 10px rgba(54, 207, 233, 0.4);
}
.realtime-date { font-size: 12px; color: #5a7a9a; margin-top: 2px; }

/* ==================== 主体内容 ==================== */
.page-main {
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

.stat-card {
  position: relative;
  padding: 24px;
  border-radius: 16px;
  background: linear-gradient(135deg, rgba(27, 40, 56, 0.8), rgba(13, 27, 42, 0.9));
  border: 1px solid color-mix(in srgb, var(--card-color) 40%, transparent);
  backdrop-filter: blur(10px);
  overflow: hidden;
  transition: all 0.3s ease;
  cursor: pointer;
}

.stat-card:hover {
  transform: translateY(-4px);
  border-color: var(--card-color);
  box-shadow: 0 8px 32px color-mix(in srgb, var(--card-color) 30%, transparent);
}

.stat-card:hover .card-glow { opacity: 1; }

.card-glow {
  position: absolute;
  top: -50%; left: -50%;
  width: 200%; height: 200%;
  background: radial-gradient(circle, color-mix(in srgb, var(--card-color) 20%, transparent) 0%, transparent 70%);
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

.stat-info { flex: 1; }
.stat-value {
  font-size: 36px;
  font-weight: 700;
  line-height: 1.2;
  letter-spacing: -1px;
}
.stat-label {
  font-size: 13px;
  color: #8a9bb0;
  margin-top: 8px;
  letter-spacing: 1px;
}

.card-decoration {
  position: absolute;
  bottom: 0; left: 0; right: 0;
  height: 3px;
  background: linear-gradient(90deg, transparent, var(--card-color), transparent);
  opacity: 0.6;
}

/* ==================== 中间区域 ==================== */
.middle-section {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
  margin-bottom: 20px;
}

.chart-panel, .action-panel {
  background: linear-gradient(135deg, rgba(27, 40, 56, 0.7), rgba(13, 27, 42, 0.8));
  border-radius: 12px;
  padding: 20px;
  border: 1px solid rgba(42, 58, 74, 0.6);
  backdrop-filter: blur(8px);
  transition: all 0.3s ease;
}

.chart-panel:hover, .action-panel:hover {
  border-color: rgba(24, 144, 255, 0.3);
  box-shadow: 0 4px 24px rgba(24, 144, 255, 0.1);
}

.panel-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 16px;
}

.panel-icon { color: #1890ff; font-size: 10px; }
.panel-title { font-size: 15px; font-weight: 600; color: #e0e6ed; letter-spacing: 1px; }
.panel-badge {
  margin-left: auto;
  font-size: 12px;
  color: #1890ff;
  background: rgba(24, 144, 255, 0.1);
  padding: 2px 10px;
  border-radius: 10px;
  border: 1px solid rgba(24, 144, 255, 0.2);
}

.chart-container { height: 300px; width: 100%; }

/* ==================== 操作面板 ==================== */
.action-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 20px;
  padding: 20px 0;
}

.action-desc {
  color: #8a9bb0;
  font-size: 14px;
  text-align: center;
  line-height: 1.6;
  max-width: 360px;
}

.generate-btn {
  background: linear-gradient(135deg, #1890ff, #36cfe9) !important;
  border: none !important;
  font-size: 16px !important;
  padding: 12px 40px !important;
  height: auto !important;
  border-radius: 8px !important;
  letter-spacing: 2px;
  box-shadow: 0 4px 20px rgba(24, 144, 255, 0.4);
  transition: all 0.3s ease;
}

.generate-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 30px rgba(24, 144, 255, 0.6);
}

.generate-result {
  width: 100%;
  max-width: 360px;
  background: rgba(13, 27, 42, 0.6);
  border: 1px solid rgba(42, 58, 74, 0.6);
  border-radius: 10px;
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.result-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.result-label { color: #5a7a9a; font-size: 13px; }
.result-value { color: #e0e6ed; font-size: 14px; font-weight: 600; }

/* ==================== 表格区域 ==================== */
.table-section {
  background: linear-gradient(135deg, rgba(27, 40, 56, 0.7), rgba(13, 27, 42, 0.8));
  border-radius: 12px;
  padding: 20px;
  border: 1px solid rgba(42, 58, 74, 0.6);
  backdrop-filter: blur(8px);
}

.filter-bar {
  display: flex;
  gap: 12px;
  margin-bottom: 16px;
  align-items: center;
}

.filter-select {
  width: 160px;
}

.filter-btn {
  background: rgba(24, 144, 255, 0.1) !important;
  border: 1px solid rgba(24, 144, 255, 0.3) !important;
  color: #1890ff !important;
}

.filter-btn:hover {
  background: rgba(24, 144, 255, 0.2) !important;
}

/* Element Plus 表格深色适配 */
.prediction-table {
  --el-table-bg-color: transparent;
  --el-table-tr-bg-color: transparent;
  --el-table-header-bg-color: rgba(13, 27, 42, 0.8);
  --el-table-row-hover-bg-color: rgba(24, 144, 255, 0.06);
  --el-table-border-color: rgba(42, 58, 74, 0.4);
  --el-table-text-color: #e0e6ed;
  --el-table-header-text-color: #8a9bb0;
}

.pagination-bar {
  display: flex;
  justify-content: flex-end;
  margin-top: 16px;
}

.pagination-bar .el-pagination {
  --el-pagination-bg-color: transparent;
  --el-pagination-text-color: #8a9bb0;
  --el-pagination-button-bg-color: rgba(24, 144, 255, 0.1);
  --el-pagination-hover-color: #1890ff;
}

/* ==================== 值颜色 ==================== */
.value-good { color: #52c41a; font-weight: 700; }
.value-normal { color: #1890ff; font-weight: 700; }
.value-warn { color: #fa8c16; font-weight: 700; }
.value-danger { color: #ff4d4f; font-weight: 700; }

.life-value { color: #36cfe9; font-weight: 600; }

.time-cell { color: #5a7a9a; font-family: 'Courier New', monospace; font-size: 13px; }

/* ==================== 等级徽章 ==================== */
.level-badge {
  display: inline-block;
  padding: 2px 10px;
  border-radius: 10px;
  font-size: 12px;
  font-weight: 600;
  letter-spacing: 1px;
}

.level-low {
  background: rgba(24, 144, 255, 0.15);
  color: #1890ff;
  border: 1px solid rgba(24, 144, 255, 0.3);
}

.level-medium {
  background: rgba(250, 219, 20, 0.15);
  color: #fadb14;
  border: 1px solid rgba(250, 219, 20, 0.3);
}

.level-high {
  background: rgba(250, 140, 22, 0.15);
  color: #fa8c16;
  border: 1px solid rgba(250, 140, 22, 0.3);
}

.level-critical {
  background: rgba(255, 77, 79, 0.15);
  color: #ff4d4f;
  border: 1px solid rgba(255, 77, 79, 0.3);
  animation: criticalPulse 2s ease-in-out infinite;
}

@keyframes criticalPulse {
  0%, 100% { box-shadow: 0 0 4px rgba(255, 77, 79, 0.3); }
  50% { box-shadow: 0 0 12px rgba(255, 77, 79, 0.6); }
}

/* ==================== Element Plus 深色覆盖 ==================== */
:deep(.el-select .el-input__wrapper) {
  background: rgba(13, 27, 42, 0.6) !important;
  border-color: rgba(42, 58, 74, 0.6) !important;
  box-shadow: none !important;
}

:deep(.el-select .el-input__inner) {
  color: #e0e6ed !important;
}

:deep(.el-select .el-input__inner::placeholder) {
  color: #5a6f86 !important;
}

:deep(.el-pagination button),
:deep(.el-pagination .el-pager li) {
  background: rgba(13, 27, 42, 0.6) !important;
  color: #8a9bb0 !important;
  border: 1px solid rgba(42, 58, 74, 0.4) !important;
}

:deep(.el-pagination .el-pager li.is-active) {
  background: rgba(24, 144, 255, 0.2) !important;
  color: #1890ff !important;
  border-color: rgba(24, 144, 255, 0.4) !important;
}

:deep(.el-table .el-loading-mask) {
  background: rgba(13, 27, 42, 0.5) !important;
}

/* ==================== 适配 ==================== */
@media (max-width: 1400px) {
  .middle-section { grid-template-columns: 1fr 1fr; }
}

@media (max-width: 1024px) {
  .stat-section { grid-template-columns: repeat(2, 1fr); }
  .middle-section { grid-template-columns: 1fr; }
}
</style>
