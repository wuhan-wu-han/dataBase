<template>
  <div class="tunnel">
    <PageHeader title="综合管廊" subtitle="Utility Tunnel">
      <el-button @click="refreshAll">
        <el-icon><Refresh /></el-icon> 刷新
      </el-button>
    </PageHeader>

    <!-- 4 个统计卡片 -->
    <div class="tunnel__stats">
      <StatCard label="传感器在线率" :value="`${overview.online_rate ?? 0}%`" icon="Monitor" color="#34C759" />
      <StatCard label="今日告警" :value="overview.alarms_today ?? 0" icon="Bell" color="#FF9500" />
      <StatCard label="管线数量" :value="overview.pipeline_count ?? 0" icon="Share" color="#0071E3" />
      <StatCard label="管内人数" :value="overview.in_tunnel_count ?? 0" icon="User" color="#FF3B30" />
    </div>

    <!-- 分模块标签页 -->
    <section class="app-card tunnel__tabs-card">
      <el-tabs v-model="activeTab">
        <!-- ============ Tab 1 环境监测 ============ -->
        <el-tab-pane label="环境监测" name="env">
          <div class="filter-bar tunnel__filter">
            <el-select v-model="envQuery.cabin" placeholder="舱室" clearable class="tunnel__filter-item" @change="loadEnv">
              <el-option v-for="c in cabins" :key="c.code" :label="c.name" :value="c.code" />
            </el-select>
            <el-select v-model="envQuery.online" placeholder="在线状态" clearable class="tunnel__filter-item">
              <el-option label="全部" value="" />
              <el-option label="在线" :value="true" />
              <el-option label="离线" :value="false" />
            </el-select>
            <el-input
              v-model="envQuery.keyword"
              placeholder="传感器ID/名称"
              clearable
              class="tunnel__filter-item"
            />
            <el-button type="primary" @click="loadEnv">
              <el-icon><Search /></el-icon> 查询
            </el-button>
            <el-button @click="resetEnvQuery">重置</el-button>
            <el-button class="tunnel__export-btn" @click="exportEnv">
              <el-icon><Download /></el-icon> 导出Excel
            </el-button>
          </div>

          <el-table :data="envPaged" v-loading="envLoading" class="app-table">
            <el-table-column prop="sensor_id" label="传感器ID" min-width="140">
              <template #default="{ row }"><span class="code-cell">{{ row.sensor_id }}</span></template>
            </el-table-column>
            <el-table-column prop="sensor_name" label="名称" min-width="150" show-overflow-tooltip />
            <el-table-column prop="cabin_name" label="舱室" width="100" />
            <el-table-column prop="zone_code" label="区段" width="80" align="center" />
            <el-table-column label="在线" width="80" align="center">
              <template #default="{ row }">
                <el-tag :type="row.online ? 'success' : 'info'" size="small">
                  {{ row.online ? '在线' : '离线' }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column
              v-for="key in envMetricKeys"
              :key="key"
              :label="envMetricLabels[key]"
              width="110"
              align="center"
            >
              <template #default="{ row }">
                <span v-if="row.metrics && row.metrics[key]" class="metric-cell" :class="metricLevelClass(row.metrics[key].level)">
                  {{ row.metrics[key].value }}<span class="metric-cell__unit">{{ row.metrics[key].unit }}</span>
                </span>
                <span v-else class="metric-cell--empty">-</span>
              </template>
            </el-table-column>
            <el-table-column label="操作" width="90" align="center" fixed="right">
              <template #default="{ row }">
                <div class="table-actions">
                  <el-button link type="primary" size="small" @click="openEnvDetail(row)">详情</el-button>
                </div>
              </template>
            </el-table-column>
          </el-table>

          <div class="tunnel__pagination">
            <el-pagination
              v-model:current-page="envPage"
              v-model:page-size="envSize"
              :total="envFiltered.length"
              :page-sizes="[10, 20, 50]"
              layout="total, sizes, prev, pager, next"
            />
          </div>
        </el-tab-pane>

        <!-- ============ Tab 2 告警管理 ============ -->
        <el-tab-pane label="告警管理" name="alarm">
          <div class="filter-bar tunnel__filter">
            <el-select v-model="alarmQuery.cabin" placeholder="舱室" clearable class="tunnel__filter-item" @change="loadAlarms">
              <el-option v-for="c in cabins" :key="c.code" :label="c.name" :value="c.code" />
            </el-select>
            <el-select v-model="alarmQuery.level" placeholder="严重度" clearable class="tunnel__filter-item" @change="loadAlarms">
              <el-option label="全部" value="" />
              <el-option label="预警" :value="1" />
              <el-option label="严重" :value="2" />
            </el-select>
            <el-select v-model="alarmQuery.status" placeholder="处理状态" clearable class="tunnel__filter-item" @change="loadAlarms">
              <el-option label="全部" value="" />
              <el-option label="未处理" value="未处理" />
              <el-option label="处理中" value="处理中" />
              <el-option label="已处理" value="已处理" />
            </el-select>
            <el-button type="primary" @click="loadAlarms">
              <el-icon><Search /></el-icon> 查询
            </el-button>
            <el-button @click="resetAlarmQuery">重置</el-button>
            <el-button class="tunnel__export-btn" @click="exportAlarms">
              <el-icon><Download /></el-icon> 导出Excel
            </el-button>
          </div>

          <el-table :data="alarmPaged" v-loading="alarmLoading" class="app-table">
            <el-table-column prop="alarm_id" label="告警ID" min-width="140">
              <template #default="{ row }"><span class="code-cell">{{ row.alarm_id }}</span></template>
            </el-table-column>
            <el-table-column label="时间" width="170">
              <template #default="{ row }"><span class="time-cell">{{ row.time }}</span></template>
            </el-table-column>
            <el-table-column prop="cabin" label="舱室" width="80" align="center" />
            <el-table-column prop="zone_code" label="区段" width="80" align="center" />
            <el-table-column prop="metric_name" label="指标" width="110" />
            <el-table-column label="监测值" width="120" align="center">
              <template #default="{ row }">
                <span class="metric-value">{{ row.value }}</span>
                <span class="metric-unit">{{ row.unit }}</span>
              </template>
            </el-table-column>
            <el-table-column label="严重度" width="90" align="center">
              <template #default="{ row }">
                <el-tag :type="row.level === 2 ? 'danger' : 'warning'" size="small">
                  {{ row.severity || (row.level === 2 ? '严重' : '预警') }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column label="状态" width="90" align="center">
              <template #default="{ row }">
                <el-tag :type="alarmStatusType(row.status)" size="small">{{ row.status }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="desc" label="描述" min-width="200" show-overflow-tooltip />
            <el-table-column label="操作" width="130" align="center" fixed="right">
              <template #default="{ row }">
                <div class="table-actions">
                  <el-button link type="primary" size="small" @click="openAlarmDetail(row)">详情</el-button>
                  <el-button
                    v-if="row.status === '未处理'"
                    link type="warning" size="small"
                    @click="handleAck(row)"
                  >确认</el-button>
                </div>
              </template>
            </el-table-column>
          </el-table>

          <div class="tunnel__pagination">
            <el-pagination
              v-model:current-page="alarmPage"
              v-model:page-size="alarmSize"
              :total="alarms.length"
              :page-sizes="[10, 20, 50]"
              layout="total, sizes, prev, pager, next"
            />
          </div>
        </el-tab-pane>

        <!-- ============ Tab 3 管线管理 ============ -->
        <el-tab-pane label="管线管理" name="pipeline">
          <div class="filter-bar tunnel__filter">
            <el-select v-model="pipeQuery.cabin" placeholder="舱室" clearable class="tunnel__filter-item" @change="loadPipelines">
              <el-option v-for="c in cabins" :key="c.code" :label="c.name" :value="c.code" />
            </el-select>
            <el-select v-model="pipeQuery.pipeline_type" placeholder="管线类型" clearable class="tunnel__filter-item" @change="loadPipelines">
              <el-option label="全部" value="" />
              <el-option v-for="t in PIPELINE_TYPES" :key="t" :label="t" :value="t" />
            </el-select>
            <el-select v-model="pipeQuery.status" placeholder="状态" clearable class="tunnel__filter-item">
              <el-option label="全部" value="" />
              <el-option v-for="s in PIPELINE_STATUS" :key="s" :label="s" :value="s" />
            </el-select>
            <el-button type="primary" @click="loadPipelines">
              <el-icon><Search /></el-icon> 查询
            </el-button>
            <el-button @click="resetPipeQuery">重置</el-button>
            <el-button type="primary" plain @click="openPipeDialog(null)">
              <el-icon><Plus /></el-icon> 新增管线
            </el-button>
            <el-upload
              class="tunnel__upload"
              accept=".xlsx,.xls"
              :show-file-list="false"
              :http-request="importPipelines"
            >
              <el-button plain>
                <el-icon><Upload /></el-icon> 导入Excel
              </el-button>
            </el-upload>
            <el-button class="tunnel__export-btn" @click="exportPipelines">
              <el-icon><Download /></el-icon> 导出Excel
            </el-button>
          </div>

          <el-table :data="pipePaged" v-loading="pipeLoading" class="app-table">
            <el-table-column prop="pipeline_id" label="管线ID" min-width="130">
              <template #default="{ row }"><span class="code-cell">{{ row.pipeline_id }}</span></template>
            </el-table-column>
            <el-table-column prop="pipeline_type" label="类型" width="90" align="center" />
            <el-table-column prop="cabin" label="舱室" width="80" align="center" />
            <el-table-column label="区段" width="110" align="center">
              <template #default="{ row }">Z{{ String(row.zone_start).padStart(2, '0') }} ~ Z{{ String(row.zone_end).padStart(2, '0') }}</template>
            </el-table-column>
            <el-table-column prop="diameter_mm" label="管径(mm)" width="100" align="center" />
            <el-table-column prop="material" label="材质" width="110" show-overflow-tooltip />
            <el-table-column prop="owner_unit" label="权属单位" min-width="140" show-overflow-tooltip />
            <el-table-column label="状态" width="90" align="center">
              <template #default="{ row }">
                <el-tag :type="pipeStatusType(row.status)" size="small">{{ row.status }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column label="操作" width="220" align="center" fixed="right">
              <template #default="{ row }">
                <div class="table-actions">
                  <el-button link type="primary" size="small" @click="openPipeDetail(row)">详情</el-button>
                  <el-button link type="primary" size="small" @click="openPipeDialog(row)">编辑</el-button>
                  <el-button link type="warning" size="small" @click="handleStatusChange(row)">状态变更</el-button>
                  <el-button link type="danger" size="small" @click="handlePipeDelete(row)">删除</el-button>
                </div>
              </template>
            </el-table-column>
          </el-table>

          <div class="tunnel__pagination">
            <el-pagination
              v-model:current-page="pipePage"
              v-model:page-size="pipeSize"
              :total="pipelinesFiltered.length"
              :page-sizes="[10, 20, 50]"
              layout="total, sizes, prev, pager, next"
            />
          </div>
        </el-tab-pane>

        <!-- ============ Tab 4 安防管理 ============ -->
        <el-tab-pane label="安防管理" name="security">
          <div class="tunnel__security-grid" v-loading="secLoading">
            <!-- 门禁出入记录 -->
            <div class="tunnel__security-panel">
              <header class="card-title">
                <h3 class="card-title__text">门禁出入记录</h3>
                <div class="tunnel__security-actions">
                  <el-button size="small" type="primary" plain @click="openAccessDialog">
                    <el-icon><Plus /></el-icon> 登记出入
                  </el-button>
                  <el-upload
                    class="tunnel__upload"
                    accept=".xlsx,.xls"
                    :show-file-list="false"
                    :http-request="importAccessRecords"
                  >
                    <el-button size="small" plain>
                      <el-icon><Upload /></el-icon> 导入
                    </el-button>
                  </el-upload>
                  <el-button size="small" @click="exportAccess">
                    <el-icon><Download /></el-icon> 导出
                  </el-button>
                </div>
              </header>
              <el-table :data="accessPaged" class="app-table" max-height="420">
                <el-table-column label="时间" width="165">
                  <template #default="{ row }"><span class="time-cell">{{ row.time }}</span></template>
                </el-table-column>
                <el-table-column prop="gate_name" label="门禁" min-width="130" show-overflow-tooltip />
                <el-table-column prop="person_name" label="人员" width="100" />
                <el-table-column label="方向" width="70" align="center">
                  <template #default="{ row }">
                    <el-tag :type="row.direction === '进' ? 'success' : 'info'" size="small">{{ row.direction }}</el-tag>
                  </template>
                </el-table-column>
                <el-table-column label="授权" width="80" align="center">
                  <template #default="{ row }">
                    <el-tag :type="row.authorized ? 'success' : 'danger'" size="small">
                      {{ row.authorized ? '已授权' : '未授权' }}
                    </el-tag>
                  </template>
                </el-table-column>
                <el-table-column label="操作" width="70" align="center">
                  <template #default="{ row }">
                    <el-button link type="primary" size="small" @click="openAccessDetail(row)">详情</el-button>
                  </template>
                </el-table-column>
              </el-table>
              <div class="tunnel__pagination">
                <el-pagination
                  v-model:current-page="accessPage"
                  v-model:page-size="accessSize"
                  :total="accessRecords.length"
                  :page-sizes="[10, 20, 50]"
                  layout="total, prev, pager, next"
                  small
                />
              </div>
            </div>

            <!-- 入侵检测告警 -->
            <div class="tunnel__security-panel">
              <header class="card-title">
                <h3 class="card-title__text">入侵检测告警</h3>
                <el-button size="small" @click="exportIntrusions">
                  <el-icon><Download /></el-icon> 导出
                </el-button>
              </header>
              <el-table :data="intrusions" class="app-table" max-height="420">
                <el-table-column prop="intrusion_id" label="告警ID" min-width="130">
                  <template #default="{ row }"><span class="code-cell">{{ row.intrusion_id }}</span></template>
                </el-table-column>
                <el-table-column prop="zone_name" label="防区" min-width="140" show-overflow-tooltip />
                <el-table-column label="等级" width="80" align="center">
                  <template #default="{ row }">
                    <el-tag :type="row.level === 2 ? 'danger' : 'warning'" size="small">
                      {{ row.level === 2 ? '严重' : '一般' }}
                    </el-tag>
                  </template>
                </el-table-column>
                <el-table-column label="状态" width="90" align="center">
                  <template #default="{ row }">
                    <el-tag :type="row.status === '未处理' ? 'danger' : 'success'" size="small">{{ row.status }}</el-tag>
                  </template>
                </el-table-column>
                <el-table-column label="时间" width="165">
                  <template #default="{ row }"><span class="time-cell">{{ row.time }}</span></template>
                </el-table-column>
              </el-table>
            </div>
          </div>
        </el-tab-pane>
      </el-tabs>
    </section>

    <!-- ============ 传感器详情对话框 ============ -->
    <el-dialog v-model="envDetailVisible" title="传感器详情" width="620px" class="tunnel__dialog">
      <el-descriptions v-if="envDetail" :column="2" border>
        <el-descriptions-item label="传感器ID">{{ envDetail.sensor_id }}</el-descriptions-item>
        <el-descriptions-item label="名称">{{ envDetail.sensor_name }}</el-descriptions-item>
        <el-descriptions-item label="类型">{{ envDetail.sensor_type }}</el-descriptions-item>
        <el-descriptions-item label="在线状态">
          <el-tag :type="envDetail.online ? 'success' : 'info'" size="small">{{ envDetail.online ? '在线' : '离线' }}</el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="舱室">{{ envDetail.cabin_name }}（{{ envDetail.cabin }}）</el-descriptions-item>
        <el-descriptions-item label="区段">{{ envDetail.zone_code }}</el-descriptions-item>
      </el-descriptions>
      <h4 class="tunnel__dialog-subtitle">监测指标</h4>
      <el-table v-if="envDetail" :data="envDetailMetrics" class="app-table" size="small">
        <el-table-column prop="name" label="指标" min-width="100" />
        <el-table-column label="数值" width="120" align="center">
          <template #default="{ row }">
            <span class="metric-cell" :class="metricLevelClass(row.level)">{{ row.value }}{{ row.unit }}</span>
          </template>
        </el-table-column>
        <el-table-column label="等级" width="90" align="center">
          <template #default="{ row }">
            <el-tag :type="levelTagType(row.level)" size="small">{{ levelText(row.level) }}</el-tag>
          </template>
        </el-table-column>
      </el-table>
    </el-dialog>

    <!-- ============ 告警详情对话框 ============ -->
    <el-dialog v-model="alarmDetailVisible" title="告警详情" width="620px" class="tunnel__dialog">
      <el-descriptions v-if="alarmDetail" :column="2" border>
        <el-descriptions-item label="告警ID">{{ alarmDetail.alarm_id }}</el-descriptions-item>
        <el-descriptions-item label="告警码">{{ alarmDetail.alarm_code }}</el-descriptions-item>
        <el-descriptions-item label="来源">{{ alarmDetail.source_id }}（{{ alarmDetail.source_type }}）</el-descriptions-item>
        <el-descriptions-item label="时间">{{ alarmDetail.time }}</el-descriptions-item>
        <el-descriptions-item label="舱室">{{ alarmDetail.cabin || '公共区域' }}</el-descriptions-item>
        <el-descriptions-item label="区段">{{ alarmDetail.zone_code }}</el-descriptions-item>
        <el-descriptions-item label="指标">{{ alarmDetail.metric_name }}（{{ alarmDetail.metric }}）</el-descriptions-item>
        <el-descriptions-item label="监测值">{{ alarmDetail.value }} {{ alarmDetail.unit }}</el-descriptions-item>
        <el-descriptions-item label="严重度">
          <el-tag :type="alarmDetail.level === 2 ? 'danger' : 'warning'" size="small">
            {{ alarmDetail.severity || (alarmDetail.level === 2 ? '严重' : '预警') }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="状态">
          <el-tag :type="alarmStatusType(alarmDetail.status)" size="small">{{ alarmDetail.status }}</el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="描述" :span="2">{{ alarmDetail.desc }}</el-descriptions-item>
      </el-descriptions>
    </el-dialog>

    <!-- ============ 管线新增/编辑对话框 ============ -->
    <el-dialog
      v-model="pipeDialogVisible"
      :title="pipeIsEdit ? '编辑管线' : '新增管线'"
      width="640px"
      destroy-on-close
      class="tunnel__dialog"
    >
      <el-form ref="pipeFormRef" :model="pipeForm" :rules="pipeRules" label-width="110px">
        <el-form-item label="管线类型" prop="pipeline_type">
          <el-select v-model="pipeForm.pipeline_type" placeholder="选择管线类型" style="width: 100%;">
            <el-option v-for="t in PIPELINE_TYPES" :key="t" :label="t" :value="t" />
          </el-select>
        </el-form-item>
        <el-form-item label="舱室" prop="cabin">
          <el-select v-model="pipeForm.cabin" placeholder="选择舱室" style="width: 100%;">
            <el-option label="电力舱（EL）" value="EL" />
            <el-option label="燃气舱（GS）" value="GS" />
            <el-option label="水信舱（WS）" value="WS" />
          </el-select>
        </el-form-item>
        <el-form-item label="起始区段" prop="zone_start">
          <el-input-number v-model="pipeForm.zone_start" :min="1" :max="6" style="width: 100%;" />
        </el-form-item>
        <el-form-item label="结束区段" prop="zone_end">
          <el-input-number v-model="pipeForm.zone_end" :min="1" :max="6" style="width: 100%;" />
        </el-form-item>
        <el-form-item label="管径(mm)" prop="diameter_mm">
          <el-input-number v-model="pipeForm.diameter_mm" :min="1" :step="50" style="width: 100%;" />
        </el-form-item>
        <el-form-item label="材质" prop="material">
          <el-input v-model="pipeForm.material" placeholder="如 球墨铸铁 / PE / 钢制" />
        </el-form-item>
        <el-form-item label="设计压力" prop="design_pressure">
          <el-input v-model="pipeForm.design_pressure" placeholder="如 1.6MPa" />
        </el-form-item>
        <el-form-item label="水平位置(m)" prop="lateral_pos">
          <el-input-number v-model="pipeForm.lateral_pos" :min="0" :precision="2" :step="0.1" style="width: 100%;" />
        </el-form-item>
        <el-form-item label="支架层位" prop="vertical_pos">
          <el-input-number v-model="pipeForm.vertical_pos" :min="1" :max="4" style="width: 100%;" />
        </el-form-item>
        <el-form-item label="权属单位" prop="owner_unit">
          <el-input v-model="pipeForm.owner_unit" placeholder="如 市水务集团" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="pipeDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="pipeSubmitting" @click="handlePipeSubmit">确定</el-button>
      </template>
    </el-dialog>

    <!-- ============ 管线详情对话框 ============ -->
    <el-dialog v-model="pipeDetailVisible" title="管线详情" width="620px" class="tunnel__dialog">
      <el-descriptions v-if="pipeDetail" :column="2" border>
        <el-descriptions-item label="管线ID">{{ pipeDetail.pipeline_id }}</el-descriptions-item>
        <el-descriptions-item label="类型">{{ pipeDetail.pipeline_type }}</el-descriptions-item>
        <el-descriptions-item label="舱室">{{ pipeDetail.cabin }}</el-descriptions-item>
        <el-descriptions-item label="区段">Z{{ String(pipeDetail.zone_start).padStart(2, '0') }} ~ Z{{ String(pipeDetail.zone_end).padStart(2, '0') }}</el-descriptions-item>
        <el-descriptions-item label="管径">{{ pipeDetail.diameter_mm }} mm</el-descriptions-item>
        <el-descriptions-item label="材质">{{ pipeDetail.material || '-' }}</el-descriptions-item>
        <el-descriptions-item label="设计压力">{{ pipeDetail.design_pressure || '-' }}</el-descriptions-item>
        <el-descriptions-item label="水平位置">{{ pipeDetail.lateral_pos }} m</el-descriptions-item>
        <el-descriptions-item label="支架层位">第 {{ pipeDetail.vertical_pos }} 层</el-descriptions-item>
        <el-descriptions-item label="状态">
          <el-tag :type="pipeStatusType(pipeDetail.status)" size="small">{{ pipeDetail.status }}</el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="入廊日期">{{ pipeDetail.commission_date || '-' }}</el-descriptions-item>
        <el-descriptions-item label="权属单位">{{ pipeDetail.owner_unit || '-' }}</el-descriptions-item>
      </el-descriptions>
    </el-dialog>

    <!-- ============ 出入登记对话框 ============ -->
    <el-dialog v-model="accessDialogVisible" title="登记出入记录" width="520px" destroy-on-close class="tunnel__dialog">
      <el-form ref="accessFormRef" :model="accessForm" :rules="accessRules" label-width="90px">
        <el-form-item label="门禁" prop="gate_id">
          <el-select v-model="accessForm.gate_id" placeholder="选择门禁" style="width: 100%;">
            <el-option
              v-for="g in gates"
              :key="g.gate_id"
              :label="`${g.name || g.gate_name}（${g.gate_id}）`"
              :value="g.gate_id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="方向" prop="direction">
          <el-radio-group v-model="accessForm.direction">
            <el-radio value="进">进</el-radio>
            <el-radio value="出">出</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="人员ID" prop="person_id">
          <el-input v-model="accessForm.person_id" placeholder="如 P-1001" />
        </el-form-item>
        <el-form-item label="姓名" prop="person_name">
          <el-input v-model="accessForm.person_name" placeholder="人员姓名" />
        </el-form-item>
        <el-form-item label="已授权">
          <el-switch v-model="accessForm.authorized" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="accessDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="accessSubmitting" @click="handleAccessSubmit">确定</el-button>
      </template>
    </el-dialog>

    <!-- ============ 出入记录详情对话框 ============ -->
    <el-dialog v-model="accessDetailVisible" title="出入记录详情" width="560px" class="tunnel__dialog">
      <el-descriptions v-if="accessDetail" :column="2" border>
        <el-descriptions-item label="记录ID">{{ accessDetail.record_id }}</el-descriptions-item>
        <el-descriptions-item label="时间">{{ accessDetail.time }}</el-descriptions-item>
        <el-descriptions-item label="门禁">{{ accessDetail.gate_name }}（{{ accessDetail.gate_id }}）</el-descriptions-item>
        <el-descriptions-item label="位置">{{ accessDetail.location }}</el-descriptions-item>
        <el-descriptions-item label="人员">{{ accessDetail.person_name }}</el-descriptions-item>
        <el-descriptions-item label="人员ID">{{ accessDetail.person_id }}</el-descriptions-item>
        <el-descriptions-item label="方向">
          <el-tag :type="accessDetail.direction === '进' ? 'success' : 'info'" size="small">{{ accessDetail.direction }}</el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="授权">
          <el-tag :type="accessDetail.authorized ? 'success' : 'danger'" size="small">
            {{ accessDetail.authorized ? '已授权' : '未授权' }}
          </el-tag>
        </el-descriptions-item>
      </el-descriptions>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Search, Upload, Download, Refresh } from '@element-plus/icons-vue'
import * as XLSX from 'xlsx'
import { saveAs } from 'file-saver'
import PageHeader from '@/components/PageHeader.vue'
import StatCard from '@/components/StatCard.vue'
import {
  getOverview, getCabins, getEnvRealtime, getAlarms, ackAlarm,
  getPipelines, createPipeline, updatePipeline,
  getSecurityOverview, getAccessRecords, createAccessRecord, getIntrusions
} from '@/api/tunnel'

// ===== 枚举常量（与后端约定一致） =====
const PIPELINE_TYPES = ['供水', '燃气', '电力', '通信']
const PIPELINE_STATUS = ['在运', '检修', '停运']

const activeTab = ref('env')

// ===== 总览统计 =====
const overview = ref({})
const cabins = ref([])

const loadOverview = async () => {
  try {
    overview.value = await getOverview() || {}
  } catch (e) {
    console.error('加载管廊总览失败:', e)
  }
}

const loadCabins = async () => {
  try {
    const res = await getCabins()
    cabins.value = Array.isArray(res) ? res : []
  } catch (e) {
    console.error('加载舱室结构失败:', e)
  }
}

// ===== Tab 1 环境监测 =====
const envQuery = ref({ cabin: '', online: '', keyword: '' })
const envSensors = ref([])
const envLoading = ref(false)
const envPage = ref(1)
const envSize = ref(10)

const envMetricKeys = ['temperature', 'o2', 'co', 'h2s', 'ch4']
const envMetricLabels = { temperature: '温度', o2: '氧气', co: 'CO', h2s: 'H2S', ch4: 'CH4' }

const envFiltered = computed(() => {
  const { online, keyword } = envQuery.value
  return envSensors.value.filter(s => {
    if (online !== '' && online !== null && online !== undefined && s.online !== online) return false
    if (keyword) {
      const kw = keyword.toLowerCase()
      const hit = (s.sensor_id || '').toLowerCase().includes(kw) ||
        (s.sensor_name || '').toLowerCase().includes(kw)
      if (!hit) return false
    }
    return true
  })
})

const envPaged = computed(() => {
  const start = (envPage.value - 1) * envSize.value
  return envFiltered.value.slice(start, start + envSize.value)
})

const loadEnv = async () => {
  envLoading.value = true
  try {
    const params = {}
    if (envQuery.value.cabin) params.cabin = envQuery.value.cabin
    const res = await getEnvRealtime(params)
    envSensors.value = res?.sensors || []
    envPage.value = 1
  } catch (e) {
    ElMessage.error('加载环境监测数据失败')
    console.error('加载环境监测数据失败:', e)
  } finally {
    envLoading.value = false
  }
}

const resetEnvQuery = () => {
  envQuery.value = { cabin: '', online: '', keyword: '' }
  loadEnv()
}

const metricLevelClass = (level) => ({
  0: 'metric-cell--normal',
  1: 'metric-cell--warning',
  2: 'metric-cell--critical'
}[level] || 'metric-cell--normal')

const levelTagType = (level) => ({ 0: 'success', 1: 'warning', 2: 'danger' }[level] || 'success')
const levelText = (level) => ({ 0: '正常', 1: '预警', 2: '严重' }[level] ?? '正常')

// 传感器详情
const envDetailVisible = ref(false)
const envDetail = ref(null)
const envDetailMetrics = computed(() => {
  if (!envDetail.value?.metrics) return []
  return Object.values(envDetail.value.metrics).filter(Boolean)
})
const openEnvDetail = (row) => {
  envDetail.value = row
  envDetailVisible.value = true
}

// ===== Tab 2 告警管理 =====
const alarmQuery = ref({ cabin: '', level: '', status: '' })
const alarms = ref([])
const alarmLoading = ref(false)
const alarmPage = ref(1)
const alarmSize = ref(10)

const alarmPaged = computed(() => {
  const start = (alarmPage.value - 1) * alarmSize.value
  return alarms.value.slice(start, start + alarmSize.value)
})

const alarmStatusType = (status) => ({
  '未处理': 'danger',
  '处理中': 'warning',
  '已处理': 'success'
}[status] || 'info')

const loadAlarms = async () => {
  alarmLoading.value = true
  try {
    const params = { limit: 100 }
    if (alarmQuery.value.cabin) params.cabin = alarmQuery.value.cabin
    if (alarmQuery.value.level !== '' && alarmQuery.value.level !== null) params.level = alarmQuery.value.level
    if (alarmQuery.value.status) params.status = alarmQuery.value.status
    const res = await getAlarms(params)
    alarms.value = res?.alarms || []
    alarmPage.value = 1
  } catch (e) {
    ElMessage.error('加载告警列表失败')
    console.error('加载告警列表失败:', e)
  } finally {
    alarmLoading.value = false
  }
}

const resetAlarmQuery = () => {
  alarmQuery.value = { cabin: '', level: '', status: '' }
  loadAlarms()
}

// 告警详情
const alarmDetailVisible = ref(false)
const alarmDetail = ref(null)
const openAlarmDetail = (row) => {
  alarmDetail.value = row
  alarmDetailVisible.value = true
}

// 确认告警（状态变更：未处理 → 已处理）
const handleAck = async (row) => {
  try {
    const res = await ackAlarm(row.alarm_id)
    ElMessage.success(res?.message || '告警已确认')
    loadAlarms()
    loadOverview()
  } catch (e) {
    ElMessage.error('确认告警失败')
    console.error('确认告警失败:', e)
  }
}

// ===== Tab 3 管线管理 =====
const pipeQuery = ref({ cabin: '', pipeline_type: '', status: '' })
const pipelines = ref([])
const pipeLoading = ref(false)
const pipePage = ref(1)
const pipeSize = ref(10)

const pipelinesFiltered = computed(() => {
  const st = pipeQuery.value.status
  return st ? pipelines.value.filter(p => p.status === st) : pipelines.value
})

const pipePaged = computed(() => {
  const start = (pipePage.value - 1) * pipeSize.value
  return pipelinesFiltered.value.slice(start, start + pipeSize.value)
})

const pipeStatusType = (status) => ({
  '在运': 'success',
  '检修': 'warning',
  '停运': 'info'
}[status] || 'info')

const loadPipelines = async () => {
  pipeLoading.value = true
  try {
    const params = {}
    if (pipeQuery.value.cabin) params.cabin = pipeQuery.value.cabin
    if (pipeQuery.value.pipeline_type) params.pipeline_type = pipeQuery.value.pipeline_type
    const res = await getPipelines(params)
    pipelines.value = res?.pipelines || []
    pipePage.value = 1
  } catch (e) {
    ElMessage.error('加载管线台账失败')
    console.error('加载管线台账失败:', e)
  } finally {
    pipeLoading.value = false
  }
}

const resetPipeQuery = () => {
  pipeQuery.value = { cabin: '', pipeline_type: '', status: '' }
  loadPipelines()
}

// 新增/编辑管线
const pipeDialogVisible = ref(false)
const pipeIsEdit = ref(false)
const pipeSubmitting = ref(false)
const pipeFormRef = ref(null)
const pipeEditingId = ref(null)

const defaultPipeForm = () => ({
  pipeline_type: '',
  cabin: '',
  zone_start: 1,
  zone_end: 1,
  diameter_mm: 300,
  material: '',
  design_pressure: '',
  lateral_pos: 0.5,
  vertical_pos: 1,
  owner_unit: ''
})

const pipeForm = ref(defaultPipeForm())

const pipeRules = {
  pipeline_type: [{ required: true, message: '请选择管线类型', trigger: 'change' }],
  cabin: [{ required: true, message: '请选择舱室', trigger: 'change' }],
  zone_start: [{ required: true, message: '请输入起始区段', trigger: 'blur' }],
  zone_end: [{ required: true, message: '请输入结束区段', trigger: 'blur' }],
  diameter_mm: [{ required: true, message: '请输入管径', trigger: 'blur' }],
  lateral_pos: [{ required: true, message: '请输入水平位置', trigger: 'blur' }],
  vertical_pos: [{ required: true, message: '请选择支架层位', trigger: 'blur' }]
}

const openPipeDialog = (row) => {
  if (row) {
    pipeIsEdit.value = true
    pipeEditingId.value = row.pipeline_id
    pipeForm.value = {
      pipeline_type: row.pipeline_type,
      cabin: row.cabin,
      zone_start: row.zone_start,
      zone_end: row.zone_end,
      diameter_mm: row.diameter_mm,
      material: row.material || '',
      design_pressure: row.design_pressure || '',
      lateral_pos: row.lateral_pos ?? 0.5,
      vertical_pos: row.vertical_pos ?? 1,
      owner_unit: row.owner_unit || ''
    }
  } else {
    pipeIsEdit.value = false
    pipeEditingId.value = null
    pipeForm.value = defaultPipeForm()
  }
  pipeDialogVisible.value = true
}

const handlePipeSubmit = async () => {
  if (!pipeFormRef.value) return
  try {
    await pipeFormRef.value.validate()
  } catch (e) {
    return
  }
  if (pipeForm.value.zone_start > pipeForm.value.zone_end) {
    ElMessage.warning('起始区段不得大于结束区段')
    return
  }
  pipeSubmitting.value = true
  try {
    if (pipeIsEdit.value) {
      await updatePipeline(pipeEditingId.value, pipeForm.value)
      ElMessage.success('更新成功')
    } else {
      await createPipeline(pipeForm.value)
      ElMessage.success('创建成功')
    }
    pipeDialogVisible.value = false
    loadPipelines()
    loadOverview()
  } catch (e) {
    ElMessage.error(e?.response?.data?.detail || (pipeIsEdit.value ? '更新失败' : '创建失败'))
    console.error('提交管线失败:', e)
  } finally {
    pipeSubmitting.value = false
  }
}

// 状态变更：在运 → 检修 → 停运 → 在运 循环
const handleStatusChange = async (row) => {
  const idx = PIPELINE_STATUS.indexOf(row.status)
  const next = PIPELINE_STATUS[(idx + 1) % PIPELINE_STATUS.length]
  try {
    await updatePipeline(row.pipeline_id, { status: next })
    ElMessage.success(`状态已变更为「${next}」`)
    loadPipelines()
  } catch (e) {
    ElMessage.error('状态变更失败')
    console.error('状态变更失败:', e)
  }
}

// 删除（后端无物理删除接口，软删除为「停运」）
const handlePipeDelete = async (row) => {
  try {
    await ElMessageBox.confirm(
      `确认删除管线 ${row.pipeline_id}？删除后管线将标记为「停运」并退出运行台账。`,
      '删除确认',
      { type: 'warning', confirmButtonText: '删除', cancelButtonText: '取消' }
    )
  } catch (e) {
    return
  }
  try {
    await updatePipeline(row.pipeline_id, { status: '停运' })
    ElMessage.success('删除成功')
    loadPipelines()
    loadOverview()
  } catch (e) {
    ElMessage.error('删除失败')
    console.error('删除管线失败:', e)
  }
}

// 管线详情
const pipeDetailVisible = ref(false)
const pipeDetail = ref(null)
const openPipeDetail = (row) => {
  pipeDetail.value = row
  pipeDetailVisible.value = true
}

// ===== Tab 4 安防管理 =====
const secLoading = ref(false)
const secOverview = ref({})
const accessRecords = ref([])
const intrusions = ref([])
const accessPage = ref(1)
const accessSize = ref(10)

const accessPaged = computed(() => {
  const start = (accessPage.value - 1) * accessSize.value
  return accessRecords.value.slice(start, start + accessSize.value)
})

const gates = computed(() => {
  const g = secOverview.value?.gates
  return Array.isArray(g) && g.length ? g : []
})

const loadSecurity = async () => {
  secLoading.value = true
  try {
    const [ov, access, intr] = await Promise.all([
      getSecurityOverview(),
      getAccessRecords(50),
      getIntrusions(50)
    ])
    secOverview.value = ov || {}
    accessRecords.value = access?.records || []
    intrusions.value = intr?.intrusions || []
    accessPage.value = 1
  } catch (e) {
    ElMessage.error('加载安防数据失败')
    console.error('加载安防数据失败:', e)
  } finally {
    secLoading.value = false
  }
}

// 登记出入
const accessDialogVisible = ref(false)
const accessSubmitting = ref(false)
const accessFormRef = ref(null)
const accessForm = ref({ gate_id: '', direction: '进', person_id: '', person_name: '', authorized: true })
const accessRules = {
  gate_id: [{ required: true, message: '请选择门禁', trigger: 'change' }],
  direction: [{ required: true, message: '请选择方向', trigger: 'change' }],
  person_id: [{ required: true, message: '请输入人员ID', trigger: 'blur' }]
}

const openAccessDialog = () => {
  accessForm.value = { gate_id: '', direction: '进', person_id: '', person_name: '', authorized: true }
  accessDialogVisible.value = true
}

const handleAccessSubmit = async () => {
  if (!accessFormRef.value) return
  try {
    await accessFormRef.value.validate()
  } catch (e) {
    return
  }
  accessSubmitting.value = true
  try {
    await createAccessRecord(accessForm.value)
    ElMessage.success('登记成功')
    accessDialogVisible.value = false
    loadSecurity()
    loadOverview()
  } catch (e) {
    ElMessage.error('登记失败')
    console.error('登记出入记录失败:', e)
  } finally {
    accessSubmitting.value = false
  }
}

// 出入记录详情
const accessDetailVisible = ref(false)
const accessDetail = ref(null)
const openAccessDetail = (row) => {
  accessDetail.value = row
  accessDetailVisible.value = true
}

// ===== Excel 导出 =====
const exportSheet = (rows, filename, sheetName = 'Sheet1') => {
  if (!rows.length) {
    ElMessage.warning('暂无数据可导出')
    return
  }
  const wb = XLSX.utils.book_new()
  XLSX.utils.book_append_sheet(wb, XLSX.utils.json_to_sheet(rows), sheetName)
  const out = XLSX.write(wb, { bookType: 'xlsx', type: 'array' })
  saveAs(new Blob([out], { type: 'application/octet-stream' }), filename)
  ElMessage.success('导出成功')
}

const exportEnv = () => {
  exportSheet(
    envFiltered.value.map(s => ({
      传感器ID: s.sensor_id,
      名称: s.sensor_name,
      舱室: s.cabin_name,
      区段: s.zone_code,
      在线: s.online ? '在线' : '离线',
      ...Object.fromEntries(Object.entries(s.metrics || {}).map(([k, m]) => [
        `${m?.name || k}(${m?.unit || ''})`, m?.value
      ]))
    })),
    '环境监测数据.xlsx'
  )
}

const exportAlarms = () => {
  exportSheet(
    alarms.value.map(a => ({
      告警ID: a.alarm_id, 时间: a.time, 舱室: a.cabin, 区段: a.zone_code,
      指标: a.metric_name, 监测值: a.value, 单位: a.unit,
      严重度: a.severity, 状态: a.status, 描述: a.desc
    })),
    '管廊告警记录.xlsx'
  )
}

const exportPipelines = () => {
  exportSheet(
    pipelinesFiltered.value.map(p => ({
      管线ID: p.pipeline_id, 类型: p.pipeline_type, 舱室: p.cabin,
      起始区段: p.zone_start, 结束区段: p.zone_end, 管径mm: p.diameter_mm,
      材质: p.material, 设计压力: p.design_pressure, 状态: p.status,
      入廊日期: p.commission_date, 权属单位: p.owner_unit
    })),
    '管线台账.xlsx'
  )
}

const exportAccess = () => {
  exportSheet(
    accessRecords.value.map(r => ({
      记录ID: r.record_id, 时间: r.time, 门禁: r.gate_name, 位置: r.location,
      人员ID: r.person_id, 人员: r.person_name,
      方向: r.direction, 授权: r.authorized ? '已授权' : '未授权'
    })),
    '门禁出入记录.xlsx'
  )
}

const exportIntrusions = () => {
  exportSheet(
    intrusions.value.map(i => ({
      告警ID: i.intrusion_id, 防区: i.zone_name,
      等级: i.level === 2 ? '严重' : '一般', 状态: i.status, 时间: i.time
    })),
    '入侵检测告警.xlsx'
  )
}

// ===== Excel 导入 =====
const readWorkbook = (file) => new Promise((resolve, reject) => {
  const reader = new FileReader()
  reader.onload = (e) => {
    try {
      const wb = XLSX.read(new Uint8Array(e.target.result), { type: 'array' })
      const sheet = wb.Sheets[wb.SheetNames[0]]
      resolve(XLSX.utils.sheet_to_json(sheet))
    } catch (err) {
      reject(err)
    }
  }
  reader.onerror = reject
  reader.readAsArrayBuffer(file)
})

// 管线批量导入（表头：pipeline_type, cabin, zone_start, zone_end, diameter_mm, material, design_pressure, lateral_pos, vertical_pos, owner_unit）
const importPipelines = async ({ file }) => {
  try {
    const rows = await readWorkbook(file)
    if (!rows.length) {
      ElMessage.warning('文件中没有数据')
      return
    }
    let ok = 0
    let fail = 0
    for (const r of rows) {
      try {
        await createPipeline({
          pipeline_type: r.pipeline_type || r['管线类型'] || r['类型'],
          cabin: r.cabin || r['舱室'],
          zone_start: Number(r.zone_start ?? r['起始区段'] ?? 1),
          zone_end: Number(r.zone_end ?? r['结束区段'] ?? 1),
          diameter_mm: Number(r.diameter_mm ?? r['管径mm'] ?? r['管径'] ?? 300),
          material: String(r.material ?? r['材质'] ?? ''),
          design_pressure: String(r.design_pressure ?? r['设计压力'] ?? ''),
          lateral_pos: Number(r.lateral_pos ?? r['水平位置'] ?? 0.5),
          vertical_pos: Number(r.vertical_pos ?? r['支架层位'] ?? 1),
          owner_unit: String(r.owner_unit ?? r['权属单位'] ?? '')
        })
        ok += 1
      } catch (e) {
        fail += 1
      }
    }
    ElMessage.success(`导入完成：成功 ${ok} 条${fail ? `，失败 ${fail} 条` : ''}`)
    loadPipelines()
    loadOverview()
  } catch (e) {
    ElMessage.error('导入失败：文件解析错误')
    console.error('导入管线失败:', e)
  }
}

// 出入记录批量导入（表头：gate_id, direction, person_id, person_name, authorized）
const importAccessRecords = async ({ file }) => {
  try {
    const rows = await readWorkbook(file)
    if (!rows.length) {
      ElMessage.warning('文件中没有数据')
      return
    }
    let ok = 0
    let fail = 0
    for (const r of rows) {
      try {
        const authorized = r.authorized ?? r['授权']
        await createAccessRecord({
          gate_id: r.gate_id || r['门禁ID'],
          direction: r.direction || r['方向'] || '进',
          person_id: String(r.person_id || r['人员ID'] || ''),
          person_name: String(r.person_name ?? r['人员'] ?? ''),
          authorized: authorized === undefined ? true : !['否', 'false', '0', 0, false].includes(authorized)
        })
        ok += 1
      } catch (e) {
        fail += 1
      }
    }
    ElMessage.success(`导入完成：成功 ${ok} 条${fail ? `，失败 ${fail} 条` : ''}`)
    loadSecurity()
    loadOverview()
  } catch (e) {
    ElMessage.error('导入失败：文件解析错误')
    console.error('导入出入记录失败:', e)
  }
}

// ===== 刷新 & 生命周期 =====
const refreshAll = () => {
  loadOverview()
  loadCabins()
  if (activeTab.value === 'env') loadEnv()
  else if (activeTab.value === 'alarm') loadAlarms()
  else if (activeTab.value === 'pipeline') loadPipelines()
  else loadSecurity()
}

onMounted(() => {
  loadOverview()
  loadCabins()
  loadEnv()
  loadAlarms()
  loadPipelines()
  loadSecurity()
})
</script>

<style scoped>
.tunnel__stats {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
  margin-bottom: 16px;
}
.tunnel__tabs-card {
  padding: 8px 20px 16px;
}
.tunnel__filter {
  margin-bottom: 16px;
}
.tunnel__filter-item {
  width: 160px;
}
.tunnel__export-btn {
  margin-left: auto;
}
.tunnel__upload {
  display: inline-flex;
  margin-left: 12px;
}
.tunnel__pagination {
  display: flex;
  justify-content: flex-end;
  margin-top: 16px;
}

/* 卡片小标题（安防分栏） */
.card-title {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}
.card-title__text {
  margin: 0;
  font-size: 15px;
  font-weight: 600;
  color: var(--app-text-1);
}
.tunnel__security-grid {
  display: grid;
  grid-template-columns: 1.2fr 1fr;
  gap: 24px;
}
.tunnel__security-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}
.tunnel__security-actions .tunnel__upload {
  margin-left: 0;
}

/* 表格内单元样式 */
.code-cell {
  font-family: 'Courier New', monospace;
  font-size: 13px;
  color: var(--app-primary);
}
.time-cell {
  color: var(--app-text-3);
  font-size: 13px;
}
.metric-cell {
  font-weight: 600;
  font-family: 'Courier New', monospace;
  font-size: 13px;
}
.metric-cell__unit {
  font-weight: 400;
  font-size: 11px;
  margin-left: 2px;
  opacity: 0.7;
}
.metric-cell--normal { color: #34C759; }
.metric-cell--warning { color: #FF9500; }
.metric-cell--critical { color: #FF3B30; }
.metric-cell--empty { color: var(--app-text-3); }
.metric-value {
  color: var(--app-text-1);
  font-weight: 600;
}
.metric-unit {
  color: var(--app-text-3);
  font-size: 12px;
  margin-left: 3px;
}

/* 详情对话框小节标题 */
.tunnel__dialog-subtitle {
  margin: 18px 0 10px;
  font-size: 14px;
  font-weight: 600;
  color: var(--app-text-2);
}

@media (max-width: 1024px) {
  .tunnel__stats { grid-template-columns: repeat(2, 1fr); }
  .tunnel__security-grid { grid-template-columns: 1fr; }
}
</style>
