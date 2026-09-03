<template>
  <div class="hazmat">
    <PageHeader title="危化品监管" subtitle="Hazardous Materials Supervision">
      <el-button @click="refreshAll">
        <el-icon><Refresh /></el-icon> 刷新
      </el-button>
      <el-button type="primary" plain @click="openForm('add')">
        <el-icon><Plus /></el-icon> 新增
      </el-button>
      <el-upload
        :show-file-list="false"
        accept=".xlsx,.xls"
        :http-request="handleImport"
        class="hazmat__upload"
      >
        <el-button plain>
          <el-icon><Upload /></el-icon> 导入
        </el-button>
      </el-upload>
      <el-button plain @click="handleExport">
        <el-icon><Download /></el-icon> 导出
      </el-button>
    </PageHeader>

    <!-- 4 个统计卡片 -->
    <div class="hazmat__stats">
      <StatCard label="介质总数" :value="overview.media_count ?? 0" icon="Files" color="#0071E3" />
      <StatCard label="预警介质" :value="overview.media_warning_count ?? 0" icon="Warning" color="#FF3B30" />
      <StatCard label="运输路径" :value="overview.route_count ?? 0" icon="Guide" color="#FF9500" />
      <StatCard label="合规率" :value="complianceText" icon="CircleCheck" color="#34C759" />
    </div>

    <!-- Tab 主体 -->
    <section class="app-card hazmat__main">
      <el-tabs v-model="activeTab" @tab-change="handleTabChange">
        <!-- ============ Tab 1 介质监测 ============ -->
        <el-tab-pane label="介质监测" name="media">
          <div class="filter-bar hazmat__filter">
            <el-select v-model="query.status" placeholder="介质状态" clearable class="hazmat__filter-item" @change="search">
              <el-option label="正常" value="normal" />
              <el-option label="预警" value="warning" />
            </el-select>
            <el-input v-model="query.keyword" placeholder="名称 / 危化品编码" clearable class="hazmat__filter-item" @keyup.enter="search" />
            <el-button type="primary" @click="search"><el-icon><Search /></el-icon> 查询</el-button>
            <el-button @click="resetQuery">重置</el-button>
          </div>
          <el-table :data="rows" v-loading="loading" class="app-table" empty-text="暂无数据">
            <el-table-column prop="media_id" label="介质ID" width="120" />
            <el-table-column prop="type_name" label="介质类型" width="110" />
            <el-table-column prop="name" label="名称" min-width="140" show-overflow-tooltip />
            <el-table-column prop="hw_code" label="危化品编码" width="130">
              <template #default="{ row }"><span class="code-cell">{{ row.hw_code }}</span></template>
            </el-table-column>
            <el-table-column prop="source" label="来源" min-width="130" show-overflow-tooltip />
            <el-table-column prop="pressure_mpa" label="压力(MPa)" width="100" align="right" />
            <el-table-column prop="temperature_c" label="温度(℃)" width="100" align="right" />
            <el-table-column prop="flow_rate_m3h" label="流量(m³/h)" width="110" align="right" />
            <el-table-column label="浓度(mg/L)" width="120" align="right">
              <template #default="{ row }">
                <span :class="{ 'value-danger': isOverThreshold(row) }">{{ row.concentration_mgL ?? '-' }}</span>
                <span v-if="row.threshold_concentration != null" class="threshold-cell"> / {{ row.threshold_concentration }}</span>
              </template>
            </el-table-column>
            <el-table-column label="状态" width="90" align="center">
              <template #default="{ row }">
                <el-tag :type="row.status === 'warning' ? 'danger' : 'success'" size="small">
                  {{ row.status === 'warning' ? '预警' : '正常' }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="last_sample" label="最近采样" width="160" />
            <el-table-column label="操作" width="220" align="center" fixed="right">
              <template #default="{ row }">
                <div class="table-actions">
                  <el-button link type="primary" size="small" @click="openDetail(row)">详情</el-button>
                  <el-button link type="primary" size="small" @click="openForm('edit', row)">编辑</el-button>
                  <el-button link type="warning" size="small" @click="handleStatusToggle(row)">
                    {{ row.status === 'warning' ? '恢复正常' : '设为预警' }}
                  </el-button>
                  <el-button link type="danger" size="small" @click="handleDelete(row)">删除</el-button>
                </div>
              </template>
            </el-table-column>
          </el-table>
        </el-tab-pane>

        <!-- ============ Tab 2 路径合规 ============ -->
        <el-tab-pane label="路径合规" name="routes">
          <div class="filter-bar hazmat__filter">
            <el-select v-model="query.status" placeholder="路径状态" clearable class="hazmat__filter-item" @change="search">
              <el-option label="已批准" value="approved" />
              <el-option label="偏离" value="deviated" />
            </el-select>
            <el-input v-model="query.keyword" placeholder="起点 / 终点 / 承运商" clearable class="hazmat__filter-item" @keyup.enter="search" />
            <el-button type="primary" @click="search"><el-icon><Search /></el-icon> 查询</el-button>
            <el-button @click="resetQuery">重置</el-button>
          </div>
          <el-table :data="rows" v-loading="loading" class="app-table" empty-text="暂无数据">
            <el-table-column prop="route_id" label="路径ID" width="120" />
            <el-table-column prop="source" label="起点" min-width="130" show-overflow-tooltip />
            <el-table-column prop="destination" label="终点" min-width="130" show-overflow-tooltip />
            <el-table-column prop="hw_code" label="危化品编码" width="130">
              <template #default="{ row }"><span class="code-cell">{{ row.hw_code }}</span></template>
            </el-table-column>
            <el-table-column prop="carrier" label="承运商" min-width="140" show-overflow-tooltip />
            <el-table-column prop="distance_km" label="距离(km)" width="100" align="right" />
            <el-table-column label="状态" width="100" align="center">
              <template #default="{ row }">
                <el-tag :type="row.status === 'deviated' ? 'danger' : 'success'" size="small">
                  {{ row.status === 'deviated' ? '偏离' : '已批准' }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="approved_date" label="批准日期" width="120" />
            <el-table-column prop="valid_until" label="有效期至" width="120" />
            <el-table-column label="操作" width="220" align="center" fixed="right">
              <template #default="{ row }">
                <div class="table-actions">
                  <el-button link type="primary" size="small" @click="openDetail(row)">详情</el-button>
                  <el-button link type="primary" size="small" @click="handleCheckRoute(row)">合规检查</el-button>
                  <el-button link type="primary" size="small" @click="openForm('edit', row)">编辑</el-button>
                  <el-button link type="warning" size="small" @click="handleStatusToggle(row)">
                    {{ row.status === 'deviated' ? '恢复批准' : '标记偏离' }}
                  </el-button>
                  <el-button link type="danger" size="small" @click="handleDelete(row)">删除</el-button>
                </div>
              </template>
            </el-table-column>
          </el-table>
        </el-tab-pane>

        <!-- ============ Tab 3 溯源管理 ============ -->
        <el-tab-pane label="溯源管理" name="traces">
          <div class="filter-bar hazmat__filter">
            <el-select v-model="query.status" placeholder="运输状态" clearable class="hazmat__filter-item" @change="search">
              <el-option label="在途" value="in_transit" />
              <el-option label="已完成" value="completed" />
            </el-select>
            <el-input v-model="query.keyword" placeholder="运单号 / 介质名称" clearable class="hazmat__filter-item" @keyup.enter="search" />
            <el-button type="primary" @click="search"><el-icon><Search /></el-icon> 查询</el-button>
            <el-button @click="resetQuery">重置</el-button>
          </div>
          <el-table :data="rows" v-loading="loading" class="app-table" empty-text="暂无数据">
            <el-table-column prop="trace_id" label="溯源ID" width="120" />
            <el-table-column prop="manifest_no" label="运单号" width="150">
              <template #default="{ row }"><span class="code-cell">{{ row.manifest_no }}</span></template>
            </el-table-column>
            <el-table-column prop="media_name" label="介质名称" min-width="130" show-overflow-tooltip />
            <el-table-column prop="hw_code" label="危化品编码" width="130" />
            <el-table-column label="运输区间" min-width="200" show-overflow-tooltip>
              <template #default="{ row }">{{ row.source }} → {{ row.destination }}</template>
            </el-table-column>
            <el-table-column prop="carrier" label="承运商" min-width="130" show-overflow-tooltip />
            <el-table-column prop="volume_m3" label="体积(m³)" width="100" align="right" />
            <el-table-column label="状态" width="100" align="center">
              <template #default="{ row }">
                <el-tag :type="traceStatusTag(row.status)" size="small">{{ traceStatusLabel(row.status) }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="generate_time" label="生成时间" width="160" />
            <el-table-column label="操作" width="220" align="center" fixed="right">
              <template #default="{ row }">
                <div class="table-actions">
                  <el-button link type="primary" size="small" @click="openDetail(row)">详情</el-button>
                  <el-button link type="primary" size="small" @click="openChain(row)">链路</el-button>
                  <el-button link type="primary" size="small" @click="openForm('edit', row)">编辑</el-button>
                  <el-button link type="warning" size="small" @click="handleStatusToggle(row)">
                    {{ row.status === 'completed' ? '标记在途' : '标记完成' }}
                  </el-button>
                  <el-button link type="danger" size="small" @click="handleDelete(row)">删除</el-button>
                </div>
              </template>
            </el-table-column>
          </el-table>
        </el-tab-pane>

        <!-- ============ Tab 4 腐蚀评估 ============ -->
        <el-tab-pane label="腐蚀评估" name="segments">
          <div class="filter-bar hazmat__filter">
            <el-select v-model="query.status" placeholder="风险等级" clearable class="hazmat__filter-item" @change="search">
              <el-option label="高风险" value="high" />
              <el-option label="中风险" value="medium" />
              <el-option label="低风险" value="low" />
            </el-select>
            <el-input v-model="query.keyword" placeholder="管段 / 位置" clearable class="hazmat__filter-item" @keyup.enter="search" />
            <el-button type="primary" @click="search"><el-icon><Search /></el-icon> 查询</el-button>
            <el-button @click="resetQuery">重置</el-button>
          </div>
          <el-table :data="rows" v-loading="loading" class="app-table" empty-text="暂无数据">
            <el-table-column prop="segment_id" label="管段ID" width="120" />
            <el-table-column prop="route_id" label="所属路径" width="120" />
            <el-table-column prop="material" label="材质" width="110" />
            <el-table-column prop="location" label="位置" min-width="150" show-overflow-tooltip />
            <el-table-column prop="original_thickness_mm" label="原壁厚(mm)" width="110" align="right" />
            <el-table-column prop="current_thickness_mm" label="现壁厚(mm)" width="110" align="right" />
            <el-table-column prop="corrosion_rate_mm_year" label="腐蚀速率(mm/年)" width="140" align="right" />
            <el-table-column prop="remaining_life_years" label="剩余寿命(年)" width="120" align="right" />
            <el-table-column label="风险等级" width="100" align="center">
              <template #default="{ row }">
                <el-tag :type="riskTagType(row.risk_level)" size="small">{{ riskLabel(row.risk_level) }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="next_inspect" label="下次巡检" width="120" />
            <el-table-column label="操作" width="220" align="center" fixed="right">
              <template #default="{ row }">
                <div class="table-actions">
                  <el-button link type="primary" size="small" @click="openDetail(row)">详情</el-button>
                  <el-button link type="primary" size="small" @click="handleEvaluate(row)">腐蚀评估</el-button>
                  <el-button link type="primary" size="small" @click="openForm('edit', row)">编辑</el-button>
                  <el-button link type="danger" size="small" @click="handleDelete(row)">删除</el-button>
                </div>
              </template>
            </el-table-column>
          </el-table>
        </el-tab-pane>

        <!-- ============ Tab 5 合规台账 ============ -->
        <el-tab-pane label="合规台账" name="ledger">
          <div class="filter-bar hazmat__filter">
            <el-select v-model="query.status" placeholder="合规情况" clearable class="hazmat__filter-item" @change="search">
              <el-option label="合规" value="true" />
              <el-option label="不合规" value="false" />
            </el-select>
            <el-input v-model="query.keyword" placeholder="工厂 / 类别 / 介质" clearable class="hazmat__filter-item" @keyup.enter="search" />
            <el-button type="primary" @click="search"><el-icon><Search /></el-icon> 查询</el-button>
            <el-button @click="resetQuery">重置</el-button>
          </div>
          <el-table :data="rows" v-loading="loading" class="app-table" empty-text="暂无数据">
            <el-table-column prop="ledger_id" label="台账ID" width="120" />
            <el-table-column prop="category_name" label="类别" width="130" />
            <el-table-column prop="factory" label="工厂" min-width="150" show-overflow-tooltip />
            <el-table-column prop="hw_code" label="危化品编码" width="130">
              <template #default="{ row }"><span class="code-cell">{{ row.hw_code }}</span></template>
            </el-table-column>
            <el-table-column prop="media_name" label="介质名称" min-width="130" show-overflow-tooltip />
            <el-table-column prop="volume_m3" label="存量(m³)" width="100" align="right" />
            <el-table-column prop="report_period" label="报告周期" width="120" />
            <el-table-column label="合规" width="90" align="center">
              <template #default="{ row }">
                <el-tag :type="row.compliant ? 'success' : 'danger'" size="small">
                  {{ row.compliant ? '合规' : '不合规' }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="issue_count" label="问题数" width="90" align="right" />
            <el-table-column prop="inspector" label="检查人" width="110" />
            <el-table-column prop="filing_date" label="归档日期" width="120" />
            <el-table-column label="操作" width="220" align="center" fixed="right">
              <template #default="{ row }">
                <div class="table-actions">
                  <el-button link type="primary" size="small" @click="openDetail(row)">详情</el-button>
                  <el-button link type="primary" size="small" @click="openForm('edit', row)">编辑</el-button>
                  <el-button link type="warning" size="small" @click="handleStatusToggle(row)">
                    {{ row.compliant ? '标记不合规' : '标记合规' }}
                  </el-button>
                  <el-button link type="danger" size="small" @click="handleDelete(row)">删除</el-button>
                </div>
              </template>
            </el-table-column>
          </el-table>
        </el-tab-pane>

        <!-- ============ Tab 6 应急阀门 ============ -->
        <el-tab-pane label="应急阀门" name="valves">
          <div class="filter-bar hazmat__filter">
            <el-input v-model="query.keyword" placeholder="阀门 / 位置" clearable class="hazmat__filter-item" @keyup.enter="search" />
            <el-button type="primary" @click="search"><el-icon><Search /></el-icon> 查询</el-button>
            <el-button @click="resetQuery">重置</el-button>
            <div class="hazmat__filter-spacer"></div>
            <el-button type="danger" plain :disabled="!rows.length" @click="handleEmergencyShutdown()">
              <el-icon><SwitchButton /></el-icon> 紧急关阀
            </el-button>
          </div>
          <el-table :data="rows" v-loading="loading" class="app-table" empty-text="暂无数据">
            <el-table-column prop="valve_id" label="阀门ID" width="120" />
            <el-table-column prop="route_id" label="所属路径" width="120" />
            <el-table-column prop="location" label="位置" min-width="160" show-overflow-tooltip />
            <el-table-column prop="valve_type" label="阀门类型" width="120" />
            <el-table-column prop="model" label="型号" width="130" />
            <el-table-column label="状态" width="100" align="center">
              <template #default="{ row }">
                <el-tag :type="valveStatusTag(row.status)" size="small">{{ row.status }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="cascade_level" label="联动级别" width="100" align="center" />
            <el-table-column prop="response_time_sec" label="响应时间(s)" width="120" align="right" />
            <el-table-column label="自动关闭" width="100" align="center">
              <template #default="{ row }">
                <el-tag :type="row.auto_close ? 'success' : 'info'" size="small" effect="plain">
                  {{ row.auto_close ? '启用' : '停用' }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="last_test" label="最近测试" width="160" />
            <el-table-column label="操作" width="220" align="center" fixed="right">
              <template #default="{ row }">
                <div class="table-actions">
                  <el-button link type="primary" size="small" @click="openDetail(row)">详情</el-button>
                  <el-button link type="primary" size="small" @click="openForm('edit', row)">编辑</el-button>
                  <el-button link type="danger" size="small" @click="handleEmergencyShutdown(row)">紧急关阀</el-button>
                  <el-button link type="danger" size="small" @click="handleDelete(row)">删除</el-button>
                </div>
              </template>
            </el-table-column>
          </el-table>
        </el-tab-pane>
      </el-tabs>

      <!-- 分页（各 Tab 共用） -->
      <div class="hazmat__pagination">
        <el-pagination
          v-model:current-page="query.page"
          v-model:page-size="query.size"
          :total="total"
          :page-sizes="[10, 20, 50]"
          layout="total, sizes, prev, pager, next"
          @size-change="loadList"
          @current-change="loadList"
        />
      </div>
    </section>

    <!-- 新增/编辑对话框 -->
    <el-dialog
      v-model="formVisible"
      :title="formMode === 'add' ? `新增${currentModule.label}` : `编辑${currentModule.label}`"
      width="680px"
      class="hazmat__dialog"
      destroy-on-close
    >
      <el-form ref="formRef" :model="form" label-width="120px">
        <el-row :gutter="16">
          <el-col v-for="f in currentModule.formFields" :key="f.prop" :span="12">
            <el-form-item :label="f.label" :prop="f.prop">
              <el-select v-if="f.type === 'select'" v-model="form[f.prop]" clearable style="width: 100%">
                <el-option v-for="o in f.options" :key="String(o.value)" :label="o.label" :value="o.value" />
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
    <el-dialog v-model="detailVisible" :title="`${currentModule.label}详情`" width="640px" class="hazmat__dialog">
      <div v-loading="detailLoading">
        <el-descriptions :column="2" border>
          <el-descriptions-item v-for="[k, v] in detailEntries" :key="k" :label="k">
            {{ formatDetailValue(v) }}
          </el-descriptions-item>
        </el-descriptions>
      </div>
      <template #footer>
        <el-button type="primary" @click="detailVisible = false">关闭</el-button>
      </template>
    </el-dialog>

    <!-- 溯源链路对话框 -->
    <el-dialog v-model="chainVisible" title="溯源链路" width="600px" class="hazmat__dialog">
      <div v-loading="chainLoading">
        <div class="hazmat__chain-head">
          <span class="code-cell">{{ chainData.manifest_no }}</span>
          <el-tag size="small" :type="traceStatusTag(chainData.current_status)">
            {{ traceStatusLabel(chainData.current_status) }}
          </el-tag>
          <span class="hazmat__chain-steps">共 {{ chainData.total_steps ?? (chainData.chain || []).length }} 步</span>
        </div>
        <el-timeline class="hazmat__chain-timeline">
          <el-timeline-item
            v-for="item in chainData.chain || []"
            :key="item.step"
            :timestamp="item.time"
            :type="item.status === 'completed' ? 'success' : item.status === 'failed' ? 'danger' : 'primary'"
            placement="top"
          >
            <div class="chain-node">
              <div class="chain-node__stage">第{{ item.step }}步 · {{ item.stage }}</div>
              <div class="chain-node__location">{{ item.location }}</div>
            </div>
          </el-timeline-item>
        </el-timeline>
      </div>
      <template #footer>
        <el-button type="primary" @click="chainVisible = false">关闭</el-button>
      </template>
    </el-dialog>

    <!-- 操作结果对话框（合规检查 / 腐蚀评估 / 紧急关阀） -->
    <el-dialog v-model="resultVisible" :title="resultTitle" width="560px" class="hazmat__dialog">
      <pre class="hazmat__result">{{ resultText }}</pre>
      <template #footer>
        <el-button type="primary" @click="resultVisible = false">关闭</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Search, Plus, Upload, Download, Refresh, SwitchButton } from '@element-plus/icons-vue'
import * as XLSX from 'xlsx'
import { saveAs } from 'file-saver'
import PageHeader from '@/components/PageHeader.vue'
import StatCard from '@/components/StatCard.vue'
import { createModuleHttp, MODULE_PREFIX } from '@/api/gateway'
import {
  getOverview,
  getMedia, getMediaDetail,
  getRoutes, getRouteDetail, checkRoute,
  getTraces, getTraceDetail, getTraceChain,
  getSegments, evaluateCorrosion,
  getLedger,
  getValves, emergencyShutdown
} from '@/api/hazmat'

// 写操作（新增/编辑/删除/状态）走同一网关前缀的 RESTful 端点
const http = createModuleHttp(MODULE_PREFIX.platform)

// ==================== 模块配置 ====================
const MODULES = {
  media: {
    label: '介质', listFn: getMedia, listKey: 'media', detailFn: getMediaDetail,
    base: '/hazmat/media', idKey: 'media_id',
    statusField: 'status',
    statusOptions: [{ value: 'normal', label: '正常' }, { value: 'warning', label: '预警' }],
    formFields: [
      { prop: 'name', label: '介质名称' },
      { prop: 'media_type', label: '介质类型代码' },
      { prop: 'type_name', label: '类型名称' },
      { prop: 'hw_code', label: '危化品编码' },
      { prop: 'source', label: '来源' },
      { prop: 'pressure_mpa', label: '压力(MPa)', type: 'number' },
      { prop: 'temperature_c', label: '温度(℃)', type: 'number' },
      { prop: 'flow_rate_m3h', label: '流量(m³/h)', type: 'number' },
      { prop: 'concentration_mgL', label: '浓度(mg/L)', type: 'number' },
      { prop: 'threshold_concentration', label: '阈值浓度', type: 'number' },
      { prop: 'status', label: '状态', type: 'select', options: [{ value: 'normal', label: '正常' }, { value: 'warning', label: '预警' }] },
      { prop: 'last_sample', label: '最近采样' }
    ]
  },
  routes: {
    label: '运输路径', listFn: getRoutes, listKey: 'routes', detailFn: getRouteDetail,
    base: '/hazmat/routes', idKey: 'route_id',
    statusField: 'status',
    statusOptions: [{ value: 'approved', label: '已批准' }, { value: 'deviated', label: '偏离' }],
    formFields: [
      { prop: 'source', label: '起点' },
      { prop: 'destination', label: '终点' },
      { prop: 'hw_code', label: '危化品编码' },
      { prop: 'carrier', label: '承运商' },
      { prop: 'distance_km', label: '距离(km)', type: 'number' },
      { prop: 'waypoints', label: '途经点' },
      { prop: 'status', label: '状态', type: 'select', options: [{ value: 'approved', label: '已批准' }, { value: 'deviated', label: '偏离' }] },
      { prop: 'approved_date', label: '批准日期', type: 'date' },
      { prop: 'valid_until', label: '有效期至', type: 'date' }
    ]
  },
  traces: {
    label: '溯源运单', listFn: getTraces, listKey: 'traces', detailFn: getTraceDetail,
    base: '/hazmat/trace', idKey: 'trace_id',
    statusField: 'status',
    statusOptions: [{ value: 'in_transit', label: '在途' }, { value: 'completed', label: '已完成' }],
    formFields: [
      { prop: 'manifest_no', label: '运单号' },
      { prop: 'media_name', label: '介质名称' },
      { prop: 'hw_code', label: '危化品编码' },
      { prop: 'source', label: '起点' },
      { prop: 'destination', label: '终点' },
      { prop: 'carrier', label: '承运商' },
      { prop: 'volume_m3', label: '体积(m³)', type: 'number' },
      { prop: 'status', label: '状态', type: 'select', options: [{ value: 'in_transit', label: '在途' }, { value: 'completed', label: '已完成' }] },
      { prop: 'generate_time', label: '生成时间' },
      { prop: 'dispatch_time', label: '发车时间' },
      { prop: 'arrive_time', label: '到达时间' },
      { prop: 'disposal_result', label: '处置结果' }
    ]
  },
  segments: {
    label: '腐蚀管段', listFn: getSegments, listKey: 'segments', detailFn: null,
    base: '/hazmat/segments', idKey: 'segment_id',
    statusField: null, statusOptions: null,
    formFields: [
      { prop: 'route_id', label: '所属路径' },
      { prop: 'material', label: '材质' },
      { prop: 'location', label: '位置' },
      { prop: 'original_thickness_mm', label: '原壁厚(mm)', type: 'number' },
      { prop: 'current_thickness_mm', label: '现壁厚(mm)', type: 'number' },
      { prop: 'corrosion_rate_mm_year', label: '腐蚀速率', type: 'number' },
      { prop: 'install_year', label: '安装年份', type: 'number' },
      { prop: 'remaining_life_years', label: '剩余寿命(年)', type: 'number' },
      { prop: 'risk_level', label: '风险等级', type: 'select', options: [{ value: 'high', label: '高风险' }, { value: 'medium', label: '中风险' }, { value: 'low', label: '低风险' }] },
      { prop: 'last_inspect', label: '上次巡检', type: 'date' },
      { prop: 'next_inspect', label: '下次巡检', type: 'date' }
    ]
  },
  ledger: {
    label: '台账记录', listFn: getLedger, listKey: 'ledger', detailFn: null,
    base: '/hazmat/ledger', idKey: 'ledger_id',
    statusField: 'compliant',
    statusOptions: [{ value: true, label: '合规' }, { value: false, label: '不合规' }],
    formFields: [
      { prop: 'category', label: '类别编码' },
      { prop: 'category_name', label: '类别名称' },
      { prop: 'factory', label: '工厂' },
      { prop: 'hw_code', label: '危化品编码' },
      { prop: 'media_name', label: '介质名称' },
      { prop: 'volume_m3', label: '存量(m³)', type: 'number' },
      { prop: 'report_period', label: '报告周期' },
      { prop: 'compliant', label: '是否合规', type: 'select', options: [{ value: true, label: '合规' }, { value: false, label: '不合规' }] },
      { prop: 'issue_count', label: '问题数', type: 'number' },
      { prop: 'inspector', label: '检查人' },
      { prop: 'filing_date', label: '归档日期', type: 'date' }
    ]
  },
  valves: {
    label: '应急阀门', listFn: getValves, listKey: 'valves', detailFn: null,
    base: '/hazmat/valves', idKey: 'valve_id',
    statusField: null, statusOptions: null,
    formFields: [
      { prop: 'route_id', label: '所属路径' },
      { prop: 'location', label: '位置' },
      { prop: 'valve_type', label: '阀门类型' },
      { prop: 'model', label: '型号' },
      { prop: 'status', label: '状态' },
      { prop: 'cascade_level', label: '联动级别', type: 'number' },
      { prop: 'response_time_sec', label: '响应时间(s)', type: 'number' },
      { prop: 'auto_close', label: '自动关闭', type: 'select', options: [{ value: true, label: '启用' }, { value: false, label: '停用' }] },
      { prop: 'last_test', label: '最近测试' }
    ]
  }
}

const activeTab = ref('media')
const currentModule = computed(() => MODULES[activeTab.value])

// ==================== 总览统计 ====================
const overview = ref({})

const complianceText = computed(() => {
  const r = Number(overview.value.compliance_rate)
  if (isNaN(r)) return '0%'
  return `${(r <= 1 ? r * 100 : r).toFixed(1)}%`
})

async function loadOverview() {
  try {
    overview.value = (await getOverview()) || {}
  } catch (e) {
    ElMessage.error('加载总览数据失败')
    console.error(e)
  }
}

// ==================== 列表加载（各 Tab 共用） ====================
const rows = ref([])
const total = ref(0)
const loading = ref(false)
const query = ref({ page: 1, size: 10, keyword: '', status: '' })

async function loadList() {
  loading.value = true
  try {
    const mod = currentModule.value
    const params = { page: query.value.page, size: query.value.size }
    if (query.value.keyword) params.keyword = query.value.keyword
    if (query.value.status !== '' && query.value.status != null) params.status = query.value.status
    const res = await mod.listFn(params)
    rows.value = res?.[mod.listKey] || []
    total.value = res?.total || 0
  } catch (e) {
    ElMessage.error(`加载${currentModule.value.label}列表失败`)
    console.error(e)
  } finally {
    loading.value = false
  }
}

function search() {
  query.value.page = 1
  loadList()
}

function resetQuery() {
  query.value = { page: 1, size: 10, keyword: '', status: '' }
  loadList()
}

function handleTabChange() {
  resetQuery()
}

function rowId(row) {
  return row[currentModule.value.idKey] ?? row.id
}

// ==================== 新增 / 编辑 ====================
const formVisible = ref(false)
const formMode = ref('add')
const formSubmitting = ref(false)
const formRef = ref(null)
const form = reactive({})
const editingId = ref(null)

function openForm(mode, row) {
  formMode.value = mode
  Object.keys(form).forEach(k => delete form[k])
  if (mode === 'edit' && row) {
    editingId.value = rowId(row)
    currentModule.value.formFields.forEach(f => { form[f.prop] = row[f.prop] ?? undefined })
  } else {
    editingId.value = null
  }
  formVisible.value = true
}

async function submitForm() {
  formSubmitting.value = true
  try {
    const mod = currentModule.value
    const body = { ...form }
    if (formMode.value === 'add') {
      await http.post(mod.base, body)
      ElMessage.success('新增成功')
    } else {
      await http.put(`${mod.base}/${editingId.value}`, body)
      ElMessage.success('保存成功')
    }
    formVisible.value = false
    loadList()
    loadOverview()
  } catch (e) {
    ElMessage.error(formMode.value === 'add' ? '新增失败' : '保存失败')
    console.error(e)
  } finally {
    formSubmitting.value = false
  }
}

// ==================== 删除 ====================
async function handleDelete(row) {
  const mod = currentModule.value
  const id = rowId(row)
  try {
    await ElMessageBox.confirm(`确认删除该${mod.label}记录（${id}）吗？删除后不可恢复。`, '删除确认', {
      type: 'warning',
      confirmButtonText: '删除',
      cancelButtonText: '取消'
    })
  } catch {
    return
  }
  try {
    await http.delete(`${mod.base}/${id}`)
    ElMessage.success('删除成功')
    loadList()
    loadOverview()
  } catch (e) {
    ElMessage.error('删除失败')
    console.error(e)
  }
}

// ==================== 状态变更（直接调用 API） ====================
async function handleStatusToggle(row) {
  const mod = currentModule.value
  if (!mod.statusOptions) return
  const id = rowId(row)
  const current = row[mod.statusField]
  const next = mod.statusOptions.find(o => o.value !== current) || mod.statusOptions[0]
  try {
    await http.put(`${mod.base}/${id}/status`, { [mod.statusField]: next.value })
    ElMessage.success(`状态已更新为「${next.label}」`)
    loadList()
    loadOverview()
  } catch (e) {
    ElMessage.error('状态变更失败')
    console.error(e)
  }
}

// ==================== 详情 ====================
const detailVisible = ref(false)
const detailLoading = ref(false)
const detailEntries = ref([])

async function openDetail(row) {
  detailVisible.value = true
  detailEntries.value = Object.entries(row)
  const mod = currentModule.value
  if (!mod.detailFn) return
  detailLoading.value = true
  try {
    const detail = await mod.detailFn(rowId(row))
    if (detail) detailEntries.value = Object.entries(detail)
  } catch (e) {
    console.error('加载详情失败，展示列表行数据:', e)
  } finally {
    detailLoading.value = false
  }
}

// ==================== 溯源链路 ====================
const chainVisible = ref(false)
const chainLoading = ref(false)
const chainData = ref({})

async function openChain(row) {
  chainVisible.value = true
  chainLoading.value = true
  chainData.value = {}
  try {
    chainData.value = (await getTraceChain(row.trace_id)) || {}
  } catch (e) {
    ElMessage.error('加载溯源链路失败')
    console.error(e)
  } finally {
    chainLoading.value = false
  }
}

// ==================== 专项操作：合规检查 / 腐蚀评估 / 紧急关阀 ====================
const resultVisible = ref(false)
const resultTitle = ref('操作结果')
const resultText = ref('')

function showResult(title, res) {
  resultTitle.value = title
  resultText.value = JSON.stringify(res ?? {}, null, 2)
  resultVisible.value = true
}

async function handleCheckRoute(row) {
  try {
    const res = await checkRoute({ route_id: row.route_id, hw_code: row.hw_code })
    showResult('路径合规检查结果', res)
  } catch (e) {
    ElMessage.error('合规检查失败')
    console.error(e)
  }
}

async function handleEvaluate(row) {
  try {
    const res = await evaluateCorrosion({
      segment_id: row.segment_id,
      original_thickness_mm: row.original_thickness_mm,
      current_thickness_mm: row.current_thickness_mm,
      corrosion_rate_mm_year: row.corrosion_rate_mm_year
    })
    showResult('腐蚀评估结果', res)
    loadList()
  } catch (e) {
    ElMessage.error('腐蚀评估失败')
    console.error(e)
  }
}

async function handleEmergencyShutdown(row) {
  const target = row || rows.value[0]
  if (!target) return ElMessage.warning('暂无可操作的阀门')
  try {
    await ElMessageBox.confirm(
      `确认对阀门「${target.valve_id}」（${target.location || '-'}）执行紧急关阀吗？该操作将立即切断输送。`,
      '紧急关阀确认',
      { type: 'error', confirmButtonText: '立即关阀', cancelButtonText: '取消' }
    )
  } catch {
    return
  }
  try {
    const res = await emergencyShutdown({ valve_id: target.valve_id, route_id: target.route_id })
    showResult('紧急关阀执行结果', res)
    loadList()
    loadOverview()
  } catch (e) {
    ElMessage.error('紧急关阀失败')
    console.error(e)
  }
}

// ==================== Excel 导入 / 导出 ====================
async function handleImport({ file }) {
  const mod = currentModule.value
  try {
    const buf = await file.arrayBuffer()
    const wb = XLSX.read(buf, { type: 'array' })
    const ws = wb.Sheets[wb.SheetNames[0]]
    const data = XLSX.utils.sheet_to_json(ws)
    if (!data.length) return ElMessage.warning('文件中没有可导入的数据')
    await http.post(`${mod.base}/import`, { rows: data })
    ElMessage.success(`成功导入 ${data.length} 条${mod.label}数据`)
    loadList()
    loadOverview()
  } catch (e) {
    ElMessage.error('导入失败：' + (e?.message || '未知错误'))
    console.error(e)
  }
}

function handleExport() {
  const mod = currentModule.value
  if (!rows.value.length) return ElMessage.warning('暂无数据可导出')
  const wb = XLSX.utils.book_new()
  XLSX.utils.book_append_sheet(wb, XLSX.utils.json_to_sheet(rows.value), 'Sheet1')
  const buf = XLSX.write(wb, { bookType: 'xlsx', type: 'array' })
  saveAs(
    new Blob([buf], { type: 'application/octet-stream' }),
    `危化品_${mod.label}_${Date.now()}.xlsx`
  )
  ElMessage.success('导出成功')
}

// ==================== 展示辅助 ====================
function isOverThreshold(row) {
  return row.concentration_mgL != null
    && row.threshold_concentration != null
    && Number(row.concentration_mgL) > Number(row.threshold_concentration)
}

function traceStatusLabel(status) {
  const map = { in_transit: '在途', completed: '已完成', pending: '待发车', failed: '异常' }
  return map[status] || status || '-'
}
function traceStatusTag(status) {
  const map = { in_transit: 'warning', completed: 'success', pending: 'info', failed: 'danger' }
  return map[status] || 'info'
}

function riskLabel(level) {
  const map = { high: '高风险', medium: '中风险', low: '低风险' }
  return map[level] || level || '-'
}
function riskTagType(level) {
  const map = { high: 'danger', medium: 'warning', low: 'success' }
  return map[level] || 'info'
}

function valveStatusTag(status) {
  const map = { normal: 'success', online: 'success', open: 'success', closed: 'warning', fault: 'danger', offline: 'info' }
  return map[String(status || '').toLowerCase()] || 'info'
}

function formatDetailValue(v) {
  if (v == null || v === '') return '-'
  if (typeof v === 'boolean') return v ? '是' : '否'
  if (typeof v === 'object') return JSON.stringify(v)
  return v
}

async function refreshAll() {
  await Promise.all([loadOverview(), loadList()])
}

onMounted(() => {
  loadOverview()
  loadList()
})
</script>

<style scoped>
/* ===== 布局 ===== */
.hazmat__stats {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
  margin-bottom: 16px;
}
.hazmat__main {
  padding: 16px 24px 24px;
}
.hazmat__upload {
  display: inline-flex;
}

/* ===== 筛选条 ===== */
.hazmat__filter {
  margin-bottom: 16px;
}
.hazmat__filter-item {
  width: 160px;
}
.hazmat__filter-spacer {
  flex: 1;
}
.hazmat__pagination {
  display: flex;
  justify-content: flex-end;
  margin-top: 16px;
}

/* ===== 表格单元 ===== */
.code-cell {
  font-family: 'Courier New', monospace;
  font-size: 13px;
  color: var(--app-primary);
}
.threshold-cell {
  color: var(--app-text-3);
  font-size: 12px;
}
.value-danger {
  color: var(--app-color-red);
  font-weight: 600;
}

/* ===== 溯源链路 ===== */
.hazmat__chain-head {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 20px;
}
.hazmat__chain-steps {
  font-size: 13px;
  color: var(--app-text-3);
  margin-left: auto;
}
.hazmat__chain-timeline {
  padding-left: 4px;
  max-height: 420px;
  overflow-y: auto;
}
.chain-node__stage {
  font-size: 14px;
  font-weight: 600;
  color: var(--app-text-1);
}
.chain-node__location {
  font-size: 13px;
  color: var(--app-text-3);
  margin-top: 2px;
}

/* ===== 对话框 ===== */
.hazmat__dialog {
  border-radius: var(--app-radius-card);
}
.hazmat__result {
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
  .hazmat__stats { grid-template-columns: repeat(2, 1fr); }
}
@media (max-width: 640px) {
  .hazmat__stats { grid-template-columns: 1fr; }
}
</style>
