<script setup lang="ts">
import { nextTick, onBeforeUnmount, onMounted, reactive, ref, watch } from 'vue'
import { ElMessage, type FormInstance } from 'element-plus'
import {
  createCavity, getCavities, getCavityOptions, getCavityStats, updateCavity
} from '../api'
import type { Cavity } from '../types'
import { barOption, initChart, riskPieOption } from '../utils/chart'
import { fmt, riskTagType, statusTagType } from '../utils/format'

const emit = defineEmits<{ (e: 'changed'): void }>()

// ---------------- 列表 ----------------
const query = reactive({ keyword: '', district: '', risk_level: '', status: '', page: 1, page_size: 10 })
const total = ref(0)
const rows = ref<Cavity[]>([])
const loading = ref(false)
const options = ref({ districts: [] as string[], statuses: [] as string[] })

async function load() {
  loading.value = true
  try {
    const d = await getCavities({
      keyword: query.keyword || undefined, district: query.district || undefined,
      risk_level: query.risk_level || undefined, status: query.status || undefined,
      page: query.page, page_size: query.page_size
    })
    rows.value = d.items
    total.value = d.total
  } catch (e: any) {
    ElMessage.error('空洞列表加载失败：' + (e?.message || e))
  } finally {
    loading.value = false
  }
}

function search() { query.page = 1; load() }
function reset() {
  query.keyword = ''; query.district = ''; query.risk_level = ''; query.status = ''
  search()
}

// ---------------- 图表 ----------------
const riskEl = ref<HTMLElement>()
const distEl = ref<HTMLElement>()
let riskChart: ReturnType<typeof initChart> | null = null
let distChart: ReturnType<typeof initChart> | null = null

async function loadCharts() {
  try {
    const s = await getCavityStats()
    await nextTick()
    if (riskEl.value && !riskChart) riskChart = initChart(riskEl.value)
    if (distEl.value && !distChart) distChart = initChart(distEl.value)
    riskChart?.setOption(riskPieOption(s.by_risk, '空洞风险等级分布'))
    distChart?.setOption(barOption(s.by_district, '#409eff'))
  } catch (e) {
    console.error('空洞统计加载失败', e)
  }
}

function onResize() { riskChart?.resize(); distChart?.resize() }

onMounted(async () => {
  const opt = await getCavityOptions().catch(() => null)
  if (opt) options.value = { districts: opt.districts, statuses: opt.statuses }
  load()
  loadCharts()
  window.addEventListener('resize', onResize)
})
onBeforeUnmount(() => {
  window.removeEventListener('resize', onResize)
  riskChart?.dispose(); distChart?.dispose()
})

// ---------------- 新增 / 编辑 ----------------
const dialogVisible = ref(false)
const editing = ref<Cavity | null>(null)
const formRef = ref<FormInstance>()
const saving = ref(false)
const form = reactive({
  road_name: '', district: '', location: '', radar_velocity: undefined as number | undefined,
  radar_area: undefined as number | undefined, leakage_index: 0, cavity_volume: 0,
  depth_m: undefined as number | undefined, status: '监测中', found_at: '', remark: ''
})
const rules = {
  road_name: [{ required: true, message: '请输入道路名称', trigger: 'blur' }],
  district: [{ required: true, message: '请选择所属区域', trigger: 'change' }],
  radar_area: [{ required: true, message: '请输入雷达异常区面积', trigger: 'blur' }]
}

function openCreate() {
  editing.value = null
  Object.assign(form, {
    road_name: '', district: '', location: '', radar_velocity: undefined,
    radar_area: undefined, leakage_index: 0, cavity_volume: 0,
    depth_m: undefined, status: '监测中', found_at: '', remark: ''
  })
  dialogVisible.value = true
}

function openEdit(row: Cavity) {
  editing.value = row
  Object.assign(form, {
    road_name: row.road_name, district: row.district, location: row.location || '',
    radar_velocity: row.radar_velocity ?? undefined, radar_area: row.radar_area,
    leakage_index: row.leakage_index, cavity_volume: row.cavity_volume,
    depth_m: row.depth_m ?? undefined, status: row.status,
    found_at: row.found_at || '', remark: row.remark || ''
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
      Object.keys(payload).forEach(k => {
        if (payload[k] === '' || payload[k] === undefined) delete payload[k]
      })
      if (editing.value) {
        const r = await updateCavity(editing.value.id, payload)
        ElMessage.success(`已更新，风险重算：${r.risk_level}（${r.risk_score} 分）`)
      } else {
        const r = await createCavity(payload)
        ElMessage.success(`已录入 ${r.code}，判定 ${r.risk_level}（${r.risk_score} 分）`)
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

watch(dialogVisible, v => { if (v) nextTick(() => formRef.value?.clearValidate()) })
</script>

<template>
  <div>
    <div class="panel">
      <div class="panel-title">空洞风险分布</div>
      <div class="chart-row">
        <div ref="riskEl" class="chart-box"></div>
        <div>
          <div style="font-size:12px;color:#909399;text-align:center;margin-bottom:4px">空洞区域分布（处）</div>
          <div ref="distEl" class="chart-box"></div>
        </div>
      </div>
    </div>

    <div class="panel">
      <div class="panel-title">地下空洞台账</div>
      <div class="toolbar">
        <el-input v-model="query.keyword" placeholder="编号 / 道路 / 位置" clearable
                  style="width:210px" @keyup.enter="search" @clear="search" />
        <el-select v-model="query.district" placeholder="全部区域" clearable style="width:130px" @change="search">
          <el-option v-for="d in options.districts" :key="d" :label="d" :value="d" />
        </el-select>
        <el-select v-model="query.risk_level" placeholder="全部风险等级" clearable style="width:140px" @change="search">
          <el-option label="高风险" value="高风险" />
          <el-option label="中风险" value="中风险" />
          <el-option label="低风险" value="低风险" />
        </el-select>
        <el-select v-model="query.status" placeholder="全部状态" clearable style="width:130px" @change="search">
          <el-option v-for="s in options.statuses" :key="s" :label="s" :value="s" />
        </el-select>
        <el-button type="primary" @click="search">查询</el-button>
        <el-button @click="reset">重置</el-button>
        <div class="spacer"></div>
        <el-button type="primary" plain @click="openCreate">+ 录入空洞数据</el-button>
      </div>

      <el-table :data="rows" v-loading="loading" size="small" border stripe>
        <el-table-column prop="code" label="编号" width="110" />
        <el-table-column label="道路 / 区域" min-width="130">
          <template #default="{ row }">{{ row.road_name }}<div style="font-size:11px;color:#909399">{{ row.district }}</div></template>
        </el-table-column>
        <el-table-column prop="location" label="具体位置" min-width="190" show-overflow-tooltip />
        <el-table-column label="雷达波速(m/s)" width="110" align="right">
          <template #default="{ row }">{{ fmt(row.radar_velocity, 0) }}</template>
        </el-table-column>
        <el-table-column label="异常面积(m²)" width="110" align="right">
          <template #default="{ row }">{{ fmt(row.radar_area) }}</template>
        </el-table-column>
        <el-table-column label="渗漏指数" width="90" align="right">
          <template #default="{ row }">{{ fmt(row.leakage_index) }}</template>
        </el-table-column>
        <el-table-column label="体积(m³)" width="90" align="right">
          <template #default="{ row }">{{ fmt(row.cavity_volume) }}</template>
        </el-table-column>
        <el-table-column label="风险评分" width="90" align="center">
          <template #default="{ row }"><b>{{ row.risk_score }}</b></template>
        </el-table-column>
        <el-table-column label="风险等级" width="90" align="center">
          <template #default="{ row }">
            <el-tag :type="riskTagType(row.risk_level)" size="small">{{ row.risk_level }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="90" align="center">
          <template #default="{ row }">
            <el-tag :type="statusTagType(row.status)" size="small">{{ row.status }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="found_at" label="发现日期" width="100" />
        <el-table-column label="操作" width="80" fixed="right">
          <template #default="{ row }">
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

    <!-- 新增 / 编辑弹窗 -->
    <el-dialog v-model="dialogVisible" :title="editing ? `编辑空洞 ${editing.code}` : '录入空洞探测数据'"
               width="560px" :close-on-click-modal="false">
      <el-form ref="formRef" :model="form" :rules="rules" label-width="110px">
        <el-form-item label="道路名称" prop="road_name">
          <el-input v-model="form.road_name" placeholder="如：建设大道" />
        </el-form-item>
        <el-form-item label="所属区域" prop="district">
          <el-select v-model="form.district" placeholder="请选择" style="width:100%">
            <el-option v-for="d in options.districts" :key="d" :label="d" :value="d" />
            <el-option label="城东区" value="城东区" v-if="!options.districts.length" />
          </el-select>
        </el-form-item>
        <el-form-item label="具体位置">
          <el-input v-model="form.location" placeholder="桩号 / 参照物描述" />
        </el-form-item>
        <el-form-item label="雷达波速(m/s)">
          <el-input-number v-model="form.radar_velocity" :min="0" :controls="false" style="width:100%" />
        </el-form-item>
        <el-form-item label="异常面积(m²)" prop="radar_area">
          <el-input-number v-model="form.radar_area" :min="0" :precision="1" :controls="false" style="width:100%" />
        </el-form-item>
        <el-form-item label="渗漏指数(0-10)">
          <el-input-number v-model="form.leakage_index" :min="0" :max="10" :precision="1" style="width:100%" />
        </el-form-item>
        <el-form-item label="空洞体积(m³)">
          <el-input-number v-model="form.cavity_volume" :min="0" :precision="1" style="width:100%" />
        </el-form-item>
        <el-form-item label="埋深(m)">
          <el-input-number v-model="form.depth_m" :min="0" :precision="1" :controls="false" style="width:100%" />
        </el-form-item>
        <el-form-item label="状态">
          <el-radio-group v-model="form.status">
            <el-radio label="监测中">监测中</el-radio>
            <el-radio label="处置中">处置中</el-radio>
            <el-radio label="已处置">已处置</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="发现日期">
          <el-input v-model="form.found_at" placeholder="yyyy-MM-dd" />
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="form.remark" type="textarea" :rows="2" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="save">
          {{ editing ? '保存并重新评估' : '录入并自动评估' }}
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>
