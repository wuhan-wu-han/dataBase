<script setup lang="ts">
import { nextTick, onBeforeUnmount, onMounted, reactive, ref, watch } from 'vue'
import { ElMessage, type FormInstance } from 'element-plus'
import {
  createNet, getArchiveOptions, getArchives, getNetDetail, getNets, getNetStats, maintainNet
} from '../api'
import type { NetDetail, NetStats, SafetyNet } from '../types'
import { initChart, pieOption } from '../utils/chart'
import { netStatusTag, today } from '../utils/format'

const emit = defineEmits<{ (e: 'changed'): void }>()
const props = defineProps<{ active?: boolean }>()

// 切换到本页签时重新拉取，避免其它页签写入后数据陈旧
watch(() => props.active, v => { if (v) reload() })

const NET_STATUSES = ['已安装', '破损', '已维修', '已更换']
const MAINTAIN_TYPES = ['破损登记', '维修', '更换']
const MATERIALS = ['聚乙烯', '尼龙', '不锈钢', '复合材料']

// ---------------- 列表 ----------------
const query = reactive({ net_status: '', district: '', keyword: '', page: 1, page_size: 10 })
const total = ref(0)
const rows = ref<SafetyNet[]>([])
const loading = ref(false)
const districts = ref<string[]>([])
const manholeOptions = ref<{ id: number; code: string; location: string }[]>([])

async function load() {
  loading.value = true
  try {
    const d = await getNets({
      net_status: query.net_status || undefined, district: query.district || undefined,
      keyword: query.keyword || undefined, page: query.page, page_size: query.page_size
    })
    rows.value = d.items
    total.value = d.total
  } catch (e: any) {
    ElMessage.error('防坠网台账加载失败：' + (e?.message || e))
  } finally {
    loading.value = false
  }
}

function search() { query.page = 1; load() }
function reset() { query.net_status = ''; query.district = ''; query.keyword = ''; search() }

const isOverdue = (d?: string) => !!d && d < today()

// ---------------- 统计 ----------------
const stats = ref<NetStats | null>(null)
const statusEl = ref<HTMLElement>()
let statusChart: ReturnType<typeof initChart> | null = null

async function loadStats() {
  try {
    stats.value = await getNetStats()
    await nextTick()
    if (statusEl.value && !statusChart) statusChart = initChart(statusEl.value)
    const ordered = NET_STATUSES
      .map(s => stats.value!.by_status.find(b => b.name === s))
      .filter(Boolean) as { name: string; value: number }[]
    statusChart?.setOption(pieOption(ordered, '防坠网状态分布'), true)
  } catch (e) {
    console.error('防坠网统计加载失败', e)
  }
}

function onResize() { statusChart?.resize() }
function reload() { load(); loadStats(); emit('changed') }

// ---------------- 安装登记 ----------------
const installVisible = ref(false)
const installRef = ref<FormInstance>()
const saving = ref(false)
const installForm = reactive({
  manhole_id: undefined as number | undefined, material: '聚乙烯',
  load_kg: 150, next_check: '', remark: ''
})
const installRules = { manhole_id: [{ required: true, message: '请选择井盖', trigger: 'change' }] }

function openInstall() {
  Object.assign(installForm, {
    manhole_id: undefined, material: '聚乙烯', load_kg: 150, next_check: '', remark: ''
  })
  installVisible.value = true
}

async function submitInstall() {
  if (!installRef.value) return
  await installRef.value.validate(async valid => {
    if (!valid) return
    saving.value = true
    try {
      const payload: any = { ...installForm }
      Object.keys(payload).forEach(k => { if (payload[k] === '' || payload[k] === undefined) delete payload[k] })
      const r = await createNet(payload)
      ElMessage.success(`安装登记成功，防坠网编号 ${r.net_code}`)
      installVisible.value = false
      reload()
    } catch (e: any) {
      ElMessage.error(e?.response?.data?.detail || e?.message || '登记失败')
    } finally {
      saving.value = false
    }
  })
}

// ---------------- 运维登记 ----------------
const maintainVisible = ref(false)
const maintainRef = ref<FormInstance>()
const maintainTarget = ref<SafetyNet | null>(null)
const maintainForm = reactive({ type: '维修', date: today(), detail: '', operator: '' })
const maintainRules = {
  type: [{ required: true, message: '请选择运维类型', trigger: 'change' }],
  date: [{ required: true, message: '请输入日期', trigger: 'blur' }]
}

function openMaintain(row: SafetyNet) {
  maintainTarget.value = row
  Object.assign(maintainForm, {
    type: row.net_status === '破损' ? '维修' : '破损登记', date: today(), detail: '', operator: ''
  })
  maintainVisible.value = true
}

async function submitMaintain() {
  if (!maintainRef.value || !maintainTarget.value) return
  await maintainRef.value.validate(async valid => {
    if (!valid) return
    saving.value = true
    try {
      const payload: any = { ...maintainForm }
      Object.keys(payload).forEach(k => { if (payload[k] === '' || payload[k] === undefined) delete payload[k] })
      const r = await maintainNet(maintainTarget.value!.id, payload)
      ElMessage.success(`运维记录已登记，防坠网状态：${r.net_status}`)
      maintainVisible.value = false
      reload()
      if (drawerVisible.value && detail.value?.item.id === maintainTarget.value!.id) {
        openDetail(maintainTarget.value!)
      }
    } catch (e: any) {
      ElMessage.error(e?.response?.data?.detail || e?.message || '登记失败')
    } finally {
      saving.value = false
    }
  })
}

// ---------------- 详情 ----------------
const drawerVisible = ref(false)
const detail = ref<NetDetail | null>(null)
const detailLoading = ref(false)

async function openDetail(row: SafetyNet) {
  drawerVisible.value = true
  detailLoading.value = true
  detail.value = null
  try {
    detail.value = await getNetDetail(row.id)
  } catch (e: any) {
    ElMessage.error('详情加载失败：' + (e?.message || e))
  } finally {
    detailLoading.value = false
  }
}

watch([installVisible, maintainVisible], vs => {
  if (vs.some(Boolean)) nextTick(() => { installRef.value?.clearValidate(); maintainRef.value?.clearValidate() })
})

onMounted(async () => {
  load()
  loadStats()
  window.addEventListener('resize', onResize)
  const [opt, arc] = await Promise.all([
    getArchiveOptions().catch(() => null),
    getArchives({ page: 1, page_size: 100 }).catch(() => null)
  ])
  if (opt) districts.value = opt.districts
  if (arc) manholeOptions.value = arc.items.map(m => ({ id: m.id, code: m.code, location: m.location }))
})
onBeforeUnmount(() => {
  window.removeEventListener('resize', onResize)
  statusChart?.dispose()
})
</script>

<template>
  <div>
    <div class="panel">
      <div class="panel-title">防坠网运维概况</div>
      <div class="chart-row">
        <div ref="statusEl" class="chart-box"></div>
        <div>
          <div class="stat-cards" style="grid-template-columns:repeat(2,1fr);margin-bottom:0">
            <div class="stat-card">
              <div class="label">在册防坠网</div>
              <div class="value">{{ stats ? stats.by_status.reduce((a, b) => a + b.value, 0) : '-' }}</div>
              <div class="extra">安装覆盖率 {{ stats?.cover_rate_pct ?? '-' }}%</div>
            </div>
            <div class="stat-card">
              <div class="label">破损待修</div>
              <div class="value danger">
                {{ stats?.by_status.find(b => b.name === '破损')?.value ?? 0 }}
              </div>
              <div class="extra">需及时维修或更换</div>
            </div>
            <div class="stat-card">
              <div class="label">超期未检查</div>
              <div class="value" :class="{ warn: (stats?.overdue_check ?? 0) > 0 }">
                {{ stats?.overdue_check ?? '-' }}
              </div>
              <div class="extra">下次检查日期已过期</div>
            </div>
            <div class="stat-card">
              <div class="label">运维记录</div>
              <div class="value">{{ stats?.maintain_total ?? '-' }}</div>
              <div class="extra">破损登记 / 维修 / 更换</div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <div class="panel">
      <div class="panel-title">防坠网台账<span class="tip">安装登记 → 定期检查 → 破损记录 → 维修更换</span></div>
      <div class="toolbar">
        <el-input v-model="query.keyword" placeholder="网编号 / 井盖编号 / 位置" clearable
                  style="width:210px" @keyup.enter="search" @clear="search" />
        <el-select v-model="query.net_status" placeholder="全部状态" clearable style="width:120px" @change="search">
          <el-option v-for="s in NET_STATUSES" :key="s" :label="s" :value="s" />
        </el-select>
        <el-select v-model="query.district" placeholder="全部区域" clearable style="width:120px" @change="search">
          <el-option v-for="d in districts" :key="d" :label="d" :value="d" />
        </el-select>
        <el-button type="primary" @click="search">查询</el-button>
        <el-button @click="reset">重置</el-button>
        <div class="spacer"></div>
        <el-button type="primary" plain @click="openInstall">+ 防坠网安装登记</el-button>
      </div>

      <el-table :data="rows" v-loading="loading" size="small" border stripe>
        <el-table-column prop="net_code" label="网编号" width="110" />
        <el-table-column label="关联井盖" width="115">
          <template #default="{ row }">{{ row.manhole_code }}</template>
        </el-table-column>
        <el-table-column label="安装位置" min-width="200" show-overflow-tooltip>
          <template #default="{ row }">
            {{ row.location }}<div class="cell-sub">{{ row.road_name }} · {{ row.district }}</div>
          </template>
        </el-table-column>
        <el-table-column prop="material" label="材质" width="90" align="center" />
        <el-table-column label="承载(kg)" width="85" align="right">
          <template #default="{ row }">{{ row.load_kg ?? '-' }}</template>
        </el-table-column>
        <el-table-column prop="install_date" label="安装日期" width="100" />
        <el-table-column label="状态" width="85" align="center">
          <template #default="{ row }">
            <el-tag :type="netStatusTag(row.net_status)" size="small">{{ row.net_status }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="last_check" label="上次检查" width="100" />
        <el-table-column label="下次检查" width="100">
          <template #default="{ row }">
            <span :style="{ color: isOverdue(row.next_check) ? '#f56c6c' : '' }">
              {{ row.next_check || '-' }}
              <el-tag v-if="isOverdue(row.next_check)" type="danger" size="small" effect="plain">超期</el-tag>
            </span>
          </template>
        </el-table-column>
        <el-table-column label="维修次数" width="85" align="center">
          <template #default="{ row }">{{ row.repair_count }} 次</template>
        </el-table-column>
        <el-table-column label="操作" width="150" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" size="small" @click="openDetail(row)">运维台账</el-button>
            <el-button link type="primary" size="small" @click="openMaintain(row)">登记</el-button>
          </template>
        </el-table-column>
      </el-table>

      <div style="margin-top:12px;display:flex;justify-content:flex-end">
        <el-pagination v-model:current-page="query.page" v-model:page-size="query.page_size"
                       :total="total" :page-sizes="[10, 20, 50]" layout="total, sizes, prev, pager, next"
                       @current-change="load" @size-change="search" />
      </div>
    </div>

    <!-- 安装登记 -->
    <el-dialog v-model="installVisible" title="防坠网安装登记" width="520px" :close-on-click-modal="false">
      <el-form ref="installRef" :model="installForm" :rules="installRules" label-width="110px">
        <el-form-item label="关联井盖" prop="manhole_id">
          <el-select v-model="installForm.manhole_id" filterable placeholder="请选择井盖" style="width:100%">
            <el-option v-for="m in manholeOptions" :key="m.id" :label="`${m.code}　${m.location}`" :value="m.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="网体材质">
          <el-select v-model="installForm.material" style="width:100%">
            <el-option v-for="m in MATERIALS" :key="m" :label="m" :value="m" />
          </el-select>
        </el-form-item>
        <el-form-item label="承载能力(kg)">
          <el-input-number v-model="installForm.load_kg" :min="0" :precision="0" style="width:100%" />
        </el-form-item>
        <el-form-item label="下次检查日期">
          <el-input v-model="installForm.next_check" placeholder="yyyy-MM-dd，留空默认三个月后" />
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="installForm.remark" type="textarea" :rows="2" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="installVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="submitInstall">登记并生成编号</el-button>
      </template>
    </el-dialog>

    <!-- 运维登记 -->
    <el-dialog v-model="maintainVisible" :title="`防坠网运维登记 · ${maintainTarget?.net_code ?? ''}`"
               width="500px" :close-on-click-modal="false">
      <el-form ref="maintainRef" :model="maintainForm" :rules="maintainRules" label-width="90px">
        <el-form-item label="运维类型" prop="type">
          <el-radio-group v-model="maintainForm.type">
            <el-radio v-for="t in MAINTAIN_TYPES" :key="t" :value="t">{{ t }}</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="日期" prop="date">
          <el-input v-model="maintainForm.date" placeholder="yyyy-MM-dd" />
        </el-form-item>
        <el-form-item label="作业详情">
          <el-input v-model="maintainForm.detail" type="textarea" :rows="3"
                    placeholder="如：网体局部断裂，已整张更换并复检承载" />
        </el-form-item>
        <el-form-item label="作业人">
          <el-input v-model="maintainForm.operator" placeholder="如：市政一处 李工" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="maintainVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="submitMaintain">登记入台账</el-button>
      </template>
    </el-dialog>

    <!-- 运维台账详情 -->
    <el-drawer v-model="drawerVisible" size="560px"
               :title="`防坠网运维台账 · ${detail?.item.net_code ?? '加载中'}`">
      <div v-loading="detailLoading">
        <template v-if="detail">
          <div class="sub-title">安装信息</div>
          <div class="kv">
            <div class="row"><span class="k">网编号</span><span>{{ detail.item.net_code }}</span></div>
            <div class="row"><span class="k">当前状态</span>
              <el-tag :type="netStatusTag(detail.item.net_status)" size="small">{{ detail.item.net_status }}</el-tag>
            </div>
            <div class="row"><span class="k">关联井盖</span><span>{{ detail.manhole?.code ?? '-' }}</span></div>
            <div class="row"><span class="k">安装位置</span><span>{{ detail.manhole?.location ?? '-' }}</span></div>
            <div class="row"><span class="k">网体材质</span><span>{{ detail.item.material || '-' }}</span></div>
            <div class="row"><span class="k">承载能力</span><span>{{ detail.item.load_kg ?? '-' }} kg</span></div>
            <div class="row"><span class="k">安装日期</span><span>{{ detail.item.install_date || '-' }}</span></div>
            <div class="row"><span class="k">维修次数</span><span>{{ detail.item.repair_count }} 次</span></div>
            <div class="row"><span class="k">上次检查</span>
              <span>{{ detail.item.last_check || '-' }}</span>
            </div>
            <div class="row"><span class="k">下次检查</span>
              <span :style="{ color: isOverdue(detail.item.next_check) ? '#f56c6c' : '' }">
                {{ detail.item.next_check || '-' }}{{ isOverdue(detail.item.next_check) ? '（超期）' : '' }}
              </span>
            </div>
          </div>
          <div v-if="detail.item.remark" class="cell-sub" style="margin-top:6px">备注：{{ detail.item.remark }}</div>

          <div class="sub-title">破损 / 维修 / 更换记录（{{ detail.maintains.length }} 条）</div>
          <el-table :data="detail.maintains" size="small" border>
            <el-table-column prop="type" label="类型" width="90" align="center" />
            <el-table-column prop="date" label="日期" width="100" />
            <el-table-column prop="detail" label="作业详情" min-width="180" show-overflow-tooltip />
            <el-table-column prop="operator" label="作业人" width="110" show-overflow-tooltip />
          </el-table>

          <div style="margin-top:16px">
            <el-button type="primary" plain size="small" @click="openMaintain(detail.item)">+ 登记运维记录</el-button>
          </div>
        </template>
      </div>
    </el-drawer>
  </div>
</template>
