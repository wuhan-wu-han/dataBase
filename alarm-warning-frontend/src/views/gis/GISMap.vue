<template>
  <div class="gis-page">
    <!-- ===================== 顶部工具栏 ===================== -->
    <header class="gis-toolbar">
      <div class="gis-toolbar__main">
        <el-input
          v-model="keyword"
          class="gis-toolbar__search"
          placeholder="搜索管线 / 设备 / 预警编号"
          clearable
          :prefix-icon="Search"
          @keyup.enter="onSearch"
          @clear="onSearch"
        />
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
        placeholder="搜索管线 / 设备 / 预警编号"
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
        <!-- Leaflet 容器 -->
        <div ref="mapEl" class="gis-map"></div>

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
import {
  Search, Refresh, Filter, Files, Close,
  DArrowLeft, DArrowRight, Loading, WarningFilled, Aim
} from '@element-plus/icons-vue'
import 'leaflet/dist/leaflet.css'
import L from 'leaflet'
import LayerTree from './LayerTree.vue'
import { fetchAllLayers } from '@/api/gis'
import {
  GIS_LAYERS, LAYER_MAP, ANSAI_CENTER,
  AREAS, STATUS, STATUS_OPTIONS, toneColor
} from '@/config/gisLayers'

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

/** 图层开关与要素计数（配置本身保持只读，状态单独存放） */
const visible = reactive(Object.fromEntries(GIS_LAYERS.map((l) => [l.key, true])))
const counts = reactive(Object.fromEntries(GIS_LAYERS.map((l) => [l.key, 0])))
const sources = reactive({})

// ---------------------------------------------------------------------------
// Leaflet 运行时对象（非响应式，避免 Vue 代理 Leaflet 内部结构）
// ---------------------------------------------------------------------------
let map = null
let resizeObserver = null
let viewportQuery = null
let viewportHandler = null
let resizeFrame = null
const groups = {}        // key -> L.LayerGroup
const collections = {}   // key -> GeoJSON.FeatureCollection（全量，筛选在渲染时进行）
const rendered = {}      // key -> [{ layers, feature, cfg, isTrunk }]，用于按 zoom 精细显隐
let clusterGroup = null
let networkNodeGroup = null
let selectedOverlay = null
let highlighted = null   // { layer, cfg, props }

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
function createMap() {
  map = L.map(mapEl.value, {
    center: ANSAI_CENTER,
    zoom: 13,
    minZoom: 9,
    maxZoom: 19,
    zoomControl: false,
    attributionControl: true
  })

  // 缩放控件放右上角，避开左上角图层面板与移动端底部抽屉
  L.control.zoom({ position: 'topright' }).addTo(map)

  // 业务图层使用独立 pane，明确控制覆盖顺序，避免依赖添加先后。
  const panes = [
    ['gis-risk-pane', 310],
    ['gis-pipeline-pane', 410],
    ['gis-node-pane', 470],
    ['gis-facility-pane', 510],
    ['gis-warning-pane', 610],
    ['gis-critical-pane', 650],
    ['gis-selected-pane', 700]
  ]
  for (const [name, zIndex] of panes) {
    const pane = map.createPane(name)
    pane.style.zIndex = String(zIndex)
  }

  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '&copy; OpenStreetMap contributors',
    minZoom: 9,
    maxZoom: 19
  }).addTo(map)

  for (const cfg of GIS_LAYERS) {
    groups[cfg.key] = L.layerGroup()
    rendered[cfg.key] = []
  }

  clusterGroup = L.layerGroup().addTo(map)
  networkNodeGroup = L.layerGroup().addTo(map)

  map.on('click', () => {
    drawerVisible.value = false
    clearHighlight()
  })
  map.on('zoomend', () => {
    applyZoomVisibility()
    applyLabels()
    renderClusters()
    renderNetworkNodes()
  })
}

async function loadBoundary() {
  try {
    const response = await fetch('/ansai-boundary.geojson')
    if (!response.ok) throw new Error(`HTTP ${response.status}`)
    const geojson = await response.json()
    const layer = L.geoJSON(geojson, {
      pane: 'gis-risk-pane',
      style: getRiskAreaStyle(false),
      onEachFeature: (_feature, polygon) => {
        polygon.bindTooltip('安塞区基础设施监管范围', {
          sticky: true,
          className: 'gis-tooltip'
        })
        polygon.on({
          mouseover: () => polygon.setStyle(getRiskAreaStyle(true)),
          mouseout: () => polygon.setStyle(getRiskAreaStyle(false))
        })
      }
    })
    layer.addTo(map)
    map.fitBounds(layer.getBounds(), { padding: [28, 28] })
  } catch (err) {
    console.warn('[GIS] 安塞区边界加载失败，回退到默认中心点:', err)
    map.setView(ANSAI_CENTER, 13)
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
// 渲染：地图组件只消费标准 GeoJSON Feature
// ---------------------------------------------------------------------------
function getRiskAreaStyle(active = false) {
  return {
    color: active ? '#718AA0' : '#8294A3',
    weight: active ? 2 : 1.5,
    opacity: active ? 0.78 : 0.58,
    fillColor: '#7890A4',
    fillOpacity: active ? 0.075 : 0.045,
    dashArray: active ? '7 5' : '6 6',
    lineCap: 'round',
    lineJoin: 'round'
  }
}

function isTrunkPipeline(props) {
  if (props.is_main === true || props.isMain === true || props.trunk === true) return true
  const level = String(props.pipeline_level ?? props.level ?? props.grade ?? '').toLowerCase()
  if (level.includes('main') || level.includes('trunk') || level.includes('主干')) return true
  return Number(props.diameter ?? props.pipeDiameter ?? 0) >= 250
}

function getPipelineStyle(cfg, props, state = 'default') {
  const status = props._status || 'normal'
  const trunk = isTrunkPipeline(props)
  const typeColor = cfg.color
  const color = status === 'danger'
    ? '#C94F46'
    : status === 'warning' ? '#D18B3C' : typeColor
  const normalWeight = trunk ? 2.4 : 1.65
  const weight = normalWeight + (status === 'danger' ? 0.55 : status === 'warning' ? 0.25 : 0)
  const opacity = status === 'danger' ? 0.92 : status === 'warning' ? 0.82 : (trunk ? 0.74 : 0.64)

  if (state === 'hover') return { color, weight: weight + 0.8, opacity: Math.min(1, opacity + 0.18) }
  if (state === 'selected') return { color, weight: weight + 1.45, opacity: 1 }
  return { color, weight, opacity }
}

function getMarkerVisual(cfg, props) {
  const status = props._status || 'normal'
  const isAlert = cfg.key === 'alert'
  const isRisk = cfg.key === 'hazard'
  const size = status === 'danger' ? (isAlert || isRisk ? 15 : 13) : status === 'warning' ? 11 : (isAlert ? 10 : 8)
  const pane = status === 'danger'
    ? 'gis-critical-pane'
    : (status === 'warning' || isAlert || isRisk) ? 'gis-warning-pane' : 'gis-facility-pane'
  return { size, pane }
}

function shouldPulse(cfg, props) {
  if (props._status !== 'danger') return false
  const level = String(props.warning_level ?? props.warningLevel ?? props.alertLevel ?? props.risk_level ?? props.riskLevel ?? '').toLowerCase()
  return (cfg.key === 'alert' && (level.includes('red') || level.includes('红')))
    || (cfg.key === 'hazard' && level.includes('极高'))
}

/**
 * 点位图标：class 片段全部来自固定配置（图层 key / 三态 / 白名单图标种类），
 * 不拼接任何后端文本，避免注入风险。字形由 CSS ::before 提供。
 */
function pointIcon(cfg, props, isSelected = false) {
  const { size } = getMarkerVisual(cfg, props)
  const classes = [
    'gis-pin',
    `gis-pin--${cfg.key}`,
    `gis-pin--s-${props._status}`,
    `gis-pin--k-${props._iconKind || 'default'}`
  ]
  if (shouldPulse(cfg, props)) classes.push('is-pulse')
  if (isSelected) classes.push('is-selected')
  const hostSize = Math.max(24, size + 12)
  return L.divIcon({
    className: 'gis-pin-host',
    html: `<span class="${classes.join(' ')}"></span>`,
    iconSize: [hostSize, hostSize],
    iconAnchor: [hostSize / 2, hostSize / 2]
  })
}

function bindFeature(cfg, feature, layer) {
  layer.__gisProps = feature.properties
  layer.__gisCfg = cfg
  layer.__gisTooltipMode = 'hover'
  layer.bindTooltip(feature.properties._title, {
    sticky: true,
    direction: 'top',
    offset: [0, -8],
    opacity: 0.96,
    className: 'gis-tooltip'
  })
  layer.on('click', (event) => {
    L.DomEvent.stopPropagation(event)
    selectFeature(cfg, feature, layer, event.latlng)
  })
}

function updateLineState(layer, state) {
  const cfg = layer.__gisCfg
  const props = layer.__gisProps
  if (!cfg || !props) return
  const style = getPipelineStyle(cfg, props, state)
  layer.__gisMain?.setStyle(style)
  layer.setStyle({
    color: state === 'selected' ? '#FFFFFF' : '#F7F8F6',
    weight: style.weight + (state === 'selected' ? 3.2 : 2.2),
    opacity: state === 'default' ? 0.48 : 0.82
  })
  if (layer.__gisGlow) {
    layer.__gisGlow.setStyle({
      weight: style.weight + (state === 'selected' ? 5.5 : 4),
      opacity: state === 'default' ? 0.16 : 0.28
    })
  }
}

function buildLine(cfg, feature, group) {
  const coords = feature.geometry.coordinates.map(([lon, lat]) => [lat, lon])
  const style = getPipelineStyle(cfg, feature.properties)

  // 细浅描边用于从道路中分离，并兼任点击热区；不再制造整条粗白色发光线。
  const casing = L.polyline(coords, {
    pane: 'gis-pipeline-pane',
    color: '#F7F8F6',
    weight: style.weight + 2.2,
    opacity: 0.48,
    lineCap: 'round',
    lineJoin: 'round'
  })
  const main = L.polyline(coords, {
    pane: 'gis-pipeline-pane',
    ...style,
    lineCap: 'round',
    lineJoin: 'round',
    interactive: false
  })
  let glow = null
  if (feature.properties._status === 'danger') {
    glow = L.polyline(coords, {
      pane: 'gis-pipeline-pane',
      color: '#C94F46',
      weight: style.weight + 4,
      opacity: 0.16,
      lineCap: 'round',
      lineJoin: 'round',
      interactive: false
    })
    glow.addTo(group)
  }
  bindFeature(cfg, feature, casing)
  casing.__gisMain = main
  casing.__gisGlow = glow
  casing.__gisCoords = coords
  casing.on({
    mouseover: () => { if (highlighted?.layer !== casing) updateLineState(casing, 'hover') },
    mouseout: () => { if (highlighted?.layer !== casing) updateLineState(casing, 'default') }
  })
  casing.addTo(group)
  main.addTo(group)
  return {
    cfg,
    feature,
    isTrunk: isTrunkPipeline(feature.properties),
    layers: [glow, casing, main].filter(Boolean),
    interactiveLayer: casing
  }
}

function buildPoint(cfg, feature, group) {
  const [lon, lat] = feature.geometry.coordinates
  const visual = getMarkerVisual(cfg, feature.properties)
  const marker = L.marker([lat, lon], {
    icon: pointIcon(cfg, feature.properties),
    pane: visual.pane,
    zIndexOffset: feature.properties._status === 'danger' ? 500 : feature.properties._status === 'warning' ? 250 : 0,
    riseOnHover: true,
    keyboard: false
  })
  bindFeature(cfg, feature, marker)
  marker.on({
    mouseover: () => marker.getElement()?.classList.add('is-hovered'),
    mouseout: () => marker.getElement()?.classList.remove('is-hovered')
  })
  marker.addTo(group)
  return { cfg, feature, layers: [marker], interactiveLayer: marker }
}

function renderLayer(key) {
  const cfg = LAYER_MAP[key]
  const group = groups[key]
  if (!cfg || !group) return
  group.clearLayers()
  rendered[key] = []
  const features = filteredFeatures(key)
  counts[key] = features.length
  for (const feature of features) {
    const bundle = cfg.geometry === 'line'
      ? buildLine(cfg, feature, group)
      : buildPoint(cfg, feature, group)
    rendered[key].push(bundle)
  }
}

function renderAll() {
  for (const cfg of GIS_LAYERS) renderLayer(cfg.key)
  applyZoomVisibility()
  renderClusters()
  renderNetworkNodes()
  applyLabels()
}

function setBundleVisible(group, bundle, show) {
  for (const layer of bundle.layers) {
    if (show && !group.hasLayer(layer)) group.addLayer(layer)
    else if (!show && group.hasLayer(layer)) group.removeLayer(layer)
  }
}

function shouldShowFeatureAtZoom(cfg, feature, zoom) {
  const status = feature.properties._status || 'normal'
  if (cfg.geometry === 'line') return zoom >= 12 || isTrunkPipeline(feature.properties)
  if (zoom <= 12) return false // 低缩放由风险/预警聚合点表达
  if (cfg.key === 'alert' || cfg.key === 'hazard') return zoom >= 15 || status !== 'normal'
  if (cfg.key === 'asset') return zoom >= 15 || (zoom >= 13 && status !== 'normal')
  if (cfg.key === 'manhole') return zoom >= 16 || (zoom >= 15 && status === 'danger')
  return zoom >= cfg.minZoom
}

/** 按缩放级别控制整层与单要素 LOD */
function applyZoomVisibility() {
  if (!map) return
  const zoom = map.getZoom()
  for (const cfg of GIS_LAYERS) {
    const group = groups[cfg.key]
    if (!group) continue
    if (!visible[cfg.key]) {
      if (map.hasLayer(group)) map.removeLayer(group)
      continue
    }
    if (!map.hasLayer(group)) group.addTo(map)
    for (const bundle of rendered[cfg.key] || []) {
      setBundleVisible(group, bundle, shouldShowFeatureAtZoom(cfg, bundle.feature, zoom))
    }
  }
}

/**
 * 低缩放级别的轻量聚合。无需额外插件，按当前地图投影的像素网格合并风险/预警点；
 * 放大到 13 级后自动拆散为业务单点。
 */
function renderClusters() {
  if (!map || !clusterGroup) return
  clusterGroup.clearLayers()
  const zoom = map.getZoom()
  if (zoom > 12) return

  const cellSize = zoom <= 10 ? 88 : 70
  const buckets = new Map()
  for (const key of ['hazard', 'alert']) {
    if (!visible[key]) continue
    const cfg = LAYER_MAP[key]
    for (const feature of filteredFeatures(key)) {
      if (feature.properties._status === 'normal') continue
      const [lon, lat] = feature.geometry.coordinates
      const pixel = map.project(L.latLng(lat, lon), zoom)
      const bucketKey = `${Math.floor(pixel.x / cellSize)}:${Math.floor(pixel.y / cellSize)}`
      const bucket = buckets.get(bucketKey) || { items: [], lat: 0, lon: 0, danger: false }
      bucket.items.push({ cfg, feature })
      bucket.lat += lat
      bucket.lon += lon
      bucket.danger ||= feature.properties._status === 'danger'
      buckets.set(bucketKey, bucket)
    }
  }

  for (const bucket of buckets.values()) {
    const count = bucket.items.length
    const lat = bucket.lat / count
    const lon = bucket.lon / count
    const size = 28 + Math.min(8, count * 1.5)
    const marker = L.marker([lat, lon], {
      pane: bucket.danger ? 'gis-critical-pane' : 'gis-warning-pane',
      icon: L.divIcon({
        className: 'gis-cluster-host',
        html: `<span class="gis-cluster${bucket.danger ? ' is-danger' : ''}">${count}</span>`,
        iconSize: [size, size],
        iconAnchor: [size / 2, size / 2]
      }),
      keyboard: false
    })
    marker.bindTooltip(`${count} 个风险 / 预警点，点击放大查看`, {
      direction: 'top',
      className: 'gis-tooltip'
    })
    marker.on('click', (event) => {
      L.DomEvent.stopPropagation(event)
      const bounds = L.latLngBounds(bucket.items.map(({ feature }) => {
        const [itemLon, itemLat] = feature.geometry.coordinates
        return [itemLat, itemLon]
      }))
      if (count === 1) map.setView([lat, lon], 14)
      else map.fitBounds(bounds, { padding: [54, 54], maxZoom: 14 })
    })
    marker.addTo(clusterGroup)
  }
}

/** 高缩放级别基于已有管线坐标显示端点/转折点，不额外虚构拓扑数据。 */
function renderNetworkNodes() {
  if (!map || !networkNodeGroup) return
  networkNodeGroup.clearLayers()
  if (map.getZoom() < 16) return
  const seen = new Set()
  for (const cfg of GIS_LAYERS.filter((item) => item.geometry === 'line')) {
    if (!visible[cfg.key]) continue
    for (const bundle of rendered[cfg.key] || []) {
      const coords = bundle.feature.geometry.coordinates
      coords.forEach(([lon, lat], index) => {
        const id = `${lon.toFixed(5)}:${lat.toFixed(5)}`
        if (seen.has(id)) return
        seen.add(id)
        const kind = index === 0 || index === coords.length - 1 ? '端点' : '转折点'
        const node = L.circleMarker([lat, lon], {
          pane: 'gis-node-pane',
          radius: 3,
          color: '#FFFFFF',
          weight: 1,
          opacity: 0.9,
          fillColor: cfg.color,
          fillOpacity: 0.82
        })
        node.bindTooltip(`${bundle.feature.properties._title} · ${kind}`, {
          sticky: true,
          className: 'gis-tooltip'
        })
        node.on('click', (event) => {
          L.DomEvent.stopPropagation(event)
          selectFeature(cfg, bundle.feature, bundle.interactiveLayer, event.latlng)
        })
        node.addTo(networkNodeGroup)
      })
    }
  }
}

/** 高缩放级别显示常驻标签 */
function applyLabels() {
  if (!map) return
  const zoom = map.getZoom()
  for (const cfg of GIS_LAYERS) {
    if (cfg.labelZoom > 90) continue
    const group = groups[cfg.key]
    if (!group) continue
    const show = zoom >= cfg.labelZoom
    group.eachLayer((layer) => {
      const props = layer.__gisProps
      if (!props) return
      const desiredMode = show ? 'label' : 'hover'
      if (layer.__gisTooltipMode === desiredMode) return
      layer.unbindTooltip()
      if (show) {
        layer.bindTooltip(props._title, {
          permanent: true,
          direction: 'top',
          offset: [0, -13],
          className: 'gis-label'
        }).openTooltip()
      } else {
        layer.bindTooltip(props._title, {
          sticky: true,
          direction: 'top',
          offset: [0, -8],
          opacity: 0.96,
          className: 'gis-tooltip'
        })
      }
      layer.__gisTooltipMode = desiredMode
    })
  }
}

// ---------------------------------------------------------------------------
// 选中 / 高亮
// ---------------------------------------------------------------------------
function selectFeature(cfg, feature, layer, latlng) {
  clearHighlight()
  const props = feature.properties
  selected.value = {
    key: cfg.key,
    cfg,
    properties: props,
    title: props._title,
    area: props._area,
    status: props._status,
    latlng: latlng ? [latlng.lng, latlng.lat] : (props._coords || null)
  }
  highlighted = { layer, cfg, props }

  if (cfg.geometry === 'line') {
    updateLineState(layer, 'selected')
    layer.__gisMain?.bringToFront()
    layer.bringToFront()
    selectedOverlay = L.polyline(layer.__gisCoords, {
      pane: 'gis-selected-pane',
      color: '#315B78',
      weight: getPipelineStyle(cfg, props).weight + 3.8,
      opacity: 0.24,
      lineCap: 'round',
      lineJoin: 'round',
      interactive: false
    }).addTo(map)
  } else {
    layer.setIcon(pointIcon(cfg, props, true))
    layer.setZIndexOffset(1200)
    const markerVisual = getMarkerVisual(cfg, props)
    selectedOverlay = L.circleMarker(layer.getLatLng(), {
      pane: 'gis-selected-pane',
      radius: markerVisual.size / 2 + 4,
      color: '#315B78',
      weight: 2,
      opacity: 0.72,
      fill: false,
      interactive: false
    }).addTo(map)
  }

  drawerVisible.value = true
}

function clearHighlight() {
  if (selectedOverlay) {
    selectedOverlay.remove()
    selectedOverlay = null
  }
  if (!highlighted) return
  const { layer, cfg, props } = highlighted
  try {
    if (cfg.geometry === 'line') {
      updateLineState(layer, 'default')
    } else {
      layer.setIcon(pointIcon(cfg, props, false))
      layer.setZIndexOffset(props._status === 'danger' ? 500 : props._status === 'warning' ? 250 : 0)
    }
  } catch {
    // 图层已因筛选/刷新被重建，忽略
  }
  highlighted = null
}

function onDrawerClosed() {
  clearHighlight()
  selected.value = null
  // 抽屉是覆盖层，不改变地图尺寸；此处仅保证面板/抽屉动画结束后瓦片重排正确
  map?.invalidateSize()
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
    renderAll()
    applyLabels()
  } catch (err) {
    console.error('[GIS] 数据加载失败:', err)
    loadError.value = 'GIS 数据加载失败，请检查后端服务或网关连通性'
  } finally {
    loading.value = false
  }
}

function onSearch() {
  appliedKeyword.value = keyword.value
  if (appliedKeyword.value.trim()) fitToMatches()
}

function fitToMatches() {
  const bounds = L.latLngBounds([])
  let total = 0
  for (const cfg of GIS_LAYERS) {
    for (const feature of filteredFeatures(cfg.key)) {
      const coords = feature.geometry.type === 'Point'
        ? [feature.geometry.coordinates]
        : feature.geometry.coordinates
      for (const [lon, lat] of coords) {
        bounds.extend([lat, lon])
        total++
      }
    }
  }
  if (total > 0 && bounds.isValid()) {
    map.fitBounds(bounds, { padding: [60, 60], maxZoom: 16 })
  }
}

function resetFilters() {
  keyword.value = ''
  appliedKeyword.value = ''
  areaFilter.value = ''
  statusFilter.value = ''
}

// ---------------------------------------------------------------------------
// 交互
// ---------------------------------------------------------------------------
function onToggleLayer(key, value) {
  visible[key] = value
}

function togglePanel() {
  panelCollapsed.value = !panelCollapsed.value
  // 栅格列宽过渡结束后重算地图尺寸（ResizeObserver 是主保障，这里兜底）
  nextTick(() => setTimeout(() => map?.invalidateSize(), 320))
}

watch(visible, () => {
  applyZoomVisibility()
  renderClusters()
  renderNetworkNodes()
})
// 关键字必须一并监听：否则只有关键字命中的空数据态点「重置筛选」时，
// 区域/状态本就为空、watcher 不触发，地图会一直停在空白。
watch([areaFilter, statusFilter, appliedKeyword], () => renderAll())

// ---------------------------------------------------------------------------
// 生命周期
// ---------------------------------------------------------------------------
function setupViewportWatcher() {
  if (typeof window.matchMedia !== 'function') return
  // 与下方 CSS 的 1024px 断点保持一致：768–1024px 区间里桌面侧边栏 + 图层面板
  // 会把地图挤到两百多像素宽，因此这里就切换到紧凑形态（图层树进底部抽屉）。
  viewportQuery = window.matchMedia('(max-width: 1024px)')
  viewportHandler = () => { isMobile.value = viewportQuery.matches }
  viewportHandler()
  if (viewportQuery.addEventListener) viewportQuery.addEventListener('change', viewportHandler)
  else viewportQuery.addListener(viewportHandler)
}

onMounted(async () => {
  setupViewportWatcher()
  createMap()

  // 容器尺寸变化（窗口缩放、侧栏折叠、面板折叠）后必须重算 Leaflet 尺寸
  if (typeof ResizeObserver !== 'undefined') {
    resizeObserver = new ResizeObserver(() => {
      if (resizeFrame) cancelAnimationFrame(resizeFrame)
      resizeFrame = requestAnimationFrame(() => { map?.invalidateSize() })
    })
    resizeObserver.observe(mapEl.value)
  }

  await Promise.all([loadBoundary(), reload()])
})

onBeforeUnmount(() => {
  if (resizeObserver) {
    resizeObserver.disconnect()
    resizeObserver = null
  }
  if (resizeFrame) {
    cancelAnimationFrame(resizeFrame)
    resizeFrame = null
  }
  if (viewportQuery && viewportHandler) {
    if (viewportQuery.removeEventListener) viewportQuery.removeEventListener('change', viewportHandler)
    else viewportQuery.removeListener(viewportHandler)
  }
  viewportQuery = null
  viewportHandler = null
  if (map) {
    map.remove()
    map = null
  }
})
</script>

<!--
  非 scoped：Leaflet 的 divIcon 标记、tooltip、缩放控件由 Leaflet 自己创建 DOM，
  不带 Vue 的 data-v 属性，scoped 选择器无法命中。
  这里统一用 .gis-page / .gis-mapwrap / .gis-drawer 三个命名空间隔离，避免污染全局。
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
/* 折叠后 0px 列上仍会画出 1px 右边框，在地图左侧留一条竖线 */
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

/* Leaflet 容器：绝对定位铺满，永远不撑破栅格 */
.gis-mapwrap .gis-map {
  position: absolute;
  inset: 0;
  z-index: 0;
  width: 100%;
  height: 100%;
}

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
/* 左上角，但下移避开 Leaflet 缩放控件（缩放在右上，互不遮挡） */
.gis-fab--panel {
  top: 14px;
  left: 14px;
}

/* 状态浮层：加载 / 失败 / 空 */
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

/* ===================== Leaflet 元素 ===================== */
.gis-mapwrap .leaflet-container {
  font-family: var(--app-font-family);
  background-color: #EAECEF;
  outline: none;
}

/* 轻微压低 OSM 底图，不牺牲道路、水系和行政边界的辨识度。 */
.gis-mapwrap .leaflet-tile-pane {
  filter: saturate(0.72) contrast(0.92) brightness(1.035);
}

.gis-mapwrap .leaflet-control-zoom {
  border: 1px solid var(--app-border) !important;
  border-radius: 12px !important;
  overflow: hidden;
  box-shadow: var(--app-shadow-float) !important;
  margin: 14px 14px 0 0 !important;
}
.gis-mapwrap .leaflet-control-zoom a {
  width: 32px !important;
  height: 32px !important;
  line-height: 30px !important;
  font-size: 16px !important;
  color: var(--app-text-1) !important;
  background-color: rgba(255, 255, 255, 0.92) !important;
  border-bottom: 1px solid var(--app-border) !important;
}
.gis-mapwrap .leaflet-control-zoom a:hover {
  background-color: var(--app-hover) !important;
}
.gis-mapwrap .leaflet-control-zoom a.leaflet-disabled {
  color: var(--app-text-4) !important;
}

.gis-mapwrap .leaflet-control-attribution {
  padding: 2px 8px !important;
  font-size: 10px !important;
  color: var(--app-text-4) !important;
  background-color: rgba(255, 255, 255, 0.72) !important;
  border-top-left-radius: 8px;
}

/* 高缩放级别的常驻标签 */
.gis-mapwrap .gis-label {
  padding: 2px 7px;
  font-family: var(--app-font-family);
  font-size: 11px;
  font-weight: 500;
  color: var(--app-text-1);
  white-space: nowrap;
  background-color: rgba(255, 255, 255, 0.92);
  border: 1px solid var(--app-border);
  border-radius: var(--app-radius-tag);
  box-shadow: var(--app-shadow-float);
}
.gis-mapwrap .gis-label::before {
  display: none;
}

/* hover tooltip：克制的白色信息卡，不使用暗色气泡或重阴影。 */
.gis-mapwrap .gis-tooltip {
  padding: 5px 8px;
  font-family: var(--app-font-family);
  font-size: 11px;
  font-weight: 500;
  line-height: 1.35;
  color: #30353B;
  white-space: nowrap;
  background: rgba(255, 255, 255, 0.96);
  border: 1px solid rgba(84, 101, 116, 0.18);
  border-radius: 6px;
  box-shadow: 0 3px 10px rgba(42, 54, 64, 0.12);
}
.gis-mapwrap .gis-tooltip::before {
  border-top-color: rgba(255, 255, 255, 0.96);
}

/* ===================== 点位图标 ===================== */
.gis-mapwrap .gis-pin-host {
  display: flex !important;
  align-items: center;
  justify-content: center;
  background: transparent;
  border: 0;
}

.gis-mapwrap .gis-pin {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  box-sizing: border-box;
  width: 8px;
  height: 8px;
  font-family: var(--app-font-family);
  font-size: 0;
  font-weight: 600;
  line-height: 1;
  color: transparent;
  background-color: #71847A;
  border: 1px solid rgba(255, 255, 255, 0.92);
  border-radius: 50%;
  box-shadow: 0 1px 3px rgba(37, 49, 43, 0.26);
  transition: transform 0.16s ease, box-shadow 0.16s ease, opacity 0.16s ease;
}
.gis-mapwrap .gis-pin::before {
  content: '';
}
.gis-mapwrap .gis-pin.is-selected {
  transform: scale(1.3);
  box-shadow: 0 0 0 3px rgba(52, 82, 105, 0.22), 0 2px 7px rgba(37, 49, 43, 0.3);
}
.gis-mapwrap .gis-pin-host.is-hovered .gis-pin {
  transform: scale(1.24);
}

/* 三态底色 */
.gis-mapwrap .gis-pin--s-normal { background-color: #71847A; }
.gis-mapwrap .gis-pin--s-warning {
  width: 11px;
  height: 11px;
  font-size: 8px;
  color: #fff;
  background-color: #D59435;
  border-width: 1.5px;
}
.gis-mapwrap .gis-pin--s-danger {
  width: 15px;
  height: 15px;
  font-size: 9px;
  color: #fff;
  background-color: #C84740;
  border-width: 1.5px;
  box-shadow: 0 2px 5px rgba(130, 48, 43, 0.3);
}

/* 预警事件：按等级用固定色，覆盖三态底色 */
.gis-mapwrap .gis-pin--alert {
  width: 10px;
  height: 10px;
  font-size: 8px;
  color: #fff;
}
.gis-mapwrap .gis-pin--alert.gis-pin--k-blue { background-color: #5D82A3; }
.gis-mapwrap .gis-pin--alert.gis-pin--k-yellow { background-color: #D3A23B; color: #fff; }
.gis-mapwrap .gis-pin--alert.gis-pin--k-orange { width: 12px; height: 12px; background-color: #D4773F; }
.gis-mapwrap .gis-pin--alert.gis-pin--k-red { width: 15px; height: 15px; font-size: 9px; background-color: #C84740; }

/* 分类字形：内容全部来自 CSS，不拼接后端文本 */
.gis-mapwrap .gis-pin--k-gas::before { content: '燃'; }
.gis-mapwrap .gis-pin--k-water::before { content: '水'; }
.gis-mapwrap .gis-pin--k-drain::before { content: '排'; }
.gis-mapwrap .gis-pin--k-sensor::before { content: '感'; }
.gis-mapwrap .gis-pin--k-camera::before { content: '摄'; }
.gis-mapwrap .gis-pin--k-detector::before { content: '探'; }
.gis-mapwrap .gis-pin--k-fan::before { content: '风'; }
.gis-mapwrap .gis-pin--alert::before { content: '!'; font-size: inherit; }

/* 高风险脉冲动画 */
.gis-mapwrap .gis-pin.is-pulse::after {
  content: '';
  position: absolute;
  inset: -5px;
  border-radius: 50%;
  border: 1.5px solid currentColor;
  color: #C84740;
  opacity: 0;
  animation: gis-pulse 1.8s ease-out infinite;
  pointer-events: none;
}
@keyframes gis-pulse {
  0% { transform: scale(0.8); opacity: 0.38; }
  72% { transform: scale(1.55); opacity: 0; }
  100% { transform: scale(1.55); opacity: 0; }
}

/* 低缩放风险聚合：数量清楚，但体量显著小于旧版大圆点。 */
.gis-mapwrap .gis-cluster-host {
  display: flex !important;
  align-items: center;
  justify-content: center;
  background: transparent;
  border: 0;
}
.gis-mapwrap .gis-cluster {
  display: flex;
  align-items: center;
  justify-content: center;
  box-sizing: border-box;
  width: 100%;
  height: 100%;
  font-family: var(--app-font-family);
  font-size: 11px;
  font-weight: 700;
  color: #6B4B1D;
  background: rgba(229, 182, 94, 0.84);
  border: 2px solid rgba(255, 255, 255, 0.92);
  border-radius: 50%;
  box-shadow: 0 2px 8px rgba(77, 63, 38, 0.2);
}
.gis-mapwrap .gis-cluster.is-danger {
  color: #fff;
  background: rgba(190, 69, 62, 0.86);
  box-shadow: 0 2px 8px rgba(122, 45, 40, 0.24);
}

@media (prefers-reduced-motion: reduce) {
  .gis-mapwrap .gis-pin.is-pulse::after { animation: none; }
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

/* ≤1024px 进入紧凑形态：工具栏收成图标按钮，图层树移入底部抽屉，地图独占一列 */
@media (max-width: 1024px) {
  .gis-toolbar {
    gap: 10px;
    padding: 8px 12px;
  }
  /* 桌面工具栏整组隐藏，改用三个图标按钮 */
  .gis-toolbar__main { display: none; }
  .gis-toolbar__meta { display: none; }
  .gis-toolbar__mobile {
    display: flex;
    flex: 1 1 auto;
    justify-content: flex-end;
  }

  /* 图层树移入底部抽屉：主体只剩地图一列 */
  .gis-body,
  .gis-body.is-collapsed {
    grid-template-columns: minmax(0, 1fr);
  }
  .gis-panel { display: none; }
  .gis-fab--panel { display: none; }

  .gis-legend {
    left: 12px;
    right: 12px;
    bottom: 18px;
    gap: 10px;
    justify-content: center;
    font-size: 11px;
  }
  .gis-mapwrap .leaflet-control-zoom {
    margin: 12px 12px 0 0 !important;
  }
  .gis-state {
    top: 12px;
    padding: 8px 14px;
    font-size: 12px;
  }
}

/* 390px 窄屏：确保不出现逐字换行与横向溢出 */
@media (max-width: 400px) {
  .gis-toolbar { gap: 6px; padding: 8px 10px; }
  .gis-toolbar__mobile .el-button { margin-left: 0; }
  .gis-searchrow { padding: 8px 10px; }
  .gis-detail__row { gap: 10px; }
}
</style>
