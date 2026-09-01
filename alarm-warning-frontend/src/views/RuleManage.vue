<template>
  <div class="rule-manage">
    <PageHeader title="预警规则管理">
      <el-button type="primary" @click="openDialog(null)">
        <el-icon><Plus /></el-icon> 新增规则
      </el-button>
    </PageHeader>

    <section class="app-card rule-manage__table-card">
      <!-- 筛选栏 -->
      <div class="filter-bar rule-manage__filter">
        <el-input
          v-model="query.ruleName"
          placeholder="规则名称"
          clearable
          class="rule-manage__filter-item"
          @keyup.enter="loadData"
        />
        <el-select v-model="query.deviceType" placeholder="设备类型" clearable class="rule-manage__filter-item">
          <el-option label="全部" value="" />
          <el-option label="温度传感器" value="TEMPERATURE" />
          <el-option label="湿度传感器" value="HUMIDITY" />
          <el-option label="气体检测器" value="GAS_DETECTOR" />
          <el-option label="水位传感器" value="WATER_LEVEL" />
          <el-option label="压力传感器" value="PRESSURE" />
        </el-select>
        <el-select v-model="query.enabled" placeholder="启用状态" clearable class="rule-manage__filter-item">
          <el-option label="全部" value="" />
          <el-option label="已启用" :value="true" />
          <el-option label="已禁用" :value="false" />
        </el-select>
        <el-button type="primary" @click="loadData">
          <el-icon><Search /></el-icon> 查询
        </el-button>
        <el-button @click="resetQuery">重置</el-button>
      </div>

      <!-- 表格 -->
      <el-table :data="tableData" v-loading="tableLoading" class="app-table">
        <el-table-column prop="ruleCode" label="规则编码" min-width="160">
          <template #default="{ row }"><span class="code-cell">{{ row.ruleCode }}</span></template>
        </el-table-column>
        <el-table-column prop="ruleName" label="规则名称" min-width="160" />
        <el-table-column prop="deviceType" label="设备类型" width="120" />
        <el-table-column prop="metricKey" label="监测指标" width="120" />
        <el-table-column label="比较方式" width="100" align="center">
          <template #default="{ row }"><span class="compare-tag">{{ compareText(row.compareType) }}</span></template>
        </el-table-column>
        <el-table-column label="蓝色阈值" width="100" align="center">
          <template #default="{ row }"><span class="threshold threshold--blue">{{ row.blueThreshold }}</span></template>
        </el-table-column>
        <el-table-column label="黄色阈值" width="100" align="center">
          <template #default="{ row }"><span class="threshold threshold--yellow">{{ row.yellowThreshold }}</span></template>
        </el-table-column>
        <el-table-column label="橙色阈值" width="100" align="center">
          <template #default="{ row }"><span class="threshold threshold--orange">{{ row.orangeThreshold }}</span></template>
        </el-table-column>
        <el-table-column label="红色阈值" width="100" align="center">
          <template #default="{ row }"><span class="threshold threshold--red">{{ row.redThreshold }}</span></template>
        </el-table-column>
        <el-table-column label="状态" width="90" align="center">
          <template #default="{ row }">
            <span class="status-dot" :class="row.enabled ? 'status-dot--enabled' : 'status-dot--disabled'"></span>
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

      <!-- 分页 -->
      <div class="rule-manage__pagination">
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

    <!-- 新增/编辑对话框：Element Plus 默认浅色样式，不覆盖任何 el-dialog 深色 -->
    <el-dialog
      v-model="dialogVisible"
      :title="isEdit ? '编辑规则' : '新增规则'"
      width="640px"
      destroy-on-close
    >
      <el-form ref="formRef" :model="form" :rules="rules" label-width="100px">
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
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitting" @click="handleSubmit">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Plus, Search } from '@element-plus/icons-vue'
import PageHeader from '@/components/PageHeader.vue'
import { getAlertRuleList, createAlertRule, updateAlertRule, deleteAlertRule } from '@/api/alertRule'

// 查询条件 + 表格数据
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

// 比较方式文本映射
const compareText = (type) => {
  const map = { GT: '>', GTE: '>=', LT: '<', LTE: '<=' }
  return map[type] || type
}

// 删除规则
const handleDelete = async (row) => {
  try {
    await deleteAlertRule(row.id)
    ElMessage.success('删除成功')
    loadData()
  } catch (e) {
    ElMessage.error('删除失败')
  }
}

// ===== Dialog 表单 =====
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

// 提交：表单校验 + 新增/更新
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
  loadData()
})
</script>

<style scoped>
.rule-manage__table-card {
  padding: 16px 20px;
}
.rule-manage__filter {
  margin-bottom: 16px;
}
.rule-manage__filter-item {
  width: 180px;
}
.rule-manage__pagination {
  display: flex;
  justify-content: flex-end;
  margin-top: 16px;
}

/* 表格内单元样式 */
.code-cell {
  font-family: 'Courier New', monospace;
  font-size: 13px;
  color: var(--app-primary);
}
.compare-tag {
  display: inline-block;
  padding: 2px 8px;
  border-radius: 4px;
  background-color: rgba(41, 121, 255, 0.1);
  color: var(--app-primary);
  font-size: 13px;
  font-weight: 600;
  font-family: 'Courier New', monospace;
}
.threshold {
  font-weight: 600;
  font-family: 'Courier New', monospace;
  font-size: 13px;
}
.threshold--blue { color: #2979FF; }
.threshold--yellow { color: #FAAD14; }
.threshold--orange { color: #FA8C16; }
.threshold--red { color: #F5222D; }

.status-dot {
  display: inline-block;
  width: 8px;
  height: 8px;
  border-radius: 50%;
  margin-right: 6px;
  vertical-align: middle;
}
.status-dot--enabled { background: #52C41A; }
.status-dot--disabled { background: var(--app-text-3); }
.text-enabled { color: #52C41A; font-size: 13px; }
.text-disabled { color: var(--app-text-3); font-size: 13px; }
</style>
