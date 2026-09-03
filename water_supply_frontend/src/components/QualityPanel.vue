<script setup lang="ts">
import { nextTick, onBeforeUnmount, onMounted, reactive, ref } from 'vue'
import { ElMessage, type FormInstance } from 'element-plus'
import { collectQuality, getQualityChain, getQualityRecords, getQualityStats } from '../api'
import type { QualityNode, QualityRecord } from '../types'
import { chainOption, historyLineOption, initChart, pieOption } from '../utils/chart'
import { fmt, fmtTs } from '../utils/format'

const emit = defineEmits<{ (e: 'changed'): void }>()

// ---------------- 链路图 + 统计 ----------------
const chainEl = ref<HTMLElement>()
const kindEl = ref<HTMLElement>()
let chainChart: ReturnType<typeof initChart> | null = null
let kindChart: ReturnType<typeof initChart> | null = null
const nodes = ref<QualityNode[]>([])
const abnormalNodes = ref(0)

async function loadChain() {
  try {
    const [c, s] = await Promise.all([getQualityChain(), getQualityStats()])
    nodes.value = c.nodes
    abnormalNodes.value = s.abnormal_nodes
    await nextTick()
    if (chainEl.value && !chainChart) chainChart = initChart(chainEl.value)
    if (kindEl.value && !kindChart) kindChart = initChart(kindEl.value)
    chainChart?.setOption(chainOption(c.nodes.map(n => ({
      name: n.name, kind: n.kind, status: n.status,
      value: `浊度${fmt(n.turbidity_ntu, 2)}NTU 余氯${fmt(n.residual_cl, 2)}mg/L pH${fmt(n.ph)}`
    }))), true)
    kindChart?.setOption(pieOption(s.by_kind, '链路节点类型'), true)
    chainChart?.resize()
  } catch (e) {
    console.error('水质链路加载失败', e)
  }
}

function onResize() { chainChart?.resize(); kindChart?.resize() }

// ---------------- 节点台账 ----------------
const rows = ref<QualityNode[]>([])
const loading = ref(false)

async function loadNodes() {
  loading.value = true
  try {
    const c = await getQualityChain()
    rows.value = c.nodes
  } catch (e: any) {
    ElMessage.error('节点加载失败：' + (e?.message || e))
  } finally {
    loading.value = false
  }
}

// ---------------- 节点水质记录 ----------------
const recordVisible = ref(false)
const recordTitle = ref('')
const recordRows = ref<QualityRecord[]>([])
const recordEl = ref<HTMLElement>()
let recordChart: ReturnType<typeof initChart> | null = null

async function openRecords(row: QualityNode) {
  recordTitle.value = `${row.code} · ${row.name}`
  recordVisible.value = true
  try {
    const d = await getQualityRecords(row.id, 30)
    recordRows.value = [...d.records].reverse()
    await nextTick()
    if (recordEl.value && !recordChart) recordChart = initChart(recordEl.value)
    recordChart?.setOption(historyLineOption(recordRows.value.map(r => fmtTs(r.ts).slice(5)), [
      { name: '浊度(NTU)', data: recordRows.value.map(r => r.turbidity_ntu ?? null) },
      { name: '余氯(mg/L)', data: recordRows.value.map(r => r.residual_cl ?? null) },
      { name: 'pH', data: recordRows.value.map(r => r.ph ?? null) }
    ]), true)
    recordChart?.resize()
  } catch (e: any) {
    ElMessage.error('水质记录加载失败：' + (e?.message || e))
  }
}

function closeRecords() {
  recordChart?.dispose()
  recordChart = null
}

// ---------------- 采集水质 ----------------
const addVisible = ref(false)
const addRef = ref<FormInstance>()
const adding = ref(false)
const addForm = reactive({
  node_id: undefined as number | undefined,
  turbidity_ntu: undefined as number | undefined,
  residual_cl: undefined as number | undefined,
  ph: undefined as number | undefined
})
const addRules = { node_id: [{ required: true, message: '请选择节点', trigger: 'change' }] }

function openAdd(row?: QualityNode) {
  Object.assign(addForm, {
    node_id: row ? row.id : undefined,
    turbidity_ntu: row?.turbidity_ntu ?? undefined,
    residual_cl: row?.residual_cl ?? undefined,
    ph: row?.ph ?? undefined
  })
  addVisible.value = true
}

async function submitAdd() {
  if (!addRef.value) return
  await addRef.value.validate(async valid => {
    if (!valid) return
    adding.value = true
    try {
      const r = await collectQuality({ ...addForm })
      if (r.is_abnormal) {
        const suspect = r.suspect_pipe ? `，溯源定位问题管段：${r.suspect_pipe.name}(${r.suspect_pipe.code})` : ''
        ElMessage.warning(`水质异常，产生 ${r.alarms.length} 条告警${suspect}`)
      } else {
        ElMessage.success('水质正常')
      }
      addVisible.value = false
      loadNodes(); loadChain(); emit('changed')
    } catch (e: any) {
      ElMessage.error(e?.response?.data?.detail || e?.message || '采集失败')
    } finally {
      adding.value = false
    }
  })
}

onMounted(() => {
  loadNodes()
  loadChain()
  window.addEventListener('resize', onResize)
})
onBeforeUnmount(() => {
  window.removeEventListener('resize', onResize)
  chainChart?.dispose(); kindChart?.dispose(); recordChart?.dispose()
})
</script>

<template>
  <div>
    <div class="panel">
      <div class="panel-title">水厂→终端 全链路水质追踪
        <span class="tip">异常节点 {{ abnormalNodes }} 个 · 污染异常自动沿链路溯源定位问题管段</span>
      </div>
      <div class="chart-row">
        <div>
          <div ref="chainEl" class="chart-box tall"></div>
        </div>
        <div>
          <div ref="kindEl" class="chart-box tall"></div>
        </div>
      </div>
    </div>

    <div class="panel">
      <div class="panel-title">链路节点水质台账</div>
      <div class="toolbar">
        <div class="spacer"></div>
        <el-button type="primary" plain @click="openAdd()">+ 采集节点水质</el-button>
      </div>

      <el-table :data="rows" v-loading="loading" size="small" border stripe>
        <el-table-column prop="seq" label="链路序" width="70" align="center" />
        <el-table-column prop="code" label="节点编号" width="100" />
        <el-table-column prop="name" label="节点名称" min-width="180" />
        <el-table-column prop="kind" label="节点类型" width="100" align="center" />
        <el-table-column label="浊度(NTU)" width="95" align="right">
          <template #default="{ row }">
            <span :style="{ color: row.turbidity_ntu > 1 ? '#f56c6c' : '' }">{{ fmt(row.turbidity_ntu, 2) }}</span>
          </template>
        </el-table-column>
        <el-table-column label="余氯(mg/L)" width="100" align="right">
          <template #default="{ row }">
            <span :style="{ color: row.residual_cl < 0.05 ? '#f56c6c' : '' }">{{ fmt(row.residual_cl, 2) }}</span>
          </template>
        </el-table-column>
        <el-table-column label="pH" width="70" align="right">
          <template #default="{ row }">
            <span :style="{ color: (row.ph < 6.5 || row.ph > 8.5) ? '#f56c6c' : '' }">{{ fmt(row.ph) }}</span>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="80" align="center">
          <template #default="{ row }">
            <el-tag :type="row.status === '正常' ? 'success' : 'danger'" size="small">{{ row.status }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="160" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" size="small" @click="openRecords(row)">水质曲线</el-button>
            <el-button link type="primary" size="small" @click="openAdd(row)">采集</el-button>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <!-- 节点水质记录 -->
    <el-dialog v-model="recordVisible" :title="`水质历史曲线 · ${recordTitle}`" width="760px" @closed="closeRecords">
      <div ref="recordEl" class="chart-box tall"></div>
    </el-dialog>

    <!-- 采集水质 -->
    <el-dialog v-model="addVisible" title="采集链路节点水质" width="480px" :close-on-click-modal="false">
      <el-form ref="addRef" :model="addForm" :rules="addRules" label-width="110px">
        <el-form-item label="节点" prop="node_id">
          <el-select v-model="addForm.node_id" filterable placeholder="请选择节点" style="width:100%">
            <el-option v-for="n in nodes" :key="n.id" :label="`${n.code}　${n.name}`" :value="n.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="浊度(NTU)">
          <el-input-number v-model="addForm.turbidity_ntu" :min="0" :precision="2" :controls="false" style="width:100%" />
        </el-form-item>
        <el-form-item label="余氯(mg/L)">
          <el-input-number v-model="addForm.residual_cl" :min="0" :precision="2" :controls="false" style="width:100%" />
        </el-form-item>
        <el-form-item label="pH">
          <el-input-number v-model="addForm.ph" :min="0" :max="14" :precision="1" :controls="false" style="width:100%" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="addVisible = false">取消</el-button>
        <el-button type="primary" :loading="adding" @click="submitAdd">提交并溯源研判</el-button>
      </template>
    </el-dialog>
  </div>
</template>
