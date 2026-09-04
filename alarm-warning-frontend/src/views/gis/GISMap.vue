<template>
  <div class="gis-page">
    <!-- ===================== 顶部工具栏 ===================== -->
    <header class="gis-toolbar">
      <div class="gis-toolbar__main">
        <el-input
          v-model="keyword"
          class="gis-toolbar__search"
          placeholder="搜索地点 / 管线 / 设备 / 预警编号"
          clearable
          :prefix-icon="Search"
          @keyup.enter="onSearch"
          @clear="onSearch"
          @focus="onSearchFocus"
        />

        <!-- 搜索建议下拉 -->
        <div v-if="searchSuggestions.length > 0 && keyword" class="gis-suggestions">
          <div
            v-for="(item, idx) in searchSuggestions"
            :key="idx"
            class="gis-suggestion-item"
            @click="selectSuggestion(item)"
          >
            <span class="gis-suggestion-title">{{ item.name }}</span>
            <span v-if="item.address" class="gis-suggestion-addr">{{ item.address }}</span>
          </div>
        </div>

        <el-select v-model="areaFilter" class="gis-toolbar__select" placeholder="区域筛选">
          <el-option label="全部区域" value="" />
          <el-option v-for="a in areaOptions" :key="a" :label="a" :value="a" />
        </el-select>
        <el-select v-model="riskFilter" class="gis-toolbar__select" placeholder="风险等级">
          <el-option label="全部风险等级" value="" />
          <el-option v-for="r in RISK_OPTIONS" :key="r.value" :label="r.label" :value="r.value" />
        </el-select>
        <el-select v-model="statusFilter" class="gis-toolbar__select" placeholder="状态筛选">
          <el-option label="全部状态" value="" />
          <el-option v-for="s in STATUS_OPTIONS" :key="s.value" :label="s.label" :value="s.value" />
        </el-select>
        <el-button class="gis-toolbar__btn" :icon="Refresh" :loading="loading" @click="reload">
          刷新
        </el-button>
        <el-button class="gis-toolbar__btn" :icon="Position" @click="startNavigate" title="路线导航">
          导航
        </el-button>
      </div>

      <div class="gis-toolbar__meta">
        <span class="gis-meta__item">安塞区城市生命线安全监测</span>
        <span class="gis-meta__divider"></span>
        <span class="gis-meta__item">最后刷新 {{ updatedAt || '--:--:--' }}</span>
      </div>

      <!-- 移动端：精简为三个图标按钮 -->
      <div class="gis-toolbar__mobile">
        <el-button :icon="Search" circle @click="mobileSearch = !mobileSearch" />
        <el-button :icon="Filter" circle @click="mobileFilter = true" />
        <el-button :icon="Files" circle @click="mobileLayers = true" />
      </div>
    </header>

    <!-- 移动端搜索行 -->
    <div v-if="mobileSearch" class="gis-searchrow">
      <el-input
        v-model="keyword"
        placeholder="搜索地点 / 管线 / 设备 / 预警编号"
        clearable
        :prefix-icon="Search"
        @keyup.enter="onSearch(); mobileSearch = false"
        @clear="onSearch"
      />
    </div>

    <!-- ===================== 主体：图层树 + 地图 ===================== -->
    <div class="gis-body" :class="{ 'is-collapsed': panelCollapsed }">
      <aside class="gis-panel">
        <div class="gis-panel__head">
          <span class="gis-panel__title">图层</span>
          <span class="gis-panel__total">{{ totalFeatures }} 个要素</span>
          <el-button
            class="gis-panel__toggle"
            link
            :icon="DArrowLeft"
            title="折叠图层面板"
            @click="togglePanel"
          />
        </div>
        <div class="gis-panel__body">
          <LayerTree :layers="layerView" @toggle="onToggleLayer" />
        </div>
      </aside>

      <main class="gis-workspace">
        <div class="gis-stage">
          <div class="gis-mapwrap">
        <!-- 百度地图容器 -->
        <div ref="mapEl" class="gis-map"></div>

        <!-- 右上角自定义控件组：回到安塞区 + 缩放 + 地图类型 -->
        <div class="gis-map-controls">
          <button class="gis-home-btn" type="button" title="回到安塞区检测区域" @click="fitToAnsei(14)">
            <!-- 中心定位图标（同心圆 + 十字） -->
            <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
              <circle cx="8" cy="8" r="6.2" stroke="currentColor" stroke-width="1.4"/>
              <circle cx="8" cy="8" r="1.6" fill="currentColor"/>
              <line x1="8" y1="0.6" x2="8" y2="3.4" stroke="currentColor" stroke-width="1.4" stroke-linecap="round"/>
              <line x1="8" y1="12.6" x2="8" y2="15.4" stroke="currentColor" stroke-width="1.4" stroke-linecap="round"/>
              <line x1="0.6" y1="8" x2="3.4" y2="8" stroke="currentColor" stroke-width="1.4" stroke-linecap="round"/>
              <line x1="12.6" y1="8" x2="15.4" y2="8" stroke="currentColor" stroke-width="1.4" stroke-linecap="round"/>
            </svg>
          </button>
          <div class="gis-zoom-group">
            <button class="gis-zoom-btn" type="button" title="放大" @click="zoomIn">
              <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
                <path d="M8 3v10M3 8h10" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"/>
              </svg>
            </button>
            <div class="gis-zoom-divider"></div>
            <button class="gis-zoom-btn" type="button" title="缩小" @click="zoomOut">
              <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
                <path d="M3 8h10" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"/>
              </svg>
            </button>
          </div>
          <el-dropdown trigger="click" @command="changeMapType" class="gis-maptype-dropdown">
            <button class="gis-maptype-btn" type="button">
              <span>{{ mapTypeLabel }}</span>
              <el-icon :size="12"><svg viewBox="0 0 1024 1024" width="14" height="14"><path d="M512 666.667c-8.533 0-17.067-2.134-24.533-8.534l-384-362.666c-14.934-14.934-14.934-38.4 0-53.334 14.933-14.933 38.4-14.933 53.333 0L512 618.667l355.2-376.534c14.933-14.933 38.4-14.933 53.333 0 14.934 14.934 14.934 38.4 0 53.334l-384 362.666C529.067 664.533 520.533 666.667 512 666.667z" fill="currentColor"/></svg></el-icon>
            </button>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="normal">标准地图</el-dropdown-item>
                <el-dropdown-item command="satellite">卫星图</el-dropdown-item>
                <el-dropdown-item command="hybrid">混合图</el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>

        <!-- 面板折叠后的展开把手 -->
        <button
          v-show="panelCollapsed"
          class="gis-fab gis-fab--panel"
          type="button"
          title="展开图层面板"
          @click="togglePanel"
        >
          <el-icon :size="15"><DArrowRight /></el-icon>
          <span>图层</span>
        </button>

        <!-- 路线导航浮层 -->
        <div v-if="navMode" class="gis-nav-box">
          <div class="gis-nav-box__head">
            <span class="gis-nav-box__title">路线导航（驾车）</span>
            <el-button link :icon="Close" class="gis-nav-box__close" @click="cancelNavigate" />
          </div>
          <div class="gis-nav-box__body">
            <el-input
              v-model="navStart"
              placeholder="起点（点击地图自动填入，或手动输入）"
              size="small"
              :prefix-icon="Location"
              readonly
            />
            <div class="gis-nav-box__arrow"><el-icon><Top /></el-icon></div>
            <el-input
              v-model="navEnd"
              placeholder="终点（点击地图自动填入，或手动输入）"
              size="small"
              :prefix-icon="Location"
              readonly
            />
            <el-button type="primary" size="small" class="gis-nav-box__go" @click="doNavigate">
              规划路线
            </el-button>
            <el-button size="small" @click="clearRouteOverlay">清除路线</el-button>
          </div>
          <div v-if="navResult" class="gis-nav-box__result">
            <span>距离：<b>{{ navResult.distance }}</b></span>
            <span>用时：<b>{{ navResult.duration }}</b></span>
          </div>
        </div>

        <!-- 加载态 -->
        <div v-if="loading" class="gis-state">
          <el-icon class="is-loading" :size="20"><Loading /></el-icon>
          <span>正在加载 GIS 数据…</span>
        </div>

        <!-- 失败态 -->
        <div v-else-if="loadError" class="gis-state gis-state--error">
          <el-icon :size="20"><WarningFilled /></el-icon>
          <span>{{ loadError }}</span>
          <el-button size="small" type="primary" plain @click="reload">重试</el-button>
        </div>

        <!-- 空数据态 -->
        <div v-else-if="!loading && totalFeatures === 0" class="gis-state">
          <el-icon :size="20"><Aim /></el-icon>
          <span>当前筛选条件下没有可定位的要素</span>
          <el-button size="small" plain @click="resetFilters">重置筛选</el-button>
        </div>

        <div v-else-if="!loading && anseiPointCount === 0" class="gis-state gis-state--notice">
          <el-icon :size="18"><Aim /></el-icon>
          <span>安塞区范围内暂无风险或设备坐标</span>
        </div>

        <!-- 左下角图例：管线类型 + 风险等级 两张卡片 -->
        <div class="gis-legend">
          <div class="gis-legend__group">
            <div class="gis-legend__title">管线类型</div>
            <span
              v-for="cfg in GIS_LAYERS.filter(l => l.geometry === 'line')"
              :key="'type-' + cfg.key"
              class="gis-legend__item"
            >
              <span class="gis-legend__line" :style="{ background: cfg.color }"></span>
              {{ cfg.label }}
            </span>
          </div>
          <div class="gis-legend__divider"></div>
          <div class="gis-legend__group">
            <div class="gis-legend__title">风险等级</div>
            <span
              v-for="s in riskLegendItems"
              :key="'risk-' + s.key"
              class="gis-legend__item"
            >
              <i class="gis-legend__dot" :style="{ background: s.color }"></i>
              {{ s.label }}
            </span>
          </div>
        </div>
          </div>

          <GISBusinessPanel
            :alarms="recentAlarms"
            :today-count="todayAlarmCount"
            :risk-items="riskDistribution"
            :online="deviceOnline"
            @locate="locateAlarm"
          />
        </div>

        <GISMetrics :items="metricItems" />
      </main>
    </div>

    <!-- ===================== 要素详情抽屉（桌面右侧 / 移动底部） ===================== -->
    <el-drawer
      v-model="drawerVisible"
      class="gis-drawer"
      :direction="isMobile ? 'btt' : 'rtl'"
      :size="isMobile ? '62vh' : '360px'"
      :with-header="false"
      :z-index="2000"
      @closed="onDrawerClosed"
    >
      <div v-if="selected" class="gis-detail">
        <header class="gis-detail__head">
          <span class="gis-detail__swatch" :style="{ background: selected.cfg.color }"></span>
          <div class="gis-detail__titles">
            <h3 class="gis-detail__title">{{ selected.title }}</h3>
            <p class="gis-detail__sub">{{ selected.cfg.label }} · {{ selected.area }}</p>
          </div>
          <el-button link :icon="Close" class="gis-detail__close" @click="drawerVisible = false" />
        </header>

        <div class="gis-detail__body">
          <span
            class="gis-detail__status"
            :style="{ color: statusMeta.color, background: `${statusMeta.color}14` }"
          >{{ statusMeta.label }}</span>

          <dl class="gis-detail__list">
            <div v-for="row in detailRows" :key="row.label" class="gis-detail__row">
              <dt>{{ row.label }}</dt>
              <dd :style="row.color ? { color: row.color, fontWeight: 600 } : null">
                {{ row.value }}<em v-if="row.unit"> {{ row.unit }}</em>
              </dd>
            </div>
          </dl>

          <div v-if="selected.latlng" class="gis-detail__actions">
            <el-button size="small" :icon="Position" @click="navigateFromSelected">从这里出发</el-button>
            <el-button
              v-if="selectedEmergencyEligible"
              size="small"
              type="danger"
              plain
              :loading="emergencyLoading"
              @click="startEmergencyAnalysis"
            >应急推演</el-button>
          </div>

          <section v-if="emergencyActive" class="emergency-panel">
            <div class="emergency-panel__title">
              <strong>应急处置辅助</strong>
              <el-tag size="small" type="danger" effect="plain">影响半径 {{ impactRadius }}m</el-tag>
            </div>

            <div class="emergency-kpis">
              <div><b>{{ impactedDevices.length }}</b><span>影响设备</span></div>
              <div><b>{{ nearestTeam?.name || '--' }}</b><span>推荐队伍</span></div>
            </div>

            <p v-if="nearestTeam" class="emergency-team">
              {{ nearestTeam.status_name }} · {{ nearestTeam.location }} ·
              {{ nearestTeam.distance_m }}m · 匹配度 {{ nearestTeam.total_score }}
            </p>

            <div class="emergency-actions">
              <el-button size="small" @click="focusImpactArea">查看影响圈</el-button>
              <el-button
                size="small"
                type="primary"
                :loading="aiLoading"
                @click="generateAiPlan"
              >AI 处置方案</el-button>
              <el-button
                size="small"
                type="success"
                :disabled="!!createdOrder"
                :loading="orderLoading"
                @click="createEmergencyOrder"
              >{{ createdOrder ? createdOrder.order_id : '一键生成工单' }}</el-button>
            </div>

            <div v-if="aiPlan" class="emergency-plan">{{ aiPlan }}</div>

            <el-timeline v-if="emergencyTimeline.length" class="emergency-timeline">
              <el-timeline-item
                v-for="(item, index) in emergencyTimeline"
                :key="`${item.at}-${index}`"
                :timestamp="item.at"
                placement="top"
                size="small"
                :type="index === emergencyTimeline.length - 1 ? 'primary' : ''"
              >
                <b>{{ item.step_name }}</b>
                <p>{{ item.note }}</p>
              </el-timeline-item>
            </el-timeline>
          </section>
        </div>

        <footer class="gis-detail__foot">
          <el-button type="primary" class="gis-detail__go" @click="goModule">
            {{ selected.cfg.routeLabel }}
          </el-button>
        </footer>
      </div>
    </el-drawer>

    <!-- ===================== 移动端：图层抽屉 ===================== -->
    <el-drawer
      v-model="mobileLayers"
      class="gis-drawer"
      direction="btt"
      size="60vh"
      title="图层控制"
      :z-index="2000"
    >
      <LayerTree :layers="layerView" @toggle="onToggleLayer" />
    </el-drawer>

    <!-- ===================== 移动端：筛选抽屉 ===================== -->
    <el-drawer
      v-model="mobileFilter"
      class="gis-drawer"
      direction="btt"
      size="55vh"
      title="筛选条件"
      :z-index="2000"
    >
      <div class="gis-filter-sheet">
        <label class="gis-filter-sheet__label">区域</label>
        <el-select v-model="areaFilter" placeholder="全部区域">
          <el-option label="全部区域" value="" />
          <el-option v-for="a in areaOptions" :key="a" :label="a" :value="a" />
        </el-select>

        <label class="gis-filter-sheet__label">风险等级</label>
        <el-select v-model="riskFilter" placeholder="全部风险等级">
          <el-option label="全部风险等级" value="" />
          <el-option v-for="r in RISK_OPTIONS" :key="r.value" :label="r.label" :value="r.value" />
        </el-select>

        <label class="gis-filter-sheet__label">状态</label>
        <el-select v-model="statusFilter" placeholder="全部状态">
          <el-option label="全部状态" value="" />
          <el-option v-for="s in STATUS_OPTIONS" :key="s.value" :label="s.label" :value="s.value" />
        </el-select>

        <div class="gis-filter-sheet__actions">
          <el-button plain @click="resetFilters">重置</el-button>
          <el-button type="primary" @click="mobileFilter = false">完成</el-button>
        </div>
      </div>
    </el-drawer>
  </div>
</template>

<script setup>
import { ref, reactive, computed, nextTick, onMounted, onBeforeUnmount, onActivated, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import {
  Search, Refresh, Filter, Files, Close,
  DArrowLeft, DArrowRight, Loading, WarningFilled, Aim,
  Position, Location, Top
} from '@element-plus/icons-vue'
import LayerTree from './LayerTree.vue'
import GISBusinessPanel from './GISBusinessPanel.vue'
import GISMetrics from './GISMetrics.vue'
import { fetchAllLayers } from '@/api/gis'
import {
  GIS_LAYERS, LAYER_MAP, ANSAI_CENTER, ANSAI_BOUNDS,
  AREAS, STATUS_OPTIONS, RISK_LEVELS, RISK_OPTIONS, riskLevelOf, toneColor
} from '@/config/gisLayers'
import { waitBMap, buildMarkerIcon, buildClusterIcon, buildDotIcon } from '@/utils/baidumap'
import { searchPlace as backendSearchPlace, convertCoords, planDriving as backendPlanDriving } from '@/api/baiduMap'
import { sendChat } from '@/api/assistant'
import { createOrder, getDispatchRecommend, assignOrder, getProcess } from '@/api/workOrder'

const router = useRouter()
const route = useRoute()

// ---------------------------------------------------------------------------
// 状态
// ---------------------------------------------------------------------------
const mapEl = ref(null)

const loading = ref(false)
const loadError = ref('')
const updatedAt = ref('')

const keyword = ref('')
const appliedKeyword = ref('')
const areaFilter = ref('')
const riskFilter = ref('')
const statusFilter = ref('')

const panelCollapsed = ref(false)
const drawerVisible = ref(false)
const selected = ref(null)
const emergencyActive = ref(false)
const emergencyLoading = ref(false)
const aiLoading = ref(false)
const orderLoading = ref(false)
const impactedDevices = ref([])
const nearestTeam = ref(null)
const aiPlan = ref('')
const createdOrder = ref(null)
const emergencyEvents = ref([])
const orderTimeline = ref([])

const isMobile = ref(false)
const mobileSearch = ref(false)
const mobileLayers = ref(false)
const mobileFilter = ref(false)

// 搜索建议
const searchSuggestions = ref([])
let suggestTimer = null

// 路线导航
const navMode = ref(false)      // 是否在导航模式
const navStart = ref('')        // 起点描述（仅展示）
const navEnd = ref('')          // 终点描述（仅展示）
const navStartPoint = ref(null) // BMap.Point
const navEndPoint = ref(null)   // BMap.Point
const navResult = ref(null)     // { distance, duration }
let drivingRoute = null         // BMap.DrivingRoute 实例，用于清除

/** 图层开关与要素计数 */
// 管网数据保留，但进入页面时默认关闭；风险、告警和设施点位优先成为主视觉。
const visible = reactive(Object.fromEntries(GIS_LAYERS.map((l) => [l.key, l.geometry !== 'line'])))
const counts = reactive(Object.fromEntries(GIS_LAYERS.map((l) => [l.key, 0])))
const sources = reactive({})
const records = reactive({})
/** 数据通道附带的汇总口径（演示模式来自 GIS_DEMO_DATA.summary，真实接口为 null）。 */
const demoSummary = ref(null)

// ---------------------------------------------------------------------------
// 百度地图运行时对象（非响应式）
// ---------------------------------------------------------------------------

let BMap = null               // 百度地图 SDK 命名空间
let map = null                // BMap.Map 实例
let resizeObserver = null
let viewportQuery = null
let viewportHandler = null

// 覆盖物管理：所有覆盖物按 key 分组，支持整体显隐
const overlayMap = {}         // key -> Array<{ overlay, feature, cfg, props, bdCoords }>
const collections = {}        // key -> GeoJSON.FeatureCollection（全量）
const rendered = {}           // key -> 已渲染要素索引

let clusterMarkers = []       // 聚合覆盖物
let networkNodes = []         // 网络节点覆盖物
let highlightOverlay = null   // 当前选中高亮覆盖物
let selectedOverlay = null    // 选中描边覆盖物
let impactCircleOverlay = null // 当前告警影响范围

// ---------------------------------------------------------------------------
// 视野控制：默认聚焦安塞区检测区域
// ---------------------------------------------------------------------------

/** 是否是首次进入（true 时 renderAll 后自动 fitBounds） */
let firstEntry = true

/** 默认视野只采集安塞区内可定位的风险、告警与设施点，不让隐藏管线拉远视野。 */
function collectBusinessBounds() {
  let minLng = Infinity, maxLng = -Infinity
  let minLat = Infinity, maxLat = -Infinity
  let hasAny = false

  for (const key of ['alert', 'hazard', 'asset', 'manhole']) {
    if (!visible[key]) continue
    const items = overlayMap[key] || []
    for (const item of items) {
      const bdCoords = item.bdCoords
      const raw = item.feature?.geometry?.coordinates
      if (!Array.isArray(bdCoords) || Array.isArray(bdCoords[0]) || !Array.isArray(raw)) continue
      const [rawLng, rawLat] = raw.map(Number)
      // 后端若返回其他城市的种子数据，不把安塞区默认视野拉到外地。
      if (rawLng < ANSAI_BOUNDS.west - 0.03 || rawLng > ANSAI_BOUNDS.east + 0.03 ||
          rawLat < ANSAI_BOUNDS.south - 0.03 || rawLat > ANSAI_BOUNDS.north + 0.03) continue
      const [lng, lat] = bdCoords.map(Number)
      if (!Number.isFinite(lng) || !Number.isFinite(lat)) continue
      if (lng < minLng) minLng = lng
      if (lng > maxLng) maxLng = lng
      if (lat < minLat) minLat = lat
      if (lat > maxLat) maxLat = lat
      hasAny = true
    }
  }

  if (!hasAny) return null
  return { minLng, maxLng, minLat, maxLat }
}

/** 聚焦安塞区主要风险点与监测点；没有安塞区坐标时回到行政区中心。 */
function fitToAnsei(maxZoom = 14) {
  if (!map) return false

  const bounds = collectBusinessBounds()
  if (!bounds) {
    const center = new BMap.Point(ANSAI_CENTER[1], ANSAI_CENTER[0])
    map.centerAndZoom(center, 13)
    return false
  }

  const w = bounds.maxLng - bounds.minLng
  const h = bounds.maxLat - bounds.minLat
  if (w < 0.0001 && h < 0.0001) {
    map.centerAndZoom(new BMap.Point(bounds.minLng, bounds.minLat), Math.min(maxZoom, 15))
    return true
  }
  const padLng = Math.max(w * 0.28, 0.006)
  const padLat = Math.max(h * 0.28, 0.006)
  const sw = new BMap.Point(bounds.minLng - padLng, bounds.minLat - padLat)
  const ne = new BMap.Point(bounds.maxLng + padLng, bounds.maxLat + padLat)
  const paddedBounds = new BMap.Bounds(sw, ne)

  try {
    map.setViewport(paddedBounds, { zoomFactor: 0, enableAnimation: true })
    const currentZoom = map.getZoom()
    if (currentZoom > maxZoom) {
      map.setZoom(maxZoom)
    }
    return true
  } catch (e) {
    console.warn('[BMap] setViewport 失败，降级 centerAndZoom:', e?.message)
    const center = paddedBounds.getCenter()
    map.centerAndZoom(center, 13)
    return false
  }
}

/**
 * 地图容器 resize + 重新聚焦视野。
 * 从其他页面切回 /gis 时调用，确保容器尺寸变化后地图正确刷新。
 */
function refreshMapAfterActivate() {
  if (!map || !mapEl.value) return
  nextTick(() => {
    setTimeout(() => {
      // BMap v3.0 没有 invalidateSize()，用 DOM 重置 + 重新设置 center/zoom 触发重绘
      try { map.checkResize?.() } catch { /* noop */ }
      // 用 setViewport 再次聚焦（同时刷新容器尺寸）
      fitToAnsei(14)
    }, 120)
  })
}

// ---------------------------------------------------------------------------
// 派生数据
// ---------------------------------------------------------------------------
const layerView = computed(() =>
  GIS_LAYERS.map((cfg) => ({
    key: cfg.key,
    label: cfg.label,
    group: cfg.group,
    geometry: cfg.geometry,
    color: cfg.color,
    visible: visible[cfg.key],
    count: counts[cfg.key]
  }))
)

const totalFeatures = computed(() =>
  GIS_LAYERS.reduce((sum, cfg) => sum + (counts[cfg.key] || 0), 0)
)

const anseiPointCount = computed(() => ['alert', 'hazard', 'asset', 'manhole'].reduce((sum, key) => {
  const count = (collections[key]?.features || []).filter((feature) => {
    const [lng, lat] = feature.geometry?.coordinates || []
    return Number(lng) >= ANSAI_BOUNDS.west - 0.03 && Number(lng) <= ANSAI_BOUNDS.east + 0.03 &&
      Number(lat) >= ANSAI_BOUNDS.south - 0.03 && Number(lat) <= ANSAI_BOUNDS.north + 0.03
  }).length
  return sum + count
}, 0))

const areaOptions = computed(() => {
  const dynamic = GIS_LAYERS.flatMap((cfg) =>
    (collections[cfg.key]?.features || []).map((feature) => feature.properties?._area).filter(Boolean)
  )
  return [...new Set([...AREAS, ...dynamic])]
})

const riskLegendItems = computed(() => ['high', 'elevated', 'medium', 'low'].map((key) => RISK_LEVELS[key]))

const statusMeta = computed(() =>
  (selected.value ? RISK_LEVELS[selected.value.risk] : null) || RISK_LEVELS.normal
)

// ---------------------------------------------------------------------------
// 详情字段
// ---------------------------------------------------------------------------
function pickValue(props, propList) {
  for (const key of propList) {
    const value = props[key]
    if (value !== undefined && value !== null && value !== '') return value
  }
  return null
}

const detailRows = computed(() => {
  const sel = selected.value
  if (!sel) return []
  const rows = []
  for (const field of sel.cfg.fields) {
    const keys = Array.isArray(field.prop) ? field.prop : [field.prop]
    const raw = pickValue(sel.properties, keys)
    if (raw === null) continue
    const value = typeof raw === 'object' ? JSON.stringify(raw) : String(raw)
    rows.push({
      label: field.label,
      value,
      unit: field.unit || '',
      color: field.tone ? toneColor(value) : null
    })
  }
  rows.push({ label: '所属片区', value: sel.area, unit: '', color: null })
  const coord = sel.sourceCoords || sel.latlng
  if (coord) {
    rows.push({
      label: '坐标 (经纬度)',
      value: `${Number(coord[0]).toFixed(5)}, ${Number(coord[1]).toFixed(5)}`,
      unit: '',
      color: null
    })
  }
  return rows
})

const selectedEmergencyEligible = computed(() => {
  const sel = selected.value
  return !!sel?.latlng && (sel.key === 'alert' || sel.key === 'hazard' || sel.risk !== 'normal')
})

const impactRadius = computed(() => ({
  high: 1000,
  elevated: 700,
  medium: 450,
  low: 250,
  normal: 200
}[selected.value?.risk] || 450))

const emergencyTimeline = computed(() => {
  const process = orderTimeline.value.map((item) => ({
    step_name: item.step_name || item.step || '工单处置',
    at: item.at || '',
    note: item.note || ''
  }))
  return [...emergencyEvents.value, ...process]
})

function emergencyTime() {
  return new Date().toLocaleTimeString('zh-CN', { hour12: false })
}

function addEmergencyEvent(stepName, note) {
  emergencyEvents.value.push({ step_name: stepName, note, at: emergencyTime() })
}

function haversineMeters(a, b) {
  const toRad = (value) => value * Math.PI / 180
  const lat1 = toRad(Number(a[1]))
  const lat2 = toRad(Number(b[1]))
  const dLat = lat2 - lat1
  const dLng = toRad(Number(b[0]) - Number(a[0]))
  const h = Math.sin(dLat / 2) ** 2 + Math.cos(lat1) * Math.cos(lat2) * Math.sin(dLng / 2) ** 2
  return 6371000 * 2 * Math.atan2(Math.sqrt(h), Math.sqrt(1 - h))
}

function requiredSkillForSelection(sel) {
  const text = `${sel?.title || ''} ${sel?.properties?.device_type || ''}`
  if (sel?.key === 'hazard' || /沉降|塌陷|道路/.test(text)) return '土建维修'
  if (/通信|网络/.test(text)) return '弱电网络'
  if (/仪表|传感|压力|浓度/.test(text)) return '仪表调试'
  return '管道抢修'
}

function categoryForSelection(sel) {
  const skill = requiredSkillForSelection(sel)
  return ({ '土建维修': 'civil', '弱电网络': 'it', '仪表调试': 'instrument', '管道抢修': 'pipeline' })[skill]
}

function priorityForRisk(risk) {
  return ({ high: 'urgent', elevated: 'high', medium: 'medium', low: 'low' })[risk] || 'medium'
}

// ---------------------------------------------------------------------------
// 右侧业务态势与底部指标（全部由当前数据通道的记录与汇总派生）
// ---------------------------------------------------------------------------
function identityOf(item) {
  return String(
    item?.alertEventCode ?? item?.alert_event_code ?? item?.code ?? item?.asset_code ??
    item?.assetCode ?? item?.id ?? ''
  )
}

function parseBusinessTime(item) {
  const raw = item?.eventTimestamp ?? item?.event_timestamp ?? item?.event_time ?? item?.eventTime ??
    item?.alarm_ts ?? item?.ts_ms ?? item?.created_ts ?? item?.createdAt ?? item?.created_at
  if (raw === undefined || raw === null || raw === '') return null
  const numeric = Number(raw)
  const value = Number.isFinite(numeric)
    ? (Math.abs(numeric) < 1e11 ? numeric * 1000 : numeric)
    : raw
  const date = new Date(value)
  return Number.isNaN(date.getTime()) ? null : date
}

function sameLocalDay(a, b = new Date()) {
  return !!a && a.getFullYear() === b.getFullYear() && a.getMonth() === b.getMonth() && a.getDate() === b.getDate()
}

function compactBusinessTime(date) {
  if (!date) return '--:--'
  const pad = (value) => String(value).padStart(2, '0')
  if (sameLocalDay(date)) return `${pad(date.getHours())}:${pad(date.getMinutes())}`
  return `${pad(date.getMonth() + 1)}-${pad(date.getDate())}`
}

function findFeatureForRecord(key, item) {
  const id = identityOf(item)
  if (!id) return null
  return (collections[key]?.features || []).find((feature) => identityOf(feature.properties) === id) || null
}

const recentAlarms = computed(() => {
  const cfg = LAYER_MAP.alert
  return (records.alert || [])
    .map((item, index) => {
      const feature = findFeatureForRecord('alert', item)
      const level = riskLevelOf(item, cfg.statusOf(item))
      const date = parseBusinessTime(item)
      return {
        id: identityOf(item) || `alert-${index}`,
        title: cfg.titleOf(item),
        level,
        levelLabel: RISK_LEVELS[level]?.label || '风险',
        area: item.area_name ?? item.areaName ?? item.zone ?? item.area_id ?? item.areaId ?? '',
        device: item.device_id ?? item.deviceId ?? item.device_type ?? item.deviceType ?? '',
        time: compactBusinessTime(date),
        timestamp: date?.getTime() || 0,
        feature,
        locatable: !!feature
      }
    })
    .sort((a, b) => b.timestamp - a.timestamp)
    .slice(0, 8)
})

const todayAlarmCount = computed(() =>
  (records.alert || []).reduce((sum, item) => sum + (sameLocalDay(parseBusinessTime(item)) ? 1 : 0), 0)
)

const riskDistribution = computed(() => {
  const countsByLevel = { high: 0, elevated: 0, medium: 0, low: 0 }
  const candidates = [...(records.alert || []), ...(records.hazard || [])]
  for (const item of candidates) {
    const explicit = item.warning_level ?? item.warningLevel ?? item.alertLevel ?? item.risk_level ?? item.riskLevel ?? item.level
    if (explicit === undefined || explicit === null || explicit === '') continue
    const level = riskLevelOf(item)
    if (level in countsByLevel) countsByLevel[level] += 1
  }
  return ['high', 'elevated', 'medium', 'low'].map((key) => ({ ...RISK_LEVELS[key], value: countsByLevel[key] }))
})

const deviceOnline = computed(() => {
  // 演示通道带回了统一配置的设备总量口径，优先使用，避免在模板里硬编码数字。
  const summary = demoSummary.value
  const summaryTotal = Number(summary?.deviceTotal)
  if (Number.isFinite(summaryTotal) && summaryTotal > 0) {
    const online = Number(summary.deviceOnline) || 0
    return {
      available: true,
      rate: Math.round(online / summaryTotal * 1000) / 10,
      online,
      total: summaryTotal,
      hasHistory: false
    }
  }

  const items = [...(records.asset || []), ...(records.manhole || [])]
  const withOnlineStatus = items
    .map((item) => item.online_status ?? item.onlineStatus ?? item.is_online ?? item.isOnline)
    .filter((value) => value !== undefined && value !== null && value !== '')
  if (!withOnlineStatus.length) {
    return { available: false, rate: 0, online: null, total: null, hasHistory: false }
  }
  const online = withOnlineStatus.filter((value) => {
    if (value === true || value === 1) return true
    const text = String(value).toLowerCase()
    return text === 'online' || text === 'true' || text.includes('在线')
  }).length
  return {
    available: true,
    rate: Math.round(online / withOnlineStatus.length * 1000) / 10,
    online,
    total: withOnlineStatus.length,
    hasHistory: false
  }
})

function sumNumeric(items, keys) {
  return (items || []).reduce((sum, item) => {
    const raw = keys.map((key) => item?.[key]).find((value) => value !== undefined && value !== null && value !== '')
    const value = Number(raw)
    return sum + (Number.isFinite(value) ? value : 0)
  }, 0)
}

const metricItems = computed(() => {
  // 演示口径：设备总量与工单数取自统一配置，预警与高风险数仍由同一份数据实时算出。
  // 注意两处统计口径不同：环形图统计「预警事件 + 风险点」两类要素，
  // 指标卡只统计风险点，因此卡片备注明确写"风险点"，避免被误读成与环形图矛盾。
  const summary = demoSummary.value
  if (Number(summary?.deviceTotal) > 0) {
    const highRisk = (records.hazard || []).reduce(
      (sum, item) => sum + (riskLevelOf(item) === 'high' ? 1 : 0),
      0
    )
    return [
      { key: 'device-total', label: '设备总数', value: summary.deviceTotal, unit: '台', note: `在线 ${summary.deviceOnline ?? 0} 台`, icon: 'device', tone: 'blue' },
      { key: 'today-alert', label: '今日预警', value: todayAlarmCount.value, unit: '起', note: '按事件时间统计', icon: 'alarm', tone: 'orange' },
      { key: 'high-risk', label: '高风险', value: highRisk, unit: '处', note: '风险等级为高的风险点', icon: 'risk', tone: highRisk ? 'red' : 'green' },
      { key: 'today-order', label: '今日工单', value: summary.todayWorkOrders ?? 0, unit: '单', note: '今日新增处置工单', icon: 'point', tone: 'blue' },
      { key: 'processing-order', label: '处理中工单', value: summary.processingWorkOrders ?? 0, unit: '单', note: '尚未闭环处置', icon: 'alarm', tone: summary.processingWorkOrders ? 'orange' : 'green' }
    ]
  }

  const pipelineLengthM = sumNumeric(records.asset, ['length_m', 'lengthM'])
  const facilities = (records.asset?.length || 0) + (records.manhole?.length || 0)
  const risks = (records.hazard?.length || 0)
  const activeAlerts = (records.alert || []).filter((item) => {
    const status = String(item.alertStatus ?? item.alert_status ?? item.status ?? '').toLowerCase()
    return !['closed', 'resolved', '已关闭', '已处理', '已闭环'].some((value) => status.includes(value))
  }).length
  return [
    { key: 'length', label: '管线资产总长', value: pipelineLengthM ? (pipelineLengthM / 1000).toFixed(1) : '0', unit: 'km', note: '资产台账管段长度汇总', icon: 'pipeline', tone: 'blue' },
    { key: 'facility', label: '设施记录', value: facilities, unit: '处', note: '资产设备与智能井盖', icon: 'device', tone: 'green' },
    { key: 'today-alert', label: '今日预警', value: todayAlarmCount.value, unit: '起', note: '按事件时间统计', icon: 'alarm', tone: 'orange' },
    { key: 'active-alert', label: '未闭环预警', value: activeAlerts, unit: '起', note: '按处置状态统计', icon: 'alarm', tone: activeAlerts ? 'red' : 'green' },
    { key: 'risk', label: '风险记录', value: risks, unit: '处', note: '道路塌陷风险点位', icon: 'risk', tone: risks ? 'orange' : 'blue' }
  ]
})

// ---------------------------------------------------------------------------
// 地图初始化
// ---------------------------------------------------------------------------
async function createMap() {
  BMap = await waitBMap()

  // 百度地图：中心点使用 ANSAI_CENTER（[lat, lon]），但 BMap.Point 是 [lng, lat]
  // ANSAI_CENTER = [36.55, 109.22] → BMap.Point(109.22, 36.55)
  const center = new BMap.Point(ANSAI_CENTER[1], ANSAI_CENTER[0])

  map = new BMap.Map(mapEl.value)
  map.centerAndZoom(center, 13)
  map.enableScrollWheelZoom(true)
  map.enableDoubleClickZoom(true)

  // 只加比例尺（ScaleControl 是 BMap v3.0 内置的），
  // 缩放控件和地图类型切换用 Element Plus 按钮自己实现（见模板 .gis-fab 区域），
  // 避免 BMap v3.0 与 BMapGL 的控件命名差异问题。
  try {
    const scale = new BMap.ScaleControl({ anchor: BMAP_ANCHOR_BOTTOM_LEFT })
    map.addControl(scale)
  } catch (e) {
    console.warn('[BMap] ScaleControl 加载失败:', e?.message)
  }

  // 点击事件：清空导航/高亮
  map.addEventListener('click', (e) => {
    if (navMode.value && !navStartPoint.value) {
      navStartPoint.value = e.point
      navStart.value = `起点: ${e.point.lng.toFixed(5)}, ${e.point.lat.toFixed(5)}`
      return
    }
    if (navMode.value && !navEndPoint.value) {
      navEndPoint.value = e.point
      navEnd.value = `终点: ${e.point.lng.toFixed(5)}, ${e.point.lat.toFixed(5)}`
      return
    }
    // 正常点击：关闭抽屉，清除高亮
    drawerVisible.value = false
    try { map.closeInfoWindow?.() } catch { /* noop */ }
    clearHighlight()
  })

  // 缩放事件：控制显隐、聚合、网络节点、标签、管线线宽
  map.addEventListener('zoomend', () => {
    applyZoomVisibility()
    applyLabels()
    renderClusters()
    renderNetworkNodes()
    updateLineWeights()
    updateHighlightRing()
  })

  for (const cfg of GIS_LAYERS) {
    overlayMap[cfg.key] = []
    rendered[cfg.key] = []
  }
}

// ---------------------------------------------------------------------------
// 筛选
// ---------------------------------------------------------------------------
function passesFilter(props) {
  if (areaFilter.value && props._area !== areaFilter.value) return false
  if (riskFilter.value && props._risk !== riskFilter.value) return false
  if (statusFilter.value && props._status !== statusFilter.value) return false
  const kw = appliedKeyword.value.trim().toLowerCase()
  if (kw && !props._search.includes(kw)) return false
  return true
}

function filteredFeatures(key) {
  const fc = collections[key]
  if (!fc) return []
  return fc.features.filter((f) => passesFilter(f.properties))
}

// ---------------------------------------------------------------------------
// 渲染：管线 / 点位
// ---------------------------------------------------------------------------

/** 判断是否主干管线 */
function isTrunkPipeline(props) {
  if (props.is_main === true || props.isMain === true || props.trunk === true) return true
  const level = String(props.pipeline_level ?? props.level ?? props.grade ?? '').toLowerCase()
  if (level.includes('main') || level.includes('trunk') || level.includes('主干')) return true
  return Number(props.diameter ?? props.pipeDiameter ?? 0) >= 250
}

/**
 * 管线样式（颜色 = 管线类型，风险/状态只通过 线宽/描边/Marker 表达，
 * 避免"红色到底是燃气管线还是高风险"的语义混乱）。
 * 线宽根据当前 zoom 动态调整：zoom 小时细线避免重叠，zoom 大时加粗让管线清晰。
 */
function getPipelineStyle(cfg, props, state = 'default', zoom = 13) {
  const status = props._status || 'normal'
  const trunk = isTrunkPipeline(props)
  // 颜色 = 管线类型固定色（燃气管=土红、给水管=蓝、废水管=灰绿）
  const color = cfg.color

  // 主干与支线保持轻量层级，避免再次覆盖真实道路底图。
  const zoomFactor = Math.max(0.78, Math.min(1.22, 0.78 + (zoom - 11) * 0.055))
  let baseWeight = (trunk ? 2.4 : 1.55) * zoomFactor
  if (status === 'danger') baseWeight += 0.75
  if (status === 'warning') baseWeight += 0.35
  if (state === 'selected') baseWeight += 1.4

  const weight = Math.max(1.2, Math.round(baseWeight * 10) / 10)
  const opacity = status === 'danger' ? 0.86 : status === 'warning' ? 0.72 : (trunk ? 0.62 : 0.5)

  return {
    strokeColor: color,
    strokeWeight: weight,
    strokeOpacity: state === 'hover' ? Math.min(1, opacity + 0.12) : opacity,
    // 风险描边配置
    dangerStroke: status === 'danger',   // 白色描边 + 加粗
    warningStroke: status === 'warning'   // 细白描边
  }
}

/** 更新所有已渲染管线的 strokeWeight（zoom 变化时调用） */
function updateLineWeights() {
  if (!map) return
  const zoom = map.getZoom()
  for (const cfg of GIS_LAYERS.filter((c) => c.geometry === 'line')) {
    const items = overlayMap[cfg.key] || []
    for (const item of items) {
      const bundle = item.bundle
      if (!bundle) continue
      const { feature, cfg: bundleCfg, overlays } = bundle
      const style = getPipelineStyle(bundleCfg, feature.properties, 'default', zoom)
      const casingWeightOffset = style.dangerStroke ? 3.5 : style.warningStroke ? 1.8 : 1
      const casingOpacity = style.dangerStroke ? 0.2 : style.warningStroke ? 0.12 : 0.08
      for (const entry of overlays) {
        if (!(entry.overlay instanceof BMap.Polyline)) continue
        if (entry.layer === 'casing') {
          entry.overlay.setStrokeStyle({
            color: style.dangerStroke ? '#C9433B' : style.strokeColor,
            weight: style.strokeWeight + casingWeightOffset,
            opacity: casingOpacity
          })
        } else if (entry.layer === 'main') {
          entry.overlay.setStrokeStyle({
            color: style.strokeColor,
            weight: style.strokeWeight,
            opacity: style.strokeOpacity
          })
        }
      }
    }
  }
}

/** 获取点位视觉参数 */
function getMarkerVisual(cfg, props) {
  const risk = props._risk || 'normal'
  const size = { high: 14, elevated: 12, medium: 10, low: 9, normal: 7 }[risk] || 7
  return { size }
}

/**
 * BMap.Circle 的半径单位是墨卡托米，屏幕上 1 像素 = 2^(18 - zoom) 米，
 * 所以高亮圈必须按当前缩放级别把"期望像素半径"换算成米。
 * 直接用图标像素尺寸当半径的话，zoom 13 下 22 米还不到 1 像素，选中点位等于没有高亮。
 */
function highlightRingRadius(cfg, props) {
  const px = getMarkerVisual(cfg, props).size / 2 + 8
  const zoom = map ? map.getZoom() : 13
  return px * Math.pow(2, 18 - zoom)
}

/** 缩放后重算高亮圈半径，让它始终保持恒定的屏幕像素大小 */
function updateHighlightRing() {
  const sel = selected.value
  if (!selectedOverlay || !sel || sel.cfg?.geometry !== 'point') return
  try {
    selectedOverlay.setRadius?.(highlightRingRadius(sel.cfg, sel.properties))
  } catch { /* noop */ }
}

function itemOverlays(item) {
  const bundleOverlays = item?.bundle?.overlays?.map((entry) => entry.overlay).filter(Boolean)
  return bundleOverlays?.length ? bundleOverlays : (item?.overlay ? [item.overlay] : [])
}

function removeItemOverlays(item) {
  for (const overlay of itemOverlays(item)) {
    try { map.removeOverlay(overlay) } catch { /* noop */ }
  }
}

function addItemOverlays(item) {
  const current = map.getOverlays?.() || []
  for (const overlay of itemOverlays(item)) {
    try { if (!current.includes(overlay)) map.addOverlay(overlay) } catch { /* noop */ }
  }
}

/** 移除某图层所有覆盖物 */
function clearOverlayGroup(key) {
  if (!map) return
  for (const item of overlayMap[key] || []) {
    removeItemOverlays(item)
  }
  overlayMap[key] = []
}

/**
 * 收集所有图层的原始 WGS84 坐标，建立 feature → 原始坐标的索引映射。
 * 返回：{ coordsList: [[lon,lat], ...], mapping: [{ key, feature, start, count }] }
 * 后续批量转换后用 mapping 把结果重新分发到各 feature。
 */
function collectAllCoords() {
  const coordsList = []
  const mapping = []
  for (const cfg of GIS_LAYERS) {
    const features = filteredFeatures(cfg.key)
    for (const feature of features) {
      if (cfg.geometry === 'line') {
        const coords = feature.geometry.coordinates
        if (!Array.isArray(coords) || coords.length < 2) continue
        const start = coordsList.length
        coords.forEach(([lon, lat]) => coordsList.push([lon, lat]))
        mapping.push({ key: cfg.key, feature, start, count: coords.length, isLine: true })
      } else {
        const [lon, lat] = feature.geometry.coordinates
        coordsList.push([lon, lat])
        mapping.push({ key: cfg.key, feature, start: coordsList.length - 1, count: 1, isLine: false })
      }
    }
  }
  return { coordsList, mapping }
}

/**
 * 构建管线覆盖物：白色描边（表达风险程度） + 主色线（固定为管线类型色）。
 * 风险只通过「主色线加粗 + 白色描边加粗」表达，不再改变管线本身颜色，
 * 避免"红色到底是燃气管线还是高风险"的语义混乱。
 */
function buildLine(cfg, feature, bdCoords) {
  const bdPoints = bdCoords.map(([lng, lat]) => new BMap.Point(lng, lat))
  const zoom = map ? map.getZoom() : 13
  const style = getPipelineStyle(cfg, feature.properties, 'default', zoom)

  const overlays = []

  // 1. 轻量底描边；只有异常管段形成很弱的风险 glow。
  const casingWeightOffset = style.dangerStroke ? 3.5 : style.warningStroke ? 1.8 : 1
  const casingOpacity = style.dangerStroke ? 0.2 : style.warningStroke ? 0.12 : 0.08
  const casing = new BMap.Polyline(bdPoints, {
    strokeColor: style.dangerStroke ? '#C9433B' : style.strokeColor,
    strokeWeight: style.strokeWeight + casingWeightOffset,
    strokeOpacity: casingOpacity,
    strokeLineCap: 'round',
    strokeLineJoin: 'round'
  })
  overlays.push({ overlay: casing, layer: 'casing' })

  // 2. 主色线（固定为 cfg.color = 管线类型色）
  const main = new BMap.Polyline(bdPoints, {
    strokeColor: style.strokeColor,
    strokeWeight: style.strokeWeight,
    strokeOpacity: style.strokeOpacity,
    strokeLineCap: 'round',
    strokeLineJoin: 'round'
  })
  overlays.push({ overlay: main, layer: 'main', feature, cfg, props: feature.properties, bdCoords })

  for (const { overlay } of overlays) {
    if (!(overlay instanceof BMap.Polyline)) continue
    overlay.addEventListener('click', () => {
      selectFeature(cfg, feature, overlay, bdPoints)
    })
    overlay.addEventListener('mouseover', () => {
      updateLineState(feature, 'hover', overlays)
    })
    overlay.addEventListener('mouseout', () => {
      if (!highlightOverlay || highlightOverlay._bdLine !== bdPoints) {
        updateLineState(feature, 'default', overlays)
      }
    })
  }

  return { overlays, bdCoords, feature, cfg }
}

/** 构建点位覆盖物，接收已转换好的 BD09 坐标 */
function buildPoint(cfg, feature, bdLon, bdLat) {
  const bdPoint = new BMap.Point(bdLon, bdLat)

  const iconOpts = buildMarkerIcon(cfg, feature.properties)
  // BMap v3.0 的 Icon 只渲染图片地址（内部 new Image()），不支持注入 DOM，
  // 因此图标统一由 buildMarkerIcon 画成 SVG 再以 data URI 传入。
  const icon = new BMap.Icon(iconOpts.url, new BMap.Size(iconOpts.width, iconOpts.height), {
    anchor: new BMap.Size(iconOpts.anchor.x, iconOpts.anchor.y),
    imageSize: new BMap.Size(iconOpts.width, iconOpts.height)
  })

  const marker = new BMap.Marker(bdPoint, { icon })
  marker.setTitle(feature.properties._title || '')

  marker.addEventListener('click', () => {
    selectFeature(cfg, feature, marker, [bdLon, bdLat])
  })

  marker.addEventListener('mouseover', () => {
    try { marker.setTop?.(true) } catch { /* noop */ }
  })
  marker.addEventListener('mouseout', () => {
    if (highlightOverlay !== marker) {
      try { marker.setTop?.(false) } catch { /* noop */ }
    }
  })

  return { overlay: marker, feature, cfg, props: feature.properties, bdCoords: [bdLon, bdLat] }
}

/** 更新管线状态样式 */
function updateLineState(feature, state, overlays) {
  // 从 layer === 'main' 的覆盖物上取 cfg / props
  const mainEntry = overlays.find((e) => e.layer === 'main')
  const cfg = mainEntry?.cfg
  const props = mainEntry?.props
  if (!cfg || !props) return
  const style = getPipelineStyle(cfg, props, state)

  for (const entry of overlays) {
    const overlay = entry.overlay
    if (!(overlay instanceof BMap.Polyline)) continue
    if (entry.layer === 'casing') {
      // hover 时白色描边也略加粗，增强交互反馈
      const casingWeightOffset = style.dangerStroke ? 3.8 : style.warningStroke ? 2.2 : 1.3
      const casingOpacity = state === 'hover' ? 0.28 : (style.dangerStroke ? 0.2 : style.warningStroke ? 0.12 : 0.08)
      overlay.setStrokeStyle({
        color: style.dangerStroke ? '#C9433B' : style.strokeColor,
        weight: style.strokeWeight + casingWeightOffset,
        opacity: casingOpacity
      })
    } else if (entry.layer === 'main') {
      overlay.setStrokeStyle({
        color: style.strokeColor,
        weight: style.strokeWeight,
        opacity: style.strokeOpacity
      })
    }
  }
}

/** 渲染单个图层，使用已经转换好的 BD09 坐标 */
function renderLayer(key, bdCoordsMap) {
  const cfg = LAYER_MAP[key]
  if (!cfg) return
  clearOverlayGroup(key)
  rendered[key] = []
  const features = filteredFeatures(key)
  counts[key] = features.length

  for (const feature of features) {
    const bdCoords = bdCoordsMap.get(feature)
    if (!bdCoords) continue

    if (cfg.geometry === 'line') {
      const bundle = buildLine(cfg, feature, bdCoords)
      for (const { overlay } of bundle.overlays) {
        map.addOverlay(overlay)
      }
      const mainOverlay = bundle.overlays[bundle.overlays.length - 1].overlay
      overlayMap[key].push({
        overlay: mainOverlay,
        feature,
        cfg,
        props: feature.properties,
        bdCoords: bundle.bdCoords,
        bundle
      })
      rendered[key].push({ cfg, feature, bundle })
    } else {
      const [bdLon, bdLat] = bdCoords
      const item = buildPoint(cfg, feature, bdLon, bdLat)
      map.addOverlay(item.overlay)
      overlayMap[key].push(item)
      rendered[key].push({ cfg, feature, item })
    }
  }
}

/**
 * 渲染所有图层：先批量采集 WGS84 坐标 → 一次请求后端 convertCoords → 再逐图层渲染。
 * 相比之前逐点异步转换，请求次数从 N 降到 1~ceil(N/50)。
 */
async function renderAll() {
  const { coordsList, mapping } = collectAllCoords()

  // 批量坐标转换（后端单次最多 50 个，convertCoords 内部自动分批）
  let converted = coordsList
  if (coordsList.length > 0) {
    try {
      converted = await convertCoords(coordsList)
    } catch (err) {
      console.warn('[GIS] 坐标转换请求失败，降级使用原 WGS84 坐标:', err?.message)
      converted = coordsList
    }
  }

  // 建立 feature → bdCoords 的映射（管线 = 坐标数组，点位 = 单点数组）
  const bdCoordsMap = new Map()
  for (const { feature, start, count, isLine } of mapping) {
    if (isLine) {
      bdCoordsMap.set(feature, converted.slice(start, start + count))
    } else {
      bdCoordsMap.set(feature, converted[start]) // [lon, lat]
    }
  }

  // 逐图层渲染（已全部转换，可同步执行）
  for (const cfg of GIS_LAYERS) {
    renderLayer(cfg.key, bdCoordsMap)
  }

  applyZoomVisibility()
  renderClusters()
  renderNetworkNodes()
  applyLabels()
}

/** 按缩放级别 + 图层开关控制覆盖物显隐 */
function applyZoomVisibility() {
  if (!map) return
  const zoom = map.getZoom()
  for (const cfg of GIS_LAYERS) {
    if (!visible[cfg.key]) {
      // 隐藏：全部移除
      for (const item of overlayMap[cfg.key] || []) {
        removeItemOverlays(item)
      }
      continue
    }
    // 重新添加（如果之前因为隐藏被移除）
    for (const item of overlayMap[cfg.key] || []) {
      addItemOverlays(item)
    }
    // 再次过滤：按缩放级别控制单要素显隐
    const showList = []
    const hideList = []
    for (const item of overlayMap[cfg.key] || []) {
      const shouldShow = shouldShowFeatureAtZoom(cfg, item.feature, zoom)
      if (shouldShow) showList.push(item)
      else hideList.push(item)
    }
    for (const item of hideList) {
      removeItemOverlays(item)
    }
    for (const item of showList) {
      addItemOverlays(item)
    }
  }
}

function shouldShowFeatureAtZoom(cfg, feature, zoom) {
  const status = feature.properties._status || 'normal'
  if (cfg.geometry === 'line') return zoom >= 12 || isTrunkPipeline(feature.properties)
  // 10 级及以下交给聚合气泡表达，避免小比例尺下点位糊成一片；
  // 11 级起风险点、预警点、设备点全部单独显示，保证进入页面即可看到业务点位。
  if (zoom <= 10) return false
  if (cfg.key === 'manhole') return zoom >= 13 || status !== 'normal'
  return true
}

/** 低缩放级别：风险/预警聚合 */
function renderClusters() {
  if (!map) return
  for (const m of clusterMarkers) { try { map.removeOverlay(m) } catch { /* noop */ } }
  clusterMarkers = []
  const zoom = map.getZoom()
  if (zoom > 10) return

  const cellSize = zoom <= 9 ? 88 : 70
  const buckets = new Map()
  for (const key of ['hazard', 'alert']) {
    if (!visible[key]) continue
    const cfg = LAYER_MAP[key]
    for (const item of overlayMap[key] || []) {
      const { feature } = item
      if (feature.properties._status === 'normal') continue
      const [lng, lat] = item.bdCoords
      const point = new BMap.Point(lng, lat)
      const pixel = map.pointToPixel(point)
      const bucketKey = `${Math.floor(pixel.x / cellSize)}:${Math.floor(pixel.y / cellSize)}`
      const bucket = buckets.get(bucketKey) || { items: [], lat: 0, lng: 0, danger: false }
      bucket.items.push({ cfg, feature, point })
      bucket.lat += lat
      bucket.lng += lng
      bucket.danger ||= feature.properties._status === 'danger'
      buckets.set(bucketKey, bucket)
    }
  }

  for (const bucket of buckets.values()) {
    const count = bucket.items.length
    const lat = bucket.lat / count
    const lng = bucket.lng / count

    const iconOpts = buildClusterIcon(count, bucket.danger)
    const icon = new BMap.Icon(iconOpts.url, new BMap.Size(iconOpts.width, iconOpts.height), {
      anchor: new BMap.Size(iconOpts.anchor.x, iconOpts.anchor.y),
      imageSize: new BMap.Size(iconOpts.width, iconOpts.height)
    })

    const marker = new BMap.Marker(new BMap.Point(lng, lat), { icon })
    marker.setTitle(`${count} 个风险/预警点，点击放大查看`)
    marker.addEventListener('click', () => {
      if (count === 1) {
        map.centerAndZoom(new BMap.Point(lng, lat), 14)
      } else {
        const bounds = new BMap.Bounds()
        for (const { point } of bucket.items) bounds.extend(point)
        map.setViewport([bounds])
      }
    })
    map.addOverlay(marker)
    clusterMarkers.push(marker)
  }
}

/** 高缩放级别显示网络节点（管线端点/转折点） */
function renderNetworkNodes() {
  if (!map) return
  for (const m of networkNodes) { try { map.removeOverlay(m) } catch { /* noop */ } }
  networkNodes = []
  if (map.getZoom() < 16) return

  const seen = new Set()
  for (const cfg of GIS_LAYERS.filter((item) => item.geometry === 'line')) {
    if (!visible[cfg.key]) continue
    for (const item of overlayMap[cfg.key] || []) {
      if (!item.bdCoords || !Array.isArray(item.bdCoords)) continue
      const [mainOverlay] = (overlayMap[cfg.key] || []).filter((x) => x.feature === item.feature)
      const bundle = mainOverlay?.bundle
      const bdLine = bundle?.bdCoords
      if (!bdLine) continue
      bdLine.forEach(([lng, lat], index) => {
        const id = `${lng.toFixed(5)}:${lat.toFixed(5)}`
        if (seen.has(id)) return
        seen.add(id)
        const kind = index === 0 || index === bdLine.length - 1 ? '端点' : '转折点'
        const point = new BMap.Point(lng, lat)
        const circle = new BMap.Circle(point, 6, {
          strokeColor: cfg.color,
          strokeWeight: 1,
          strokeOpacity: 0.9,
          fillColor: cfg.color,
          fillOpacity: 0.82,
          enableEditing: false,
          enableMassClear: false
        })
        circle.setTitle(`${item.feature.properties._title || ''} · ${kind}`)
        circle.addEventListener('click', () => {
          selectFeature(cfg, item.feature, item.overlay, [lng, lat])
        })
        map.addOverlay(circle)
        networkNodes.push(circle)
      })
    }
  }
}

/** 高缩放级别显示常驻标签（BMap.Label） */
function applyLabels() {
  if (!map) return
  const zoom = map.getZoom()
  for (const cfg of GIS_LAYERS) {
    if (cfg.labelZoom > 90) continue

    // 标签只在高风险点位 + 足够高的缩放级别才显示，避免地图被白色文字淹没。
    // 规则：
    //   - 管线 (line)：永远不显示文字标签（已通过 labelZoom=99 屏蔽）
    //   - 点位 (point)：只给 danger / warning 状态的要素显示标签，
    //     normal 状态的 asset / manhole 完全不显示文字。
    for (const item of overlayMap[cfg.key] || []) {
      const overlay = item.overlay
      const props = item.props
      if (!props) continue

      // 清除旧标签
      if (overlay._gisLabel) {
        try { map.removeOverlay(overlay._gisLabel) } catch { /* noop */ }
        overlay._gisLabel = null
      }

      if (!(overlay instanceof BMap.Marker) && !(overlay instanceof BMap.Polyline)) continue
      // 管线不在此处显示标签（labelZoom 已经是 99）
      if (overlay instanceof BMap.Polyline) continue
      // 点位：只有 danger / warning 状态才显示标签，且 zoom >= labelZoom
      if (props._status !== 'danger' && props._status !== 'warning') continue
      if (zoom < cfg.labelZoom) continue

      const label = new BMap.Label(props._title || '', {
        position: overlay.getPosition(),
        offset: new BMap.Size(0, -24)
      })
      const statusColor = props._status === 'danger' ? '#C84740' : '#D59435'
      label.setStyle({
        padding: '2px 7px',
        fontSize: '11px',
        fontWeight: '500',
        color: 'var(--app-text-1, #30353B)',
        backgroundColor: 'rgba(255,255,255,0.94)',
        border: `1px solid ${statusColor}40`,
        borderRadius: '4px',
        boxShadow: '0 3px 10px rgba(42,54,64,0.12)'
      })
      map.addOverlay(label)
      overlay._gisLabel = label
    }
  }
}

// ---------------------------------------------------------------------------
// 选中 / 高亮
// ---------------------------------------------------------------------------
function escapeHtml(value) {
  return String(value ?? '')
    .replaceAll('&', '&amp;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;')
    .replaceAll("'", '&#039;')
}

function openFeatureInfoWindow(cfg, feature, coords) {
  if (!map || cfg.geometry !== 'point' || !Array.isArray(coords)) return
  const props = feature.properties || {}
  const level = RISK_LEVELS[props._risk] || RISK_LEVELS.normal
  const rows = cfg.fields
    .map((field) => {
      const keys = Array.isArray(field.prop) ? field.prop : [field.prop]
      const value = pickValue(props, keys)
      if (value === null) return null
      return `<div class="gis-popup__row"><span>${escapeHtml(field.label)}</span><b>${escapeHtml(value)}${field.unit ? ` ${escapeHtml(field.unit)}` : ''}</b></div>`
    })
    .filter(Boolean)
    .slice(0, 7)
  const rawCoords = props._coords
  if (Array.isArray(rawCoords)) {
    rows.push(`<div class="gis-popup__row"><span>坐标</span><b>${Number(rawCoords[0]).toFixed(5)}, ${Number(rawCoords[1]).toFixed(5)}</b></div>`)
  }
  const html = `<div class="gis-popup">
    <div class="gis-popup__head"><i style="background:${level.color}"></i><strong>${escapeHtml(props._title || cfg.label)}</strong></div>
    <div class="gis-popup__level" style="color:${level.color};background:${level.color}14">${escapeHtml(level.label)}</div>
    <div class="gis-popup__rows">${rows.join('')}</div>
  </div>`
  const point = new BMap.Point(Number(coords[0]), Number(coords[1]))
  map.openInfoWindow(new BMap.InfoWindow(html, { width: 280, title: '', enableMessage: false }), point)
}

function selectFeature(cfg, feature, overlay, coords) {
  clearHighlight()
  resetEmergencyAnalysis()
  const props = feature.properties
  const item = overlayMap[cfg.key]?.find((entry) => entry.feature === feature)
  const pointCoords = cfg.geometry === 'point'
    ? (Array.isArray(coords) ? coords : item?.bdCoords)
    : item?.bdCoords?.[Math.floor((item?.bdCoords?.length || 1) / 2)]
  selected.value = {
    key: cfg.key,
    cfg,
    properties: props,
    title: props._title,
    area: props._area,
    status: props._status,
    risk: props._risk || 'normal',
    latlng: pointCoords ? [Number(pointCoords[0]), Number(pointCoords[1])] : null,
    sourceCoords: Array.isArray(props._coords) ? [Number(props._coords[0]), Number(props._coords[1])] : null
  }

  // 高亮覆盖物
  if (cfg.geometry === 'line') {
    // 找到主色线的 bdCoords
    let bdLine = null
    if (item) bdLine = item.bdCoords
    if (bdLine) {
      highlightOverlay = overlay
      // 选中描边
      const bdPoints = bdLine.map(([lng, lat]) => new BMap.Point(lng, lat))
      selectedOverlay = new BMap.Polyline(bdPoints, {
        strokeColor: '#315B78',
        strokeWeight: getPipelineStyle(cfg, props).strokeWeight + 4,
        strokeOpacity: 0.24,
        strokeLineCap: 'round',
        strokeLineJoin: 'round'
      })
      map.addOverlay(selectedOverlay)
    }
  } else {
    highlightOverlay = overlay
    const [lng, lat] = pointCoords
    try { overlay.setTop?.(true) } catch { /* noop */ }
    selectedOverlay = new BMap.Circle(new BMap.Point(lng, lat), highlightRingRadius(cfg, props), {
      strokeColor: '#315B78',
      strokeWeight: 2,
      strokeOpacity: 0.72,
      fillColor: '#315B78',
      fillOpacity: 0.06,
      enableEditing: false
    })
    map.addOverlay(selectedOverlay)
    openFeatureInfoWindow(cfg, feature, pointCoords)
  }

  drawerVisible.value = true
}

function clearHighlight() {
  try { highlightOverlay?.setTop?.(false) } catch { /* noop */ }
  if (selectedOverlay) {
    try { map.removeOverlay(selectedOverlay) } catch { /* noop */ }
    selectedOverlay = null
  }
  highlightOverlay = null
}

async function locateAlarm(alarm) {
  if (!alarm?.feature) {
    ElMessage.warning('该预警暂无可关联的坐标信息')
    return
  }
  const cfg = LAYER_MAP.alert
  const findItem = () => overlayMap.alert?.find((entry) => entry.feature === alarm.feature)
  let item = findItem()
  if (!item) {
    // 右侧预警列表来自全量记录，目标可能被当前筛选条件排除；先恢复全量再定位。
    keyword.value = ''
    appliedKeyword.value = ''
    areaFilter.value = ''
    riskFilter.value = ''
    statusFilter.value = ''
    await renderAll()
    item = findItem()
  }
  if (!item?.bdCoords) {
    ElMessage.warning('该预警暂时无法定位')
    return
  }
  visible.alert = true
  // 先定位再刷新显隐：zoomend 是异步触发的，顺序颠倒会用旧缩放级别把目标 Marker 判为隐藏。
  map.centerAndZoom(new BMap.Point(item.bdCoords[0], item.bdCoords[1]), 16)
  applyZoomVisibility()
  selectFeature(cfg, alarm.feature, item.overlay, item.bdCoords)
}

function onDrawerClosed() {
  clearHighlight()
  resetEmergencyAnalysis()
  selected.value = null
}

function clearImpactCircle() {
  if (!impactCircleOverlay || !map) return
  try { map.removeOverlay(impactCircleOverlay) } catch { /* noop */ }
  impactCircleOverlay = null
}

function resetEmergencyAnalysis() {
  clearImpactCircle()
  emergencyActive.value = false
  impactedDevices.value = []
  nearestTeam.value = null
  aiPlan.value = ''
  createdOrder.value = null
  emergencyEvents.value = []
  orderTimeline.value = []
}

function drawImpactCircle() {
  const sel = selected.value
  if (!sel?.latlng || !map || !BMap) return
  clearImpactCircle()
  const [lng, lat] = sel.latlng
  const meta = RISK_LEVELS[sel.risk] || RISK_LEVELS.medium
  impactCircleOverlay = new BMap.Circle(new BMap.Point(lng, lat), impactRadius.value, {
    strokeColor: meta.color,
    strokeWeight: 2,
    strokeOpacity: 0.7,
    strokeStyle: 'dashed',
    fillColor: meta.color,
    fillOpacity: 0.1,
    enableEditing: false
  })
  map.addOverlay(impactCircleOverlay)
}

function collectImpactedDevices() {
  const center = selected.value?.latlng
  if (!center) return []
  return ['asset', 'manhole'].flatMap((key) => (overlayMap[key] || [])
    .filter((item) => Array.isArray(item.bdCoords) && !Array.isArray(item.bdCoords[0]))
    .map((item) => ({
      key,
      title: item.feature?.properties?._title || LAYER_MAP[key]?.label,
      distance: Math.round(haversineMeters(center, item.bdCoords))
    })))
    .filter((item) => item.distance <= impactRadius.value)
    .sort((a, b) => a.distance - b.distance)
}

async function startEmergencyAnalysis() {
  if (!selectedEmergencyEligible.value) return
  emergencyLoading.value = true
  emergencyActive.value = true
  drawImpactCircle()
  impactedDevices.value = collectImpactedDevices()
  emergencyEvents.value = []
  addEmergencyEvent('告警确认', `已确认“${selected.value.title}”，启动应急处置分析`)
  addEmergencyEvent('影响分析', `影响半径 ${impactRadius.value} 米，范围内识别到 ${impactedDevices.value.length} 台设备`)
  try {
    const result = await getDispatchRecommend({
      required_skill: requiredSkillForSelection(selected.value),
      location: selected.value.area || selected.value.title
    })
    nearestTeam.value = result?.candidates?.[0] || null
    if (nearestTeam.value) {
      addEmergencyEvent('队伍匹配', `推荐 ${nearestTeam.value.name}，当前${nearestTeam.value.status_name}，综合得分 ${nearestTeam.value.total_score}`)
    }
  } catch (err) {
    console.warn('[GIS] 应急队伍匹配失败:', err)
    ElMessage.warning('影响范围已生成，暂时无法获取应急队伍')
  } finally {
    emergencyLoading.value = false
  }
}

function focusImpactArea() {
  if (!impactCircleOverlay || !map) return
  try { map.setViewport(impactCircleOverlay.getBounds(), { margins: [70, 70, 70, 70] }) } catch { /* noop */ }
}

async function generateAiPlan() {
  const sel = selected.value
  if (!sel) return
  aiLoading.value = true
  try {
    const prompt = `请为城市基础设施告警生成简洁、可执行的现场处置方案。\n事件：${sel.title}\n风险等级：${statusMeta.value.label}\n区域：${sel.area}\n影响半径：${impactRadius.value}米\n影响设备：${impactedDevices.value.length}台\n推荐人员：${nearestTeam.value?.name || '待调度'}。\n请按“立即措施、现场核查、安全隔离、恢复与复盘”五项输出，每项不超过两句，不虚构监测数据。`
    const result = await sendChat(prompt)
    aiPlan.value = result?.answer || 'AI 暂未返回处置建议，请按应急预案执行并联系值班负责人。'
    addEmergencyEvent('AI 辅助研判', '处置建议已生成，等待值班人员确认')
  } catch (err) {
    console.warn('[GIS] AI 处置方案生成失败:', err)
    ElMessage.error('AI 处置方案生成失败，请检查智能助手服务')
  } finally {
    aiLoading.value = false
  }
}

async function createEmergencyOrder() {
  const sel = selected.value
  if (!sel || createdOrder.value) return
  orderLoading.value = true
  try {
    const order = await createOrder({
      title: `应急处置-${sel.title}`,
      channel: 'alarm',
      category: categoryForSelection(sel),
      priority: priorityForRisk(sel.risk),
      location: sel.area || sel.title,
      description: `GIS 告警联动生成；影响半径 ${impactRadius.value} 米，范围内设备 ${impactedDevices.value.length} 台。`,
      reporter: 'GIS 综合态势平台'
    })
    createdOrder.value = order
    if (nearestTeam.value?.staff_id) {
      createdOrder.value = await assignOrder({ order_id: order.order_id, staff_id: nearestTeam.value.staff_id })
    }
    const process = await getProcess(order.order_id)
    orderTimeline.value = process?.timeline || createdOrder.value?.process || []
    ElMessage.success(`工单 ${order.order_id} 已生成${nearestTeam.value ? '并完成派单' : ''}`)
  } catch (err) {
    console.error('[GIS] 一键生成工单失败:', err)
    ElMessage.error(err?.response?.data?.detail || '工单生成失败，请检查工单服务')
  } finally {
    orderLoading.value = false
  }
}

function goModule() {
  const sel = selected.value
  if (!sel) return
  drawerVisible.value = false
  router.push(sel.cfg.route)
}

// ---------------------------------------------------------------------------
// 数据加载
// ---------------------------------------------------------------------------
function formatTime(ts) {
  const d = new Date(ts)
  const pad = (n) => String(n).padStart(2, '0')
  return `${pad(d.getHours())}:${pad(d.getMinutes())}:${pad(d.getSeconds())}`
}

async function reload() {
  loading.value = true
  loadError.value = ''
  try {
    const result = await fetchAllLayers()
    for (const key of Object.keys(collections)) delete collections[key]
    Object.assign(collections, result.collections)
    for (const key of Object.keys(records)) delete records[key]
    Object.assign(records, result.records)
    for (const key of Object.keys(sources)) delete sources[key]
    Object.assign(sources, result.sources)
    demoSummary.value = result.summary || null
    updatedAt.value = formatTime(result.loadedAt)
    clearHighlight()
    selected.value = null
    drawerVisible.value = false
    await renderAll()
    // 首次进入页面时自动聚焦安塞区检测区域；之后不再自动干预，
    // 用户可以自由拖动/缩放地图；手动触发 fitToAnsei 的入口是「回到安塞区」按钮
    if (firstEntry) {
      firstEntry = false
      await nextTick()
      setTimeout(() => fitToAnsei(15), 200)
    }
  } catch (err) {
    console.error('[GIS] 数据加载失败:', err)
    loadError.value = 'GIS 数据加载失败，请检查后端服务或网关连通性'
  } finally {
    loading.value = false
  }
}

// ---------------------------------------------------------------------------
// 搜索（百度地图地点搜索 + 业务数据过滤）
// ---------------------------------------------------------------------------

async function onSearch() {
  const kw = keyword.value.trim()
  if (!kw) {
    appliedKeyword.value = ''
    searchSuggestions.value = []
    return
  }
  appliedKeyword.value = kw

  // 如果是纯业务关键字（编号/名称），在现有数据中查找
  // 如果像地名，则走后端代理的百度地点搜索
  if (/^[A-Za-z0-9\-#\s]+$/.test(kw) || /^(GP|WP|WW|MH|RH|AS|AL)-/i.test(kw)) {
    fitToMatches()
  } else {
    try {
      const data = await backendSearchPlace(kw)
      const pois = data.pois || []
      if (pois.length > 0) {
        const poi = pois[0]
        const point = new BMap.Point(poi.lng, poi.lat)
        map.centerAndZoom(point, 16)

        // 临时标记 POI 位置
        const iconOpts = buildDotIcon()
        const icon = new BMap.Icon(iconOpts.url, new BMap.Size(iconOpts.width, iconOpts.height), {
          anchor: new BMap.Size(iconOpts.anchor.x, iconOpts.anchor.y),
          imageSize: new BMap.Size(iconOpts.width, iconOpts.height)
        })
        const poiMarker = new BMap.Marker(point, { icon })
        poiMarker.setTitle(`${poi.name}\n${poi.address}`)
        map.addOverlay(poiMarker)
        setTimeout(() => { try { map.removeOverlay(poiMarker) } catch { /* noop */ } }, 5000)

        const infoWin = new BMap.InfoWindow(
          `<div style="padding:8px 12px;">
            <div style="font-weight:600;font-size:14px;margin-bottom:4px;">${poi.name}</div>
            <div style="color:#666;font-size:12px;">${poi.address || ''}</div>
          </div>`,
          { width: 240, height: 60, title: '', enableMessage: false }
        )
        map.openInfoWindow(infoWin, point)
      } else {
        fitToMatches()
      }
    } catch (err) {
      console.warn('[Baidu] 地点搜索失败，回退到业务搜索:', err)
      fitToMatches()
    }
  }
}

/** 搜索输入聚焦时触发建议 */
function onSearchFocus() {
  triggerSuggest()
}

watch(keyword, () => {
  if (suggestTimer) clearTimeout(suggestTimer)
  suggestTimer = setTimeout(triggerSuggest, 400)
})

async function triggerSuggest() {
  const kw = keyword.value.trim()
  if (kw.length < 1) { searchSuggestions.value = []; return }
  try {
    const data = await backendSearchPlace(kw)
    const pois = data.pois || []
    searchSuggestions.value = pois.slice(0, 5).map((p) => ({
      name: p.name,
      address: p.address,
      lng: p.lng,
      lat: p.lat
    }))
  } catch {
    searchSuggestions.value = []
  }
}

function selectSuggestion(item) {
  searchSuggestions.value = []
  keyword.value = item.name
  if (item.lng && item.lat) {
    map.centerAndZoom(new BMap.Point(item.lng, item.lat), 16)
  }
  onSearch()
}

function fitToMatches() {
  let match = null
  for (const cfg of GIS_LAYERS) {
    for (const feature of filteredFeatures(cfg.key)) {
      const item = overlayMap[cfg.key]?.find((entry) => entry.feature === feature)
      if (item?.bdCoords) { match = { cfg, feature, item }; break }
    }
    if (match) break
  }
  if (!match) {
    ElMessage.info('未找到可定位的业务要素')
    return
  }
  visible[match.cfg.key] = true
  applyZoomVisibility()
  const coords = match.cfg.geometry === 'line'
    ? match.item.bdCoords[Math.floor(match.item.bdCoords.length / 2)]
    : match.item.bdCoords
  map.centerAndZoom(new BMap.Point(coords[0], coords[1]), match.cfg.geometry === 'line' ? 15 : 16)
  selectFeature(match.cfg, match.feature, match.item.overlay, coords)
}

function resetFilters() {
  keyword.value = ''
  appliedKeyword.value = ''
  areaFilter.value = ''
  riskFilter.value = ''
  statusFilter.value = ''
}

// ---------------------------------------------------------------------------
// 路线导航
// ---------------------------------------------------------------------------

function startNavigate() {
  cancelNavigate()
  navMode.value = true
  navStart.value = ''
  navEnd.value = ''
  navStartPoint.value = null
  navEndPoint.value = null
  navResult.value = null
  ElMessage.info('请在地图上点击两次：第一次选起点，第二次选终点')
}

function cancelNavigate() {
  navMode.value = false
  navStart.value = ''
  navEnd.value = ''
  navStartPoint.value = null
  navEndPoint.value = null
  navResult.value = null
  clearRouteOverlay()
}

// 路线导航覆盖物引用（自定义 Polyline）
let routePolyline = null

function clearRouteOverlay() {
  if (routePolyline) {
    try { map.removeOverlay(routePolyline) } catch { /* noop */ }
    routePolyline = null
  }
}

function formatRouteDistance(value) {
  const meters = Number(value)
  if (!Number.isFinite(meters)) return value || '--'
  return meters >= 1000 ? `${(meters / 1000).toFixed(1)} km` : `${Math.round(meters)} m`
}

function formatRouteDuration(value) {
  const seconds = Number(value)
  if (!Number.isFinite(seconds)) return value || '--'
  const minutes = Math.max(1, Math.round(seconds / 60))
  return minutes >= 60 ? `${Math.floor(minutes / 60)}小时${minutes % 60}分钟` : `${minutes}分钟`
}

function drawRoutePath(path, distance, duration) {
  const pathPoints = (path || []).map((point) => {
    if (Array.isArray(point)) return new BMap.Point(Number(point[0]), Number(point[1]))
    return point
  }).filter((point) => Number.isFinite(point?.lng) && Number.isFinite(point?.lat))
  if (pathPoints.length < 2) throw new Error('路线返回的轨迹点不足')
  routePolyline = new BMap.Polyline(pathPoints, {
    strokeColor: '#1A73E8',
    strokeWeight: 6,
    strokeOpacity: 0.78,
    strokeLineCap: 'round',
    strokeLineJoin: 'round',
    enableEditing: false
  })
  map.addOverlay(routePolyline)
  map.setViewport(pathPoints)
  navResult.value = { distance, duration }
}

function planDrivingWithBMap(start, end) {
  return new Promise((resolve, reject) => {
    const timeout = window.setTimeout(() => reject(new Error('百度地图路线检索超时')), 12000)
    drivingRoute = new BMap.DrivingRoute(map, {
      onSearchComplete(results) {
        window.clearTimeout(timeout)
        if (drivingRoute.getStatus() !== BMAP_STATUS_SUCCESS || !results?.getPlan?.(0)) {
          reject(new Error('百度地图未找到可行驾车路线'))
          return
        }
        const plan = results.getPlan(0)
        const path = []
        for (let index = 0; index < plan.getNumRoutes(); index += 1) {
          path.push(...(plan.getRoute(index)?.getPath?.() || []))
        }
        resolve({
          path,
          distance: plan.getDistance(true),
          duration: plan.getDuration(true)
        })
      }
    })
    drivingRoute.search(start, end)
  })
}

async function doNavigate() {
  if (!navStartPoint.value || !navEndPoint.value) {
    ElMessage.warning('请先在地图上点击确定起点和终点')
    return
  }
  try {
    ElMessage.loading({ message: '正在规划路线...', duration: 0 })
    clearRouteOverlay()

    // 后端代理调用百度 Directionlite 接口
    const result = await backendPlanDriving(
      navStartPoint.value.lng, navStartPoint.value.lat,
      navEndPoint.value.lng, navEndPoint.value.lat
    )
    drawRoutePath(
      result.path,
      formatRouteDistance(result.distance),
      formatRouteDuration(result.duration)
    )

    ElMessage.closeAll()
    ElMessage.success(`路线规划完成：${navResult.value.distance}，约 ${navResult.value.duration}`)
  } catch (err) {
    // 部分百度 AK 只开通了 JavaScript 地图、未开通 DirectionLite Web API。
    // 这种情况下自动复用已加载的 BMap 驾车检索能力，保证路线功能可用。
    console.warn('[GIS] 后端路线服务不可用，切换 BMap SDK:', err?.response?.data?.detail || err.message)
    try {
      const fallback = await planDrivingWithBMap(navStartPoint.value, navEndPoint.value)
      drawRoutePath(fallback.path, fallback.distance, fallback.duration)
      ElMessage.closeAll()
      ElMessage.success(`路线规划完成：${fallback.distance}，约 ${fallback.duration}`)
    } catch (fallbackError) {
      ElMessage.closeAll()
      ElMessage.error(fallbackError.message || '路线规划失败，请检查百度地图服务权限')
    }
  }
}

function navigateFromSelected() {
  const sel = selected.value
  if (!sel || !sel.latlng) return
  const [lng, lat] = sel.latlng
  cancelNavigate()
  navMode.value = true
  navStartPoint.value = new BMap.Point(lng, lat)
  navStart.value = `起点: ${sel.title}`
  navEnd.value = ''
  navEndPoint.value = null
  ElMessage.info('已从选中地点设为起点，请继续点击地图选择终点')
}

// ---------------------------------------------------------------------------
// 自定义控件：缩放 / 地图类型（避开 BMap v3.0 控件类名差异）
// ---------------------------------------------------------------------------

/** 当前地图类型：normal / satellite / hybrid */
const currentMapType = ref('normal')
const mapTypeLabel = computed(() => ({
  normal: '标准地图',
  satellite: '卫星图',
  hybrid: '混合图'
}[currentMapType.value]))

function zoomIn() {
  if (!map) return
  const z = Math.min(21, map.getZoom() + 1)
  map.setZoom(z)
}

function zoomOut() {
  if (!map) return
  const z = Math.max(4, map.getZoom() - 1)
  map.setZoom(z)
}

function changeMapType(type) {
  if (!map) return
  currentMapType.value = type
  try {
    if (type === 'normal') {
      map.setMapType(BMAP_NORMAL_MAP)
    } else if (type === 'satellite') {
      map.setMapType(BMAP_SATELLITE_MAP)
    } else if (type === 'hybrid') {
      map.setMapType(BMAP_HYBRID_MAP)
    }
  } catch (e) {
    console.warn('[BMap] setMapType 失败:', e?.message)
  }
}

// ---------------------------------------------------------------------------
// 交互
// ---------------------------------------------------------------------------
function onToggleLayer(key, value) {
  visible[key] = value
}

function togglePanel() {
  panelCollapsed.value = !panelCollapsed.value
  nextTick(() => {
    setTimeout(() => {
      if (map) {
        // 百度地图需要触发 resize
        map.reset?.() || map.checkResize?.()
        // BMap.Map 没有 invalidateSize，但可以 setCenter 一次重绘
        const center = map.getCenter()
        map.centerAndZoom(center, map.getZoom())
      }
    }, 320)
  })
}

watch(visible, () => {
  applyZoomVisibility()
  renderClusters()
  renderNetworkNodes()
})

watch([areaFilter, riskFilter, statusFilter, appliedKeyword], async () => {
  if (!map) return
  await renderAll()
})

// ---------------------------------------------------------------------------
// 生命周期
// ---------------------------------------------------------------------------
function setupViewportWatcher() {
  if (typeof window.matchMedia !== 'function') return
  viewportQuery = window.matchMedia('(max-width: 1024px)')
  viewportHandler = () => { isMobile.value = viewportQuery.matches }
  viewportHandler()
  if (viewportQuery.addEventListener) viewportQuery.addEventListener('change', viewportHandler)
  else viewportQuery.addListener(viewportHandler)
}

// 路由变化：当从其他页面切回 /gis 时，重新聚焦安塞区 + 刷新地图尺寸
// 防止地图从 display:none 状态恢复后 canvas 尺寸错误
watch(
  () => route.path,
  (newPath, oldPath) => {
    if (newPath === '/gis' && oldPath !== '/gis') {
      // 从非 /gis 页面切换回来，重置 firstEntry 让 fitToAnsei 生效
      firstEntry = true
      if (map) refreshMapAfterActivate()
    }
  }
)

// keep-alive 场景：组件被激活时也需要刷新地图尺寸（即使当前没有 keep-alive 也保留作保险）
onActivated(() => {
  firstEntry = true
  if (map) refreshMapAfterActivate()
})

onMounted(async () => {
  setupViewportWatcher()
  try {
    await createMap()

    if (typeof ResizeObserver !== 'undefined') {
      resizeObserver = new ResizeObserver(() => {
        if (map) {
          // 百度地图容器尺寸变化时，需要手动触发重绘
          try { map.checkResize?.() } catch { /* noop */ }
          const center = map.getCenter()
          const zoom = map.getZoom()
          map.centerAndZoom(center, zoom)
        }
      })
      resizeObserver.observe(mapEl.value)
    }

    await reload()
  } catch (err) {
    console.error('[GIS] 初始化失败:', err)
    loadError.value = err.message || '百度地图初始化失败，请检查 AK 配置'
  }
})

onBeforeUnmount(() => {
  if (resizeObserver) {
    resizeObserver.disconnect()
    resizeObserver = null
  }
  if (viewportQuery && viewportHandler) {
    if (viewportQuery.removeEventListener) viewportQuery.removeEventListener('change', viewportHandler)
    else viewportQuery.removeListener(viewportHandler)
  }
  viewportQuery = null
  viewportHandler = null
  // 百度地图销毁
  if (map) {
    try {
      // 移除所有覆盖物
      const all = map.getOverlays?.() || []
      for (const ov of all) { try { map.removeOverlay(ov) } catch { /* noop */ } }
      map = null
    } catch { /* noop */ }
  }
})
</script>

<!--
  百度地图覆盖物的 DOM 由 BMap 自己创建，可能不带 Vue 的 data-v 属性。
  用 .gis-page / .gis-mapwrap / .gis-drawer 命名空间隔离样式。
-->
<style>
/* ===================== 页面骨架 ===================== */
.gis-page {
  display: flex;
  flex-direction: column;
  height: 100%;
  min-height: 0;
  min-width: 0;
  background-color: var(--app-bg);
  overflow: hidden;
}

/* ===================== 工具栏 ===================== */
.gis-toolbar {
  flex: 0 0 auto;
  position: relative;
  display: flex;
  align-items: center;
  gap: 16px;
  min-width: 0;
  padding: 12px 20px;
  background-color: rgba(255, 255, 255, 0.78);
  -webkit-backdrop-filter: blur(20px) saturate(1.8);
  backdrop-filter: blur(20px) saturate(1.8);
  border-bottom: 1px solid var(--app-border);
}

.gis-toolbar__main {
  position: relative;
  display: flex;
  align-items: center;
  gap: 10px;
  flex: 1 1 auto;
  min-width: 0;
}

.gis-toolbar__search {
  flex: 0 1 300px;
  min-width: 140px;
}
.gis-toolbar__select {
  flex: 0 0 132px;
  min-width: 0;
}
.gis-toolbar__btn {
  flex-shrink: 0;
  white-space: nowrap;
}

.gis-toolbar__meta {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-shrink: 0;
  font-size: 12px;
  color: var(--app-text-4);
  white-space: nowrap;
}
.gis-meta__divider {
  width: 1px;
  height: 12px;
  background-color: var(--app-border-strong);
}
.gis-meta__item {
  font-variant-numeric: tabular-nums;
}

.gis-toolbar__mobile {
  display: none;
  align-items: center;
  gap: 8px;
  flex-shrink: 0;
}

/* 搜索建议下拉 */
.gis-suggestions {
  position: absolute;
  top: 100%;
  left: 0;
  z-index: 1100;
  width: 320px;
  margin-top: 4px;
  background: #fff;
  border: 1px solid var(--app-border);
  border-radius: 12px;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.12);
  max-height: 280px;
  overflow-y: auto;
}
.gis-suggestion-item {
  padding: 10px 14px;
  cursor: pointer;
  border-bottom: 1px solid var(--app-border);
  transition: background 0.15s;
}
.gis-suggestion-item:last-child { border-bottom: none; }
.gis-suggestion-item:hover { background: var(--app-hover); }
.gis-suggestion-title {
  display: block;
  font-size: 13px;
  font-weight: 500;
  color: var(--app-text-1);
}
.gis-suggestion-addr {
  display: block;
  font-size: 11px;
  color: var(--app-text-4);
  margin-top: 2px;
}

/* 移动端搜索行 */
.gis-searchrow {
  flex: 0 0 auto;
  padding: 10px 16px;
  background-color: rgba(255, 255, 255, 0.78);
  border-bottom: 1px solid var(--app-border);
}

/* ===================== 主体栅格 ===================== */
.gis-body {
  flex: 1 1 auto;
  min-height: 0;
  min-width: 0;
  display: grid;
  grid-template-columns: 280px minmax(0, 1fr);
  transition: grid-template-columns 0.28s cubic-bezier(0.4, 0, 0.2, 1);
}
.gis-body.is-collapsed {
  grid-template-columns: 0px minmax(0, 1fr);
}
.gis-body.is-collapsed .gis-panel {
  border-right-width: 0;
}

.gis-workspace {
  display: flex;
  flex-direction: column;
  min-width: 0;
  min-height: 0;
  padding: 12px;
  background: var(--app-bg, #f4f6f8);
  overflow: hidden;
}

.gis-stage {
  display: grid;
  grid-template-columns: minmax(0, 1fr) clamp(280px, 22vw, 320px);
  flex: 1 1 auto;
  min-width: 0;
  min-height: 0;
}

/* ---------- 左侧图层树 ---------- */
.gis-panel {
  display: flex;
  flex-direction: column;
  min-width: 0;
  min-height: 0;
  overflow: hidden;
  background-color: rgba(255, 255, 255, 0.72);
  -webkit-backdrop-filter: blur(20px) saturate(1.8);
  backdrop-filter: blur(20px) saturate(1.8);
  border-right: 1px solid var(--app-border);
}

.gis-panel__head {
  flex: 0 0 auto;
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 14px 16px;
  border-bottom: 1px solid var(--app-border);
}
.gis-panel__title {
  font-size: 14px;
  font-weight: 600;
  color: var(--app-text-1);
  white-space: nowrap;
}
.gis-panel__total {
  flex: 1;
  min-width: 0;
  font-size: 11px;
  color: var(--app-text-4);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.gis-panel__toggle {
  flex-shrink: 0;
  color: var(--app-text-3);
}

.gis-panel__body {
  flex: 1 1 auto;
  min-height: 0;
  overflow-y: auto;
  overflow-x: hidden;
  padding: 12px 8px;
}

/* ---------- 地图区 ---------- */
.gis-mapwrap {
  position: relative;
  min-width: 0;
  min-height: 0;
  overflow: hidden;
  background-color: #EAECEF;
  border: 1px solid var(--app-border, #e1e6eb);
  border-radius: 14px;
  box-shadow: 0 4px 18px rgba(39, 54, 68, 0.05);
}

/*
 * 高清适配：百度 BMap v3.0 是栅格瓦片（256x256），高 DPI 屏幕会糊。
 * 以下处理：
 * 1. translateZ(0) 把地图推入 GPU 合成层，防止浏览器子像素渲染模糊
 * 2. -webkit-font-smoothing 让覆盖物文字更锐利
 * 3. image-rendering: -webkit-optimize-contrast 让瓦片缩放时走清晰算法
 */
.gis-mapwrap .gis-map {
  position: absolute;
  inset: 0;
  z-index: 0;
  width: 100%;
  height: 100%;
  transform: translateZ(0);
  -webkit-transform: translateZ(0);
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}
.gis-mapwrap .gis-map img,
.gis-mapwrap .gis-map canvas {
  image-rendering: -webkit-optimize-contrast;
  image-rendering: crisp-edges;
}

/* 百度地图控件样式 */
.gis-mapwrap .BMap_cpyCtrl { display: none !important; }
.gis-mapwrap .anchorBL { display: none !important; }
.gis-mapwrap .BMap_zm_ctrl {
  border: 1px solid var(--app-border) !important;
  border-radius: 12px !important;
  overflow: hidden;
  box-shadow: var(--app-shadow-float) !important;
  margin: 14px 14px 0 0 !important;
}
/* 清除百度缩放控件的 transform 模糊副作用 */
.gis-mapwrap .BMap_zm_ctrl,
.gis-mapwrap .BMap_zm_ctrl * {
  transform: none !important;
}

/* 百度信息窗：只展示真实字段，使用平台统一的浅色卡片语言。 */
.gis-mapwrap .BMap_pop > div,
.gis-mapwrap .BMap_pop > img { filter: none !important; }
.gis-popup { padding: 5px 4px 2px; color: var(--app-text-1, #2b3138); font-family: var(--app-font-family, sans-serif); }
.gis-popup__head { display: flex; align-items: center; gap: 8px; padding-right: 18px; }
.gis-popup__head i { flex: none; width: 9px; height: 9px; border-radius: 50%; }
.gis-popup__head strong { overflow: hidden; font-size: 14px; font-weight: 650; line-height: 1.35; text-overflow: ellipsis; white-space: nowrap; }
.gis-popup__level { display: inline-block; margin: 9px 0 5px; padding: 3px 8px; border-radius: 999px; font-size: 10px; font-weight: 600; }
.gis-popup__rows { border-top: 1px solid var(--app-border, #edf0f3); }
.gis-popup__row { display: flex; justify-content: space-between; gap: 12px; padding: 6px 0; border-bottom: 1px solid var(--app-border, #f0f2f4); font-size: 11px; }
.gis-popup__row span { flex: none; color: var(--app-text-4, #929aa4); }
.gis-popup__row b { overflow: hidden; color: var(--app-text-2, #4d5660); font-weight: 550; text-align: right; text-overflow: ellipsis; white-space: nowrap; }

/* 回到安塞区按钮（复用 gis-zoom-btn 风格） */
.gis-home-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 34px;
  height: 34px;
  padding: 0;
  background-color: rgba(255, 255, 255, 0.94);
  -webkit-backdrop-filter: blur(16px) saturate(1.6);
  backdrop-filter: blur(16px) saturate(1.6);
  border: 1px solid var(--app-border);
  border-radius: 10px;
  color: var(--app-text-2);
  cursor: pointer;
  box-shadow: var(--app-shadow-float);
  transition: background 0.15s, color 0.15s, transform 0.12s;
}
.gis-home-btn:hover { background-color: var(--app-hover); color: var(--app-primary); }
.gis-home-btn:active { transform: scale(0.94); }

/* 导航浮层 */
.gis-nav-box {
  position: absolute;
  z-index: 1000;
  top: 14px;
  right: 14px;
  width: 280px;
  padding: 0;
  background-color: rgba(255, 255, 255, 0.96);
  -webkit-backdrop-filter: blur(16px) saturate(1.6);
  backdrop-filter: blur(16px) saturate(1.6);
  border: 1px solid var(--app-border);
  border-radius: 16px;
  box-shadow: 0 6px 24px rgba(0, 0, 0, 0.12);
  overflow: hidden;
}
.gis-nav-box__head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 14px;
  border-bottom: 1px solid var(--app-border);
}
.gis-nav-box__title {
  font-size: 13px;
  font-weight: 600;
  color: var(--app-text-1);
}
.gis-nav-box__close {
  color: var(--app-text-3);
}
.gis-nav-box__body {
  padding: 12px 14px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.gis-nav-box__arrow {
  text-align: center;
  color: var(--app-text-3);
  font-size: 12px;
}
.gis-nav-box__go {
  margin-top: 4px;
}
.gis-nav-box__result {
  padding: 10px 14px;
  border-top: 1px solid var(--app-border);
  font-size: 12px;
  color: var(--app-text-2);
  display: flex;
  gap: 16px;
  background: var(--app-hover);
}
.gis-nav-box__result b {
  color: var(--app-primary);
  font-weight: 600;
}

/* 右上角自定义控件组：缩放 + 地图类型切换 */
.gis-map-controls {
  position: absolute;
  z-index: 1000;
  top: 14px;
  right: 14px;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.gis-zoom-group {
  display: flex;
  flex-direction: column;
  align-items: center;
  overflow: hidden;
  background-color: rgba(255, 255, 255, 0.94);
  -webkit-backdrop-filter: blur(16px) saturate(1.6);
  backdrop-filter: blur(16px) saturate(1.6);
  border: 1px solid var(--app-border);
  border-radius: 10px;
  box-shadow: var(--app-shadow-float);
}
.gis-zoom-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 34px;
  height: 34px;
  padding: 0;
  background: transparent;
  border: none;
  color: var(--app-text-2);
  cursor: pointer;
  transition: background 0.15s, color 0.15s;
}
.gis-zoom-btn:hover { background-color: var(--app-hover); color: var(--app-text-1); }
.gis-zoom-btn:active { transform: scale(0.94); }
.gis-zoom-divider {
  width: 18px;
  height: 1px;
  background-color: var(--app-border);
}

.gis-maptype-btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 7px 12px;
  font-family: var(--app-font-family);
  font-size: 12px;
  font-weight: 500;
  color: var(--app-text-2);
  background-color: rgba(255, 255, 255, 0.94);
  -webkit-backdrop-filter: blur(16px) saturate(1.6);
  backdrop-filter: blur(16px) saturate(1.6);
  border: 1px solid var(--app-border);
  border-radius: var(--app-radius-tag);
  box-shadow: var(--app-shadow-float);
  cursor: pointer;
  transition: background 0.15s, color 0.15s;
}
.gis-maptype-btn:hover { background-color: var(--app-hover); color: var(--app-text-1); }

/* 面板折叠把手 */
.gis-fab {
  position: absolute;
  z-index: 1000;
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 8px 12px;
  font-family: var(--app-font-family);
  font-size: 13px;
  font-weight: 500;
  color: var(--app-text-1);
  background-color: rgba(255, 255, 255, 0.92);
  -webkit-backdrop-filter: blur(16px) saturate(1.6);
  backdrop-filter: blur(16px) saturate(1.6);
  border: 1px solid var(--app-border);
  border-radius: var(--app-radius-tag);
  box-shadow: var(--app-shadow-float);
  cursor: pointer;
  white-space: nowrap;
  transition: transform 0.18s ease, box-shadow 0.18s ease;
}
.gis-fab:hover {
  transform: translateY(-1px);
  box-shadow: 0 6px 18px rgba(0, 0, 0, 0.1);
}
.gis-fab--panel {
  top: 14px;
  left: 14px;
}

/* 状态浮层 */
.gis-state {
  position: absolute;
  z-index: 1000;
  top: 14px;
  left: 50%;
  transform: translateX(-50%);
  display: flex;
  align-items: center;
  gap: 10px;
  max-width: calc(100% - 32px);
  padding: 10px 18px;
  font-size: 13px;
  color: var(--app-text-2);
  white-space: nowrap;
  background-color: rgba(255, 255, 255, 0.92);
  -webkit-backdrop-filter: blur(16px) saturate(1.6);
  backdrop-filter: blur(16px) saturate(1.6);
  border: 1px solid var(--app-border);
  border-radius: var(--app-radius-tag);
  box-shadow: var(--app-shadow-float);
  pointer-events: auto;
}
.gis-state--error {
  color: #B42318;
  border-color: rgba(255, 59, 48, 0.28);
  background-color: rgba(255, 255, 255, 0.96);
}
.gis-state--notice {
  top: auto;
  bottom: 16px;
  color: #6e7782;
  background: rgba(255, 255, 255, 0.9);
}

/* 左下角图例：管线类型 + 风险等级 两组并排 */
.gis-legend {
  position: absolute;
  z-index: 1000;
  left: 14px;
  bottom: 50px;
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 10px 14px 12px;
  font-size: 11px;
  color: var(--app-text-2);
  background-color: rgba(255, 255, 255, 0.90);
  -webkit-backdrop-filter: blur(18px) saturate(1.6);
  backdrop-filter: blur(18px) saturate(1.6);
  border: 1px solid var(--app-border);
  border-radius: 10px;
  box-shadow: 0 4px 20px rgba(42, 54, 64, 0.10);
  pointer-events: none;
  user-select: none;
}
.gis-legend__group {
  display: flex;
  flex-direction: column;
  gap: 4px;
  min-width: 88px;
}
.gis-legend__title {
  font-size: 10px;
  font-weight: 600;
  letter-spacing: 0.4px;
  text-transform: uppercase;
  color: var(--app-text-3, #8E96A0);
  padding-bottom: 2px;
  border-bottom: 1px solid var(--app-border);
  margin-bottom: 2px;
}
.gis-legend__divider {
  align-self: stretch;
  width: 1px;
  background-color: var(--app-border);
  margin: 2px 0;
}
.gis-legend__item {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  white-space: nowrap;
  line-height: 1.4;
}
/* 管线类型色条（小短线段） */
.gis-legend__line {
  width: 16px;
  height: 3px;
  border-radius: 2px;
  box-shadow: 0 0 0 1px rgba(255,255,255,0.9);
}
/* 风险等级圆点 */
.gis-legend__dot {
  width: 9px;
  height: 9px;
  border-radius: 50%;
  box-shadow: 0 0 0 2px rgba(255,255,255,0.9);
  flex-shrink: 0;
}

/* ===================== 详情抽屉 ===================== */
.gis-drawer.el-drawer {
  border-radius: 0;
  box-shadow: -8px 0 40px rgba(0, 0, 0, 0.1);
}
.gis-drawer.el-drawer.rtl {
  border-top-left-radius: 20px;
  border-bottom-left-radius: 20px;
}
.gis-drawer.el-drawer.btt {
  border-top-left-radius: 20px;
  border-top-right-radius: 20px;
}
.gis-drawer .el-drawer__header {
  margin-bottom: 0;
  padding: 16px 20px;
  font-size: 15px;
  font-weight: 600;
  color: var(--app-text-1);
  border-bottom: 1px solid var(--app-border);
}
.gis-drawer .el-drawer__body {
  padding: 0;
  overflow-y: auto;
}

.gis-detail {
  display: flex;
  flex-direction: column;
  height: 100%;
  min-height: 0;
}

.gis-detail__head {
  flex: 0 0 auto;
  display: flex;
  align-items: flex-start;
  gap: 10px;
  padding: 18px 20px 14px;
  border-bottom: 1px solid var(--app-border);
}
.gis-detail__swatch {
  flex-shrink: 0;
  width: 4px;
  height: 34px;
  margin-top: 2px;
  border-radius: 2px;
}
.gis-detail__titles {
  flex: 1;
  min-width: 0;
}
.gis-detail__title {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  line-height: 1.35;
  color: var(--app-text-1);
  letter-spacing: -0.01em;
  word-break: break-word;
}
.gis-detail__sub {
  margin: 4px 0 0;
  font-size: 12px;
  color: var(--app-text-4);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.gis-detail__close {
  flex-shrink: 0;
  color: var(--app-text-3);
}

.gis-detail__body {
  flex: 1 1 auto;
  min-height: 0;
  overflow-y: auto;
  padding: 16px 20px 20px;
}

.gis-detail__status {
  display: inline-block;
  margin-bottom: 14px;
  padding: 4px 12px;
  font-size: 12px;
  font-weight: 600;
  border-radius: var(--app-radius-tag);
}

.gis-detail__list {
  margin: 0;
  display: flex;
  flex-direction: column;
  gap: 0;
}
.gis-detail__row {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
  padding: 11px 0;
  border-bottom: 1px solid var(--app-border);
}
.gis-detail__row:last-child {
  border-bottom: 0;
}
.gis-detail__row dt {
  flex-shrink: 0;
  margin: 0;
  font-size: 13px;
  color: var(--app-text-3);
  white-space: nowrap;
}
.gis-detail__row dd {
  margin: 0;
  min-width: 0;
  font-size: 13px;
  color: var(--app-text-1);
  text-align: right;
  word-break: break-word;
}
.gis-detail__row dd em {
  font-style: normal;
  font-size: 11px;
  color: var(--app-text-4);
}

.gis-detail__actions {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 16px;
  padding-top: 14px;
  border-top: 1px solid var(--app-border);
}
.gis-detail__actions .el-button { margin-left: 0; }

.emergency-panel {
  margin-top: 14px;
  padding: 14px;
  border: 1px solid #f1d4cf;
  border-radius: 10px;
  background: #fffafa;
}
.emergency-panel__title {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  margin-bottom: 12px;
  color: var(--app-text-1);
}
.emergency-kpis {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 8px;
}
.emergency-kpis > div {
  display: flex;
  flex-direction: column;
  gap: 3px;
  padding: 10px;
  border-radius: 8px;
  background: #fff;
  border: 1px solid var(--app-border);
}
.emergency-kpis b { font-size: 16px; color: #c3483e; }
.emergency-kpis span { font-size: 11px; color: var(--app-text-3); }
.emergency-team {
  margin: 10px 0 0;
  font-size: 12px;
  line-height: 1.6;
  color: var(--app-text-2);
}
.emergency-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 7px;
  margin-top: 12px;
}
.emergency-actions .el-button { margin-left: 0; }
.emergency-plan {
  margin-top: 12px;
  padding: 10px;
  border-left: 3px solid #409eff;
  border-radius: 4px;
  background: #f5f9ff;
  white-space: pre-wrap;
  font-size: 12px;
  line-height: 1.7;
  color: var(--app-text-2);
}
.emergency-timeline {
  margin: 16px 0 0;
  padding-left: 4px;
}
.emergency-timeline :deep(.el-timeline-item__timestamp) { font-size: 11px; }
.emergency-timeline b { font-size: 12px; }
.emergency-timeline p {
  margin: 3px 0 0;
  font-size: 11px;
  line-height: 1.5;
  color: var(--app-text-3);
}

.gis-detail__foot {
  flex: 0 0 auto;
  padding: 14px 20px calc(14px + env(safe-area-inset-bottom, 0px));
  border-top: 1px solid var(--app-border);
  background-color: rgba(255, 255, 255, 0.7);
}
.gis-detail__go {
  width: 100%;
}

/* 移动端筛选面板 */
.gis-filter-sheet {
  display: flex;
  flex-direction: column;
  gap: 10px;
  padding: 16px 20px 24px;
}
.gis-filter-sheet__label {
  margin-top: 6px;
  font-size: 12px;
  font-weight: 600;
  color: var(--app-text-3);
}
.gis-filter-sheet__actions {
  display: flex;
  gap: 10px;
  margin-top: 18px;
}
.gis-filter-sheet__actions .el-button {
  flex: 1;
}

/* ===================== 响应式 ===================== */
@media (max-width: 1440px) {
  .gis-body { grid-template-columns: 230px minmax(0, 1fr); }
  .gis-stage { grid-template-columns: minmax(0, 1fr) 260px; }
}

@media (max-width: 1280px) {
  .gis-body { grid-template-columns: 220px minmax(0, 1fr); }
  .gis-stage { grid-template-columns: minmax(0, 1fr) 260px; }
  .gis-toolbar__search { flex-basis: 220px; }
  .gis-toolbar__select { flex-basis: 118px; }
}

@media (max-width: 1024px) {
  .gis-toolbar {
    gap: 10px;
    padding: 8px 12px;
  }
  .gis-toolbar__main > .gis-toolbar__search,
  .gis-toolbar__main > .gis-toolbar__select,
  .gis-toolbar__main > .gis-toolbar__btn:not(:last-of-type) {
    display: none;
  }
  .gis-toolbar__meta { display: none; }
  .gis-toolbar__mobile { display: inline-flex; }
  .gis-body { grid-template-columns: 0px minmax(0, 1fr); }
  .gis-workspace { padding: 8px; }
  .gis-stage { grid-template-columns: minmax(0, 1fr); }
  .gis-business { display: none; }
  .gis-nav-box {
    left: 14px;
    right: 14px;
    width: auto;
  }
}
</style>
