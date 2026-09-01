<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { EXPORT_URL, fetchAssets, fetchOptions } from '../api'
import { ASSET_STATUS_TAG } from '../utils/format'
import type { Asset, AssetOptions } from '../types'
import AssetDetailDrawer from './AssetDetailDrawer.vue'

const emit = defineEmits<{ (e: 'changed'): void }>()

const options = ref<AssetOptions | null>(null)
const rows = ref<Asset[]>([])
const total = ref(0)
const loading = ref(false)

const query = reactive({
  keyword: '',
  region: '',
  material: '',
  diameter: '',
  status: ''
})
const page = ref(1)
const pageSize = ref(10)

const drawerVisible = ref(false)
const activeAssetId = ref<number>(0)

async function load() {
  loading.value = true
  try {
    const r = await fetchAssets({
      keyword: query.keyword || undefined,
      region: query.region || undefined,
      material: query.material || undefined,
      diameter: query.diameter || undefined,
      status: query.status || undefined,
      page: page.value,
      page_size: pageSize.value
    })
    rows.value = r.items
    total.value = r.total
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || '加载资产列表失败')
  } finally {
    loading.value = false
  }
}

function onSearch() {
  page.value = 1
  load()
}

function onReset() {
  query.keyword = ''
  query.region = ''
  query.material = ''
  query.diameter = ''
  query.status = ''
  onSearch()
}

function onExport() {
  window.open(EXPORT_URL, '_blank')
}

function openDetail(row: Asset) {
  activeAssetId.value = row.id
  drawerVisible.value = true
}

onMounted(async () => {
  options.value = await fetchOptions()
  load()
})
</script>

<template>
  <div class="panel">
    <div class="panel-title">资产明细台账</div>
    <div class="filter-bar">
      <el-input
        v-model="query.keyword" style="width: 220px" clearable
        placeholder="搜索编号 / 管段名称 / 位置"
        @keyup.enter="onSearch" @clear="onSearch"
      />
      <el-select v-model="query.region" placeholder="所属区域" clearable style="width:130px" @change="onSearch">
        <el-option v-for="v in options?.regions || []" :key="v" :label="v" :value="v" />
      </el-select>
      <el-select v-model="query.diameter" placeholder="管径" clearable style="width:120px" @change="onSearch">
        <el-option v-for="v in options?.diameters || []" :key="v" :label="v" :value="v" />
      </el-select>
      <el-select v-model="query.material" placeholder="材质" clearable style="width:120px" @change="onSearch">
        <el-option v-for="v in options?.materials || []" :key="v" :label="v" :value="v" />
      </el-select>
      <el-select v-model="query.status" placeholder="状态" clearable style="width:120px" @change="onSearch">
        <el-option v-for="v in options?.statuses || []" :key="v" :label="v" :value="v" />
      </el-select>
      <el-button type="primary" @click="onSearch">查询</el-button>
      <el-button @click="onReset">重置</el-button>
      <span class="spacer"></span>
      <el-button type="success" plain @click="onExport">导出 CSV</el-button>
    </div>

    <el-table v-loading="loading" :data="rows" size="small" height="360">
      <el-table-column prop="asset_code" label="资产编号" min-width="130" show-overflow-tooltip />
      <el-table-column prop="segment_name" label="管段名称" min-width="150" show-overflow-tooltip />
      <el-table-column prop="diameter" label="管径" width="78" />
      <el-table-column prop="material" label="材质" width="84" />
      <el-table-column prop="build_year" label="建设年代" width="84" align="center" />
      <el-table-column prop="owner_unit" label="权属单位" min-width="120" show-overflow-tooltip />
      <el-table-column prop="region" label="区域" width="76" />
      <el-table-column label="长度(m)" width="86" align="right">
        <template #default="{ row }">{{ row.length_m.toLocaleString() }}</template>
      </el-table-column>
      <el-table-column prop="pressure_level" label="压力等级" width="84" />
      <el-table-column label="状态" width="80" align="center">
        <template #default="{ row }">
          <el-tag size="small" :type="ASSET_STATUS_TAG[row.status] || 'info'">{{ row.status }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="70" fixed="right">
        <template #default="{ row }">
          <el-button size="small" link type="primary" @click="openDetail(row)">档案</el-button>
        </template>
      </el-table-column>
    </el-table>

    <div class="pager">
      <el-pagination
        v-model:current-page="page"
        v-model:page-size="pageSize"
        :total="total"
        :page-sizes="[10, 20, 50]"
        layout="total, sizes, prev, pager, next"
        background
        @current-change="load"
        @size-change="onSearch"
      />
    </div>

    <AssetDetailDrawer
      v-model:visible="drawerVisible"
      :asset-id="activeAssetId"
      @changed="emit('changed')"
    />
  </div>
</template>
