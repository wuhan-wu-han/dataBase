<template>
  <div class="gis-map">
    <!-- 地图容器 -->
    <div ref="mapContainer" class="gis-map__viewport"></div>

    <!-- 图层控制面板（左上角浮动） -->
    <div class="gis-map__layer-panel">
      <div class="gis-map__panel-header">
        <span class="gis-map__panel-title">图层控制</span>
      </div>
      <div class="gis-map__layer-list">
        <label class="gis-map__layer-item" v-for="layer in layerGroups" :key="layer.key">
          <input type="checkbox" :checked="layer.visible" @change="toggleLayer(layer.key, $event.target.checked)" />
          <span class="gis-map__layer-dot" :style="{ background: layer.color }"></span>
          <span class="gis-map__layer-label">{{ layer.label }}</span>
          <span class="gis-map__layer-count">{{ layer.count }}</span>
        </label>
      </div>
    </div>

    <!-- Popup 覆盖层 -->
    <div ref="popupRef" class="gis-popup"></div>
  </div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount, watch } from 'vue'
import { useRouter } from 'vue-router'
import 'leaflet/dist/leaflet.css'
import L from 'leaflet'
import { fetchAllLayers } from '@/api/gis'

const router = useRouter()
const mapContainer = ref(null)
const popupRef = ref(null)

// ---------------------------------------------------------------------------
// 图层组定义（7 个）
// ---------------------------------------------------------------------------
const layerGroups = ref([
  { key: 'gas',       label: '燃气管网',   color: '#FF3B30', visible: true, count: 0 },
  { key: 'water',     label: '供水管网',   color: '#0071E3', visible: true, count: 0 },
  { key: 'waste',     label: '废水管网',   color: '#30C0C0', visible: true, count: 0 },
  { key: 'manhole',   label: '智能井盖',   color: '#8E8E93', visible: true, count: 0 },
  { key: 'hazard',    label: '道路塌陷',   color: '#FF9500', visible: true, count: 0 },
  { key: 'asset',     label: '资产设备',   color: '#34C759', visible: true, count: 0 },
  { key: 'alert',     label: '预警事件',   color: '#0071E3', visible: true, count: 0 }
])

// ---------------------------------------------------------------------------
// 地图实例 & 图层引用
// ---------------------------------------------------------------------------
let mapInstance = null
let vectorLayers = {}
let boundaryLayer = null

// Ansai 中心坐标
const CENTER = [36.55, 109.22] // [lat, lon] for Leaflet

// ---------------------------------------------------------------------------
// Popup 相关
// ---------------------------------------------------------------------------
let olPopup = null

function initPopup() {
  const popupEl = popupRef.value
  olPopup = L.popup({
    closeButton: true,
    autoPan: true,
    autoPanPadding: [50, 50]
  })
  olPopup.setElement(popupEl)
}

function showPopup(latlng, htmlContent) {
  const popupEl = popupRef.value
  popupEl.innerHTML = htmlContent
  popupEl.classList.add('gis-popup--visible')
  olPopup.setLatLng(latlng).setContent(popupEl).openOn(mapInstance)
}

function hidePopup() {
  const popupEl = popupRef.value
  popupEl.classList.remove('gis-popup--visible')
  popupEl.innerHTML = ''
  if (olPopup) olPopup.close()
}

// ---------------------------------------------------------------------------
// Popup 卡片渲染
// ---------------------------------------------------------------------------

function renderGasCard(props) {
  const statusType = props.status === '告警' ? 'danger' : 'success'
  const riskBg = props.risk_level === '高' ? 'rgba(255,59,48,0.08)' :
                 props.risk_level === '中' ? 'rgba(255,149,0,0.08)' :
                 'rgba(52,199,89,0.08)'
  return `
    <div class="gis-card">
      <div class="gis-card__header">
        <strong>${props.name || props.id}</strong>
        <el-tag size="small" type="${statusType}" effect="light">${props.status}</el-tag>
      </div>
      <div class="gis-card__row"><span class="gis-card__label">管线编号</span><span>${props.id}</span></div>
      <div class="gis-card__row"><span class="gis-card__label">管内压力</span><span>${props.pressure || props.diameter} MPa</span></div>
      <div class="gis-card__row"><span class="gis-card__label">风险等级</span><span style="background:${riskBg};padding:2px 8px;border-radius:980px;font-size:12px;">${props.risk_level || '正常'}</span></div>
      <div class="gis-card__footer">
        <button class="gis-btn gis-btn--primary">燃气风控详情</button>
      </div>
    </div>`
}

function renderWaterCard(props) {
  return `
    <div class="gis-card">
      <div class="gis-card__header">
        <strong>${props.name || props.id}</strong>
        <el-tag size="small" type="success" effect="light">${props.status}</el-tag>
      </div>
      <div class="gis-card__row"><span class="gis-card__label">供水管线编号</span><span>${props.id}</span></div>
      <div class="gis-card__row"><span class="gis-card__label">管径</span><span>${props.diameter} mm</span></div>
      <div class="gis-card__row"><span class="gis-card__label">压力</span><span>${props.pressure} MPa</span></div>
      <div class="gis-card__footer">
        <button class="gis-btn gis-btn--primary">燃气风控详情</button>
      </div>
    </div>`
}

function renderWasteCard(props) {
  return `
    <div class="gis-card">
      <div class="gis-card__header">
        <strong>${props.name || props.id}</strong>
        <el-tag size="small" type="success" effect="light">${props.status}</el-tag>
      </div>
      <div class="gis-card__row"><span class="gis-card__label">废水管线编号</span><span>${props.id}</span></div>
      <div class="gis-card__row"><span class="gis-card__label">流量</span><span>${props.flow_rate} m³/h</span></div>
      <div class="gis-card__footer">
        <button class="gis-btn gis-btn--primary">燃气风控详情</button>
      </div>
    </div>`
}

function renderManholeCard(props) {
  const statusColor = props.status === '正常' ? '#34C759' : '#FF3B30'
  return `
    <div class="gis-card">
      <div class="gis-card__header">
        <strong>${props.name || props.id}</strong>
        <span style="display:flex;align-items:center;gap:4px;font-size:13px;">
          <span style="width:6px;height:6px;border-radius:50%;background:${statusColor};"></span>
          ${props.status}
        </span>
      </div>
      <div class="gis-card__row"><span class="gis-card__label">井盖编号</span><span>${props.id}</span></div>
      <div class="gis-card__row"><span class="gis-card__label">类型</span><span>${props.type}</span></div>
      <div class="gis-card__footer">
        <button class="gis-btn gis-btn--primary">燃气风控详情</button>
      </div>
    </div>`
}

function renderHazardCard(props) {
  const riskColor = (props.risk_level?.includes('极高') || props.risk_level?.includes('高')) ? '#FF3B30' :
                    props.risk_level?.includes('中') ? '#FF9500' : '#34C759'
  return `
    <div class="gis-card">
      <div class="gis-card__header">
        <strong>${props.location || props.id}</strong>
        <span style="color:${riskColor};font-weight:600;font-size:13px;">${props.risk_level}</span>
      </div>
      <div class="gis-card__row"><span class="gis-card__label">风险点编号</span><span>${props.id}</span></div>
      <div class="gis-card__row"><span class="gis-card__label">沉降值</span><span>${props.settlement} mm</span></div>
      <div class="gis-card__row"><span class="gis-card__label">影响半径</span><span>${props.impact_radius} m</span></div>
      <div class="gis-card__footer">
        <button class="gis-btn gis-btn--primary">道路塌陷详情</button>
      </div>
    </div>`
}

function renderAssetCard(props) {
  const statusDot = props.online_status === '在线' ? '#34C759' : props.online_status === '故障' ? '#FF3B30' : '#8E8E93'
  return `
    <div class="gis-card">
      <div class="gis-card__header">
        <strong>${props.device_type} - ${props.id}</strong>
        <span style="display:flex;align-items:center;gap:4px;font-size:13px;">
          <span style="width:6px;height:6px;border-radius:50%;background:${statusDot};"></span>
          ${props.online_status}
        </span>
      </div>
      <div class="gis-card__row"><span class="gis-card__label">设备类型</span><span>${props.device_type}</span></div>
      <div class="gis-card__row"><span class="gis-card__label">资产状态</span><span>${props.asset_status}</span></div>
      <div class="gis-card__footer">
        <button class="gis-btn">资产管理</button>
      </div>
    </div>`
}

function renderAlertCard(props) {
  return `
    <div class="gis-card">
      <div class="gis-card__header">
        <strong>${props.warning_label}</strong>
        <span class="gis-badge" style="background:${props.color};color:#fff;">${props.id}</span>
      </div>
      <div class="gis-card__row"><span class="gis-card__label">预警级别</span><span style="color:${props.color};font-weight:600;">${props.warning_label}</span></div>
      <div class="gis-card__row"><span class="gis-card__label">事件描述</span><span>${props.description}</span></div>
      <div class="gis-card__footer">
        <button class="gis-btn gis-btn--primary">预警中心</button>
      </div>
    </div>`
}

// ---------------------------------------------------------------------------
// 导航按钮绑定
// ---------------------------------------------------------------------------
function bindNavButtons() {
  setTimeout(() => {
    const btns = popupRef.value.querySelectorAll('.gis-btn')
    btns.forEach(btn => {
      btn.addEventListener('click', () => {
        const text = btn.textContent.trim()
        switch (text) {
          case '燃气风控详情': router.push('/gas-risk'); break
          case '道路塌陷详情': router.push('/road-hazard'); break
          case '资产管理':     router.push('/asset'); break
          case '预警中心':     router.push('/alerts'); break
          default: break
        }
        hidePopup()
      })
    })
  }, 50)
}

// ---------------------------------------------------------------------------
// 样式函数
// ---------------------------------------------------------------------------

function gasStyleFn(feature) {
  const risk = feature.get('risk_level') || '低'
  return L.svg({
    color: '#FF3B30',
    weight: risk === '高' ? 4 : risk === '中' ? 3 : 2,
    opacity: risk === '高' ? 1.0 : 0.8
  })
}

function waterStyleFn(feature) {
  return L.svg({ color: '#0071E3', weight: 2, opacity: 0.7 })
}

function wasteStyleFn(feature) {
  return L.svg({ color: '#30C0C0', weight: 2, opacity: 0.7 })
}

function manholeStyleFn(feature) {
  const status = feature.get('status') || '正常'
  const color = status === '正常' ? '#8E8E93' : '#FF3B30'
  return L.circleMarker({
    radius: 6,
    fillColor: color,
    color: '#fff',
    weight: 2,
    opacity: 1,
    fillOpacity: 0.9
  })
}

function hazardStyleFn(feature) {
  const risk = feature.get('risk_level') || '低风险'
  const radius = risk.includes('极高') ? 12 : risk.includes('高') ? 9 : risk.includes('中') ? 7 : 5
  const color = risk.includes('极高') || risk.includes('高') ? '#FF3B30' :
                risk.includes('中') ? '#FF9500' : '#FFCC00'
  return L.circleMarker({
    radius,
    fillColor: color,
    color: '#fff',
    weight: 2,
    opacity: 1,
    fillOpacity: 0.9
  })
}

function assetStyleFn(feature) {
  const status = feature.get('online_status') || '离线'
  const color = status === '在线' ? '#34C759' : status === '故障' ? '#FF3B30' : '#8E8E93'
  return L.circleMarker({
    radius: 6,
    fillColor: color,
    color: '#fff',
    weight: 2,
    opacity: 1,
    fillOpacity: 0.9
  })
}

function alertStyleFn(feature) {
  const lvl = feature.get('warning_level') || 'blue'
  const colorMap = { blue: '#0071E3', yellow: '#FFCC00', orange: '#FF9500', red: '#FF3B30' }
  const radiusMap = { blue: 6, yellow: 8, orange: 10, red: 12 }
  return L.circleMarker({
    radius: radiusMap[lvl] || 8,
    fillColor: colorMap[lvl] || '#0071E3',
    color: '#fff',
    weight: 2,
    opacity: 1,
    fillOpacity: 0.9
  })
}

// ---------------------------------------------------------------------------
// 点击处理
// ---------------------------------------------------------------------------
function handleMapClick(evt) {
  const point = evt.latlng
  const keys = ['gas', 'water', 'waste', 'manhole', 'hazard', 'asset', 'alert']
  let found = false

  for (const key of keys) {
    mapInstance.eachLayer(layer => {
      if (found) return
      if (layer.feature) {
        if (layer.getBounds && layer.getBounds().contains(point)) {
          showPopup(point, getPopupContent(key, layer.feature))
          found = true
        }
      }
    })
  }

  if (!found) hidePopup()
}

function getPopupContent(key, feature) {
  const props = feature.properties || {}
  switch (key) {
    case 'gas':       return renderGasCard(props)
    case 'water':     return renderWaterCard(props)
    case 'waste':     return renderWasteCard(props)
    case 'manhole':   return renderManholeCard(props)
    case 'hazard':    return renderHazardCard(props)
    case 'asset':     return renderAssetCard(props)
    case 'alert':     return renderAlertCard(props)
    default:          return ''
  }
}

// ---------------------------------------------------------------------------
// 初始化地图
// ---------------------------------------------------------------------------
function createMap() {
  mapInstance = L.map(mapContainer.value, {
    center: CENTER,
    zoom: 13,
    zoomControl: false,
    attributionControl: true
  })

  // 添加缩放控件到右上角
  L.control.zoom({ position: 'topright' }).addTo(mapInstance)

  // OSM 底图
  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '&copy; OpenStreetMap contributors',
    maxZoom: 19
  }).addTo(mapInstance)

  // Ansai 边界
  loadBoundary()

  // 创建矢量图层
  vectorLayers.gas = L.layerGroup().addTo(mapInstance)
  vectorLayers.water = L.layerGroup().addTo(mapInstance)
  vectorLayers.waste = L.layerGroup().addTo(mapInstance)
  vectorLayers.manhole = L.layerGroup().addTo(mapInstance)
  vectorLayers.hazard = L.layerGroup().addTo(mapInstance)
  vectorLayers.asset = L.layerGroup().addTo(mapInstance)
  vectorLayers.alert = L.layerGroup().addTo(mapInstance)

  initPopup()

  // 点击事件
  mapInstance.on('click', handleMapClick)
}

async function loadBoundary() {
  try {
    const response = await fetch('/ansai-boundary.geojson')
    const geojson = await response.json()
    boundaryLayer = L.geoJSON(geojson, {
      style: {
        color: '#0071E3',
        weight: 2,
        opacity: 0.6,
        fillColor: '#0071E3',
        fillOpacity: 0.05
      },
      onEachFeature: (feature, layer) => {
        layer.bindPopup(`<div class="gis-card"><div class="gis-card__header"><strong>安塞区</strong></div><div class="gis-card__row"><span class="gis-card__label">区域</span><span>ansai district</span></div></div>`)
      }
    })
    boundaryLayer.addTo(mapInstance)
    mapInstance.fitBounds(boundaryLayer.getBounds(), { padding: [50, 50] })
  } catch (err) {
    console.error('[GIS] 加载 Ansai 边界失败:', err)
  }
}

// ---------------------------------------------------------------------------
// 图层可见性联动
// ---------------------------------------------------------------------------
watch(layerGroups, () => {
  layerGroups.value.forEach(lg => {
    const layer = vectorLayers[lg.key]
    if (layer) {
      if (lg.visible) {
        layer.addTo(mapInstance)
      } else {
        mapInstance.removeLayer(layer)
      }
    }
  })
}, { deep: true })

// ---------------------------------------------------------------------------
// 数据加载 & 渲染
// ---------------------------------------------------------------------------
async function loadAllData() {
  try {
    const data = await fetchAllLayers()

    // 燃气管线
    const gasFeatures = data.gasPipelines.map(p => {
      const coords = p.coordinates.map(c => [c[1], c[0]]) // [lat, lon] for Leaflet
      const feat = L.polyline(coords, { layerKey: 'gas' })
      feat.feature = { properties: p }
      feat.layerKey = 'gas'
      return feat
    })
    vectorLayers.gas.clearLayers()
    gasFeatures.forEach(f => f.addTo(vectorLayers.gas))
    layerGroups.value[0].count = data.gasPipelines.length

    // 供水管线
    const waterFeatures = data.waterPipelines.map(p => {
      const coords = p.coordinates.map(c => [c[1], c[0]])
      const feat = L.polyline(coords, { layerKey: 'water' })
      feat.feature = { properties: p }
      feat.layerKey = 'water'
      return feat
    })
    vectorLayers.water.clearLayers()
    waterFeatures.forEach(f => f.addTo(vectorLayers.water))
    layerGroups.value[1].count = data.waterPipelines.length

    // 废水管线
    const wasteFeatures = data.wastePipelines.map(p => {
      const coords = p.coordinates.map(c => [c[1], c[0]])
      const feat = L.polyline(coords, { layerKey: 'waste' })
      feat.feature = { properties: p }
      feat.layerKey = 'waste'
      return feat
    })
    vectorLayers.waste.clearLayers()
    wasteFeatures.forEach(f => f.addTo(vectorLayers.waste))
    layerGroups.value[2].count = data.wastePipelines.length

    // 智能井盖
    const manholeFeatures = data.manholes.map(m => {
      const latlng = [m.coordinates[1], m.coordinates[0]] // [lat, lon]
      const feat = L.circleMarker(latlng, { layerKey: 'manhole' })
      feat.feature = { properties: m }
      feat.layerKey = 'manhole'
      return feat
    })
    vectorLayers.manhole.clearLayers()
    manholeFeatures.forEach(f => f.addTo(vectorLayers.manhole))
    layerGroups.value[3].count = data.manholes.length

    // 道路塌陷
    const hazardFeatures = data.cavities.map(h => {
      const latlng = [h.coordinates[1], h.coordinates[0]]
      const feat = L.circleMarker(latlng, { layerKey: 'hazard' })
      feat.feature = { properties: h }
      feat.layerKey = 'hazard'
      return feat
    })
    vectorLayers.hazard.clearLayers()
    hazardFeatures.forEach(f => f.addTo(vectorLayers.hazard))
    layerGroups.value[4].count = data.cavities.length

    // 资产设备
    const assetFeatures = data.assets.map(a => {
      const latlng = [a.coordinates[1], a.coordinates[0]]
      const feat = L.circleMarker(latlng, { layerKey: 'asset' })
      feat.feature = { properties: a }
      feat.layerKey = 'asset'
      return feat
    })
    vectorLayers.asset.clearLayers()
    assetFeatures.forEach(f => f.addTo(vectorLayers.asset))
    layerGroups.value[5].count = data.assets.length

    // 预警事件
    const alertFeatures = data.alerts.map(a => {
      const latlng = [a.coordinates[1], a.coordinates[0]]
      const feat = L.circleMarker(latlng, { layerKey: 'alert' })
      feat.feature = { properties: a }
      feat.layerKey = 'alert'
      return feat
    })
    vectorLayers.alert.clearLayers()
    alertFeatures.forEach(f => f.addTo(vectorLayers.alert))
    layerGroups.value[6].count = data.alerts.length

  } catch (err) {
    console.error('[GIS] 加载数据失败:', err)
  }
}

// ---------------------------------------------------------------------------
// 生命周期
// ---------------------------------------------------------------------------
onMounted(async () => {
  createMap()
  bindNavButtons()
  await loadAllData()
})

onBeforeUnmount(() => {
  if (mapInstance) {
    mapInstance.remove()
    mapInstance = null
  }
})
</script>

<style scoped>
.gis-map {
  position: relative;
  width: 100%;
  height: 100%;
  min-height: 600px;
}

.gis-map__viewport {
  width: 100%;
  height: 100%;
  min-height: 600px;
  border-radius: var(--app-radius-card);
  overflow: hidden;
  box-shadow: var(--app-shadow-card);
  border: 1px solid var(--app-border);
  background-color: var(--app-card-solid);
}

/* 图层控制面板 */
.gis-map__layer-panel {
  position: absolute;
  top: 16px;
  left: 16px;
  z-index: 1000;
  background-color: var(--app-card);
  -webkit-backdrop-filter: blur(20px) saturate(1.6);
  backdrop-filter: blur(20px) saturate(1.6);
  border-radius: 16px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.12);
  padding: 16px;
  border: 1px solid rgba(255, 255, 255, 0.6);
  min-width: 200px;
  max-width: 240px;
}

.gis-map__panel-header {
  margin-bottom: 12px;
  padding-bottom: 8px;
  border-bottom: 1px solid var(--app-border);
}

.gis-map__panel-title {
  font-size: 14px;
  font-weight: 600;
  color: var(--app-text-1);
}

.gis-map__layer-list {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.gis-map__layer-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 8px;
  border-radius: 8px;
  cursor: pointer;
  transition: background-color 0.2s ease;
  user-select: none;
}

.gis-map__layer-item:hover {
  background-color: var(--app-hover);
}

.gis-map__layer-item input[type="checkbox"] {
  width: 14px;
  height: 14px;
  accent-color: var(--app-primary);
  cursor: pointer;
}

.gis-map__layer-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  flex-shrink: 0;
}

.gis-map__layer-label {
  flex: 1;
  font-size: 12px;
  color: var(--app-text-1);
}

.gis-map__layer-count {
  font-size: 11px;
  color: var(--app-text-3);
  background-color: var(--app-hover);
  padding: 2px 6px;
  border-radius: 980px;
  min-width: 20px;
  text-align: center;
}

/* Popup 覆盖层 */
.gis-popup {
  position: absolute;
  z-index: 1001;
  pointer-events: none;
  opacity: 0;
  transition: opacity 0.25s ease;
  max-width: 280px;
}

.gis-popup--visible {
  pointer-events: auto;
  opacity: 1;
}

.gis-card {
  background-color: var(--app-card);
  -webkit-backdrop-filter: blur(20px) saturate(1.6);
  backdrop-filter: blur(20px) saturate(1.6);
  border-radius: 16px;
  box-shadow: 0 12px 40px rgba(0, 0, 0, 0.12);
  padding: 14px 16px;
  border: 1px solid rgba(255, 255, 255, 0.6);
  font-family: var(--app-font-family);
  color: var(--app-text-1);
  box-sizing: border-box;
}

.gis-card__header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 8px;
  margin-bottom: 10px;
  font-size: 14px;
  font-weight: 600;
}

.gis-card__row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 4px 0;
  font-size: 12px;
  gap: 12px;
}

.gis-card__label {
  color: var(--app-text-3);
  flex-shrink: 0;
  white-space: nowrap;
}

.gis-card__footer {
  margin-top: 10px;
  display: flex;
  gap: 8px;
}

.gis-badge {
  font-size: 11px;
  padding: 2px 8px;
  border-radius: 980px;
  font-weight: 500;
}

.gis-btn {
  font-family: var(--app-font-family);
  font-size: 12px;
  font-weight: 500;
  padding: 5px 12px;
  border-radius: 8px;
  border: 1px solid var(--app-border-strong);
  background-color: #fff;
  color: var(--app-text-1);
  cursor: pointer;
  transition: all 0.2s ease;
}

.gis-btn:hover {
  background-color: var(--app-hover);
  transform: translateY(-1px);
}

.gis-btn--primary {
  background-color: var(--app-primary);
  color: #fff;
  border-color: var(--app-primary);
}

.gis-btn--primary:hover {
  background-color: var(--app-primary-hover);
  box-shadow: 0 4px 12px rgba(0, 113, 227, 0.3);
}

/* Leaflet 控件样式覆盖 */
.leaflet-control-zoom a {
  background-color: var(--app-card) !important;
  color: var(--app-text-1) !important;
  border: 1px solid var(--app-border) !important;
  border-radius: 8px !important;
  width: 32px !important;
  height: 32px !important;
  line-height: 32px !important;
  font-size: 16px !important;
}

.leaflet-control-zoom a:hover {
  background-color: var(--app-hover) !important;
}

.leaflet-control-attribution {
  background-color: rgba(255, 255, 255, 0.8) !important;
  font-size: 10px !important;
  color: var(--app-text-3) !important;
  border-radius: 4px !important;
  padding: 2px 6px !important;
}
</style>
