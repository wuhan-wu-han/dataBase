<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, reactive, ref, watch } from 'vue'
import { ElMessage, type FormInstance } from 'element-plus'
import {
  addPolice, addTrack, getPolice, getTheftCases, getTracks, locateManhole, updatePolice
} from '../api'
import type { PoliceRecord, TheftCase, TrackPoint } from '../types'
import { initChart, trackOption } from '../utils/chart'
import { fmt, fmtTs, manholeStatusTag, policeStatusTag } from '../utils/format'

const emit = defineEmits<{ (e: 'changed'): void }>()
const props = defineProps<{ active?: boolean }>()

// 切换到本页签时重新拉取，避免其它页签写入后数据陈旧
watch(() => props.active, v => { if (v) reload() })

const POLICE_STATUSES = ['已报案', '已立案', '侦破中', '已追回']

// ---------------- 被盗案件 ----------------
const cases = ref<TheftCase[]>([])
const caseLoading = ref(false)

async function loadCases() {
  caseLoading.value = true
  try {
    cases.value = (await getTheftCases()).cases
  } catch (e: any) {
    ElMessage.error('被盗案件加载失败：' + (e?.message || e))
  } finally {
    caseLoading.value = false
  }
}

// ---------------- 公安联动记录 ----------------
const policeQuery = reactive({ status: '' })
const policeRows = ref<PoliceRecord[]>([])
const policeLoading = ref(false)

async function loadPolice() {
  policeLoading.value = true
  try {
    policeRows.value = (await getPolice({ status: policeQuery.status || undefined })).records
  } catch (e: any) {
    ElMessage.error('公安联动记录加载失败：' + (e?.message || e))
  } finally {
    policeLoading.value = false
  }
}

function reload() { loadCases(); loadPolice(); emit('changed') }

// ---------------- 轨迹回放 ----------------
const trackVisible = ref(false)
const trackTitle = ref('')
const trackPoints = ref<TrackPoint[]>([])
const trackEl = ref<HTMLElement>()
let trackChart: ReturnType<typeof initChart> | null = null
const cursor = ref(0)
const playing = ref(false)
let timer: ReturnType<typeof setInterval> | null = null

const trackLabels = computed(() => trackPoints.value.map(p => `${fmtTs(p.ts)}${p.note ? ' · ' + p.note : ''}`))

function renderTrack() {
  trackChart?.setOption(trackOption(
    trackPoints.value.map((p, i) => ({ lng: p.lng, lat: p.lat, label: trackLabels.value[i] })),
    cursor.value
  ), true)
}

async function openTrack(row: TheftCase) {
  trackTitle.value = `${row.code} · ${row.location}`
  trackVisible.value = true
  cursor.value = 0
  stopPlay()
  try {
    const d = await getTracks(row.manhole_id)
    trackPoints.value = d.tracks
    await nextTick()
    if (trackEl.value && !trackChart) trackChart = initChart(trackEl.value)
    renderTrack()
    setTimeout(() => trackChart?.resize(), 60)
  } catch (e: any) {
    ElMessage.error('轨迹加载失败：' + (e?.message || e))
  }
}

function step(delta: number) {
  const n = trackPoints.value.length
  if (!n) return
  cursor.value = Math.min(n - 1, Math.max(0, cursor.value + delta))
  renderTrack()
}

function startPlay() {
  if (trackPoints.value.length < 2) return
  if (cursor.value >= trackPoints.value.length - 1) cursor.value = 0
  playing.value = true
  timer = setInterval(() => {
    if (cursor.value >= trackPoints.value.length - 1) { stopPlay(); return }
    cursor.value += 1
    renderTrack()
  }, 900)
}

function stopPlay() {
  playing.value = false
  if (timer) { clearInterval(timer); timer = null }
}

function onCursorChange(v: number) { cursor.value = v; renderTrack() }

function closeTrack() {
  stopPlay()
  trackChart?.dispose()
  trackChart = null
}

// ---------------- 定位追踪 ----------------
const locateVisible = ref(false)
const locateInfo = ref<any>(null)

async function openLocate(row: TheftCase) {
  try {
    locateInfo.value = await locateManhole(row.manhole_id)
    locateVisible.value = true
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || e?.message || '定位失败')
  }
}

// ---------------- 上报轨迹点 ----------------
const trackFormVisible = ref(false)
const trackFormRef = ref<FormInstance>()
const trackFormTarget = ref<TheftCase | null>(null)
const saving = ref(false)
const trackForm = reactive({
  lat: undefined as number | undefined, lng: undefined as number | undefined,
  speed_kmh: undefined as number | undefined, note: ''
})
const trackRules = {
  lat: [{ required: true, message: '请输入纬度', trigger: 'blur' }],
  lng: [{ required: true, message: '请输入经度', trigger: 'blur' }]
}

function openTrackForm(row: TheftCase) {
  trackFormTarget.value = row
  Object.assign(trackForm, { lat: undefined, lng: undefined, speed_kmh: undefined, note: '' })
  trackFormVisible.value = true
}

async function submitTrack() {
  if (!trackFormRef.value || !trackFormTarget.value) return
  await trackFormRef.value.validate(async valid => {
    if (!valid) return
    saving.value = true
    try {
      const payload: any = { manhole_id: trackFormTarget.value!.manhole_id, ...trackForm }
      Object.keys(payload).forEach(k => { if (payload[k] === '' || payload[k] === undefined) delete payload[k] })
      await addTrack(payload)
      ElMessage.success('轨迹点已保存，可用于回放与定位')
      trackFormVisible.value = false
      loadCases()
    } catch (e: any) {
      ElMessage.error(e?.response?.data?.detail || e?.message || '上报失败')
    } finally {
      saving.value = false
    }
  })
}

// ---------------- 公安报案 / 进展 ----------------
const policeVisible = ref(false)
const policeRef = ref<FormInstance>()
const policeTarget = ref<TheftCase | null>(null)
const policeForm = reactive({ police_unit: '', contact: '', status: '已报案', result: '' })
const policeRules = {
  police_unit: [{ required: true, message: '请输入受理公安机关', trigger: 'blur' }],
  contact: [{ required: true, message: '请输入报案联系人/电话', trigger: 'blur' }]
}

function openPolice(row: TheftCase) {
  policeTarget.value = row
  Object.assign(policeForm, { police_unit: '高新区分局刑侦大队', contact: '', status: '已报案', result: '' })
  policeVisible.value = true
}

async function submitPolice() {
  if (!policeRef.value || !policeTarget.value) return
  await policeRef.value.validate(async valid => {
    if (!valid) return
    saving.value = true
    try {
      const payload: any = {
        manhole_id: policeTarget.value!.manhole_id, alarm_id: policeTarget.value!.alarm_id,
        ...policeForm
      }
      Object.keys(payload).forEach(k => { if (payload[k] === '' || payload[k] === undefined) delete payload[k] })
      const r = await addPolice(payload)
      ElMessage.success(`报案成功，案件编号 ${r.case_no}`)
      policeVisible.value = false
      reload()
    } catch (e: any) {
      ElMessage.error(e?.response?.data?.detail || e?.message || '报案失败')
    } finally {
      saving.value = false
    }
  })
}

const progressVisible = ref(false)
const progressRef = ref<FormInstance>()
const progressTarget = ref<PoliceRecord | null>(null)
const progressForm = reactive({ status: '已立案', result: '' })

function openProgress(row: PoliceRecord) {
  progressTarget.value = row
  Object.assign(progressForm, { status: row.status, result: row.result || '' })
  progressVisible.value = true
}

async function submitProgress() {
  if (!progressTarget.value) return
  saving.value = true
  try {
    await updatePolice(progressTarget.value.id, progressForm.status, progressForm.result || undefined)
    ElMessage.success(progressForm.status === '已追回'
      ? '进展已更新，井盖状态转为维修中'
      : '公安处置进展已更新')
    progressVisible.value = false
    reload()
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || e?.message || '更新失败')
  } finally {
    saving.value = false
  }
}

onMounted(() => {
  loadCases()
  loadPolice()
})
onBeforeUnmount(() => {
  stopPlay()
  trackChart?.dispose()
})
</script>

<template>
  <div>
    <div class="panel">
      <div class="panel-title">被盗异动案件<span class="tip">位移 ≥ 30mm 自动判定为被盗异动，留存异动数据并支持轨迹回放与定位追踪</span></div>
      <el-table :data="cases" v-loading="caseLoading" size="small" border stripe>
        <el-table-column prop="alarm_code" label="告警编号" width="150" />
        <el-table-column label="井盖 / 位置" min-width="230">
          <template #default="{ row }">{{ row.code }}<div class="cell-sub">{{ row.location }}</div></template>
        </el-table-column>
        <el-table-column label="道路 / 区域" min-width="140">
          <template #default="{ row }">{{ row.road_name }}<div class="cell-sub">{{ row.district }}</div></template>
        </el-table-column>
        <el-table-column label="井盖状态" width="90" align="center">
          <template #default="{ row }">
            <el-tag :type="manholeStatusTag(row.status)" size="small">{{ row.status }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="异动时间" width="130">
          <template #default="{ row }">{{ fmtTs(row.alarm_ts) }}</template>
        </el-table-column>
        <el-table-column label="轨迹点" width="80" align="center">
          <template #default="{ row }">{{ row.track_points }} 个</template>
        </el-table-column>
        <el-table-column label="公安案件" width="150">
          <template #default="{ row }">
            <span v-if="row.case_no">{{ row.case_no }}</span>
            <span v-else class="cell-sub">未报案</span>
          </template>
        </el-table-column>
        <el-table-column label="办案进展" width="90" align="center">
          <template #default="{ row }">
            <el-tag v-if="row.police_status" :type="policeStatusTag(row.police_status)" size="small">
              {{ row.police_status }}
            </el-tag>
            <span v-else>-</span>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="250" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" size="small" @click="openTrack(row)">轨迹回放</el-button>
            <el-button link type="primary" size="small" @click="openLocate(row)">定位追踪</el-button>
            <el-button link type="primary" size="small" @click="openTrackForm(row)">上报轨迹</el-button>
            <el-button v-if="!row.case_no" link type="danger" size="small" @click="openPolice(row)">公安报案</el-button>
          </template>
        </el-table-column>
      </el-table>
      <div v-if="!caseLoading && !cases.length" class="cell-sub" style="text-align:center;padding:10px 0">
        暂无被盗异动案件
      </div>
    </div>

    <div class="panel">
      <div class="panel-title">公安联动处置记录</div>
      <div class="toolbar">
        <el-select v-model="policeQuery.status" placeholder="全部办案状态" clearable style="width:140px"
                   @change="loadPolice">
          <el-option v-for="s in POLICE_STATUSES" :key="s" :label="s" :value="s" />
        </el-select>
        <el-button type="primary" @click="loadPolice">查询</el-button>
        <div class="spacer"></div>
        <el-button @click="reload">刷新</el-button>
      </div>

      <el-table :data="policeRows" v-loading="policeLoading" size="small" border stripe>
        <el-table-column prop="case_no" label="案件编号" width="150" />
        <el-table-column label="井盖 / 位置" min-width="220">
          <template #default="{ row }">{{ row.code }}<div class="cell-sub">{{ row.location }}</div></template>
        </el-table-column>
        <el-table-column prop="police_unit" label="受理公安机关" min-width="170" show-overflow-tooltip />
        <el-table-column prop="contact" label="报案联系人" min-width="130" show-overflow-tooltip />
        <el-table-column label="报案时间" width="130">
          <template #default="{ row }">{{ fmtTs(row.report_ts) }}</template>
        </el-table-column>
        <el-table-column label="办案状态" width="90" align="center">
          <template #default="{ row }">
            <el-tag :type="policeStatusTag(row.status)" size="small">{{ row.status }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="result" label="处置结果" min-width="180" show-overflow-tooltip />
        <el-table-column label="操作" width="100" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" size="small" @click="openProgress(row)">更新进展</el-button>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <!-- 轨迹回放 -->
    <el-dialog v-model="trackVisible" :title="`异动轨迹回放 · ${trackTitle}`" width="820px" @closed="closeTrack">
      <div ref="trackEl" class="chart-box tall"></div>
      <div class="toolbar" style="margin-top:10px">
        <el-button size="small" :disabled="cursor <= 0" @click="step(-1)">上一点</el-button>
        <el-button size="small" type="primary" @click="playing ? stopPlay() : startPlay()">
          {{ playing ? '暂停' : '播放' }}
        </el-button>
        <el-button size="small" :disabled="cursor >= trackPoints.length - 1" @click="step(1)">下一点</el-button>
        <el-slider :model-value="cursor" :min="0" :max="Math.max(trackPoints.length - 1, 0)" :step="1"
                   :show-tooltip="false" style="flex:1;margin:0 12px" @input="onCursorChange" />
        <span class="cell-sub" style="min-width:120px;text-align:right">
          {{ cursor + 1 }} / {{ trackPoints.length }} 点
        </span>
      </div>
      <div class="sub-title">当前轨迹点</div>
      <div v-if="trackPoints[cursor]" class="kv">
        <div class="row"><span class="k">采集时间</span><span>{{ fmtTs(trackPoints[cursor].ts) }}</span></div>
        <div class="row"><span class="k">移动速度</span><span>{{ fmt(trackPoints[cursor].speed_kmh) }} km/h</span></div>
        <div class="row"><span class="k">经度</span><span>{{ trackPoints[cursor].lng }}</span></div>
        <div class="row"><span class="k">纬度</span><span>{{ trackPoints[cursor].lat }}</span></div>
      </div>
      <div class="sub-title">轨迹明细（{{ trackPoints.length }} 点）</div>
      <el-table :data="trackPoints" size="small" border max-height="200"
                :row-class-name="({ rowIndex }: { rowIndex: number }) => rowIndex === cursor ? 'current-row' : ''">
        <el-table-column label="#" width="50" align="center">
          <template #default="{ $index }">{{ $index + 1 }}</template>
        </el-table-column>
        <el-table-column label="时间" width="140">
          <template #default="{ row }">{{ fmtTs(row.ts) }}</template>
        </el-table-column>
        <el-table-column prop="lat" label="纬度" width="110" />
        <el-table-column prop="lng" label="经度" width="110" />
        <el-table-column label="速度(km/h)" width="100" align="right">
          <template #default="{ row }">{{ fmt(row.speed_kmh) }}</template>
        </el-table-column>
        <el-table-column prop="note" label="备注" min-width="150" show-overflow-tooltip />
      </el-table>
    </el-dialog>

    <!-- 定位追踪 -->
    <el-dialog v-model="locateVisible" title="井盖最新位置定位" width="440px">
      <template v-if="locateInfo">
        <div class="kv">
          <div class="row"><span class="k">井盖编号</span><span>{{ locateInfo.code }}</span></div>
          <div class="row"><span class="k">当前状态</span>
            <el-tag :type="manholeStatusTag(locateInfo.status)" size="small">{{ locateInfo.status }}</el-tag>
          </div>
          <div class="row"><span class="k">定位来源</span><span>{{ locateInfo.source }}</span></div>
          <div class="row"><span class="k">定位时间</span><span>{{ fmtTs(locateInfo.ts) }}</span></div>
          <div class="row"><span class="k">经度</span><span>{{ locateInfo.lng }}</span></div>
          <div class="row"><span class="k">纬度</span><span>{{ locateInfo.lat }}</span></div>
          <div class="row"><span class="k">移动速度</span><span>{{ fmt(locateInfo.speed_kmh) }} km/h</span></div>
          <div class="row"><span class="k">备注</span><span>{{ locateInfo.note || '-' }}</span></div>
        </div>
      </template>
      <template #footer>
        <el-button type="primary" @click="locateVisible = false">关闭</el-button>
      </template>
    </el-dialog>

    <!-- 上报轨迹点 -->
    <el-dialog v-model="trackFormVisible" :title="`上报异动轨迹点 · ${trackFormTarget?.code ?? ''}`"
               width="480px" :close-on-click-modal="false">
      <el-form ref="trackFormRef" :model="trackForm" :rules="trackRules" label-width="90px">
        <el-form-item label="纬度" prop="lat">
          <el-input-number v-model="trackForm.lat" :precision="6" :controls="false" style="width:100%" />
        </el-form-item>
        <el-form-item label="经度" prop="lng">
          <el-input-number v-model="trackForm.lng" :precision="6" :controls="false" style="width:100%" />
        </el-form-item>
        <el-form-item label="速度(km/h)">
          <el-input-number v-model="trackForm.speed_kmh" :min="0" :precision="1" :controls="false" style="width:100%" />
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="trackForm.note" placeholder="如：卡口抓拍 / 巡查发现" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="trackFormVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="submitTrack">保存轨迹点</el-button>
      </template>
    </el-dialog>

    <!-- 公安报案 -->
    <el-dialog v-model="policeVisible" :title="`公安联动报案 · ${policeTarget?.code ?? ''}`"
               width="500px" :close-on-click-modal="false">
      <el-alert type="warning" :closable="false" show-icon style="margin-bottom:12px"
                :title="`${policeTarget?.alarm_code ?? ''} 被盗异动 · ${policeTarget?.location ?? ''}`" />
      <el-form ref="policeRef" :model="policeForm" :rules="policeRules" label-width="110px">
        <el-form-item label="受理公安机关" prop="police_unit">
          <el-input v-model="policeForm.police_unit" placeholder="如：高新区分局刑侦大队" />
        </el-form-item>
        <el-form-item label="报案联系人" prop="contact">
          <el-input v-model="policeForm.contact" placeholder="姓名 / 联系电话" />
        </el-form-item>
        <el-form-item label="办案状态">
          <el-select v-model="policeForm.status" style="width:100%">
            <el-option v-for="s in POLICE_STATUSES" :key="s" :label="s" :value="s" />
          </el-select>
        </el-form-item>
        <el-form-item label="处置结果">
          <el-input v-model="policeForm.result" type="textarea" :rows="2" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="policeVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="submitPolice">提交报案</el-button>
      </template>
    </el-dialog>

    <!-- 更新办案进展 -->
    <el-dialog v-model="progressVisible" :title="`更新办案进展 · ${progressTarget?.case_no ?? ''}`"
               width="480px" :close-on-click-modal="false">
      <el-form ref="progressRef" :model="progressForm" label-width="90px">
        <el-form-item label="办案状态">
          <el-select v-model="progressForm.status" style="width:100%">
            <el-option v-for="s in POLICE_STATUSES" :key="s" :label="s" :value="s" />
          </el-select>
        </el-form-item>
        <el-form-item label="处置结果">
          <el-input v-model="progressForm.result" type="textarea" :rows="3"
                    placeholder="如：已抓获嫌疑人，井盖于 XX 处追回" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="progressVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="submitProgress">保存进展</el-button>
      </template>
    </el-dialog>
  </div>
</template>
