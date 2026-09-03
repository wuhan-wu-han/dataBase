<template>
  <div class="risk-analysis">
    <PageHeader title="风险研判中心" subtitle="Risk Analysis Center">
      <el-button @click="refreshAll">
        <el-icon><Refresh /></el-icon> 刷新
      </el-button>
    </PageHeader>

    <!-- 4 个统计卡片 -->
    <div class="risk-analysis__stats">
      <StatCard label="主数据总量" :value="overview.total_master_data ?? 0" icon="Coin" color="#0071E3" />
      <StatCard label="平均质量分" :value="qualityScoreText" icon="DataLine" color="#34C759" />
      <StatCard label="API 服务数" :value="overview.api_services_count ?? 0" icon="Connection" color="#AF52DE" />
      <StatCard label="24h 调用量" :value="overview.api_total_calls_24h ?? 0" icon="Odometer" color="#FF9500" />
    </div>

    <!-- Tab 主体 -->
    <section class="app-card risk-analysis__main">
      <el-tabs v-model="activeTab" @tab-change="handleTabChange">
        <!-- ============ Tab 1 数据总览 ============ -->
        <el-tab-pane label="数据总览" name="overview">
          <div v-loading="overviewLoading">
            <header class="card-title">
              <h3 class="card-title__text">核心指标</h3>
            </header>
            <div class="risk-analysis__metrics">
              <div v-for="tile in overviewTiles" :key="tile.key" class="metric-tile">
                <div class="metric-tile__label">{{ tile.label }}</div>
                <div class="metric-tile__value">
                  {{ overview[tile.key] ?? '-' }}<span v-if="tile.unit" class="metric-tile__unit">{{ tile.unit }}</span>
                </div>
              </div>
            </div>

            <header class="card-title risk-analysis__section-title">
              <h3 class="card-title__text">主数据分布</h3>
              <span class="card-title__badge">共 {{ masterStats.length }} 类</span>
            </header>
            <div class="risk-analysis__master-grid">
              <div
                v-for="m in masterStats"
                :key="m.type"
                class="master-card"
                @click="gotoMaster(m.type)"
              >
                <div class="master-card__head">
                  <div class="master-card__icon">
                    <el-icon :size="22"><component :is="getMasterIcon(m.icon)" /></el-icon>
                  </div>
                  <div class="master-card__count">{{ m.count ?? 0 }}</div>
                </div>
                <div class="master-card__name">{{ m.name }}</div>
                <div class="master-card__subtypes">
                  <el-tag
                    v-for="st in getSubtypeLabels(m.type).slice(0, 4)"
                    :key="st"
                    size="small"
                    type="info"
                    effect="plain"
                  >{{ st }}</el-tag>
                </div>
              </div>
            </div>
          </div>
        </el-tab-pane>

        <!-- ============ Tab 2 主数据管理 ============ -->
        <el-tab-pane label="主数据管理" name="master">
          <div class="filter-bar risk-analysis__filter">
            <el-select v-model="masterType" class="risk-analysis__filter-item" @change="handleTypeChange">
              <el-option v-for="t in DATA_TYPES" :key="t.value" :label="t.label" :value="t.value" />
            </el-select>
            <el-input
              v-model="masterQuery.keyword"
              placeholder="关键字搜索"
              clearable
              class="risk-analysis__filter-item"
              @keyup.enter="searchMaster"
            />
            <el-button type="primary" @click="searchMaster">
              <el-icon><Search /></el-icon> 查询
            </el-button>
            <el-button @click="resetMasterQuery">重置</el-button>
            <div class="risk-analysis__filter-spacer"></div>
            <el-button type="primary" plain @click="openForm('add')">
              <el-icon><Plus /></el-icon> 新增
            </el-button>
            <el-upload
              :show-file-list="false"
              accept=".xlsx,.xls"
              :http-request="handleImport"
              class="risk-analysis__upload"
            >
              <el-button plain>
                <el-icon><Upload /></el-icon> 导入
              </el-button>
            </el-upload>
            <el-button plain @click="handleExport">
              <el-icon><Download /></el-icon> 导出
            </el-button>
          </div>

          <el-table :data="masterRows" v-loading="masterLoading" class="app-table" empty-text="暂无数据">
            <el-table-column
              v-for="col in masterColumns"
              :key="col.prop"
              :prop="col.prop"
              :label="col.label"
              :width="col.width"
              :min-width="col.minWidth || 110"
              show-overflow-tooltip
            >
              <template #default="{ row }">
                <el-tag v-if="col.tag" :type="statusTagType(row[col.prop])" size="small">
                  {{ row[col.prop] ?? '-' }}
                </el-tag>
                <span v-else-if="col.score" class="score-cell" :style="{ color: scoreColor(row[col.prop]) }">
                  {{ row[col.prop] ?? '-' }}
                </span>
                <span v-else>{{ row[col.prop] ?? '-' }}</span>
              </template>
            </el-table-column>
            <el-table-column label="操作" width="220" align="center" fixed="right">
              <template #default="{ row }">
                <div class="table-actions">
                  <el-button link type="primary" size="small" @click="openDetail(row)">详情</el-button>
                  <el-button link type="primary" size="small" @click="openForm('edit', row)">编辑</el-button>
                  <el-button link type="warning" size="small" @click="handleStatusChange(row)">状态</el-button>
                  <el-button link type="danger" size="small" @click="handleDelete(row)">删除</el-button>
                </div>
              </template>
            </el-table-column>
          </el-table>

          <div class="risk-analysis__pagination">
            <el-pagination
              v-model:current-page="masterQuery.page"
              v-model:page-size="masterQuery.size"
              :total="masterTotal"
              :page-sizes="[10, 20, 50]"
              layout="total, sizes, prev, pager, next"
              @size-change="loadMasterList"
              @current-change="loadMasterList"
            />
          </div>
        </el-tab-pane>

        <!-- ============ Tab 3 数据质量 ============ -->
        <el-tab-pane label="数据质量" name="quality">
          <div v-loading="qualityLoading">
            <header class="card-title">
              <h3 class="card-title__text">质量报告</h3>
              <div class="risk-analysis__title-actions">
                <el-tag v-if="quality.overall_level" :type="quality.overall_score >= 90 ? 'success' : quality.overall_score >= 75 ? 'warning' : 'danger'" size="large">
                  {{ quality.overall_level }}
                </el-tag>
                <el-button type="primary" plain size="small" :loading="checkRunning" @click="handleRunCheck">
                  <el-icon><CircleCheck /></el-icon> 执行质检
                </el-button>
              </div>
            </header>

            <div class="risk-analysis__quality-head">
              <div class="quality-score">
                <div class="quality-score__label">综合质量分</div>
                <div class="quality-score__value">{{ quality.overall_score ?? '-' }}</div>
              </div>
              <div class="quality-trend">
                <div class="quality-trend__label">近 7 日趋势</div>
                <div class="quality-trend__bars">
                  <div v-for="t in quality.trend_7d || []" :key="t.date" class="trend-item">
                    <div class="trend-item__score">{{ t.score }}</div>
                    <div class="trend-item__bar" :style="{ height: trendBarHeight(t.score) }"></div>
                    <div class="trend-item__date">{{ t.date }}</div>
                  </div>
                </div>
              </div>
            </div>

            <header class="card-title risk-analysis__section-title">
              <h3 class="card-title__text">质检规则明细</h3>
              <span class="card-title__badge">{{ (quality.rules || []).length }} 条规则</span>
            </header>
            <el-table :data="quality.rules || []" class="app-table" empty-text="暂无规则数据">
              <el-table-column prop="rule_code" label="规则编码" width="150" />
              <el-table-column prop="rule_name" label="规则名称" min-width="180" show-overflow-tooltip />
              <el-table-column label="得分" width="100" align="center">
                <template #default="{ row }">
                  <span class="score-cell" :style="{ color: scoreColor(row.score) }">{{ row.score }}</span>
                </template>
              </el-table-column>
              <el-table-column prop="threshold" label="阈值" width="90" align="center" />
              <el-table-column label="结果" width="100" align="center">
                <template #default="{ row }">
                  <el-tag :type="row.passed ? 'success' : 'danger'" size="small">
                    {{ row.passed ? '通过' : '未通过' }}
                  </el-tag>
                </template>
              </el-table-column>
              <el-table-column prop="sample_size" label="样本量" width="100" align="right" />
              <el-table-column prop="error_count" label="异常数" width="100" align="right" />
            </el-table>
          </div>
        </el-tab-pane>

        <!-- ============ Tab 4 数据标准 ============ -->
        <el-tab-pane label="数据标准" name="standards">
          <div v-loading="standardsLoading">
            <header class="card-title">
              <h3 class="card-title__text">标准符合度</h3>
              <span class="card-title__badge">
                总体符合率 {{ formatRate(compliance.overall_compliance) }}
              </span>
            </header>
            <el-table :data="compliance.checks || []" class="app-table" empty-text="暂无符合度数据">
              <el-table-column prop="standard_code" label="标准编码" width="150" />
              <el-table-column prop="standard_name" label="标准名称" min-width="180" show-overflow-tooltip />
              <el-table-column label="符合率" width="200" align="center">
                <template #default="{ row }">
                  <el-progress
                    :percentage="toPercent(row.compliance_rate)"
                    :stroke-width="8"
                    :color="row.passed ? '#34C759' : '#FF9500'"
                  />
                </template>
              </el-table-column>
              <el-table-column label="结果" width="100" align="center">
                <template #default="{ row }">
                  <el-tag :type="row.passed ? 'success' : 'danger'" size="small">
                    {{ row.passed ? '达标' : '未达标' }}
                  </el-tag>
                </template>
              </el-table-column>
              <el-table-column prop="sample_count" label="样本数" width="100" align="right" />
              <el-table-column prop="violations" label="违规数" width="100" align="right" />
            </el-table>

            <header class="card-title risk-analysis__section-title">
              <h3 class="card-title__text">数据标准清单</h3>
              <span class="card-title__badge">{{ standardsTotal }} 项标准</span>
            </header>
            <el-table :data="standards" class="app-table" empty-text="暂无标准数据">
              <el-table-column prop="code" label="标准编码" width="150" />
              <el-table-column prop="name" label="标准名称" min-width="160" show-overflow-tooltip />
              <el-table-column prop="encoding_rule" label="编码规则" min-width="180" show-overflow-tooltip />
              <el-table-column prop="unit_standard" label="单位标准" width="120" />
              <el-table-column prop="format_spec" label="格式规范" min-width="140" show-overflow-tooltip />
              <el-table-column prop="sample_count" label="样本数" width="100" align="right" />
            </el-table>
          </div>
        </el-tab-pane>

        <!-- ============ Tab 5 API服务 ============ -->
        <el-tab-pane label="API服务" name="api">
          <div v-loading="apiLoading">
            <div class="risk-analysis__metrics risk-analysis__metrics--api">
              <div class="metric-tile">
                <div class="metric-tile__label">API 总数</div>
                <div class="metric-tile__value">{{ apiStats.total_apis ?? '-' }}</div>
              </div>
              <div class="metric-tile">
                <div class="metric-tile__label">24h 调用量</div>
                <div class="metric-tile__value">{{ apiStats.total_calls_24h ?? '-' }}</div>
              </div>
              <div class="metric-tile">
                <div class="metric-tile__label">平均响应</div>
                <div class="metric-tile__value">{{ apiStats.avg_response_ms ?? '-' }}<span class="metric-tile__unit">ms</span></div>
              </div>
              <div class="metric-tile">
                <div class="metric-tile__label">热门 API</div>
                <div class="metric-tile__value metric-tile__value--sm">{{ topApiName }}</div>
              </div>
            </div>

            <div class="filter-bar risk-analysis__filter">
              <el-input
                v-model="apiDomain"
                placeholder="按业务域筛选"
                clearable
                class="risk-analysis__filter-item"
                @keyup.enter="loadApi"
              />
              <el-button type="primary" @click="loadApi">
                <el-icon><Search /></el-icon> 查询
              </el-button>
              <el-button @click="apiDomain = ''; loadApi()">重置</el-button>
            </div>

            <el-table :data="apiServices" class="app-table" empty-text="暂无服务数据">
              <el-table-column prop="api_id" label="API ID" width="130" />
              <el-table-column prop="name" label="服务名称" min-width="160" show-overflow-tooltip />
              <el-table-column prop="domain" label="业务域" width="120" />
              <el-table-column prop="endpoint" label="端点" min-width="220" show-overflow-tooltip>
                <template #default="{ row }"><span class="code-cell">{{ row.endpoint }}</span></template>
              </el-table-column>
              <el-table-column label="方法" width="90" align="center">
                <template #default="{ row }">
                  <el-tag :type="row.method === 'GET' ? 'success' : 'warning'" size="small" effect="plain">
                    {{ row.method }}
                  </el-tag>
                </template>
              </el-table-column>
              <el-table-column prop="qps_limit" label="QPS限制" width="100" align="right" />
              <el-table-column label="鉴权" width="90" align="center">
                <template #default="{ row }">
                  <el-tag :type="row.auth_required ? 'danger' : 'info'" size="small" effect="plain">
                    {{ row.auth_required ? '需要' : '公开' }}
                  </el-tag>
                </template>
              </el-table-column>
              <el-table-column label="状态" width="100" align="center">
                <template #default="{ row }">
                  <el-tag :type="statusTagType(row.status)" size="small">{{ row.status }}</el-tag>
                </template>
              </el-table-column>
              <el-table-column prop="call_count_24h" label="24h调用" width="100" align="right" />
              <el-table-column prop="avg_response_ms" label="平均响应(ms)" width="120" align="right" />
            </el-table>
          </div>
        </el-tab-pane>
      </el-tabs>
    </section>

    <!-- 新增/编辑对话框 -->
    <el-dialog
      v-model="formVisible"
      :title="formMode === 'add' ? `新增${currentTypeLabel}` : `编辑${currentTypeLabel}`"
      width="680px"
      class="risk-analysis__dialog"
      destroy-on-close
    >
      <el-form ref="formRef" :model="form" label-width="110px">
        <el-row :gutter="16">
          <el-col v-for="f in formFields" :key="f.prop" :span="12">
            <el-form-item :label="f.label" :prop="f.prop">
              <el-select v-if="f.type === 'select'" v-model="form[f.prop]" clearable style="width: 100%">
                <el-option v-for="o in f.options" :key="o" :label="o" :value="o" />
              </el-select>
              <el-input-number
                v-else-if="f.type === 'number'"
                v-model="form[f.prop]"
                :controls="false"
                style="width: 100%"
              />
              <el-date-picker
                v-else-if="f.type === 'date'"
                v-model="form[f.prop]"
                type="date"
                value-format="YYYY-MM-DD"
                placeholder="选择日期"
                style="width: 100%"
              />
              <el-input v-else v-model="form[f.prop]" :placeholder="`请输入${f.label}`" />
            </el-form-item>
          </el-col>
        </el-row>
      </el-form>
      <template #footer>
        <el-button @click="formVisible = false">取消</el-button>
        <el-button type="primary" :loading="formSubmitting" @click="submitForm">保存</el-button>
      </template>
    </el-dialog>

    <!-- 详情对话框 -->
    <el-dialog v-model="detailVisible" title="数据详情" width="640px" class="risk-analysis__dialog">
      <el-descriptions :column="2" border>
        <el-descriptions-item v-for="[k, v] in detailEntries" :key="k" :label="k">
          {{ formatDetailValue(v) }}
        </el-descriptions-item>
      </el-descriptions>
      <template #footer>
        <el-button type="primary" @click="detailVisible = false">关闭</el-button>
      </template>
    </el-dialog>

    <!-- 质检结果对话框 -->
    <el-dialog v-model="resultVisible" title="质检结果" width="560px" class="risk-analysis__dialog">
      <pre class="risk-analysis__result">{{ resultText }}</pre>
      <template #footer>
        <el-button type="primary" @click="resultVisible = false">关闭</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Search, Plus, Upload, Download, Refresh, CircleCheck } from '@element-plus/icons-vue'
import * as XLSX from 'xlsx'
import { saveAs } from 'file-saver'
import PageHeader from '@/components/PageHeader.vue'
import StatCard from '@/components/StatCard.vue'
import { createModuleHttp, MODULE_PREFIX } from '@/api/gateway'
import {
  getOverview, getMasterStats, getMasterList,
  getStandards, getCompliance,
  getQualityReport, runQualityCheck,
  getApiServices, getApiStats
} from '@/api/riskAnalysis'

// 写操作（新增/编辑/删除/状态/导入）走同一网关前缀的 RESTful 端点
const http = createModuleHttp(MODULE_PREFIX.platform)

const activeTab = ref('overview')

// ==================== 总览 ====================
const overview = ref({})
const overviewLoading = ref(false)
const masterStats = ref([])

const overviewTiles = [
  { key: 'pipeline_count', label: '管线数据' },
  { key: 'equipment_count', label: '设备数据' },
  { key: 'personnel_count', label: '人员数据' },
  { key: 'organization_count', label: '组织数据' },
  { key: 'geo_space_count', label: '地理空间' },
  { key: 'data_standards_count', label: '数据标准' },
  { key: 'quality_rules_count', label: '质量规则' },
  { key: 'quality_passed', label: '质量达标' },
  { key: 'avg_quality_score', label: '平均质量分' },
  { key: 'api_services_count', label: 'API 服务' },
  { key: 'api_total_calls_24h', label: '24h 调用量' },
  { key: 'api_avg_response_ms', label: '平均响应', unit: 'ms' }
]

const qualityScoreText = computed(() => {
  const s = overview.value.avg_quality_score
  return s == null ? 0 : Number(s).toFixed(1)
})

async function loadOverview() {
  overviewLoading.value = true
  try {
    const [ov, ms] = await Promise.all([getOverview(), getMasterStats()])
    overview.value = ov || {}
    masterStats.value = ms?.master_data || []
  } catch (e) {
    ElMessage.error('加载数据总览失败')
    console.error(e)
  } finally {
    overviewLoading.value = false
  }
}

function gotoMaster(type) {
  const known = DATA_TYPES.some(t => t.value === type)
  masterType.value = known ? type : 'pipeline'
  activeTab.value = 'master'
  handleTypeChange()
}

// 主数据卡片图标映射（后端 icon 字段 → Element Plus 图标名）
const MASTER_ICON_MAP = {
  pipeline: 'Share',
  equipment: 'Setting',
  personnel: 'User',
  organization: 'OfficeBuilding',
  geo_space: 'MapLocation',
  valve: 'Setting',
  sensor: 'Odometer',
  station: 'OfficeBuilding',
  workorder: 'Tickets'
}

function getMasterIcon(iconName) {
  if (!iconName) return 'Folder'
  // 如果已经是有效的 Element Plus 图标名，直接返回
  if (MASTER_ICON_MAP[iconName]) return MASTER_ICON_MAP[iconName]
  // 否则尝试直接使用
  return iconName
}

// 主数据子类型标签映射
const SUBTYPE_LABELS = {
  pipeline: ['燃气干管', '给水管道', '电力电缆', '通信光缆'],
  equipment: ['电动闸阀', '蝶阀', '球阀', '安全阀'],
  personnel: ['巡检员', '维修工', '调度员', '管理员'],
  organization: ['运营公司', '维护部门', '监管机构', '应急队伍'],
  geo_space: ['监控中心', '分区节点', '出入口', '通风口']
}

function getSubtypeLabels(type) {
  return SUBTYPE_LABELS[type] || []
}

// ==================== 主数据管理 ====================
const DATA_TYPES = [
  { value: 'pipeline', label: '管线数据', idKey: 'pipeline_id' },
  { value: 'equipment', label: '设备数据', idKey: 'equipment_id' },
  { value: 'personnel', label: '人员数据', idKey: 'person_id' },
  { value: 'organization', label: '组织数据', idKey: 'org_id' },
  { value: 'geo_space', label: '地理空间', idKey: 'space_id' }
]

const COLUMN_CONFIG = {
  pipeline: [
    { prop: 'pipeline_id', label: '管线ID', width: 140 },
    { prop: 'type_name', label: '类型', width: 110 },
    { prop: 'zone', label: '区域', width: 110 },
    { prop: 'name', label: '名称', minWidth: 160 },
    { prop: 'spec', label: '规格', width: 110 },
    { prop: 'material', label: '材质', width: 110 },
    { prop: 'install_year', label: '敷设年份', width: 100 },
    { prop: 'length_m', label: '长度(m)', width: 100 },
    { prop: 'status', label: '状态', width: 110, tag: true },
    { prop: 'owner', label: '权属单位', minWidth: 140 },
    { prop: 'health_score', label: '健康度', width: 100, score: true }
  ],
  equipment: [
    { prop: 'equipment_id', label: '设备ID', width: 140 },
    { prop: 'name', label: '设备名称', minWidth: 150 },
    { prop: 'model', label: '型号', width: 120 },
    { prop: 'location', label: '位置', minWidth: 150 },
    { prop: 'status', label: '状态', width: 110, tag: true },
    { prop: 'health_score', label: '健康度', width: 100, score: true },
    { prop: 'manufacturer', label: '厂商', minWidth: 130 },
    { prop: 'install_date', label: '安装日期', width: 120 },
    { prop: 'last_maintenance', label: '最近维护', width: 120 }
  ],
  personnel: [
    { prop: 'person_id', label: '人员ID', width: 130 },
    { prop: 'name', label: '姓名', width: 110 },
    { prop: 'role', label: '角色', width: 120 },
    { prop: 'dept_name', label: '部门', minWidth: 140 },
    { prop: 'status', label: '状态', width: 110, tag: true },
    { prop: 'phone', label: '联系电话', width: 140 },
    { prop: 'cert_level', label: '证书等级', width: 110 },
    { prop: 'entry_date', label: '入职日期', width: 120 }
  ],
  organization: [
    { prop: 'org_id', label: '组织ID', width: 130 },
    { prop: 'name', label: '组织名称', minWidth: 170 },
    { prop: 'type', label: '类型', width: 120 },
    { prop: 'parent', label: '上级组织', minWidth: 150 },
    { prop: 'staff_count', label: '人员数', width: 100 },
    { prop: 'duty', label: '职责', minWidth: 180 }
  ]
}

const FORM_CONFIG = {
  pipeline: [
    { prop: 'name', label: '管线名称' },
    { prop: 'pipeline_type', label: '类型代码' },
    { prop: 'type_name', label: '类型名称' },
    { prop: 'zone', label: '所属区域' },
    { prop: 'spec', label: '规格' },
    { prop: 'material', label: '材质' },
    { prop: 'install_year', label: '敷设年份', type: 'number' },
    { prop: 'length_m', label: '长度(m)', type: 'number' },
    { prop: 'status', label: '状态' },
    { prop: 'owner', label: '权属单位' },
    { prop: 'last_inspect', label: '最近巡检', type: 'date' },
    { prop: 'health_score', label: '健康评分', type: 'number' }
  ],
  equipment: [
    { prop: 'name', label: '设备名称' },
    { prop: 'model', label: '型号' },
    { prop: 'location', label: '位置' },
    { prop: 'manufacturer', label: '厂商' },
    { prop: 'status', label: '状态' },
    { prop: 'health_score', label: '健康评分', type: 'number' },
    { prop: 'install_date', label: '安装日期', type: 'date' },
    { prop: 'last_maintenance', label: '最近维护', type: 'date' }
  ],
  personnel: [
    { prop: 'name', label: '姓名' },
    { prop: 'role', label: '角色' },
    { prop: 'department', label: '部门编码' },
    { prop: 'dept_name', label: '部门名称' },
    { prop: 'status', label: '状态' },
    { prop: 'phone', label: '联系电话' },
    { prop: 'cert_level', label: '证书等级' },
    { prop: 'entry_date', label: '入职日期', type: 'date' }
  ],
  organization: [
    { prop: 'name', label: '组织名称' },
    { prop: 'type', label: '类型' },
    { prop: 'parent', label: '上级组织' },
    { prop: 'staff_count', label: '人员数', type: 'number' },
    { prop: 'duty', label: '职责' }
  ]
}

const masterType = ref('pipeline')
const masterQuery = ref({ page: 1, size: 10, keyword: '' })
const masterRows = ref([])
const masterTotal = ref(0)
const masterLoading = ref(false)

const currentTypeConfig = computed(() => DATA_TYPES.find(t => t.value === masterType.value) || DATA_TYPES[0])
const currentTypeLabel = computed(() => currentTypeConfig.value.label)

// 表格列：已知类型用配置，未知类型（如 geo_space）根据首行动态生成
const masterColumns = computed(() => {
  const cfg = COLUMN_CONFIG[masterType.value]
  if (cfg) return cfg
  const first = masterRows.value[0]
  if (!first) return []
  return Object.keys(first).map(k => ({ prop: k, label: k }))
})

async function loadMasterList() {
  masterLoading.value = true
  try {
    const params = { page: masterQuery.value.page, size: masterQuery.value.size }
    if (masterQuery.value.keyword) params.keyword = masterQuery.value.keyword
    const res = await getMasterList(masterType.value, params)
    masterRows.value = res?.data || []
    masterTotal.value = res?.total || 0
  } catch (e) {
    ElMessage.error('加载主数据列表失败')
    console.error(e)
  } finally {
    masterLoading.value = false
  }
}

function searchMaster() {
  masterQuery.value.page = 1
  loadMasterList()
}

function resetMasterQuery() {
  masterQuery.value = { page: 1, size: 10, keyword: '' }
  loadMasterList()
}

function handleTypeChange() {
  masterQuery.value = { page: 1, size: 10, keyword: '' }
  loadMasterList()
}

function rowId(row) {
  return row[currentTypeConfig.value.idKey] ?? row.id
}

// ---------- 新增 / 编辑 ----------
const formVisible = ref(false)
const formMode = ref('add')
const formSubmitting = ref(false)
const formRef = ref(null)
const form = reactive({})
const editingId = ref(null)

const formFields = computed(() => {
  const cfg = FORM_CONFIG[masterType.value]
  if (cfg) return cfg
  // geo_space 等未知结构：编辑时按行字段生成，新增时按当前列生成
  const keys = editingId.value != null && Object.keys(form).length
    ? Object.keys(form)
    : masterColumns.value.map(c => c.prop)
  return keys.map(k => ({ prop: k, label: k }))
})

function openForm(mode, row) {
  formMode.value = mode
  Object.keys(form).forEach(k => delete form[k])
  if (mode === 'edit' && row) {
    editingId.value = rowId(row)
    const fields = FORM_CONFIG[masterType.value]
    const keys = fields ? fields.map(f => f.prop) : Object.keys(row)
    keys.forEach(k => { form[k] = row[k] ?? undefined })
  } else {
    editingId.value = null
  }
  formVisible.value = true
}

async function submitForm() {
  formSubmitting.value = true
  try {
    const base = `/governance/master/${masterType.value}`
    const body = { ...form }
    if (formMode.value === 'add') {
      await http.post(base, body)
      ElMessage.success('新增成功')
    } else {
      await http.put(`${base}/${editingId.value}`, body)
      ElMessage.success('保存成功')
    }
    formVisible.value = false
    loadMasterList()
    loadOverview()
  } catch (e) {
    ElMessage.error(formMode.value === 'add' ? '新增失败' : '保存失败')
    console.error(e)
  } finally {
    formSubmitting.value = false
  }
}

// ---------- 删除 ----------
async function handleDelete(row) {
  const id = rowId(row)
  try {
    await ElMessageBox.confirm(`确认删除该${currentTypeLabel.value}记录（${id}）吗？删除后不可恢复。`, '删除确认', {
      type: 'warning',
      confirmButtonText: '删除',
      cancelButtonText: '取消'
    })
  } catch {
    return
  }
  try {
    await http.delete(`/governance/master/${masterType.value}/${id}`)
    ElMessage.success('删除成功')
    loadMasterList()
    loadOverview()
  } catch (e) {
    ElMessage.error('删除失败')
    console.error(e)
  }
}

// ---------- 状态变更 ----------
async function handleStatusChange(row) {
  const id = rowId(row)
  let newStatus
  try {
    const res = await ElMessageBox.prompt('请输入新的状态值', '状态变更', {
      inputValue: row.status ?? '',
      confirmButtonText: '确定',
      cancelButtonText: '取消'
    })
    newStatus = res.value
  } catch {
    return
  }
  if (!newStatus) return ElMessage.warning('状态值不能为空')
  try {
    await http.put(`/governance/master/${masterType.value}/${id}/status`, { status: newStatus })
    ElMessage.success('状态已更新')
    loadMasterList()
  } catch (e) {
    ElMessage.error('状态变更失败')
    console.error(e)
  }
}

// ---------- 详情 ----------
const detailVisible = ref(false)
const detailEntries = ref([])

function openDetail(row) {
  detailEntries.value = Object.entries(row)
  detailVisible.value = true
}

// ---------- Excel 导入 / 导出 ----------
async function handleImport({ file }) {
  try {
    const buf = await file.arrayBuffer()
    const wb = XLSX.read(buf, { type: 'array' })
    const ws = wb.Sheets[wb.SheetNames[0]]
    const rows = XLSX.utils.sheet_to_json(ws)
    if (!rows.length) return ElMessage.warning('文件中没有可导入的数据')
    await http.post(`/governance/master/${masterType.value}/import`, { rows })
    ElMessage.success(`成功导入 ${rows.length} 条数据`)
    loadMasterList()
    loadOverview()
  } catch (e) {
    ElMessage.error('导入失败：' + (e?.message || '未知错误'))
    console.error(e)
  }
}

function handleExport() {
  if (!masterRows.value.length) return ElMessage.warning('暂无数据可导出')
  const wb = XLSX.utils.book_new()
  XLSX.utils.book_append_sheet(wb, XLSX.utils.json_to_sheet(masterRows.value), 'Sheet1')
  const buf = XLSX.write(wb, { bookType: 'xlsx', type: 'array' })
  saveAs(
    new Blob([buf], { type: 'application/octet-stream' }),
    `主数据_${masterType.value}_${Date.now()}.xlsx`
  )
  ElMessage.success('导出成功')
}

// ==================== 数据质量 ====================
const quality = ref({})
const qualityLoading = ref(false)
const checkRunning = ref(false)
const resultVisible = ref(false)
const resultText = ref('')

async function loadQuality() {
  qualityLoading.value = true
  try {
    quality.value = (await getQualityReport()) || {}
  } catch (e) {
    ElMessage.error('加载质量报告失败')
    console.error(e)
  } finally {
    qualityLoading.value = false
  }
}

async function handleRunCheck() {
  checkRunning.value = true
  try {
    const res = await runQualityCheck({ scope: 'all', data_type: masterType.value })
    resultText.value = JSON.stringify(res ?? {}, null, 2)
    resultVisible.value = true
    loadQuality()
  } catch (e) {
    ElMessage.error('执行质检失败')
    console.error(e)
  } finally {
    checkRunning.value = false
  }
}

function trendBarHeight(score) {
  const s = Number(score) || 0
  return `${Math.max(4, Math.min(72, s * 0.72))}px`
}

// ==================== 数据标准 ====================
const standards = ref([])
const standardsTotal = ref(0)
const compliance = ref({})
const standardsLoading = ref(false)

async function loadStandards() {
  standardsLoading.value = true
  try {
    const [std, comp] = await Promise.all([getStandards(), getCompliance()])
    standards.value = std?.standards || []
    standardsTotal.value = std?.total || standards.value.length
    compliance.value = comp || {}
  } catch (e) {
    ElMessage.error('加载数据标准失败')
    console.error(e)
  } finally {
    standardsLoading.value = false
  }
}

// ==================== API 服务 ====================
const apiServices = ref([])
const apiStats = ref({})
const apiDomain = ref('')
const apiLoading = ref(false)

const topApiName = computed(() => {
  const top = apiStats.value.top_apis
  if (Array.isArray(top) && top.length) return top[0].name || top[0].api_id || '-'
  return '-'
})

async function loadApi() {
  apiLoading.value = true
  try {
    const [svc, stats] = await Promise.all([
      getApiServices(apiDomain.value || undefined),
      getApiStats()
    ])
    apiServices.value = svc?.services || []
    apiStats.value = stats || {}
  } catch (e) {
    ElMessage.error('加载 API 服务失败')
    console.error(e)
  } finally {
    apiLoading.value = false
  }
}

// ==================== 通用工具 ====================
const STATUS_TAG_MAP = {
  normal: 'success', active: 'success', online: 'success', running: 'success',
  in_service: 'success', enabled: 'success', approved: 'success', completed: 'success',
  healthy: 'success', good: 'success', pass: 'success',
  warning: 'danger', alarm: 'danger', error: 'danger', fault: 'danger',
  offline: 'danger', disabled: 'danger', deviated: 'danger', failed: 'danger',
  maintenance: 'warning', pending: 'warning', inactive: 'info', retired: 'info'
}

function statusTagType(status) {
  if (status == null) return 'info'
  return STATUS_TAG_MAP[String(status).toLowerCase()] || 'info'
}

function scoreColor(score) {
  const s = Number(score)
  if (isNaN(s)) return 'var(--app-text-2)'
  if (s >= 85) return '#34C759'
  if (s >= 70) return '#FF9500'
  return '#FF3B30'
}

function toPercent(rate) {
  const r = Number(rate)
  if (isNaN(r)) return 0
  return Math.round(r <= 1 ? r * 100 : r)
}

function formatRate(rate) {
  return rate == null ? '-' : `${toPercent(rate)}%`
}

function formatDetailValue(v) {
  if (v == null || v === '') return '-'
  if (typeof v === 'boolean') return v ? '是' : '否'
  if (typeof v === 'object') return JSON.stringify(v)
  return v
}

// Tab 懒加载：首次切换到某 Tab 才拉取对应数据
const loadedTabs = new Set(['overview'])
function handleTabChange(name) {
  if (loadedTabs.has(name)) return
  loadedTabs.add(name)
  if (name === 'master') loadMasterList()
  else if (name === 'quality') loadQuality()
  else if (name === 'standards') loadStandards()
  else if (name === 'api') loadApi()
}

async function refreshAll() {
  loadedTabs.clear()
  loadedTabs.add(activeTab.value)
  await loadOverview()
  if (activeTab.value === 'master') loadMasterList()
  else if (activeTab.value === 'quality') loadQuality()
  else if (activeTab.value === 'standards') loadStandards()
  else if (activeTab.value === 'api') loadApi()
}

onMounted(() => {
  loadOverview()
})
</script>

<style scoped>
/* ===== 布局 ===== */
.risk-analysis__stats {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
  margin-bottom: 16px;
}
.risk-analysis__main {
  padding: 16px 24px 24px;
}
.risk-analysis__section-title {
  margin-top: 28px;
}
.risk-analysis__title-actions {
  display: flex;
  align-items: center;
  gap: 12px;
}

/* ===== 筛选条 ===== */
.risk-analysis__filter {
  margin-bottom: 16px;
}
.risk-analysis__filter-item {
  width: 160px;
}
.risk-analysis__filter-spacer {
  flex: 1;
}
.risk-analysis__upload {
  display: inline-flex;
}
.risk-analysis__pagination {
  display: flex;
  justify-content: flex-end;
  margin-top: 16px;
}

/* ===== 总览指标瓦片 ===== */
.risk-analysis__metrics {
  display: grid;
  grid-template-columns: repeat(6, 1fr);
  gap: 12px;
}
.risk-analysis__metrics--api {
  grid-template-columns: repeat(4, 1fr);
  margin-bottom: 20px;
}
.metric-tile {
  background: rgba(0, 0, 0, 0.02);
  border: 1px solid var(--app-border);
  border-radius: 14px;
  padding: 14px 16px;
  transition: background 0.2s;
}
.metric-tile:hover {
  background: rgba(0, 0, 0, 0.04);
}
.metric-tile__label {
  font-size: 12px;
  color: var(--app-text-3);
  margin-bottom: 6px;
}
.metric-tile__value {
  font-size: 22px;
  font-weight: 600;
  color: var(--app-text-1);
  font-variant-numeric: tabular-nums;
  letter-spacing: -0.02em;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.metric-tile__value--sm {
  font-size: 15px;
  line-height: 1.5;
}
.metric-tile__unit {
  font-size: 12px;
  font-weight: 500;
  color: var(--app-text-3);
  margin-left: 3px;
}

/* ===== 主数据分布卡片 ===== */
.risk-analysis__master-grid {
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  gap: 12px;
}
.master-card {
  background: var(--app-card-solid);
  border: 1px solid var(--app-border);
  border-radius: 16px;
  padding: 18px;
  cursor: pointer;
  transition: transform 0.25s cubic-bezier(0.4, 0, 0.2, 1), box-shadow 0.25s;
}
.master-card:hover {
  transform: translateY(-3px);
  box-shadow: var(--app-shadow-card);
}
.master-card__head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
}
.master-card__icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 40px;
  height: 40px;
  border-radius: 12px;
  background: var(--app-primary-soft);
  color: var(--app-primary);
}
.master-card__count {
  font-size: 24px;
  font-weight: 600;
  color: var(--app-text-1);
  font-variant-numeric: tabular-nums;
}
.master-card__name {
  font-size: 14px;
  font-weight: 600;
  color: var(--app-text-2);
  margin-bottom: 8px;
}
.master-card__subtypes {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

/* ===== 数据质量 ===== */
.risk-analysis__quality-head {
  display: grid;
  grid-template-columns: 220px 1fr;
  gap: 16px;
  margin-bottom: 8px;
}
.quality-score {
  background: rgba(0, 0, 0, 0.02);
  border: 1px solid var(--app-border);
  border-radius: 16px;
  padding: 20px 24px;
  display: flex;
  flex-direction: column;
  justify-content: center;
}
.quality-score__label {
  font-size: 13px;
  color: var(--app-text-3);
  margin-bottom: 6px;
}
.quality-score__value {
  font-size: 44px;
  font-weight: 700;
  color: var(--app-primary);
  line-height: 1.1;
  letter-spacing: -0.03em;
}
.quality-trend {
  background: rgba(0, 0, 0, 0.02);
  border: 1px solid var(--app-border);
  border-radius: 16px;
  padding: 16px 24px;
}
.quality-trend__label {
  font-size: 13px;
  color: var(--app-text-3);
  margin-bottom: 10px;
}
.quality-trend__bars {
  display: flex;
  align-items: flex-end;
  gap: 16px;
  height: 130px;
}
.trend-item {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: flex-end;
  height: 100%;
}
.trend-item__score {
  font-size: 12px;
  color: var(--app-text-2);
  font-weight: 600;
  margin-bottom: 4px;
}
.trend-item__bar {
  width: 60%;
  max-width: 36px;
  border-radius: 6px 6px 2px 2px;
  background: linear-gradient(180deg, #5AC8FA, var(--app-primary));
}
.trend-item__date {
  font-size: 11px;
  color: var(--app-text-3);
  margin-top: 6px;
}

/* ===== 表格单元 ===== */
.code-cell {
  font-family: 'Courier New', monospace;
  font-size: 13px;
  color: var(--app-primary);
}
.score-cell {
  font-weight: 600;
  font-variant-numeric: tabular-nums;
}

/* ===== 对话框 ===== */
.risk-analysis__dialog {
  border-radius: var(--app-radius-card);
}
.risk-analysis__result {
  margin: 0;
  max-height: 400px;
  overflow: auto;
  background: rgba(0, 0, 0, 0.03);
  border-radius: var(--app-radius-control);
  padding: 16px;
  font-size: 12px;
  line-height: 1.6;
  color: var(--app-text-2);
  white-space: pre-wrap;
  word-break: break-all;
}

/* ===== 响应式 ===== */
@media (max-width: 1024px) {
  .risk-analysis__stats { grid-template-columns: repeat(2, 1fr); }
  .risk-analysis__metrics { grid-template-columns: repeat(3, 1fr); }
  .risk-analysis__master-grid { grid-template-columns: repeat(2, 1fr); }
  .risk-analysis__quality-head { grid-template-columns: 1fr; }
}
@media (max-width: 640px) {
  .risk-analysis__stats { grid-template-columns: 1fr; }
  .risk-analysis__metrics { grid-template-columns: repeat(2, 1fr); }
  .risk-analysis__master-grid { grid-template-columns: 1fr; }
}
</style>
