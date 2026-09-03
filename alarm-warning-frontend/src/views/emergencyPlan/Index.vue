<template>
  <div class="emergency-plan">
    <PageHeader title="应急预案" subtitle="Emergency Plan">
      <el-button @click="refreshAll">
        <el-icon><Refresh /></el-icon> 刷新
      </el-button>
    </PageHeader>

    <!-- 4 个统计卡片 -->
    <div class="emergency-plan__stats">
      <StatCard label="预案总数" :value="overview.total_plans ?? 0" icon="Notebook" color="#0071E3" />
      <StatCard label="活跃预案" :value="overview.active_plans ?? 0" icon="CircleCheck" color="#34C759" />
      <StatCard label="今日匹配" :value="overview.today_match_count ?? 0" icon="Aim" color="#FF9500" />
      <StatCard label="演练次数" :value="overview.today_drill_count ?? 0" icon="Flag" color="#FF3B30" />
    </div>

    <!-- 分模块标签页 -->
    <section class="app-card emergency-plan__tabs-card">
      <el-tabs v-model="activeTab">
        <!-- ============ Tab 1 预案管理 ============ -->
        <el-tab-pane label="预案管理" name="plans">
          <div class="filter-bar emergency-plan__filter">
            <el-input
              v-model="planQuery.keyword"
              placeholder="预案名称/编号"
              clearable
              class="emergency-plan__filter-item"
              @keyup.enter="loadPlans"
            />
            <el-select v-model="planQuery.category" placeholder="预案类别" clearable class="emergency-plan__filter-item" @change="loadPlans">
              <el-option v-for="c in categories" :key="c.code" :label="c.name" :value="c.code" />
            </el-select>
            <el-select v-model="planQuery.status" placeholder="状态" clearable class="emergency-plan__filter-item" @change="loadPlans">
              <el-option label="全部" value="" />
              <el-option label="启用中" value="active" />
              <el-option label="草稿" value="draft" />
              <el-option label="已废弃" value="deprecated" />
            </el-select>
            <el-button type="primary" @click="loadPlans">
              <el-icon><Search /></el-icon> 查询
            </el-button>
            <el-button @click="resetPlanQuery">重置</el-button>
            <el-button type="primary" plain @click="openPlanDialog(null)">
              <el-icon><Plus /></el-icon> 新增预案
            </el-button>
            <el-upload
              class="emergency-plan__upload"
              accept=".xlsx,.xls"
              :show-file-list="false"
              :http-request="importPlans"
            >
              <el-button plain>
                <el-icon><Upload /></el-icon> 导入Excel
              </el-button>
            </el-upload>
            <el-button class="emergency-plan__export-btn" @click="exportPlans">
              <el-icon><Download /></el-icon> 导出Excel
            </el-button>
          </div>

          <el-table :data="planPaged" v-loading="planLoading" class="app-table">
            <el-table-column prop="plan_id" label="预案编号" min-width="130">
              <template #default="{ row }"><span class="code-cell">{{ row.plan_id }}</span></template>
            </el-table-column>
            <el-table-column prop="plan_name" label="预案名称" min-width="200" show-overflow-tooltip />
            <el-table-column label="类别" width="110" align="center">
              <template #default="{ row }">{{ categoryName(row.category) }}</template>
            </el-table-column>
            <el-table-column label="适用级别" width="100" align="center">
              <template #default="{ row }">L{{ row.level_min }} ~ L{{ row.level_max }}</template>
            </el-table-column>
            <el-table-column prop="priority" label="优先级" width="80" align="center">
              <template #default="{ row }"><span class="priority-value">{{ row.priority }}</span></template>
            </el-table-column>
            <el-table-column label="状态" width="90" align="center">
              <template #default="{ row }">
                <el-tag :type="planStatusType(row.status)" size="small">{{ planStatusText(row.status) }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="commander" label="指挥长" width="110" show-overflow-tooltip />
            <el-table-column label="节点数" width="80" align="center">
              <template #default="{ row }">{{ (row.flow_nodes || []).length }}</template>
            </el-table-column>
            <el-table-column label="更新时间" width="170">
              <template #default="{ row }"><span class="time-cell">{{ row.updated_at }}</span></template>
            </el-table-column>
            <el-table-column label="操作" width="220" align="center" fixed="right">
              <template #default="{ row }">
                <div class="table-actions">
                  <el-button link type="primary" size="small" @click="openPlanDetail(row)">详情</el-button>
                  <el-button link type="primary" size="small" @click="openPlanDialog(row)">编辑</el-button>
                  <el-button link type="warning" size="small" @click="handleStatusChange(row)">
                    {{ row.status === 'active' ? '停用' : '启用' }}
                  </el-button>
                  <el-button link type="danger" size="small" @click="handlePlanDelete(row)">删除</el-button>
                </div>
              </template>
            </el-table-column>
          </el-table>

          <div class="emergency-plan__pagination">
            <el-pagination
              v-model:current-page="planPage"
              v-model:page-size="planSize"
              :total="plans.length"
              :page-sizes="[10, 20, 50]"
              layout="total, sizes, prev, pager, next"
            />
          </div>
        </el-tab-pane>

        <!-- ============ Tab 2 智能匹配 ============ -->
        <el-tab-pane label="智能匹配" name="match">
          <div class="emergency-plan__match-grid">
            <!-- 手动匹配 -->
            <div class="emergency-plan__match-panel">
              <header class="card-title">
                <h3 class="card-title__text">手动匹配</h3>
              </header>
              <div class="filter-bar emergency-plan__filter">
                <el-select v-model="matchForm.category" placeholder="预案类别" clearable class="emergency-plan__filter-item">
                  <el-option v-for="c in categories" :key="c.code" :label="c.name" :value="c.code" />
                </el-select>
                <el-select v-model="matchForm.level" placeholder="事件级别" class="emergency-plan__filter-item">
                  <el-option label="Ⅰ级（严重）" :value="2" />
                  <el-option label="Ⅱ级（预警）" :value="1" />
                </el-select>
                <el-select v-model="matchForm.cabin" placeholder="舱室" clearable class="emergency-plan__filter-item">
                  <el-option label="电力舱" value="EL" />
                  <el-option label="燃气舱" value="GS" />
                  <el-option label="水信舱" value="WS" />
                </el-select>
                <el-input v-model="matchForm.zone" placeholder="区段（如 Z03）" clearable class="emergency-plan__filter-item" />
                <el-button type="primary" :loading="matchLoading" @click="handleMatch">
                  <el-icon><Aim /></el-icon> 匹配预案
                </el-button>
              </div>

              <template v-if="matchResult">
                <el-alert
                  v-if="matchResult.fallback || !(matchResult.candidates || []).length"
                  :title="matchResult.fallback_message || '未匹配到适用预案，请转入人工决策'"
                  type="warning"
                  :closable="false"
                  class="emergency-plan__fallback"
                />
                <el-table v-else :data="matchResult.candidates" class="app-table">
                  <el-table-column prop="rank" label="排名" width="70" align="center" />
                  <el-table-column prop="plan_id" label="预案编号" width="130">
                    <template #default="{ row }"><span class="code-cell">{{ row.plan_id }}</span></template>
                  </el-table-column>
                  <el-table-column prop="plan_name" label="预案名称" min-width="180" show-overflow-tooltip />
                  <el-table-column label="匹配得分" width="160" align="center">
                    <template #default="{ row }">
                      <el-progress
                        :percentage="Math.min(100, Math.round(row.score))"
                        :stroke-width="8"
                        :color="scoreColor(row.score)"
                      />
                    </template>
                  </el-table-column>
                  <el-table-column label="匹配依据" min-width="220">
                    <template #default="{ row }">
                      <el-tag
                        v-for="(reason, i) in row.reasons || []"
                        :key="i"
                        size="small"
                        type="info"
                        class="reason-tag"
                      >{{ reason }}</el-tag>
                    </template>
                  </el-table-column>
                  <el-table-column label="操作" width="90" align="center">
                    <template #default="{ row }">
                      <el-button link type="primary" size="small" @click="viewMatchedPlan(row.plan_id)">详情</el-button>
                    </template>
                  </el-table-column>
                </el-table>
              </template>
              <el-empty v-else description="填写事件信息后点击「匹配预案」" :image-size="80" />
            </div>

            <!-- 实时匹配流 -->
            <div class="emergency-plan__match-panel">
              <header class="card-title">
                <h3 class="card-title__text">管廊告警实时匹配流</h3>
                <el-button size="small" @click="loadLiveMatches">刷新</el-button>
              </header>
              <el-table :data="liveMatches" v-loading="liveLoading" class="app-table" max-height="480" empty-text="暂无实时匹配">
                <el-table-column label="时间" width="165">
                  <template #default="{ row }"><span class="time-cell">{{ row.time }}</span></template>
                </el-table-column>
                <el-table-column label="告警" min-width="160" show-overflow-tooltip>
                  <template #default="{ row }">{{ row.alarm?.alarm_desc || row.alarm?.metric || row.alarm_id }}</template>
                </el-table-column>
                <el-table-column prop="category_name" label="类别" width="100" align="center" />
                <el-table-column label="最优预案" min-width="160" show-overflow-tooltip>
                  <template #default="{ row }">
                    <span v-if="row.best">{{ row.best.plan_name }}</span>
                    <span v-else class="text-muted">无候选</span>
                  </template>
                </el-table-column>
                <el-table-column label="得分" width="80" align="center">
                  <template #default="{ row }">
                    <span v-if="row.best" class="score-value" :style="{ color: scoreColor(row.best.score) }">{{ row.best.score }}</span>
                    <span v-else>-</span>
                  </template>
                </el-table-column>
                <el-table-column label="联动" width="80" align="center">
                  <template #default="{ row }">
                    <el-tag v-if="row.auto_acked" type="success" size="small">已确认</el-tag>
                    <el-tag v-else-if="row.fallback" type="warning" size="small">转人工</el-tag>
                    <span v-else>-</span>
                  </template>
                </el-table-column>
              </el-table>
            </div>
          </div>
        </el-tab-pane>

        <!-- ============ Tab 3 演练记录 ============ -->
        <el-tab-pane label="演练记录" name="activations">
          <div class="filter-bar emergency-plan__filter">
            <el-select v-model="actQuery.status" placeholder="状态" clearable class="emergency-plan__filter-item" @change="loadActivations">
              <el-option label="全部" value="" />
              <el-option label="进行中" value="running" />
              <el-option label="已完结" value="finished" />
            </el-select>
            <el-button type="primary" @click="loadActivations">
              <el-icon><Search /></el-icon> 查询
            </el-button>
            <el-button type="primary" plain @click="openDrillDialog">
              <el-icon><Plus /></el-icon> 发起演练
            </el-button>
            <el-button class="emergency-plan__export-btn" @click="exportActivations">
              <el-icon><Download /></el-icon> 导出Excel
            </el-button>
          </div>

          <el-table :data="actPaged" v-loading="actLoading" class="app-table">
            <el-table-column prop="activation_id" label="实例编号" min-width="120">
              <template #default="{ row }"><span class="code-cell">{{ row.activation_id }}</span></template>
            </el-table-column>
            <el-table-column prop="plan_name" label="预案名称" min-width="200" show-overflow-tooltip />
            <el-table-column prop="category_name" label="类别" width="100" align="center" />
            <el-table-column prop="trigger" label="触发方式" min-width="140" show-overflow-tooltip />
            <el-table-column label="状态" width="90" align="center">
              <template #default="{ row }">
                <el-tag :type="row.status === 'running' ? 'warning' : 'success'" size="small">
                  {{ row.status === 'running' ? '进行中' : '已完结' }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column label="激活时间" width="170">
              <template #default="{ row }"><span class="time-cell">{{ row.activated_at }}</span></template>
            </el-table-column>
            <el-table-column label="完结时间" width="170">
              <template #default="{ row }"><span class="time-cell">{{ row.finished_at || '-' }}</span></template>
            </el-table-column>
            <el-table-column label="操作" width="130" align="center" fixed="right">
              <template #default="{ row }">
                <div class="table-actions">
                  <el-button link type="primary" size="small" @click="openActDetail(row)">详情</el-button>
                  <el-button
                    v-if="row.status === 'running'"
                    link type="success" size="small"
                    @click="handleFinish(row)"
                  >完结</el-button>
                </div>
              </template>
            </el-table-column>
          </el-table>

          <div class="emergency-plan__pagination">
            <el-pagination
              v-model:current-page="actPage"
              v-model:page-size="actSize"
              :total="activations.length"
              :page-sizes="[10, 20, 50]"
              layout="total, sizes, prev, pager, next"
            />
          </div>
        </el-tab-pane>

        <!-- ============ Tab 4 预案分类 ============ -->
        <el-tab-pane label="预案分类" name="categories">
          <div class="filter-bar emergency-plan__filter">
            <span class="emergency-plan__category-tip">共 {{ categories.length }} 大类预案目录（只读）</span>
            <el-button class="emergency-plan__export-btn" @click="exportCategories">
              <el-icon><Download /></el-icon> 导出Excel
            </el-button>
          </div>
          <el-table :data="categories" v-loading="categoryLoading" class="app-table">
            <el-table-column prop="code" label="类别编码" width="120">
              <template #default="{ row }"><span class="code-cell">{{ row.code }}</span></template>
            </el-table-column>
            <el-table-column prop="name" label="类别名称" width="120" />
            <el-table-column prop="description" label="说明" min-width="260" show-overflow-tooltip />
            <el-table-column label="关联传感指标" min-width="160">
              <template #default="{ row }">
                <el-tag
                  v-for="m in row.sensor_metrics || []"
                  :key="m"
                  size="small"
                  type="info"
                  class="reason-tag"
                >{{ m }}</el-tag>
                <span v-if="!(row.sensor_metrics || []).length" class="text-muted">人工上报</span>
              </template>
            </el-table-column>
            <el-table-column prop="drill_alarm_code" label="演练告警码" width="110" align="center" />
            <el-table-column prop="plan_count" label="预案数" width="90" align="center" />
            <el-table-column prop="active_count" label="启用数" width="90" align="center" />
          </el-table>
        </el-tab-pane>
      </el-tabs>
    </section>

    <!-- ============ 预案新增/编辑对话框 ============ -->
    <el-dialog
      v-model="planDialogVisible"
      :title="planIsEdit ? '编辑预案' : '新增预案'"
      width="640px"
      destroy-on-close
      class="emergency-plan__dialog"
    >
      <el-form ref="planFormRef" :model="planForm" :rules="planRules" label-width="100px">
        <el-form-item label="预案名称" prop="plan_name">
          <el-input v-model="planForm.plan_name" placeholder="如 燃气泄漏Ⅰ级应急处置预案" />
        </el-form-item>
        <el-form-item label="预案类别" prop="category">
          <el-select v-model="planForm.category" placeholder="选择类别" style="width: 100%;">
            <el-option v-for="c in categories" :key="c.code" :label="`${c.name}（${c.code}）`" :value="c.code" />
          </el-select>
        </el-form-item>
        <el-form-item label="最低级别" prop="level_min">
          <el-input-number v-model="planForm.level_min" :min="1" :max="2" style="width: 100%;" />
        </el-form-item>
        <el-form-item label="最高级别" prop="level_max">
          <el-input-number v-model="planForm.level_max" :min="1" :max="2" style="width: 100%;" />
        </el-form-item>
        <el-form-item label="优先级" prop="priority">
          <el-input-number v-model="planForm.priority" :min="1" :max="10" style="width: 100%;" />
        </el-form-item>
        <el-form-item label="状态" prop="status">
          <el-select v-model="planForm.status" style="width: 100%;">
            <el-option label="启用中" value="active" />
            <el-option label="草稿" value="draft" />
            <el-option label="已废弃" value="deprecated" />
          </el-select>
        </el-form-item>
        <el-form-item label="适用舱室">
          <el-checkbox-group v-model="planForm.scope_cabins">
            <el-checkbox value="EL">电力舱</el-checkbox>
            <el-checkbox value="GS">燃气舱</el-checkbox>
            <el-checkbox value="WS">水信舱</el-checkbox>
          </el-checkbox-group>
        </el-form-item>
        <el-form-item label="处置目标">
          <el-input v-model="planForm.objective" type="textarea" :rows="2" placeholder="预案处置目标概述" />
        </el-form-item>
        <el-form-item label="指挥长">
          <el-input v-model="planForm.commander" placeholder="现场指挥长姓名/职务" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="planDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="planSubmitting" @click="handlePlanSubmit">确定</el-button>
      </template>
    </el-dialog>

    <!-- ============ 预案详情对话框（含流程节点管理） ============ -->
    <el-dialog v-model="planDetailVisible" title="预案详情" width="860px" class="emergency-plan__dialog">
      <template v-if="planDetail">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="预案编号">{{ planDetail.plan_id }}</el-descriptions-item>
          <el-descriptions-item label="预案名称">{{ planDetail.plan_name }}</el-descriptions-item>
          <el-descriptions-item label="类别">{{ categoryName(planDetail.category) }}</el-descriptions-item>
          <el-descriptions-item label="状态">
            <el-tag :type="planStatusType(planDetail.status)" size="small">{{ planStatusText(planDetail.status) }}</el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="适用级别">L{{ planDetail.level_min }} ~ L{{ planDetail.level_max }}</el-descriptions-item>
          <el-descriptions-item label="优先级">{{ planDetail.priority }}</el-descriptions-item>
          <el-descriptions-item label="适用舱室">{{ (planDetail.scope_cabins || []).join('、') }}</el-descriptions-item>
          <el-descriptions-item label="适用区段">{{ (planDetail.scope_zones || []).join('、') }}</el-descriptions-item>
          <el-descriptions-item label="指挥长">{{ planDetail.commander || '-' }}</el-descriptions-item>
          <el-descriptions-item label="标签">{{ (planDetail.tags || []).join('、') || '-' }}</el-descriptions-item>
          <el-descriptions-item label="处置目标" :span="2">{{ planDetail.objective || '-' }}</el-descriptions-item>
          <el-descriptions-item label="创建时间">{{ planDetail.created_at }}</el-descriptions-item>
          <el-descriptions-item label="更新时间">{{ planDetail.updated_at }}</el-descriptions-item>
        </el-descriptions>

        <div class="emergency-plan__nodes-header">
          <h4 class="emergency-plan__dialog-subtitle">处置流程节点（{{ (planDetail.flow_nodes || []).length }}）</h4>
          <el-button size="small" type="primary" plain @click="openNodeDialog(null)">
            <el-icon><Plus /></el-icon> 新增节点
          </el-button>
        </div>
        <el-table :data="planDetail.flow_nodes || []" class="app-table" size="small" max-height="320">
          <el-table-column prop="seq" label="序号" width="60" align="center" />
          <el-table-column label="节点类型" width="100" align="center">
            <template #default="{ row }">
              <el-tag size="small" type="info">{{ NODE_TYPES[row.node_type] || row.node_type }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="title" label="节点标题" min-width="150" show-overflow-tooltip />
          <el-table-column prop="desc" label="说明" min-width="180" show-overflow-tooltip />
          <el-table-column label="时限" width="90" align="center">
            <template #default="{ row }">{{ row.deadline_min }} 分钟</template>
          </el-table-column>
          <el-table-column prop="exit_condition" label="退出条件" min-width="150" show-overflow-tooltip />
          <el-table-column label="操作" width="110" align="center">
            <template #default="{ row }">
              <el-button link type="primary" size="small" @click="openNodeDialog(row)">编辑</el-button>
              <el-button link type="danger" size="small" @click="handleNodeDelete(row)">删除</el-button>
            </template>
          </el-table-column>
        </el-table>
      </template>
    </el-dialog>

    <!-- ============ 流程节点新增/编辑对话框 ============ -->
    <el-dialog
      v-model="nodeDialogVisible"
      :title="nodeIsEdit ? '编辑节点' : '新增节点'"
      width="560px"
      destroy-on-close
      append-to-body
      class="emergency-plan__dialog"
    >
      <el-form ref="nodeFormRef" :model="nodeForm" :rules="nodeRules" label-width="90px">
        <el-form-item label="节点类型" prop="node_type">
          <el-select v-model="nodeForm.node_type" style="width: 100%;">
            <el-option v-for="(label, key) in NODE_TYPES" :key="key" :label="label" :value="key" />
          </el-select>
        </el-form-item>
        <el-form-item label="节点标题" prop="title">
          <el-input v-model="nodeForm.title" placeholder="如 关闭燃气舱入口阀门" />
        </el-form-item>
        <el-form-item label="节点说明">
          <el-input v-model="nodeForm.desc" type="textarea" :rows="2" placeholder="节点处置说明" />
        </el-form-item>
        <el-form-item label="时限(分钟)" prop="deadline_min">
          <el-input-number v-model="nodeForm.deadline_min" :min="1" style="width: 100%;" />
        </el-form-item>
        <el-form-item label="退出条件">
          <el-input v-model="nodeForm.exit_condition" placeholder="如 甲烷浓度降至 1%LEL 以下" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="nodeDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="nodeSubmitting" @click="handleNodeSubmit">确定</el-button>
      </template>
    </el-dialog>

    <!-- ============ 发起演练对话框 ============ -->
    <el-dialog v-model="drillDialogVisible" title="发起演练" width="560px" destroy-on-close class="emergency-plan__dialog">
      <el-form ref="drillFormRef" :model="drillForm" :rules="drillRules" label-width="100px">
        <el-form-item label="演练类别" prop="category">
          <el-select v-model="drillForm.category" placeholder="选择类别" style="width: 100%;">
            <el-option v-for="c in categories" :key="c.code" :label="c.name" :value="c.code" />
          </el-select>
        </el-form-item>
        <el-form-item label="事件级别" prop="level">
          <el-select v-model="drillForm.level" style="width: 100%;">
            <el-option label="Ⅰ级（严重）" :value="2" />
            <el-option label="Ⅱ级（预警）" :value="1" />
          </el-select>
        </el-form-item>
        <el-form-item label="演练舱室">
          <el-select v-model="drillForm.cabin" placeholder="不限" clearable style="width: 100%;">
            <el-option label="电力舱" value="EL" />
            <el-option label="燃气舱" value="GS" />
            <el-option label="水信舱" value="WS" />
          </el-select>
        </el-form-item>
        <el-form-item label="演练区段">
          <el-input v-model="drillForm.zone" placeholder="如 Z03（可空）" />
        </el-form-item>
        <el-form-item label="演练说明">
          <el-input v-model="drillForm.description" type="textarea" :rows="2" placeholder="如 桌面演练" />
        </el-form-item>
        <el-form-item label="激活最优预案">
          <el-switch v-model="drillForm.activate_best" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="drillDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="drillSubmitting" @click="handleDrillSubmit">发起</el-button>
      </template>
    </el-dialog>

    <!-- ============ 演练实例详情对话框 ============ -->
    <el-dialog v-model="actDetailVisible" title="处置实例详情" width="760px" class="emergency-plan__dialog">
      <template v-if="actDetail">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="实例编号">{{ actDetail.activation_id }}</el-descriptions-item>
          <el-descriptions-item label="预案">{{ actDetail.plan_name }}（{{ actDetail.plan_id }}）</el-descriptions-item>
          <el-descriptions-item label="类别">{{ actDetail.category_name }}</el-descriptions-item>
          <el-descriptions-item label="触发方式">{{ actDetail.trigger }}</el-descriptions-item>
          <el-descriptions-item label="状态">
            <el-tag :type="actDetail.status === 'running' ? 'warning' : 'success'" size="small">
              {{ actDetail.status === 'running' ? '进行中' : '已完结' }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="处置进度">{{ actProgress }}</el-descriptions-item>
          <el-descriptions-item label="激活时间">{{ actDetail.activated_at }}</el-descriptions-item>
          <el-descriptions-item label="完结时间">{{ actDetail.finished_at || '-' }}</el-descriptions-item>
        </el-descriptions>

        <h4 class="emergency-plan__dialog-subtitle">节点处置状态</h4>
        <el-table :data="actDetail.nodes || []" class="app-table" size="small" max-height="320">
          <el-table-column label="节点" min-width="180" show-overflow-tooltip>
            <template #default="{ row }">
              <el-tag size="small" type="info" class="reason-tag">{{ NODE_TYPES[row.node_type] || row.node_type }}</el-tag>
              {{ row.title }}
            </template>
          </el-table-column>
          <el-table-column label="状态" width="90" align="center">
            <template #default="{ row }">
              <el-tag :type="nodeStatusType(row.status)" size="small">{{ nodeStatusText(row.status) }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column label="完成时间" width="170">
            <template #default="{ row }"><span class="time-cell">{{ row.finished_at || '-' }}</span></template>
          </el-table-column>
          <el-table-column label="操作" width="100" align="center">
            <template #default="{ row }">
              <el-button
                v-if="actDetail.status === 'running' && row.status === 'pending'"
                link type="success" size="small"
                @click="handleNodeDone(row)"
              >标记完成</el-button>
            </template>
          </el-table-column>
        </el-table>
      </template>
      <template #footer>
        <el-button @click="actDetailVisible = false">关闭</el-button>
        <el-button
          v-if="actDetail && actDetail.status === 'running'"
          type="success"
          @click="handleFinish(actDetail)"
        >完结实例</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Search, Upload, Download, Refresh, Aim } from '@element-plus/icons-vue'
import * as XLSX from 'xlsx'
import { saveAs } from 'file-saver'
import PageHeader from '@/components/PageHeader.vue'
import StatCard from '@/components/StatCard.vue'
import {
  getOverview, getCategories, getPlans, createPlan, getPlanDetail,
  updatePlan, deletePlan, addNode, updateNode, deleteNode,
  matchPlans, getLiveMatches, runDrill, getActivations,
  markNodeDone, finishActivation
} from '@/api/emergencyPlan'

// ===== 枚举常量（与后端约定一致） =====
const NODE_TYPES = {
  detect: '侦检确认',
  notify: '通报预警',
  isolate: '隔离控制',
  rescue: '应急处置',
  restore: '恢复重建',
  verify: '核查复盘'
}

const activeTab = ref('plans')

// ===== 总览统计 =====
const overview = ref({})
const loadOverview = async () => {
  try {
    overview.value = await getOverview() || {}
  } catch (e) {
    console.error('加载预案总览失败:', e)
  }
}

// ===== 预案分类 =====
const categories = ref([])
const categoryLoading = ref(false)

const loadCategories = async () => {
  categoryLoading.value = true
  try {
    const res = await getCategories()
    categories.value = res?.categories || []
  } catch (e) {
    ElMessage.error('加载预案分类失败')
    console.error('加载预案分类失败:', e)
  } finally {
    categoryLoading.value = false
  }
}

const categoryName = (code) =>
  categories.value.find(c => c.code === code)?.name || code || '-'

// ===== Tab 1 预案管理 =====
const planQuery = ref({ keyword: '', category: '', status: '' })
const plans = ref([])
const planLoading = ref(false)
const planPage = ref(1)
const planSize = ref(10)

const planPaged = computed(() => {
  const start = (planPage.value - 1) * planSize.value
  return plans.value.slice(start, start + planSize.value)
})

const planStatusType = (status) => ({
  active: 'success',
  draft: 'warning',
  deprecated: 'info'
}[status] || 'info')

const planStatusText = (status) => ({
  active: '启用中',
  draft: '草稿',
  deprecated: '已废弃'
}[status] || status)

const loadPlans = async () => {
  planLoading.value = true
  try {
    const params = {}
    if (planQuery.value.keyword) params.keyword = planQuery.value.keyword
    if (planQuery.value.category) params.category = planQuery.value.category
    if (planQuery.value.status) params.status = planQuery.value.status
    const res = await getPlans(params)
    plans.value = res?.plans || []
    planPage.value = 1
  } catch (e) {
    ElMessage.error('加载预案列表失败')
    console.error('加载预案列表失败:', e)
  } finally {
    planLoading.value = false
  }
}

const resetPlanQuery = () => {
  planQuery.value = { keyword: '', category: '', status: '' }
  loadPlans()
}

// 新增/编辑预案
const planDialogVisible = ref(false)
const planIsEdit = ref(false)
const planSubmitting = ref(false)
const planFormRef = ref(null)
const planEditingId = ref(null)

const defaultPlanForm = () => ({
  plan_name: '',
  category: '',
  level_min: 1,
  level_max: 2,
  priority: 5,
  status: 'draft',
  scope_cabins: [],
  objective: '',
  commander: ''
})

const planForm = ref(defaultPlanForm())

const planRules = {
  plan_name: [{ required: true, message: '请输入预案名称', trigger: 'blur' }],
  category: [{ required: true, message: '请选择预案类别', trigger: 'change' }],
  level_min: [{ required: true, message: '请选择最低级别', trigger: 'change' }],
  level_max: [{ required: true, message: '请选择最高级别', trigger: 'change' }],
  priority: [{ required: true, message: '请输入优先级', trigger: 'blur' }],
  status: [{ required: true, message: '请选择状态', trigger: 'change' }]
}

const openPlanDialog = (row) => {
  if (row) {
    planIsEdit.value = true
    planEditingId.value = row.plan_id
    planForm.value = {
      plan_name: row.plan_name,
      category: row.category,
      level_min: row.level_min ?? 1,
      level_max: row.level_max ?? 2,
      priority: row.priority ?? 5,
      status: row.status || 'draft',
      scope_cabins: (row.scope_cabins || []).filter(c => c !== '*'),
      objective: row.objective || '',
      commander: row.commander || ''
    }
  } else {
    planIsEdit.value = false
    planEditingId.value = null
    planForm.value = defaultPlanForm()
  }
  planDialogVisible.value = true
}

const handlePlanSubmit = async () => {
  if (!planFormRef.value) return
  try {
    await planFormRef.value.validate()
  } catch (e) {
    return
  }
  if (planForm.value.level_min > planForm.value.level_max) {
    ElMessage.warning('最低级别不得大于最高级别')
    return
  }
  planSubmitting.value = true
  try {
    const body = {
      ...planForm.value,
      scope_cabins: planForm.value.scope_cabins.length ? planForm.value.scope_cabins : ['*']
    }
    if (planIsEdit.value) {
      await updatePlan(planEditingId.value, body)
      ElMessage.success('更新成功')
    } else {
      await createPlan(body)
      ElMessage.success('创建成功')
    }
    planDialogVisible.value = false
    loadPlans()
    loadOverview()
  } catch (e) {
    ElMessage.error(e?.response?.data?.detail || (planIsEdit.value ? '更新失败' : '创建失败'))
    console.error('提交预案失败:', e)
  } finally {
    planSubmitting.value = false
  }
}

// 状态变更（启用 ⇄ 停用）
const handleStatusChange = async (row) => {
  const next = row.status === 'active' ? 'deprecated' : 'active'
  try {
    await updatePlan(row.plan_id, { status: next })
    ElMessage.success(next === 'active' ? '预案已启用' : '预案已停用')
    loadPlans()
    loadOverview()
  } catch (e) {
    ElMessage.error('状态变更失败')
    console.error('状态变更失败:', e)
  }
}

// 删除预案
const handlePlanDelete = async (row) => {
  try {
    await ElMessageBox.confirm(
      `确认删除预案「${row.plan_name}」（${row.plan_id}）？删除后不可恢复。`,
      '删除确认',
      { type: 'warning', confirmButtonText: '删除', cancelButtonText: '取消' }
    )
  } catch (e) {
    return
  }
  try {
    await deletePlan(row.plan_id)
    ElMessage.success('删除成功')
    loadPlans()
    loadOverview()
  } catch (e) {
    ElMessage.error('删除失败')
    console.error('删除预案失败:', e)
  }
}

// 预案详情（含流程节点管理）
const planDetailVisible = ref(false)
const planDetail = ref(null)

const openPlanDetail = async (row) => {
  try {
    planDetail.value = await getPlanDetail(row.plan_id)
    planDetailVisible.value = true
  } catch (e) {
    ElMessage.error('加载预案详情失败')
    console.error('加载预案详情失败:', e)
  }
}

const reloadPlanDetail = async () => {
  if (!planDetail.value) return
  try {
    planDetail.value = await getPlanDetail(planDetail.value.plan_id)
    loadPlans()
  } catch (e) {
    console.error('刷新预案详情失败:', e)
  }
}

// 匹配结果中查看预案详情
const viewMatchedPlan = async (planId) => {
  try {
    planDetail.value = await getPlanDetail(planId)
    planDetailVisible.value = true
  } catch (e) {
    ElMessage.error('加载预案详情失败')
  }
}

// 流程节点 CRUD
const nodeDialogVisible = ref(false)
const nodeIsEdit = ref(false)
const nodeSubmitting = ref(false)
const nodeFormRef = ref(null)
const nodeEditingId = ref(null)

const defaultNodeForm = () => ({
  node_type: 'rescue',
  title: '',
  desc: '',
  deadline_min: 30,
  exit_condition: ''
})

const nodeForm = ref(defaultNodeForm())

const nodeRules = {
  node_type: [{ required: true, message: '请选择节点类型', trigger: 'change' }],
  title: [{ required: true, message: '请输入节点标题', trigger: 'blur' }],
  deadline_min: [{ required: true, message: '请输入时限', trigger: 'blur' }]
}

const openNodeDialog = (row) => {
  if (row) {
    nodeIsEdit.value = true
    nodeEditingId.value = row.node_id
    nodeForm.value = {
      node_type: row.node_type || 'rescue',
      title: row.title || '',
      desc: row.desc || '',
      deadline_min: row.deadline_min ?? 30,
      exit_condition: row.exit_condition || ''
    }
  } else {
    nodeIsEdit.value = false
    nodeEditingId.value = null
    nodeForm.value = defaultNodeForm()
  }
  nodeDialogVisible.value = true
}

const handleNodeSubmit = async () => {
  if (!nodeFormRef.value || !planDetail.value) return
  try {
    await nodeFormRef.value.validate()
  } catch (e) {
    return
  }
  nodeSubmitting.value = true
  try {
    const planId = planDetail.value.plan_id
    if (nodeIsEdit.value) {
      await updateNode(planId, nodeEditingId.value, nodeForm.value)
      ElMessage.success('节点已更新')
    } else {
      await addNode(planId, nodeForm.value)
      ElMessage.success('节点已新增')
    }
    nodeDialogVisible.value = false
    reloadPlanDetail()
  } catch (e) {
    ElMessage.error(e?.response?.data?.detail || '节点保存失败')
    console.error('保存节点失败:', e)
  } finally {
    nodeSubmitting.value = false
  }
}

const handleNodeDelete = async (row) => {
  try {
    await ElMessageBox.confirm(
      `确认删除节点「${row.title}」？`,
      '删除确认',
      { type: 'warning', confirmButtonText: '删除', cancelButtonText: '取消' }
    )
  } catch (e) {
    return
  }
  try {
    await deleteNode(planDetail.value.plan_id, row.node_id)
    ElMessage.success('节点已删除')
    reloadPlanDetail()
  } catch (e) {
    ElMessage.error('删除节点失败')
    console.error('删除节点失败:', e)
  }
}

// ===== Tab 2 智能匹配 =====
const matchForm = ref({ category: '', level: 1, cabin: '', zone: '' })
const matchResult = ref(null)
const matchLoading = ref(false)

const scoreColor = (score) => {
  if (score >= 80) return '#34C759'
  if (score >= 60) return '#FF9500'
  return '#FF3B30'
}

const handleMatch = async () => {
  matchLoading.value = true
  try {
    const body = { level: matchForm.value.level, top_n: 5 }
    if (matchForm.value.category) body.category = matchForm.value.category
    if (matchForm.value.cabin) body.cabin = matchForm.value.cabin
    if (matchForm.value.zone) body.zone = matchForm.value.zone
    matchResult.value = await matchPlans(body)
    loadOverview()
  } catch (e) {
    ElMessage.error(e?.response?.data?.detail || '预案匹配失败')
    console.error('预案匹配失败:', e)
  } finally {
    matchLoading.value = false
  }
}

const liveMatches = ref([])
const liveLoading = ref(false)

const loadLiveMatches = async () => {
  liveLoading.value = true
  try {
    const res = await getLiveMatches(20)
    liveMatches.value = res?.matches || []
  } catch (e) {
    console.error('加载实时匹配流失败:', e)
  } finally {
    liveLoading.value = false
  }
}

// ===== Tab 3 演练记录（处置实例） =====
const actQuery = ref({ status: '' })
const activations = ref([])
const actLoading = ref(false)
const actPage = ref(1)
const actSize = ref(10)

const actPaged = computed(() => {
  const start = (actPage.value - 1) * actSize.value
  return activations.value.slice(start, start + actSize.value)
})

const loadActivations = async () => {
  actLoading.value = true
  try {
    const params = {}
    if (actQuery.value.status) params.status = actQuery.value.status
    const res = await getActivations(params)
    activations.value = res?.activations || []
    actPage.value = 1
  } catch (e) {
    ElMessage.error('加载演练记录失败')
    console.error('加载演练记录失败:', e)
  } finally {
    actLoading.value = false
  }
}

// 发起演练
const drillDialogVisible = ref(false)
const drillSubmitting = ref(false)
const drillFormRef = ref(null)
const drillForm = ref({ category: '', level: 1, cabin: '', zone: '', description: '', activate_best: true })
const drillRules = {
  category: [{ required: true, message: '请选择演练类别', trigger: 'change' }],
  level: [{ required: true, message: '请选择事件级别', trigger: 'change' }]
}

const openDrillDialog = () => {
  drillForm.value = { category: '', level: 1, cabin: '', zone: '', description: '', activate_best: true }
  drillDialogVisible.value = true
}

const handleDrillSubmit = async () => {
  if (!drillFormRef.value) return
  try {
    await drillFormRef.value.validate()
  } catch (e) {
    return
  }
  drillSubmitting.value = true
  try {
    const body = {
      category: drillForm.value.category,
      level: drillForm.value.level,
      description: drillForm.value.description,
      activate_best: drillForm.value.activate_best
    }
    if (drillForm.value.cabin) body.cabin = drillForm.value.cabin
    if (drillForm.value.zone) body.zone = drillForm.value.zone
    const res = await runDrill(body)
    const best = res?.match?.candidates?.[0]
    ElMessage.success(best
      ? `演练已发起，匹配最优预案：${best.plan_name}（${best.score} 分）`
      : '演练已发起，未匹配到候选预案')
    drillDialogVisible.value = false
    loadActivations()
    loadOverview()
    loadLiveMatches()
  } catch (e) {
    ElMessage.error(e?.response?.data?.detail || '发起演练失败')
    console.error('发起演练失败:', e)
  } finally {
    drillSubmitting.value = false
  }
}

// 实例详情
const actDetailVisible = ref(false)
const actDetail = ref(null)

const actProgress = computed(() => {
  const nodes = actDetail.value?.nodes || []
  if (!nodes.length) return '0/0'
  const done = nodes.filter(n => n.status === 'done' || n.status === 'skipped').length
  return `${done}/${nodes.length}`
})

const openActDetail = (row) => {
  actDetail.value = row
  actDetailVisible.value = true
}

const nodeStatusType = (status) => ({
  done: 'success',
  skipped: 'info',
  pending: 'warning'
}[status] || 'info')

const nodeStatusText = (status) => ({
  done: '已完成',
  skipped: '已跳过',
  pending: '待处置'
}[status] || status)

// 标记节点完成
const handleNodeDone = async (row) => {
  try {
    const res = await markNodeDone(actDetail.value.activation_id, row.node_id)
    ElMessage.success(`节点已完成（进度 ${res?.progress || ''}）`)
    row.status = 'done'
    row.finished_at = new Date().toLocaleString('zh-CN', { hour12: false })
    loadActivations()
  } catch (e) {
    ElMessage.error(e?.response?.data?.detail || '标记失败')
    console.error('标记节点完成失败:', e)
  }
}

// 完结实例
const handleFinish = async (row) => {
  try {
    await ElMessageBox.confirm(
      `确认完结处置实例 ${row.activation_id}？完结前需所有节点均已处置。`,
      '完结确认',
      { type: 'warning', confirmButtonText: '完结', cancelButtonText: '取消' }
    )
  } catch (e) {
    return
  }
  try {
    await finishActivation(row.activation_id)
    ElMessage.success('实例已完结')
    actDetailVisible.value = false
    loadActivations()
    loadOverview()
  } catch (e) {
    ElMessage.error(e?.response?.data?.detail || '完结失败')
    console.error('完结实例失败:', e)
  }
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

const exportPlans = () => {
  exportSheet(
    plans.value.map(p => ({
      预案编号: p.plan_id, 预案名称: p.plan_name, 类别: categoryName(p.category),
      最低级别: p.level_min, 最高级别: p.level_max, 优先级: p.priority,
      状态: planStatusText(p.status), 适用舱室: (p.scope_cabins || []).join('/'),
      指挥长: p.commander, 节点数: (p.flow_nodes || []).length,
      处置目标: p.objective, 更新时间: p.updated_at
    })),
    '应急预案台账.xlsx'
  )
}

const exportActivations = () => {
  exportSheet(
    activations.value.map(a => ({
      实例编号: a.activation_id, 预案编号: a.plan_id, 预案名称: a.plan_name,
      类别: a.category_name, 触发方式: a.trigger,
      状态: a.status === 'running' ? '进行中' : '已完结',
      激活时间: a.activated_at, 完结时间: a.finished_at || '',
      节点数: (a.nodes || []).length,
      已完成节点: (a.nodes || []).filter(n => n.status === 'done').length
    })),
    '演练处置记录.xlsx'
  )
}

const exportCategories = () => {
  exportSheet(
    categories.value.map(c => ({
      类别编码: c.code, 类别名称: c.name, 说明: c.description,
      关联传感指标: (c.sensor_metrics || []).join('/'),
      演练告警码: c.drill_alarm_code, 预案数: c.plan_count, 启用数: c.active_count
    })),
    '预案分类目录.xlsx'
  )
}

// ===== Excel 导入（预案批量导入） =====
// 表头：plan_name, category, level_min, level_max, priority, status, objective, commander
const importPlans = async ({ file }) => {
  const reader = new FileReader()
  reader.onload = async (e) => {
    try {
      const wb = XLSX.read(new Uint8Array(e.target.result), { type: 'array' })
      const sheet = wb.Sheets[wb.SheetNames[0]]
      const rows = XLSX.utils.sheet_to_json(sheet)
      if (!rows.length) {
        ElMessage.warning('文件中没有数据')
        return
      }
      let ok = 0
      let fail = 0
      for (const r of rows) {
        try {
          await createPlan({
            plan_name: String(r.plan_name || r['预案名称'] || ''),
            category: String(r.category || r['类别'] || '').toUpperCase(),
            level_min: Number(r.level_min ?? r['最低级别'] ?? 1),
            level_max: Number(r.level_max ?? r['最高级别'] ?? 2),
            priority: Number(r.priority ?? r['优先级'] ?? 5),
            status: ['active', 'draft', 'deprecated'].includes(r.status) ? r.status : 'draft',
            objective: String(r.objective ?? r['处置目标'] ?? ''),
            commander: String(r.commander ?? r['指挥长'] ?? '')
          })
          ok += 1
        } catch (err) {
          fail += 1
        }
      }
      ElMessage.success(`导入完成：成功 ${ok} 条${fail ? `，失败 ${fail} 条` : ''}`)
      loadPlans()
      loadOverview()
    } catch (err) {
      ElMessage.error('导入失败：文件解析错误')
      console.error('导入预案失败:', err)
    }
  }
  reader.onerror = () => ElMessage.error('读取文件失败')
  reader.readAsArrayBuffer(file)
}

// ===== 刷新 & 生命周期 =====
const refreshAll = () => {
  loadOverview()
  loadCategories()
  if (activeTab.value === 'plans') loadPlans()
  else if (activeTab.value === 'match') loadLiveMatches()
  else if (activeTab.value === 'activations') loadActivations()
}

onMounted(() => {
  loadOverview()
  loadCategories()
  loadPlans()
  loadLiveMatches()
  loadActivations()
})
</script>

<style scoped>
.emergency-plan__stats {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
  margin-bottom: 16px;
}
.emergency-plan__tabs-card {
  padding: 8px 20px 16px;
}
.emergency-plan__filter {
  margin-bottom: 16px;
}
.emergency-plan__filter-item {
  width: 160px;
}
.emergency-plan__export-btn {
  margin-left: auto;
}
.emergency-plan__upload {
  display: inline-flex;
  margin-left: 12px;
}
.emergency-plan__pagination {
  display: flex;
  justify-content: flex-end;
  margin-top: 16px;
}

/* 智能匹配双栏布局 */
.emergency-plan__match-grid {
  display: grid;
  grid-template-columns: 1.3fr 1fr;
  gap: 24px;
}
.emergency-plan__match-panel {
  min-width: 0;
}
.emergency-plan__fallback {
  border-radius: 12px;
}

/* 卡片小标题 */
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

/* 详情对话框节点区头部 */
.emergency-plan__nodes-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 8px;
}
.emergency-plan__dialog-subtitle {
  margin: 18px 0 10px;
  font-size: 14px;
  font-weight: 600;
  color: var(--app-text-2);
}

/* 分类页提示 */
.emergency-plan__category-tip {
  font-size: 13px;
  color: var(--app-text-3);
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
.priority-value {
  font-weight: 600;
  color: var(--app-text-1);
}
.score-value {
  font-weight: 700;
  font-family: 'Courier New', monospace;
}
.reason-tag {
  margin: 2px 4px 2px 0;
}
.text-muted {
  color: var(--app-text-3);
  font-size: 13px;
}

@media (max-width: 1024px) {
  .emergency-plan__stats { grid-template-columns: repeat(2, 1fr); }
  .emergency-plan__match-grid { grid-template-columns: 1fr; }
}
</style>
