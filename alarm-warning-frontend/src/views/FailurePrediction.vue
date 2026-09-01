<template>
  <div class="prediction">
    <!-- 页头 -->
    <PageHeader
      title="故障预报与寿命预测"
      subtitle="基于设备健康评估与剩余寿命分析"
    />

    <!-- 统计卡片 -->
    <section class="prediction__stats">
      <StatCard label="设备总数" :value="stats.totalDevices" icon="Monitor" color="#2979FF" />
      <StatCard label="高风险设备" :value="stats.highRiskCount" icon="WarningFilled" color="#F5222D" />
      <StatCard label="平均健康度" :value="stats.avgHealthScore" icon="CircleCheck" color="#52C41A" />
      <StatCard label="平均剩余寿命(月)" :value="stats.avgRemainingLifeMonth" icon="Timer" color="#FA8C16" />
    </section>

    <!-- 网格：环形图 + 预测操作面板 -->
    <section class="prediction__grid">
      <div class="app-card prediction__chart-card">
        <div class="card-title">
          <span class="card-title__text">风险等级分布</span>
          <span class="card-title__badge">{{ stats.totalDevices }} 台</span>
        </div>
        <div ref="pieChartRef" class="prediction__chart"></div>
      </div>

      <div class="app-card prediction__action-card">
        <div class="card-title">
          <span class="card-title__text">预测操作</span>
        </div>
        <div class="prediction__action">
          <p class="prediction__action-desc">
            基于当前预警事件数据，对所有设备进行健康评估、故障概率计算和剩余寿命预测。
          </p>
          <el-button
            type="primary"
            size="large"
            :loading="generating"
            @click="handleGenerate"
          >
            <el-icon><Cpu /></el-icon>
            生成预测
          </el-button>

          <div v-if="generateResult" class="prediction__result">
            <div class="result-row">
              <span class="result-label">设备ID</span>
              <span class="result-value">{{ generateResult.deviceId }}</span>
            </div>
            <div class="result-row">
              <span class="result-label">健康度</span>
              <span class="result-value">{{ generateResult.healthScore }}</span>
            </div>
            <div class="result-row">
              <span class="result-label">故障概率</span>
              <span class="result-value">{{ generateResult.failureProbability }}%</span>
            </div>
            <div class="result-row">
              <span class="result-label">剩余寿命</span>
              <span class="result-value">{{ generateResult.remainingLifeMonth }} 月</span>
            </div>
            <div class="result-row">
              <span class="result-label">预测等级</span>
              <span
                class="level-tag"
                :class="'level-tag--' + (generateResult.predictionLevel || '').toLowerCase()"
              >
                {{ levelText(generateResult.predictionLevel) }}
              </span>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- 预测记录列表 -->
    <section class="app-card prediction__table-card">
      <div class="card-title">
        <span class="card-title__text">预测记录列表</span>
        <span class="card-title__badge">{{ total }} 条</span>
      </div>

      <!-- 筛选栏 -->
      <div class="filter-bar prediction__filter">
        <el-select
          v-model="query.predictionLevel"
          placeholder="预测等级"
          clearable
          class="prediction__filter-item"
        >
          <el-option label="全部" value="" />
          <el-option label="低风险" value="LOW" />
          <el-option label="中风险" value="MEDIUM" />
          <el-option label="高风险" value="HIGH" />
          <el-option label="危急" value="CRITICAL" />
        </el-select>
        <el-button type="primary" @click="loadData">
          <el-icon><Search /></el-icon> 查询
        </el-button>
        <el-button @click="resetQuery">重置</el-button>
      </div>

      <!-- 表格 -->
      <el-table :data="tableData" v-loading="tableLoading" class="app-table">
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
            <span
              class="level-tag"
              :class="'level-tag--' + (row.predictionLevel || '').toLowerCase()"
            >
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
      <div class="prediction__pagination">
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
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Cpu, Search } from '@element-plus/icons-vue'
import PageHeader from '@/components/PageHeader.vue'
import StatCard from '@/components/StatCard.vue'
import { useEChart } from '@/utils/chart.js'
import {
  getPredictionList,
  generatePrediction,
  getPredictionStatistics
} from '@/api/failurePrediction'

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
    if (res) stats.value = res
  } catch (e) {
    console.error('加载统计数据失败:', e)
  }
}

// ==================== 表格 + 分页 ====================
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
      renderPieChart()
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

// ==================== ECharts 环形图 ====================
const pieChartRef = ref(null)
const { setOption } = useEChart(pieChartRef)

// 渲染环形图：拉取全量数据按等级聚合
const renderPieChart = async () => {
  try {
    const res = await getPredictionList({ page: 1, size: 200 })
    const records = res?.records || []
    const levelCount = { LOW: 0, MEDIUM: 0, HIGH: 0, CRITICAL: 0 }
    records.forEach(item => {
      if (levelCount[item.predictionLevel] !== undefined) {
        levelCount[item.predictionLevel]++
      }
    })

    setOption({
      tooltip: {
        trigger: 'item',
        formatter: '{b}: {c}台 ({d}%)'
      },
      legend: {
        orient: 'vertical',
        right: 16,
        top: 'center',
        itemWidth: 12,
        itemHeight: 12,
        itemGap: 16,
        textStyle: { fontSize: 12 }
      },
      series: [
        {
          name: '风险等级',
          type: 'pie',
          radius: ['45%', '70%'],
          center: ['40%', '50%'],
          avoidLabelOverlap: false,
          startAngle: 90,
          itemStyle: {
            borderRadius: 6,
            borderWidth: 3,
            borderColor: '#ffffff'
          },
          label: {
            show: true,
            position: 'outside',
            fontSize: 12,
            formatter: '{b}\n{c}台'
          },
          emphasis: {
            scaleSize: 6
          },
          data: [
            { value: levelCount.LOW, name: '低风险', itemStyle: { color: '#2979FF' } },
            { value: levelCount.MEDIUM, name: '中风险', itemStyle: { color: '#FADB14' } },
            { value: levelCount.HIGH, name: '高风险', itemStyle: { color: '#FA8C16' } },
            { value: levelCount.CRITICAL, name: '危急', itemStyle: { color: '#F5222D' } }
          ]
        },
        {
          type: 'pie',
          radius: ['0%', '0%'],
          center: ['40%', '50%'],
          silent: true,
          label: {
            show: true,
            position: 'center',
            formatter: () => `{total|${stats.value.totalDevices}}\n{label|设备总数}`,
            rich: {
              total: { fontSize: 30, fontWeight: 700, color: '#1D2129', lineHeight: 38 },
              label: { fontSize: 12, color: '#86909C', lineHeight: 20 }
            }
          },
          data: [{ value: 0 }]
        }
      ]
    })
  } catch (e) {
    console.error('渲染饼图失败:', e)
  }
}

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
  return String(t).replace('T', ' ').substring(0, 19)
}

// ==================== 生命周期 ====================
onMounted(() => {
  loadStats()
  loadData()
  renderPieChart()
})
</script>

<style scoped>
/* 统计卡片网格 */
.prediction__stats {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
  margin-bottom: 16px;
}

/* 中间网格：环形图 + 操作面板 */
.prediction__grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
  margin-bottom: 16px;
}

.prediction__chart-card,
.prediction__action-card,
.prediction__table-card {
  padding: 16px 20px;
}

/* 卡片标题 */
.card-title {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 16px;
}
.card-title__text {
  font-size: 15px;
  font-weight: 600;
  color: var(--app-text-1);
}
.card-title__badge {
  margin-left: auto;
  padding: 2px 10px;
  font-size: 12px;
  color: var(--app-primary);
  background-color: rgba(41, 121, 255, 0.08);
  border-radius: 10px;
}

/* 环形图容器 */
.prediction__chart {
  height: 300px;
  width: 100%;
}

/* 操作面板 */
.prediction__action {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16px;
  padding: 12px 0 4px;
}
.prediction__action-desc {
  margin: 0;
  font-size: 14px;
  color: var(--app-text-3);
  text-align: center;
  line-height: 1.6;
  max-width: 360px;
}

/* 生成结果展示 */
.prediction__result {
  width: 100%;
  max-width: 360px;
  padding: 14px 16px;
  background-color: var(--app-bg);
  border-radius: 8px;
  border: 1px solid var(--app-border-light);
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.result-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.result-label {
  font-size: 13px;
  color: var(--app-text-3);
}
.result-value {
  font-size: 14px;
  font-weight: 600;
  color: var(--app-text-1);
}

/* 筛选栏 */
.prediction__filter {
  margin-bottom: 16px;
}
.prediction__filter-item {
  width: 160px;
}

/* 分页 */
.prediction__pagination {
  display: flex;
  justify-content: flex-end;
  margin-top: 16px;
}

/* 值颜色 */
.value-good { color: #52C41A; font-weight: 600; }
.value-normal { color: #2979FF; font-weight: 600; }
.value-warn { color: #FA8C16; font-weight: 600; }
.value-danger { color: #F5222D; font-weight: 600; }

.life-value { color: var(--app-primary); font-weight: 600; }
.time-cell {
  color: var(--app-text-3);
  font-family: 'Courier New', monospace;
  font-size: 13px;
}

/* 等级标签 */
.level-tag {
  display: inline-block;
  padding: 2px 10px;
  border-radius: 10px;
  font-size: 12px;
  font-weight: 600;
}
.level-tag--low {
  color: #2979FF;
  background-color: rgba(41, 121, 255, 0.1);
}
.level-tag--medium {
  color: #C9A227;
  background-color: rgba(250, 219, 20, 0.15);
}
.level-tag--high {
  color: #FA8C16;
  background-color: rgba(250, 140, 22, 0.1);
}
.level-tag--critical {
  color: #F5222D;
  background-color: rgba(245, 34, 45, 0.1);
}

/* 响应式 */
@media (max-width: 1024px) {
  .prediction__stats { grid-template-columns: repeat(2, 1fr); }
  .prediction__grid { grid-template-columns: 1fr; }
}
</style>
