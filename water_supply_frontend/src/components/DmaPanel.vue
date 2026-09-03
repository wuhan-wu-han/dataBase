<script setup lang="ts">
import { nextTick, onBeforeUnmount, onMounted, reactive, ref } from 'vue'
import { ElMessage, type FormInstance } from 'element-plus'
import { addDmaRecord, getDmaRecords, getDmaStats, getDmaZones, locateDarkLeak } from '../api'
import type { DmaRecord, DmaZone } from '../types'
import { barOption, historyLineOption, initChart } from '../utils/chart'
import { fmt, today } from '../utils/format'

const emit = defineEmits<{ (e: 'changed'): void }>()

// ---------------- 图表 ----------------
const rateEl = ref<HTMLElement>()
const nightEl = ref<HTMLElement>()
let rateChart: ReturnType<typeof initChart> | null = null
let nightChart: ReturnType<typeof initChart> | null = null
const stats = ref<{ avg_rate: number; total_users: number; dark_leaks: any[] } | null>(null)

async function loadCharts() {
  try {
    const s = await getDmaStats()
    stats.value = s
    await nextTick()
    if (rateEl.value && !rateChart) rateChart = initChart(rateEl.value)
    if (nightEl.value && !nightChart) nightChart = initChart(nightEl.value)
    rateChart?.setOption(barOption(s.by_rate, '#e6a23c'), true)
    nightChart?.setOption(barOption(s.night, '#409eff'), true)
  } catch (e) {
    console.error('DMA统计加载失败', e)
  }
}

function onResize() { rateChart?.resize(); nightChart?.resize() }

// ---------------- 分区列表 ----------------
const query = reactive({ keyword: '', status: '' })
const rows = ref<DmaZone[]>([])
const loading = ref(false)

async function load() {
  loading.value = true
  try {
    const d = await getDmaZones({
      keyword: query.keyword || undefined, status: query.status || undefined
    })
    rows.value = d.items
  } catch (e: any) {
    ElMessage.error('分区列表加载失败：' + (e?.message || e))
  } finally {
    loading.value = false
  }
}

// ---------------- 计量记录 ----------------
const recordVisible = ref(false)
const recordTitle = ref('')
const recordRows = ref<DmaRecord[]>([])
const recordEl = ref<HTMLElement>()
let recordChart: ReturnType<typeof initChart> | null = null

async function openRecords(row: DmaZone) {
  recordTitle.value = `${row.code} · ${row.name}`
  recordVisible.value = true
  try {
    const d = await getDmaRecords(row.id, 7)
    recordRows.value = [...d.records].reverse()
    await nextTick()
    if (recordEl.value && !recordChart) recordChart = initChart(recordEl.value)
    recordChart?.setOption(historyLineOption(recordRows.value.map(r => r.date.slice(5)), [
      { name: '漏损率(%)', data: recordRows.value.map(r => r.leakage_rate_pct) },
      { name: '夜间最小流量(m3/h)', data: recordRows.value.map(r => r.night_min_flow_m3h ?? null) }
    ]), true)
    recordChart?.resize()
  } catch (e: any) {
    ElMessage.error('计量记录加载失败：' + (e?.message || e))
  }
}

function closeRecords() {
  recordChart?.dispose()
  recordChart = null
}

// ---------------- 录入计量数据 ----------------
const addVisible = ref(false)
const addTarget = ref<DmaZone | null>(null)
const addRef = ref<FormInstance>()
const adding = ref(false)
const addForm = reactive({
  date: today(), inflow_m3: undefined as number | undefined,
  billed_m3: undefined as number | undefined, night_min_flow_m3h: undefined as number | undefined
})
const addRules = {
  date: [{ required: true, message: '请输入日期', trigger: 'blur' }],
  inflow_m3: [{ required: true, message: '请输入供水量', trigger: 'blur' }],
  billed_m3: [{ required: true, message: '请输入售水量', trigger: 'blur' }]
}

function openAdd(row: DmaZone) {
  addTarget.value = row
  Object.assign(addForm, { date: today(), inflow_m3: undefined, billed_m3: undefined, night_min_flow_m3h: undefined })
  addVisible.value = true
}

async function submitAdd() {
  if (!addRef.value || !addTarget.value) return
  await addRef.value.validate(async valid => {
    if (!valid) return
    adding.value = true
    try {
      const r = await addDmaRecord({ dma_id: addTarget.value!.id, ...addForm })
      if (r.alerts?.length) {
        ElMessage.warning(`核算漏损率 ${r.leakage_rate_pct}%，产生 ${r.alerts.length} 条告警`)
      } else {
        ElMessage.success(`核算完成，漏损率 ${r.leakage_rate_pct}%`)
      }
      addVisible.value = false
      load(); loadCharts(); emit('changed')
    } catch (e: any) {
      ElMessage.error(e?.response?.data?.detail || e?.message || '录入失败')
    } finally {
      adding.value = false
    }
  })
}

// ---------------- 暗漏定位 ----------------
const locateVisible = ref(false)
const locateTarget = ref<DmaZone | null>(null)
const locateText = ref('')

function openLocate(row: DmaZone) {
  locateTarget.value = row
  locateText.value = row.dark_leak_location || ''
  locateVisible.value = true
}

async function submitLocate() {
  if (!locateTarget.value || !locateText.value) return
  await locateDarkLeak(locateTarget.value.id, locateText.value)
  ElMessage.success('暗漏点位已定位登记')
  locateVisible.value = false
  load(); emit('changed')
}

onMounted(() => {
  load()
  loadCharts()
  window.addEventListener('resize', onResize)
})
onBeforeUnmount(() => {
  window.removeEventListener('resize', onResize)
  rateChart?.dispose(); nightChart?.dispose(); recordChart?.dispose()
})
</script>

<template>
  <div>
    <div class="panel">
      <div class="panel-title">DMA 分区漏损统计
        <span class="tip">平均漏损率 {{ stats?.avg_rate ?? '-' }}% · 管控线 12% · 覆盖用户 {{ stats?.total_users ?? '-' }} 户</span>
      </div>
      <div class="chart-row">
        <div>
          <div class="chart-caption">各分区漏损率（%）</div>
          <div ref="rateEl" class="chart-box"></div>
        </div>
        <div>
          <div class="chart-caption">夜间最小流量（m3/h）</div>
          <div ref="nightEl" class="chart-box"></div>
        </div>
      </div>
      <div v-if="stats?.dark_leaks?.length" class="sub-title">暗漏点位定位结果</div>
      <el-table v-if="stats?.dark_leaks?.length" :data="stats.dark_leaks" size="small" border>
        <el-table-column prop="code" label="分区编号" width="110" />
        <el-table-column prop="name" label="分区名称" min-width="160" />
        <el-table-column prop="dark_leak_location" label="暗漏点位" min-width="240" />
      </el-table>
    </div>

    <div class="panel">
      <div class="panel-title">DMA 分区计量台账<span class="tip">分区计量统计 / 夜间最小流量分析 / 漏损率自动核算 / 暗漏定位</span></div>
      <div class="toolbar">
        <el-input v-model="query.keyword" placeholder="编号 / 名称 / 区域" clearable
                  style="width:200px" @keyup.enter="load" @clear="load" />
        <el-select v-model="query.status" placeholder="全部状态" clearable style="width:130px" @change="load">
          <el-option label="正常" value="正常" />
          <el-option label="漏损偏高" value="漏损偏高" />
          <el-option label="暗漏定位" value="暗漏定位" />
        </el-select>
        <el-button type="primary" @click="load">查询</el-button>
      </div>

      <el-table :data="rows" v-loading="loading" size="small" border stripe>
        <el-table-column prop="code" label="分区编号" width="100" />
        <el-table-column prop="name" label="分区名称" min-width="160" />
        <el-table-column prop="district" label="区域" width="90" align="center" />
        <el-table-column prop="pipe_count" label="管道数" width="80" align="center" />
        <el-table-column prop="user_count" label="用户数" width="90" align="right" />
        <el-table-column label="日均流量(m3/h)" width="120" align="right">
          <template #default="{ row }">{{ fmt(row.avg_flow_m3h) }}</template>
        </el-table-column>
        <el-table-column label="夜间最小流量" width="110" align="right">
          <template #default="{ row }">
            <span :style="{ color: row.night_min_flow_m3h > 8 ? '#e6a23c' : '' }">{{ fmt(row.night_min_flow_m3h) }}</span>
          </template>
        </el-table-column>
        <el-table-column label="漏损率(%)" width="95" align="right">
          <template #default="{ row }">
            <span :style="{ color: row.leakage_rate_pct > 12 ? '#f56c6c' : '', fontWeight: row.leakage_rate_pct > 12 ? 700 : 400 }">
              {{ fmt(row.leakage_rate_pct) }}
            </span>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="95" align="center">
          <template #default="{ row }">
            <el-tag :type="row.status === '正常' ? 'success' : 'danger'" size="small">{{ row.status }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" size="small" @click="openRecords(row)">计量记录</el-button>
            <el-button link type="primary" size="small" @click="openAdd(row)">录入计量</el-button>
            <el-button link type="primary" size="small" @click="openLocate(row)">暗漏定位</el-button>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <!-- 计量记录 -->
    <el-dialog v-model="recordVisible" :title="`近7日计量趋势 · ${recordTitle}`" width="760px" @closed="closeRecords">
      <div ref="recordEl" class="chart-box tall"></div>
      <el-table :data="recordRows" size="small" border style="margin-top:10px">
        <el-table-column prop="date" label="日期" width="110" />
        <el-table-column prop="inflow_m3" label="供水量(m3)" align="right" />
        <el-table-column prop="billed_m3" label="售水量(m3)" align="right" />
        <el-table-column prop="night_min_flow_m3h" label="夜间最小流量(m3/h)" align="right" />
        <el-table-column prop="leakage_rate_pct" label="漏损率(%)" align="right" />
      </el-table>
    </el-dialog>

    <!-- 录入计量 -->
    <el-dialog v-model="addVisible" :title="`录入分区计量数据 · ${addTarget?.code ?? ''}`" width="480px" :close-on-click-modal="false">
      <el-form ref="addRef" :model="addForm" :rules="addRules" label-width="130px">
        <el-form-item label="日期" prop="date">
          <el-input v-model="addForm.date" placeholder="yyyy-MM-dd" />
        </el-form-item>
        <el-form-item label="供水量(m3)" prop="inflow_m3">
          <el-input-number v-model="addForm.inflow_m3" :min="0" :precision="1" :controls="false" style="width:100%" />
        </el-form-item>
        <el-form-item label="售水量(m3)" prop="billed_m3">
          <el-input-number v-model="addForm.billed_m3" :min="0" :precision="1" :controls="false" style="width:100%" />
        </el-form-item>
        <el-form-item label="夜间最小流量">
          <el-input-number v-model="addForm.night_min_flow_m3h" :min="0" :precision="1" :controls="false" style="width:100%" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="addVisible = false">取消</el-button>
        <el-button type="primary" :loading="adding" @click="submitAdd">提交并核算漏损率</el-button>
      </template>
    </el-dialog>

    <!-- 暗漏定位 -->
    <el-dialog v-model="locateVisible" :title="`暗漏点位定位 · ${locateTarget?.code ?? ''}`" width="480px">
      <el-input v-model="locateText" type="textarea" :rows="2"
                placeholder="如：二七路DN400管段K0+350处，相关仪定位偏差0.5m" />
      <template #footer>
        <el-button @click="locateVisible = false">取消</el-button>
        <el-button type="primary" @click="submitLocate">保存定位</el-button>
      </template>
    </el-dialog>
  </div>
</template>
