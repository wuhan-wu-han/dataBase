<script setup lang="ts">
import { nextTick, onBeforeUnmount, onMounted, ref } from 'vue'
import * as echarts from 'echarts'
import { fetchOwnershipMatrix, fetchUnclearAssets } from '../api'
import type { MatrixData, Ownership } from '../types'
import OwnershipFormDialog from './OwnershipFormDialog.vue'

const emit = defineEmits<{ (e: 'changed'): void }>()

type Side = 'property' | 'operation' | 'supervision'
const SIDE_LABEL: Record<Side, string> = {
  property: '产权单位',
  operation: '运维单位',
  supervision: '监管单位'
}

const side = ref<Side>('property')
const matrix = ref<Record<Side, MatrixData> | null>(null)
const unclear = ref<Ownership[]>([])

const elHeat = ref<HTMLDivElement>()
let heat: echarts.ECharts | null = null

const dialogRef = ref(false)
const editAssetId = ref<number | null>(null)
const editAssetCode = ref('')
const editInitial = ref<Partial<Ownership> | null>(null)

async function load() {
  const [m, u] = await Promise.all([fetchOwnershipMatrix(), fetchUnclearAssets()])
  matrix.value = m
  unclear.value = u.items
  await nextTick()
  renderHeat()
}

function renderHeat() {
  if (!elHeat.value || !matrix.value) return
  if (!heat) heat = echarts.init(elHeat.value)
  const m = matrix.value[side.value]
  const max = Math.max(1, ...m.values.map((v) => v[2]))
  heat.setOption({
    tooltip: {
      position: 'top',
      formatter: (p: any) => {
        const [j, i, n] = p.value
        return `${m.columns[j]} × ${m.rows[i]}<br/>资产数量：${n} 项`
      }
    },
    grid: { left: 8, right: 8, top: 14, bottom: 44, containLabel: true },
    xAxis: {
      type: 'category', data: m.columns,
      axisLine: { lineStyle: { color: '#c6d3e6' } },
      axisLabel: { color: '#5a6b84', fontSize: 11 }, splitArea: { show: true }
    },
    yAxis: {
      type: 'category', data: m.rows,
      axisLine: { lineStyle: { color: '#c6d3e6' } },
      axisLabel: { color: '#5a6b84', fontSize: 11 }, splitArea: { show: true }
    },
    visualMap: {
      min: 0, max, calculable: true, orient: 'horizontal', left: 'center', bottom: 0,
      itemHeight: 80, textStyle: { color: '#5a6b84' },
      inRange: { color: ['#eaf2ff', '#9cc0ff', '#3d7eff'] }
    },
    series: [{
      type: 'heatmap',
      data: m.values,
      label: { show: true, color: '#1f3b64' },
      itemStyle: { borderColor: '#fff', borderWidth: 1 },
      emphasis: { itemStyle: { shadowBlur: 6, shadowColor: 'rgba(61,126,255,0.4)' } }
    }]
  }, true)
}

function changeSide(s: Side) {
  side.value = s
  renderHeat()
}

function openEdit(row: Ownership) {
  editAssetId.value = row.asset_id
  editAssetCode.value = row.asset_code || ''
  editInitial.value = row
  dialogRef.value = true
}

async function onSaved() {
  await load()
  emit('changed')
}

const onResize = () => heat?.resize()

onMounted(() => {
  load()
  window.addEventListener('resize', onResize)
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', onResize)
  heat?.dispose()
  heat = null
})
</script>

<template>
  <div class="panel">
    <div class="panel-title">资产权属管理</div>
    <el-tabs>
      <el-tab-pane label="三方责任矩阵">
        <el-radio-group size="small" :model-value="side" @update:model-value="changeSide($event as Side)">
          <el-radio-button v-for="(label, key) in SIDE_LABEL" :key="key" :label="key">{{ label }}</el-radio-button>
        </el-radio-group>
        <div ref="elHeat" style="width:100%;height:300px;" class="mt8"></div>
        <div class="muted" style="font-size:12px;">行 = 责任单位，列 = 区域，颜色深浅 = 资产数量</div>
      </el-tab-pane>

      <el-tab-pane :label="`权属不清预警（${unclear.length}）`">
        <el-table :data="unclear" size="small" height="330">
          <el-table-column prop="asset_code" label="资产编号" min-width="122" show-overflow-tooltip />
          <el-table-column prop="region" label="区域" width="72" />
          <el-table-column label="缺失项" min-width="130">
            <template #default="{ row }">
              <el-tag v-for="m in row.missing" :key="m" size="small" type="danger" style="margin-right:4px;">
                {{ m }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="72">
            <template #default="{ row }">
              <el-button size="small" link type="primary" @click="openEdit(row)">补录</el-button>
            </template>
          </el-table-column>
        </el-table>
      </el-tab-pane>
    </el-tabs>

    <OwnershipFormDialog
      v-model:visible="dialogRef"
      :asset-id="editAssetId"
      :asset-code="editAssetCode"
      :initial="editInitial"
      @saved="onSaved"
    />
  </div>
</template>
