<template>
  <div class="rule-manage-container">
    <div class="bg-particles">
      <div v-for="i in 20" :key="i" class="particle" :style="particleStyle(i)"></div>
    </div>

    <header class="page-header">
      <div class="header-left">
        <span class="back-btn" @click="$router.push('/')">
          <el-icon><ArrowLeft /></el-icon> 返回大屏
        </span>
      </div>
      <div class="header-center">
        <div class="header-decor left-decor">
          <span class="decor-line"></span>
          <span class="decor-diamond"></span>
          <span class="decor-line"></span>
        </div>
        <div class="header-title-group">
          <h1 class="header-title">预警规则管理</h1>
          <p class="header-subtitle">ALERT RULE MANAGEMENT</p>
        </div>
        <div class="header-decor right-decor">
          <span class="decor-line"></span>
          <span class="decor-diamond"></span>
          <span class="decor-line"></span>
        </div>
      </div>
      <div class="header-right">
        <div class="realtime-clock">{{ currentTime }}</div>
        <div class="realtime-date">{{ currentDate }}</div>
      </div>
    </header>

    <main class="page-main">
      <section class="table-section">
        <div class="panel-header">
          <span class="panel-icon">&#9670;</span>
          <span class="panel-title">规则列表</span>
          <span class="panel-badge">{{ total }} 条</span>
          <el-button type="primary" class="add-btn" @click="openDialog(null)">
            <el-icon><Plus /></el-icon> 新增规则
          </el-button>
        </div>

        <div class="filter-bar">
          <el-input v-model="query.ruleName" placeholder="规则名称" clearable class="filter-input" />
          <el-select v-model="query.deviceType" placeholder="设备类型" clearable class="filter-select">
            <el-option label="全部" value="" />
            <el-option label="温度传感器" value="TEMPERATURE" />
            <el-option label="湿度传感器" value="HUMIDITY" />
            <el-option label="气体检测器" value="GAS_DETECTOR" />
            <el-option label="水位传感器" value="WATER_LEVEL" />
            <el-option label="压力传感器" value="PRESSURE" />
          </el-select>
          <el-select v-model="query.enabled" placeholder="启用状态" clearable class="filter-select">
            <el-option label="全部" value="" />
            <el-option label="已启用" :value="true" />
            <el-option label="已禁用" :value="false" />
          </el-select>
          <el-button type="primary" @click="loadData" class="filter-btn">
            <el-icon><Search /></el-icon> 查询
          </el-button>
          <el-button @click="resetQuery" class="filter-btn">重置</el-button>
        </div>

        <el-table
          :data="tableData"
          v-loading="tableLoading"
          element-loading-background="rgba(0,0,0,0.3)"
          class="rule-table"
          :header-cell-style="{ background: 'rgba(13, 27, 42, 0.8)', color: '#8a9bb0', borderColor: 'rgba(42, 58, 74, 0.6)' }"
          :cell-style="{ background: 'rgba(13, 27, 42, 0.4)', color: '#e0e6ed', borderColor: 'rgba(42, 58, 74, 0.4)' }"
        >
          <el-table-column prop="ruleCode" label="规则编码" min-width="160">
            <template #default="{ row }">
              <span class="code-cell">{{ row.ruleCode }}</span>
            </template>
          </el-table-column>
          <el-table-column prop="ruleName" label="规则名称" min-width="160" />
          <el-table-column prop="deviceType" label="设备类型" width="120" />
          <el-table-column prop="metricKey" label="监测指标" width="120" />
          <el-table-column prop="compareType" label="比较方式" width="100" align="center">
            <template #default="{ row }">
              <span class="compare-tag">{{ compareText(row.compareType) }}</span>
            </template>
          </el-table-column>
          <el-table-column label="蓝色阈值" width="100" align="center">
            <template #default="{ row }">
              <span class="threshold blue">{{ row.blueThreshold }}</span>
            </template>
          </el-table-column>
          <el-table-column label="黄色阈值" width="100" align="center">
            <template #default="{ row }">
              <span class="threshold yellow">{{ row.yellowThreshold }}</span>
            </template>
          </el-table-column>
          <el-table-column label="橙色阈值" width="100" align="center">
            <template #default="{ row }">
              <span class="threshold orange">{{ row.orangeThreshold }}</span>
            </template>
          </el-table-column>
          <el-table-column label="红色阈值" width="100" align="center">
            <template #default="{ row }">
              <span class="threshold red">{{ row.redThreshold }}</span>
            </template>
          </el-table-column>
          <el-table-column label="状态" width="90" align="center">
            <template #default="{ row }">
              <span class="status-dot" :class="row.enabled ? 'enabled' : 'disabled'"></span>
              <span :class="row.enabled ? 'text-enabled' : 'text-disabled'">{{ row.enabled ? '启用' : '禁用' }}</span>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="160" align="center" fixed="right">
            <template #default="{ row }">
              <el-button link type="primary" size="small" @click="openDialog(row)">编辑</el-button>
              <el-popconfirm title="确认删除该规则？" @confirm="handleDelete(row)">
                <template #reference>
                  <el-button link type="danger" size="small">删除</el-button>
                </template>
              </el-popconfirm>
            </template>
          </el-table-column>
        </el-table>

        <div class="pagination-bar">
          <el-pagination
            v-model:current-page="query.page"
            v-model:page-size="query.size"
            :total="total"
            :page-sizes="[10, 20, 50]"
            layout="total, sizes, prev, pager, next"
            @size-change="loadData"
            @current-change="loadData"
          />
        </div>
      </section>
    </main>

    <!-- 新增/编辑对话框 -->
    <el-dialog
      v-model="dialogVisible"
      :title="isEdit ? '编辑规则' : '新增规则'"
      width="640px"
      class="rule-dialog"
      destroy-on-close
    >
      <el-form ref="formRef" :model="form" :rules="rules" label-width="100px" class="rule-form">
        <el-form-item label="规则编码" prop="ruleCode">
          <el-input v-model="form.ruleCode" :disabled="isEdit" placeholder="如 RULE_TEMP_001" />
        </el-form-item>
        <el-form-item label="规则名称" prop="ruleName">
          <el-input v-model="form.ruleName" placeholder="如 温度过高预警" />
        </el-form-item>
        <el-form-item label="设备类型" prop="deviceType">
          <el-select v-model="form.deviceType" placeholder="选择设备类型" style="width: 100%;">
            <el-option label="温度传感器" value="TEMPERATURE" />
            <el-option label="湿度传感器" value="HUMIDITY" />
            <el-option label="气体检测器" value="GAS_DETECTOR" />
            <el-option label="水位传感器" value="WATER_LEVEL" />
            <el-option label="压力传感器" value="PRESSURE" />
          </el-select>
        </el-form-item>
        <el-form-item label="监测指标" prop="metricKey">
          <el-input v-model="form.metricKey" placeholder="如 temperature, humidity" />
        </el-form-item>
        <el-form-item label="比较方式" prop="compareType">
          <el-select v-model="form.compareType" placeholder="选择比较方式" style="width: 100%;">
            <el-option label="大于 (>)" value="GT" />
            <el-option label="大于等于 (>=)" value="GTE" />
            <el-option label="小于 (<)" value="LT" />
            <el-option label="小于等于 (<=)" value="LTE" />
          </el-select>
        </el-form-item>
        <el-form-item label="蓝色阈值" prop="blueThreshold">
          <el-input-number v-model="form.blueThreshold" :precision="2" style="width: 100%;" />
        </el-form-item>
        <el-form-item label="黄色阈值" prop="yellowThreshold">
          <el-input-number v-model="form.yellowThreshold" :precision="2" style="width: 100%;" />
        </el-form-item>
        <el-form-item label="橙色阈值" prop="orangeThreshold">
          <el-input-number v-model="form.orangeThreshold" :precision="2" style="width: 100%;" />
        </el-form-item>
        <el-form-item label="红色阈值" prop="redThreshold">
          <el-input-number v-model="form.redThreshold" :precision="2" style="width: 100%;" />
        </el-form-item>
        <el-form-item label="区域" prop="areaId">
          <el-input v-model="form.areaId" placeholder="区域ID" />
        </el-form-item>
        <el-form-item label="启用状态">
          <el-switch v-model="form.enabled" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false" class="dialog-btn">取消</el-button>
        <el-button type="primary" :loading="submitting" @click="handleSubmit" class="dialog-btn submit-btn">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { ElMessage } from 'element-plus'
import { ArrowLeft, Plus, Search } from '@element-plus/icons-vue'
import { getAlertRuleList, createAlertRule, updateAlertRule, deleteAlertRule } from '@/api/alertRule'

const currentTime = ref('')
const currentDate = ref('')
let clockTimer = null

const updateClock = () => {
  const now = new Date()
  currentTime.value = `${String(now.getHours()).padStart(2, '0')}:${String(now.getMinutes()).padStart(2, '0')}:${String(now.getSeconds()).padStart(2, '0')}`
  const y = now.getFullYear()
  const mo = String(now.getMonth() + 1).padStart(2, '0')
  const d = String(now.getDate()).padStart(2, '0')
  const weekDays = ['星期日', '星期一', '星期二', '星期三', '星期四', '星期五', '星期六']
  currentDate.value = `${y}-${mo}-${d} ${weekDays[now.getDay()]}`
}

const particleStyle = (i) => ({
  left: `${Math.random() * 100}%`,
  top: `${Math.random() * 100}%`,
  animationDelay: `${Math.random() * 6}s`,
  animationDuration: `${4 + Math.random() * 6}s`,
  width: `${2 + Math.random() * 3}px`,
  height: `${2 + Math.random() * 3}px`,
  opacity: 0.2 + Math.random() * 0.4
})

const query = ref({ page: 1, size: 10, ruleName: '', deviceType: '', enabled: '' })
const tableData = ref([])
const total = ref(0)
const tableLoading = ref(false)

const loadData = async () => {
  tableLoading.value = true
  try {
    const params = { page: query.value.page, size: query.value.size }
    if (query.value.ruleName) params.ruleName = query.value.ruleName
    if (query.value.deviceType) params.deviceType = query.value.deviceType
    if (query.value.enabled !== '') params.enabled = query.value.enabled
    const res = await getAlertRuleList(params)
    tableData.value = res?.records || res || []
    total.value = res?.total || tableData.value.length
  } catch (e) {
    ElMessage.error('加载规则列表失败')
    console.error('加载规则列表失败:', e)
  } finally {
    tableLoading.value = false
  }
}

const resetQuery = () => {
  query.value = { page: 1, size: 10, ruleName: '', deviceType: '', enabled: '' }
  loadData()
}

const compareText = (type) => {
  const map = { GT: '>', GTE: '>=', LT: '<', LTE: '<=' }
  return map[type] || type
}

const handleDelete = async (row) => {
  try {
    await deleteAlertRule(row.id)
    ElMessage.success('删除成功')
    loadData()
  } catch (e) {
    ElMessage.error('删除失败')
  }
}

const dialogVisible = ref(false)
const isEdit = ref(false)
const submitting = ref(false)
const formRef = ref(null)
const editingId = ref(null)

const defaultForm = () => ({
  ruleCode: '',
  ruleName: '',
  deviceType: '',
  metricKey: '',
  compareType: 'GT',
  blueThreshold: 0,
  yellowThreshold: 0,
  orangeThreshold: 0,
  redThreshold: 0,
  areaId: '',
  enabled: true
})

const form = ref(defaultForm())

const rules = {
  ruleCode: [{ required: true, message: '请输入规则编码', trigger: 'blur' }],
  ruleName: [{ required: true, message: '请输入规则名称', trigger: 'blur' }],
  deviceType: [{ required: true, message: '请选择设备类型', trigger: 'change' }],
  metricKey: [{ required: true, message: '请输入监测指标', trigger: 'blur' }],
  compareType: [{ required: true, message: '请选择比较方式', trigger: 'change' }]
}

const openDialog = (row) => {
  if (row) {
    isEdit.value = true
    editingId.value = row.id
    form.value = { ...row }
  } else {
    isEdit.value = false
    editingId.value = null
    form.value = defaultForm()
  }
  dialogVisible.value = true
}

const handleSubmit = async () => {
  if (!formRef.value) return
  await formRef.value.validate()
  submitting.value = true
  try {
    if (isEdit.value) {
      await updateAlertRule(editingId.value, form.value)
      ElMessage.success('更新成功')
    } else {
      await createAlertRule(form.value)
      ElMessage.success('创建成功')
    }
    dialogVisible.value = false
    loadData()
  } catch (e) {
    ElMessage.error(isEdit.value ? '更新失败' : '创建失败')
    console.error('提交规则失败:', e)
  } finally {
    submitting.value = false
  }
}

onMounted(() => {
  updateClock()
  clockTimer = setInterval(updateClock, 1000)
  loadData()
})

onUnmounted(() => {
  clearInterval(clockTimer)
})
</script>

<style scoped>
.rule-manage-container {
  min-height: 100vh;
  position: relative;
  overflow: hidden;
}

.bg-particles {
  position: fixed;
  top: 0; left: 0; right: 0; bottom: 0;
  pointer-events: none;
  z-index: 0;
}

.particle {
  position: absolute;
  background: #1890ff;
  border-radius: 50%;
  animation: particleFloat 6s ease-in-out infinite;
}

@keyframes particleFloat {
  0%, 100% { transform: translateY(0) scale(1); opacity: 0.2; }
  50% { transform: translateY(-30px) scale(1.5); opacity: 0.6; }
}

.page-header {
  position: relative;
  z-index: 10;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 40px;
  background: linear-gradient(180deg, rgba(10, 22, 40, 0.95) 0%, rgba(10, 22, 40, 0.7) 100%);
  border-bottom: 1px solid rgba(24, 144, 255, 0.2);
  backdrop-filter: blur(12px);
}

.header-left { flex: 1; }

.back-btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  color: #8a9bb0;
  font-size: 13px;
  cursor: pointer;
  transition: color 0.2s;
}
.back-btn:hover { color: #1890ff; }

.header-center {
  display: flex;
  align-items: center;
  gap: 24px;
  flex-shrink: 0;
}

.header-decor { display: flex; align-items: center; gap: 4px; }
.decor-line { display: block; width: 60px; height: 2px; background: linear-gradient(90deg, transparent, #1890ff); }
.right-decor .decor-line { background: linear-gradient(90deg, #1890ff, transparent); }
.decor-diamond { display: block; width: 8px; height: 8px; background: #1890ff; transform: rotate(45deg); box-shadow: 0 0 10px rgba(24, 144, 255, 0.6); }

.header-title-group { text-align: center; }
.header-title {
  font-size: 26px;
  font-weight: 700;
  margin: 0;
  letter-spacing: 6px;
  background: linear-gradient(90deg, #36cfe9, #1890ff, #36cfe9);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  filter: drop-shadow(0 0 12px rgba(24, 144, 255, 0.4));
}
.header-subtitle {
  font-size: 11px;
  color: #5a7a9a;
  margin: 6px 0 0 0;
  letter-spacing: 4px;
  text-transform: uppercase;
}

.header-right { flex: 1; text-align: right; }
.realtime-clock {
  font-size: 24px;
  font-weight: 700;
  color: #36cfe9;
  font-family: 'Courier New', monospace;
  letter-spacing: 2px;
  text-shadow: 0 0 10px rgba(54, 207, 233, 0.4);
}
.realtime-date { font-size: 12px; color: #5a7a9a; margin-top: 2px; }

.page-main {
  position: relative;
  z-index: 1;
  padding: 20px 40px;
}

.table-section {
  background: linear-gradient(135deg, rgba(27, 40, 56, 0.7), rgba(13, 27, 42, 0.8));
  border-radius: 12px;
  padding: 20px;
  border: 1px solid rgba(42, 58, 74, 0.6);
  backdrop-filter: blur(8px);
}

.panel-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 16px;
}

.panel-icon { color: #1890ff; font-size: 10px; }
.panel-title { font-size: 15px; font-weight: 600; color: #e0e6ed; letter-spacing: 1px; }
.panel-badge {
  font-size: 12px;
  color: #1890ff;
  background: rgba(24, 144, 255, 0.1);
  padding: 2px 10px;
  border-radius: 10px;
  border: 1px solid rgba(24, 144, 255, 0.2);
}

.add-btn {
  margin-left: auto;
  background: linear-gradient(135deg, #1890ff, #36cfe9) !important;
  border: none !important;
  border-radius: 8px !important;
  box-shadow: 0 4px 16px rgba(24, 144, 255, 0.3);
}

.filter-bar {
  display: flex;
  gap: 12px;
  margin-bottom: 16px;
  align-items: center;
}

.filter-input { width: 180px; }
.filter-select { width: 160px; }

.filter-btn {
  background: rgba(24, 144, 255, 0.1) !important;
  border: 1px solid rgba(24, 144, 255, 0.3) !important;
  color: #1890ff !important;
}
.filter-btn:hover {
  background: rgba(24, 144, 255, 0.2) !important;
}

.rule-table {
  --el-table-bg-color: transparent;
  --el-table-tr-bg-color: transparent;
  --el-table-header-bg-color: rgba(13, 27, 42, 0.8);
  --el-table-row-hover-bg-color: rgba(24, 144, 255, 0.06);
  --el-table-border-color: rgba(42, 58, 74, 0.4);
  --el-table-text-color: #e0e6ed;
  --el-table-header-text-color: #8a9bb0;
}

.code-cell {
  font-family: 'Courier New', monospace;
  font-size: 13px;
  color: #36cfe9;
}

.compare-tag {
  display: inline-block;
  padding: 2px 8px;
  border-radius: 4px;
  background: rgba(24, 144, 255, 0.1);
  color: #1890ff;
  font-size: 13px;
  font-weight: 600;
  font-family: 'Courier New', monospace;
}

.threshold {
  font-weight: 600;
  font-family: 'Courier New', monospace;
  font-size: 13px;
}
.threshold.blue { color: #1890ff; }
.threshold.yellow { color: #fadb14; }
.threshold.orange { color: #fa8c16; }
.threshold.red { color: #ff4d4f; }

.status-dot {
  display: inline-block;
  width: 8px;
  height: 8px;
  border-radius: 50%;
  margin-right: 6px;
  vertical-align: middle;
}
.status-dot.enabled {
  background: #52c41a;
  box-shadow: 0 0 6px rgba(82, 196, 26, 0.6);
}
.status-dot.disabled {
  background: #5a6f86;
}

.text-enabled { color: #52c41a; font-size: 13px; }
.text-disabled { color: #5a6f86; font-size: 13px; }

.pagination-bar {
  display: flex;
  justify-content: flex-end;
  margin-top: 16px;
}

.pagination-bar .el-pagination {
  --el-pagination-bg-color: transparent;
  --el-pagination-text-color: #8a9bb0;
  --el-pagination-button-bg-color: rgba(24, 144, 255, 0.1);
  --el-pagination-hover-color: #1890ff;
}

:deep(.el-select .el-input__wrapper) {
  background: rgba(13, 27, 42, 0.6) !important;
  border-color: rgba(42, 58, 74, 0.6) !important;
  box-shadow: none !important;
}
:deep(.el-select .el-input__inner) { color: #e0e6ed !important; }
:deep(.el-select .el-input__inner::placeholder) { color: #5a6f86 !important; }

:deep(.el-input__wrapper) {
  background: rgba(13, 27, 42, 0.6) !important;
  border-color: rgba(42, 58, 74, 0.6) !important;
  box-shadow: none !important;
}
:deep(.el-input__inner) { color: #e0e6ed !important; }

:deep(.el-input-number .el-input-number__decrease),
:deep(.el-input-number .el-input-number__increase) {
  background: rgba(24, 144, 255, 0.1) !important;
  border-color: rgba(42, 58, 74, 0.6) !important;
  color: #8a9bb0 !important;
}

:deep(.el-pagination button),
:deep(.el-pagination .el-pager li) {
  background: rgba(13, 27, 42, 0.6) !important;
  color: #8a9bb0 !important;
  border: 1px solid rgba(42, 58, 74, 0.4) !important;
}
:deep(.el-pagination .el-pager li.is-active) {
  background: rgba(24, 144, 255, 0.2) !important;
  color: #1890ff !important;
  border-color: rgba(24, 144, 255, 0.4) !important;
}

:deep(.el-table .el-loading-mask) {
  background: rgba(13, 27, 42, 0.5) !important;
}

/* 对话框深色适配 */
:deep(.el-dialog) {
  background: linear-gradient(135deg, #0f1c2e, #0a1628) !important;
  border: 1px solid rgba(24, 144, 255, 0.2) !important;
  border-radius: 12px !important;
}
:deep(.el-dialog__header) {
  border-bottom: 1px solid rgba(42, 58, 74, 0.6);
  padding: 16px 20px !important;
}
:deep(.el-dialog__title) {
  color: #e0e6ed !important;
  font-size: 16px;
  font-weight: 600;
}
:deep(.el-dialog__body) {
  padding: 20px !important;
}
:deep(.el-dialog__footer) {
  border-top: 1px solid rgba(42, 58, 74, 0.6);
  padding: 12px 20px !important;
}

.rule-form :deep(.el-form-item__label) {
  color: #8a9bb0 !important;
}

.dialog-btn {
  background: rgba(24, 144, 255, 0.1) !important;
  border: 1px solid rgba(24, 144, 255, 0.3) !important;
  color: #1890ff !important;
}

.submit-btn {
  background: linear-gradient(135deg, #1890ff, #36cfe9) !important;
  border: none !important;
  color: #fff !important;
}

:deep(.el-form-item) {
  margin-bottom: 18px;
}

:deep(.el-switch__core) {
  border-color: rgba(42, 58, 74, 0.6) !important;
  background: rgba(42, 58, 74, 0.6) !important;
}

:deep(.el-switch.is-checked .el-switch__core) {
  background: #1890ff !important;
  border-color: #1890ff !important;
}

:deep(.el-popconfirm) {
  background: #0f1c2e !important;
}
</style>
