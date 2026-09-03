<script setup lang="ts">
import { nextTick, onBeforeUnmount, onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { getBurstCases, getBurstStats, getBurstValves, getLatest, handleBurst, predictBurst } from '../api'
import type { BurstCase, BurstValve, MonitorLatest } from '../types'
import { initChart, levelPieOption, pieOption } from '../utils/chart'
import { fmtTs, riskTagType } from '../utils/format'

const emit = defineEmits<{ (e: 'changed'): void }>()

// ---------------- 图表 ----------------
const levelEl = ref<HTMLElement>()
const statusEl = ref<HTMLElement>()
let levelChart: ReturnType<typeof initChart> | null = null
let statusChart: ReturnType<typeof initChart> | null = null

async function loadCharts() {
  try {
    const s = await getBurstStats()
    await nextTick()
    if (levelEl.value && !levelChart) levelChart = initChart(levelEl.value)
    if (statusEl.value && !statusChart) statusChart = initChart(statusEl.value)
    levelChart?.setOption(levelPieOption(s.by_level, '爆管风险等级分布'), true)
    statusChart?.setOption(pieOption(s.by_status, '处置状态分布'), true)
  } catch (e) {
    console.error('爆管统计加载失败', e)
  }
}

function onResize() { levelChart?.resize(); statusChart?.resize() }

// ---------------- 案例列表 ----------------
const statusFilter = ref('')
const rows = ref<BurstCase[]>([])
const loading = ref(false)

async function load() {
  loading.value = true
  try {
    const d = await getBurstCases(statusFilter.value)
    rows.value = d.items
  } catch (e: any) {
    ElMessage.error('爆管案例加载失败：' + (e?.message || e))
  } finally {
    loading.value = false
  }
}

// ---------------- 风险预判 ----------------
const pipeOptions = ref<MonitorLatest[]>([])
const predictVisible = ref(false)
const predictPipe = ref<number | undefined>(undefined)
const predicting = ref(false)

function openPredict() {
  predictPipe.value = undefined
  predictVisible.value = true
}

async function submitPredict() {
  if (!predictPipe.value) {
    ElMessage.warning('请选择管道')
    return
  }
  predicting.value = true
  try {
    const r = await predictBurst(predictPipe.value)
    ElMessage.success(`预判完成：风险${r.risk_level}（${r.risk_score}分），停水影响 ${r.affected_users} 户，已生成关阀方案`)
    predictVisible.value = false
    load(); loadCharts(); emit('changed')
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || e?.message || '预判失败')
  } finally {
    predicting.value = false
  }
}

// ---------------- 关阀方案 ----------------
const valveVisible = ref(false)
const valveTitle = ref('')
const valveRows = ref<BurstValve[]>([])

async function openValves(row: BurstCase) {
  valveTitle.value = `${row.code} · ${row.name}`
  valveVisible.value = true
  try {
    const d = await getBurstValves(row.id)
    valveRows.value = d.items
  } catch (e: any) {
    ElMessage.error('关阀方案加载失败：' + (e?.message || e))
  }
}

// ---------------- 处置流转 ----------------
async function doHandle(row: BurstCase, status: string) {
  await handleBurst(row.id, status)
  ElMessage.success(`案例已流转为「${status}」`)
  load(); loadCharts(); emit('changed')
}

onMounted(async () => {
  const p = await getLatest().catch(() => null)
  if (p) pipeOptions.value = p.items
  load()
  loadCharts()
  window.addEventListener('resize', onResize)
})
onBeforeUnmount(() => {
  window.removeEventListener('resize', onResize)
  levelChart?.dispose(); statusChart?.dispose()
})
</script>

<template>
  <div>
    <div class="panel">
      <div class="panel-title">爆管风险态势<span class="tip">管龄+材质+压力综合评分预判，自动评估停水影响并推荐最优关阀方案</span></div>
      <div class="chart-row">
        <div>
          <div ref="levelEl" class="chart-box"></div>
        </div>
        <div>
          <div ref="statusEl" class="chart-box"></div>
        </div>
      </div>
    </div>

    <div class="panel">
      <div class="panel-title">爆管风险案例与关阀处置</div>
      <div class="toolbar">
        <el-select v-model="statusFilter" placeholder="全部处置状态" clearable style="width:130px" @change="load">
          <el-option label="风险预警" value="风险预警" />
          <el-option label="处置中" value="处置中" />
          <el-option label="已关阀" value="已关阀" />
          <el-option label="已修复" value="已修复" />
        </el-select>
        <el-button type="primary" @click="load">查询</el-button>
        <div class="spacer"></div>
        <el-button type="primary" plain @click="openPredict">+ 爆管风险预判</el-button>
      </div>

      <el-table :data="rows" v-loading="loading" size="small" border stripe>
        <el-table-column prop="code" label="管道编号" width="100" />
        <el-table-column label="管道 / 区域" min-width="200">
          <template #default="{ row }">
            {{ row.name }}<div class="cell-sub">{{ row.district }} · {{ row.road_name }}</div>
          </template>
        </el-table-column>
        <el-table-column label="材质/管径" width="110" align="center">
          <template #default="{ row }">{{ row.material }}<div class="cell-sub">DN{{ row.diameter_mm }}</div></template>
        </el-table-column>
        <el-table-column label="风险评分" width="90" align="right">
          <template #default="{ row }">
            <span :style="{ color: row.risk_score >= 60 ? '#f56c6c' : (row.risk_score >= 40 ? '#e6a23c' : '#67c23a'), fontWeight: 700 }">
              {{ row.risk_score }}
            </span>
          </template>
        </el-table-column>
        <el-table-column label="风险等级" width="85" align="center">
          <template #default="{ row }">
            <el-tag :type="riskTagType(row.risk_level)" size="small">{{ row.risk_level }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="predict_detail" label="预判依据" min-width="240" show-overflow-tooltip />
        <el-table-column label="停水影响" width="130">
          <template #default="{ row }">
            {{ row.affected_users }} 户<div class="cell-sub">{{ row.affected_area }}</div>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="90" align="center">
          <template #default="{ row }">
            <el-tag :type="row.status === '已修复' ? 'success' : (row.status === '风险预警' ? 'danger' : 'warning')" size="small">{{ row.status }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="230" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" size="small" @click="openValves(row)">关阀方案</el-button>
            <el-button v-if="row.status === '风险预警'" link type="warning" size="small" @click="doHandle(row, '处置中')">开始处置</el-button>
            <el-button v-if="row.status === '处置中'" link type="warning" size="small" @click="doHandle(row, '已关阀')">确认关阀</el-button>
            <el-button v-if="row.status === '已关阀'" link type="success" size="small" @click="doHandle(row, '已修复')">修复完成</el-button>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <!-- 风险预判 -->
    <el-dialog v-model="predictVisible" title="爆管风险预判" width="460px" :close-on-click-modal="false">
      <el-form label-width="100px">
        <el-form-item label="管道">
          <el-select v-model="predictPipe" filterable placeholder="请选择管道" style="width:100%">
            <el-option v-for="p in pipeOptions" :key="p.id" :label="`${p.code}　${p.name}`" :value="p.id" />
          </el-select>
        </el-form-item>
      </el-form>
      <div class="cell-sub">评分模型：管龄40% + 材质30% + 运行压力30%；≥60 高风险 / ≥40 中风险</div>
      <template #footer>
        <el-button @click="predictVisible = false">取消</el-button>
        <el-button type="primary" :loading="predicting" @click="submitPredict">开始预判</el-button>
      </template>
    </el-dialog>

    <!-- 关阀方案 -->
    <el-dialog v-model="valveVisible" :title="`最优关阀方案 · ${valveTitle}`" width="640px">
      <el-alert type="info" :closable="false" style="margin-bottom:10px"
                title="按操作顺序依次关闭以下阀门，可最小化停水范围并隔离爆管管段" />
      <el-table :data="valveRows" size="small" border>
        <el-table-column prop="order_no" label="顺序" width="70" align="center" />
        <el-table-column prop="valve_code" label="阀门编号" width="140" />
        <el-table-column prop="position" label="位置" min-width="220" />
      </el-table>
    </el-dialog>
  </div>
</template>
