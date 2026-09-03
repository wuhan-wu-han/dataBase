<script setup lang="ts">
import { nextTick, onBeforeUnmount, onMounted, reactive, ref } from 'vue'
import { ElMessage, type FormInstance } from 'element-plus'
import {
  createHydrant, getHydrantEvents, getHydrantOptions, getHydrantStats, getHydrants,
  testHydrant, updateHydrant
} from '../api'
import type { Hydrant, HydrantEvent } from '../types'
import { barOption, initChart, pieOption } from '../utils/chart'
import { fmt, fmtTs } from '../utils/format'

const emit = defineEmits<{ (e: 'changed'): void }>()

// ---------------- 图表 ----------------
const statusEl = ref<HTMLElement>()
const distEl = ref<HTMLElement>()
let statusChart: ReturnType<typeof initChart> | null = null
let distChart: ReturnType<typeof initChart> | null = null

async function loadCharts() {
  try {
    const s = await getHydrantStats()
    await nextTick()
    if (statusEl.value && !statusChart) statusChart = initChart(statusEl.value)
    if (distEl.value && !distChart) distChart = initChart(distEl.value)
    statusChart?.setOption(pieOption(s.by_status, '消防栓状态分布'), true)
    distChart?.setOption(barOption(s.by_district, '#409eff'), true)
  } catch (e) {
    console.error('消防栓统计加载失败', e)
  }
}

function onResize() { statusChart?.resize(); distChart?.resize() }

// ---------------- 列表 ----------------
const query = reactive({ keyword: '', status: '', district: '', page: 1, page_size: 10 })
const total = ref(0)
const rows = ref<Hydrant[]>([])
const loading = ref(false)
const options = ref<{ districts: string[]; pipes: { id: number; code: string; name: string }[] }>({ districts: [], pipes: [] })

async function load() {
  loading.value = true
  try {
    const d = await getHydrants({
      keyword: query.keyword || undefined, status: query.status || undefined,
      district: query.district || undefined, page: query.page, page_size: query.page_size
    })
    rows.value = d.items
    total.value = d.total
  } catch (e: any) {
    ElMessage.error('消防栓列表加载失败：' + (e?.message || e))
  } finally {
    loading.value = false
  }
}

function search() { query.page = 1; load() }

// ---------------- 新增 / 编辑 ----------------
const dialogVisible = ref(false)
const editing = ref<Hydrant | null>(null)
const formRef = ref<FormInstance>()
const saving = ref(false)
const emptyForm = () => ({
  location: '', road_name: '', district: '', pipe_id: undefined as number | undefined,
  pressure_mpa: undefined as number | undefined, install_date: '', remark: ''
})
const form = reactive(emptyForm())
const rules = {
  location: [{ required: true, message: '请输入安装位置', trigger: 'blur' }]
}

function openCreate() {
  editing.value = null
  Object.assign(form, emptyForm())
  dialogVisible.value = true
}

function openEdit(row: Hydrant) {
  editing.value = row
  Object.assign(form, {
    location: row.location, road_name: row.road_name || '', district: row.district || '',
    pipe_id: row.pipe_id ?? undefined, pressure_mpa: row.pressure_mpa ?? undefined,
    install_date: row.install_date || '', remark: row.remark || ''
  })
  dialogVisible.value = true
}

async function save() {
  if (!formRef.value) return
  await formRef.value.validate(async valid => {
    if (!valid) return
    saving.value = true
    try {
      const payload: any = { ...form }
      Object.keys(payload).forEach(k => { if (payload[k] === '' || payload[k] === undefined) delete payload[k] })
      if (editing.value) {
        await updateHydrant(editing.value.id, payload)
        ElMessage.success(`消防栓 ${editing.value.code} 已更新`)
      } else {
        const r = await createHydrant(payload)
        ElMessage.success(`新建台账成功，编号 ${r.code}`)
      }
      dialogVisible.value = false
      load(); loadCharts(); emit('changed')
    } catch (e: any) {
      ElMessage.error(e?.response?.data?.detail || e?.message || '保存失败')
    } finally {
      saving.value = false
    }
  })
}

// ---------------- 出水测试 ----------------
const testVisible = ref(false)
const testTarget = ref<Hydrant | null>(null)
const testing = ref(false)
const testForm = reactive({
  pressure_mpa: undefined as number | undefined,
  test_flow_ls: undefined as number | undefined,
  note: ''
})

function openTest(row: Hydrant) {
  testTarget.value = row
  Object.assign(testForm, { pressure_mpa: row.pressure_mpa ?? undefined, test_flow_ls: row.test_flow_ls ?? undefined, note: '' })
  testVisible.value = true
}

async function submitTest() {
  if (!testTarget.value) return
  testing.value = true
  try {
    const r = await testHydrant(testTarget.value.id, { ...testForm })
    if (r.is_abnormal) {
      ElMessage.warning(`产生 ${r.alarms.length} 条告警：` + r.alarms.map(a => a.detail).join('；'))
    } else {
      ElMessage.success('出水测试正常')
    }
    testVisible.value = false
    load(); emit('changed')
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || e?.message || '测试失败')
  } finally {
    testing.value = false
  }
}

// ---------------- 事件记录 ----------------
const eventsVisible = ref(false)
const eventsTitle = ref('')
const eventRows = ref<HydrantEvent[]>([])

async function openEvents(row: Hydrant) {
  eventsTitle.value = `${row.code} · ${row.location}`
  eventsVisible.value = true
  try {
    const d = await getHydrantEvents(row.id)
    eventRows.value = d.items
  } catch (e: any) {
    ElMessage.error('事件加载失败：' + (e?.message || e))
  }
}

onMounted(async () => {
  const opt = await getHydrantOptions().catch(() => null)
  if (opt) options.value = opt
  load()
  loadCharts()
  window.addEventListener('resize', onResize)
})
onBeforeUnmount(() => {
  window.removeEventListener('resize', onResize)
  statusChart?.dispose(); distChart?.dispose()
})
</script>

<template>
  <div>
    <div class="panel">
      <div class="panel-title">消防栓专项统计<span class="tip">水压/出水监测 · 盗用异常告警 · 设备台账</span></div>
      <div class="chart-row">
        <div>
          <div ref="statusEl" class="chart-box"></div>
        </div>
        <div>
          <div class="chart-caption">区域分布（处）</div>
          <div ref="distEl" class="chart-box"></div>
        </div>
      </div>
    </div>

    <div class="panel">
      <div class="panel-title">消防栓设备台账</div>
      <div class="toolbar">
        <el-input v-model="query.keyword" placeholder="编号 / 位置 / 道路" clearable
                  style="width:200px" @keyup.enter="search" @clear="search" />
        <el-select v-model="query.district" placeholder="全部区域" clearable style="width:120px" @change="search">
          <el-option v-for="d in options.districts" :key="d" :label="d" :value="d" />
        </el-select>
        <el-select v-model="query.status" placeholder="全部状态" clearable style="width:110px" @change="search">
          <el-option label="正常" value="正常" />
          <el-option label="告警" value="告警" />
        </el-select>
        <el-button type="primary" @click="search">查询</el-button>
        <div class="spacer"></div>
        <el-button type="primary" plain @click="openCreate">+ 新增消防栓</el-button>
      </div>

      <el-table :data="rows" v-loading="loading" size="small" border stripe>
        <el-table-column prop="code" label="编号" width="90" />
        <el-table-column prop="location" label="安装位置" min-width="200" show-overflow-tooltip />
        <el-table-column label="道路 / 区域" min-width="140">
          <template #default="{ row }">{{ row.road_name }}<div class="cell-sub">{{ row.district }}</div></template>
        </el-table-column>
        <el-table-column prop="pipe_code" label="接入管道" width="100" />
        <el-table-column label="水压(MPa)" width="90" align="right">
          <template #default="{ row }">
            <span :style="{ color: row.pressure_mpa < 0.1 ? '#f56c6c' : '' }">{{ fmt(row.pressure_mpa, 2) }}</span>
          </template>
        </el-table-column>
        <el-table-column label="出水流量(L/s)" width="110" align="right">
          <template #default="{ row }">
            <span :style="{ color: row.test_flow_ls > 30 ? '#e6a23c' : '' }">{{ fmt(row.test_flow_ls) }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="install_date" label="安装日期" width="100" />
        <el-table-column label="状态" width="80" align="center">
          <template #default="{ row }">
            <el-tag :type="row.status === '正常' ? 'success' : 'danger'" size="small">{{ row.status }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="190" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" size="small" @click="openTest(row)">出水测试</el-button>
            <el-button link type="primary" size="small" @click="openEvents(row)">事件</el-button>
            <el-button link type="primary" size="small" @click="openEdit(row)">编辑</el-button>
          </template>
        </el-table-column>
      </el-table>

      <div style="margin-top:12px;display:flex;justify-content:flex-end">
        <el-pagination v-model:current-page="query.page" v-model:page-size="query.page_size"
                       :total="total" :page-sizes="[10, 20, 50]" layout="total, sizes, prev, pager, next"
                       @current-change="load" @size-change="search" />
      </div>
    </div>

    <!-- 新增 / 编辑 -->
    <el-dialog v-model="dialogVisible" :title="editing ? `编辑消防栓 ${editing.code}` : '新增消防栓台账'"
               width="560px" :close-on-click-modal="false">
      <el-form ref="formRef" :model="form" :rules="rules" label-width="100px">
        <el-form-item label="安装位置" prop="location">
          <el-input v-model="form.location" placeholder="如：建设大道与新华路交叉口东50m" />
        </el-form-item>
        <el-form-item label="所在道路">
          <el-input v-model="form.road_name" placeholder="如：建设大道" />
        </el-form-item>
        <el-form-item label="所属区域">
          <el-select v-model="form.district" filterable allow-create placeholder="可选择或输入" style="width:100%">
            <el-option v-for="d in options.districts" :key="d" :label="d" :value="d" />
          </el-select>
        </el-form-item>
        <el-form-item label="接入管道">
          <el-select v-model="form.pipe_id" filterable placeholder="请选择管道" style="width:100%">
            <el-option v-for="p in options.pipes" :key="p.id" :label="`${p.code}　${p.name}`" :value="p.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="水压(MPa)">
          <el-input-number v-model="form.pressure_mpa" :min="0" :max="1" :precision="2" :controls="false" style="width:100%" />
        </el-form-item>
        <el-form-item label="安装日期">
          <el-input v-model="form.install_date" placeholder="yyyy-MM-dd" />
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="form.remark" type="textarea" :rows="2" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="save">{{ editing ? '保存修改' : '建档' }}</el-button>
      </template>
    </el-dialog>

    <!-- 出水测试 -->
    <el-dialog v-model="testVisible" :title="`出水测试 · ${testTarget?.code ?? ''}`" width="460px" :close-on-click-modal="false">
      <el-form :model="testForm" label-width="120px">
        <el-form-item label="水压(MPa)">
          <el-input-number v-model="testForm.pressure_mpa" :min="0" :max="1" :precision="2" :controls="false" style="width:100%" />
        </el-form-item>
        <el-form-item label="出水流量(L/s)">
          <el-input-number v-model="testForm.test_flow_ls" :min="0" :precision="1" :controls="false" style="width:100%" />
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="testForm.note" placeholder="如：例行季度出水测试" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="testVisible = false">取消</el-button>
        <el-button type="primary" :loading="testing" @click="submitTest">提交并研判</el-button>
      </template>
    </el-dialog>

    <!-- 事件记录 -->
    <el-dialog v-model="eventsVisible" :title="`事件记录 · ${eventsTitle}`" width="640px">
      <el-table :data="eventRows" size="small" border>
        <el-table-column prop="type" label="类型" width="100" align="center" />
        <el-table-column label="时间" width="140">
          <template #default="{ row }">{{ fmtTs(row.ts) }}</template>
        </el-table-column>
        <el-table-column prop="detail" label="详情" min-width="220" show-overflow-tooltip />
        <el-table-column label="状态" width="90" align="center">
          <template #default="{ row }">
            <el-tag :type="row.status === '已处理' ? 'success' : 'warning'" size="small">{{ row.status }}</el-tag>
          </template>
        </el-table-column>
      </el-table>
    </el-dialog>
  </div>
</template>
