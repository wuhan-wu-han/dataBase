<script setup lang="ts">
import { nextTick, onBeforeUnmount, onMounted, reactive, ref, watch } from 'vue'
import { ElMessage, ElMessageBox, type FormInstance } from 'element-plus'
import {
  closeOrder, dispatchOrder, getOrders, getOrderStats, reportOrder, verifyOrder
} from '../api'
import type { OrderDetail, OrderStats } from '../types'
import { initChart, pieOption } from '../utils/chart'
import { flowStatusTag, fmtTs, levelTagType } from '../utils/format'

const emit = defineEmits<{ (e: 'changed'): void }>()
const props = defineProps<{ active?: boolean }>()

// 切换到本页签时重新拉取，避免其它页签写入后数据陈旧
watch(() => props.active, v => { if (v) reload() })

const HANDLE_TYPES = ['维修', '更换', '现场核查', '公安报案']
const STATUSES = ['待派发', '处置中', '待核验', '已核验', '已闭环']

// ---------------- 列表 ----------------
const query = reactive({ status: '', handle_type: '', keyword: '', page: 1, page_size: 10 })
const total = ref(0)
const rows = ref<OrderDetail[]>([])
const loading = ref(false)

async function load() {
  loading.value = true
  try {
    const d = await getOrders({
      status: query.status || undefined, handle_type: query.handle_type || undefined,
      keyword: query.keyword || undefined, page: query.page, page_size: query.page_size
    })
    rows.value = d.items
    total.value = d.total
  } catch (e: any) {
    ElMessage.error('工单列表加载失败：' + (e?.message || e))
  } finally {
    loading.value = false
  }
}

function search() { query.page = 1; load() }
function reset() { query.status = ''; query.handle_type = ''; query.keyword = ''; search() }

// ---------------- 统计 ----------------
const stats = ref<OrderStats | null>(null)
const statusEl = ref<HTMLElement>()
let statusChart: ReturnType<typeof initChart> | null = null

async function loadStats() {
  try {
    stats.value = await getOrderStats()
    await nextTick()
    if (statusEl.value && !statusChart) statusChart = initChart(statusEl.value)
    const ordered = STATUSES
      .map(s => stats.value!.by_status.find(b => b.name === s))
      .filter(Boolean) as { name: string; value: number }[]
    statusChart?.setOption(pieOption(ordered, '工单状态分布'), true)
  } catch (e) {
    console.error('工单统计加载失败', e)
  }
}

function onResize() { statusChart?.resize() }

function reload() { load(); loadStats(); emit('changed') }

// ---------------- 派发 ----------------
const dispatchVisible = ref(false)
const dispatchRef = ref<FormInstance>()
const acting = ref(false)
const target = ref<OrderDetail | null>(null)
const dispatchForm = reactive({ assignee: '', handle_type: '维修' })
const dispatchRules = {
  assignee: [{ required: true, message: '请输入运维班组/负责人', trigger: 'blur' }],
  handle_type: [{ required: true, message: '请选择处置方式', trigger: 'change' }]
}

function openDispatch(row: OrderDetail) {
  target.value = row
  Object.assign(dispatchForm, { assignee: '', handle_type: row.handle_type || '维修' })
  dispatchVisible.value = true
}

async function submitDispatch() {
  if (!dispatchRef.value || !target.value) return
  await dispatchRef.value.validate(async valid => {
    if (!valid) return
    acting.value = true
    try {
      await dispatchOrder(target.value!.id, { ...dispatchForm })
      ElMessage.success(`工单 ${target.value!.order_code} 已派发至 ${dispatchForm.assignee}`)
      dispatchVisible.value = false
      reload()
    } catch (e: any) {
      ElMessage.error(e?.response?.data?.detail || e?.message || '派发失败')
    } finally {
      acting.value = false
    }
  })
}

// ---------------- 处置上报 ----------------
const reportVisible = ref(false)
const reportRef = ref<FormInstance>()
const reportForm = reactive({ report_info: '' })
const reportRules = {
  report_info: [{ required: true, min: 2, message: '请填写现场处置情况（不少于 2 字）', trigger: 'blur' }]
}

function openReport(row: OrderDetail) {
  target.value = row
  reportForm.report_info = ''
  reportVisible.value = true
}

async function submitReport() {
  if (!reportRef.value || !target.value) return
  await reportRef.value.validate(async valid => {
    if (!valid) return
    acting.value = true
    try {
      await reportOrder(target.value!.id, { report_info: reportForm.report_info })
      ElMessage.success('处置信息已上报，工单转入待核验')
      reportVisible.value = false
      reload()
    } catch (e: any) {
      ElMessage.error(e?.response?.data?.detail || e?.message || '上报失败')
    } finally {
      acting.value = false
    }
  })
}

// ---------------- 整改核验 ----------------
const verifyVisible = ref(false)
const verifyRef = ref<FormInstance>()
const verifyForm = reactive({ passed: true, verify_result: '' })
const verifyRules = {
  verify_result: [{ required: true, message: '请填写核验结论', trigger: 'blur' }]
}

function openVerify(row: OrderDetail) {
  target.value = row
  Object.assign(verifyForm, { passed: true, verify_result: '' })
  verifyVisible.value = true
}

async function submitVerify() {
  if (!verifyRef.value || !target.value) return
  await verifyRef.value.validate(async valid => {
    if (!valid) return
    acting.value = true
    try {
      await verifyOrder(target.value!.id, { ...verifyForm })
      ElMessage[verifyForm.passed ? 'success' : 'warning'](
        verifyForm.passed ? '核验通过，可执行闭环销号' : '核验不通过，工单已退回处置中'
      )
      verifyVisible.value = false
      reload()
    } catch (e: any) {
      ElMessage.error(e?.response?.data?.detail || e?.message || '核验失败')
    } finally {
      acting.value = false
    }
  })
}

// ---------------- 闭环销号 ----------------
async function doClose(row: OrderDetail) {
  try {
    await ElMessageBox.confirm(
      `确认对工单 ${row.order_code} 执行闭环销号归档？关联告警将同步闭环，井盖状态复位为正常。`,
      '隐患闭环销号', { type: 'warning', confirmButtonText: '确认销号', cancelButtonText: '取消' }
    )
  } catch {
    return
  }
  try {
    await closeOrder(row.id)
    ElMessage.success('已闭环销号归档')
    reload()
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || e?.message || '销号失败')
  }
}

// ---------------- 流程详情 ----------------
const drawerVisible = ref(false)
const detailRow = ref<OrderDetail | null>(null)

function openDetail(row: OrderDetail) {
  detailRow.value = row
  drawerVisible.value = true
}

watch([dispatchVisible, reportVisible, verifyVisible], vs => {
  if (vs.some(Boolean)) nextTick(() => {
    dispatchRef.value?.clearValidate(); reportRef.value?.clearValidate(); verifyRef.value?.clearValidate()
  })
})

onMounted(() => {
  load()
  loadStats()
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
      <div class="panel-title">闭环处置效能<span class="tip">告警 → 派发 → 上报 → 核验 → 销号归档</span></div>
      <div class="chart-row">
        <div ref="statusEl" class="chart-box"></div>
        <div>
          <div class="stat-cards" style="grid-template-columns:repeat(2,1fr);margin-bottom:0">
            <div class="stat-card">
              <div class="label">工单总数</div>
              <div class="value">{{ stats?.total ?? '-' }}</div>
              <div class="extra">由告警自动生成</div>
            </div>
            <div class="stat-card">
              <div class="label">已闭环工单</div>
              <div class="value">{{ stats?.closed ?? '-' }}</div>
              <div class="extra">完成销号归档</div>
            </div>
            <div class="stat-card">
              <div class="label">隐患闭环率</div>
              <div class="value" :class="{ warn: (stats?.close_rate_pct ?? 0) < 60 }">
                {{ stats?.close_rate_pct ?? '-' }}%
              </div>
              <div class="extra">已闭环 / 工单总数</div>
            </div>
            <div class="stat-card">
              <div class="label">平均闭环时长</div>
              <div class="value">{{ stats?.avg_close_hours ?? '-' }}</div>
              <div class="extra">小时（生成 → 销号）</div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <div class="panel">
      <div class="panel-title">运维处置工单</div>
      <div class="toolbar">
        <el-input v-model="query.keyword" placeholder="工单号 / 井盖编号 / 位置" clearable
                  style="width:210px" @keyup.enter="search" @clear="search" />
        <el-select v-model="query.status" placeholder="全部工单状态" clearable style="width:140px" @change="search">
          <el-option v-for="s in STATUSES" :key="s" :label="s" :value="s" />
        </el-select>
        <el-select v-model="query.handle_type" placeholder="全部处置方式" clearable style="width:140px" @change="search">
          <el-option v-for="h in HANDLE_TYPES" :key="h" :label="h" :value="h" />
        </el-select>
        <el-button type="primary" @click="search">查询</el-button>
        <el-button @click="reset">重置</el-button>
      </div>

      <el-table :data="rows" v-loading="loading" size="small" border stripe>
        <el-table-column prop="order_code" label="工单编号" width="165" />
        <el-table-column label="关联告警" min-width="180">
          <template #default="{ row }">
            <div>{{ row.alarm_code || '-' }}</div>
            <div class="cell-sub">
              {{ row.alarm_type || '无' }}
              <el-tag v-if="row.alarm_level" :type="levelTagType(row.alarm_level)" size="small"
                      style="margin-left:4px">{{ row.alarm_level }}</el-tag>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="井盖 / 位置" min-width="200">
          <template #default="{ row }">{{ row.code }}<div class="cell-sub">{{ row.location }}</div></template>
        </el-table-column>
        <el-table-column label="处置方式" width="95" align="center">
          <template #default="{ row }">{{ row.handle_type || '待定' }}</template>
        </el-table-column>
        <el-table-column label="责任班组" width="110" show-overflow-tooltip>
          <template #default="{ row }">{{ row.assignee || '-' }}</template>
        </el-table-column>
        <el-table-column label="工单状态" width="90" align="center">
          <template #default="{ row }">
            <el-tag :type="flowStatusTag(row.status)" size="small">{{ row.status }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="派发时间" width="130">
          <template #default="{ row }">{{ fmtTs(row.dispatch_ts) }}</template>
        </el-table-column>
        <el-table-column label="操作" width="180" fixed="right">
          <template #default="{ row }">
            <el-button v-if="row.status === '待派发'" link type="primary" size="small"
                       @click="openDispatch(row)">派发</el-button>
            <el-button v-if="row.status === '处置中'" link type="primary" size="small"
                       @click="openReport(row)">处置上报</el-button>
            <el-button v-if="row.status === '待核验'" link type="warning" size="small"
                       @click="openVerify(row)">整改核验</el-button>
            <el-button v-if="row.status === '已核验'" link type="success" size="small"
                       @click="doClose(row)">闭环销号</el-button>
            <el-button link type="primary" size="small" @click="openDetail(row)">流程详情</el-button>
          </template>
        </el-table-column>
      </el-table>

      <div style="margin-top:12px;display:flex;justify-content:flex-end">
        <el-pagination v-model:current-page="query.page" v-model:page-size="query.page_size"
                       :total="total" :page-sizes="[10, 20, 50]" layout="total, sizes, prev, pager, next"
                       @current-change="load" @size-change="search" />
      </div>
    </div>

    <!-- 派发 -->
    <el-dialog v-model="dispatchVisible" :title="`派发工单 · ${target?.order_code ?? ''}`" width="480px"
               :close-on-click-modal="false">
      <el-alert type="info" :closable="false" show-icon style="margin-bottom:12px"
                :title="`${target?.alarm_type ?? ''}（${target?.alarm_level ?? ''}）· ${target?.alarm_detail ?? ''}`" />
      <el-form ref="dispatchRef" :model="dispatchForm" :rules="dispatchRules" label-width="90px">
        <el-form-item label="责任班组" prop="assignee">
          <el-input v-model="dispatchForm.assignee" placeholder="如：市政一处抢修班 / 张三" />
        </el-form-item>
        <el-form-item label="处置方式" prop="handle_type">
          <el-select v-model="dispatchForm.handle_type" style="width:100%">
            <el-option v-for="h in HANDLE_TYPES" :key="h" :label="h" :value="h" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dispatchVisible = false">取消</el-button>
        <el-button type="primary" :loading="acting" @click="submitDispatch">确认派发</el-button>
      </template>
    </el-dialog>

    <!-- 处置上报 -->
    <el-dialog v-model="reportVisible" :title="`现场处置上报 · ${target?.order_code ?? ''}`" width="520px"
               :close-on-click-modal="false">
      <el-form ref="reportRef" :model="reportForm" :rules="reportRules" label-width="90px">
        <el-form-item label="处置情况" prop="report_info">
          <el-input v-model="reportForm.report_info" type="textarea" :rows="4"
                    placeholder="现场处置过程、使用材料、恢复情况等" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="reportVisible = false">取消</el-button>
        <el-button type="primary" :loading="acting" @click="submitReport">提交并转核验</el-button>
      </template>
    </el-dialog>

    <!-- 核验 -->
    <el-dialog v-model="verifyVisible" :title="`整改结果核验 · ${target?.order_code ?? ''}`" width="520px"
               :close-on-click-modal="false">
      <div class="sub-title">上报内容</div>
      <div style="font-size:12px;line-height:1.7;margin-bottom:12px">{{ target?.report_info || '-' }}</div>
      <el-form ref="verifyRef" :model="verifyForm" :rules="verifyRules" label-width="90px">
        <el-form-item label="核验结论">
          <el-radio-group v-model="verifyForm.passed">
            <el-radio :value="true">通过（可销号）</el-radio>
            <el-radio :value="false">不通过（退回处置）</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="核验意见" prop="verify_result">
          <el-input v-model="verifyForm.verify_result" type="textarea" :rows="3"
                    placeholder="如：现场复测井盖安装平整，无松动，同意销号" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="verifyVisible = false">取消</el-button>
        <el-button :type="verifyForm.passed ? 'primary' : 'warning'" :loading="acting" @click="submitVerify">
          提交核验结果
        </el-button>
      </template>
    </el-dialog>

    <!-- 流程详情 -->
    <el-drawer v-model="drawerVisible" size="560px"
               :title="`处置流程 · ${detailRow?.order_code ?? ''}`">
      <template v-if="detailRow">
        <div class="sub-title">隐患信息</div>
        <div class="kv">
          <div class="row"><span class="k">井盖编号</span><span>{{ detailRow.code }}</span></div>
          <div class="row"><span class="k">工单状态</span>
            <el-tag :type="flowStatusTag(detailRow.status)" size="small">{{ detailRow.status }}</el-tag>
          </div>
          <div class="row"><span class="k">告警编号</span><span>{{ detailRow.alarm_code || '-' }}</span></div>
          <div class="row"><span class="k">告警类型</span><span>{{ detailRow.alarm_type || '-' }}</span></div>
        </div>
        <div style="font-size:12px;margin-top:8px">{{ detailRow.location }}</div>
        <div class="cell-sub" style="margin-top:4px">{{ detailRow.road_name }} · {{ detailRow.district }}</div>

        <div class="sub-title">闭环流程时间线</div>
        <el-timeline style="padding-left:4px">
          <el-timeline-item type="danger" :timestamp="fmtTs(detailRow.created_ts)" placement="top">
            <b>隐患告警产生</b>
            <div class="cell-sub">{{ detailRow.alarm_detail || '监测数据超阈值自动告警' }}</div>
          </el-timeline-item>
          <el-timeline-item :type="detailRow.dispatch_ts ? 'primary' : 'info'"
                            :timestamp="fmtTs(detailRow.dispatch_ts)" placement="top">
            <b>工单派发</b>
            <div class="cell-sub">
              {{ detailRow.assignee ? `${detailRow.assignee} · ${detailRow.handle_type}` : '尚未派发' }}
            </div>
          </el-timeline-item>
          <el-timeline-item :type="detailRow.report_ts ? 'primary' : 'info'"
                            :timestamp="fmtTs(detailRow.report_ts)" placement="top">
            <b>现场处置上报</b>
            <div class="cell-sub">{{ detailRow.report_info || '尚未上报' }}</div>
          </el-timeline-item>
          <el-timeline-item :type="detailRow.verify_ts ? (detailRow.status === '已闭环' || detailRow.status === '已核验' ? 'success' : 'warning') : 'info'"
                            :timestamp="fmtTs(detailRow.verify_ts)" placement="top">
            <b>整改结果核验</b>
            <div class="cell-sub">{{ detailRow.verify_result || '尚未核验' }}</div>
          </el-timeline-item>
          <el-timeline-item :type="detailRow.close_ts ? 'success' : 'info'"
                            :timestamp="fmtTs(detailRow.close_ts)" placement="top">
            <b>隐患闭环销号归档</b>
            <div class="cell-sub">{{ detailRow.close_ts ? '告警与井盖状态已同步复位' : '尚未销号' }}</div>
          </el-timeline-item>
        </el-timeline>
      </template>
    </el-drawer>
  </div>
</template>
