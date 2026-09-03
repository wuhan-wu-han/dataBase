<template>
  <div class="asset-cost">
    <PageHeader title="资产成本管理" subtitle="Asset Cost Management">
      <el-upload
        v-if="canImport"
        class="asset-cost__upload"
        :show-file-list="false"
        :http-request="handleImport"
        accept=".xlsx,.xls"
      >
        <el-button :loading="importing">
          <el-icon><Upload /></el-icon> 导入Excel
        </el-button>
      </el-upload>
      <el-button v-if="canExport" :loading="exporting" @click="handleExport">
        <el-icon><Download /></el-icon> 导出Excel
      </el-button>
      <el-button @click="refreshCurrentTab">刷新</el-button>
      <el-button v-if="canAdd" type="primary" @click="openAddDialog">
        <el-icon><Plus /></el-icon> {{ addButtonText }}
      </el-button>
    </PageHeader>

    <!-- 4 个统计卡片 -->
    <div class="asset-cost__stats">
      <StatCard label="资产总数" :value="overview?.total_assets ?? 0" icon="OfficeBuilding" color="#0071E3" />
      <StatCard label="资产原值(万元)" :value="originalValueWan" icon="Money" color="#34C759" />
      <StatCard label="年度费用(万元)" :value="annualCostWan" icon="Wallet" color="#FF9500" />
      <StatCard label="折旧率(%)" :value="deprPctText" icon="TrendCharts" color="#5856D6" />
    </div>

    <!-- 主体：4 个 Tab -->
    <section class="app-card asset-cost__main">
      <el-tabs v-model="activeTab" @tab-change="handleTabChange">
        <!-- ============ Tab 1 资产台账 ============ -->
        <el-tab-pane label="资产台账" name="assets">
          <div class="filter-bar asset-cost__filter">
            <el-input
              v-model="assetQuery.keyword"
              placeholder="资产名称/编号"
              clearable
              class="asset-cost__filter-item"
              @keyup.enter="searchAssets"
            />
            <el-select v-model="assetQuery.category" placeholder="资产类别" clearable class="asset-cost__filter-item" @change="searchAssets">
              <el-option v-for="(cfg, code) in categories" :key="code" :label="cfg.name" :value="code" />
            </el-select>
            <el-select v-model="assetQuery.region" placeholder="所属片区" clearable class="asset-cost__filter-item" @change="searchAssets">
              <el-option v-for="r in regions" :key="r" :label="r" :value="r" />
            </el-select>
            <el-select v-model="assetQuery.status" placeholder="资产状态" clearable class="asset-cost__filter-item" @change="searchAssets">
              <el-option v-for="s in ASSET_STATUS_LIST" :key="s" :label="s" :value="s" />
            </el-select>
            <el-button type="primary" @click="searchAssets">
              <el-icon><Search /></el-icon> 查询
            </el-button>
            <el-button @click="resetAssetQuery">重置</el-button>
          </div>

          <el-table :data="assets" v-loading="assetLoading" class="app-table" empty-text="暂无资产数据">
            <el-table-column prop="asset_id" label="资产编号" width="130">
              <template #default="{ row }"><span class="code-cell">{{ row.asset_id }}</span></template>
            </el-table-column>
            <el-table-column prop="name" label="资产名称" min-width="150" show-overflow-tooltip />
            <el-table-column label="类别" width="100">
              <template #default="{ row }">{{ row.category_name || categoryName(row.category) }}</template>
            </el-table-column>
            <el-table-column prop="region" label="片区" width="100" />
            <el-table-column label="材质" width="100">
              <template #default="{ row }">{{ row.material_name || materialName(row.material) }}</template>
            </el-table-column>
            <el-table-column prop="specs" label="规格" min-width="120" show-overflow-tooltip />
            <el-table-column label="原值(元)" width="120" align="right">
              <template #default="{ row }"><span class="num-cell">{{ fmtMoney(row.original_value) }}</span></template>
            </el-table-column>
            <el-table-column prop="install_date" label="安装日期" width="110" align="center" />
            <el-table-column label="状态" width="90" align="center">
              <template #default="{ row }">
                <el-tag :type="assetStatusType(row.status)" size="small">{{ row.status }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column label="累计折旧" width="110" align="right">
              <template #default="{ row }">{{ fmtMoney(row.accumulated_depr) }}</template>
            </el-table-column>
            <el-table-column label="净值(元)" width="120" align="right">
              <template #default="{ row }"><span class="num-cell">{{ fmtMoney(row.net_value) }}</span></template>
            </el-table-column>
            <el-table-column label="折旧率" width="90" align="right">
              <template #default="{ row }">{{ fmtPct(row.depr_pct) }}</template>
            </el-table-column>
            <el-table-column label="操作" width="220" align="center" fixed="right">
              <template #default="{ row }">
                <div class="table-actions">
                  <el-button link type="primary" size="small" @click="openAssetDetail(row)">详情</el-button>
                  <el-button v-if="row.status === '在用'" link type="success" size="small" @click="handleReviewAsset(row, true)">通过</el-button>
                  <el-button v-if="row.status === '在用'" link type="danger" size="small" @click="handleReviewAsset(row, false)">驳回</el-button>
                  <el-button link type="warning" size="small" @click="openAssetDialog(row)">编辑</el-button>
                  <el-button link type="danger" size="small" @click="handleDeleteAsset(row)">删除</el-button>
                </div>
              </template>
            </el-table-column>
          </el-table>

          <div class="asset-cost__pagination">
            <el-pagination
              v-model:current-page="assetQuery.page"
              v-model:page-size="assetQuery.page_size"
              :total="assetTotal"
              :page-sizes="[10, 20, 50]"
              layout="total, sizes, prev, pager, next"
              @size-change="loadAssets"
              @current-change="loadAssets"
            />
          </div>
        </el-tab-pane>

        <!-- ============ Tab 2 费用记录 ============ -->
        <el-tab-pane label="费用记录" name="costs">
          <div class="filter-bar asset-cost__filter">
            <el-select v-model="costQuery.cost_type" placeholder="费用类型" clearable class="asset-cost__filter-item" @change="searchCosts">
              <el-option v-for="t in COST_TYPES" :key="t" :label="t" :value="t" />
            </el-select>
            <el-select v-model="costQuery.region" placeholder="所属片区" clearable class="asset-cost__filter-item" @change="searchCosts">
              <el-option v-for="r in regions" :key="r" :label="r" :value="r" />
            </el-select>
            <el-select v-model="costQuery.approved" placeholder="审批状态" clearable class="asset-cost__filter-item" @change="searchCosts">
              <el-option label="已审批" :value="true" />
              <el-option label="待审批" :value="false" />
            </el-select>
            <el-button type="primary" @click="searchCosts">
              <el-icon><Search /></el-icon> 查询
            </el-button>
            <el-button @click="resetCostQuery">重置</el-button>
          </div>

          <el-table :data="costRecords" v-loading="costLoading" class="app-table" empty-text="暂无费用记录">
            <el-table-column prop="record_id" label="记录编号" width="120">
              <template #default="{ row }"><span class="code-cell">{{ row.record_id }}</span></template>
            </el-table-column>
            <el-table-column prop="asset_id" label="资产编号" width="130" />
            <el-table-column prop="cost_type" label="费用类型" width="110" align="center" />
            <el-table-column label="金额(元)" width="110" align="right">
              <template #default="{ row }"><span class="num-cell">{{ fmtMoney(row.amount) }}</span></template>
            </el-table-column>
            <el-table-column prop="description" label="费用说明" min-width="170" show-overflow-tooltip />
            <el-table-column prop="region" label="片区" width="100" />
            <el-table-column prop="record_date" label="记录日期" width="110" align="center" />
            <el-table-column label="审批状态" width="100" align="center">
              <template #default="{ row }">
                <el-tag :type="row.approved ? 'success' : 'warning'" size="small">
                  {{ row.approved ? '已审批' : '待审批' }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column label="创建时间" width="160">
              <template #default="{ row }"><span class="time-cell">{{ formatDateTime(row.created_at) }}</span></template>
            </el-table-column>
            <el-table-column label="操作" width="220" align="center" fixed="right">
              <template #default="{ row }">
                <div class="table-actions">
                  <el-button link type="primary" size="small" @click="openCostDetail(row)">详情</el-button>
                  <el-button v-if="!row.approved" link type="success" size="small" @click="handleReviewCost(row, true)">通过</el-button>
                  <el-button v-if="!row.approved" link type="danger" size="small" @click="handleReviewCost(row, false)">驳回</el-button>
                  <el-button link type="warning" size="small" @click="openCostDialog(row)">编辑</el-button>
                  <el-button link type="danger" size="small" @click="handleDeleteCost(row)">删除</el-button>
                </div>
              </template>
            </el-table-column>
          </el-table>

          <div class="asset-cost__pagination">
            <el-pagination
              v-model:current-page="costQuery.page"
              v-model:page-size="costQuery.page_size"
              :total="costTotal"
              :page-sizes="[10, 20, 50]"
              layout="total, sizes, prev, pager, next"
              @size-change="loadCosts"
              @current-change="loadCosts"
            />
          </div>
        </el-tab-pane>

        <!-- ============ Tab 3 成本分析 ============ -->
        <el-tab-pane label="成本分析" name="analysis">
          <div class="asset-cost__analysis" v-loading="analysisLoading">
            <div class="analysis-grid">
              <section class="analysis-panel">
                <header class="card-title">
                  <h3 class="card-title__text">按费用类型</h3>
                  <span class="card-title__badge">总费用 {{ fmtMoney(analysis?.total_cost) }} 元</span>
                </header>
                <el-table :data="byTypeRows" class="app-table" size="small" empty-text="暂无数据">
                  <el-table-column prop="type" label="费用类型" min-width="110" />
                  <el-table-column label="总金额(元)" min-width="120" align="right">
                    <template #default="{ row }"><span class="num-cell">{{ fmtMoney(row.total) }}</span></template>
                  </el-table-column>
                  <el-table-column prop="count" label="笔数" width="80" align="right" />
                </el-table>
              </section>

              <section class="analysis-panel">
                <header class="card-title">
                  <h3 class="card-title__text">按片区分布</h3>
                </header>
                <el-table :data="byRegionRows" class="app-table" size="small" empty-text="暂无数据">
                  <el-table-column prop="region" label="片区" min-width="110" />
                  <el-table-column label="总金额(元)" min-width="120" align="right">
                    <template #default="{ row }"><span class="num-cell">{{ fmtMoney(row.total) }}</span></template>
                  </el-table-column>
                  <el-table-column prop="count" label="笔数" width="80" align="right" />
                </el-table>
              </section>

              <section class="analysis-panel">
                <header class="card-title">
                  <h3 class="card-title__text">月度费用趋势</h3>
                </header>
                <el-table :data="trendRows" class="app-table" size="small" empty-text="暂无数据">
                  <el-table-column prop="month" label="月份" width="100" />
                  <el-table-column label="金额(元)" width="120" align="right">
                    <template #default="{ row }"><span class="num-cell">{{ fmtMoney(row.amount) }}</span></template>
                  </el-table-column>
                  <el-table-column label="占比" min-width="160">
                    <template #default="{ row }">
                      <div class="trend-bar">
                        <div class="trend-bar__fill" :style="{ width: trendBarPct(row.amount) }"></div>
                      </div>
                    </template>
                  </el-table-column>
                </el-table>
              </section>

              <section class="analysis-panel">
                <header class="card-title">
                  <h3 class="card-title__text">高成本资产 TOP</h3>
                </header>
                <el-table :data="analysis?.top_cost_assets || []" class="app-table" size="small" empty-text="暂无数据">
                  <el-table-column label="排名" width="70" align="center">
                    <template #default="{ $index }">
                      <span class="rank-cell" :class="{ 'rank-cell--top': $index < 3 }">{{ $index + 1 }}</span>
                    </template>
                  </el-table-column>
                  <el-table-column prop="asset_id" label="资产编号" min-width="120">
                    <template #default="{ row }"><span class="code-cell">{{ row.asset_id }}</span></template>
                  </el-table-column>
                  <el-table-column label="累计费用(元)" min-width="120" align="right">
                    <template #default="{ row }"><span class="num-cell">{{ fmtMoney(row.total_cost) }}</span></template>
                  </el-table-column>
                  <el-table-column prop="record_count" label="费用笔数" width="90" align="right" />
                </el-table>
              </section>
            </div>
          </div>
        </el-tab-pane>

        <!-- ============ Tab 4 LCC分析 ============ -->
        <el-tab-pane label="LCC分析" name="lcc">
          <el-table :data="lccList" v-loading="lccLoading" class="app-table" empty-text="暂无LCC分析数据">
            <el-table-column prop="analysis_id" label="分析编号" width="130">
              <template #default="{ row }"><span class="code-cell">{{ row.analysis_id }}</span></template>
            </el-table-column>
            <el-table-column prop="project_name" label="项目名称" min-width="180" show-overflow-tooltip />
            <el-table-column label="设计寿命" width="100" align="center">
              <template #default="{ row }">{{ row.design_life }} 年</template>
            </el-table-column>
            <el-table-column prop="discount_rate" label="折现率" width="90" align="center" />
            <el-table-column label="推荐方案" width="150" align="center">
              <template #default="{ row }">
                <el-tag v-if="row.recommended" type="success" size="small">{{ materialName(row.recommended) }}</el-tag>
                <span v-else>-</span>
              </template>
            </el-table-column>
            <el-table-column label="比选方案数" width="100" align="center">
              <template #default="{ row }">{{ (row.options || []).length }}</template>
            </el-table-column>
            <el-table-column label="创建时间" width="160">
              <template #default="{ row }"><span class="time-cell">{{ formatDateTime(row.created_at) }}</span></template>
            </el-table-column>
            <el-table-column label="操作" width="90" align="center" fixed="right">
              <template #default="{ row }">
                <div class="table-actions">
                  <el-button link type="primary" size="small" @click="openLccDetail(row)">详情</el-button>
                </div>
              </template>
            </el-table-column>
          </el-table>
        </el-tab-pane>
      </el-tabs>
    </section>

    <!-- ============ 资产新增/编辑对话框 ============ -->
    <el-dialog
      v-model="assetDialogVisible"
      :title="assetIsEdit ? '编辑资产' : '新增资产'"
      width="680px"
      destroy-on-close
    >
      <el-form ref="assetFormRef" :model="assetForm" :rules="assetRules" label-width="100px">
        <el-form-item label="资产名称" prop="name">
          <el-input v-model="assetForm.name" placeholder="如 城北片区供水主管" />
        </el-form-item>
        <el-form-item label="资产类别" prop="category">
          <el-select v-model="assetForm.category" placeholder="选择类别" style="width: 100%;" @change="onCategoryChange">
            <el-option v-for="(cfg, code) in categories" :key="code" :label="cfg.name" :value="code" />
          </el-select>
        </el-form-item>
        <el-form-item label="所属片区" prop="region">
          <el-select v-model="assetForm.region" placeholder="选择片区" style="width: 100%;">
            <el-option v-for="r in regions" :key="r" :label="r" :value="r" />
          </el-select>
        </el-form-item>
        <el-form-item label="材质" prop="material">
          <el-select v-model="assetForm.material" placeholder="选择材质" style="width: 100%;">
            <el-option v-for="(cfg, code) in materials" :key="code" :label="cfg.name" :value="code" />
          </el-select>
        </el-form-item>
        <el-form-item label="规格型号" prop="specs">
          <el-input v-model="assetForm.specs" placeholder="如 DN500 × 120m" />
        </el-form-item>
        <el-form-item label="资产原值(元)" prop="original_value">
          <el-input-number v-model="assetForm.original_value" :min="0" :precision="2" :step="10000" style="width: 100%;" />
        </el-form-item>
        <el-form-item label="安装日期" prop="install_date">
          <el-date-picker
            v-model="assetForm.install_date"
            type="date"
            placeholder="选择安装日期"
            value-format="YYYY-MM-DD"
            style="width: 100%;"
          />
        </el-form-item>
        <el-form-item label="折旧方法" prop="depr_method">
          <el-select v-model="assetForm.depr_method" placeholder="选择折旧方法" style="width: 100%;">
            <el-option v-for="(label, code) in deprMethods" :key="code" :label="label" :value="code" />
          </el-select>
        </el-form-item>
        <el-form-item label="折旧年限" prop="depr_years">
          <el-input-number v-model="assetForm.depr_years" :min="1" :max="100" :step="1" style="width: 100%;" />
        </el-form-item>
        <el-form-item label="残值率" prop="residual_rate">
          <el-input-number v-model="assetForm.residual_rate" :min="0" :max="1" :precision="2" :step="0.01" style="width: 100%;" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="assetDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="assetSubmitting" @click="submitAsset">确定</el-button>
      </template>
    </el-dialog>

    <!-- ============ 费用记录新增/编辑对话框 ============ -->
    <el-dialog
      v-model="costDialogVisible"
      :title="costIsEdit ? '编辑费用记录' : '新增费用记录'"
      width="620px"
      destroy-on-close
    >
      <el-form ref="costFormRef" :model="costForm" :rules="costRules" label-width="100px">
        <el-form-item label="资产编号" prop="asset_id">
          <el-input v-model="costForm.asset_id" placeholder="如 AST_0001" />
        </el-form-item>
        <el-form-item label="费用类型" prop="cost_type">
          <el-select v-model="costForm.cost_type" placeholder="选择费用类型" style="width: 100%;">
            <el-option v-for="t in COST_TYPES" :key="t" :label="t" :value="t" />
          </el-select>
        </el-form-item>
        <el-form-item label="金额(元)" prop="amount">
          <el-input-number v-model="costForm.amount" :min="0" :precision="2" :step="1000" style="width: 100%;" />
        </el-form-item>
        <el-form-item label="费用说明" prop="description">
          <el-input v-model="costForm.description" type="textarea" :rows="3" placeholder="费用发生原因、内容等" />
        </el-form-item>
        <el-form-item label="所属片区" prop="region">
          <el-select v-model="costForm.region" placeholder="选择片区" clearable style="width: 100%;">
            <el-option v-for="r in regions" :key="r" :label="r" :value="r" />
          </el-select>
        </el-form-item>
        <el-form-item label="记录日期" prop="record_date">
          <el-date-picker
            v-model="costForm.record_date"
            type="date"
            placeholder="选择记录日期"
            value-format="YYYY-MM-DD"
            style="width: 100%;"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="costDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="costSubmitting" @click="submitCost">确定</el-button>
      </template>
    </el-dialog>

    <!-- ============ 资产详情对话框 ============ -->
    <el-dialog v-model="assetDetailVisible" title="资产详情" width="860px" destroy-on-close>
      <div v-loading="assetDetailLoading">
        <el-descriptions :column="3" border size="small">
          <el-descriptions-item label="资产编号">
            <span class="code-cell">{{ detailAsset.asset_id }}</span>
          </el-descriptions-item>
          <el-descriptions-item label="资产名称">{{ detailAsset.name }}</el-descriptions-item>
          <el-descriptions-item label="状态">
            <el-tag :type="assetStatusType(detailAsset.status)" size="small">{{ detailAsset.status }}</el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="类别">{{ detailAsset.category_name || categoryName(detailAsset.category) }}</el-descriptions-item>
          <el-descriptions-item label="片区">{{ detailAsset.region }}</el-descriptions-item>
          <el-descriptions-item label="材质">{{ detailAsset.material_name || materialName(detailAsset.material) }}</el-descriptions-item>
          <el-descriptions-item label="规格" :span="2">{{ detailAsset.specs || '-' }}</el-descriptions-item>
          <el-descriptions-item label="安装日期">{{ detailAsset.install_date || '-' }}</el-descriptions-item>
          <el-descriptions-item label="资产原值">{{ fmtMoney(detailAsset.original_value) }} 元</el-descriptions-item>
          <el-descriptions-item label="累计折旧">{{ fmtMoney(detailAsset.accumulated_depr) }} 元</el-descriptions-item>
          <el-descriptions-item label="资产净值">{{ fmtMoney(detailAsset.net_value) }} 元</el-descriptions-item>
          <el-descriptions-item label="折旧方法">{{ deprMethodName(detailAsset.depr_method) }}</el-descriptions-item>
          <el-descriptions-item label="折旧年限">{{ detailAsset.depr_years ?? '-' }} 年</el-descriptions-item>
          <el-descriptions-item label="残值率">{{ detailAsset.residual_rate ?? '-' }}</el-descriptions-item>
          <el-descriptions-item label="年折旧额">{{ fmtMoney(detailAsset.annual_depr) }} 元</el-descriptions-item>
          <el-descriptions-item label="已使用">{{ detailAsset.years_elapsed ?? '-' }} 年</el-descriptions-item>
          <el-descriptions-item label="折旧进度">{{ fmtPct(detailAsset.depr_pct) }}</el-descriptions-item>
        </el-descriptions>

        <template v-if="assetDepreciation">
          <header class="card-title asset-cost__section-title">
            <h3 class="card-title__text">折旧计划（{{ deprMethodName(assetDepreciation.method) }} · {{ assetDepreciation.years }}年）</h3>
            <span class="card-title__badge">可折旧额 {{ fmtMoney(assetDepreciation.depreciable) }} 元</span>
          </header>
          <el-table :data="assetDepreciation.schedule || []" class="app-table" size="small" max-height="240" empty-text="暂无折旧计划">
            <el-table-column prop="year" label="年度" width="80" align="center" />
            <el-table-column label="期初净值" align="right">
              <template #default="{ row }">{{ fmtMoney(row.beginning_value) }}</template>
            </el-table-column>
            <el-table-column label="本期折旧" align="right">
              <template #default="{ row }"><span class="num-cell">{{ fmtMoney(row.depr_amount) }}</span></template>
            </el-table-column>
            <el-table-column label="累计折旧" align="right">
              <template #default="{ row }">{{ fmtMoney(row.accumulated) }}</template>
            </el-table-column>
            <el-table-column label="期末净值" align="right">
              <template #default="{ row }">{{ fmtMoney(row.ending_value) }}</template>
            </el-table-column>
          </el-table>
        </template>

        <header class="card-title asset-cost__section-title">
          <h3 class="card-title__text">费用历史</h3>
          <span class="card-title__badge">全生命周期费用 {{ fmtMoney(detailTotalCost) }} 元</span>
        </header>
        <el-table :data="detailCostHistory" class="app-table" size="small" max-height="240" empty-text="暂无费用记录">
          <el-table-column prop="record_date" label="日期" width="110" align="center" />
          <el-table-column prop="cost_type" label="费用类型" width="110" align="center" />
          <el-table-column label="金额(元)" width="120" align="right">
            <template #default="{ row }"><span class="num-cell">{{ fmtMoney(row.amount) }}</span></template>
          </el-table-column>
          <el-table-column prop="description" label="说明" min-width="160" show-overflow-tooltip />
          <el-table-column label="审批" width="90" align="center">
            <template #default="{ row }">
              <el-tag :type="row.approved ? 'success' : 'warning'" size="small">
                {{ row.approved ? '已审批' : '待审批' }}
              </el-tag>
            </template>
          </el-table-column>
        </el-table>
      </div>
      <template #footer>
        <el-button type="primary" @click="assetDetailVisible = false">关闭</el-button>
      </template>
    </el-dialog>

    <!-- ============ 费用记录详情对话框 ============ -->
    <el-dialog v-model="costDetailVisible" title="费用记录详情" width="620px" destroy-on-close>
      <el-descriptions :column="2" border size="small">
        <el-descriptions-item label="记录编号">
          <span class="code-cell">{{ costDetailRow.record_id }}</span>
        </el-descriptions-item>
        <el-descriptions-item label="资产编号">{{ costDetailRow.asset_id }}</el-descriptions-item>
        <el-descriptions-item label="费用类型">{{ costDetailRow.cost_type }}</el-descriptions-item>
        <el-descriptions-item label="金额">
          <span class="num-cell">{{ fmtMoney(costDetailRow.amount) }} 元</span>
        </el-descriptions-item>
        <el-descriptions-item label="所属片区">{{ costDetailRow.region || '-' }}</el-descriptions-item>
        <el-descriptions-item label="记录日期">{{ costDetailRow.record_date || '-' }}</el-descriptions-item>
        <el-descriptions-item label="审批状态">
          <el-tag :type="costDetailRow.approved ? 'success' : 'warning'" size="small">
            {{ costDetailRow.approved ? '已审批' : '待审批' }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="创建时间">{{ formatDateTime(costDetailRow.created_at) }}</el-descriptions-item>
        <el-descriptions-item label="费用说明" :span="2">{{ costDetailRow.description || '-' }}</el-descriptions-item>
      </el-descriptions>
      <template #footer>
        <el-button type="primary" @click="costDetailVisible = false">关闭</el-button>
      </template>
    </el-dialog>

    <!-- ============ LCC 详情对话框 ============ -->
    <el-dialog v-model="lccDetailVisible" title="LCC 全生命周期成本分析" width="860px" destroy-on-close>
      <div v-loading="lccDetailLoading">
        <el-descriptions :column="3" border size="small">
          <el-descriptions-item label="分析编号">
            <span class="code-cell">{{ lccDetail?.analysis_id }}</span>
          </el-descriptions-item>
          <el-descriptions-item label="项目名称" :span="2">{{ lccDetail?.project_name }}</el-descriptions-item>
          <el-descriptions-item label="设计寿命">{{ lccDetail?.design_life }} 年</el-descriptions-item>
          <el-descriptions-item label="折现率">{{ lccDetail?.discount_rate }}</el-descriptions-item>
          <el-descriptions-item label="推荐方案">
            <el-tag v-if="lccDetail?.recommended" type="success" size="small">
              {{ materialName(lccDetail.recommended) }}
            </el-tag>
            <span v-else>-</span>
          </el-descriptions-item>
        </el-descriptions>

        <header class="card-title asset-cost__section-title">
          <h3 class="card-title__text">方案比选（按 LCC 升序）</h3>
        </header>
        <el-table :data="lccOptions" class="app-table" size="small" empty-text="暂无比选方案">
          <el-table-column label="排名" width="70" align="center">
            <template #default="{ row, $index }">
              <span class="rank-cell" :class="{ 'rank-cell--top': (row.rank ?? $index + 1) <= 1 }">{{ row.rank ?? $index + 1 }}</span>
            </template>
          </el-table-column>
          <el-table-column label="材质方案" min-width="120">
            <template #default="{ row }">
              {{ row.material_name || materialName(row.material) }}
              <el-tag v-if="lccDetail?.recommended === row.material" type="success" size="small" class="lcc-rec-tag">推荐</el-tag>
            </template>
          </el-table-column>
          <el-table-column label="初始成本" align="right">
            <template #default="{ row }">{{ fmtMoney(row.initial_cost) }}</template>
          </el-table-column>
          <el-table-column label="年维护费" align="right">
            <template #default="{ row }">{{ fmtMoney(row.annual_maintenance) }}</template>
          </el-table-column>
          <el-table-column label="年能耗费" align="right">
            <template #default="{ row }">{{ fmtMoney(row.annual_energy) }}</template>
          </el-table-column>
          <el-table-column label="更换成本" align="right">
            <template #default="{ row }">{{ fmtMoney(row.replacement_cost) }}</template>
          </el-table-column>
          <el-table-column label="处置成本" align="right">
            <template #default="{ row }">{{ fmtMoney(row.disposal_cost) }}</template>
          </el-table-column>
          <el-table-column label="LCC总额" align="right">
            <template #default="{ row }"><span class="num-cell">{{ fmtMoney(row.total_lcc) }}</span></template>
          </el-table-column>
          <el-table-column label="NPV" align="right">
            <template #default="{ row }">{{ fmtMoney(row.npv) }}</template>
          </el-table-column>
        </el-table>
      </div>
      <template #footer>
        <el-button type="primary" @click="lccDetailVisible = false">关闭</el-button>
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
  getAssets, getAssetDetail, createAsset, deleteAsset, reviewAsset, getDepreciation,
  getCostRecords, createCostRecord, deleteCostRecord, reviewCostRecord,
  getCostAnalysis,
  getLccList, getLccDetail,
  getCategories, getMaterials, getRegions, getDeprMethods
} from '@/api/assetCost'

// ===================== 常量 =====================
const ASSET_STATUS_LIST = ['在用', '已审核', '已驳回', '已提足', '已报废']
const ASSET_STATUS_TYPE = {
  '在用': 'success',
  '已审核': 'success',
  '已驳回': 'danger',
  '已提足': 'warning',
  '已报废': 'info'
}
const COST_TYPES = ['日常运维', '定期维修', '应急维修', '技改更换', '能耗费用', '人工费用']

// Excel 导入表头映射（支持中英文列名）
const ASSET_IMPORT_MAP = {
  name: 'name', '资产名称': 'name', '名称': 'name',
  category: 'category', '类别': 'category', '资产类别': 'category',
  region: 'region', '区域': 'region', '片区': 'region', '所属片区': 'region',
  material: 'material', '材质': 'material',
  specs: 'specs', '规格': 'specs', '规格型号': 'specs',
  original_value: 'original_value', '原值': 'original_value', '资产原值': 'original_value',
  install_date: 'install_date', '安装日期': 'install_date', '启用日期': 'install_date',
  depr_method: 'depr_method', '折旧方法': 'depr_method',
  depr_years: 'depr_years', '折旧年限': 'depr_years',
  residual_rate: 'residual_rate', '残值率': 'residual_rate'
}
const COST_IMPORT_MAP = {
  asset_id: 'asset_id', '资产编号': 'asset_id', '资产ID': 'asset_id',
  cost_type: 'cost_type', '费用类型': 'cost_type', '类型': 'cost_type',
  amount: 'amount', '金额': 'amount', '费用金额': 'amount',
  description: 'description', '说明': 'description', '费用说明': 'description', '描述': 'description',
  region: 'region', '区域': 'region', '片区': 'region',
  record_date: 'record_date', '记录日期': 'record_date', '费用日期': 'record_date', '日期': 'record_date'
}

// ===================== 页面状态 =====================
const activeTab = ref('assets')
const overview = ref(null)

// 配置数据
const categories = ref({})
const materials = ref({})
const regions = ref([])
const deprMethods = ref({})

// 资产台账
const assetQuery = ref({ page: 1, page_size: 10, keyword: '', category: '', region: '', status: '' })
const assets = ref([])
const assetTotal = ref(0)
const assetLoading = ref(false)

// 费用记录
const costQuery = ref({ page: 1, page_size: 10, cost_type: '', region: '', approved: '' })
const costRecords = ref([])
const costTotal = ref(0)
const costLoading = ref(false)

// 成本分析
const analysis = ref(null)
const analysisLoading = ref(false)

// LCC 分析
const lccList = ref([])
const lccLoading = ref(false)
const lccDetail = ref(null)
const lccDetailVisible = ref(false)
const lccDetailLoading = ref(false)

// 导入导出
const importing = ref(false)
const exporting = ref(false)

// ===================== 头部按钮可见性 =====================
const canAdd = computed(() => ['assets', 'costs'].includes(activeTab.value))
const canImport = computed(() => ['assets', 'costs'].includes(activeTab.value))
const canExport = computed(() => ['assets', 'costs', 'lcc'].includes(activeTab.value))
const addButtonText = computed(() => (activeTab.value === 'assets' ? '新增资产' : '新增费用记录'))
const openAddDialog = () => {
  if (activeTab.value === 'assets') openAssetDialog(null)
  else if (activeTab.value === 'costs') openCostDialog(null)
}

// ===================== 统计卡片 =====================
const toWan = (v) => Math.round((Number(v) || 0) / 10000)
const originalValueWan = computed(() => toWan(overview.value?.total_original_value))
const annualCostWan = computed(() => toWan(overview.value?.total_annual_cost))
const deprPctText = computed(() => `${Number(overview.value?.overall_depr_pct ?? 0).toFixed(1)}%`)

// ===================== 格式化工具 =====================
const fmtMoney = (v) => Number(v ?? 0).toLocaleString('zh-CN', { maximumFractionDigits: 2 })
const fmtPct = (v) => `${Number(v ?? 0).toFixed(1)}%`
const assetStatusType = (s) => ASSET_STATUS_TYPE[s] || 'info'
const categoryName = (code) => categories.value[code]?.name || code || '-'
const materialName = (code) => materials.value[code]?.name || code || '-'
const deprMethodName = (code) => deprMethods.value[code] || code || '-'
const today = () => new Date().toISOString().slice(0, 10)
const normalizeDate = (v) => {
  if (!v) return ''
  if (v instanceof Date && !isNaN(v.getTime())) {
    return `${v.getFullYear()}-${String(v.getMonth() + 1).padStart(2, '0')}-${String(v.getDate()).padStart(2, '0')}`
  }
  return String(v).trim().slice(0, 10)
}

// ===================== 数据加载 =====================
const loadOverview = async () => {
  try {
    overview.value = await getOverview()
  } catch (e) {
    console.error('加载总览失败:', e)
  }
}

const loadConfig = async () => {
  try {
    const [c, m, r, d] = await Promise.all([getCategories(), getMaterials(), getRegions(), getDeprMethods()])
    categories.value = c || {}
    materials.value = m || {}
    regions.value = Array.isArray(r) ? r : (r?.regions || [])
    deprMethods.value = d || {}
  } catch (e) {
    console.error('加载配置失败:', e)
  }
}

const buildAssetParams = (override = {}) => {
  const q = assetQuery.value
  const params = { page: q.page, page_size: q.page_size, ...override }
  if (q.keyword) params.keyword = q.keyword
  if (q.category) params.category = q.category
  if (q.region) params.region = q.region
  if (q.status) params.status = q.status
  return params
}

const loadAssets = async () => {
  assetLoading.value = true
  try {
    const res = await getAssets(buildAssetParams())
    assets.value = res?.items || []
    assetTotal.value = res?.total || 0
  } catch (e) {
    ElMessage.error('加载资产列表失败')
    console.error('加载资产列表失败:', e)
  } finally {
    assetLoading.value = false
  }
}

const searchAssets = () => {
  assetQuery.value.page = 1
  loadAssets()
}

const resetAssetQuery = () => {
  assetQuery.value = { page: 1, page_size: 10, keyword: '', category: '', region: '', status: '' }
  loadAssets()
}

const buildCostParams = (override = {}) => {
  const q = costQuery.value
  const params = { page: q.page, page_size: q.page_size, ...override }
  if (q.cost_type) params.cost_type = q.cost_type
  if (q.region) params.region = q.region
  if (q.approved !== '' && q.approved !== null && q.approved !== undefined) params.approved = q.approved
  return params
}

const loadCosts = async () => {
  costLoading.value = true
  try {
    const res = await getCostRecords(buildCostParams())
    costRecords.value = res?.items || []
    costTotal.value = res?.total || 0
  } catch (e) {
    ElMessage.error('加载费用记录失败')
    console.error('加载费用记录失败:', e)
  } finally {
    costLoading.value = false
  }
}

const searchCosts = () => {
  costQuery.value.page = 1
  loadCosts()
}

const resetCostQuery = () => {
  costQuery.value = { page: 1, page_size: 10, cost_type: '', region: '', approved: '' }
  loadCosts()
}

const loadAnalysis = async () => {
  analysisLoading.value = true
  try {
    analysis.value = await getCostAnalysis()
  } catch (e) {
    ElMessage.error('加载成本分析失败')
    console.error('加载成本分析失败:', e)
  } finally {
    analysisLoading.value = false
  }
}

const loadLcc = async () => {
  lccLoading.value = true
  try {
    const res = await getLccList()
    lccList.value = Array.isArray(res) ? res : (res?.items || [])
  } catch (e) {
    ElMessage.error('加载LCC分析失败')
    console.error('加载LCC分析失败:', e)
  } finally {
    lccLoading.value = false
  }
}

const handleTabChange = (name) => {
  if (name === 'assets') loadAssets()
  else if (name === 'costs') loadCosts()
  else if (name === 'analysis') loadAnalysis()
  else if (name === 'lcc') loadLcc()
}

const refreshCurrentTab = () => {
  loadOverview()
  handleTabChange(activeTab.value)
}

// ===================== 成本分析计算 =====================
const byTypeRows = computed(() =>
  Object.entries(analysis.value?.by_type || {}).map(([type, v]) => ({ type, total: v?.total, count: v?.count }))
)
const byRegionRows = computed(() =>
  Object.entries(analysis.value?.by_region || {}).map(([region, v]) => ({ region, total: v?.total, count: v?.count }))
)
const trendRows = computed(() =>
  Object.entries(analysis.value?.monthly_trend || {})
    .map(([month, amount]) => ({ month, amount }))
    .sort((a, b) => a.month.localeCompare(b.month))
)
const trendMax = computed(() => Math.max(...trendRows.value.map(r => Number(r.amount) || 0), 1))
const trendBarPct = (amount) => `${Math.max(2, Math.round((Number(amount) || 0) / trendMax.value * 100))}%`

// ===================== LCC 详情 =====================
const lccOptions = computed(() =>
  [...(lccDetail.value?.options || [])].sort((a, b) => (Number(a.total_lcc) || 0) - (Number(b.total_lcc) || 0))
)

const openLccDetail = async (row) => {
  lccDetailVisible.value = true
  lccDetailLoading.value = true
  lccDetail.value = row
  try {
    lccDetail.value = await getLccDetail(row.analysis_id)
  } catch (e) {
    console.error('加载LCC详情失败:', e)
  } finally {
    lccDetailLoading.value = false
  }
}

// ===================== 资产新增/编辑 =====================
const assetDialogVisible = ref(false)
const assetIsEdit = ref(false)
const assetSubmitting = ref(false)
const assetFormRef = ref(null)
const editingAssetId = ref(null)

const defaultAssetForm = () => ({
  name: '',
  category: '',
  region: '',
  material: '',
  specs: '',
  original_value: 0,
  install_date: '',
  depr_method: 'STRAIGHT_LINE',
  depr_years: 10,
  residual_rate: 0.05
})
const assetForm = ref(defaultAssetForm())

const assetRules = {
  name: [{ required: true, message: '请输入资产名称', trigger: 'blur' }],
  category: [{ required: true, message: '请选择资产类别', trigger: 'change' }],
  region: [{ required: true, message: '请选择所属片区', trigger: 'change' }],
  material: [{ required: true, message: '请选择材质', trigger: 'change' }],
  original_value: [{ required: true, message: '请输入资产原值', trigger: 'blur' }]
}

// 选择类别后自动带出该类别的默认折旧年限/残值率
const onCategoryChange = (code) => {
  const cfg = categories.value[code]
  if (!cfg) return
  if (cfg.depr_years != null) assetForm.value.depr_years = cfg.depr_years
  if (cfg.residual_rate != null) assetForm.value.residual_rate = cfg.residual_rate
}

const openAssetDialog = (row) => {
  if (row) {
    assetIsEdit.value = true
    editingAssetId.value = row.asset_id
    assetForm.value = {
      name: row.name ?? '',
      category: row.category ?? '',
      region: row.region ?? '',
      material: row.material ?? '',
      specs: row.specs ?? '',
      original_value: Number(row.original_value) || 0,
      install_date: normalizeDate(row.install_date),
      depr_method: row.depr_method ?? 'STRAIGHT_LINE',
      depr_years: Number(row.depr_years) || 10,
      residual_rate: Number(row.residual_rate) || 0
    }
  } else {
    assetIsEdit.value = false
    editingAssetId.value = null
    assetForm.value = defaultAssetForm()
  }
  assetDialogVisible.value = true
}

const submitAsset = async () => {
  if (!assetFormRef.value) return
  try {
    await assetFormRef.value.validate()
  } catch {
    return
  }
  assetSubmitting.value = true
  try {
    const body = { ...assetForm.value }
    if (assetIsEdit.value) body.asset_id = editingAssetId.value
    await createAsset(body)
    ElMessage.success(assetIsEdit.value ? '保存成功' : '创建成功')
    assetDialogVisible.value = false
    loadAssets()
    loadOverview()
  } catch (e) {
    ElMessage.error(assetIsEdit.value ? '保存失败' : '创建失败')
    console.error('提交资产失败:', e)
  } finally {
    assetSubmitting.value = false
  }
}

// ===================== 资产详情 =====================
const assetDetailVisible = ref(false)
const assetDetailLoading = ref(false)
const assetDetail = ref(null)
const assetDepreciation = ref(null)

const detailAsset = computed(() => assetDetail.value?.asset ?? assetDetail.value ?? {})
const detailCostHistory = computed(() => assetDetail.value?.cost_history ?? [])
const detailTotalCost = computed(() => assetDetail.value?.total_cost ?? 0)

const openAssetDetail = async (row) => {
  assetDetailVisible.value = true
  assetDetailLoading.value = true
  assetDetail.value = null
  assetDepreciation.value = null
  try {
    const [detail, depr] = await Promise.all([
      getAssetDetail(row.asset_id),
      getDepreciation(row.asset_id).catch(() => null)
    ])
    assetDetail.value = detail
    assetDepreciation.value = depr
  } catch (e) {
    ElMessage.error('加载资产详情失败')
    console.error('加载资产详情失败:', e)
  } finally {
    assetDetailLoading.value = false
  }
}

// ===================== 资产审核 / 删除 =====================
const handleReviewAsset = async (row, approved) => {
  let comment = ''
  if (approved) {
    await reviewAsset(row.asset_id, true, '')
      .then(() => {
        ElMessage.success('审核通过')
        loadAssets()
        loadOverview()
      })
      .catch((e) => {
        ElMessage.error('审核操作失败')
        console.error(e)
      })
    return
  }
  try {
    const { value } = await ElMessageBox.prompt(`确认驳回资产「${row.name}」？`, '驳回审核', {
      confirmButtonText: '驳回',
      cancelButtonText: '取消',
      inputPlaceholder: '驳回原因（可选）',
      type: 'warning'
    })
    comment = value || ''
  } catch {
    return
  }
  try {
    await reviewAsset(row.asset_id, false, comment)
    ElMessage.success('已驳回')
    loadAssets()
    loadOverview()
  } catch (e) {
    ElMessage.error('审核操作失败')
    console.error(e)
  }
}

const handleDeleteAsset = (row) => {
  ElMessageBox.confirm(`确认删除资产「${row.name}」？删除后不可恢复。`, '删除确认', {
    confirmButtonText: '删除',
    cancelButtonText: '取消',
    type: 'warning'
  })
    .then(async () => {
      try {
        await deleteAsset(row.asset_id)
        ElMessage.success('删除成功')
        loadAssets()
        loadOverview()
      } catch (e) {
        ElMessage.error('删除失败')
        console.error(e)
      }
    })
    .catch(() => {})
}

// ===================== 费用记录新增/编辑 =====================
const costDialogVisible = ref(false)
const costIsEdit = ref(false)
const costSubmitting = ref(false)
const costFormRef = ref(null)
const editingCostId = ref(null)

const defaultCostForm = () => ({
  asset_id: '',
  cost_type: '日常运维',
  amount: 0,
  description: '',
  region: '',
  record_date: ''
})
const costForm = ref(defaultCostForm())

const costRules = {
  asset_id: [{ required: true, message: '请输入资产编号', trigger: 'blur' }],
  cost_type: [{ required: true, message: '请选择费用类型', trigger: 'change' }],
  amount: [{ required: true, message: '请输入金额', trigger: 'blur' }]
}

const openCostDialog = (row) => {
  if (row) {
    costIsEdit.value = true
    editingCostId.value = row.record_id
    costForm.value = {
      asset_id: row.asset_id ?? '',
      cost_type: row.cost_type ?? '日常运维',
      amount: Number(row.amount) || 0,
      description: row.description ?? '',
      region: row.region ?? '',
      record_date: normalizeDate(row.record_date)
    }
  } else {
    costIsEdit.value = false
    editingCostId.value = null
    costForm.value = defaultCostForm()
  }
  costDialogVisible.value = true
}

const submitCost = async () => {
  if (!costFormRef.value) return
  try {
    await costFormRef.value.validate()
  } catch {
    return
  }
  costSubmitting.value = true
  try {
    const body = { ...costForm.value }
    if (costIsEdit.value) body.record_id = editingCostId.value
    await createCostRecord(body)
    ElMessage.success(costIsEdit.value ? '保存成功' : '创建成功')
    costDialogVisible.value = false
    loadCosts()
    loadOverview()
  } catch (e) {
    ElMessage.error(costIsEdit.value ? '保存失败' : '创建失败')
    console.error('提交费用记录失败:', e)
  } finally {
    costSubmitting.value = false
  }
}

// ===================== 费用详情 / 审批 / 删除 =====================
const costDetailVisible = ref(false)
const costDetailRow = ref({})

const openCostDetail = (row) => {
  costDetailRow.value = row
  costDetailVisible.value = true
}

const handleReviewCost = async (row, approved) => {
  if (!approved) {
    try {
      await ElMessageBox.confirm(`确认驳回该笔「${row.cost_type}」费用？`, '驳回确认', {
        confirmButtonText: '驳回',
        cancelButtonText: '取消',
        type: 'warning'
      })
    } catch {
      return
    }
  }
  try {
    await reviewCostRecord(row.record_id, approved)
    ElMessage.success(approved ? '已审批通过' : '已驳回')
    loadCosts()
    loadOverview()
  } catch (e) {
    ElMessage.error('审批操作失败')
    console.error(e)
  }
}

const handleDeleteCost = (row) => {
  ElMessageBox.confirm(`确认删除费用记录「${row.record_id}」？删除后不可恢复。`, '删除确认', {
    confirmButtonText: '删除',
    cancelButtonText: '取消',
    type: 'warning'
  })
    .then(async () => {
      try {
        await deleteCostRecord(row.record_id)
        ElMessage.success('删除成功')
        loadCosts()
        loadOverview()
      } catch (e) {
        ElMessage.error('删除失败')
        console.error(e)
      }
    })
    .catch(() => {})
}

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

const handleExport = async () => {
  exporting.value = true
  try {
    if (activeTab.value === 'assets') {
      const res = await getAssets(buildAssetParams({ page: 1, page_size: 10000 }))
      const rows = (res?.items || []).map(i => ({
        资产编号: i.asset_id,
        资产名称: i.name,
        类别: i.category_name || categoryName(i.category),
        片区: i.region,
        材质: i.material_name || materialName(i.material),
        规格: i.specs,
        资产原值: i.original_value,
        安装日期: i.install_date,
        折旧方法: deprMethodName(i.depr_method),
        折旧年限: i.depr_years,
        残值率: i.residual_rate,
        状态: i.status,
        累计折旧: i.accumulated_depr,
        年折旧额: i.annual_depr,
        净值: i.net_value,
        已使用年数: i.years_elapsed,
        折旧率: i.depr_pct
      }))
      exportExcel(rows, `资产台账_${today()}.xlsx`)
    } else if (activeTab.value === 'costs') {
      const res = await getCostRecords(buildCostParams({ page: 1, page_size: 10000 }))
      const rows = (res?.items || []).map(i => ({
        记录编号: i.record_id,
        资产编号: i.asset_id,
        费用类型: i.cost_type,
        金额: i.amount,
        费用说明: i.description,
        片区: i.region,
        记录日期: i.record_date,
        审批状态: i.approved ? '已审批' : '待审批',
        创建时间: formatDateTime(i.created_at)
      }))
      exportExcel(rows, `费用记录_${today()}.xlsx`)
    } else if (activeTab.value === 'lcc') {
      const rows = lccList.value.map(i => ({
        分析编号: i.analysis_id,
        项目名称: i.project_name,
        设计寿命: i.design_life,
        折现率: i.discount_rate,
        推荐方案: materialName(i.recommended),
        方案数: (i.options || []).length,
        创建时间: formatDateTime(i.created_at)
      }))
      exportExcel(rows, `LCC分析_${today()}.xlsx`)
    }
  } catch (e) {
    ElMessage.error('导出失败')
    console.error('导出失败:', e)
  } finally {
    exporting.value = false
  }
}

// ===================== Excel 导入 =====================
// 按映射字典将任意表头行转换为标准字段
const mapImportRow = (row, dict) => {
  const out = {}
  for (const [k, v] of Object.entries(row)) {
    const raw = String(k).trim()
    const key = dict[raw] || dict[raw.toLowerCase()]
    if (key) out[key] = v
  }
  return out
}

// 类别/材质编码解析：支持直接填编码或中文名称
const lookupCode = (dict, val) => {
  const v = String(val ?? '').trim()
  if (!v) return ''
  if (dict[v]) return v
  const hit = Object.entries(dict).find(([, cfg]) => cfg?.name === v)
  return hit ? hit[0] : v
}

// 折旧方法解析：支持编码或中文名
const lookupDeprMethod = (val) => {
  const v = String(val ?? '').trim()
  if (!v) return 'STRAIGHT_LINE'
  if (deprMethods.value[v]) return v
  const hit = Object.entries(deprMethods.value).find(([, name]) => name === v)
  return hit ? hit[0] : v
}

const toAssetBody = (r) => {
  const body = {
    name: String(r.name ?? '').trim(),
    category: lookupCode(categories.value, r.category),
    region: String(r.region ?? '').trim(),
    material: lookupCode(materials.value, r.material),
    specs: String(r.specs ?? ''),
    original_value: Number(r.original_value) || 0,
    install_date: normalizeDate(r.install_date),
    depr_method: lookupDeprMethod(r.depr_method)
  }
  if (r.depr_years !== '' && r.depr_years != null) body.depr_years = Number(r.depr_years)
  if (r.residual_rate !== '' && r.residual_rate != null) body.residual_rate = Number(r.residual_rate)
  return body
}

const toCostBody = (r) => ({
  asset_id: String(r.asset_id ?? '').trim(),
  cost_type: String(r.cost_type ?? '').trim() || '日常运维',
  amount: Number(r.amount) || 0,
  description: String(r.description ?? ''),
  region: String(r.region ?? '').trim(),
  record_date: normalizeDate(r.record_date)
})

const handleImport = ({ file }) => {
  const isAsset = activeTab.value === 'assets'
  if (!isAsset && activeTab.value !== 'costs') return
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
        .map(r => (isAsset ? toAssetBody(mapImportRow(r, ASSET_IMPORT_MAP)) : toCostBody(mapImportRow(r, COST_IMPORT_MAP))))
        .filter(b => (isAsset ? !!b.name : !!b.asset_id))
      if (!bodies.length) {
        ElMessage.warning('未识别到有效数据行，请确认表头包含"资产名称/名称"或"资产编号"等列')
        return
      }
      importing.value = true
      let ok = 0
      let fail = 0
      for (const body of bodies) {
        try {
          if (isAsset) await createAsset(body)
          else await createCostRecord(body)
          ok += 1
        } catch {
          fail += 1
        }
      }
      ElMessage.success(`导入完成：成功 ${ok} 条${fail ? `，失败 ${fail} 条` : ''}`)
      if (isAsset) loadAssets()
      else loadCosts()
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
  loadConfig()
  loadOverview()
  loadAssets()
})
</script>

<style scoped>
.asset-cost__stats {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
  margin-bottom: 16px;
}
.asset-cost__main {
  padding: 16px 24px 24px;
}
.asset-cost__filter {
  margin-bottom: 16px;
}
.asset-cost__filter-item {
  width: 160px;
}
.asset-cost__pagination {
  display: flex;
  justify-content: flex-end;
  margin-top: 16px;
}
.asset-cost__upload {
  display: inline-flex;
}
.asset-cost__section-title {
  margin-top: 20px;
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
.lcc-rec-tag {
  margin-left: 6px;
}

/* 成本分析面板 */
.analysis-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
}
.analysis-panel {
  background: rgba(255, 255, 255, 0.6);
  border: 1px solid var(--app-border);
  border-radius: var(--app-radius-control);
  padding: 16px 20px;
  box-sizing: border-box;
}
.trend-bar {
  width: 100%;
  height: 8px;
  border-radius: 4px;
  background-color: var(--app-hover);
  overflow: hidden;
}
.trend-bar__fill {
  height: 100%;
  border-radius: 4px;
  background: linear-gradient(90deg, rgba(0, 113, 227, 0.4), var(--app-primary));
  transition: width 0.4s cubic-bezier(0.4, 0, 0.2, 1);
}

@media (max-width: 1024px) {
  .asset-cost__stats { grid-template-columns: repeat(2, 1fr); }
  .analysis-grid { grid-template-columns: 1fr; }
}
</style>
