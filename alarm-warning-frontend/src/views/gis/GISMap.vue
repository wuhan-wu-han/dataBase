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
          <el-option v-for="a in AREAS" :key="a" :label="a" :value="a" />
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
        <span class="gis-meta__item">数据来源：{{ sourceSummary }}</span>
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

      <div class="gis-mapwrap">
        <!-- 百度地图容器 -->
        <div ref="mapEl" class="gis-map"></div>

        <!-- 右上角自定义控件组：缩放 + 地图类型 -->
        <div class="gis-map-controls">
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
          <span>当前筛选条件下没有要素</span>
          <el-button size="small" plain @click="resetFilters">重置筛选</el-button>
        </div>

        <!-- 左下角图例 -->
        <div class="gis-legend">
          <span
            v-for="s in STATUS_OPTIONS"
            :key="s.value"
            class="gis-legend__item"
          >
            <i class="gis-legend__dot" :style="{ background: STATUS[s.value].color }"></i>
            {{ STATUS[s.value].label }}
          </span>
        </div>
      </div>
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
          </div>
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
          <el-option v-for="a in AREAS" :key="a" :label="a" :value="a" />
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
import { ref, reactive, computed, nextTick, onMounted, onBeforeUnmount, watch } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import {
  Search, Refresh, Filter, Files, Close,
  DArrowLeft, DArrowRight, Loading, WarningFilled, Aim,
  Position, Location, Top
} from '@element-plus/icons-vue'
import LayerTree from './LayerTree.vue'
import { fetchAllLayers } from '@/api/gis'
import {
  GIS_LAYERS, LAYER_MAP, ANSAI_CENTER,
  AREAS, STATUS, STATUS_OPTIONS, toneColor
} from '@/config/gisLayers'
import { waitBMap, buildMarkerIcon } from '@/utils/baidumap'
import { searchPlace as backendSearchPlace, convertCoords, planDriving as backendPlanDriving } from '@/api/baiduMap'

const router = useRouter()

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
const statusFilter = ref('')

const panelCollapsed = ref(false)
const drawerVisible = ref(false)
const selected = ref(null)

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
const visible = reactive(Object.fromEntries(GIS_LAYERS.map((l) => [l.key, true])))
const counts = reactive(Object.fromEntries(GIS_LAYERS.map((l) => [l.key, 0])))
const sources = reactive({})

// ---------------------------------------------------------------------------
// 百度地图运行时对象（非响应式）
// ---------------------------------------------------------------------------

// BMap.Icon 必须传一个有效的图片 URL 作为占位（不能传空字符串），
// 内部通过 _html 注入 DOM 样式覆盖掉图片显示。
// 1x1 透明 GIF 是百度 DOM Icon 的标准做法。
const TRANSPARENT_GIF = 'data:image/gif;base64,R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7'

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

const sourceSummary = computed(() => {
  const list = Object.values(sources)
  if (list.length === 0) return '加载中'
  const real = list.filter((s) => !s.mock).length
  const mock = list.filter((s) => s.mock).length
  if (mock === 0) return `实时接口 ${real}/${list.length}`
  if (real === 0) return '演示数据（接口未连通）'
  return `实时 ${real} · 演示 ${mock}`
})

const statusMeta = computed(() =>
  (selected.value ? STATUS[selected.value.status] : null) || STATUS.normal
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
  if (sel.latlng) {
    rows.push({
      label: '坐标 (经纬度)',
      value: `${sel.latlng[1].toFixed(5)}, ${sel.latlng[0].toFixed(5)}`,
      unit: '',
      color: null
    })
  }
  return rows
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
    clearHighlight()
  })

  // 缩放事件：控制显隐、聚合、网络节点、标签
  map.addEventListener('zoomend', () => {
    applyZoomVisibility()
    applyLabels()
    renderClusters()
    renderNetworkNodes()
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

/** 管线样式 */
function getPipelineStyle(cfg, props, state = 'default') {
  const status = props._status || 'normal'
  const trunk = isTrunkPipeline(props)
  const baseColor = cfg.color
  const color = status === 'danger'
    ? '#C94F46'
    : status === 'warning' ? '#D18B3C' : baseColor
  const normalWeight = trunk ? 6 : 4
  const weight = state === 'selected' ? normalWeight + 4 : normalWeight + (status === 'danger' ? 2 : status === 'warning' ? 1 : 0)
  const opacity = status === 'danger' ? 0.92 : status === 'warning' ? 0.82 : (trunk ? 0.74 : 0.64)

  return {
    strokeColor: color,
    strokeWeight: weight,
    strokeOpacity: state === 'hover' ? Math.min(1, opacity + 0.18) : opacity
  }
}

/** 获取点位视觉参数 */
function getMarkerVisual(cfg, props) {
  const status = props._status || 'normal'
  const isAlert = cfg.key === 'alert'
  const isRisk = cfg.key === 'hazard'
  const size = status === 'danger' ? (isAlert || isRisk ? 15 : 13) : status === 'warning' ? 11 : (isAlert ? 10 : 8)
  return { size }
}

/** 移除某图层所有覆盖物 */
function clearOverlayGroup(key) {
  if (!map) return
  for (const item of overlayMap[key] || []) {
    try { map.removeOverlay(item.overlay) } catch { /* noop */ }
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

/** 构建管线覆盖物（含白色描边 + 主色线 + 危险态光晕），接收已转换好的 BD09 坐标 */
function buildLine(cfg, feature, bdCoords) {
  const bdPoints = bdCoords.map(([lng, lat]) => new BMap.Point(lng, lat))
  const style = getPipelineStyle(cfg, feature.properties)
  const isDanger = feature.properties._status === 'danger'

  const overlays = []

  // 1. 危险态光晕
  if (isDanger) {
    const glow = new BMap.Polyline(bdPoints, {
      strokeColor: '#C94F46',
      strokeWeight: style.strokeWeight + 8,
      strokeOpacity: 0.16,
      strokeLineCap: 'round',
      strokeLineJoin: 'round'
    })
    overlays.push({ overlay: glow })
  }

  // 2. 白色描边
  const casing = new BMap.Polyline(bdPoints, {
    strokeColor: '#FFFFFF',
    strokeWeight: style.strokeWeight + 2,
    strokeOpacity: 0.22,
    strokeLineCap: 'round',
    strokeLineJoin: 'round'
  })
  overlays.push({ overlay: casing, feature, cfg, props: feature.properties, bdCoords })

  // 3. 主色线
  const main = new BMap.Polyline(bdPoints, {
    strokeColor: style.strokeColor,
    strokeWeight: style.strokeWeight,
    strokeOpacity: style.strokeOpacity,
    strokeLineCap: 'round',
    strokeLineJoin: 'round'
  })
  overlays.push({ overlay: main, feature, cfg, props: feature.properties, bdCoords })

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
  // 必须用一个有效的图片 URL（1x1 透明 GIF data URL），不能传空字符串
  // BMap v3.0 内部会 new Image() 加载它，空字符串会导致 initialize 时读 width 报错
  const TRANSPARENT_GIF = 'data:image/gif;base64,R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7'
  const icon = new BMap.Icon(TRANSPARENT_GIF, new BMap.Size(iconOpts.width, iconOpts.height), {
    anchor: new BMap.Size(iconOpts.anchor.x, iconOpts.anchor.y),
    imageSize: new BMap.Size(iconOpts.width, iconOpts.height)
  })
  icon._html = iconOpts.innerHTML

  const marker = new BMap.Marker(bdPoint, { icon })
  marker.setTitle(feature.properties._title || '')

  marker.addEventListener('click', () => {
    selectFeature(cfg, feature, marker, [bdLon, bdLat])
  })

  marker.addEventListener('mouseover', () => {
    marker.showInfoWindow?.(new BMap.InfoWindow(
      `<div style="padding:4px 8px;font-size:12px;">${feature.properties._title}</div>`,
      { width: 180, height: 24, title: '', enableMessage: false }
    ), bdPoint)
  })

  return { overlay: marker, feature, cfg, props: feature.properties, bdCoords: [bdLon, bdLat] }
}

/** 更新管线状态样式 */
function updateLineState(feature, state, overlays) {
  const cfg = overlays[1]?.cfg
  const props = overlays[1]?.props
  if (!cfg || !props) return
  const style = getPipelineStyle(cfg, props, state)
  for (const item of overlays) {
    const overlay = item.overlay
    if (overlay instanceof BMap.Polyline) {
      const strokeColor = overlay.getStrokeColor()
      if (strokeColor === '#FFFFFF') continue
      if (strokeColor === '#C94F46' && feature.properties._status === 'danger') continue
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
        try { map.removeOverlay(item.overlay) } catch { /* noop */ }
      }
      continue
    }
    // 重新添加（如果之前因为隐藏被移除）
    for (const item of overlayMap[cfg.key] || []) {
      try {
        if (!map.getOverlays().includes(item.overlay)) {
          map.addOverlay(item.overlay)
        }
      } catch { /* noop */ }
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
      try { map.removeOverlay(item.overlay) } catch { /* noop */ }
    }
    for (const item of showList) {
      try {
        if (!map.getOverlays().includes(item.overlay)) {
          map.addOverlay(item.overlay)
        }
      } catch { /* noop */ }
    }
  }
}

function shouldShowFeatureAtZoom(cfg, feature, zoom) {
  const status = feature.properties._status || 'normal'
  if (cfg.geometry === 'line') return zoom >= 12 || isTrunkPipeline(feature.properties)
  if (zoom <= 12) return false
  if (cfg.key === 'alert' || cfg.key === 'hazard') return zoom >= 15 || status !== 'normal'
  if (cfg.key === 'asset') return zoom >= 15 || (zoom >= 13 && status !== 'normal')
  if (cfg.key === 'manhole') return zoom >= 16 || (zoom >= 15 && status === 'danger')
  return zoom >= cfg.minZoom
}

/** 低缩放级别：风险/预警聚合 */
function renderClusters() {
  if (!map) return
  for (const m of clusterMarkers) { try { map.removeOverlay(m) } catch { /* noop */ } }
  clusterMarkers = []
  const zoom = map.getZoom()
  if (zoom > 12) return

  const cellSize = zoom <= 10 ? 88 : 70
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

  // 注入聚合样式（首次）
  ensureClusterStyles()

  for (const bucket of buckets.values()) {
    const count = bucket.items.length
    const lat = bucket.lat / count
    const lng = bucket.lng / count
    const size = 28 + Math.min(8, count * 1.5)

    const icon = new BMap.Icon(TRANSPARENT_GIF, new BMap.Size(size, size), {
      anchor: new BMap.Size(size / 2, size / 2),
      imageSize: new BMap.Size(size, size)
    })
    icon._html = `<span class="gis-cluster${bucket.danger ? ' is-danger' : ''}">${count}</span>`

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

let clusterStylesInjected = false
function ensureClusterStyles() {
  if (clusterStylesInjected) return
  clusterStylesInjected = true
  const style = document.createElement('style')
  style.setAttribute('data-bmap-gis', 'cluster-styles')
  style.textContent = `
    .gis-cluster {
      display: flex; align-items: center; justify-content: center;
      box-sizing: border-box; width: 100%; height: 100%;
      font-family: inherit; font-size: 11px; font-weight: 700; color: #6B4B1D;
      background: rgba(229,182,94,0.84);
      border: 2px solid rgba(255,255,255,0.92);
      border-radius: 50%;
      box-shadow: 0 2px 8px rgba(77,63,38,0.2);
    }
    .gis-cluster.is-danger { color: #fff; background: rgba(190,69,62,0.86); box-shadow: 0 2px 8px rgba(122,45,40,0.24); }
  `
  document.head.appendChild(style)
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
    const show = zoom >= cfg.labelZoom
    for (const item of overlayMap[cfg.key] || []) {
      const overlay = item.overlay
      const props = item.props
      if (!props) continue

      // 清除旧标签
      if (overlay._gisLabel) {
        try { map.removeOverlay(overlay._gisLabel) } catch { /* noop */ }
        overlay._gisLabel = null
      }

      if (!show) continue
      // 只给点位和管线主线加标签，避免同一管线多条叠加
      if (!(overlay instanceof BMap.Marker) && !(overlay instanceof BMap.Polyline)) continue

      let labelPoint
      if (overlay instanceof BMap.Marker) {
        labelPoint = overlay.getPosition()
      } else {
        const pts = overlay.getPath()
        if (!pts || pts.length === 0) continue
        labelPoint = pts[Math.floor(pts.length / 2)]
      }

      const label = new BMap.Label(props._title || '', {
        position: labelPoint,
        offset: new BMap.Size(0, -20)
      })
      label.setStyle({
        padding: '2px 7px',
        fontSize: '11px',
        fontWeight: '500',
        color: 'var(--app-text-1, #30353B)',
        backgroundColor: 'rgba(255,255,255,0.92)',
        border: '1px solid rgba(84,101,116,0.18)',
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
function selectFeature(cfg, feature, overlay, coords) {
  clearHighlight()
  const props = feature.properties
  selected.value = {
    key: cfg.key,
    cfg,
    properties: props,
    title: props._title,
    area: props._area,
    status: props._status,
    latlng: coords ? [coords[0], coords[1]] : (props._coords ? [props._coords[1], props._coords[0]] : null)
  }

  // 高亮覆盖物
  if (cfg.geometry === 'line') {
    // 找到主色线的 bdCoords
    let bdLine = null
    const item = overlayMap[cfg.key]?.find((x) => x.feature === feature)
    if (item) bdLine = item.bdCoords
    if (bdLine) {
      highlightOverlay = overlay
      // 选中描边
      const bdPoints = bdLine.map(([lng, lat]) => new BMap.Point(lng, lat))
      selectedOverlay = new BMap.Polyline(bdPoints, {
        strokeColor: '#315B78',
        strokeWeight: getPipelineStyle(cfg, props).strokeWeight + 6,
        strokeOpacity: 0.24,
        strokeLineCap: 'round',
        strokeLineJoin: 'round'
      })
      map.addOverlay(selectedOverlay)
    }
  } else {
    highlightOverlay = overlay
    const [lng, lat] = coords
    selectedOverlay = new BMap.Circle(new BMap.Point(lng, lat), getMarkerVisual(cfg, props).size + 8, {
      strokeColor: '#315B78',
      strokeWeight: 2,
      strokeOpacity: 0.72,
      fillColor: '#315B78',
      fillOpacity: 0.06,
      enableEditing: false
    })
    map.addOverlay(selectedOverlay)
  }

  drawerVisible.value = true
}

function clearHighlight() {
  if (selectedOverlay) {
    try { map.removeOverlay(selectedOverlay) } catch { /* noop */ }
    selectedOverlay = null
  }
  highlightOverlay = null
}

function onDrawerClosed() {
  clearHighlight()
  selected.value = null
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
    for (const key of Object.keys(sources)) delete sources[key]
    Object.assign(sources, result.sources)
    updatedAt.value = formatTime(result.loadedAt)
    clearHighlight()
    selected.value = null
    drawerVisible.value = false
    await renderAll()
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
        const icon = new BMap.Icon(TRANSPARENT_GIF, new BMap.Size(24, 24), {
          anchor: new BMap.Size(12, 24),
          imageSize: new BMap.Size(24, 24)
        })
        icon._html = `<div style="width:24px;height:24px;background:#1A73E8;border:2px solid #fff;border-radius:50%;box-shadow:0 2px 6px rgba(0,0,0,0.2);"></div>`
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
  let hasAny = false
  let firstPoint = null
  for (const cfg of GIS_LAYERS) {
    for (const feature of filteredFeatures(cfg.key)) {
      hasAny = true
      if (!firstPoint) {
        if (cfg.geometry === 'line') {
          const bdLine = overlayMap[cfg.key]?.find((x) => x.feature === feature)?.bdCoords
          if (bdLine && bdLine.length > 0) firstPoint = new BMap.Point(bdLine[0][0], bdLine[0][1])
        } else {
          const bdCoords = overlayMap[cfg.key]?.find((x) => x.feature === feature)?.bdCoords
          if (bdCoords) firstPoint = new BMap.Point(bdCoords[0], bdCoords[1])
        }
      }
    }
  }
  if (firstPoint) {
    map.centerAndZoom(firstPoint, 16)
  } else if (!hasAny) {
    // 无匹配，保持原位，不强制 fitBounds（百度的 getViewport 接口用法不同）
  }
}

function resetFilters() {
  keyword.value = ''
  appliedKeyword.value = ''
  areaFilter.value = ''
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
    navResult.value = { distance: result.distance, duration: result.duration }

    // 后端已经解码好路径坐标数组，直接用 BMap.Polyline 绘制
    const pathPoints = (result.path || []).map(([lng, lat]) => new BMap.Point(lng, lat))
    if (pathPoints.length >= 2) {
      routePolyline = new BMap.Polyline(pathPoints, {
        strokeColor: '#1A73E8',
        strokeWeight: 6,
        strokeOpacity: 0.78,
        strokeLineCap: 'round',
        strokeLineJoin: 'round',
        enableEditing: false
      })
      map.addOverlay(routePolyline)
      map.setViewport([routePolyline])
    }

    ElMessage.closeAll()
    ElMessage.success(`路线规划完成：${result.distance}，约 ${result.duration}`)
  } catch (err) {
    ElMessage.closeAll()
    ElMessage.error(err.message || '路线规划失败，请稍后重试')
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

watch([areaFilter, statusFilter, appliedKeyword], async () => {
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
}

.gis-mapwrap .gis-map {
  position: absolute;
  inset: 0;
  z-index: 0;
  width: 100%;
  height: 100%;
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

/* 左下角图例 */
.gis-legend {
  position: absolute;
  z-index: 1000;
  left: 14px;
  bottom: 22px;
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 7px 14px;
  font-size: 12px;
  color: var(--app-text-2);
  background-color: rgba(255, 255, 255, 0.88);
  -webkit-backdrop-filter: blur(16px) saturate(1.6);
  backdrop-filter: blur(16px) saturate(1.6);
  border: 1px solid var(--app-border);
  border-radius: var(--app-radius-tag);
  box-shadow: var(--app-shadow-float);
  pointer-events: none;
  white-space: nowrap;
}
.gis-legend__item {
  display: inline-flex;
  align-items: center;
  gap: 6px;
}
.gis-legend__dot {
  width: 9px;
  height: 9px;
  border-radius: 50%;
  box-shadow: 0 0 0 2px #fff;
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
  margin-top: 16px;
  padding-top: 14px;
  border-top: 1px solid var(--app-border);
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
@media (max-width: 1280px) {
  .gis-body { grid-template-columns: 250px minmax(0, 1fr); }
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
  .gis-nav-box {
    left: 14px;
    right: 14px;
    width: auto;
  }
}
</style>
