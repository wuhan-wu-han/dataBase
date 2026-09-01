<script setup lang="ts">
import { reactive, ref, watch } from 'vue'
import { ElMessage } from 'element-plus'
import {
  createLifecycle, fetchAssetDetail, fetchLifecycleStages,
  fetchLifecycleTimeline, updateLifecycle
} from '../api'
import { ASSET_STATUS_TAG, fmtCost, STAGE_TAG } from '../utils/format'
import type { AssetDetail, LifecycleRecord } from '../types'
import OwnershipFormDialog from './OwnershipFormDialog.vue'

const props = defineProps<{ visible: boolean; assetId: number }>()
const emit = defineEmits<{ (e: 'update:visible', v: boolean): void; (e: 'changed'): void }>()

const detail = ref<AssetDetail | null>(null)
const records = ref<LifecycleRecord[]>([])
const totalCost = ref(0)
const stages = ref<string[]>([])

const recordDialogVisible = ref(false)
const editingId = ref<number | null>(null)
const recordForm = reactive({
  stage: '运维', occurred_at: '', responsible: '', description: '', attachment: '', cost: undefined as number | undefined
})

const ownershipDialogVisible = ref(false)

async function load() {
  if (!props.assetId) return
  const [d, tl, st] = await Promise.all([
    fetchAssetDetail(props.assetId),
    fetchLifecycleTimeline(props.assetId),
    stages.value.length ? Promise.resolve({ stages: stages.value }) : fetchLifecycleStages()
  ])
  detail.value = d
  records.value = tl.records
  totalCost.value = tl.total_cost
  stages.value = st.stages
}

watch(() => props.visible, (v) => {
  if (v) load()
})

function openCreate() {
  editingId.value = null
  recordForm.stage = '运维'
  recordForm.occurred_at = ''
  recordForm.responsible = ''
  recordForm.description = ''
  recordForm.attachment = ''
  recordForm.cost = undefined
  recordDialogVisible.value = true
}

function openEdit(r: LifecycleRecord) {
  editingId.value = r.id
  recordForm.stage = r.stage
  recordForm.occurred_at = r.occurred_at
  recordForm.responsible = r.responsible
  recordForm.description = r.description
  recordForm.attachment = r.attachment
  recordForm.cost = r.cost
  recordDialogVisible.value = true
}

async function onRecordSave() {
  if (!recordForm.occurred_at || !recordForm.responsible.trim() || !recordForm.description.trim()) {
    ElMessage.warning('请填写完整的时间、责任单位与事件描述')
    return
  }
  try {
    if (editingId.value) {
      await updateLifecycle(editingId.value, { ...recordForm })
      ElMessage.success('阶段记录已更新')
    } else {
      await createLifecycle({ asset_id: props.assetId, ...recordForm })
      ElMessage.success('阶段记录已新增')
    }
    recordDialogVisible.value = false
    await load()
    emit('changed')
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || '保存失败')
  }
}

async function onOwnershipSaved() {
  await load()
  emit('changed')
}
</script>

<template>
  <el-drawer
    :model-value="visible"
    :title="detail ? `${detail.asset.asset_code} · ${detail.asset.segment_name}` : '资产档案'"
    size="560px"
    @update:model-value="emit('update:visible', $event)"
  >
    <template v-if="detail">
      <el-descriptions :column="2" size="small" border>
        <el-descriptions-item label="管径">{{ detail.asset.diameter }}</el-descriptions-item>
        <el-descriptions-item label="材质">{{ detail.asset.material }}</el-descriptions-item>
        <el-descriptions-item label="建设年代">{{ detail.asset.build_year }}</el-descriptions-item>
        <el-descriptions-item label="压力等级">{{ detail.asset.pressure_level }}</el-descriptions-item>
        <el-descriptions-item label="权属单位">{{ detail.asset.owner_unit }}</el-descriptions-item>
        <el-descriptions-item label="所属区域">{{ detail.asset.region }}</el-descriptions-item>
        <el-descriptions-item label="长度">{{ detail.asset.length_m.toLocaleString() }} m</el-descriptions-item>
        <el-descriptions-item label="当前状态">
          <el-tag size="small" :type="ASSET_STATUS_TAG[detail.asset.status] || 'info'">
            {{ detail.asset.status }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="安装位置" :span="2">{{ detail.asset.location }}</el-descriptions-item>
        <el-descriptions-item label="坐标" :span="2">
          {{ detail.asset.longitude }}, {{ detail.asset.latitude }}
        </el-descriptions-item>
      </el-descriptions>

      <div class="panel-title mt12">权属信息（产权 / 运维 / 监管）</div>
      <template v-if="detail.ownership">
        <el-descriptions :column="1" size="small" border>
          <el-descriptions-item label="产权单位">
            {{ detail.ownership.property_unit || '—（缺失）' }}
            <span class="muted">（{{ detail.ownership.property_nature || '未登记' }}）</span>
          </el-descriptions-item>
          <el-descriptions-item label="产权证书编号">{{ detail.ownership.property_cert_no || '—' }}</el-descriptions-item>
          <el-descriptions-item label="运维单位">{{ detail.ownership.operation_unit || '—（缺失）' }}</el-descriptions-item>
          <el-descriptions-item label="运维合同编号">{{ detail.ownership.operation_contract_no || '—' }}</el-descriptions-item>
          <el-descriptions-item label="监管单位">{{ detail.ownership.supervision_unit || '—（缺失）' }}</el-descriptions-item>
          <el-descriptions-item label="责任边界">{{ detail.ownership.responsibility_boundary || '—' }}</el-descriptions-item>
          <el-descriptions-item label="交接时间">{{ detail.ownership.handover_at || '—' }}</el-descriptions-item>
        </el-descriptions>
      </template>
      <div v-else class="muted">尚未登记权属信息</div>
      <el-button size="small" type="primary" plain class="mt8" @click="ownershipDialogVisible = true">
        补录 / 修正权属
      </el-button>

      <div class="panel-title mt12" style="justify-content:space-between;display:flex;">
        <span style="display:flex;align-items:center;gap:8px;">
          全生命周期时间线（累计投入 {{ fmtCost(totalCost) }}）
        </span>
        <el-button size="small" type="primary" @click="openCreate">新增记录</el-button>
      </div>
      <el-timeline>
        <el-timeline-item
          v-for="r in records" :key="r.id"
          :timestamp="r.occurred_at" placement="top"
          :type="r.stage === '报废' ? 'danger' : r.stage === '运维' ? 'success' : 'primary'"
        >
          <div style="display:flex;align-items:center;gap:8px;">
            <el-tag size="small" :type="STAGE_TAG[r.stage] || 'info'">{{ r.stage }}</el-tag>
            <b>{{ r.responsible }}</b>
            <span class="muted">{{ fmtCost(r.cost) }}</span>
            <span class="spacer" style="flex:1"></span>
            <el-button size="small" link type="primary" @click="openEdit(r)">编辑</el-button>
          </div>
          <div class="mt8" style="font-size:13px;">{{ r.description }}</div>
          <div v-if="r.attachment" class="muted mt8" style="font-size:12px;">附件：{{ r.attachment }}</div>
        </el-timeline-item>
      </el-timeline>
    </template>

    <!-- 阶段记录新增/编辑 -->
    <el-dialog
      v-model="recordDialogVisible"
      :title="editingId ? '编辑阶段记录' : '新增阶段记录'"
      width="460px" append-to-body
    >
      <el-form label-width="88px">
        <el-form-item label="阶段">
          <el-select v-model="recordForm.stage" style="width:100%">
            <el-option v-for="s in stages" :key="s" :label="s" :value="s" />
          </el-select>
        </el-form-item>
        <el-form-item label="发生时间">
          <el-input v-model="recordForm.occurred_at" placeholder="yyyy-MM-dd" />
        </el-form-item>
        <el-form-item label="责任单位/人">
          <el-input v-model="recordForm.responsible" />
        </el-form-item>
        <el-form-item label="事件描述">
          <el-input v-model="recordForm.description" type="textarea" :rows="2" />
        </el-form-item>
        <el-form-item label="附件">
          <el-input v-model="recordForm.attachment" placeholder="如：合同/验收单/维修记录文件名" />
        </el-form-item>
        <el-form-item label="费用(元)">
          <el-input-number v-model="recordForm.cost" :min="0" :step="1000" style="width:100%" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="recordDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="onRecordSave">保存</el-button>
      </template>
    </el-dialog>

    <!-- 权属补录 -->
    <OwnershipFormDialog
      v-model:visible="ownershipDialogVisible"
      :asset-id="props.assetId"
      :asset-code="detail?.asset.asset_code"
      :initial="detail?.ownership"
      @saved="onOwnershipSaved"
    />
  </el-drawer>
</template>
