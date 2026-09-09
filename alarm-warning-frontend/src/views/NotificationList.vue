<template>
  <section class="notification-page">
    <div class="page-head"><div><h2>通知记录</h2><p>查询邮件、短信发送状态与失败重试记录</p></div><el-button :icon="Refresh" :loading="loading" @click="load">刷新</el-button></div>
    <el-card shadow="never">
      <div class="filters">
        <el-input v-model.trim="filters.alertId" clearable placeholder="告警编号" @keyup.enter="search" />
        <el-select v-model="filters.channel" clearable placeholder="通知通道"><el-option label="邮件" value="EMAIL" /><el-option label="短信" value="SMS" /></el-select>
        <el-select v-model="filters.status" clearable placeholder="发送状态"><el-option v-for="item in statusOptions" :key="item.value" :label="item.label" :value="item.value" /></el-select>
        <el-button type="primary" @click="search">查询</el-button>
        <el-button @click="reset">重置</el-button>
      </div>
      <el-table v-loading="loading" :data="rows">
        <el-table-column prop="id" label="通知编号" width="100" />
        <el-table-column prop="alertId" label="告警编号" min-width="190" show-overflow-tooltip />
        <el-table-column prop="recipientName" label="接收用户" min-width="110" />
        <el-table-column label="通道" width="90"><template #default="{ row }"><el-tag effect="plain">{{ row.channel === 'EMAIL' ? '邮件' : '短信' }}</el-tag></template></el-table-column>
        <el-table-column prop="recipient" label="接收地址" min-width="180" />
        <el-table-column label="状态" width="105"><template #default="{ row }"><el-tag :type="statusTag(row.status)">{{ statusName(row.status) }}</el-tag></template></el-table-column>
        <el-table-column prop="retryCount" label="尝试次数" width="90" align="center" />
        <el-table-column prop="sentAt" label="发送时间" min-width="165"><template #default="{ row }">{{ row.sentAt || '-' }}</template></el-table-column>
        <el-table-column prop="errorMessage" label="失败原因" min-width="180" show-overflow-tooltip />
        <el-table-column v-if="can('notification:retry')" label="操作" width="90" fixed="right"><template #default="{ row }"><el-button v-if="row.status === 'FAILED'" link type="primary" :loading="retrying === row.id" @click="retry(row)">重试</el-button></template></el-table-column>
      </el-table>
      <el-pagination v-model:current-page="page" v-model:page-size="size" layout="total, prev, pager, next" :total="total" @current-change="load" />
    </el-card>
  </section>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { Refresh } from '@element-plus/icons-vue'
import { can } from '@/stores/auth'
import { getNotifications, retryNotification } from '@/api/notification'

const rows = ref([])
const total = ref(0)
const page = ref(1)
const size = ref(20)
const loading = ref(false)
const retrying = ref(null)
const filters = reactive({ alertId: '', channel: '', status: '' })
const statusOptions = [
  { label: '待发送', value: 'PENDING' }, { label: '发送中', value: 'SENDING' },
  { label: '发送成功', value: 'SUCCESS' }, { label: '发送失败', value: 'FAILED' }
]
const statusName = (status) => statusOptions.find((item) => item.value === status)?.label || status
const statusTag = (status) => ({ SUCCESS: 'success', FAILED: 'danger', SENDING: 'warning', PENDING: 'info' }[status] || 'info')

async function load() {
  loading.value = true
  try {
    const data = await getNotifications({ page: page.value, size: size.value, ...filters })
    rows.value = data.items || []
    total.value = data.total || 0
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || '通知记录加载失败')
  } finally {
    loading.value = false
  }
}
function search() { page.value = 1; load() }
function reset() { Object.assign(filters, { alertId: '', channel: '', status: '' }); search() }
async function retry(row) {
  retrying.value = row.id
  try { await retryNotification(row.id); ElMessage.success('重试已执行'); await load() }
  catch (error) { ElMessage.error(error.response?.data?.detail || '重试失败') }
  finally { retrying.value = null }
}
onMounted(load)
</script>

<style scoped>
.notification-page { display: flex; flex-direction: column; gap: 20px; }
.page-head { display: flex; align-items: center; justify-content: space-between; }
.page-head h2 { margin: 0; color: var(--app-text-1); }.page-head p { margin: 7px 0 0; color: var(--app-text-3); }
.filters { display: grid; grid-template-columns: minmax(180px, 1fr) 150px 150px auto auto; gap: 10px; margin-bottom: 16px; }
:deep(.el-card) { border: 0; border-radius: var(--app-radius-card); box-shadow: var(--app-shadow-card); }
:deep(.el-pagination) { justify-content: flex-end; margin-top: 18px; }
@media (max-width: 900px) { .filters { grid-template-columns: 1fr 1fr; } }
</style>
