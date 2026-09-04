<template>
  <div class="alert-list">
    <PageHeader title="预警事件列表">
      <el-button @click="resetQuery">刷新</el-button>
    </PageHeader>

    <!-- 4 个统计卡片 -->
    <div class="alert-list__stats">
      <StatCard label="预警总数" :value="stats.total" icon="Bell" color="#2979FF" />
      <StatCard label="待处理" :value="stats.open" icon="Clock" color="#FA8C16" />
      <StatCard label="红色预警" :value="stats.red" icon="Warning" color="#F5222D" />
      <StatCard label="已解决" :value="stats.resolved" icon="CircleCheck" color="#52C41A" />
    </div>

    <!-- 筛选 + 表格 -->
    <section class="app-card alert-list__table-card">
      <div class="filter-bar alert-list__filter">
        <el-select v-model="query.alertLevel" placeholder="预警等级" clearable class="alert-list__filter-item">
          <el-option label="全部等级" value="" />
          <el-option label="蓝色预警" value="BLUE" />
          <el-option label="黄色预警" value="YELLOW" />
          <el-option label="橙色预警" value="ORANGE" />
          <el-option label="红色预警" value="RED" />
        </el-select>
        <el-select v-model="query.alertStatus" placeholder="处理状态" clearable class="alert-list__filter-item">
          <el-option label="全部状态" value="" />
          <el-option label="待处理" value="OPEN" />
          <el-option label="已确认" value="ACKNOWLEDGED" />
          <el-option label="已解决" value="RESOLVED" />
          <el-option label="已关闭" value="CLOSED" />
        </el-select>
        <el-input v-model="query.deviceType" placeholder="设备类型" clearable class="alert-list__filter-item" @keyup.enter="loadData" />
        <el-button type="primary" @click="loadData">
          <el-icon><Search /></el-icon> 查询
        </el-button>
        <el-button @click="resetQuery">重置</el-button>
      </div>

      <el-table
        :data="tableData"
        v-loading="tableLoading"
        class="app-table"
        row-class-name="clickable-row"
        @row-click="goDetail"
      >
        <el-table-column prop="alertEventCode" label="预警编号" min-width="180">
          <template #default="{ row }"><span class="code-cell">{{ row.alertEventCode }}</span></template>
        </el-table-column>
        <el-table-column label="等级" width="110" align="center">
          <template #default="{ row }"><AlertLevelTag :level="row.alertLevel" /></template>
        </el-table-column>
        <el-table-column prop="deviceType" label="设备类型" width="120" />
        <el-table-column prop="deviceId" label="设备ID" min-width="140" />
        <el-table-column prop="areaId" label="区域" width="120" />
        <el-table-column prop="metricKey" label="指标" width="120" />
        <el-table-column label="指标值/阈值" width="150" align="center">
          <template #default="{ row }">
            <span class="metric-value">{{ row.metricValue }}</span>
            <span class="metric-sep"> / </span>
            <span class="metric-threshold">{{ row.thresholdValue }}</span>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="110" align="center">
          <template #default="{ row }"><AlertStatusTag :status="row.alertStatus" /></template>
        </el-table-column>
        <el-table-column label="优先级" width="90" align="center">
          <template #default="{ row }"><span class="priority-value">{{ row.priorityScore }}</span></template>
        </el-table-column>
        <el-table-column label="时间" width="170">
          <template #default="{ row }"><span class="time-cell">{{ formatDateTime(row.eventTimestamp) }}</span></template>
        </el-table-column>
        <el-table-column label="操作" width="220" align="center" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" size="small" @click.stop="goDetail(row)">详情</el-button>
            <el-button
              v-if="can('notification:send')"
              link type="primary" size="small"
              :loading="sendingId === row.id"
              @click.stop="handleSendEmail(row)"
            >发送邮件</el-button>
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

      <div class="alert-list__pagination">
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
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Search } from '@element-plus/icons-vue'
import PageHeader from '@/components/PageHeader.vue'
import StatCard from '@/components/StatCard.vue'
import AlertLevelTag from '@/components/AlertLevelTag.vue'
import AlertStatusTag from '@/components/AlertStatusTag.vue'
import { getAlertList, updateAlertStatus } from '@/api/alert'
import { sendConfiguredEmail } from '@/api/notification'
import { can } from '@/stores/auth'
import { formatDateTime } from '@/utils/format'

const router = useRouter()

// 统计数据
const stats = ref({ total: 0, open: 0, red: 0, resolved: 0 })

// 加载 4 组统计值（保留原 loadStats 业务逻辑）
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

// 查询条件 + 表格数据
const query = ref({ page: 1, size: 10, alertLevel: '', alertStatus: '', deviceType: '' })
const tableData = ref([])
const total = ref(0)
const tableLoading = ref(false)
const sendingId = ref(null)

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

const handleSendEmail = async (row) => {
  sendingId.value = row.id
  try {
    const result = await sendConfiguredEmail({
      alertId: row.alertEventCode || String(row.id),
      subject: `【城市生命线平台】【${row.alertLevel || '预警'}】${row.deviceType || '设备'}异常告警`,
      content: [
        `预警编号：${row.alertEventCode || row.id}`,
        `预警等级：${row.alertLevel || '-'}`,
        `设备编号：${row.deviceId || '-'}`,
        `设备类型：${row.deviceType || '-'}`,
        `所属区域：${row.areaId || '-'}`,
        `监测指标：${row.metricKey || '-'}`,
        `当前值：${row.metricValue ?? '-'}`,
        `告警阈值：${row.thresholdValue ?? '-'}`,
        `发生时间：${formatDateTime(row.eventTimestamp)}`,
        `当前状态：${row.alertStatus || '-'}`
      ].join('\n'),
      alertLevel: row.alertLevel,
      businessType: row.deviceType,
      areaId: row.areaId
    })
    const item = result.items?.[0]
    if (item?.status === 'SUCCESS') ElMessage.success('告警邮件发送成功')
    else ElMessage.error(item?.errorMessage || '邮件发送失败，请在通知记录中查看原因')
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || error.message || '邮件发送失败')
  } finally {
    sendingId.value = null
  }
}

onMounted(() => {
  loadStats()
  loadData()
})
</script>

<style scoped>
.alert-list__stats {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
  margin-bottom: 16px;
}
.alert-list__table-card {
  padding: 16px 20px;
}
.alert-list__filter {
  margin-bottom: 16px;
}
.alert-list__filter-item {
  width: 160px;
}
.alert-list__pagination {
  display: flex;
  justify-content: flex-end;
  margin-top: 16px;
}

/* 表格内的特殊单元样式 */
.code-cell {
  font-family: 'Courier New', monospace;
  font-size: 13px;
  color: var(--app-primary);
}
.metric-value {
  color: var(--app-text-1);
  font-weight: 600;
}
.metric-sep {
  color: var(--app-text-3);
  margin: 0 2px;
}
.metric-threshold {
  color: var(--app-text-3);
}
.priority-value {
  font-weight: 600;
  color: var(--app-text-1);
}
.time-cell {
  color: var(--app-text-3);
  font-size: 13px;
}

:deep(.clickable-row) {
  cursor: pointer;
}

@media (max-width: 1024px) {
  .alert-list__stats { grid-template-columns: repeat(2, 1fr); }
}
</style>
