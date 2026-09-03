<template>
  <div class="work-order">
    <PageHeader title="工单管理" subtitle="Work Order Management">
      <el-upload
        v-if="canImport"
        class="work-order__upload"
        :show-file-list="false"
        :http-request="handleImport"
        accept=".xlsx,.xls"
      >
        <el-button :loading="importing">
          <el-icon><Upload /></el-icon> 导入Excel
        </el-button>
      </el-upload>
      <el-button v-if="canExport" @click="handleExport">
        <el-icon><Download /></el-icon> 导出Excel
      </el-button>
      <el-button @click="refreshCurrentTab">刷新</el-button>
      <el-button v-if="canAdd" type="primary" @click="openOrderDialog(null)">
        <el-icon><Plus /></el-icon> 新增工单
      </el-button>
    </PageHeader>

    <!-- 4 个统计卡片 -->
    <div class="work-order__stats">
      <StatCard label="工单总数" :value="overview?.total_orders ?? 0" icon="Tickets" color="#0071E3" />
      <StatCard label="待派单" :value="overview?.pending_dispatch ?? 0" icon="Promotion" color="#FF9500" />
      <StatCard label="逾期工单" :value="overview?.overdue_orders ?? 0" icon="AlarmClock" color="#FF3B30" />
      <StatCard label="平均评分" :value="overview?.avg_rating ?? 0" icon="Star" color="#34C759" />
    </div>

    <!-- 主体：4 个 Tab -->
    <section class="app-card work-order__main">
      <el-tabs v-model="activeTab" @tab-change="handleTabChange">
        <!-- ============ Tab 1 工单列表 ============ -->
        <el-tab-pane label="工单列表" name="orders">
          <div class="filter-bar work-order__filter">
            <el-input
              v-model="orderQuery.keyword"
              placeholder="标题/编号/位置"
              clearable
              class="work-order__filter-item"
              @input="orderPage = 1"
            />
            <el-select v-model="orderQuery.priority" placeholder="优先级" clearable class="work-order__filter-item" @change="orderPage = 1">
              <el-option v-for="(label, key) in PRIORITY_TEXT" :key="key" :label="label" :value="key" />
            </el-select>
            <el-select v-model="orderQuery.status" placeholder="工单状态" clearable class="work-order__filter-item" @change="orderPage = 1">
              <el-option v-for="(label, key) in STATUS_TEXT" :key="key" :label="label" :value="key" />
            </el-select>
            <el-select v-model="orderQuery.channel" placeholder="来源渠道" clearable class="work-order__filter-item" @change="orderPage = 1">
              <el-option v-for="c in channelOptions" :key="c.key" :label="c.name" :value="c.key" />
            </el-select>
            <el-select v-model="orderQuery.category" placeholder="工单类别" clearable class="work-order__filter-item" @change="orderPage = 1">
              <el-option v-for="c in categoryOptions" :key="c.key" :label="c.name" :value="c.key" />
            </el-select>
            <el-button type="primary" @click="loadOrders">
              <el-icon><Search /></el-icon> 查询
            </el-button>
            <el-button @click="resetOrderQuery">重置</el-button>
          </div>

          <el-table :data="pagedOrders" v-loading="ordersLoading" class="app-table" empty-text="暂无工单数据">
            <el-table-column prop="order_id" label="工单编号" width="130">
              <template #default="{ row }"><span class="code-cell">{{ row.order_id }}</span></template>
            </el-table-column>
            <el-table-column prop="title" label="标题" min-width="170" show-overflow-tooltip>
              <template #default="{ row }">
                {{ row.title }}
                <el-tag v-if="row.escalated" type="danger" size="small" class="esc-tag">升级</el-tag>
              </template>
            </el-table-column>
            <el-table-column label="渠道" width="100" align="center">
              <template #default="{ row }">{{ channelName(row.channel) }}</template>
            </el-table-column>
            <el-table-column label="类别" width="90" align="center">
              <template #default="{ row }">{{ categoryName(row.category) }}</template>
            </el-table-column>
            <el-table-column label="优先级" width="90" align="center">
              <template #default="{ row }">
                <el-tag :type="priorityType(row.priority)" size="small">{{ priorityText(row.priority) }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column label="状态" width="100" align="center">
              <template #default="{ row }">
                <el-tag :type="statusType(row.status)" size="small">{{ statusText(row.status) }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="location" label="位置" width="140" show-overflow-tooltip />
            <el-table-column label="处理人" width="90" align="center">
              <template #default="{ row }">{{ row.assignee || '-' }}</template>
            </el-table-column>
            <el-table-column prop="reporter" label="上报人" width="90" align="center" />
            <el-table-column label="创建时间" width="160">
              <template #default="{ row }"><span class="time-cell">{{ formatDateTime(row.created_at) }}</span></template>
            </el-table-column>
            <el-table-column label="操作" width="220" align="center" fixed="right">
              <template #default="{ row }">
                <div class="table-actions">
                  <el-button link type="primary" size="small" @click="openOrderDetail(row)">详情</el-button>
                  <el-button link type="success" size="small" @click="handleAdvance(row)">推进</el-button>
                  <el-button link type="warning" size="small" @click="openOrderDialog(row)">编辑</el-button>
                  <el-button link type="danger" size="small" @click="handleDeleteOrder(row)">删除</el-button>
                </div>
              </template>
            </el-table-column>
          </el-table>

          <div class="work-order__pagination">
            <el-pagination
              v-model:current-page="orderPage"
              v-model:page-size="orderPageSize"
              :total="filteredOrders.length"
              :page-sizes="[10, 20, 50]"
              layout="total, sizes, prev, pager, next"
            />
          </div>
        </el-tab-pane>

        <!-- ============ Tab 2 智能派单 ============ -->
        <el-tab-pane label="智能派单" name="dispatch">
          <div class="filter-bar work-order__filter">
            <el-select
              v-model="dispatchOrderId"
              filterable
              placeholder="选择待派工单"
              class="work-order__dispatch-select"
            >
              <el-option
                v-for="o in allOrders"
                :key="o.order_id"
                :label="`${o.order_id} · ${o.title}`"
                :value="o.order_id"
              />
            </el-select>
            <el-button type="primary" :loading="dispatchLoading" @click="loadRecommend">
              <el-icon><Search /></el-icon> 获取推荐
            </el-button>
          </div>

          <template v-if="dispatchResult">
            <el-alert
              :title="`推荐结论：${recommendationText}`"
              type="success"
              :closable="false"
              show-icon
              class="work-order__recommend-alert"
            />
            <el-descriptions :column="3" border size="small" class="work-order__dispatch-meta">
              <el-descriptions-item label="工单编号">
                <span class="code-cell">{{ dispatchResult.order_id }}</span>
              </el-descriptions-item>
              <el-descriptions-item label="所需技能">{{ dispatchResult.required_skill || '-' }}</el-descriptions-item>
              <el-descriptions-item label="工单位置">{{ dispatchResult.location || '-' }}</el-descriptions-item>
            </el-descriptions>

            <el-table :data="dispatchResult.candidates || []" class="app-table" empty-text="暂无候选人">
              <el-table-column label="排名" width="70" align="center">
                <template #default="{ $index }">
                  <span class="rank-cell" :class="{ 'rank-cell--top': $index === 0 }">{{ $index + 1 }}</span>
                </template>
              </el-table-column>
              <el-table-column prop="name" label="姓名" width="100" />
              <el-table-column label="技能" min-width="180">
                <template #default="{ row }">
                  <el-tag v-for="s in skillList(row.skills)" :key="s" size="small" class="skill-tag">{{ s }}</el-tag>
                </template>
              </el-table-column>
              <el-table-column label="状态" width="90" align="center">
                <template #default="{ row }">
                  <el-tag :type="staffStatusType(row.status)" size="small">
                    {{ row.status_name || staffStatusText(row.status) }}
                  </el-tag>
                </template>
              </el-table-column>
              <el-table-column prop="location" label="当前位置" width="130" show-overflow-tooltip />
              <el-table-column label="距离" width="90" align="right">
                <template #default="{ row }">{{ row.distance_m != null ? `${row.distance_m} m` : '-' }}</template>
              </el-table-column>
              <el-table-column label="技能匹配" width="90" align="center">
                <template #default="{ row }">
                  <el-tag v-if="typeof row.skill_match === 'boolean'" :type="row.skill_match ? 'success' : 'info'" size="small">
                    {{ row.skill_match ? '匹配' : '不匹配' }}
                  </el-tag>
                  <span v-else>{{ row.skill_match ?? '-' }}</span>
                </template>
              </el-table-column>
              <el-table-column label="评分" width="80" align="center">
                <template #default="{ row }">{{ fmtRating(row.avg_rating) }}</template>
              </el-table-column>
              <el-table-column label="综合得分" width="140" align="center">
                <template #default="{ row }">
                  <div class="score-cell">
                    <span class="score-cell__value">{{ fmtScore(row.total_score) }}</span>
                    <div class="score-bar">
                      <div class="score-bar__fill" :style="{ width: scoreBarPct(row.total_score) }"></div>
                    </div>
                  </div>
                </template>
              </el-table-column>
              <el-table-column label="得分明细" width="90" align="center">
                <template #default="{ row }">
                  <el-popover placement="left" :width="260" trigger="hover">
                    <template #reference>
                      <el-button link type="primary" size="small">查看</el-button>
                    </template>
                    <div class="score-breakdown">
                      <div v-for="(v, k) in row.score_breakdown || {}" :key="k" class="score-breakdown__row">
                        <span class="score-breakdown__key">{{ k }}</span>
                        <span class="score-breakdown__val">{{ v }}</span>
                      </div>
                      <div v-if="!row.score_breakdown" class="score-breakdown__empty">暂无明细</div>
                    </div>
                  </el-popover>
                </template>
              </el-table-column>
              <el-table-column label="操作" width="80" align="center" fixed="right">
                <template #default="{ row }">
                  <div class="table-actions">
                    <el-button link type="primary" size="small" @click="handleAssign(row)">派单</el-button>
                  </div>
                </template>
              </el-table-column>
            </el-table>
          </template>
          <el-empty v-else description="选择工单后点击「获取推荐」查看智能派单候选人" :image-size="80" />
        </el-tab-pane>

        <!-- ============ Tab 3 运维人员 ============ -->
        <el-tab-pane label="运维人员" name="staff">
          <header class="card-title">
            <h3 class="card-title__text">人员列表</h3>
            <span class="card-title__badge">共 {{ staffList.length }} 人 · 空闲 {{ overview?.staff_idle ?? 0 }} 人</span>
          </header>
          <el-table :data="staffList" v-loading="staffLoading" class="app-table" empty-text="暂无运维人员">
            <el-table-column prop="staff_id" label="编号" width="120">
              <template #default="{ row }"><span class="code-cell">{{ row.staff_id }}</span></template>
            </el-table-column>
            <el-table-column prop="name" label="姓名" width="100" />
            <el-table-column label="技能" min-width="220">
              <template #default="{ row }">
                <el-tag v-for="s in skillList(row.skills)" :key="s" size="small" class="skill-tag">{{ s }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column label="状态" width="90" align="center">
              <template #default="{ row }">
                <el-tag :type="staffStatusType(row.status)" size="small">{{ staffStatusText(row.status) }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="location" label="当前位置" width="140" show-overflow-tooltip />
            <el-table-column prop="phone" label="联系电话" width="130" />
            <el-table-column prop="completed_orders" label="完成工单" width="90" align="right" />
            <el-table-column label="平均评分" width="90" align="center">
              <template #default="{ row }"><span class="num-cell">{{ fmtRating(row.avg_rating) }}</span></template>
            </el-table-column>
          </el-table>

          <header class="card-title work-order__section-title">
            <h3 class="card-title__text">工作负载</h3>
          </header>
          <el-table :data="workloadList" v-loading="staffLoading" class="app-table" empty-text="暂无负载数据">
            <el-table-column prop="staff_id" label="编号" width="120">
              <template #default="{ row }"><span class="code-cell">{{ row.staff_id }}</span></template>
            </el-table-column>
            <el-table-column prop="name" label="姓名" width="100" />
            <el-table-column label="状态" width="90" align="center">
              <template #default="{ row }">
                <el-tag :type="staffStatusType(row.status)" size="small">
                  {{ row.status_name || staffStatusText(row.status) }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column label="在处理工单" width="110" align="center">
              <template #default="{ row }">
                <span class="workload-badge" :class="{ 'workload-badge--busy': row.active_orders > 0 }">
                  {{ row.active_orders ?? 0 }}
                </span>
              </template>
            </el-table-column>
            <el-table-column prop="completed_orders" label="累计完成" width="100" align="right" />
            <el-table-column label="平均评分" width="100" align="center">
              <template #default="{ row }"><span class="num-cell">{{ fmtRating(row.avg_rating) }}</span></template>
            </el-table-column>
          </el-table>
        </el-tab-pane>

        <!-- ============ Tab 4 SLA管控 ============ -->
        <el-tab-pane label="SLA管控" name="sla">
          <div class="sla-summary" v-loading="slaLoading">
            <div class="sla-tile sla-tile--normal">
              <div class="sla-tile__value">{{ slaSummary.normal ?? 0 }}</div>
              <div class="sla-tile__label">正常</div>
            </div>
            <div class="sla-tile sla-tile--warning">
              <div class="sla-tile__value">{{ slaSummary.warning ?? 0 }}</div>
              <div class="sla-tile__label">预警</div>
            </div>
            <div class="sla-tile sla-tile--overdue">
              <div class="sla-tile__value">{{ slaSummary.overdue ?? 0 }}</div>
              <div class="sla-tile__label">逾期</div>
            </div>
            <div class="sla-tile sla-tile--escalated">
              <div class="sla-tile__value">{{ slaSummary.escalated ?? 0 }}</div>
              <div class="sla-tile__label">已升级</div>
            </div>
            <div class="sla-tile sla-tile--total">
              <div class="sla-tile__value">{{ slaMonitor?.monitored ?? 0 }}</div>
              <div class="sla-tile__label">监控中工单</div>
            </div>
          </div>

          <header class="card-title work-order__section-title">
            <h3 class="card-title__text">SLA 实时监控</h3>
          </header>
          <el-table :data="slaItems" v-loading="slaLoading" class="app-table" empty-text="暂无监控工单">
            <el-table-column prop="order_id" label="工单编号" width="130">
              <template #default="{ row }"><span class="code-cell">{{ row.order_id }}</span></template>
            </el-table-column>
            <el-table-column prop="title" label="标题" min-width="160" show-overflow-tooltip />
            <el-table-column label="优先级" width="90" align="center">
              <template #default="{ row }">
                <el-tag :type="priorityType(row.priority)" size="small">
                  {{ row.priority_name || priorityText(row.priority) }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column label="状态" width="100" align="center">
              <template #default="{ row }">
                <el-tag :type="statusType(row.status)" size="small">
                  {{ row.status_name || statusText(row.status) }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column label="处理人" width="90" align="center">
              <template #default="{ row }">{{ row.assignee || '-' }}</template>
            </el-table-column>
            <el-table-column label="已耗时" width="90" align="right">
              <template #default="{ row }">{{ fmtHours(row.elapsed_hours) }} h</template>
            </el-table-column>
            <el-table-column label="SLA时限" width="90" align="right">
              <template #default="{ row }">{{ fmtHours(row.sla_hours) }} h</template>
            </el-table-column>
            <el-table-column label="剩余时间" width="100" align="right">
              <template #default="{ row }">
                <span :class="Number(row.remaining_hours) < 0 ? 'remaining--over' : 'remaining--ok'">
                  {{ fmtHours(row.remaining_hours) }} h
                </span>
              </template>
            </el-table-column>
            <el-table-column label="SLA状态" width="100" align="center">
              <template #default="{ row }">
                <el-tag :type="slaStatusType(row.sla_status)" size="small">
                  {{ row.sla_status_name || slaStatusText(row.sla_status) }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column label="SLA截止" width="160">
              <template #default="{ row }"><span class="time-cell">{{ formatDateTime(row.sla_deadline) }}</span></template>
            </el-table-column>
            <el-table-column label="操作" width="80" align="center" fixed="right">
              <template #default="{ row }">
                <div class="table-actions">
                  <el-button
                    v-if="['warning', 'overdue'].includes(row.sla_status)"
                    link type="danger" size="small"
                    @click="handleEscalate(row)"
                  >升级</el-button>
                  <span v-else class="text-muted">-</span>
                </div>
              </template>
            </el-table-column>
          </el-table>

          <header class="card-title work-order__section-title">
            <h3 class="card-title__text">SLA 规则配置</h3>
          </header>
          <el-table :data="slaRules" class="app-table" empty-text="暂无SLA规则">
            <el-table-column label="优先级" width="100" align="center">
              <template #default="{ row }">
                <el-tag :type="priorityType(row.priority)" size="small">
                  {{ row.priority_name || priorityText(row.priority) }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column label="响应时限" width="100" align="right">
              <template #default="{ row }">{{ row.response_hours }} h</template>
            </el-table-column>
            <el-table-column label="预警阈值" width="100" align="right">
              <template #default="{ row }">{{ row.warning_threshold }}</template>
            </el-table-column>
            <el-table-column label="升级倍数" width="100" align="right">
              <template #default="{ row }">{{ row.escalate_multiplier }}×</template>
            </el-table-column>
            <el-table-column prop="escalate_target" label="升级对象" width="130" />
            <el-table-column prop="desc" label="说明" min-width="220" show-overflow-tooltip />
          </el-table>
        </el-tab-pane>
      </el-tabs>
    </section>

    <!-- ============ 工单新增/编辑对话框 ============ -->
    <el-dialog
      v-model="orderDialogVisible"
      :title="orderIsEdit ? '编辑工单' : '新增工单'"
      width="640px"
      destroy-on-close
    >
      <el-form ref="orderFormRef" :model="orderForm" :rules="orderRules" label-width="100px">
        <el-form-item label="工单标题" prop="title">
          <el-input v-model="orderForm.title" placeholder="如 城北片区供水管压力异常" />
        </el-form-item>
        <el-form-item label="来源渠道" prop="channel">
          <el-select v-model="orderForm.channel" placeholder="选择渠道" style="width: 100%;">
            <el-option v-for="c in channelOptions" :key="c.key" :label="c.name" :value="c.key" />
          </el-select>
        </el-form-item>
        <el-form-item label="工单类别" prop="category">
          <el-select v-model="orderForm.category" placeholder="选择类别" style="width: 100%;">
            <el-option v-for="c in categoryOptions" :key="c.key" :label="c.name" :value="c.key" />
          </el-select>
        </el-form-item>
        <el-form-item label="优先级" prop="priority">
          <el-select v-model="orderForm.priority" placeholder="选择优先级" style="width: 100%;">
            <el-option v-for="(label, key) in PRIORITY_TEXT" :key="key" :label="label" :value="key" />
          </el-select>
        </el-form-item>
        <el-form-item label="事发位置" prop="location">
          <el-input v-model="orderForm.location" placeholder="如 城北片区 XX 路段" />
        </el-form-item>
        <el-form-item label="问题描述" prop="description">
          <el-input v-model="orderForm.description" type="textarea" :rows="3" placeholder="详细描述问题现象" />
        </el-form-item>
        <el-form-item label="上报人" prop="reporter">
          <el-input v-model="orderForm.reporter" placeholder="上报人姓名或单位" />
        </el-form-item>
        <el-form-item label="SLA时限(h)" prop="sla_hours">
          <el-input-number v-model="orderForm.sla_hours" :min="1" :max="720" :step="1" style="width: 100%;" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="orderDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="orderSubmitting" @click="submitOrder">确定</el-button>
      </template>
    </el-dialog>

    <!-- ============ 工单详情对话框 ============ -->
    <el-dialog v-model="orderDetailVisible" title="工单详情" width="760px" destroy-on-close>
      <div v-loading="orderDetailLoading">
        <el-descriptions :column="3" border size="small">
          <el-descriptions-item label="工单编号">
            <span class="code-cell">{{ orderDetailData.order_id }}</span>
          </el-descriptions-item>
          <el-descriptions-item label="标题" :span="2">{{ orderDetailData.title }}</el-descriptions-item>
          <el-descriptions-item label="来源渠道">{{ channelName(orderDetailData.channel) }}</el-descriptions-item>
          <el-descriptions-item label="类别">{{ categoryName(orderDetailData.category) }}</el-descriptions-item>
          <el-descriptions-item label="优先级">
            <el-tag :type="priorityType(orderDetailData.priority)" size="small">
              {{ priorityText(orderDetailData.priority) }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="状态">
            <el-tag :type="statusType(orderDetailData.status)" size="small">
              {{ statusText(orderDetailData.status) }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="是否升级">
            <el-tag :type="orderDetailData.escalated ? 'danger' : 'info'" size="small">
              {{ orderDetailData.escalated ? '已升级' : '未升级' }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="处理人">{{ orderDetailData.assignee || '-' }}</el-descriptions-item>
          <el-descriptions-item label="位置" :span="2">{{ orderDetailData.location || '-' }}</el-descriptions-item>
          <el-descriptions-item label="上报人">{{ orderDetailData.reporter || '-' }}</el-descriptions-item>
          <el-descriptions-item label="创建时间">{{ formatDateTime(orderDetailData.created_at) }}</el-descriptions-item>
          <el-descriptions-item label="SLA时限">{{ orderDetailData.sla_hours ?? '-' }} h</el-descriptions-item>
          <el-descriptions-item label="SLA截止">{{ formatDateTime(orderDetailData.sla_deadline) }}</el-descriptions-item>
          <el-descriptions-item label="解决时间">{{ formatDateTime(orderDetailData.resolved_at) }}</el-descriptions-item>
          <el-descriptions-item label="所需技能">{{ orderDetailData.required_skill || '-' }}</el-descriptions-item>
          <el-descriptions-item label="满意度评分" :span="2">
            <el-rate
              v-if="orderDetailData.rating"
              :model-value="Number(orderDetailData.rating)"
              disabled
              size="small"
            />
            <span v-else>-</span>
          </el-descriptions-item>
          <el-descriptions-item label="问题描述" :span="3">{{ orderDetailData.description || '-' }}</el-descriptions-item>
        </el-descriptions>

        <header class="card-title work-order__section-title">
          <h3 class="card-title__text">流程跟踪</h3>
        </header>
        <el-timeline v-if="detailTimeline.length" class="work-order__timeline">
          <el-timeline-item
            v-for="(p, i) in detailTimeline"
            :key="i"
            :timestamp="formatDateTime(p.at)"
            placement="top"
            :type="i === detailTimeline.length - 1 ? 'primary' : ''"
          >
            <div class="timeline-step">
              <strong>{{ p.step_name || p.step }}</strong>
              <span v-if="p.operator" class="timeline-step__op">操作人：{{ p.operator }}</span>
              <p v-if="p.note" class="timeline-step__note">{{ p.note }}</p>
            </div>
          </el-timeline-item>
        </el-timeline>
        <el-empty v-else description="暂无流程记录" :image-size="60" />
      </div>
      <template #footer>
        <el-button type="primary" @click="orderDetailVisible = false">关闭</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Search, Upload, Download } from '@element-plus/icons-vue'
import * as XLSX from 'xlsx'
import { saveAs } from 'file-saver'
import PageHeader from '@/components/PageHeader.vue'
import StatCard from '@/components/StatCard.vue'
import { formatDateTime } from '@/utils/format'
import {
  getOverview,
  getOrders, getChannels, createOrder, deleteOrder, getOrderDetail,
  getDispatchRecommend, assignOrder,
  getStaff, getStaffWorkload,
  getProcess, advanceProcess,
  getSlaRules, getSlaMonitor, escalateOrder
} from '@/api/workOrder'

// ===================== 常量映射 =====================
const PRIORITY_TEXT = { urgent: '紧急', high: '高', medium: '中', low: '低' }
const PRIORITY_TYPE = { urgent: 'danger', high: 'warning', medium: 'info', low: 'success' }
const STATUS_TEXT = {
  pending: '待派单',
  assigned: '已派单',
  accepted: '已接单',
  onsite: '到场处理',
  resolved: '已解决',
  verified: '已核实',
  closed: '已关闭',
  escalated: '已升级'
}
const STATUS_TYPE = {
  pending: 'info',
  assigned: 'warning',
  accepted: 'primary',
  onsite: 'warning',
  resolved: 'success',
  verified: 'success',
  closed: 'info',
  escalated: 'danger'
}
const CHANNEL_FALLBACK = { alarm: '报警触发', patrol: '巡检上报', user: '用户报修', government: '政府督办' }
const CATEGORY_FALLBACK = {
  electrical: '电气',
  pipeline: '管道',
  instrument: '仪表',
  hvac: '暖通',
  civil: '土建',
  it: '信息化',
  fire: '消防'
}
const STAFF_STATUS_TEXT = { idle: '空闲', busy: '忙碌', off: '离线' }
const STAFF_STATUS_TYPE = { idle: 'success', busy: 'warning', off: 'info' }
const SLA_STATUS_TEXT = { normal: '正常', warning: '预警', overdue: '逾期', escalated: '已升级' }
const SLA_STATUS_TYPE = { normal: 'success', warning: 'warning', overdue: 'danger', escalated: 'danger' }

// Excel 导入表头映射（支持中英文列名）
const ORDER_IMPORT_MAP = {
  title: 'title', '标题': 'title', '工单标题': 'title',
  channel: 'channel', '渠道': 'channel', '来源渠道': 'channel',
  category: 'category', '类别': 'category', '工单类别': 'category',
  priority: 'priority', '优先级': 'priority',
  location: 'location', '位置': 'location', '事发位置': 'location',
  description: 'description', '描述': 'description', '问题描述': 'description',
  reporter: 'reporter', '上报人': 'reporter', '报修人': 'reporter',
  sla_hours: 'sla_hours', 'sla时限': 'sla_hours', 'SLA时限': 'sla_hours', 'sla小时': 'sla_hours'
}

// ===================== 页面状态 =====================
const activeTab = ref('orders')
const overview = ref(null)
const channelsConfig = ref(null)

// 工单列表
const allOrders = ref([])
const ordersLoading = ref(false)
const orderQuery = ref({ keyword: '', priority: '', status: '', channel: '', category: '' })
const orderPage = ref(1)
const orderPageSize = ref(10)

// 智能派单
const dispatchOrderId = ref('')
const dispatchLoading = ref(false)
const dispatchResult = ref(null)

// 运维人员
const staffList = ref([])
const workloadList = ref([])
const staffLoading = ref(false)

// SLA
const slaMonitor = ref(null)
const slaRules = ref([])
const slaLoading = ref(false)

// 导入
const importing = ref(false)

// ===================== 头部按钮可见性 =====================
const canAdd = computed(() => activeTab.value === 'orders')
const canImport = computed(() => activeTab.value === 'orders')
const canExport = computed(() => ['orders', 'staff', 'sla'].includes(activeTab.value))

// ===================== 字典/格式化 =====================
const channelOptions = computed(() =>
  channelsConfig.value?.channels?.length
    ? channelsConfig.value.channels
    : Object.entries(CHANNEL_FALLBACK).map(([key, name]) => ({ key, name }))
)
const categoryOptions = computed(() =>
  channelsConfig.value?.categories?.length
    ? channelsConfig.value.categories
    : Object.entries(CATEGORY_FALLBACK).map(([key, name]) => ({ key, name }))
)
const channelName = (key) =>
  channelOptions.value.find(c => c.key === key)?.name || CHANNEL_FALLBACK[key] || key || '-'
const categoryName = (key) =>
  categoryOptions.value.find(c => c.key === key)?.name || CATEGORY_FALLBACK[key] || key || '-'
const priorityText = (p) => PRIORITY_TEXT[p] || p || '-'
const priorityType = (p) => PRIORITY_TYPE[p] || 'info'
const statusText = (s) => STATUS_TEXT[s] || s || '-'
const statusType = (s) => STATUS_TYPE[s] || 'info'
const staffStatusText = (s) => STAFF_STATUS_TEXT[s] || s || '-'
const staffStatusType = (s) => STAFF_STATUS_TYPE[s] || 'info'
const slaStatusText = (s) => SLA_STATUS_TEXT[s] || s || '-'
const slaStatusType = (s) => SLA_STATUS_TYPE[s] || 'info'
const skillList = (s) => (Array.isArray(s) ? s : String(s || '').split(',').map(x => x.trim()).filter(Boolean))
const fmtRating = (v) => (v == null ? '-' : Number(v).toFixed(1))
const fmtScore = (v) => (v == null ? '-' : Number(v).toFixed(1))
const fmtHours = (v) => (v == null ? '-' : Number(v).toFixed(1))
const scoreBarPct = (v) => `${Math.min(100, Math.max(2, Math.round(Number(v) || 0)))}%`
const today = () => new Date().toISOString().slice(0, 10)

// ===================== 数据加载 =====================
const loadOverview = async () => {
  try {
    overview.value = await getOverview()
  } catch (e) {
    console.error('加载工单总览失败:', e)
  }
}

const loadChannelsConfig = async () => {
  try {
    channelsConfig.value = await getChannels()
  } catch (e) {
    console.error('加载渠道配置失败:', e)
  }
}

const loadOrders = async () => {
  ordersLoading.value = true
  try {
    const res = await getOrders({ page: 1, page_size: 1000 })
    allOrders.value = res?.orders || (Array.isArray(res) ? res : [])
  } catch (e) {
    ElMessage.error('加载工单列表失败')
    console.error('加载工单列表失败:', e)
  } finally {
    ordersLoading.value = false
  }
}

const loadStaff = async () => {
  staffLoading.value = true
  try {
    const [s, w] = await Promise.all([
      getStaff({ page: 1, page_size: 200 }),
      getStaffWorkload().catch(() => null)
    ])
    staffList.value = s?.staff || (Array.isArray(s) ? s : [])
    workloadList.value = w?.workload || []
  } catch (e) {
    ElMessage.error('加载运维人员失败')
    console.error('加载运维人员失败:', e)
  } finally {
    staffLoading.value = false
  }
}

const loadSla = async () => {
  slaLoading.value = true
  try {
    const [m, r] = await Promise.all([
      getSlaMonitor(),
      getSlaRules().catch(() => null)
    ])
    slaMonitor.value = m
    slaRules.value = r?.rules || []
  } catch (e) {
    ElMessage.error('加载SLA监控失败')
    console.error('加载SLA监控失败:', e)
  } finally {
    slaLoading.value = false
  }
}

const handleTabChange = (name) => {
  if (name === 'orders') loadOrders()
  else if (name === 'dispatch' && !allOrders.value.length) loadOrders()
  else if (name === 'staff') loadStaff()
  else if (name === 'sla') loadSla()
}

const refreshCurrentTab = () => {
  loadOverview()
  if (activeTab.value === 'dispatch') {
    loadOrders()
    if (dispatchOrderId.value) loadRecommend()
    return
  }
  handleTabChange(activeTab.value)
}

// ===================== 工单列表：筛选 + 前端分页 =====================
const filteredOrders = computed(() =>
  allOrders.value.filter(o => {
    const q = orderQuery.value
    if (q.priority && o.priority !== q.priority) return false
    if (q.status && o.status !== q.status) return false
    if (q.channel && o.channel !== q.channel) return false
    if (q.category && o.category !== q.category) return false
    if (q.keyword) {
      const kw = q.keyword.trim().toLowerCase()
      const text = `${o.order_id || ''} ${o.title || ''} ${o.location || ''} ${o.reporter || ''}`.toLowerCase()
      if (!text.includes(kw)) return false
    }
    return true
  })
)

const pagedOrders = computed(() => {
  const start = (orderPage.value - 1) * orderPageSize.value
  return filteredOrders.value.slice(start, start + orderPageSize.value)
})

const resetOrderQuery = () => {
  orderQuery.value = { keyword: '', priority: '', status: '', channel: '', category: '' }
  orderPage.value = 1
}

// ===================== 工单新增/编辑 =====================
const orderDialogVisible = ref(false)
const orderIsEdit = ref(false)
const orderSubmitting = ref(false)
const orderFormRef = ref(null)
const editingOrderId = ref(null)

const defaultOrderForm = () => ({
  title: '',
  channel: '',
  category: '',
  priority: 'medium',
  location: '',
  description: '',
  reporter: '',
  sla_hours: 24
})
const orderForm = ref(defaultOrderForm())

const orderRules = {
  title: [{ required: true, message: '请输入工单标题', trigger: 'blur' }],
  channel: [{ required: true, message: '请选择来源渠道', trigger: 'change' }],
  category: [{ required: true, message: '请选择工单类别', trigger: 'change' }],
  priority: [{ required: true, message: '请选择优先级', trigger: 'change' }]
}

const openOrderDialog = (row) => {
  if (row) {
    orderIsEdit.value = true
    editingOrderId.value = row.order_id
    orderForm.value = {
      title: row.title ?? '',
      channel: row.channel ?? '',
      category: row.category ?? '',
      priority: row.priority ?? 'medium',
      location: row.location ?? '',
      description: row.description ?? '',
      reporter: row.reporter ?? '',
      sla_hours: Number(row.sla_hours) || 24
    }
  } else {
    orderIsEdit.value = false
    editingOrderId.value = null
    orderForm.value = defaultOrderForm()
  }
  orderDialogVisible.value = true
}

const submitOrder = async () => {
  if (!orderFormRef.value) return
  try {
    await orderFormRef.value.validate()
  } catch {
    return
  }
  orderSubmitting.value = true
  try {
    const body = { ...orderForm.value }
    if (orderIsEdit.value) body.order_id = editingOrderId.value
    await createOrder(body)
    ElMessage.success(orderIsEdit.value ? '保存成功' : '创建成功')
    orderDialogVisible.value = false
    loadOrders()
    loadOverview()
  } catch (e) {
    ElMessage.error(orderIsEdit.value ? '保存失败' : '创建失败')
    console.error('提交工单失败:', e)
  } finally {
    orderSubmitting.value = false
  }
}

// ===================== 工单详情 =====================
const orderDetailVisible = ref(false)
const orderDetailLoading = ref(false)
const orderDetail = ref(null)
const orderProcess = ref(null)

const orderDetailData = computed(() => orderDetail.value || {})
const detailTimeline = computed(() => {
  const p = orderDetail.value?.process
  if (Array.isArray(p) && p.length) return p
  return orderProcess.value?.timeline || []
})

const openOrderDetail = async (row) => {
  orderDetailVisible.value = true
  orderDetailLoading.value = true
  orderDetail.value = row
  orderProcess.value = null
  try {
    const d = await getOrderDetail(row.order_id)
    orderDetail.value = d || row
    if (!orderDetail.value?.process?.length) {
      orderProcess.value = await getProcess(row.order_id).catch(() => null)
    }
  } catch (e) {
    ElMessage.error('加载工单详情失败')
    console.error('加载工单详情失败:', e)
  } finally {
    orderDetailLoading.value = false
  }
}

// ===================== 流程推进 / 删除 =====================
const handleAdvance = async (row) => {
  let proc = null
  try {
    proc = await getProcess(row.order_id)
  } catch (e) {
    ElMessage.error('获取流程信息失败')
    console.error(e)
    return
  }
  const steps = proc?.steps || []
  const idx = proc?.current_step_index ?? -1
  const next = steps[idx + 1]
  if (!next) {
    ElMessage.info('该工单已处于最终流程节点')
    return
  }
  let note = ''
  try {
    const { value } = await ElMessageBox.prompt(
      `当前节点：${steps[idx]?.name || '-'}，将推进到「${next.name}」`,
      '推进流程',
      {
        confirmButtonText: '推进',
        cancelButtonText: '取消',
        inputPlaceholder: '备注（可选）'
      }
    )
    note = value || ''
  } catch {
    return
  }
  try {
    await advanceProcess({ order_id: row.order_id, step: next.code, note })
    ElMessage.success('流程已推进')
    loadOrders()
    loadOverview()
  } catch (e) {
    ElMessage.error('推进流程失败')
    console.error(e)
  }
}

const handleDeleteOrder = (row) => {
  ElMessageBox.confirm(`确认删除工单「${row.title}」？删除后不可恢复。`, '删除确认', {
    confirmButtonText: '删除',
    cancelButtonText: '取消',
    type: 'warning'
  })
    .then(async () => {
      try {
        await deleteOrder(row.order_id)
        ElMessage.success('删除成功')
        loadOrders()
        loadOverview()
      } catch (e) {
        ElMessage.error('删除失败')
        console.error(e)
      }
    })
    .catch(() => {})
}

// ===================== 智能派单 =====================
const recommendationText = computed(() => {
  const r = dispatchResult.value?.recommendation
  if (!r) return '请从下方候选人中择优派发'
  if (typeof r === 'string') return r
  return r.reason || r.message || r.name || JSON.stringify(r)
})

const loadRecommend = async () => {
  if (!dispatchOrderId.value) {
    ElMessage.warning('请先选择工单')
    return
  }
  dispatchLoading.value = true
  try {
    dispatchResult.value = await getDispatchRecommend({ order_id: dispatchOrderId.value })
  } catch (e) {
    ElMessage.error('获取派单推荐失败')
    console.error('获取派单推荐失败:', e)
  } finally {
    dispatchLoading.value = false
  }
}

const handleAssign = (staff) => {
  ElMessageBox.confirm(`确认将工单派发给「${staff.name}」？`, '派单确认', {
    confirmButtonText: '派单',
    cancelButtonText: '取消',
    type: 'warning'
  })
    .then(async () => {
      try {
        await assignOrder({
          order_id: dispatchResult.value?.order_id || dispatchOrderId.value,
          staff_id: staff.staff_id
        })
        ElMessage.success('派单成功')
        loadOrders()
        loadOverview()
        loadRecommend()
      } catch (e) {
        ElMessage.error('派单失败')
        console.error(e)
      }
    })
    .catch(() => {})
}

// ===================== SLA 升级 =====================
const handleEscalate = (row) => {
  ElMessageBox.confirm(`确认升级工单「${row.title}」？升级后将通知上级督办。`, '升级确认', {
    confirmButtonText: '升级',
    cancelButtonText: '取消',
    type: 'warning'
  })
    .then(async () => {
      try {
        await escalateOrder(row.order_id)
        ElMessage.success('工单已升级')
        loadSla()
        loadOrders()
        loadOverview()
      } catch (e) {
        ElMessage.error('升级失败')
        console.error(e)
      }
    })
    .catch(() => {})
}

// ===================== SLA 数据 =====================
const slaSummary = computed(() => slaMonitor.value?.summary || {})
const slaItems = computed(() => slaMonitor.value?.items || [])

// ===================== Excel 导出 =====================
const exportExcel = (rows, filename) => {
  if (!rows.length) {
    ElMessage.warning('暂无可导出的数据')
    return
  }
  const wb = XLSX.utils.book_new()
  XLSX.utils.book_append_sheet(wb, XLSX.utils.json_to_sheet(rows), 'Sheet1')
  const wbout = XLSX.write(wb, { bookType: 'xlsx', type: 'array' })
  saveAs(new Blob([wbout], { type: 'application/octet-stream' }), filename)
  ElMessage.success('导出成功')
}

const handleExport = () => {
  try {
    if (activeTab.value === 'orders') {
      const rows = filteredOrders.value.map(o => ({
        工单编号: o.order_id,
        标题: o.title,
        渠道: channelName(o.channel),
        类别: categoryName(o.category),
        优先级: priorityText(o.priority),
        状态: statusText(o.status),
        位置: o.location,
        上报人: o.reporter,
        处理人: o.assignee || '',
        创建时间: formatDateTime(o.created_at),
        SLA时限h: o.sla_hours,
        SLA截止: formatDateTime(o.sla_deadline),
        评分: o.rating ?? '',
        是否升级: o.escalated ? '是' : '否',
        问题描述: o.description
      }))
      exportExcel(rows, `工单列表_${today()}.xlsx`)
    } else if (activeTab.value === 'staff') {
      const rows = staffList.value.map(s => ({
        编号: s.staff_id,
        姓名: s.name,
        技能: skillList(s.skills).join(','),
        状态: staffStatusText(s.status),
        当前位置: s.location,
        联系电话: s.phone,
        完成工单: s.completed_orders,
        平均评分: s.avg_rating
      }))
      exportExcel(rows, `运维人员_${today()}.xlsx`)
    } else if (activeTab.value === 'sla') {
      const rows = slaItems.value.map(i => ({
        工单编号: i.order_id,
        标题: i.title,
        优先级: i.priority_name || priorityText(i.priority),
        状态: i.status_name || statusText(i.status),
        处理人: i.assignee || '',
        已耗时h: i.elapsed_hours,
        SLA时限h: i.sla_hours,
        剩余h: i.remaining_hours,
        SLA状态: i.sla_status_name || slaStatusText(i.sla_status),
        SLA截止: formatDateTime(i.sla_deadline)
      }))
      exportExcel(rows, `SLA监控_${today()}.xlsx`)
    }
  } catch (e) {
    ElMessage.error('导出失败')
    console.error('导出失败:', e)
  }
}

// ===================== Excel 导入 =====================
const mapImportRow = (row, dict) => {
  const out = {}
  for (const [k, v] of Object.entries(row)) {
    const raw = String(k).trim()
    const key = dict[raw] || dict[raw.toLowerCase()]
    if (key) out[key] = v
  }
  return out
}

// 渠道/类别解析：支持 key 或中文名称
const lookupKey = (options, val) => {
  const v = String(val ?? '').trim()
  if (!v) return ''
  const hit = options.find(i => i.key === v || i.name === v)
  return hit ? hit.key : v
}

// 优先级解析：支持 urgent/high/medium/low 或 紧急/高/中/低
const lookupPriority = (val) => {
  const v = String(val ?? '').trim()
  if (PRIORITY_TEXT[v]) return v
  const hit = Object.entries(PRIORITY_TEXT).find(([, name]) => name === v)
  return hit ? hit[0] : 'medium'
}

const toOrderBody = (r) => {
  const body = {
    title: String(r.title ?? '').trim(),
    channel: lookupKey(channelOptions.value, r.channel),
    category: lookupKey(categoryOptions.value, r.category),
    priority: lookupPriority(r.priority),
    location: String(r.location ?? ''),
    description: String(r.description ?? ''),
    reporter: String(r.reporter ?? '')
  }
  if (r.sla_hours !== '' && r.sla_hours != null) body.sla_hours = Number(r.sla_hours)
  return body
}

const handleImport = ({ file }) => {
  const reader = new FileReader()
  reader.onload = async (e) => {
    try {
      const wb = XLSX.read(new Uint8Array(e.target.result), { type: 'array', cellDates: true })
      const ws = wb.Sheets[wb.SheetNames[0]]
      const rows = XLSX.utils.sheet_to_json(ws, { defval: '' })
      if (!rows.length) {
        ElMessage.warning('导入文件中没有数据')
        return
      }
      const bodies = rows
        .map(r => toOrderBody(mapImportRow(r, ORDER_IMPORT_MAP)))
        .filter(b => !!b.title)
      if (!bodies.length) {
        ElMessage.warning('未识别到有效数据行，请确认表头包含"标题/title"列')
        return
      }
      importing.value = true
      let ok = 0
      let fail = 0
      for (const body of bodies) {
        try {
          await createOrder(body)
          ok += 1
        } catch {
          fail += 1
        }
      }
      ElMessage.success(`导入完成：成功 ${ok} 条${fail ? `，失败 ${fail} 条` : ''}`)
      loadOrders()
      loadOverview()
    } catch (err) {
      ElMessage.error('导入失败：无法解析文件，请使用 .xlsx / .xls 格式')
      console.error('导入失败:', err)
    } finally {
      importing.value = false
    }
  }
  reader.readAsArrayBuffer(file)
}

// ===================== 初始化 =====================
onMounted(() => {
  loadChannelsConfig()
  loadOverview()
  loadOrders()
})
</script>

<style scoped>
.work-order__stats {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
  margin-bottom: 16px;
}
.work-order__main {
  padding: 16px 24px 24px;
}
.work-order__filter {
  margin-bottom: 16px;
}
.work-order__filter-item {
  width: 160px;
}
.work-order__dispatch-select {
  width: 320px;
}
.work-order__pagination {
  display: flex;
  justify-content: flex-end;
  margin-top: 16px;
}
.work-order__upload {
  display: inline-flex;
}
.work-order__section-title {
  margin-top: 24px;
}
.work-order__recommend-alert {
  margin-bottom: 16px;
  border-radius: var(--app-radius-control);
}
.work-order__dispatch-meta {
  margin-bottom: 16px;
}
.work-order__timeline {
  padding-left: 4px;
}

/* 表格内单元样式 */
.code-cell {
  font-family: 'Courier New', monospace;
  font-size: 13px;
  color: var(--app-primary);
}
.num-cell {
  font-weight: 600;
  color: var(--app-text-1);
  font-variant-numeric: tabular-nums;
}
.time-cell {
  color: var(--app-text-3);
  font-size: 13px;
}
.text-muted {
  color: var(--app-text-4);
}
.esc-tag {
  margin-left: 6px;
}
.skill-tag {
  margin: 2px 6px 2px 0;
}
.rank-cell {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 24px;
  height: 24px;
  border-radius: 50%;
  font-size: 13px;
  font-weight: 600;
  color: var(--app-text-3);
  background-color: var(--app-hover);
}
.rank-cell--top {
  color: #fff;
  background-color: var(--app-primary);
}

/* 综合得分单元 */
.score-cell {
  display: flex;
  align-items: center;
  gap: 8px;
}
.score-cell__value {
  font-weight: 600;
  color: var(--app-text-1);
  font-variant-numeric: tabular-nums;
  min-width: 34px;
  text-align: right;
}
.score-bar {
  flex: 1;
  height: 6px;
  border-radius: 3px;
  background-color: var(--app-hover);
  overflow: hidden;
}
.score-bar__fill {
  height: 100%;
  border-radius: 3px;
  background: linear-gradient(90deg, rgba(0, 113, 227, 0.4), var(--app-primary));
  transition: width 0.4s cubic-bezier(0.4, 0, 0.2, 1);
}

/* 得分明细弹层 */
.score-breakdown__row {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  padding: 4px 0;
  font-size: 13px;
  border-bottom: 1px solid var(--app-border);
}
.score-breakdown__row:last-child {
  border-bottom: none;
}
.score-breakdown__key {
  color: var(--app-text-3);
}
.score-breakdown__val {
  color: var(--app-text-1);
  font-weight: 600;
}
.score-breakdown__empty {
  color: var(--app-text-4);
  font-size: 13px;
}

/* 负载徽标 */
.workload-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 28px;
  height: 24px;
  padding: 0 8px;
  border-radius: var(--app-radius-tag);
  background-color: var(--app-hover);
  color: var(--app-text-2);
  font-weight: 600;
  font-size: 13px;
}
.workload-badge--busy {
  background-color: rgba(255, 149, 0, 0.12);
  color: #FF9500;
}

/* SLA 汇总块 */
.sla-summary {
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  gap: 16px;
}
.sla-tile {
  background: rgba(255, 255, 255, 0.6);
  border: 1px solid var(--app-border);
  border-radius: var(--app-radius-control);
  padding: 16px 20px;
  text-align: center;
}
.sla-tile__value {
  font-size: 30px;
  font-weight: 600;
  line-height: 1.2;
  color: var(--app-text-1);
  font-variant-numeric: tabular-nums;
}
.sla-tile__label {
  margin-top: 4px;
  font-size: 13px;
  color: var(--app-text-3);
}
.sla-tile--normal .sla-tile__value { color: #34C759; }
.sla-tile--warning .sla-tile__value { color: #FF9500; }
.sla-tile--overdue .sla-tile__value { color: #FF3B30; }
.sla-tile--escalated .sla-tile__value { color: #AF52DE; }
.sla-tile--total .sla-tile__value { color: var(--app-primary); }

/* 剩余时间 */
.remaining--ok {
  color: #34C759;
  font-weight: 600;
}
.remaining--over {
  color: #FF3B30;
  font-weight: 600;
}

/* 流程时间线 */
.timeline-step strong {
  color: var(--app-text-1);
  font-size: 14px;
}
.timeline-step__op {
  margin-left: 10px;
  font-size: 13px;
  color: var(--app-text-3);
}
.timeline-step__note {
  margin: 4px 0 0 0;
  font-size: 13px;
  color: var(--app-text-2);
}

@media (max-width: 1024px) {
  .work-order__stats { grid-template-columns: repeat(2, 1fr); }
  .sla-summary { grid-template-columns: repeat(2, 1fr); }
}
</style>
