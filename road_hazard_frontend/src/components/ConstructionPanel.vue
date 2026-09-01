<script setup lang="ts">
import { nextTick, onBeforeUnmount, onMounted, reactive, ref, watch } from 'vue'
import { ElMessage, type FormInstance } from 'element-plus'
import {
  createConstruction, getConstructionOptions, getConstructionStats, getConstructions
} from '../api'
import type { Construction } from '../types'
import { barOption, initChart, riskPieOption } from '../utils/chart'
import { fmt, riskTagType } from '../utils/format'

const emit = defineEmits<{ (e: 'changed'): void }>()

// ---------------- 列表 ----------------
const query = reactive({ keyword: '', district: '', risk_level: '', work_type: '', page: 1, page_size: 10 })
const total = ref(0)
const rows = ref<Construction[]>([])
const loading = ref(false)
const options = ref({ districts: [] as string[], work_types: [] as string[] })

async function load() {
  loading.value = true
  try {
    const d = await getConstructions({
      keyword: query.keyword || undefined, district: query.district || undefined,
      risk_level: query.risk_level || undefined, work_type: query.work_type || undefined,
      page: query.page, page_size: query.page_size
    })
    rows.value = d.items
    total.value = d.total
  } catch (e: any) {
    ElMessage.error('评估档案加载失败：' + (e?.message || e))
  } finally {
    loading.value = false
  }
}
function search() { query.page = 1; load() }
function reset() {
  query.keyword = ''; query.district = ''; query.risk_level = ''; query.work_type = ''
  search()
}

// ---------------- 图表 ----------------
const riskEl = ref<HTMLElement>()
const workEl = ref<HTMLElement>()
let riskChart: ReturnType<typeof initChart> | null = null
let workChart: ReturnType<typeof initChart> | null = null

async function loadCharts() {
  try {
    const s = await getConstructionStats()
    await nextTick()
    if (riskEl.value && !riskChart) riskChart = initChart(riskEl.value)
    if (workEl.value && !workChart) workChart = initChart(workEl.value)
    riskChart?.setOption(riskPieOption(s.by_risk, '施工项目风险等级分布'))
    workChart?.setOption(barOption(s.by_work_type, '#8e7cc3'))
  } catch (e) {
    console.error('施工统计加载失败', e)
  }
}

function onResize() { riskChart?.resize(); workChart?.resize() }

onMounted(async () => {
  const opt = await getConstructionOptions().catch(() => null)
  if (opt) options.value = { districts: opt.districts, work_types: opt.work_types }
  load()
  loadCharts()
  window.addEventListener('resize', onResize)
})
onBeforeUnmount(() => {
  window.removeEventListener('resize', onResize)
  riskChart?.dispose(); workChart?.dispose()
})

// ---------------- 详情抽屉 ----------------
const drawerVisible = ref(false)
const detail = ref<Construction | null>(null)
function showDetail(row: Construction) { detail.value = row; drawerVisible.value = true }

// ---------------- 新增评估 ----------------
const dialogVisible = ref(false)
const saving = ref(false)
const formRef = ref<FormInstance>()
const form = reactive({
  project_name: '', construction_unit: '', road_name: '', district: '', work_type: '',
  excavation_depth: undefined as number | undefined, distance_to_pipe: undefined as number | undefined,
  start_date: '', plan_days: undefined as number | undefined, measures: '', assessor: '', assessed_at: ''
})
const rules = {
  project_name: [{ required: true, message: '请输入项目名称', trigger: 'blur' }],
  construction_unit: [{ required: true, message: '请输入施工单位', trigger: 'blur' }],
  road_name: [{ required: true, message: '请输入道路名称', trigger: 'blur' }],
  district: [{ required: true, message: '请选择区域', trigger: 'change' }],
  work_type: [{ required: true, message: '请选择工法', trigger: 'change' }],
  excavation_depth: [{ required: true, message: '请输入开挖/作业深度', trigger: 'blur' }],
  distance_to_pipe: [{ required: true, message: '请输入距管线距离', trigger: 'blur' }]
}

function openCreate() {
  Object.assign(form, {
    project_name: '', construction_unit: '', road_name: '', district: '', work_type: '',
    excavation_depth: undefined, distance_to_pipe: undefined,
    start_date: '', plan_days: undefined, measures: '', assessor: '', assessed_at: ''
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
      const r = await createConstruction(payload)
      ElMessage.success(
        `评估完成：${r.risk_level}（综合 ${r.overall_score} 分 = 土体 ${r.soil_score} + 管网 ${r.pipe_score}）`)
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
      <div class="panel-title">施工风险分析</div>
      <div class="chart-row">
        <div ref="riskEl" class="chart-box"></div>
        <div>
          <div style="font-size:12px;color:#909399;text-align:center;margin-bottom:4px">工法分布（项）</div>
          <div ref="workEl" class="chart-box"></div>
        </div>
      </div>
    </div>

    <div class="panel">
      <div class="panel-title">施工影响评估档案</div>
      <div class="toolbar">
        <el-input v-model="query.keyword" placeholder="项目 / 道路 / 施工单位" clearable
                  style="width:210px" @keyup.enter="search" @clear="search" />
        <el-select v-model="query.district" placeholder="全部区域" clearable style="width:130px" @change="search">
          <el-option v-for="d in options.districts" :key="d" :label="d" :value="d" />
        </el-select>
        <el-select v-model="query.work_type" placeholder="全部工法" clearable style="width:140px" @change="search">
          <el-option v-for="w in options.work_types" :key="w" :label="w" :value="w" />
        </el-select>
        <el-select v-model="query.risk_level" placeholder="全部风险等级" clearable style="width:140px" @change="search">
          <el-option label="高风险" value="高风险" />
          <el-option label="中风险" value="中风险" />
          <el-option label="低风险" value="低风险" />
        </el-select>
        <el-button type="primary" @click="search">查询</el-button>
        <el-button @click="reset">重置</el-button>
        <div class="spacer"></div>
        <el-button type="primary" plain @click="openCreate">+ 新增施工评估</el-button>
      </div>

      <el-table :data="rows" v-loading="loading" size="small" border stripe>
        <el-table-column prop="project_name" label="项目名称" min-width="200" show-overflow-tooltip />
        <el-table-column label="道路 / 区域" min-width="130">
          <template #default="{ row }">{{ row.road_name }}<div style="font-size:11px;color:#909399">{{ row.district }}</div></template>
        </el-table-column>
        <el-table-column prop="work_type" label="工法" width="95" align="center" />
        <el-table-column label="深度(m)" width="85" align="right">
          <template #default="{ row }">{{ fmt(row.excavation_depth) }}</template>
        </el-table-column>
        <el-table-column label="距管线(m)" width="95" align="right">
          <template #default="{ row }">{{ fmt(row.distance_to_pipe) }}</template>
        </el-table-column>
        <el-table-column label="土体风险" width="90" align="center">
          <template #default="{ row }">{{ row.soil_score }}</template>
        </el-table-column>
        <el-table-column label="管网风险" width="90" align="center">
          <template #default="{ row }">{{ row.pipe_score }}</template>
        </el-table-column>
        <el-table-column label="综合评分" width="90" align="center">
          <template #default="{ row }"><b>{{ row.overall_score }}</b></template>
        </el-table-column>
        <el-table-column label="风险等级" width="90" align="center">
          <template #default="{ row }">
            <el-tag :type="riskTagType(row.risk_level)" size="small">{{ row.risk_level }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="start_date" label="计划开工" width="100" />
        <el-table-column label="操作" width="80" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" size="small" @click="showDetail(row)">详情</el-button>
          </template>
        </el-table-column>
      </el-table>

      <div style="margin-top:12px;display:flex;justify-content:flex-end">
        <el-pagination v-model:current-page="query.page" v-model:page-size="query.page_size"
                       :total="total" :page-sizes="[10, 20, 50]" layout="total, sizes, prev, pager, next"
                       @current-change="load" @size-change="search" />
      </div>
    </div>

    <!-- 详情抽屉 -->
    <el-drawer v-model="drawerVisible" :title="`评估档案：${detail?.project_name || ''}`" size="420px">
      <el-descriptions v-if="detail" :column="1" border size="small">
        <el-descriptions-item label="施工单位">{{ detail.construction_unit }}</el-descriptions-item>
        <el-descriptions-item label="道路 / 区域">{{ detail.road_name }} / {{ detail.district }}</el-descriptions-item>
        <el-descriptions-item label="工法">{{ detail.work_type }}</el-descriptions-item>
        <el-descriptions-item label="开挖/作业深度">{{ fmt(detail.excavation_depth) }} m</el-descriptions-item>
        <el-descriptions-item label="距最近管线">{{ fmt(detail.distance_to_pipe) }} m</el-descriptions-item>
        <el-descriptions-item label="计划开工">{{ detail.start_date || '-' }}</el-descriptions-item>
        <el-descriptions-item label="计划工期">{{ detail.plan_days ? detail.plan_days + ' 天' : '-' }}</el-descriptions-item>
        <el-descriptions-item label="土体风险评分">{{ detail.soil_score }} / 100</el-descriptions-item>
        <el-descriptions-item label="管网风险评分">{{ detail.pipe_score }} / 100</el-descriptions-item>
        <el-descriptions-item label="综合评分">
          <b style="font-size:15px">{{ detail.overall_score }}</b> / 100
          <el-tag :type="riskTagType(detail.risk_level)" size="small" style="margin-left:8px">{{ detail.risk_level }}</el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="保护措施">{{ detail.measures || '-' }}</el-descriptions-item>
        <el-descriptions-item label="评估人 / 日期">{{ detail.assessor || '-' }} / {{ detail.assessed_at || '-' }}</el-descriptions-item>
      </el-descriptions>
    </el-drawer>

    <!-- 新增评估弹窗 -->
    <el-dialog v-model="dialogVisible" title="新增施工影响评估" width="560px" :close-on-click-modal="false">
      <el-form ref="formRef" :model="form" :rules="rules" label-width="120px">
        <el-form-item label="项目名称" prop="project_name">
          <el-input v-model="form.project_name" placeholder="如：XX 路雨污分流改造工程" />
        </el-form-item>
        <el-form-item label="施工单位" prop="construction_unit">
          <el-input v-model="form.construction_unit" />
        </el-form-item>
        <el-form-item label="道路名称" prop="road_name">
          <el-input v-model="form.road_name" />
        </el-form-item>
        <el-form-item label="所属区域" prop="district">
          <el-select v-model="form.district" placeholder="请选择" style="width:100%">
            <el-option v-for="d in options.districts" :key="d" :label="d" :value="d" />
          </el-select>
        </el-form-item>
        <el-form-item label="施工工法" prop="work_type">
          <el-select v-model="form.work_type" placeholder="请选择" style="width:100%">
            <el-option v-for="w in options.work_types" :key="w" :label="w" :value="w" />
          </el-select>
        </el-form-item>
        <el-form-item label="开挖深度(m)" prop="excavation_depth">
          <el-input-number v-model="form.excavation_depth" :min="0" :precision="1" style="width:100%" />
        </el-form-item>
        <el-form-item label="距管线距离(m)" prop="distance_to_pipe">
          <el-input-number v-model="form.distance_to_pipe" :min="0" :precision="1" style="width:100%" />
        </el-form-item>
        <el-form-item label="计划开工日期">
          <el-input v-model="form.start_date" placeholder="yyyy-MM-dd" />
        </el-form-item>
        <el-form-item label="计划工期(天)">
          <el-input-number v-model="form.plan_days" :min="1" style="width:100%" />
        </el-form-item>
        <el-form-item label="保护措施">
          <el-input v-model="form.measures" type="textarea" :rows="2" />
        </el-form-item>
        <el-form-item label="评估人">
          <el-input v-model="form.assessor" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="save">保存并自动评估</el-button>
      </template>
    </el-dialog>
  </div>
</template>
