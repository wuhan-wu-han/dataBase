<script setup lang="ts">
import { nextTick, onBeforeUnmount, onMounted, reactive, ref, watch } from 'vue'
import { ElMessage, type FormInstance } from 'element-plus'
import {
  addRepair, createArchive, getArchiveDetail, getArchiveOptions, getArchives,
  getArchiveStats, updateArchive
} from '../api'
import type { Manhole, ManholeDetail } from '../types'
import { barOption, initChart, pieOption } from '../utils/chart'
import {
  damageTagType, flowStatusTag, fmt, fmtTs, levelTagType, manholeStatusTag, netStatusTag, today
} from '../utils/format'

const emit = defineEmits<{ (e: 'changed'): void }>()
const props = defineProps<{ active?: boolean }>()

// 切换到本页签时重新拉取，避免其它页签写入后数据陈旧
watch(() => props.active, v => { if (v) { load(); loadCharts() } })

// ---------------- 列表 ----------------
const query = reactive({
  keyword: '', district: '', type: '', status: '', owner_unit: '', page: 1, page_size: 10
})
const total = ref(0)
const rows = ref<Manhole[]>([])
const loading = ref(false)
const options = ref({ districts: [] as string[], owners: [] as string[], types: [] as string[], statuses: [] as string[] })

async function load() {
  loading.value = true
  try {
    const d = await getArchives({
      keyword: query.keyword || undefined, district: query.district || undefined,
      type: query.type || undefined, status: query.status || undefined,
      owner_unit: query.owner_unit || undefined, page: query.page, page_size: query.page_size
    })
    rows.value = d.items
    total.value = d.total
  } catch (e: any) {
    ElMessage.error('档案列表加载失败：' + (e?.message || e))
  } finally {
    loading.value = false
  }
}

function search() { query.page = 1; load() }
function reset() {
  query.keyword = ''; query.district = ''; query.type = ''; query.status = ''; query.owner_unit = ''
  search()
}

// ---------------- 图表 ----------------
const distEl = ref<HTMLElement>()
const statusEl = ref<HTMLElement>()
const ownerEl = ref<HTMLElement>()
let distChart: ReturnType<typeof initChart> | null = null
let statusChart: ReturnType<typeof initChart> | null = null
let ownerChart: ReturnType<typeof initChart> | null = null

async function loadCharts() {
  try {
    const s = await getArchiveStats()
    await nextTick()
    if (distEl.value && !distChart) distChart = initChart(distEl.value)
    if (statusEl.value && !statusChart) statusChart = initChart(statusEl.value)
    if (ownerEl.value && !ownerChart) ownerChart = initChart(ownerEl.value)
    distChart?.setOption(barOption(s.by_district, '#409eff'), true)
    statusChart?.setOption(pieOption(s.by_status, '井盖状态分布'), true)
    ownerChart?.setOption(barOption(s.by_owner, '#3aa272', true), true)
  } catch (e) {
    console.error('档案统计加载失败', e)
  }
}

function onResize() { distChart?.resize(); statusChart?.resize(); ownerChart?.resize() }

// ---------------- 新增 / 编辑 ----------------
const dialogVisible = ref(false)
const editing = ref<Manhole | null>(null)
const formRef = ref<FormInstance>()
const saving = ref(false)
const emptyForm = () => ({
  location: '', road_name: '', district: '', type: '雨水', owner_unit: '',
  material: '球墨铸铁', install_date: '', lat: undefined as number | undefined,
  lng: undefined as number | undefined, status: '正常', remark: ''
})
const form = reactive(emptyForm())
const rules = {
  location: [{ required: true, message: '请输入井盖安装位置', trigger: 'blur' }],
  road_name: [{ required: true, message: '请输入所在道路', trigger: 'blur' }],
  district: [{ required: true, message: '请选择所属区域', trigger: 'change' }],
  type: [{ required: true, message: '请选择井盖类型', trigger: 'change' }],
  owner_unit: [{ required: true, message: '请输入权属单位', trigger: 'blur' }]
}

function openCreate() {
  editing.value = null
  Object.assign(form, emptyForm())
  dialogVisible.value = true
}

function openEdit(row: Manhole) {
  editing.value = row
  Object.assign(form, {
    location: row.location, road_name: row.road_name, district: row.district,
    type: row.type, owner_unit: row.owner_unit, material: row.material || '',
    install_date: row.install_date || '', lat: row.lat ?? undefined, lng: row.lng ?? undefined,
    status: row.status, remark: row.remark || ''
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
        await updateArchive(editing.value.id, payload)
        ElMessage.success(`井盖档案 ${editing.value.code} 已更新`)
      } else {
        const r = await createArchive(payload)
        ElMessage.success(`新建档案成功，编号 ${r.code}`)
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

// ---------------- 档案详情 ----------------
const drawerVisible = ref(false)
const detail = ref<ManholeDetail | null>(null)
const detailLoading = ref(false)

async function openDetail(row: Manhole) {
  drawerVisible.value = true
  detailLoading.value = true
  detail.value = null
  try {
    detail.value = await getArchiveDetail(row.id)
  } catch (e: any) {
    ElMessage.error('档案详情加载失败：' + (e?.message || e))
  } finally {
    detailLoading.value = false
  }
}

// ---------------- 维修 / 更换登记 ----------------
const repairVisible = ref(false)
const repairTarget = ref<Manhole | null>(null)
const repairRef = ref<FormInstance>()
const repairSaving = ref(false)
const repairForm = reactive({
  type: '维修', date: today(), reason: '', detail: '',
  cost: undefined as number | undefined, operator: ''
})
const repairRules = {
  type: [{ required: true, message: '请选择类型', trigger: 'change' }],
  date: [{ required: true, message: '请输入日期', trigger: 'blur' }]
}

function openRepair(row: Manhole) {
  repairTarget.value = row
  Object.assign(repairForm, {
    type: '维修', date: today(), reason: '', detail: '', cost: undefined, operator: ''
  })
  repairVisible.value = true
}

async function saveRepair() {
  if (!repairRef.value || !repairTarget.value) return
  await repairRef.value.validate(async valid => {
    if (!valid) return
    repairSaving.value = true
    try {
      const payload: any = { ...repairForm }
      Object.keys(payload).forEach(k => { if (payload[k] === '' || payload[k] === undefined) delete payload[k] })
      await addRepair(repairTarget.value!.id, payload)
      ElMessage.success(`${payload.type}履历已登记${payload.type === '更换' ? '，井盖状态已复位为正常' : ''}`)
      repairVisible.value = false
      load(); loadCharts(); emit('changed')
      if (drawerVisible.value && detail.value) openDetail(detail.value.item)
    } catch (e: any) {
      ElMessage.error(e?.response?.data?.detail || e?.message || '登记失败')
    } finally {
      repairSaving.value = false
    }
  })
}

onMounted(async () => {
  const opt = await getArchiveOptions().catch(() => null)
  if (opt) options.value = opt
  load()
  loadCharts()
  window.addEventListener('resize', onResize)
})
onBeforeUnmount(() => {
  window.removeEventListener('resize', onResize)
  distChart?.dispose(); statusChart?.dispose(); ownerChart?.dispose()
})
</script>

<template>
  <div>
    <div class="panel">
      <div class="panel-title">井盖档案统计</div>
      <div class="chart-row three">
        <div>
          <div class="chart-caption">行政区域分布（座）</div>
          <div ref="distEl" class="chart-box"></div>
        </div>
        <div>
          <div ref="statusEl" class="chart-box"></div>
        </div>
        <div>
          <div class="chart-caption">权属单位分布（座）</div>
          <div ref="ownerEl" class="chart-box"></div>
        </div>
      </div>
    </div>

    <div class="panel">
      <div class="panel-title">一井一档电子台账<span class="tip">支持多条件组合查询与全生命周期履历追溯</span></div>
      <div class="toolbar">
        <el-input v-model="query.keyword" placeholder="编号 / 位置 / 道路" clearable
                  style="width:200px" @keyup.enter="search" @clear="search" />
        <el-select v-model="query.district" placeholder="全部区域" clearable style="width:120px" @change="search">
          <el-option v-for="d in options.districts" :key="d" :label="d" :value="d" />
        </el-select>
        <el-select v-model="query.type" placeholder="全部类型" clearable style="width:110px" @change="search">
          <el-option v-for="t in options.types" :key="t" :label="t" :value="t" />
        </el-select>
        <el-select v-model="query.status" placeholder="全部状态" clearable style="width:120px" @change="search">
          <el-option v-for="s in options.statuses" :key="s" :label="s" :value="s" />
        </el-select>
        <el-select v-model="query.owner_unit" placeholder="全部权属单位" clearable style="width:160px" @change="search">
          <el-option v-for="o in options.owners" :key="o" :label="o" :value="o" />
        </el-select>
        <el-button type="primary" @click="search">查询</el-button>
        <el-button @click="reset">重置</el-button>
        <div class="spacer"></div>
        <el-button type="primary" plain @click="openCreate">+ 新增井盖档案</el-button>
      </div>

      <el-table :data="rows" v-loading="loading" size="small" border stripe>
        <el-table-column prop="code" label="井盖编号" width="115" />
        <el-table-column prop="location" label="安装位置" min-width="200" show-overflow-tooltip />
        <el-table-column label="道路 / 区域" min-width="140">
          <template #default="{ row }">{{ row.road_name }}<div class="cell-sub">{{ row.district }}</div></template>
        </el-table-column>
        <el-table-column prop="type" label="类型" width="70" align="center" />
        <el-table-column prop="owner_unit" label="权属单位" min-width="140" show-overflow-tooltip />
        <el-table-column prop="material" label="材质" width="90" align="center" />
        <el-table-column prop="install_date" label="安装日期" width="100" />
        <el-table-column label="状态" width="85" align="center">
          <template #default="{ row }">
            <el-tag :type="manholeStatusTag(row.status)" size="small">{{ row.status }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="维修履历" width="85" align="center">
          <template #default="{ row }">{{ row.repairs ?? 0 }} 次</template>
        </el-table-column>
        <el-table-column label="累计告警" width="85" align="center">
          <template #default="{ row }">
            <span :style="{ color: (row.alarms ?? 0) > 0 ? '#e6a23c' : '' }">{{ row.alarms ?? 0 }} 条</span>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="180" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" size="small" @click="openDetail(row)">档案</el-button>
            <el-button link type="primary" size="small" @click="openEdit(row)">编辑</el-button>
            <el-button link type="primary" size="small" @click="openRepair(row)">维修登记</el-button>
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
    <el-dialog v-model="dialogVisible" :title="editing ? `编辑井盖档案 ${editing.code}` : '新增井盖档案'"
               width="600px" :close-on-click-modal="false">
      <el-form ref="formRef" :model="form" :rules="rules" label-width="100px">
        <el-form-item label="安装位置" prop="location">
          <el-input v-model="form.location" placeholder="如：建设大道与滨河路交叉口东 80m" />
        </el-form-item>
        <el-form-item label="所在道路" prop="road_name">
          <el-input v-model="form.road_name" placeholder="如：建设大道" />
        </el-form-item>
        <el-form-item label="所属区域" prop="district">
          <el-select v-model="form.district" placeholder="请选择" style="width:100%">
            <el-option v-for="d in options.districts" :key="d" :label="d" :value="d" />
          </el-select>
        </el-form-item>
        <el-form-item label="井盖类型" prop="type">
          <el-select v-model="form.type" placeholder="请选择" style="width:100%">
            <el-option v-for="t in options.types" :key="t" :label="t" :value="t" />
          </el-select>
        </el-form-item>
        <el-form-item label="权属单位" prop="owner_unit">
          <el-select v-model="form.owner_unit" filterable allow-create placeholder="可选择或直接输入" style="width:100%">
            <el-option v-for="o in options.owners" :key="o" :label="o" :value="o" />
          </el-select>
        </el-form-item>
        <el-form-item label="材质">
          <el-select v-model="form.material" placeholder="请选择" style="width:100%">
            <el-option label="球墨铸铁" value="球墨铸铁" />
            <el-option label="灰铸铁" value="灰铸铁" />
            <el-option label="复合材料" value="复合材料" />
            <el-option label="钢纤维混凝土" value="钢纤维混凝土" />
          </el-select>
        </el-form-item>
        <el-form-item label="安装日期">
          <el-input v-model="form.install_date" placeholder="yyyy-MM-dd" />
        </el-form-item>
        <el-form-item label="经纬度">
          <div style="display:flex;gap:8px;width:100%">
            <el-input-number v-model="form.lat" :precision="6" :controls="false" placeholder="纬度" style="flex:1" />
            <el-input-number v-model="form.lng" :precision="6" :controls="false" placeholder="经度" style="flex:1" />
          </div>
        </el-form-item>
        <el-form-item label="状态" v-if="editing">
          <el-radio-group v-model="form.status">
            <el-radio value="正常">正常</el-radio>
            <el-radio value="告警">告警</el-radio>
            <el-radio value="处置中">处置中</el-radio>
            <el-radio value="被盗">被盗</el-radio>
            <el-radio value="维修中">维修中</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="form.remark" type="textarea" :rows="2" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="save">
          {{ editing ? '保存修改' : '建档并生成编号' }}
        </el-button>
      </template>
    </el-dialog>

    <!-- 维修 / 更换登记 -->
    <el-dialog v-model="repairVisible" :title="`运维履历登记 · ${repairTarget?.code ?? ''}`"
               width="520px" :close-on-click-modal="false">
      <el-form ref="repairRef" :model="repairForm" :rules="repairRules" label-width="90px">
        <el-form-item label="类型" prop="type">
          <el-radio-group v-model="repairForm.type">
            <el-radio value="维修">维修</el-radio>
            <el-radio value="更换">更换</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="日期" prop="date">
          <el-input v-model="repairForm.date" placeholder="yyyy-MM-dd" />
        </el-form-item>
        <el-form-item label="原因">
          <el-input v-model="repairForm.reason" placeholder="如：井盖破损 / 被盗补装 / 沉降调平" />
        </el-form-item>
        <el-form-item label="处置详情">
          <el-input v-model="repairForm.detail" type="textarea" :rows="2" />
        </el-form-item>
        <el-form-item label="费用(元)">
          <el-input-number v-model="repairForm.cost" :min="0" :precision="2" :controls="false" style="width:100%" />
        </el-form-item>
        <el-form-item label="作业单位">
          <el-input v-model="repairForm.operator" placeholder="如：市政一处" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="repairVisible = false">取消</el-button>
        <el-button type="primary" :loading="repairSaving" @click="saveRepair">登记入档</el-button>
      </template>
    </el-dialog>

    <!-- 档案详情抽屉 -->
    <el-drawer v-model="drawerVisible" size="620px"
               :title="`一井一档 · ${detail?.item.code ?? '加载中'}`">
      <div v-loading="detailLoading">
        <template v-if="detail">
          <div class="sub-title">基础信息</div>
          <div class="kv">
            <div class="row"><span class="k">井盖编号</span><span>{{ detail.item.code }}</span></div>
            <div class="row"><span class="k">当前状态</span>
              <el-tag :type="manholeStatusTag(detail.item.status)" size="small">{{ detail.item.status }}</el-tag>
            </div>
            <div class="row"><span class="k">井盖类型</span><span>{{ detail.item.type }}</span></div>
            <div class="row"><span class="k">材质</span><span>{{ detail.item.material || '-' }}</span></div>
            <div class="row"><span class="k">权属单位</span><span>{{ detail.item.owner_unit }}</span></div>
            <div class="row"><span class="k">安装日期</span><span>{{ detail.item.install_date || '-' }}</span></div>
            <div class="row"><span class="k">所在道路</span><span>{{ detail.item.road_name }}</span></div>
            <div class="row"><span class="k">所属区域</span><span>{{ detail.item.district }}</span></div>
          </div>
          <div class="sub-title">安装位置</div>
          <div style="font-size:12px">{{ detail.item.location }}</div>
          <div class="cell-sub" style="margin-top:4px">
            经纬度：{{ detail.item.lat ?? '-' }}, {{ detail.item.lng ?? '-' }}
            <span v-if="detail.item.remark">　备注：{{ detail.item.remark }}</span>
          </div>

          <div class="sub-title">最新监测数据</div>
          <div v-if="detail.latest_monitor" class="kv">
            <div class="row"><span class="k">采集时间</span><span>{{ fmtTs(detail.latest_monitor.ts) }}</span></div>
            <div class="row"><span class="k">破损状态</span>
              <el-tag :type="damageTagType(detail.latest_monitor.damage)" size="small">
                {{ detail.latest_monitor.damage }}
              </el-tag>
            </div>
            <div class="row"><span class="k">倾角</span><span>{{ fmt(detail.latest_monitor.tilt_deg) }} °</span></div>
            <div class="row"><span class="k">位移</span><span>{{ fmt(detail.latest_monitor.displacement_mm) }} mm</span></div>
            <div class="row"><span class="k">井下水位</span><span>{{ fmt(detail.latest_monitor.water_level_cm) }} cm</span></div>
            <div class="row"><span class="k">有毒气体</span><span>{{ fmt(detail.latest_monitor.gas_ppm) }} ppm</span></div>
          </div>
          <div v-else style="font-size:12px;color:#909399">暂无监测数据</div>

          <div class="sub-title">防坠网</div>
          <div v-if="detail.net" class="kv">
            <div class="row"><span class="k">网编号</span><span>{{ detail.net.net_code }}</span></div>
            <div class="row"><span class="k">状态</span>
              <el-tag :type="netStatusTag(detail.net.net_status)" size="small">{{ detail.net.net_status }}</el-tag>
            </div>
            <div class="row"><span class="k">安装日期</span><span>{{ detail.net.install_date || '-' }}</span></div>
            <div class="row"><span class="k">承重</span><span>{{ detail.net.load_kg ?? '-' }} kg</span></div>
            <div class="row"><span class="k">上次检查</span><span>{{ detail.net.last_check || '-' }}</span></div>
            <div class="row"><span class="k">维修次数</span><span>{{ detail.net.repair_count }} 次</span></div>
          </div>
          <div v-else style="font-size:12px;color:#909399">未安装防坠网</div>

          <div class="sub-title">维修更换历史（{{ detail.repairs.length }} 条）</div>
          <el-table :data="detail.repairs" size="small" border>
            <el-table-column prop="type" label="类型" width="70" align="center" />
            <el-table-column prop="date" label="日期" width="100" />
            <el-table-column prop="reason" label="原因" min-width="120" show-overflow-tooltip />
            <el-table-column label="费用(元)" width="90" align="right">
              <template #default="{ row }">{{ fmt(row.cost, 0) }}</template>
            </el-table-column>
            <el-table-column prop="operator" label="作业单位" min-width="110" show-overflow-tooltip />
          </el-table>

          <div class="sub-title">近期告警记录（{{ detail.alarms.length }} 条）</div>
          <el-table :data="detail.alarms" size="small" border>
            <el-table-column prop="alarm_code" label="告警编号" width="150" />
            <el-table-column prop="type" label="类型" width="105" align="center" />
            <el-table-column label="等级" width="60" align="center">
              <template #default="{ row }">
                <el-tag :type="levelTagType(row.level)" size="small">{{ row.level }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column label="时间" width="125">
              <template #default="{ row }">{{ fmtTs(row.alarm_ts) }}</template>
            </el-table-column>
            <el-table-column label="状态" width="80" align="center">
              <template #default="{ row }">
                <el-tag :type="flowStatusTag(row.status)" size="small">{{ row.status }}</el-tag>
              </template>
            </el-table-column>
          </el-table>

          <div style="margin-top:16px">
            <el-button type="primary" plain size="small" @click="openRepair(detail.item)">+ 登记运维履历</el-button>
          </div>
        </template>
      </div>
    </el-drawer>
  </div>
</template>
