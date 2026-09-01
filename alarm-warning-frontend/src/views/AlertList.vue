<template>
  <div class="alert-list-container">
    <div class="bg-particles">
      <div v-for="i in 20" :key="i" class="particle" :style="particleStyle(i)"></div>
    </div>

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
          <h1 class="header-title">预警事件列表</h1>
          <p class="header-subtitle">ALERT EVENT LIST</p>
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

    <main class="page-main">
      <section class="stat-section">
        <div class="stat-card" style="--card-color: #1890ff;">
          <div class="card-glow"></div>
          <div class="card-content">
            <div class="stat-icon" style="background: linear-gradient(135deg, #1890ff33, #1890ff11); color: #1890ff;">
              <el-icon :size="32"><Bell /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value" style="background: linear-gradient(135deg, #1890ff, #fff); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">{{ stats.total }}</div>
              <div class="stat-label">预警总数</div>
            </div>
          </div>
          <div class="card-decoration"></div>
        </div>

        <div class="stat-card" style="--card-color: #fa8c16;">
          <div class="card-glow"></div>
          <div class="card-content">
            <div class="stat-icon" style="background: linear-gradient(135deg, #fa8c1633, #fa8c1611); color: #fa8c16;">
              <el-icon :size="32"><Clock /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value" style="background: linear-gradient(135deg, #fa8c16, #fff); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">{{ stats.open }}</div>
              <div class="stat-label">待处理</div>
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
              <div class="stat-value" style="background: linear-gradient(135deg, #ff4d4f, #fff); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">{{ stats.red }}</div>
              <div class="stat-label">红色预警</div>
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
              <div class="stat-value" style="background: linear-gradient(135deg, #52c41a, #fff); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">{{ stats.resolved }}</div>
              <div class="stat-label">已解决</div>
            </div>
          </div>
          <div class="card-decoration"></div>
        </div>
      </section>

      <section class="table-section">
        <div class="panel-header">
          <span class="panel-icon">&#9670;</span>
          <span class="panel-title">预警事件</span>
          <span class="panel-badge">{{ total }} 条</span>
        </div>

        <div class="filter-bar">
          <el-select v-model="query.alertLevel" placeholder="预警等级" clearable class="filter-select">
            <el-option label="全部等级" value="" />
            <el-option label="蓝色预警" value="BLUE" />
            <el-option label="黄色预警" value="YELLOW" />
            <el-option label="橙色预警" value="ORANGE" />
            <el-option label="红色预警" value="RED" />
          </el-select>
          <el-select v-model="query.alertStatus" placeholder="处理状态" clearable class="filter-select">
            <el-option label="全部状态" value="" />
            <el-option label="待处理" value="OPEN" />
            <el-option label="已确认" value="ACKNOWLEDGED" />
            <el-option label="已解决" value="RESOLVED" />
            <el-option label="已关闭" value="CLOSED" />
          </el-select>
          <el-input v-model="query.deviceType" placeholder="设备类型" clearable class="filter-input" />
          <el-button type="primary" @click="loadData" class="filter-btn">
            <el-icon><Search /></el-icon> 查询
          </el-button>
          <el-button @click="resetQuery" class="filter-btn">重置</el-button>
        </div>

        <el-table
          :data="tableData"
          v-loading="tableLoading"
          element-loading-background="rgba(0,0,0,0.3)"
          class="alert-table"
          :header-cell-style="{ background: 'rgba(13, 27, 42, 0.8)', color: '#8a9bb0', borderColor: 'rgba(42, 58, 74, 0.6)' }"
          :cell-style="{ background: 'rgba(13, 27, 42, 0.4)', color: '#e0e6ed', borderColor: 'rgba(42, 58, 74, 0.4)' }"
          @row-click="goDetail"
          row-class-name="clickable-row"
        >
          <el-table-column prop="alertEventCode" label="预警编码" min-width="180">
            <template #default="{ row }">
              <span class="code-cell">{{ row.alertEventCode }}</span>
            </template>
          </el-table-column>
          <el-table-column label="等级" width="110" align="center">
            <template #default="{ row }">
              <AlertLevelTag :level="row.alertLevel" />
            </template>
          </el-table-column>
          <el-table-column prop="deviceType" label="设备类型" width="120" />
          <el-table-column prop="deviceId" label="设备ID" min-width="140" />
          <el-table-column prop="areaId" label="区域" width="120" />
          <el-table-column prop="metricKey" label="指标" width="120" />
          <el-table-column label="指标值 / 阈值" width="150" align="center">
            <template #default="{ row }">
              <span class="metric-cell">
                <span class="metric-value">{{ row.metricValue }}</span>
                <span class="metric-sep">/</span>
                <span class="metric-threshold">{{ row.thresholdValue }}</span>
              </span>
            </template>
          </el-table-column>
          <el-table-column label="状态" width="110" align="center">
            <template #default="{ row }">
              <AlertStatusTag :status="row.alertStatus" />
            </template>
          </el-table-column>
          <el-table-column label="优先级" width="90" align="center">
            <template #default="{ row }">
              <span class="priority-value">{{ row.priorityScore }}</span>
            </template>
          </el-table-column>
          <el-table-column label="事件时间" width="170">
            <template #default="{ row }">
              <span class="time-cell">{{ formatDateTime(row.eventTimestamp) }}</span>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="160" align="center" fixed="right">
            <template #default="{ row }">
              <el-button link type="primary" size="small" @click.stop="goDetail(row)">详情</el-button>
              <el-button
                v-if="row.alertStatus === 'OPEN'"
                link type="warning" size="small"
                @click.stop="handleConfirm(row)"
              >确认</el-button>
              <el-button
                v-if="row.alertStatus === 'ACKNOWLEDGED'"
                link type="success" size="small"
                @click.stop="handleResolve(row)"
              >解决</el-button>
            </template>
          </el-table-column>
        </el-table>

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
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { ArrowLeft, Bell, Clock, Warning, CircleCheck, Search } from '@element-plus/icons-vue'
import AlertLevelTag from '@/components/AlertLevelTag.vue'
import AlertStatusTag from '@/components/AlertStatusTag.vue'
import { getAlertList, updateAlertStatus } from '@/api/alert'
import { formatDateTime } from '@/utils/format'

const router = useRouter()

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

const particleStyle = (i) => ({
  left: `${Math.random() * 100}%`,
  top: `${Math.random() * 100}%`,
  animationDelay: `${Math.random() * 6}s`,
  animationDuration: `${4 + Math.random() * 6}s`,
  width: `${2 + Math.random() * 3}px`,
  height: `${2 + Math.random() * 3}px`,
  opacity: 0.2 + Math.random() * 0.4
})

const stats = ref({ total: 0, open: 0, red: 0, resolved: 0 })

const loadStats = async () => {
  try {
    const [totalRes, openRes, redRes, resolvedRes] = await Promise.all([
      getAlertList({ page: 1, size: 1 }),
      getAlertList({ status: 'OPEN', page: 1, size: 1 }),
      getAlertList({ alertLevel: 'RED', page: 1, size: 1 }),
      getAlertList({ status: 'RESOLVED', page: 1, size: 1 })
    ])
    stats.value = {
      total: totalRes?.total || 0,
      open: openRes?.total || 0,
      red: redRes?.total || 0,
      resolved: resolvedRes?.total || 0
    }
  } catch (e) {
    console.error('加载统计数据失败:', e)
  }
}

const query = ref({ page: 1, size: 10, alertLevel: '', alertStatus: '', deviceType: '' })
const tableData = ref([])
const total = ref(0)
const tableLoading = ref(false)

const loadData = async () => {
  tableLoading.value = true
  try {
    const params = { page: query.value.page, size: query.value.size }
    if (query.value.alertLevel) params.alertLevel = query.value.alertLevel
    if (query.value.alertStatus) params.status = query.value.alertStatus
    if (query.value.deviceType) params.deviceType = query.value.deviceType
    const res = await getAlertList(params)
    tableData.value = res?.records || []
    total.value = res?.total || 0
  } catch (e) {
    ElMessage.error('加载预警列表失败')
    console.error('加载预警列表失败:', e)
  } finally {
    tableLoading.value = false
  }
}

const resetQuery = () => {
  query.value = { page: 1, size: 10, alertLevel: '', alertStatus: '', deviceType: '' }
  loadData()
}

const goDetail = (row) => {
  router.push(`/alerts/${row.id}`)
}

const handleConfirm = async (row) => {
  try {
    await updateAlertStatus(row.id, 'ACKNOWLEDGED')
    ElMessage.success('已确认')
    loadData()
    loadStats()
  } catch (e) {
    ElMessage.error('操作失败')
  }
}

const handleResolve = async (row) => {
  try {
    await updateAlertStatus(row.id, 'RESOLVED')
    ElMessage.success('已解决')
    loadData()
    loadStats()
  } catch (e) {
    ElMessage.error('操作失败')
  }
}

onMounted(() => {
  updateClock()
  clockTimer = setInterval(updateClock, 1000)
  loadStats()
  loadData()
})

onUnmounted(() => {
  clearInterval(clockTimer)
})
</script>

<style scoped>
.alert-list-container {
  min-height: 100vh;
  position: relative;
  overflow: hidden;
}

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

.page-main {
  position: relative;
  z-index: 1;
  padding: 20px 40px;
}

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

.table-section {
  background: linear-gradient(135deg, rgba(27, 40, 56, 0.7), rgba(13, 27, 42, 0.8));
  border-radius: 12px;
  padding: 20px;
  border: 1px solid rgba(42, 58, 74, 0.6);
  backdrop-filter: blur(8px);
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

.filter-bar {
  display: flex;
  gap: 12px;
  margin-bottom: 16px;
  align-items: center;
}

.filter-select { width: 160px; }
.filter-input { width: 160px; }

.filter-btn {
  background: rgba(24, 144, 255, 0.1) !important;
  border: 1px solid rgba(24, 144, 255, 0.3) !important;
  color: #1890ff !important;
}
.filter-btn:hover {
  background: rgba(24, 144, 255, 0.2) !important;
}

.alert-table {
  --el-table-bg-color: transparent;
  --el-table-tr-bg-color: transparent;
  --el-table-header-bg-color: rgba(13, 27, 42, 0.8);
  --el-table-row-hover-bg-color: rgba(24, 144, 255, 0.06);
  --el-table-border-color: rgba(42, 58, 74, 0.4);
  --el-table-text-color: #e0e6ed;
  --el-table-header-text-color: #8a9bb0;
}

:deep(.clickable-row) {
  cursor: pointer;
}

.code-cell {
  font-family: 'Courier New', monospace;
  font-size: 13px;
  color: #36cfe9;
}

.metric-cell { font-size: 13px; }
.metric-value { color: #ff7875; font-weight: 600; }
.metric-sep { color: #5a6f86; margin: 0 4px; }
.metric-threshold { color: #8a9bb0; }

.priority-value {
  font-weight: 700;
  color: #36cfe9;
  font-size: 15px;
}

.time-cell { color: #5a7a9a; font-family: 'Courier New', monospace; font-size: 13px; }

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

:deep(.el-select .el-input__wrapper) {
  background: rgba(13, 27, 42, 0.6) !important;
  border-color: rgba(42, 58, 74, 0.6) !important;
  box-shadow: none !important;
}
:deep(.el-select .el-input__inner) { color: #e0e6ed !important; }
:deep(.el-select .el-input__inner::placeholder) { color: #5a6f86 !important; }

:deep(.el-input__wrapper) {
  background: rgba(13, 27, 42, 0.6) !important;
  border-color: rgba(42, 58, 74, 0.6) !important;
  box-shadow: none !important;
}
:deep(.el-input__inner) { color: #e0e6ed !important; }

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

@media (max-width: 1024px) {
  .stat-section { grid-template-columns: repeat(2, 1fr); }
}
</style>
