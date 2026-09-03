<template>
  <div class="water-supply">
    <PageHeader title="供水管网精细化管控" subtitle="Water Supply Pipeline Management" />

    <!-- 顶部统计卡片 -->
    <div class="stats-grid">
      <StatCard label="管网总数" :value="summary.pipe_total" icon="Connection" color="#0071E3" />
      <StatCard label="异常管网" :value="summary.pipe_abnormal" icon="Warning" color="#FF3B30" />
      <StatCard label="待处理告警" :value="summary.active_alarms" icon="Bell" color="#FF9500" />
      <StatCard label="今日监测" :value="summary.monitor_today" icon="DataLine" color="#5856D6" />
      <StatCard label="DMA平均漏损率" :value="summary.avg_leakage_pct + '%'" icon="DataAnalysis" color="#34C759" />
      <StatCard label="水质异常节点" :value="summary.quality_abnormal" icon="TrendCharts" color="#AF52DE" />
      <StatCard label="消防栓总数" :value="summary.hydrant_total" icon="Opportunity" color="#30C0C0" />
      <StatCard label="爆管高风险" :value="summary.burst_high" icon="Promotion" color="#FF2D55" />
    </div>

    <!-- Tab 切换七大功能 -->
    <div class="app-card tabs-wrap">
      <el-tabs v-model="activeTab" type="card" class="app-tabs" @tab-change="onTabChange">

        <!-- ========== Tab 1: 实时运行监测 ========== -->
        <el-tab-pane label="实时监测" name="monitor">
          <div class="filter-bar" style="margin-bottom:16px">
            <el-input v-model="monitorKeyword" placeholder="搜索编号/名称/道路" clearable style="width:240px" />
            <el-switch v-model="monitorOnlyAbnormal" active-text="仅看异常" />
            <el-button type="primary" @click="loadMonitorLatest">刷新</el-button>
          </div>
          <el-table :data="monitorItems" class="app-table" v-loading="monitorLoading" stripe>
            <el-table-column prop="code" label="编号" width="120" />
            <el-table-column prop="name" label="名称" width="140" show-overflow-tooltip />
            <el-table-column prop="road_name" label="道路" width="130" show-overflow-tooltip />
            <el-table-column prop="district" label="区域" width="90" />
            <el-table-column label="状态" width="100" align="center">
              <template #default="{ row }">
                <el-tag :type="row.status === '告警' ? 'danger' : 'success'" effect="light" size="small">{{ row.status }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column label="压力MPa" width="100" align="center">
              <template #default="{ row }">
                <span :style="{ color: (row.pressure_mpa !== null && (row.pressure_mpa < 0.15 || row.pressure_mpa > 0.6)) ? '#FF3B30' : '' }">{{ row.pressure_mpa ?? '-' }}</span>
              </template>
            </el-table-column>
            <el-table-column prop="flow_m3h" label="流量m³/h" width="110" align="center" />
            <el-table-column prop="level_cm" label="液位cm" width="100" align="center" />
            <el-table-column prop="turbidity_ntu" label="浊度NTU" width="100" align="center">
              <template #default="{ row }">
                <span :style="{ color: row.turbidity_ntu > 1 ? '#FF9500' : '' }">{{ row.turbidity_ntu ?? '-' }}</span>
              </template>
            </el-table-column>
            <el-table-column prop="residual_cl" label="余氯mg/L" width="110" align="center" />
            <el-table-column prop="deformation_mm" label="形变mm" width="100" align="center">
              <template #default="{ row }">
                <span :style="{ color: row.deformation_mm > 5 ? '#FF3B30' : '' }">{{ row.deformation_mm ?? '-' }}</span>
              </template>
            </el-table-column>
          </el-table>
          <!-- 管网告警 -->
          <div style="margin-top:24px">
            <div class="card-title"><h3 class="card-title__text">管网告警记录</h3></div>
            <el-table :data="alarmItems" class="app-table" v-loading="alarmLoading" stripe>
              <el-table-column prop="alarm_code" label="编号" width="140" />
              <el-table-column prop="type" label="类型" width="120">
                <template #default="{ row }">
                  <el-tag :type="levelTag(row.level)" effect="light" size="small">{{ row.type }}</el-tag>
                </template>
              </el-table-column>
              <el-table-column label="等级" width="80" align="center">
                <template #default="{ row }">
                  <el-tag :type="levelTag(row.level)" effect="dark" size="small">{{ row.level }}</el-tag>
                </template>
              </el-table-column>
              <el-table-column prop="detail" label="详情" min-width="280" show-overflow-tooltip />
              <el-table-column label="状态" width="100" align="center">
                <template #default="{ row }">
                  <el-tag :type="row.status === '已处理' ? 'success' : 'warning'" effect="light" size="small">{{ row.status }}</el-tag>
                </template>
              </el-table-column>
              <el-table-column label="时间" width="170">
                <template #default="{ row }">{{ fmtTs(row.alarm_ts) }}</template>
              </el-table-column>
              <el-table-column label="操作" width="100" fixed="right">
                <template #default="{ row }">
                  <el-button v-if="row.status !== '已处理'" link type="primary" size="small" @click="handleAlarm(row)">处理</el-button>
                </template>
              </el-table-column>
            </el-table>
            <div style="margin-top:12px;display:flex;justify-content:flex-end">
              <el-pagination v-model:current-page="alarmPage" v-model:page-size="alarmPageSize"
                :total="alarmTotal" :page-sizes="[10,20,50]" layout="total, sizes, prev, pager, next"
                @size-change="loadAlarms" @current-change="loadAlarms" />
            </div>
          </div>
        </el-tab-pane>

        <!-- ========== Tab 2: DMA 分区漏损 ========== -->
        <el-tab-pane label="DMA漏损" name="dma">
          <div class="filter-bar" style="margin-bottom:16px">
            <el-input v-model="dmaKeyword" placeholder="搜索区域名称" clearable style="width:240px" />
            <el-button type="primary" @click="loadDmaZones">查询</el-button>
          </div>
          <el-table :data="dmaItems" class="app-table" v-loading="dmaLoading" stripe>
            <el-table-column prop="code" label="DMA编码" width="140" />
            <el-table-column prop="name" label="区域名称" min-width="160" show-overflow-tooltip />
            <el-table-column prop="district" label="区域" width="90" />
            <el-table-column prop="user_count" label="用户数" width="90" align="center" />
            <el-table-column label="漏损率%" width="100" align="center">
              <template #default="{ row }">
                <span :style="{ color: (row.leakage_rate_pct || 0) > 12 ? '#FF3B30' : (row.leakage_rate_pct || 0) > 8 ? '#FF9500' : '' }">{{ row.leakage_rate_pct ?? '-' }}</span>
              </template>
            </el-table-column>
            <el-table-column prop="night_min_flow_m3h" label="夜间最小流量" width="120" align="center" />
            <el-table-column label="状态" width="110" align="center">
              <template #default="{ row }">
                <el-tag :type="row.status === '正常' ? 'success' : (row.status === '暗漏定位' ? 'danger' : 'warning')" effect="light" size="small">{{ row.status }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="dark_leak_location" label="暗漏位置" min-width="160" show-overflow-tooltip />
            <el-table-column label="操作" width="120" fixed="right">
              <template #default="{ row }">
                <div class="table-actions">
                  <el-button link type="primary" size="small" @click="viewDmaRecords(row)">计量</el-button>
                  <el-button link type="warning" size="small" @click="openDmaLocate(row)">定位暗漏</el-button>
                </div>
              </template>
            </el-table-column>
          </el-table>
        </el-tab-pane>

        <!-- ========== Tab 3: 水质溯源 ========== -->
        <el-tab-pane label="水质溯源" name="quality">
          <div style="margin-bottom:16px;color:var(--app-text-3);font-size:13px">全链路水质节点一览，点击节点可查看历史记录</div>
          <el-row :gutter="16">
            <el-col v-for="node in qualityNodes" :key="node.id" :xs="24" :sm="12" :md="8" :lg="6">
              <div class="quality-node" :class="{ abnormal: node.status === '异常' }" @click="viewQualityRecords(node)">
                <div class="quality-node__seq">{{ node.seq }}</div>
                <div class="quality-node__kind">{{ node.kind }}</div>
                <div class="quality-node__name">{{ node.name }}</div>
                <div class="quality-node__metrics">
                  <div class="q-metric"><span class="q-label">浊度</span><span :class="{ danger: node.turbidity_ntu > 1 }">{{ node.turbidity_ntu ?? '-' }} NTU</span></div>
                  <div class="q-metric"><span class="q-label">余氯</span><span :class="{ danger: node.residual_cl < 0.05 }">{{ node.residual_cl ?? '-' }} mg/L</span></div>
                  <div class="q-metric"><span class="q-label">pH</span><span :class="{ danger: node.ph && (node.ph < 6.5 || node.ph > 8.5) }">{{ node.ph ?? '-' }}</span></div>
                </div>
                <el-tag :type="node.status === '异常' ? 'danger' : 'success'" effect="light" size="small">{{ node.status }}</el-tag>
              </div>
            </el-col>
          </el-row>
        </el-tab-pane>

        <!-- ========== Tab 4: 压力调度 ========== -->
        <el-tab-pane label="压力调度" name="pressure">
          <div class="filter-bar" style="margin-bottom:16px">
            <el-select v-model="selectedStation" placeholder="选择泵站" style="width:200px">
              <el-option v-for="s in stations" :key="s.id" :label="s.name" :value="s.id" />
            </el-select>
            <el-select v-model="planForm.period" placeholder="调度时段" style="width:150px">
              <el-option v-for="p in ['早高峰','晚高峰','日间平峰','夜间低谷']" :key="p" :label="p" :value="p" />
            </el-select>
            <el-input-number v-model="planForm.terrain_delta_m" :min="0" :step="5" placeholder="地形高差" />
            <el-button type="primary" @click="generatePlan" :disabled="!selectedStation">生成调度方案</el-button>
          </div>
          <el-table :data="planItems" class="app-table" v-loading="planLoading" stripe>
            <el-table-column prop="station_name" label="泵站" width="140" />
            <el-table-column prop="period" label="时段" width="110" />
            <el-table-column prop="current_pressure_mpa" label="当前压力MPa" width="130" align="center" />
            <el-table-column prop="target_pressure_mpa" label="目标压力MPa" width="130" align="center" />
            <el-table-column prop="energy_save_pct" label="节能率%" width="110" align="center" />
            <el-table-column prop="burst_risk_reduce" label="爆管风险降幅" min-width="140" show-overflow-tooltip />
            <el-table-column label="状态" width="100" align="center">
              <template #default="{ row }">
                <el-tag :type="row.status === '已执行' ? 'success' : 'primary'" effect="light" size="small">{{ row.status }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column label="操作" width="120" fixed="right">
              <template #default="{ row }">
                <el-button v-if="row.status !== '已执行'" link type="primary" size="small" @click="applyPlan(row)">执行</el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-tab-pane>

        <!-- ========== Tab 5: 二次供水 ========== -->
        <el-tab-pane label="二次供水" name="secondary">
          <div class="filter-bar" style="margin-bottom:16px">
            <el-select v-model="secondaryStatus" placeholder="状态" clearable style="width:130px">
              <el-option v-for="s in ['正常','告警']" :key="s" :label="s" :value="s" />
            </el-select>
            <el-input v-model="secondaryKeyword" placeholder="搜索小区/编号" clearable style="width:240px" />
            <el-button type="primary" @click="loadSecondary">查询</el-button>
          </div>
          <el-table :data="secondaryItems" class="app-table" v-loading="secondaryLoading" stripe>
            <el-table-column prop="code" label="编号" width="130" />
            <el-table-column prop="community" label="小区名称" min-width="180" show-overflow-tooltip />
            <el-table-column prop="district" label="区域" width="90" />
            <el-table-column label="状态" width="100" align="center">
              <template #default="{ row }">
                <el-tag :type="row.status === '告警' ? 'danger' : 'success'" effect="light" size="small">{{ row.status }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column label="液位%" width="100" align="center">
              <template #default="{ row }">
                <span :style="{ color: (row.level_pct !== null && (row.level_pct < 20 || row.level_pct > 95)) ? '#FF9500' : '' }">{{ row.level_pct ?? '-' }}</span>
              </template>
            </el-table-column>
            <el-table-column prop="turbidity_ntu" label="浊度NTU" width="100" align="center" />
            <el-table-column prop="residual_cl" label="余氯mg/L" width="110" align="center" />
            <el-table-column prop="disinfect_status" label="消毒设备" width="100">
              <template #default="{ row }">
                <el-tag v-if="row.disinfect_status === '异常'" type="danger" effect="light" size="small">{{ row.disinfect_status }}</el-tag>
                <span v-else>{{ row.disinfect_status || '-' }}</span>
              </template>
            </el-table-column>
            <el-table-column prop="last_check" label="上次检查" width="150" />
          </el-table>
        </el-tab-pane>

        <!-- ========== Tab 6: 消防栓管理 ========== -->
        <el-tab-pane label="消防栓" name="hydrant">
          <div class="filter-bar" style="margin-bottom:16px">
            <el-input v-model="hydrantKeyword" placeholder="搜索编号/位置" clearable style="width:240px" />
            <el-select v-model="hydrantStatus" placeholder="状态" clearable style="width:130px">
              <el-option v-for="s in ['正常','告警']" :key="s" :label="s" :value="s" />
            </el-select>
            <el-button type="primary" @click="loadHydrants">查询</el-button>
            <el-button type="success" @click="openHydrantDialog()">新增消防栓</el-button>
          </div>
          <el-table :data="hydrantItems" class="app-table" v-loading="hydrantLoading" stripe>
            <el-table-column prop="code" label="编号" width="120" />
            <el-table-column prop="location" label="位置" min-width="160" show-overflow-tooltip />
            <el-table-column prop="road_name" label="道路" width="130" show-overflow-tooltip />
            <el-table-column prop="district" label="区域" width="90" />
            <el-table-column label="状态" width="100" align="center">
              <template #default="{ row }">
                <el-tag :type="row.status === '告警' ? 'danger' : 'success'" effect="light" size="small">{{ row.status || '正常' }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="pressure_mpa" label="水压MPa" width="100" align="center" />
            <el-table-column prop="pipe_code" label="关联管网" width="120" />
            <el-table-column prop="install_date" label="安装日期" width="110" />
            <el-table-column label="操作" width="200" fixed="right">
              <template #default="{ row }">
                <div class="table-actions">
                  <el-button link type="primary" size="small" @click="openHydrantDialog(row)">编辑</el-button>
                  <el-button link type="warning" size="small" @click="openHydrantTest(row)">出水测试</el-button>
                  <el-button link type="info" size="small" @click="viewHydrantEvents(row)">事件</el-button>
                </div>
              </template>
            </el-table-column>
          </el-table>
          <div style="margin-top:12px;display:flex;justify-content:flex-end">
            <el-pagination v-model:current-page="hydrantPage" v-model:page-size="hydrantPageSize"
              :total="hydrantTotal" :page-sizes="[10,20,50]" layout="total, sizes, prev, pager, next"
              @size-change="loadHydrants" @current-change="loadHydrants" />
          </div>
        </el-tab-pane>

        <!-- ========== Tab 7: 爆管影响分析 ========== -->
        <el-tab-pane label="爆管分析" name="burst">
          <div class="filter-bar" style="margin-bottom:16px">
            <el-select v-model="burstStatus" placeholder="状态" clearable style="width:130px">
              <el-option v-for="s in ['风险预警','处置中','已关阀','已修复']" :key="s" :label="s" :value="s" />
            </el-select>
            <el-button type="primary" @click="loadBurstCases">查询</el-button>
          </div>
          <el-table :data="burstItems" class="app-table" v-loading="burstLoading" stripe>
            <el-table-column prop="code" label="管网编号" width="120" />
            <el-table-column prop="name" label="名称" width="140" show-overflow-tooltip />
            <el-table-column prop="road_name" label="道路" width="130" show-overflow-tooltip />
            <el-table-column prop="material" label="材质" width="110" />
            <el-table-column prop="diameter_mm" label="管径mm" width="100" align="center" />
            <el-table-column label="风险评分" width="100" align="center">
              <template #default="{ row }">
                <span :style="{ color: row.risk_score >= 60 ? '#FF3B30' : row.risk_score >= 40 ? '#FF9500' : '' }">{{ row.risk_score }}</span>
              </template>
            </el-table-column>
            <el-table-column label="风险等级" width="100" align="center">
              <template #default="{ row }">
                <el-tag :type="levelTag(row.risk_level)" effect="dark" size="small">{{ row.risk_level }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="affected_users" label="影响户数" width="100" align="center" />
            <el-table-column prop="affected_area" label="影响区域" min-width="160" show-overflow-tooltip />
            <el-table-column label="状态" width="100" align="center">
              <template #default="{ row }">
                <el-tag :type="row.status === '已修复' ? 'success' : 'warning'" effect="light" size="small">{{ row.status }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column label="操作" width="160" fixed="right">
              <template #default="{ row }">
                <div class="table-actions">
                  <el-button link type="primary" size="small" @click="viewBurstValves(row)">关阀方案</el-button>
                  <el-button v-if="row.status !== '已修复'" link type="success" size="small" @click="openBurstHandle(row)">处置</el-button>
                </div>
              </template>
            </el-table-column>
          </el-table>
        </el-tab-pane>
      </el-tabs>
    </div>

    <!-- DMA 计量历史 Drawer -->
    <el-drawer v-model="dmaDrawer" :title="currentDma?.name + ' · 计量历史'" size="480px">
      <el-table :data="dmaRecords" size="small" stripe>
        <el-table-column prop="date" label="日期" width="110" />
        <el-table-column prop="inflow_m3" label="供水量m³" width="110" align="center" />
        <el-table-column prop="billed_m3" label="售水量m³" width="110" align="center" />
        <el-table-column label="漏损率%" width="100" align="center">
          <template #default="{ row }">
            <span :style="{ color: (row.leakage_rate_pct || 0) > 12 ? '#FF3B30' : '' }">{{ row.leakage_rate_pct }}</span>
          </template>
        </el-table-column>
      </el-table>
    </el-drawer>

    <!-- 水质节点历史 Drawer -->
    <el-drawer v-model="qualityDrawer" :title="currentQualityNode?.name + ' · 历史记录'" size="520px">
      <el-table :data="qualityRecords" size="small" stripe max-height="420">
        <el-table-column label="时间" width="160">
          <template #default="{ row }">{{ fmtTs(row.ts) }}</template>
        </el-table-column>
        <el-table-column prop="turbidity_ntu" label="浊度NTU" width="100" align="center" />
        <el-table-column prop="residual_cl" label="余氯" width="100" align="center" />
        <el-table-column prop="ph" label="pH" width="80" align="center" />
      </el-table>
    </el-drawer>

    <!-- 消防栓编辑 Dialog -->
    <el-dialog v-model="hydrantDialog" :title="currentHydrant?.id ? '编辑消防栓' : '新增消防栓'" width="520px">
      <el-form :model="hydrantForm" label-width="90px">
        <el-form-item label="位置"><el-input v-model="hydrantForm.location" /></el-form-item>
        <el-form-item label="道路"><el-input v-model="hydrantForm.road_name" /></el-form-item>
        <el-form-item label="区域"><el-input v-model="hydrantForm.district" /></el-form-item>
        <el-form-item label="压力MPa"><el-input-number v-model="hydrantForm.pressure_mpa" :min="0" :step="0.1" /></el-form-item>
        <el-form-item label="安装日期"><el-input v-model="hydrantForm.install_date" placeholder="2024-01-01" /></el-form-item>
        <el-form-item label="备注"><el-input v-model="hydrantForm.remark" type="textarea" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="hydrantDialog = false">取消</el-button>
        <el-button type="primary" :loading="hydrantSubmitting" @click="submitHydrant">确定</el-button>
      </template>
    </el-dialog>

    <!-- 出水测试 Dialog -->
    <el-dialog v-model="hydrantTestDialog" title="出水测试" width="400px">
      <el-form :model="hydrantTestForm" label-width="90px">
        <el-form-item label="水压MPa"><el-input-number v-model="hydrantTestForm.pressure_mpa" :min="0" :step="0.1" /></el-form-item>
        <el-form-item label="出水流量L/s"><el-input-number v-model="hydrantTestForm.test_flow_ls" :min="0" :step="5" /></el-form-item>
        <el-form-item label="备注"><el-input v-model="hydrantTestForm.note" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="hydrantTestDialog = false">取消</el-button>
        <el-button type="primary" @click="submitHydrantTest">提交测试</el-button>
      </template>
    </el-dialog>

    <!-- 爆管处置 Dialog -->
    <el-dialog v-model="burstHandleDialog" title="爆管处置" width="400px">
      <el-form :model="burstHandleForm" label-width="90px">
        <el-form-item label="处置状态">
          <el-select v-model="burstHandleForm.status" style="width:100%">
            <el-option v-for="s in ['风险预警','处置中','已关阀','已修复']" :key="s" :label="s" :value="s" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="burstHandleDialog = false">取消</el-button>
        <el-button type="primary" @click="submitBurstHandle">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import PageHeader from '@/components/PageHeader.vue'
import StatCard from '@/components/StatCard.vue'
import {
  fetchSummary,
  fetchMonitorLatest, fetchMonitorAlarms, handleAlarm as handleAlarmApi,
  fetchDmaZones, fetchDmaRecords, createDmaRecord, locateDarkLeak,
  fetchQualityChain, fetchQualityRecords,
  fetchPressureStations, createPressurePlan, fetchPressurePlans, applyPressurePlan,
  fetchSecondaryUnits,
  fetchHydrants, fetchHydrantOptions, createHydrant, updateHydrant, testHydrant, fetchHydrantEvents,
  fetchBurstCases, fetchBurstValves, handleBurst
} from '@/api/waterSupply'

import {
  Connection, Warning, Bell, DataLine, Opportunity, Promotion, DataAnalysis, TrendCharts
} from '@element-plus/icons-vue'

// ---------- 汇总 ----------
const summary = reactive({
  pipe_total: 0, pipe_abnormal: 0, active_alarms: 0, monitor_today: 0,
  avg_leakage_pct: 0, quality_abnormal: 0, hydrant_total: 0, burst_high: 0
})
async function loadSummary() {
  try {
    const r = await fetchSummary()
    Object.assign(summary, r)
  } catch (e) { /* */ }
}

// ---------- Tab 切换 ----------
const activeTab = ref('monitor')
function onTabChange() { loadCurrentTab() }
function loadCurrentTab() {
  const map = {
    monitor: loadMonitorLatest,
    dma: loadDmaZones,
    quality: loadQualityChain,
    pressure: loadStationsAndPlans,
    secondary: loadSecondary,
    hydrant: loadHydrants,
    burst: loadBurstCases
  }
  map[activeTab.value]?.()
}

// ---------- 监测 ----------
const monitorItems = ref([])
const monitorLoading = ref(false)
const monitorKeyword = ref('')
const monitorOnlyAbnormal = ref(false)
async function loadMonitorLatest() {
  monitorLoading.value = true
  try {
    const r = await fetchMonitorLatest({
      keyword: monitorKeyword.value || undefined,
      only_abnormal: monitorOnlyAbnormal.value || undefined
    })
    monitorItems.value = r.items || []
  } finally { monitorLoading.value = false }
}

const alarmItems = ref([])
const alarmLoading = ref(false)
const alarmPage = ref(1)
const alarmPageSize = ref(10)
const alarmTotal = ref(0)
async function loadAlarms() {
  alarmLoading.value = true
  try {
    const r = await fetchMonitorAlarms({ page: alarmPage.value, page_size: alarmPageSize.value })
    alarmItems.value = r.items || []
    alarmTotal.value = r.total || 0
  } finally { alarmLoading.value = false }
}
async function handleAlarm(row) {
  try {
    await handleAlarmApi(row.alarm_id || row.id)
    ElMessage.success('已标记处理')
    loadAlarms(); loadSummary()
  } catch (e) { ElMessage.error(e.message || '操作失败') }
}

// ---------- DMA ----------
const dmaItems = ref([])
const dmaLoading = ref(false)
const dmaKeyword = ref('')
async function loadDmaZones() {
  dmaLoading.value = true
  try {
    const r = await fetchDmaZones({ keyword: dmaKeyword.value || undefined })
    dmaItems.value = r.items || []
  } finally { dmaLoading.value = false }
}
const dmaDrawer = ref(false)
const currentDma = ref(null)
const dmaRecords = ref([])
async function viewDmaRecords(row) {
  currentDma.value = row
  try {
    const r = await fetchDmaRecords(row.id, 7)
    dmaRecords.value = r.records || []
    dmaDrawer.value = true
  } catch (e) { ElMessage.error('加载失败') }
}
async function openDmaLocate(row) {
  try {
    const { value } = await ElMessageBox.prompt('请输入暗漏点位描述', '暗漏定位', { inputValue: row.dark_leak_location || '' })
    await locateDarkLeak(row.id, value)
    ElMessage.success('暗漏位置已登记')
    loadDmaZones(); loadSummary()
  } catch (e) { if (e !== 'cancel') ElMessage.error(e.message || '操作失败') }
}

// ---------- 水质溯源 ----------
const qualityNodes = ref([])
async function loadQualityChain() {
  try {
    const r = await fetchQualityChain()
    qualityNodes.value = r.nodes || []
  } catch (e) { /* */ }
}
const qualityDrawer = ref(false)
const currentQualityNode = ref(null)
const qualityRecords = ref([])
async function viewQualityRecords(node) {
  currentQualityNode.value = node
  try {
    const r = await fetchQualityRecords(node.id, 30)
    qualityRecords.value = r.records || []
    qualityDrawer.value = true
  } catch (e) { ElMessage.error('加载失败') }
}

// ---------- 压力调度 ----------
const stations = ref([])
const planItems = ref([])
const selectedStation = ref(null)
const planLoading = ref(false)
const planForm = reactive({ period: '日间平峰', terrain_delta_m: 0 })
async function loadStationsAndPlans() {
  try {
    const [s, p] = await Promise.all([fetchPressureStations(), fetchPressurePlans()])
    stations.value = s.items || []
    planItems.value = p.items || []
  } catch (e) { /* */ }
}
async function generatePlan() {
  planLoading.value = true
  try {
    const r = await createPressurePlan({ station_id: selectedStation.value, ...planForm })
    ElMessage.success(`目标压力：${r.target_pressure_mpa} MPa，节能率 ${r.energy_save_pct}%`)
    loadStationsAndPlans()
  } catch (e) { ElMessage.error(e.message || '生成失败') }
  finally { planLoading.value = false }
}
async function applyPlan(row) {
  try {
    await applyPressurePlan(row.id)
    ElMessage.success('已执行')
    loadStationsAndPlans()
  } catch (e) { ElMessage.error(e.message || '执行失败') }
}

// ---------- 二次供水 ----------
const secondaryItems = ref([])
const secondaryLoading = ref(false)
const secondaryStatus = ref('')
const secondaryKeyword = ref('')
async function loadSecondary() {
  secondaryLoading.value = true
  try {
    const r = await fetchSecondaryUnits({
      status: secondaryStatus.value || undefined,
      keyword: secondaryKeyword.value || undefined
    })
    secondaryItems.value = r.items || []
  } finally { secondaryLoading.value = false }
}

// ---------- 消防栓 ----------
const hydrantItems = ref([])
const hydrantLoading = ref(false)
const hydrantPage = ref(1)
const hydrantPageSize = ref(10)
const hydrantTotal = ref(0)
const hydrantKeyword = ref('')
const hydrantStatus = ref('')
const hydrantDialog = ref(false)
const hydrantSubmitting = ref(false)
const currentHydrant = ref(null)
const hydrantForm = reactive({ location: '', road_name: '', district: '', pressure_mpa: null, install_date: '', remark: '' })
const hydrantTestDialog = ref(false)
const hydrantTestForm = reactive({ pressure_mpa: null, test_flow_ls: null, note: '' })

async function loadHydrants() {
  hydrantLoading.value = true
  try {
    const r = await fetchHydrants({
      keyword: hydrantKeyword.value || undefined,
      status: hydrantStatus.value || undefined,
      page: hydrantPage.value, page_size: hydrantPageSize.value
    })
    hydrantItems.value = r.items || []
    hydrantTotal.value = r.total || 0
  } finally { hydrantLoading.value = false }
}
function openHydrantDialog(row) {
  currentHydrant.value = row || null
  if (row) Object.assign(hydrantForm, row)
  else Object.assign(hydrantForm, { location: '', road_name: '', district: '', pressure_mpa: null, install_date: '', remark: '' })
  hydrantDialog.value = true
}
async function submitHydrant() {
  hydrantSubmitting.value = true
  try {
    if (currentHydrant.value?.id) {
      await updateHydrant(currentHydrant.value.id, hydrantForm)
      ElMessage.success('更新成功')
    } else {
      await createHydrant(hydrantForm)
      ElMessage.success('新增成功')
    }
    hydrantDialog.value = false
    loadHydrants()
  } catch (e) { ElMessage.error(e.message || '操作失败') }
  finally { hydrantSubmitting.value = false }
}
function openHydrantTest(row) { currentHydrant.value = row; Object.assign(hydrantTestForm, { pressure_mpa: row.pressure_mpa, test_flow_ls: null, note: '' }); hydrantTestDialog.value = true }
async function submitHydrantTest() {
  try {
    const r = await testHydrant(currentHydrant.value.id, hydrantTestForm)
    if (r.is_abnormal) ElMessage.warning('出水测试发现异常告警！')
    else ElMessage.success('测试完成')
    hydrantTestDialog.value = false
    loadHydrants(); loadSummary()
  } catch (e) { ElMessage.error(e.message || '操作失败') }
}
async function viewHydrantEvents(row) {
  try {
    const r = await fetchHydrantEvents(row.id)
    const html = (r.items || []).map(e => `${fmtTs(e.ts)} · ${e.type} · ${e.detail || ''}`).join('<br>') || '暂无事件'
    ElMessageBox.alert(html, '消防栓事件', { dangerouslyUseHTMLString: true })
  } catch (e) { ElMessage.error('加载失败') }
}

// ---------- 爆管 ----------
const burstItems = ref([])
const burstLoading = ref(false)
const burstStatus = ref('')
const burstHandleDialog = ref(false)
const currentBurst = ref(null)
const burstHandleForm = reactive({ status: '处置中' })

async function loadBurstCases() {
  burstLoading.value = true
  try {
    const r = await fetchBurstCases({ status: burstStatus.value || undefined })
    burstItems.value = r.items || []
  } finally { burstLoading.value = false }
}
async function viewBurstValves(row) {
  try {
    const r = await fetchBurstValves(row.id)
    const html = `<h4>推荐关阀顺序（共 ${(r.items || []).length} 步）</h4>` +
      (r.items || []).map(v => `
        <div style="margin:8px 0;padding:8px 12px;background:var(--app-card);border-radius:12px;display:flex;justify-content:space-between">
          <span>${v.order_no}. <strong>${v.position}</strong></span>
          <span style="color:var(--app-text-3);font-size:12px">${v.valve_code}</span>
        </div>
      `).join('')
    ElMessageBox.alert(html, '关阀方案', { dangerouslyUseHTMLString: true })
  } catch (e) { ElMessage.error('加载失败') }
}
function openBurstHandle(row) { currentBurst.value = row; burstHandleForm.status = row.status === '已修复' ? '已修复' : '处置中'; burstHandleDialog.value = true }
async function submitBurstHandle() {
  try {
    await handleBurst(currentBurst.value.id, burstHandleForm)
    ElMessage.success('状态已更新')
    burstHandleDialog.value = false
    loadBurstCases(); loadSummary()
  } catch (e) { ElMessage.error(e.message || '操作失败') }
}

// ---------- 工具 ----------
function fmtTs(ts) {
  if (!ts) return '-'
  const d = new Date(ts)
  const pad = (n) => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}`
}
function levelTag(l) { return { '高': 'danger', '中': 'warning', '低': 'info' }[l] || 'info' }

// ---------- 生命周期 ----------
onMounted(async () => {
  await Promise.allSettled([loadSummary()])
  loadCurrentTab()
})
</script>

<style scoped>
.stats-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
  margin-bottom: 16px;
}
.tabs-wrap { padding: 16px 20px 24px; }
.app-tabs { margin-top: 8px; }
.app-tabs :deep(.el-tabs__item) { font-weight: 500; padding: 0 20px; }

/* 水质节点卡片 */
.quality-node {
  background-color: var(--app-card);
  -webkit-backdrop-filter: blur(var(--app-glass-blur));
  backdrop-filter: blur(var(--app-glass-blur));
  border-radius: var(--app-radius-card);
  border: 1px solid var(--app-border);
  padding: 16px;
  margin-bottom: 16px;
  cursor: pointer;
  transition: transform 0.2s, box-shadow 0.2s;
}
.quality-node:hover { transform: translateY(-2px); box-shadow: var(--app-shadow-hover); }
.quality-node.abnormal { border-color: #FF3B30; box-shadow: 0 0 0 3px rgba(255,59,48,0.12); }
.quality-node__seq { font-size: 12px; color: var(--app-text-4); margin-bottom: 4px; }
.quality-node__kind { font-size: 13px; color: var(--app-primary); font-weight: 600; }
.quality-node__name { font-size: 15px; font-weight: 600; margin: 4px 0 10px; }
.quality-node__metrics { display: flex; gap: 14px; margin-bottom: 10px; font-size: 12px; }
.q-metric { display: flex; flex-direction: column; gap: 2px; }
.q-label { color: var(--app-text-4); font-size: 11px; }
.q-metric .danger { color: #FF3B30; font-weight: 600; }
@media (max-width: 1024px) {
  .stats-grid { grid-template-columns: repeat(2, 1fr); }
}
@media (max-width: 640px) {
  .stats-grid { grid-template-columns: 1fr; }
}
</style>
