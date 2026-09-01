<script setup lang="ts">
import { nextTick, onBeforeUnmount, onMounted, reactive, ref } from 'vue'
import * as echarts from 'echarts'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  createInventoryTask, fetchDiffList, fetchInventoryStats, fetchOptions,
  finishInventoryTask, handleDiffItem, patrolCheck, scanCheck
} from '../api'
import { PALETTE } from '../utils/chart'
import { fmtTime, HANDLE_TAG, TASK_STATUS_TAG } from '../utils/format'
import type { DiffItem, InventoryStats } from '../types'

const emit = defineEmits<{ (e: 'changed'): void }>()

const stats = ref<InventoryStats | null>(null)
const diffs = ref<DiffItem[]>([])
const regions = ref<string[]>([])
const activeTab = ref('tasks')

const elPie = ref<HTMLDivElement>()
let pie: echarts.ECharts | null = null

const taskForm = reactive({ method: '扫码盘点', scope_region: '', operator: '' })
const taskDialogVisible = ref(false)
const scanDialogVisible = ref(false)
const scanTarget = ref<number>(0)
const scanCode = ref('')

function errMsg(e: any) {
  return e?.response?.data?.detail || e?.message || '操作失败'
}

async function load() {
  const [st, df, opt] = await Promise.all([
    fetchInventoryStats(), fetchDiffList(), fetchOptions()
  ])
  stats.value = st
  diffs.value = df.diffs
  regions.value = opt.regions
  await nextTick()
  renderPie()
}

function renderPie() {
  if (!elPie.value || !stats.value) return
  if (!pie) pie = echarts.init(elPie.value)
  pie.setOption({
    color: PALETTE,
    tooltip: { trigger: 'item', formatter: '{b}：{c} 项（{d}%）' },
    legend: { bottom: 0, textStyle: { color: '#5a6b84', fontSize: 11 }, itemWidth: 10, itemHeight: 10 },
    series: [{
      type: 'pie',
      radius: ['34%', '58%'],
      center: ['50%', '42%'],
      data: stats.value.by_handle_status,
      itemStyle: { borderRadius: 4, borderColor: '#fff', borderWidth: 2 },
      label: { color: '#5a6b84', fontSize: 11, formatter: '{b}\n{c} 项' }
    }]
  }, true)
}

async function onCreateTask() {
  if (!taskForm.operator.trim()) {
    ElMessage.warning('请填写盘点人')
    return
  }
  try {
    const scope = taskForm.scope_region ? `${taskForm.scope_region}管段` : '全城管段'
    const r = await createInventoryTask({
      method: taskForm.method, scope,
      scope_region: taskForm.scope_region || undefined,
      operator: taskForm.operator.trim()
    })
    ElMessage.success(`任务已生成，共圈定 ${r.item_count} 项资产`)
    taskDialogVisible.value = false
    taskForm.operator = ''
    load()
    emit('changed')
  } catch (e) {
    ElMessage.error(errMsg(e))
  }
}

async function onPatrol(taskId: number) {
  try {
    const r = await patrolCheck(taskId)
    const text = Object.entries(r.results).map(([k, v]) => `${k} ${v}`).join('，')
    ElMessage.success(`巡检核对完成：共 ${r.checked} 项（${text}）`)
    load()
    emit('changed')
  } catch (e) {
    ElMessage.error(errMsg(e))
  }
}

async function onScanSubmit() {
  if (!scanCode.value.trim()) return
  try {
    const r = await scanCheck(scanTarget.value, scanCode.value.trim())
    ElMessage.success(`${r.asset_code} 核对结果：${r.check_result}`)
    scanCode.value = ''
    load()
    emit('changed')
  } catch (e) {
    ElMessage.error(errMsg(e))
  }
}

async function onFinish(taskId: number) {
  try {
    const r = await finishInventoryTask(taskId)
    ElMessageBox.alert(
      `盘点完成：账实一致 ${r.matched_count} 项，差异 ${r.diff_count} 项。`,
      '盘点结果', { confirmButtonText: '确定' }
    )
    load()
    emit('changed')
  } catch (e) {
    ElMessage.error(errMsg(e))
  }
}

async function onHandle(item: DiffItem, handle: string) {
  try {
    await handleDiffItem(item.id, handle, '大屏处理')
    ElMessage.success(`${item.asset_code} 已${handle}`)
    load()
    emit('changed')
  } catch (e) {
    ElMessage.error(errMsg(e))
  }
}

const onResize = () => pie?.resize()

onMounted(() => {
  load()
  window.addEventListener('resize', onResize)
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', onResize)
  pie?.dispose()
  pie = null
})
</script>

<template>
  <div class="panel">
    <div class="panel-title">资产盘点</div>
    <el-tabs v-model="activeTab">
      <el-tab-pane label="盘点任务" name="tasks">
        <div class="filter-bar">
          <span class="muted" style="font-size:13px;">
            账实一致率
            <b style="color:#52b788;font-size:16px;">{{ stats?.match_rate_pct ?? '--' }}%</b>
          </span>
          <span class="spacer"></span>
          <el-button type="primary" size="small" @click="taskDialogVisible = true">生成盘点任务</el-button>
        </div>
        <el-table :data="stats?.recent_tasks || []" size="small" height="290">
          <el-table-column prop="task_code" label="盘点单号" min-width="120" show-overflow-tooltip />
          <el-table-column prop="method" label="方式" width="76" />
          <el-table-column prop="scope" label="范围" width="84" show-overflow-tooltip />
          <el-table-column prop="operator" label="盘点人" width="64" />
          <el-table-column label="状态" width="92" align="center">
            <template #default="{ row }">
              <el-tag size="small" :type="TASK_STATUS_TAG[row.status] || 'info'">{{ row.status }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column label="一致/差异" width="80" align="center">
            <template #default="{ row }">
              {{ row.matched_count ?? '-' }}/{{ row.diff_count ?? '-' }}
            </template>
          </el-table-column>
          <el-table-column label="操作" width="150" fixed="right">
            <template #default="{ row }">
              <template v-if="row.status !== '已完成'">
                <el-button size="small" link type="primary" @click="onPatrol(row.id)">巡检</el-button>
                <el-button size="small" link type="primary"
                           @click="scanTarget = row.id; scanDialogVisible = true">扫码</el-button>
                <el-button size="small" link type="success" @click="onFinish(row.id)">完成</el-button>
              </template>
              <span v-else class="muted">{{ fmtTime(row.finished_ts) }}</span>
            </template>
          </el-table-column>
        </el-table>
      </el-tab-pane>

      <el-tab-pane label="差异处理" name="diffs">
        <div style="display:flex;gap:8px;">
          <div ref="elPie" style="width:46%;height:200px;"></div>
          <el-table :data="diffs.filter(d => d.handle_status === '待处理')" size="small" height="200">
            <el-table-column prop="asset_code" label="资产编号" min-width="120" show-overflow-tooltip />
            <el-table-column label="差异" width="80" align="center">
              <template #default="{ row }">
                <el-tag size="small" type="danger">{{ row.check_result }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column label="处理" width="140">
              <template #default="{ row }">
                <el-button size="small" link type="primary" @click="onHandle(row, '补录')">补录</el-button>
                <el-button size="small" link type="warning" @click="onHandle(row, '修正')">修正</el-button>
                <el-button size="small" link type="danger" @click="onHandle(row, '报废')">报废</el-button>
              </template>
            </el-table-column>
          </el-table>
        </div>
        <el-table :data="diffs.filter(d => d.handle_status !== '待处理')" size="small" height="150" class="mt8">
          <el-table-column prop="task_code" label="盘点单号" min-width="118" show-overflow-tooltip />
          <el-table-column prop="asset_code" label="资产编号" min-width="120" show-overflow-tooltip />
          <el-table-column label="差异" width="80" align="center">
            <template #default="{ row }">
              <el-tag size="small" type="warning">{{ row.check_result }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column label="处理状态" width="90" align="center">
            <template #default="{ row }">
              <el-tag size="small" :type="HANDLE_TAG[row.handle_status] || 'info'">{{ row.handle_status }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="remark" label="备注" min-width="100" show-overflow-tooltip />
        </el-table>
      </el-tab-pane>
    </el-tabs>

    <!-- 生成盘点任务 -->
    <el-dialog v-model="taskDialogVisible" title="生成盘点任务" width="420px" append-to-body>
      <el-form label-width="88px">
        <el-form-item label="盘点方式">
          <el-radio-group v-model="taskForm.method">
            <el-radio label="扫码盘点">扫码盘点</el-radio>
            <el-radio label="巡检盘点">巡检盘点</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="盘点范围">
          <el-select v-model="taskForm.scope_region" placeholder="全城管段" clearable style="width:100%">
            <el-option v-for="r in regions" :key="r" :label="r" :value="r" />
          </el-select>
        </el-form-item>
        <el-form-item label="盘点人">
          <el-input v-model="taskForm.operator" placeholder="请输入盘点人姓名" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="taskDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="onCreateTask">生成任务</el-button>
      </template>
    </el-dialog>

    <!-- 模拟扫码 -->
    <el-dialog v-model="scanDialogVisible" title="扫码盘点（模拟）" width="420px" append-to-body>
      <el-form label-width="88px">
        <el-form-item label="资产编号">
          <el-input v-model="scanCode" placeholder="输入/模拟扫描资产编号，如 GX-CD-2004-0001"
                    @keyup.enter="onScanSubmit" />
        </el-form-item>
        <div class="muted" style="font-size:12px;line-height:1.6;">
          编号在任务范围内 → 账实核对；台账不存在 → 记为盘盈；不在范围内会提示拒绝。
        </div>
      </el-form>
      <template #footer>
        <el-button @click="scanDialogVisible = false">关闭</el-button>
        <el-button type="primary" @click="onScanSubmit">核对</el-button>
      </template>
    </el-dialog>
  </div>
</template>
