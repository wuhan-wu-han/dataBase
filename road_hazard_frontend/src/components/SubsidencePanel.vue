<script setup lang="ts">
import { nextTick, onBeforeUnmount, onMounted, reactive, ref } from 'vue'
import { ElMessage, type FormInstance } from 'element-plus'
import {
  addSubsRecord, getSubsHistory, getSubsOptions, getSubsPoints, getSubsStats
} from '../api'
import type { PointSummary, SubsidenceRecord } from '../types'
import { AXIS_STYLE, initChart, riskPieOption } from '../utils/chart'
import { fmt, riskTagType } from '../utils/format'

const emit = defineEmits<{ (e: 'changed'): void }>()

// ---------------- 点位列表 ----------------
const query = reactive({ keyword: '', district: '', risk_level: '' })
const points = ref<PointSummary[]>([])
const loading = ref(false)
const districts = ref<string[]>([])

async function load() {
  loading.value = true
  try {
    const d = await getSubsPoints({
      keyword: query.keyword || undefined, district: query.district || undefined,
      risk_level: query.risk_level || undefined
    })
    points.value = d.items
  } catch (e: any) {
    ElMessage.error('监测点加载失败：' + (e?.message || e))
  } finally {
    loading.value = false
  }
}
function search() { load() }
function reset() { query.keyword = ''; query.district = ''; query.risk_level = ''; load() }

// ---------------- 图表 ----------------
const riskEl = ref<HTMLElement>()
const trendEl = ref<HTMLElement>()
let riskChart: ReturnType<typeof initChart> | null = null
let trendChart: ReturnType<typeof initChart> | null = null

async function loadCharts() {
  try {
    const s = await getSubsStats()
    await nextTick()
    if (riskEl.value && !riskChart) riskChart = initChart(riskEl.value)
    if (trendEl.value && !trendChart) trendChart = initChart(trendEl.value)
    riskChart?.setOption(riskPieOption(s.by_risk, '监测点塌陷风险分布'))
    trendChart?.setOption({
      title: { text: '全网月度沉降趋势', left: 'center', textStyle: { fontSize: 13, color: '#303133' } },
      tooltip: { trigger: 'axis' },
      legend: { bottom: 0, data: ['平均单期沉降(mm)', '最大累计沉降(mm)'], textStyle: { fontSize: 11 } },
      grid: { left: 8, right: 12, top: 34, bottom: 30, containLabel: true },
      xAxis: { type: 'category', data: s.monthly.map(m => m.month), ...AXIS_STYLE },
      yAxis: [
        { type: 'value', name: 'mm/期', ...AXIS_STYLE },
        { type: 'value', name: 'mm', ...AXIS_STYLE }
      ],
      series: [
        { name: '平均单期沉降(mm)', type: 'bar', barMaxWidth: 22, data: s.monthly.map(m => m.avg_delta),
          itemStyle: { color: '#409eff', borderRadius: [4, 4, 0, 0] } },
        { name: '最大累计沉降(mm)', type: 'line', yAxisIndex: 1, smooth: true,
          data: s.monthly.map(m => m.max_cum), itemStyle: { color: '#f56c6c' } }
      ]
    })
  } catch (e) {
    console.error('沉降统计加载失败', e)
  }
}

function onResize() {
  riskChart?.resize(); trendChart?.resize(); histChart?.resize()
}

onMounted(async () => {
  districts.value = (await getSubsOptions().catch(() => null))?.districts || []
  load()
  loadCharts()
  window.addEventListener('resize', onResize)
})
onBeforeUnmount(() => {
  window.removeEventListener('resize', onResize)
  riskChart?.dispose(); trendChart?.dispose(); histChart?.dispose()
})

// ---------------- 历史记录弹窗 ----------------
const histVisible = ref(false)
const histPoint = ref<PointSummary | null>(null)
const histRecords = ref<SubsidenceRecord[]>([])
const histEl = ref<HTMLElement>()
let histChart: ReturnType<typeof initChart> | null = null

async function showHistory(p: PointSummary) {
  histPoint.value = p
  histVisible.value = true
  try {
    const d = await getSubsHistory(p.point_code)
    histRecords.value = d.records
    await nextTick()
    if (histEl.value) {
      histChart?.dispose()
      histChart = initChart(histEl.value)
      histChart.setOption({
        tooltip: { trigger: 'axis' },
        legend: { bottom: 0, data: ['本期沉降(mm)', '累计沉降(mm)'], textStyle: { fontSize: 11 } },
        grid: { left: 8, right: 12, top: 24, bottom: 30, containLabel: true },
        xAxis: { type: 'category', data: d.records.map(r => r.measured_at), ...AXIS_STYLE },
        yAxis: { type: 'value', name: 'mm', ...AXIS_STYLE },
        series: [
          { name: '本期沉降(mm)', type: 'bar', barMaxWidth: 20, data: d.records.map(r => r.delta_mm),
            itemStyle: { color: '#e6a23c', borderRadius: [4, 4, 0, 0] } },
          { name: '累计沉降(mm)', type: 'line', smooth: true, data: d.records.map(r => r.cumulative_mm),
            itemStyle: { color: '#f56c6c' }, areaStyle: { opacity: 0.08 } }
        ]
      })
    }
  } catch (e: any) {
    ElMessage.error('历史记录加载失败：' + (e?.message || e))
  }
}

// ---------------- 新增观测 ----------------
const recVisible = ref(false)
const recSaving = ref(false)
const recFormRef = ref<FormInstance>()
const recForm = reactive({
  point_code: '', road_name: '', district: '', measured_at: '', delta_mm: 1.0, source: '水准测量'
})
const recRules = {
  point_code: [{ required: true, message: '请输入监测点编号', trigger: 'blur' }],
  measured_at: [{ required: true, message: '请输入观测日期', trigger: 'blur' }]
}

function openRecord(p?: PointSummary) {
  Object.assign(recForm, {
    point_code: p?.point_code || '', road_name: p?.road_name || '', district: p?.district || '',
    measured_at: '', delta_mm: 1.0, source: '水准测量'
  })
  recVisible.value = true
}

async function saveRecord() {
  if (!recFormRef.value) return
  await recFormRef.value.validate(async valid => {
    if (!valid) return
    recSaving.value = true
    try {
      const r = await addSubsRecord({
        point_code: recForm.point_code,
        road_name: recForm.road_name || undefined,
        district: recForm.district || undefined,
        measured_at: recForm.measured_at, delta_mm: recForm.delta_mm, source: recForm.source
      })
      ElMessage.success(`已录入，${r.point_code} 累计沉降 ${r.cumulative_mm} mm`)
      recVisible.value = false
      load(); loadCharts(); emit('changed')
    } catch (e: any) {
      ElMessage.error(e?.response?.data?.detail || e?.message || '录入失败')
    } finally {
      recSaving.value = false
    }
  })
}
</script>

<template>
  <div>
    <div class="panel">
      <div class="panel-title">沉降监测分析</div>
      <div class="chart-row">
        <div ref="riskEl" class="chart-box"></div>
        <div ref="trendEl" class="chart-box"></div>
      </div>
    </div>

    <div class="panel">
      <div class="panel-title">监测点融合风险总览</div>
      <div class="toolbar">
        <el-input v-model="query.keyword" placeholder="点位 / 道路" clearable style="width:190px"
                  @keyup.enter="search" @clear="search" />
        <el-select v-model="query.district" placeholder="全部区域" clearable style="width:130px" @change="search">
          <el-option v-for="d in districts" :key="d" :label="d" :value="d" />
        </el-select>
        <el-select v-model="query.risk_level" placeholder="全部风险等级" clearable style="width:140px" @change="search">
          <el-option label="高风险" value="高风险" />
          <el-option label="中风险" value="中风险" />
          <el-option label="低风险" value="低风险" />
        </el-select>
        <el-button type="primary" @click="search">查询</el-button>
        <el-button @click="reset">重置</el-button>
        <div class="spacer"></div>
        <el-button type="primary" plain @click="openRecord()">+ 新增观测记录</el-button>
      </div>

      <el-table :data="points" v-loading="loading" size="small" border stripe>
        <el-table-column prop="point_code" label="点位编号" width="110" />
        <el-table-column label="道路 / 区域" min-width="140">
          <template #default="{ row }">{{ row.road_name }}<div style="font-size:11px;color:#909399">{{ row.district }}</div></template>
        </el-table-column>
        <el-table-column label="观测期数" width="90" align="center">
          <template #default="{ row }">{{ row.record_count }}</template>
        </el-table-column>
        <el-table-column label="最近观测" width="105">
          <template #default="{ row }">{{ row.latest_measured }}</template>
        </el-table-column>
        <el-table-column label="累计沉降(mm)" width="120" align="right">
          <template #default="{ row }"><b :style="{ color: row.cumulative_mm >= 50 ? '#f56c6c' : '' }">{{ fmt(row.cumulative_mm) }}</b></template>
        </el-table-column>
        <el-table-column label="速率(mm/月)" width="115" align="right">
          <template #default="{ row }">{{ fmt(row.rate_mm_month) }}</template>
        </el-table-column>
        <el-table-column label="趋势" width="130" align="center">
          <template #default="{ row }">
            <el-tag v-if="row.accelerating" type="danger" size="small">{{ row.trend }}</el-tag>
            <span v-else style="font-size:12px;color:#606266">{{ row.trend }}</span>
          </template>
        </el-table-column>
        <el-table-column label="风险等级" width="90" align="center">
          <template #default="{ row }">
            <el-tag :type="riskTagType(row.risk_level)" size="small">{{ row.risk_level }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="150" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" size="small" @click="showHistory(row)">历史</el-button>
            <el-button link type="primary" size="small" @click="openRecord(row)">新增观测</el-button>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <!-- 历史记录弹窗 -->
    <el-dialog v-model="histVisible" :title="`监测历史：${histPoint?.point_code || ''}（${histPoint?.road_name || ''}）`"
               width="760px">
      <div v-if="histPoint" style="margin-bottom:10px;font-size:13px;color:#606266">
        累计沉降 <b style="color:#f56c6c">{{ fmt(histPoint.cumulative_mm) }} mm</b>
        · 速率 {{ fmt(histPoint.rate_mm_month) }} mm/月
        · <el-tag :type="riskTagType(histPoint.risk_level)" size="small">{{ histPoint.risk_level }}</el-tag>
        {{ histPoint.trend }}
      </div>
      <div ref="histEl" style="height:230px"></div>
      <el-table :data="histRecords" size="small" border max-height="260" style="margin-top:10px">
        <el-table-column prop="measured_at" label="观测日期" width="110" />
        <el-table-column label="本期沉降(mm)" align="right">
          <template #default="{ row }">{{ fmt(row.delta_mm) }}</template>
        </el-table-column>
        <el-table-column label="累计沉降(mm)" align="right">
          <template #default="{ row }">{{ fmt(row.cumulative_mm) }}</template>
        </el-table-column>
        <el-table-column prop="source" label="数据来源" width="120" />
      </el-table>
    </el-dialog>

    <!-- 新增观测弹窗 -->
    <el-dialog v-model="recVisible" title="新增沉降观测记录" width="500px" :close-on-click-modal="false">
      <el-form ref="recFormRef" :model="recForm" :rules="recRules" label-width="110px">
        <el-form-item label="监测点编号" prop="point_code">
          <el-input v-model="recForm.point_code" placeholder="如：CJ-CD-01（新点自动建档）" />
        </el-form-item>
        <el-form-item label="道路名称">
          <el-input v-model="recForm.road_name" placeholder="新监测点必填" />
        </el-form-item>
        <el-form-item label="所属区域">
          <el-select v-model="recForm.district" placeholder="新监测点必填" clearable style="width:100%">
            <el-option v-for="d in districts" :key="d" :label="d" :value="d" />
          </el-select>
        </el-form-item>
        <el-form-item label="观测日期" prop="measured_at">
          <el-input v-model="recForm.measured_at" placeholder="yyyy-MM-dd" />
        </el-form-item>
        <el-form-item label="本期沉降(mm)">
          <el-input-number v-model="recForm.delta_mm" :precision="1" style="width:100%" />
        </el-form-item>
        <el-form-item label="数据来源">
          <el-radio-group v-model="recForm.source">
            <el-radio label="水准测量">水准测量</el-radio>
            <el-radio label="InSAR 校核">InSAR 校核</el-radio>
          </el-radio-group>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="recVisible = false">取消</el-button>
        <el-button type="primary" :loading="recSaving" @click="saveRecord">录入并自动累计</el-button>
      </template>
    </el-dialog>
  </div>
</template>
