<template>
  <div class="alert-detail-container">
    <div class="bg-particles">
      <div v-for="i in 20" :key="i" class="particle" :style="particleStyle(i)"></div>
    </div>

    <header class="page-header">
      <div class="header-left">
        <span class="back-btn" @click="$router.push('/alerts')">
          <el-icon><ArrowLeft /></el-icon> 返回列表
        </span>
      </div>
      <div class="header-center">
        <div class="header-decor left-decor">
          <span class="decor-line"></span>
          <span class="decor-diamond"></span>
          <span class="decor-line"></span>
        </div>
        <div class="header-title-group">
          <h1 class="header-title">预警事件详情</h1>
          <p class="header-subtitle">ALERT EVENT DETAIL</p>
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

    <main class="page-main" v-loading="loading" element-loading-background="rgba(0,0,0,0.3)">
      <template v-if="detail">
        <!-- 顶部状态卡片 -->
        <section class="status-section">
          <div class="status-card" :class="'level-' + (detail.alertLevel || '').toLowerCase()">
            <div class="card-glow"></div>
            <div class="card-content">
              <div class="level-indicator">
                <div class="level-ring">
                  <span class="level-text">{{ levelShort(detail.alertLevel) }}</span>
                </div>
              </div>
              <div class="status-info">
                <div class="status-code">{{ detail.alertEventCode }}</div>
                <div class="status-row">
                  <AlertLevelTag :level="detail.alertLevel" />
                  <AlertStatusTag :status="detail.alertStatus" />
                </div>
                <div class="status-device">{{ detail.deviceType }} - {{ detail.deviceId }}</div>
              </div>
            </div>
            <div class="card-decoration"></div>
          </div>

          <div class="action-card">
            <div class="panel-header">
              <span class="panel-icon">&#9670;</span>
              <span class="panel-title">状态操作</span>
            </div>
            <div class="action-buttons">
              <el-button
                v-if="detail.alertStatus === 'OPEN'"
                type="warning"
                @click="handleStatus('ACKNOWLEDGED')"
                :loading="statusUpdating"
                class="action-btn"
              >
                <el-icon><Check /></el-icon> 确认
              </el-button>
              <el-button
                v-if="detail.alertStatus === 'ACKNOWLEDGED'"
                type="success"
                @click="handleStatus('RESOLVED')"
                :loading="statusUpdating"
                class="action-btn"
              >
                <el-icon><CircleCheck /></el-icon> 解决
              </el-button>
              <el-button
                v-if="detail.alertStatus !== 'CLOSED'"
                type="info"
                @click="handleStatus('CLOSED')"
                :loading="statusUpdating"
                class="action-btn"
              >
                <el-icon><Close /></el-icon> 关闭
              </el-button>
              <div v-if="detail.alertStatus === 'CLOSED'" class="closed-hint">
                该事件已关闭
              </div>
            </div>
          </div>
        </section>

        <!-- 详细信息 -->
        <section class="detail-section">
          <div class="detail-panel">
            <div class="panel-header">
              <span class="panel-icon">&#9670;</span>
              <span class="panel-title">基本信息</span>
            </div>
            <div class="info-grid">
              <div class="info-item">
                <span class="info-label">预警编码</span>
                <span class="info-value code">{{ detail.alertEventCode }}</span>
              </div>
              <div class="info-item">
                <span class="info-label">数据来源</span>
                <span class="info-value">{{ detail.source }}</span>
              </div>
              <div class="info-item">
                <span class="info-label">关联事件ID</span>
                <span class="info-value code">{{ detail.sourceEventId || '-' }}</span>
              </div>
              <div class="info-item">
                <span class="info-label">设备ID</span>
                <span class="info-value">{{ detail.deviceId }}</span>
              </div>
              <div class="info-item">
                <span class="info-label">设备类型</span>
                <span class="info-value">{{ detail.deviceType }}</span>
              </div>
              <div class="info-item">
                <span class="info-label">管廊区段</span>
                <span class="info-value">{{ detail.zone }}</span>
              </div>
              <div class="info-item">
                <span class="info-label">区域ID</span>
                <span class="info-value">{{ detail.areaId }}</span>
              </div>
              <div class="info-item">
                <span class="info-label">事件时间</span>
                <span class="info-value time">{{ formatDateTime(detail.eventTimestamp) }}</span>
              </div>
            </div>
          </div>

          <div class="detail-panel">
            <div class="panel-header">
              <span class="panel-icon">&#9670;</span>
              <span class="panel-title">监测数据</span>
            </div>
            <div class="info-grid">
              <div class="info-item">
                <span class="info-label">监测指标</span>
                <span class="info-value">{{ detail.metricKey }}</span>
              </div>
              <div class="info-item">
                <span class="info-label">当前值</span>
                <span class="info-value highlight">{{ detail.metricValue }}</span>
              </div>
              <div class="info-item">
                <span class="info-label">阈值</span>
                <span class="info-value">{{ detail.thresholdValue }}</span>
              </div>
              <div class="info-item">
                <span class="info-label">优先级评分</span>
                <span class="info-value priority">{{ detail.priorityScore }}</span>
              </div>
            </div>
          </div>

          <div class="detail-panel full-width" v-if="detail.rootCause || detail.rootCauseDesc">
            <div class="panel-header">
              <span class="panel-icon">&#9670;</span>
              <span class="panel-title">原因分析</span>
            </div>
            <div class="cause-content">
              <div class="info-item" v-if="detail.rootCause">
                <span class="info-label">根因类型</span>
                <span class="info-value">{{ detail.rootCause }}</span>
              </div>
              <div class="info-item" v-if="detail.rootCauseDesc">
                <span class="info-label">详细描述</span>
                <span class="info-value desc">{{ detail.rootCauseDesc }}</span>
              </div>
            </div>
          </div>

          <div class="detail-panel" v-if="detail.alertGroupId">
            <div class="panel-header">
              <span class="panel-icon">&#9670;</span>
              <span class="panel-title">关联信息</span>
            </div>
            <div class="info-grid">
              <div class="info-item">
                <span class="info-label">预警组ID</span>
                <span class="info-value code">{{ detail.alertGroupId }}</span>
              </div>
              <div class="info-item">
                <span class="info-label">合并次数</span>
                <span class="info-value">{{ detail.mergedCount }}</span>
              </div>
            </div>
          </div>
        </section>
      </template>

      <div v-if="!loading && !detail" class="empty-state">
        <el-icon :size="48"><Warning /></el-icon>
        <p>预警事件不存在或加载失败</p>
        <el-button type="primary" @click="$router.push('/alerts')" class="back-list-btn">返回列表</el-button>
      </div>
    </main>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { ArrowLeft, Warning, Check, CircleCheck, Close } from '@element-plus/icons-vue'
import AlertLevelTag from '@/components/AlertLevelTag.vue'
import AlertStatusTag from '@/components/AlertStatusTag.vue'
import { getAlertDetail, updateAlertStatus } from '@/api/alert'
import { formatDateTime } from '@/utils/format'

const route = useRoute()
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

const loading = ref(false)
const detail = ref(null)
const statusUpdating = ref(false)

const loadDetail = async () => {
  const id = route.params.id
  if (!id) return
  loading.value = true
  try {
    detail.value = await getAlertDetail(id)
  } catch (e) {
    ElMessage.error('加载预警详情失败')
    console.error('加载预警详情失败:', e)
  } finally {
    loading.value = false
  }
}

const handleStatus = async (status) => {
  statusUpdating.value = true
  try {
    await updateAlertStatus(route.params.id, status)
    ElMessage.success('状态更新成功')
    loadDetail()
  } catch (e) {
    ElMessage.error('状态更新失败')
  } finally {
    statusUpdating.value = false
  }
}

const levelShort = (level) => {
  const map = { BLUE: '蓝', YELLOW: '黄', ORANGE: '橙', RED: '红' }
  return map[level] || level
}

onMounted(() => {
  updateClock()
  clockTimer = setInterval(updateClock, 1000)
  loadDetail()
})

onUnmounted(() => {
  clearInterval(clockTimer)
})
</script>

<style scoped>
.alert-detail-container {
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

/* 顶部状态区 */
.status-section {
  display: grid;
  grid-template-columns: 2fr 1fr;
  gap: 20px;
  margin-bottom: 20px;
}

.status-card {
  position: relative;
  padding: 28px 32px;
  border-radius: 16px;
  background: linear-gradient(135deg, rgba(27, 40, 56, 0.8), rgba(13, 27, 42, 0.9));
  border: 1px solid rgba(42, 58, 74, 0.6);
  backdrop-filter: blur(10px);
  overflow: hidden;
}

.level-red { border-color: rgba(255, 77, 79, 0.4); }
.level-orange { border-color: rgba(250, 140, 22, 0.4); }
.level-yellow { border-color: rgba(250, 219, 20, 0.4); }
.level-blue { border-color: rgba(24, 144, 255, 0.4); }

.card-glow {
  position: absolute;
  top: -50%; left: -50%;
  width: 200%; height: 200%;
  opacity: 0.5;
  pointer-events: none;
}

.level-red .card-glow { background: radial-gradient(circle, rgba(255, 77, 79, 0.08) 0%, transparent 70%); }
.level-orange .card-glow { background: radial-gradient(circle, rgba(250, 140, 22, 0.08) 0%, transparent 70%); }
.level-yellow .card-glow { background: radial-gradient(circle, rgba(250, 219, 20, 0.08) 0%, transparent 70%); }
.level-blue .card-glow { background: radial-gradient(circle, rgba(24, 144, 255, 0.08) 0%, transparent 70%); }

.card-content {
  position: relative;
  display: flex;
  align-items: center;
  gap: 24px;
  z-index: 1;
}

.level-indicator { flex-shrink: 0; }

.level-ring {
  width: 80px;
  height: 80px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  border: 3px solid;
}

.level-red .level-ring { border-color: #ff4d4f; box-shadow: 0 0 20px rgba(255, 77, 79, 0.4); }
.level-orange .level-ring { border-color: #fa8c16; box-shadow: 0 0 20px rgba(250, 140, 22, 0.4); }
.level-yellow .level-ring { border-color: #fadb14; box-shadow: 0 0 20px rgba(250, 219, 20, 0.4); }
.level-blue .level-ring { border-color: #1890ff; box-shadow: 0 0 20px rgba(24, 144, 255, 0.4); }

.level-text {
  font-size: 24px;
  font-weight: 700;
}

.level-red .level-text { color: #ff4d4f; }
.level-orange .level-text { color: #fa8c16; }
.level-yellow .level-text { color: #fadb14; }
.level-blue .level-text { color: #1890ff; }

.status-info { flex: 1; }

.status-code {
  font-family: 'Courier New', monospace;
  font-size: 18px;
  color: #e0e6ed;
  font-weight: 600;
  margin-bottom: 10px;
}

.status-row {
  display: flex;
  gap: 12px;
  margin-bottom: 10px;
}

.status-device {
  font-size: 14px;
  color: #8a9bb0;
}

.card-decoration {
  position: absolute;
  bottom: 0; left: 0; right: 0;
  height: 3px;
}

.level-red .card-decoration { background: linear-gradient(90deg, transparent, #ff4d4f, transparent); }
.level-orange .card-decoration { background: linear-gradient(90deg, transparent, #fa8c16, transparent); }
.level-yellow .card-decoration { background: linear-gradient(90deg, transparent, #fadb14, transparent); }
.level-blue .card-decoration { background: linear-gradient(90deg, transparent, #1890ff, transparent); }

.action-card {
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

.action-buttons {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.action-btn {
  width: 100%;
  height: 44px !important;
  font-size: 15px !important;
  border-radius: 8px !important;
  letter-spacing: 2px;
}

.closed-hint {
  text-align: center;
  color: #5a6f86;
  font-size: 14px;
  padding: 20px 0;
}

/* 详细信息区 */
.detail-section {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
}

.detail-panel {
  background: linear-gradient(135deg, rgba(27, 40, 56, 0.7), rgba(13, 27, 42, 0.8));
  border-radius: 12px;
  padding: 20px;
  border: 1px solid rgba(42, 58, 74, 0.6);
  backdrop-filter: blur(8px);
  transition: all 0.3s ease;
}

.detail-panel:hover {
  border-color: rgba(24, 144, 255, 0.3);
  box-shadow: 0 4px 24px rgba(24, 144, 255, 0.1);
}

.detail-panel.full-width {
  grid-column: 1 / -1;
}

.info-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
}

.info-item {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.info-label {
  font-size: 12px;
  color: #5a7a9a;
  letter-spacing: 1px;
  text-transform: uppercase;
}

.info-value {
  font-size: 15px;
  color: #e0e6ed;
  font-weight: 500;
}

.info-value.code {
  font-family: 'Courier New', monospace;
  color: #36cfe9;
}

.info-value.time {
  font-family: 'Courier New', monospace;
  color: #8a9bb0;
  font-size: 14px;
}

.info-value.highlight {
  font-size: 20px;
  font-weight: 700;
  color: #ff7875;
}

.info-value.priority {
  font-size: 20px;
  font-weight: 700;
  color: #36cfe9;
}

.info-value.desc {
  line-height: 1.6;
  color: #b0bec5;
}

.cause-content {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.empty-state {
  text-align: center;
  padding: 80px 0;
  color: #5a6f86;
}

.empty-state p {
  margin: 16px 0 24px;
  font-size: 15px;
}

.back-list-btn {
  background: linear-gradient(135deg, #1890ff, #36cfe9) !important;
  border: none !important;
  border-radius: 8px !important;
  padding: 10px 32px !important;
}

:deep(.el-table .el-loading-mask) {
  background: rgba(13, 27, 42, 0.5) !important;
}

@media (max-width: 1024px) {
  .status-section { grid-template-columns: 1fr; }
  .detail-section { grid-template-columns: 1fr; }
}
</style>
