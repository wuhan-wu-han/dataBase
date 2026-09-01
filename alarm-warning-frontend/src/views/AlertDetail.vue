<template>
  <div class="alert-detail" v-loading="loading">
    <!-- 返回链接 -->
    <router-link to="/alerts" class="alert-detail__back">
      <el-icon><ArrowLeft /></el-icon> 返回列表
    </router-link>

    <PageHeader title="预警事件详情" />

    <template v-if="detail">
      <!-- 顶部：状态卡片 + 操作面板 -->
      <section class="alert-detail__top">
        <div class="app-card alert-detail__status">
          <div class="alert-detail__level-badge" :class="'level-' + (detail.alertLevel || '').toLowerCase()">
            {{ levelShort(detail.alertLevel) }}
          </div>
          <div class="alert-detail__status-info">
            <div class="alert-detail__code">{{ detail.alertEventCode }}</div>
            <div class="alert-detail__tags">
              <AlertLevelTag :level="detail.alertLevel" />
              <AlertStatusTag :status="detail.alertStatus" />
            </div>
            <div class="alert-detail__device">{{ detail.deviceType }} · {{ detail.deviceId }}</div>
          </div>
        </div>

        <div class="app-card alert-detail__action">
          <h3 class="alert-detail__panel-title">状态操作</h3>
          <div class="alert-detail__action-buttons">
            <el-button
              v-if="detail.alertStatus === 'OPEN'"
              type="warning"
              :loading="statusUpdating"
              @click="handleStatus('ACKNOWLEDGED')"
            >确认</el-button>
            <el-button
              v-if="detail.alertStatus === 'ACKNOWLEDGED'"
              type="success"
              :loading="statusUpdating"
              @click="handleStatus('RESOLVED')"
            >解决</el-button>
            <el-button
              v-if="detail.alertStatus !== 'CLOSED'"
              type="info"
              :loading="statusUpdating"
              @click="handleStatus('CLOSED')"
            >关闭</el-button>
            <span v-if="detail.alertStatus === 'CLOSED'" class="alert-detail__closed-hint">该事件已关闭</span>
          </div>
        </div>
      </section>

      <!-- 详情网格 -->
      <section class="alert-detail__grid">
        <!-- 基本信息 -->
        <div class="app-card alert-detail__panel">
          <h3 class="alert-detail__panel-title">基本信息</h3>
          <div class="alert-detail__info-grid">
            <div class="alert-detail__info-item">
              <span class="alert-detail__info-label">预警编码</span>
              <span class="alert-detail__info-value code">{{ detail.alertEventCode }}</span>
            </div>
            <div class="alert-detail__info-item">
              <span class="alert-detail__info-label">数据来源</span>
              <span class="alert-detail__info-value">{{ detail.source || '-' }}</span>
            </div>
            <div class="alert-detail__info-item">
              <span class="alert-detail__info-label">关联事件ID</span>
              <span class="alert-detail__info-value code">{{ detail.sourceEventId || '-' }}</span>
            </div>
            <div class="alert-detail__info-item">
              <span class="alert-detail__info-label">设备ID</span>
              <span class="alert-detail__info-value">{{ detail.deviceId }}</span>
            </div>
            <div class="alert-detail__info-item">
              <span class="alert-detail__info-label">设备类型</span>
              <span class="alert-detail__info-value">{{ detail.deviceType }}</span>
            </div>
            <div class="alert-detail__info-item">
              <span class="alert-detail__info-label">管廊区段</span>
              <span class="alert-detail__info-value">{{ detail.zone || '-' }}</span>
            </div>
            <div class="alert-detail__info-item">
              <span class="alert-detail__info-label">区域ID</span>
              <span class="alert-detail__info-value">{{ detail.areaId }}</span>
            </div>
            <div class="alert-detail__info-item">
              <span class="alert-detail__info-label">事件时间</span>
              <span class="alert-detail__info-value time">{{ formatDateTime(detail.eventTimestamp) }}</span>
            </div>
          </div>
        </div>

        <!-- 监测数据 -->
        <div class="app-card alert-detail__panel">
          <h3 class="alert-detail__panel-title">监测数据</h3>
          <div class="alert-detail__info-grid">
            <div class="alert-detail__info-item">
              <span class="alert-detail__info-label">监测指标</span>
              <span class="alert-detail__info-value">{{ detail.metricKey }}</span>
            </div>
            <div class="alert-detail__info-item">
              <span class="alert-detail__info-label">当前值</span>
              <span class="alert-detail__info-value highlight">{{ detail.metricValue }}</span>
            </div>
            <div class="alert-detail__info-item">
              <span class="alert-detail__info-label">阈值</span>
              <span class="alert-detail__info-value">{{ detail.thresholdValue }}</span>
            </div>
            <div class="alert-detail__info-item">
              <span class="alert-detail__info-label">优先级评分</span>
              <span class="alert-detail__info-value priority">{{ detail.priorityScore }}</span>
            </div>
          </div>
        </div>

        <!-- 原因分析 -->
        <div
          v-if="detail.rootCause || detail.rootCauseDesc"
          class="app-card alert-detail__panel alert-detail__panel--full"
        >
          <h3 class="alert-detail__panel-title">原因分析</h3>
          <div class="alert-detail__info-grid">
            <div class="alert-detail__info-item" v-if="detail.rootCause">
              <span class="alert-detail__info-label">根因类型</span>
              <span class="alert-detail__info-value">{{ detail.rootCause }}</span>
            </div>
            <div class="alert-detail__info-item" v-if="detail.rootCauseDesc">
              <span class="alert-detail__info-label">详细描述</span>
              <span class="alert-detail__info-value desc">{{ detail.rootCauseDesc }}</span>
            </div>
          </div>
        </div>

        <!-- 关联信息 -->
        <div v-if="detail.alertGroupId" class="app-card alert-detail__panel">
          <h3 class="alert-detail__panel-title">关联信息</h3>
          <div class="alert-detail__info-grid">
            <div class="alert-detail__info-item">
              <span class="alert-detail__info-label">预警组ID</span>
              <span class="alert-detail__info-value code">{{ detail.alertGroupId }}</span>
            </div>
            <div class="alert-detail__info-item">
              <span class="alert-detail__info-label">合并次数</span>
              <span class="alert-detail__info-value">{{ detail.mergedCount }}</span>
            </div>
          </div>
        </div>
      </section>
    </template>

    <!-- 空态 -->
    <div v-if="!loading && !detail" class="alert-detail__empty">
      <el-icon :size="48"><Warning /></el-icon>
      <p>预警事件不存在或加载失败</p>
      <el-button type="primary" @click="$router.push('/alerts')">返回列表</el-button>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { ArrowLeft, Warning } from '@element-plus/icons-vue'
import PageHeader from '@/components/PageHeader.vue'
import AlertLevelTag from '@/components/AlertLevelTag.vue'
import AlertStatusTag from '@/components/AlertStatusTag.vue'
import { getAlertDetail, updateAlertStatus } from '@/api/alert'
import { formatDateTime } from '@/utils/format'

const route = useRoute()

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

// 状态操作：保留原有 handleStatus 业务逻辑
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

// 等级缩写
const levelShort = (level) => {
  const map = { BLUE: '蓝', YELLOW: '黄', ORANGE: '橙', RED: '红' }
  return map[level] || level
}

onMounted(() => {
  loadDetail()
})
</script>

<style scoped>
.alert-detail__back {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: 13px;
  color: var(--app-text-3);
  text-decoration: none;
  margin-bottom: 12px;
}
.alert-detail__back:hover {
  color: var(--app-primary);
}

/* 顶部区：状态卡 + 操作面板 */
.alert-detail__top {
  display: grid;
  grid-template-columns: 2fr 1fr;
  gap: 16px;
  margin-bottom: 16px;
}
.alert-detail__status {
  display: flex;
  align-items: center;
  gap: 20px;
}
.alert-detail__level-badge {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 56px;
  height: 56px;
  border-radius: 12px;
  font-size: 22px;
  font-weight: 600;
  flex-shrink: 0;
}
.alert-detail__level-badge.level-blue {
  background-color: rgba(41, 121, 255, 0.1);
  color: #2979FF;
}
.alert-detail__level-badge.level-yellow {
  background-color: rgba(250, 173, 20, 0.12);
  color: #FAAD14;
}
.alert-detail__level-badge.level-orange {
  background-color: rgba(250, 140, 22, 0.12);
  color: #FA8C16;
}
.alert-detail__level-badge.level-red {
  background-color: rgba(245, 34, 45, 0.1);
  color: #F5222D;
}
.alert-detail__status-info {
  min-width: 0;
  flex: 1;
}
.alert-detail__code {
  font-size: 18px;
  font-weight: 600;
  color: var(--app-text-1);
  margin-bottom: 8px;
}
.alert-detail__tags {
  display: flex;
  gap: 8px;
  margin-bottom: 8px;
}
.alert-detail__device {
  font-size: 13px;
  color: var(--app-text-3);
}

.alert-detail__action {
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.alert-detail__action-buttons {
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.alert-detail__closed-hint {
  color: var(--app-text-3);
  font-size: 14px;
  text-align: center;
  padding: 12px 0;
}

/* 详情网格 */
.alert-detail__grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
}
.alert-detail__panel {
  padding: 16px 20px;
}
.alert-detail__panel--full {
  grid-column: 1 / -1;
}
.alert-detail__panel-title {
  margin: 0 0 12px 0;
  font-size: 16px;
  font-weight: 600;
  color: var(--app-text-1);
}
.alert-detail__info-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
}
.alert-detail__info-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.alert-detail__info-label {
  font-size: 12px;
  color: var(--app-text-3);
}
.alert-detail__info-value {
  font-size: 14px;
  color: var(--app-text-1);
  font-weight: 500;
  word-break: break-all;
}
.alert-detail__info-value.code {
  font-family: 'Courier New', monospace;
  color: var(--app-primary);
}
.alert-detail__info-value.time {
  font-family: 'Courier New', monospace;
  color: var(--app-text-2);
}
.alert-detail__info-value.highlight {
  font-size: 20px;
  font-weight: 700;
  color: #F5222D;
}
.alert-detail__info-value.priority {
  font-size: 20px;
  font-weight: 700;
  color: var(--app-primary);
}
.alert-detail__info-value.desc {
  line-height: 1.6;
  color: var(--app-text-2);
  font-weight: 400;
}

/* 空态 */
.alert-detail__empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 80px 0;
  color: var(--app-text-3);
  gap: 12px;
}
.alert-detail__empty p {
  margin: 0 0 12px;
  font-size: 15px;
}

@media (max-width: 1024px) {
  .alert-detail__top { grid-template-columns: 1fr; }
  .alert-detail__grid { grid-template-columns: 1fr; }
}
</style>
