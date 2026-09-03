<script setup lang="ts">
import { nextTick, onBeforeUnmount, onMounted, reactive, ref } from 'vue'
import { ElMessage, type FormInstance } from 'element-plus'
import { collectSecondary, getSecondaryStats, getSecondaryUnits } from '../api'
import type { SecondaryUnit } from '../types'
import { initChart, pieOption } from '../utils/chart'
import { fmt } from '../utils/format'

const emit = defineEmits<{ (e: 'changed'): void }>()

// ---------------- 图表 ----------------
const statusEl = ref<HTMLElement>()
let statusChart: ReturnType<typeof initChart> | null = null
const abnormal = ref(0)

async function loadCharts() {
  try {
    const s = await getSecondaryStats()
    abnormal.value = s.abnormal
    await nextTick()
    if (statusEl.value && !statusChart) statusChart = initChart(statusEl.value)
    statusChart?.setOption(pieOption(s.by_status, '二供单元状态分布'), true)
  } catch (e) {
    console.error('二供统计加载失败', e)
  }
}

function onResize() { statusChart?.resize() }

// ---------------- 列表 ----------------
const query = reactive({ keyword: '', status: '' })
const rows = ref<SecondaryUnit[]>([])
const loading = ref(false)

async function load() {
  loading.value = true
  try {
    const d = await getSecondaryUnits({
      keyword: query.keyword || undefined, status: query.status || undefined
    })
    rows.value = d.items
  } catch (e: any) {
    ElMessage.error('二供列表加载失败：' + (e?.message || e))
  } finally {
    loading.value = false
  }
}

// ---------------- 上报数据 ----------------
const addVisible = ref(false)
const addTarget = ref<SecondaryUnit | null>(null)
const addRef = ref<FormInstance>()
const adding = ref(false)
const addForm = reactive({
  level_pct: undefined as number | undefined,
  turbidity_ntu: undefined as number | undefined,
  residual_cl: undefined as number | undefined,
  disinfect_status: '正常'
})

function openAdd(row: SecondaryUnit) {
  addTarget.value = row
  Object.assign(addForm, {
    level_pct: row.level_pct ?? undefined,
    turbidity_ntu: row.turbidity_ntu ?? undefined,
    residual_cl: row.residual_cl ?? undefined,
    disinfect_status: row.disinfect_status || '正常'
  })
  addVisible.value = true
}

async function submitAdd() {
  if (!addTarget.value) return
  adding.value = true
  try {
    const r = await collectSecondary({ unit_id: addTarget.value.id, ...addForm })
    if (r.is_abnormal) {
      ElMessage.warning(`产生 ${r.alarms.length} 条告警：` + r.alarms.map(a => a.detail).join('；'))
    } else {
      ElMessage.success('上报成功，各项指标正常')
    }
    addVisible.value = false
    load(); loadCharts(); emit('changed')
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || e?.message || '上报失败')
  } finally {
    adding.value = false
  }
}

onMounted(() => {
  load()
  loadCharts()
  window.addEventListener('resize', onResize)
})
onBeforeUnmount(() => {
  window.removeEventListener('resize', onResize)
  statusChart?.dispose()
})
</script>

<template>
  <div>
    <div class="panel">
      <div class="panel-title">二次供水管控
        <span class="tip">异常单元 {{ abnormal }} 处 · 水箱液位/水质/消毒设备实时监控告警</span>
      </div>
      <div class="chart-row">
        <div>
          <div ref="statusEl" class="chart-box"></div>
        </div>
        <div>
          <div class="sub-title">告警阈值说明</div>
          <el-table :data="[
            { item: '水箱液位', rule: '<20% 断水风险（高）；>95% 溢流风险（低）' },
            { item: '水箱浊度', rule: '>1NTU 超标（中）' },
            { item: '水箱余氯', rule: '<0.05mg/L 消毒不达标（中）' },
            { item: '消毒设备', rule: '故障/停用 立即检修（高）' }
          ]" size="small" border>
            <el-table-column prop="item" label="监测项" width="110" />
            <el-table-column prop="rule" label="告警规则" />
          </el-table>
        </div>
      </div>
    </div>

    <div class="panel">
      <div class="panel-title">小区二次供水单元台账</div>
      <div class="toolbar">
        <el-input v-model="query.keyword" placeholder="编号 / 小区 / 区域" clearable
                  style="width:200px" @keyup.enter="load" @clear="load" />
        <el-select v-model="query.status" placeholder="全部状态" clearable style="width:110px" @change="load">
          <el-option label="正常" value="正常" />
          <el-option label="告警" value="告警" />
        </el-select>
        <el-button type="primary" @click="load">查询</el-button>
      </div>

      <el-table :data="rows" v-loading="loading" size="small" border stripe>
        <el-table-column prop="code" label="单元编号" width="100" />
        <el-table-column prop="community" label="小区名称" min-width="180" />
        <el-table-column prop="district" label="区域" width="90" align="center" />
        <el-table-column prop="tank_count" label="水箱数" width="80" align="center" />
        <el-table-column label="液位(%)" width="85" align="right">
          <template #default="{ row }">
            <span :style="{ color: row.level_pct < 20 ? '#f56c6c' : (row.level_pct > 95 ? '#e6a23c' : '') }">
              {{ fmt(row.level_pct) }}
            </span>
          </template>
        </el-table-column>
        <el-table-column label="浊度(NTU)" width="90" align="right">
          <template #default="{ row }">
            <span :style="{ color: row.turbidity_ntu > 1 ? '#f56c6c' : '' }">{{ fmt(row.turbidity_ntu, 2) }}</span>
          </template>
        </el-table-column>
        <el-table-column label="余氯(mg/L)" width="95" align="right">
          <template #default="{ row }">
            <span :style="{ color: row.residual_cl < 0.05 ? '#f56c6c' : '' }">{{ fmt(row.residual_cl, 2) }}</span>
          </template>
        </el-table-column>
        <el-table-column label="消毒设备" width="90" align="center">
          <template #default="{ row }">
            <el-tag :type="row.disinfect_status === '正常' ? 'success' : 'danger'" size="small">{{ row.disinfect_status }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="last_check" label="最近检查" width="130" />
        <el-table-column label="状态" width="80" align="center">
          <template #default="{ row }">
            <el-tag :type="row.status === '正常' ? 'success' : 'danger'" size="small">{{ row.status }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="110" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" size="small" @click="openAdd(row)">上报数据</el-button>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <!-- 上报数据 -->
    <el-dialog v-model="addVisible" :title="`上报实时数据 · ${addTarget?.community ?? ''}`" width="480px" :close-on-click-modal="false">
      <el-form ref="addRef" :model="addForm" label-width="120px">
        <el-form-item label="水箱液位(%)">
          <el-input-number v-model="addForm.level_pct" :min="0" :max="100" :precision="1" :controls="false" style="width:100%" />
        </el-form-item>
        <el-form-item label="浊度(NTU)">
          <el-input-number v-model="addForm.turbidity_ntu" :min="0" :precision="2" :controls="false" style="width:100%" />
        </el-form-item>
        <el-form-item label="余氯(mg/L)">
          <el-input-number v-model="addForm.residual_cl" :min="0" :precision="2" :controls="false" style="width:100%" />
        </el-form-item>
        <el-form-item label="消毒设备状态">
          <el-radio-group v-model="addForm.disinfect_status">
            <el-radio label="正常">正常</el-radio>
            <el-radio label="故障">故障</el-radio>
            <el-radio label="停用">停用</el-radio>
          </el-radio-group>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="addVisible = false">取消</el-button>
        <el-button type="primary" :loading="adding" @click="submitAdd">提交并自动告警</el-button>
      </template>
    </el-dialog>
  </div>
</template>
