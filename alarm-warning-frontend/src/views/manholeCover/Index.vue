<template>
  <div class="manhole-cover">
    <PageHeader title="井盖全生命周期管控" subtitle="Manhole Cover Lifecycle Management" />

    <!-- 顶部统计卡片 -->
    <div class="stats-grid">
      <StatCard label="井盖总数" :value="summary.manhole_total" icon="Grid" color="#0071E3" />
      <StatCard label="异常井盖" :value="summary.manhole_abnormal" icon="Warning" color="#FF3B30" />
      <StatCard label="活跃告警" :value="summary.active_alarms" icon="Bell" color="#FF9500" />
      <StatCard label="待处置工单" :value="summary.orders_pending" icon="Tickets" color="#5856D6" />
      <StatCard label="闭环率" :value="summary.close_rate_pct + '%'" icon="CircleCheck" color="#34C759" />
      <StatCard label="被盗案件" :value="summary.theft_cases" icon="Lock" color="#AF52DE" />
      <StatCard label="防坠网总数" :value="summary.net_total" icon="Connection" color="#30C0C0" />
      <StatCard label="破损防坠网" :value="summary.net_broken" icon="Opportunity" color="#FF2D55" />
    </div>

    <!-- Tab 切换五大功能 -->
    <div class="app-card tabs-wrap">
      <el-tabs v-model="activeTab" type="card" class="app-tabs" @tab-change="onTabChange">
        <!-- ========== Tab 1: 实时监测 ========== -->
        <el-tab-pane label="实时监测" name="monitor">
          <div class="filter-bar" style="margin-bottom:16px">
            <el-input v-model="monitorKeyword" placeholder="搜索编号/道路/位置" clearable style="width:240px" />
            <el-switch v-model="monitorOnlyAbnormal" active-text="仅看异常" />
            <el-button type="primary" size="default" @click="loadMonitorLatest">刷新</el-button>
          </div>
          <el-table :data="monitorItems" class="app-table" v-loading="monitorLoading" stripe>
            <el-table-column prop="code" label="编号" width="120" />
            <el-table-column prop="location" label="位置" min-width="160" show-overflow-tooltip />
            <el-table-column prop="road_name" label="道路" width="140" show-overflow-tooltip />
            <el-table-column prop="district" label="区域" width="90" />
            <el-table-column label="状态" width="100" align="center">
              <template #default="{ row }">
                <el-tag :type="statusTag(row.status)" effect="light" size="small">{{ row.status }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column label="倾角°" width="100" align="center">
              <template #default="{ row }">{{ row.tilt_deg ?? '-' }}</template>
            </el-table-column>
            <el-table-column label="位移mm" width="100" align="center">
              <template #default="{ row }">
                <span :style="{ color: row.displacement_mm >= 10 ? '#FF3B30' : '' }">{{ row.displacement_mm ?? '-' }}</span>
              </template>
            </el-table-column>
            <el-table-column label="破损" width="100" align="center">
              <template #default="{ row }">
                <el-tag v-if="row.damage && row.damage !== '完好'" type="danger" effect="light" size="small">{{ row.damage }}</el-tag>
                <span v-else class="text-muted">完好</span>
              </template>
            </el-table-column>
            <el-table-column label="水位cm" width="100" align="center">
              <template #default="{ row }">
                <span :style="{ color: row.water_level_cm >= 80 ? '#FF9500' : '' }">{{ row.water_level_cm ?? '-' }}</span>
              </template>
            </el-table-column>
            <el-table-column label="有毒气体ppm" width="130" align="center">
              <template #default="{ row }">
                <span :style="{ color: row.gas_ppm >= 10 ? '#FF3B30' : '' }">{{ row.gas_ppm ?? '-' }}</span>
              </template>
            </el-table-column>
          </el-table>
          <!-- 告警列表 -->
          <div style="margin-top:24px">
            <div class="card-title"><h3 class="card-title__text">风险告警记录</h3></div>
            <el-table :data="alarmItems" class="app-table" v-loading="alarmLoading" stripe>
              <el-table-column prop="alarm_code" label="告警编号" width="140" />
              <el-table-column prop="code" label="井盖编号" width="120" />
              <el-table-column prop="type" label="告警类型" width="120">
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
                  <el-tag :type="orderStatusTag(row.status)" effect="light" size="small">{{ row.status }}</el-tag>
                </template>
              </el-table-column>
              <el-table-column label="时间" width="170">
                <template #default="{ row }">{{ fmtTs(row.alarm_ts) }}</template>
              </el-table-column>
            </el-table>
            <div style="margin-top:12px;display:flex;justify-content:flex-end">
              <el-pagination v-model:current-page="alarmPage" v-model:page-size="alarmPageSize"
                :total="alarmTotal" :page-sizes="[10,20,50]" layout="total, sizes, prev, pager, next"
                @size-change="loadMonitorAlarms" @current-change="loadMonitorAlarms" />
            </div>
          </div>
        </el-tab-pane>

        <!-- ========== Tab 2: 一井一档 ========== -->
        <el-tab-pane label="一井一档" name="archive">
          <div class="filter-bar" style="margin-bottom:16px">
            <el-input v-model="archiveKeyword" placeholder="搜索编号/位置/道路" clearable style="width:240px" />
            <el-select v-model="archiveDistrict" placeholder="区域" clearable style="width:130px">
              <el-option v-for="d in archiveOptions.districts" :key="d" :label="d" :value="d" />
            </el-select>
            <el-select v-model="archiveType" placeholder="类型" clearable style="width:120px">
              <el-option v-for="t in archiveOptions.types" :key="t" :label="t" :value="t" />
            </el-select>
            <el-select v-model="archiveStatus" placeholder="状态" clearable style="width:120px">
              <el-option v-for="s in archiveOptions.statuses" :key="s" :label="s" :value="s" />
            </el-select>
            <el-button type="primary" @click="loadManholes">查询</el-button>
            <el-button type="success" @click="openManholeDialog()">新增井盖</el-button>
          </div>
          <el-table :data="manholeItems" class="app-table" v-loading="archiveLoading" stripe>
            <el-table-column prop="code" label="编号" width="120" />
            <el-table-column prop="location" label="位置" min-width="140" show-overflow-tooltip />
            <el-table-column prop="road_name" label="道路" width="130" show-overflow-tooltip />
            <el-table-column prop="district" label="区域" width="90" />
            <el-table-column prop="type" label="类型" width="80" />
            <el-table-column prop="owner_unit" label="权属单位" width="130" show-overflow-tooltip />
            <el-table-column label="状态" width="100" align="center">
              <template #default="{ row }">
                <el-tag :type="statusTag(row.status)" effect="light" size="small">{{ row.status }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="repairs" label="维修次数" width="90" align="center" />
            <el-table-column prop="alarms" label="告警次数" width="90" align="center" />
            <el-table-column label="操作" width="180" fixed="right">
              <template #default="{ row }">
                <el-button link type="primary" size="small" @click="viewManhole(row)">详情</el-button>
                <el-button link type="primary" size="small" @click="openManholeDialog(row)">编辑</el-button>
              </template>
            </el-table-column>
          </el-table>
          <div style="margin-top:12px;display:flex;justify-content:flex-end">
            <el-pagination v-model:current-page="archivePage" v-model:page-size="archivePageSize"
              :total="archiveTotal" :page-sizes="[10,20,50]" layout="total, sizes, prev, pager, next"
              @size-change="loadManholes" @current-change="loadManholes" />
          </div>
        </el-tab-pane>

        <!-- ========== Tab 3: 隐患闭环工单 ========== -->
        <el-tab-pane label="隐患处置" name="orders">
          <div class="filter-bar" style="margin-bottom:16px">
            <el-select v-model="orderStatus" placeholder="工单状态" clearable style="width:140px">
              <el-option v-for="s in ['待派发','处置中','待核验','已核验','已闭环']" :key="s" :label="s" :value="s" />
            </el-select>
            <el-input v-model="orderKeyword" placeholder="工单号/井盖编号" clearable style="width:220px" />
            <el-button type="primary" @click="loadOrders">查询</el-button>
          </div>
          <el-table :data="orderItems" class="app-table" v-loading="orderLoading" stripe>
            <el-table-column prop="order_code" label="工单号" width="140" />
            <el-table-column prop="code" label="井盖编号" width="120" />
            <el-table-column prop="alarm_type" label="告警类型" width="110" />
            <el-table-column label="告警等级" width="90" align="center">
              <template #default="{ row }">
                <el-tag :type="levelTag(row.alarm_level)" effect="dark" size="small">{{ row.alarm_level }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="handle_type" label="处置方式" width="100" />
            <el-table-column prop="assignee" label="负责人" width="110" />
            <el-table-column label="状态" width="100" align="center">
              <template #default="{ row }">
                <el-tag :type="orderStatusTag(row.status)" effect="light" size="small">{{ row.status }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column label="告警详情" min-width="220" show-overflow-tooltip>
              <template #default="{ row }">{{ row.alarm_detail }}</template>
            </el-table-column>
            <el-table-column label="操作" width="280" fixed="right">
              <template #default="{ row }">
                <div class="table-actions">
                  <el-button v-if="row.status === '待派发'" link type="primary" size="small" @click="openDispatch(row)">派发</el-button>
                  <el-button v-if="row.status === '处置中'" link type="warning" size="small" @click="openReport(row)">上报</el-button>
                  <el-button v-if="row.status === '待核验'" link type="success" size="small" @click="openVerify(row)">核验</el-button>
                  <el-button v-if="row.status === '已核验'" link type="primary" size="small" @click="closeOrder(row)">闭环</el-button>
                </div>
              </template>
            </el-table-column>
          </el-table>
          <div style="margin-top:12px;display:flex;justify-content:flex-end">
            <el-pagination v-model:current-page="orderPage" v-model:page-size="orderPageSize"
              :total="orderTotal" :page-sizes="[10,20,50]" layout="total, sizes, prev, pager, next"
              @size-change="loadOrders" @current-change="loadOrders" />
          </div>
        </el-tab-pane>

        <!-- ========== Tab 4: 被盗追踪 ========== -->
        <el-tab-pane label="被盗追踪" name="theft">
          <el-table :data="theftCases" class="app-table" v-loading="theftLoading" stripe>
            <el-table-column prop="alarm_code" label="告警编号" width="140" />
            <el-table-column prop="code" label="井盖编号" width="120" />
            <el-table-column prop="location" label="位置" min-width="140" show-overflow-tooltip />
            <el-table-column prop="district" label="区域" width="90" />
            <el-table-column label="井盖状态" width="100" align="center">
              <template #default="{ row }">
                <el-tag :type="statusTag(row.status)" effect="light" size="small">{{ row.status }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="track_points" label="轨迹点数" width="100" align="center" />
            <el-table-column prop="case_no" label="公安立案号" width="160" />
            <el-table-column prop="police_status" label="公安状态" width="110" />
            <el-table-column label="告警时间" width="170">
              <template #default="{ row }">{{ fmtTs(row.alarm_ts) }}</template>
            </el-table-column>
            <el-table-column label="操作" width="200" fixed="right">
              <template #default="{ row }">
                <div class="table-actions">
                  <el-button link type="primary" size="small" @click="viewTracks(row)">轨迹</el-button>
                  <el-button link type="primary" size="small" @click="locateTheft(row)">定位</el-button>
                  <el-button link type="success" size="small" @click="openPoliceDialog(row)">报案</el-button>
                </div>
              </template>
            </el-table-column>
          </el-table>
        </el-tab-pane>

        <!-- ========== Tab 5: 防坠网台账 ========== -->
        <el-tab-pane label="防坠网台账" name="safety">
          <div class="filter-bar" style="margin-bottom:16px">
            <el-select v-model="netStatus" placeholder="状态" clearable style="width:130px">
              <el-option v-for="s in ['已安装','破损','已维修','已更换']" :key="s" :label="s" :value="s" />
            </el-select>
            <el-input v-model="netKeyword" placeholder="网编号/井盖编号/位置" clearable style="width:240px" />
            <el-button type="primary" @click="loadSafetyNets">查询</el-button>
            <el-button type="success" @click="openNetDialog()">新增登记</el-button>
          </div>
          <el-table :data="netItems" class="app-table" v-loading="netLoading" stripe>
            <el-table-column prop="net_code" label="网编号" width="140" />
            <el-table-column prop="manhole_code" label="井盖编号" width="120" />
            <el-table-column prop="location" label="位置" min-width="140" show-overflow-tooltip />
            <el-table-column prop="road_name" label="道路" width="120" show-overflow-tooltip />
            <el-table-column prop="district" label="区域" width="90" />
            <el-table-column prop="material" label="材质" width="100" />
            <el-table-column prop="load_kg" label="承载kg" width="90" align="center" />
            <el-table-column label="状态" width="100" align="center">
              <template #default="{ row }">
                <el-tag :type="row.net_status === '破损' ? 'danger' : 'success'" effect="light" size="small">{{ row.net_status }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column label="安装日期" width="110">
              <template #default="{ row }">{{ row.install_date }}</template>
            </el-table-column>
            <el-table-column prop="repair_count" label="维修次数" width="90" align="center" />
            <el-table-column label="操作" width="160" fixed="right">
              <template #default="{ row }">
                <div class="table-actions">
                  <el-button link type="primary" size="small" @click="viewNetDetail(row)">详情</el-button>
                  <el-button link type="warning" size="small" @click="openNetMaintain(row)">登记运维</el-button>
                </div>
              </template>
            </el-table-column>
          </el-table>
          <div style="margin-top:12px;display:flex;justify-content:flex-end">
            <el-pagination v-model:current-page="netPage" v-model:page-size="netPageSize"
              :total="netTotal" :page-sizes="[10,20,50]" layout="total, sizes, prev, pager, next"
              @size-change="loadSafetyNets" @current-change="loadSafetyNets" />
          </div>
        </el-tab-pane>
      </el-tabs>
    </div>

    <!-- 井盖详情抽屉 -->
    <el-drawer v-model="detailDrawer" title="井盖详情" size="520px">
      <template v-if="currentManhole">
        <el-descriptions :column="1" border>
          <el-descriptions-item label="编号">{{ currentManhole.code }}</el-descriptions-item>
          <el-descriptions-item label="位置">{{ currentManhole.location }}</el-descriptions-item>
          <el-descriptions-item label="道路">{{ currentManhole.road_name }}</el-descriptions-item>
          <el-descriptions-item label="区域">{{ currentManhole.district }}</el-descriptions-item>
          <el-descriptions-item label="类型">{{ currentManhole.type }}</el-descriptions-item>
          <el-descriptions-item label="权属单位">{{ currentManhole.owner_unit }}</el-descriptions-item>
          <el-descriptions-item label="状态">
            <el-tag :type="statusTag(currentManhole.status)" effect="light">{{ currentManhole.status }}</el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="安装日期">{{ currentManhole.install_date }}</el-descriptions-item>
          <el-descriptions-item label="备注">{{ currentManhole.remark || '-' }}</el-descriptions-item>
        </el-descriptions>
        <div style="margin-top:20px">
          <h4 style="margin:0 0 10px">维修更换履历</h4>
          <el-table :data="currentManhole.repairs || []" size="small" stripe>
            <el-table-column prop="type" label="类型" width="80" />
            <el-table-column prop="date" label="日期" width="120" />
            <el-table-column prop="reason" label="原因" show-overflow-tooltip />
            <el-table-column prop="cost" label="费用" width="90" align="center" />
          </el-table>
        </div>
        <div style="margin-top:16px">
          <h4 style="margin:0 0 10px">告警记录</h4>
          <el-table :data="currentManhole.alarms || []" size="small" stripe max-height="240">
            <el-table-column prop="type" label="类型" width="100" />
            <el-table-column prop="level" label="等级" width="70" align="center">
              <template #default="{ row }">
                <el-tag :type="levelTag(row.level)" effect="dark" size="small">{{ row.level }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column label="时间">
              <template #default="{ row }">{{ fmtTs(row.alarm_ts) }}</template>
            </el-table-column>
          </el-table>
        </div>
      </template>
    </el-drawer>

    <!-- 轨迹查看 Drawer -->
    <el-drawer v-model="trackDrawer" title="异动轨迹" size="600px">
      <template v-if="trackData">
        <div v-if="trackData.manhole" style="margin-bottom:16px">
          <el-tag :type="statusTag(trackData.manhole.status)" effect="light">{{ trackData.manhole.status }}</el-tag>
          <span style="margin-left:8px">{{ trackData.manhole.code }} · {{ trackData.manhole.location }}</span>
        </div>
        <el-table :data="trackData.tracks || []" size="small" stripe>
          <el-table-column label="时间" width="170">
            <template #default="{ row }">{{ fmtTs(row.ts) }}</template>
          </el-table-column>
          <el-table-column prop="lat" label="纬度" width="100" />
          <el-table-column prop="lng" label="经度" width="100" />
          <el-table-column prop="speed_kmh" label="km/h" width="80" align="center" />
          <el-table-column prop="note" label="备注" show-overflow-tooltip />
        </el-table>
      </template>
    </el-drawer>

    <!-- 井盖编辑 Dialog -->
    <el-dialog v-model="manholeDialog" :title="currentManhole?.id ? '编辑井盖' : '新增井盖'" width="560px">
      <el-form :model="manholeForm" label-width="100px">
        <el-form-item label="位置"><el-input v-model="manholeForm.location" /></el-form-item>
        <el-form-item label="道路名称"><el-input v-model="manholeForm.road_name" /></el-form-item>
        <el-form-item label="区域"><el-input v-model="manholeForm.district" /></el-form-item>
        <el-form-item label="类型">
          <el-select v-model="manholeForm.type" style="width:100%">
            <el-option v-for="t in archiveOptions.types" :key="t" :label="t" :value="t" />
          </el-select>
        </el-form-item>
        <el-form-item label="权属单位"><el-input v-model="manholeForm.owner_unit" /></el-form-item>
        <el-form-item label="材质"><el-input v-model="manholeForm.material" /></el-form-item>
        <el-form-item label="安装日期"><el-input v-model="manholeForm.install_date" placeholder="2024-01-01" /></el-form-item>
        <el-form-item label="备注"><el-input v-model="manholeForm.remark" type="textarea" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="manholeDialog = false">取消</el-button>
        <el-button type="primary" :loading="manholeSubmitting" @click="submitManhole">确定</el-button>
      </template>
    </el-dialog>

    <!-- 工单派发 Dialog -->
    <el-dialog v-model="dispatchDialog" title="派发工单" width="440px">
      <el-form :model="dispatchForm" label-width="90px">
        <el-form-item label="工单">{{ currentOrder?.order_code }}</el-form-item>
        <el-form-item label="负责人"><el-input v-model="dispatchForm.assignee" placeholder="运维班组/负责人" /></el-form-item>
        <el-form-item label="处置方式">
          <el-select v-model="dispatchForm.handle_type" style="width:100%">
            <el-option v-for="t in ['维修','更换','现场核查','公安报案']" :key="t" :label="t" :value="t" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dispatchDialog = false">取消</el-button>
        <el-button type="primary" @click="submitDispatch">确定派发</el-button>
      </template>
    </el-dialog>

    <!-- 处置上报 Dialog -->
    <el-dialog v-model="reportDialog" title="现场处置信息上报" width="480px">
      <el-form :model="reportForm" label-width="90px">
        <el-form-item label="处置详情">
          <el-input v-model="reportForm.report_info" type="textarea" rows="4" placeholder="请输入现场处置情况..." />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="reportDialog = false">取消</el-button>
        <el-button type="primary" @click="submitReport">提交上报</el-button>
      </template>
    </el-dialog>

    <!-- 核验 Dialog -->
    <el-dialog v-model="verifyDialog" title="整改结果核验" width="480px">
      <el-form :model="verifyForm" label-width="90px">
        <el-form-item label="核验结论">
          <el-switch v-model="verifyForm.passed" active-text="核验通过" inactive-text="核验不通过" />
        </el-form-item>
        <el-form-item label="结果说明">
          <el-input v-model="verifyForm.verify_result" type="textarea" rows="3" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="verifyDialog = false">取消</el-button>
        <el-button type="primary" @click="submitVerify">提交核验</el-button>
      </template>
    </el-dialog>

    <!-- 公安报案 Dialog -->
    <el-dialog v-model="policeDialog" title="新增公安联动记录" width="500px">
      <el-form :model="policeForm" label-width="90px">
        <el-form-item label="公安单位"><el-input v-model="policeForm.police_unit" /></el-form-item>
        <el-form-item label="联系方式"><el-input v-model="policeForm.contact" /></el-form-item>
        <el-form-item label="立案号（可选）"><el-input v-model="policeForm.case_no" /></el-form-item>
        <el-form-item label="状态">
          <el-select v-model="policeForm.status" style="width:100%">
            <el-option v-for="s in ['已报案','已立案','侦破中','已追回']" :key="s" :label="s" :value="s" />
          </el-select>
        </el-form-item>
        <el-form-item label="结果"><el-input v-model="policeForm.result" type="textarea" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="policeDialog = false">取消</el-button>
        <el-button type="primary" @click="submitPolice">提交</el-button>
      </template>
    </el-dialog>

    <!-- 防坠网新增 Dialog -->
    <el-dialog v-model="netDialog" title="防坠网安装登记" width="480px">
      <el-form :model="netForm" label-width="90px">
        <el-form-item label="井盖ID"><el-input-number v-model="netForm.manhole_id" :min="1" /></el-form-item>
        <el-form-item label="安装日期"><el-input v-model="netForm.install_date" placeholder="2024-01-01" /></el-form-item>
        <el-form-item label="材质">
          <el-select v-model="netForm.material" style="width:100%" placeholder="请选择">
            <el-option label="聚乙烯" value="聚乙烯" />
            <el-option label="尼龙" value="尼龙" />
            <el-option label="不锈钢" value="不锈钢" />
          </el-select>
        </el-form-item>
        <el-form-item label="承载kg"><el-input-number v-model="netForm.load_kg" :min="0" /></el-form-item>
        <el-form-item label="下次检查"><el-input v-model="netForm.next_check" placeholder="2024-06-01" /></el-form-item>
        <el-form-item label="备注"><el-input v-model="netForm.remark" type="textarea" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="netDialog = false">取消</el-button>
        <el-button type="primary" @click="submitNet">提交</el-button>
      </template>
    </el-dialog>

    <!-- 防坠网运维登记 Dialog -->
    <el-dialog v-model="netMaintainDialog" title="登记运维记录" width="440px">
      <el-form :model="netMaintainForm" label-width="90px">
        <el-form-item label="运维类型">
          <el-select v-model="netMaintainForm.type" style="width:100%">
            <el-option v-for="t in ['破损登记','维修','更换']" :key="t" :label="t" :value="t" />
          </el-select>
        </el-form-item>
        <el-form-item label="日期"><el-input v-model="netMaintainForm.date" placeholder="2024-01-01" /></el-form-item>
        <el-form-item label="详情"><el-input v-model="netMaintainForm.detail" type="textarea" /></el-form-item>
        <el-form-item label="操作人"><el-input v-model="netMaintainForm.operator" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="netMaintainDialog = false">取消</el-button>
        <el-button type="primary" @click="submitNetMaintain">提交</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import PageHeader from '@/components/PageHeader.vue'
import StatCard from '@/components/StatCard.vue'
import {
  fetchSummary,
  fetchMonitorLatest, fetchMonitorAlarms,
  fetchManholes, fetchArchiveOptions, fetchManholeDetail,
  fetchOrders,
  fetchTheftCases, fetchTheftTracks, locateManhole,
  fetchSafetyNets, fetchSafetyNetDetail,
  createManhole, updateManhole,
  dispatchOrder, reportOrder, verifyOrder, closeOrder as closeOrderApi,
  createPoliceRecord,
  createSafetyNet, maintainSafetyNet
} from '@/api/manholeCover'

import {
  Grid, Warning, Bell, Tickets, CircleCheck, Lock, Connection, Opportunity
} from '@element-plus/icons-vue'

// ---------- 汇总 ----------
const summary = reactive({
  manhole_total: 0, manhole_abnormal: 0, active_alarms: 0,
  orders_pending: 0, close_rate_pct: 0, theft_cases: 0,
  net_total: 0, net_broken: 0
})
async function loadSummary() {
  try {
    const r = await fetchSummary()
    Object.assign(summary, r)
  } catch (e) { /* 后端未启动时静默 */ }
}

// ---------- Tab 切换 ----------
const activeTab = ref('monitor')
function onTabChange() { loadCurrentTab() }
function loadCurrentTab() {
  const map = {
    monitor: loadMonitorLatest,
    archive: loadManholes,
    orders: loadOrders,
    theft: loadTheftCases,
    safety: loadSafetyNets
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

// 告警
const alarmItems = ref([])
const alarmLoading = ref(false)
const alarmPage = ref(1)
const alarmPageSize = ref(20)
const alarmTotal = ref(0)
async function loadMonitorAlarms() {
  alarmLoading.value = true
  try {
    const r = await fetchMonitorAlarms({ page: alarmPage.value, page_size: alarmPageSize.value })
    alarmItems.value = r.items || []
    alarmTotal.value = r.total || 0
  } finally { alarmLoading.value = false }
}

// ---------- 档案 ----------
const manholeItems = ref([])
const archiveLoading = ref(false)
const archivePage = ref(1)
const archivePageSize = ref(20)
const archiveTotal = ref(0)
const archiveKeyword = ref('')
const archiveDistrict = ref('')
const archiveType = ref('')
const archiveStatus = ref('')
const archiveOptions = reactive({ districts: [], owners: [], types: [], statuses: [] })

async function loadArchiveOptions() {
  try {
    const r = await fetchArchiveOptions()
    Object.assign(archiveOptions, r)
  } catch (e) { /* */ }
}

async function loadManholes() {
  archiveLoading.value = true
  try {
    const r = await fetchManholes({
      keyword: archiveKeyword.value || undefined,
      district: archiveDistrict.value || undefined,
      type: archiveType.value || undefined,
      status: archiveStatus.value || undefined,
      page: archivePage.value, page_size: archivePageSize.value
    })
    manholeItems.value = r.items || []
    archiveTotal.value = r.total || 0
  } finally { archiveLoading.value = false }
}

const currentManhole = ref(null)
const detailDrawer = ref(false)
async function viewManhole(row) {
  try {
    currentManhole.value = await fetchManholeDetail(row.id)
    detailDrawer.value = true
  } catch (e) { ElMessage.error('加载详情失败') }
}

const manholeDialog = ref(false)
const manholeSubmitting = ref(false)
const manholeForm = reactive({ location: '', road_name: '', district: '', type: '雨水', owner_unit: '', material: '', install_date: '', remark: '' })
function openManholeDialog(row) {
  currentManhole.value = row || null
  if (row) {
    Object.assign(manholeForm, row)
  } else {
    Object.assign(manholeForm, { location: '', road_name: '', district: '', type: '雨水', owner_unit: '', material: '', install_date: '', remark: '' })
  }
  manholeDialog.value = true
}
async function submitManhole() {
  manholeSubmitting.value = true
  try {
    if (currentManhole.value?.id) {
      await updateManhole(currentManhole.value.id, manholeForm)
      ElMessage.success('更新成功')
    } else {
      await createManhole(manholeForm)
      ElMessage.success('新增成功')
    }
    manholeDialog.value = false
    loadManholes()
  } catch (e) { ElMessage.error(e.message || '操作失败') }
  finally { manholeSubmitting.value = false }
}

// ---------- 工单 ----------
const orderItems = ref([])
const orderLoading = ref(false)
const orderPage = ref(1)
const orderPageSize = ref(20)
const orderTotal = ref(0)
const orderStatus = ref('')
const orderKeyword = ref('')
async function loadOrders() {
  orderLoading.value = true
  try {
    const r = await fetchOrders({
      status: orderStatus.value || undefined,
      keyword: orderKeyword.value || undefined,
      page: orderPage.value, page_size: orderPageSize.value
    })
    orderItems.value = r.items || []
    orderTotal.value = r.total || 0
  } finally { orderLoading.value = false }
}

const currentOrder = ref(null)
const dispatchDialog = ref(false)
const dispatchForm = reactive({ assignee: '', handle_type: '维修' })
function openDispatch(row) { currentOrder.value = row; Object.assign(dispatchForm, { assignee: '', handle_type: '维修' }); dispatchDialog.value = true }
async function submitDispatch() {
  try {
    await dispatchOrder(currentOrder.value.id, dispatchForm)
    ElMessage.success('派发成功')
    dispatchDialog.value = false
    loadOrders(); loadSummary()
  } catch (e) { ElMessage.error(e.message || '操作失败') }
}

const reportDialog = ref(false)
const reportForm = reactive({ report_info: '' })
function openReport(row) { currentOrder.value = row; reportForm.report_info = ''; reportDialog.value = true }
async function submitReport() {
  try {
    await reportOrder(currentOrder.value.id, reportForm)
    ElMessage.success('上报成功')
    reportDialog.value = false
    loadOrders()
  } catch (e) { ElMessage.error(e.message || '操作失败') }
}

const verifyDialog = ref(false)
const verifyForm = reactive({ passed: true, verify_result: '' })
function openVerify(row) { currentOrder.value = row; Object.assign(verifyForm, { passed: true, verify_result: '' }); verifyDialog.value = true }
async function submitVerify() {
  try {
    await verifyOrder(currentOrder.value.id, verifyForm)
    ElMessage.success('核验成功')
    verifyDialog.value = false
    loadOrders()
  } catch (e) { ElMessage.error(e.message || '操作失败') }
}

async function closeOrder(row) {
  try {
    await ElMessageBox.confirm('确认对该工单执行闭环销号？', '闭环确认')
    await closeOrderApi(row.id)
    ElMessage.success('已闭环')
    loadOrders(); loadSummary()
  } catch (e) { if (e !== 'cancel') ElMessage.error(e.message || '操作失败') }
}

// ---------- 被盗追踪 ----------
const theftCases = ref([])
const theftLoading = ref(false)
async function loadTheftCases() {
  theftLoading.value = true
  try {
    const r = await fetchTheftCases()
    theftCases.value = r.cases || []
  } finally { theftLoading.value = false }
}

const trackDrawer = ref(false)
const trackData = ref(null)
async function viewTracks(row) {
  try {
    trackData.value = await fetchTheftTracks(row.manhole_id)
    trackDrawer.value = true
  } catch (e) { ElMessage.error('加载轨迹失败') }
}
async function locateTheft(row) {
  try {
    const r = await locateManhole(row.manhole_id)
    ElMessage.success(`当前位置：${r.lat}, ${r.lng}（来源：${r.source}）`)
  } catch (e) { ElMessage.error('定位失败') }
}

const policeDialog = ref(false)
const policeForm = reactive({ police_unit: '', contact: '', case_no: '', status: '已报案', result: '' })
async function openPoliceDialog(row) {
  policeForm.case_no = row.case_no || ''
  policeDialog.value = true
}
async function submitPolice() {
  try {
    await createPoliceRecord(policeForm)
    ElMessage.success('报案成功')
    policeDialog.value = false
    loadTheftCases()
  } catch (e) { ElMessage.error(e.message || '操作失败') }
}

// ---------- 防坠网 ----------
const netItems = ref([])
const netLoading = ref(false)
const netPage = ref(1)
const netPageSize = ref(20)
const netTotal = ref(0)
const netStatus = ref('')
const netKeyword = ref('')
async function loadSafetyNets() {
  netLoading.value = true
  try {
    const r = await fetchSafetyNets({
      net_status: netStatus.value || undefined,
      keyword: netKeyword.value || undefined,
      page: netPage.value, page_size: netPageSize.value
    })
    netItems.value = r.items || []
    netTotal.value = r.total || 0
  } finally { netLoading.value = false }
}

const netDialog = ref(false)
const netForm = reactive({ manhole_id: 1, install_date: '', material: '', load_kg: null, next_check: '', remark: '' })
function openNetDialog() {
  Object.assign(netForm, { manhole_id: 1, install_date: '', material: '', load_kg: null, next_check: '', remark: '' })
  netDialog.value = true
}
async function submitNet() {
  try {
    await createSafetyNet(netForm)
    ElMessage.success('登记成功')
    netDialog.value = false
    loadSafetyNets(); loadSummary()
  } catch (e) { ElMessage.error(e.message || '操作失败') }
}

const netMaintainDialog = ref(false)
const netMaintainForm = reactive({ type: '破损登记', date: '', detail: '', operator: '' })
const currentNet = ref(null)
async function viewNetDetail(row) {
  try {
    const r = await fetchSafetyNetDetail(row.id)
    ElMessageBox.alert(
      `<strong>${r.item.net_code}</strong><br>
       状态：${r.item.net_status}<br>
       材质：${r.item.material || '-'}<br>
       安装：${r.item.install_date}<br>
       <h4 style="margin-top:12px">运维记录</h4>
       ${(r.maintains || []).map(m => `${m.date} · ${m.type} · ${m.detail || ''}`).join('<br>') || '暂无记录'}`,
      '防坠网详情', { dangerouslyUseHTMLString: true }
    )
  } catch (e) { ElMessage.error('加载失败') }
}
function openNetMaintain(row) {
  currentNet.value = row
  Object.assign(netMaintainForm, { type: '破损登记', date: new Date().toISOString().slice(0, 10), detail: '', operator: '' })
  netMaintainDialog.value = true
}
async function submitNetMaintain() {
  try {
    await maintainSafetyNet(currentNet.value.id, netMaintainForm)
    ElMessage.success('登记成功')
    netMaintainDialog.value = false
    loadSafetyNets(); loadSummary()
  } catch (e) { ElMessage.error(e.message || '操作失败') }
}

// ---------- 工具函数 ----------
function fmtTs(ts) {
  if (!ts) return '-'
  const d = new Date(ts)
  const pad = (n) => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}:${pad(d.getSeconds())}`
}
function statusTag(s) {
  return { '正常': 'success', '告警': 'warning', '处置中': 'primary', '被盗': 'danger', '维修中': 'info' }[s] || 'info'
}
function orderStatusTag(s) {
  return { '待派发': 'warning', '已派发': 'primary', '处置中': 'primary', '待核验': 'warning', '已核验': 'success', '已闭环': 'info' }[s] || 'info'
}
function levelTag(l) {
  return { '高': 'danger', '中': 'warning', '低': 'info' }[l] || 'info'
}

// ---------- 生命周期 ----------
onMounted(async () => {
  await Promise.allSettled([loadSummary(), loadArchiveOptions()])
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
.app-tabs :deep(.el-tabs__item) {
  font-weight: 500;
  padding: 0 20px;
}
.text-muted { color: var(--app-text-4); }
@media (max-width: 1024px) {
  .stats-grid { grid-template-columns: repeat(2, 1fr); }
}
@media (max-width: 640px) {
  .stats-grid { grid-template-columns: 1fr; }
}
</style>
