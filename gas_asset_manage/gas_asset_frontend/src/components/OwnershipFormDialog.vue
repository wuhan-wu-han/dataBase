<script setup lang="ts">
import { reactive, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { updateOwnership } from '../api'
import type { Ownership } from '../types'

const props = defineProps<{
  visible: boolean
  assetId: number | null
  assetCode?: string
  initial?: Partial<Ownership> | null
}>()

const emit = defineEmits<{
  (e: 'update:visible', v: boolean): void
  (e: 'saved'): void
}>()

const form = reactive({
  property_unit: '',
  property_nature: '',
  property_cert_no: '',
  operation_unit: '',
  operation_contract_no: '',
  supervision_unit: '',
  responsibility_boundary: '',
  handover_at: ''
})

watch(() => props.visible, (v) => {
  if (v) {
    const init = props.initial || {}
    Object.keys(form).forEach((k) => {
      (form as any)[k] = (init as any)[k] ?? ''
    })
  }
})

async function onSave() {
  if (!props.assetId) return
  try {
    await updateOwnership(props.assetId, { ...form })
    ElMessage.success('权属信息已保存')
    emit('update:visible', false)
    emit('saved')
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || e?.message || '保存失败')
  }
}
</script>

<template>
  <el-dialog
    :model-value="visible"
    :title="`权属信息补录 / 修正${assetCode ? ' · ' + assetCode : ''}`"
    width="560px"
    append-to-body
    @update:model-value="emit('update:visible', $event)"
  >
    <el-form label-width="100px">
      <el-form-item label="产权单位">
        <el-input v-model="form.property_unit" placeholder="如：天信燃气集团" />
      </el-form-item>
      <el-form-item label="产权性质">
        <el-select v-model="form.property_nature" clearable placeholder="请选择" style="width:100%">
          <el-option label="国有" value="国有" />
          <el-option label="集体" value="集体" />
          <el-option label="企业" value="企业" />
        </el-select>
      </el-form-item>
      <el-form-item label="产权证书编号">
        <el-input v-model="form.property_cert_no" />
      </el-form-item>
      <el-form-item label="运维单位">
        <el-input v-model="form.operation_unit" />
      </el-form-item>
      <el-form-item label="运维合同编号">
        <el-input v-model="form.operation_contract_no" />
      </el-form-item>
      <el-form-item label="监管单位">
        <el-input v-model="form.supervision_unit" />
      </el-form-item>
      <el-form-item label="责任边界说明">
        <el-input v-model="form.responsibility_boundary" type="textarea" :rows="2" />
      </el-form-item>
      <el-form-item label="交接时间">
        <el-input v-model="form.handover_at" placeholder="yyyy-MM-dd" />
      </el-form-item>
    </el-form>
    <template #footer>
      <el-button @click="emit('update:visible', false)">取消</el-button>
      <el-button type="primary" @click="onSave">保存</el-button>
    </template>
  </el-dialog>
</template>
