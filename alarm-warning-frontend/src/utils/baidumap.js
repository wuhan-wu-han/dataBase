/**
 * 百度地图前端工具集（仅负责渲染层）
 *
 * 本模块只处理浏览器端的地图渲染相关：
 * - waitBMap: 等待 BMap SDK 加载完成
 * - buildMarkerIcon / ensureMarkerStyles: 动态构造 Marker 的 DOM icon
 * - OverlayGroup: 覆盖物分组容器
 *
 * 坐标转换、POI 搜索、路线规划等**数据获取类**功能已全部移到后端：
 * 调用 src/api/baiduMap.js → /api/platform/baidu/** → 百度 Web API
 * 这样百度 AK 只在后端存在，前端完全不接触。
 */

const BMAP_LOAD_TIMEOUT = 10000

/**
 * 等待 window.BMap 就绪。通过 index.html 的 script 标签同步加载。
 */
export function waitBMap(timeout = BMAP_LOAD_TIMEOUT) {
  return new Promise((resolve, reject) => {
    if (window.BMap) {
      resolve(window.BMap)
      return
    }
    const start = Date.now()
    const check = () => {
      if (window.BMap) {
        resolve(window.BMap)
        return
      }
      if (Date.now() - start > timeout) {
        reject(new Error('百度地图 SDK 加载超时，请检查 index.html 中的 AK 配置'))
        return
      }
      setTimeout(check, 100)
    }
    check()
  })
}

// ---------------------------------------------------------------------------
// 自定义覆盖物：点位 Marker（divIcon 风格，带动态样式注入）
// ---------------------------------------------------------------------------

/** 判断高风险脉冲动画 */
function shouldPulse(cfg, props) {
  if (props._status !== 'danger') return false
  const level = String(props.warning_level ?? props.warningLevel ?? props.alertLevel ?? props.risk_level ?? props.riskLevel ?? '').toLowerCase()
  return (cfg.key === 'alert' && (level.includes('red') || level.includes('红')))
    || (cfg.key === 'hazard' && level.includes('极高'))
}

/**
 * 构建百度地图 Marker 的 DOM 样式配置。
 * 返回对象中的 innerHTML 会被赋给 BMap.Icon._html。
 */
export function buildMarkerIcon(cfg, props, isSelected = false) {
  const status = props._status || 'normal'
  const risk = props._risk || 'normal'
  const size = { high: 14, elevated: 12, medium: 10, low: 9, normal: 7 }[risk] || 7
  const hostSize = Math.max(24, size + 12)

  const classes = [
    'gis-pin',
    `gis-pin--${cfg.key}`,
    `gis-pin--s-${status}`,
    `gis-pin--r-${risk}`,
    `gis-pin--k-${props._iconKind || 'default'}`
  ]
  if (shouldPulse(cfg, props)) classes.push('is-pulse')
  if (isSelected) classes.push('is-selected')

  ensureMarkerStyles()

  return {
    width: hostSize,
    height: hostSize,
    anchor: { x: hostSize / 2, y: hostSize / 2 },
    innerHTML: `<span class="${classes.join(' ')}"></span>`
  }
}

/** 首次调用时注入 Marker CSS 到文档头 */
let markerStylesInjected = false
function ensureMarkerStyles() {
  if (markerStylesInjected) return
  markerStylesInjected = true
  const style = document.createElement('style')
  style.setAttribute('data-bmap-gis', 'marker-styles')
  style.textContent = `
    .gis-pin {
      position: relative; display: flex; align-items: center; justify-content: center;
      box-sizing: border-box; width: 7px; height: 7px;
      font-family: inherit; font-size: 0; font-weight: 600; line-height: 1; color: transparent;
      background-color: #71847A; border: 1px solid rgba(255,255,255,0.92); border-radius: 50%;
      box-shadow: 0 1px 3px rgba(37,49,43,0.26);
      transition: transform 0.16s ease, box-shadow 0.16s ease;
    }
    .gis-pin:hover { transform: scale(1.18); }
    .gis-pin.is-selected { transform: scale(1.3); box-shadow: 0 0 0 3px rgba(52,82,105,0.22), 0 2px 7px rgba(37,49,43,0.3); }
    .gis-pin--r-normal { width: 7px; height: 7px; background-color: #668477; box-shadow: 0 1px 2px rgba(37,49,43,0.22); }
    .gis-pin--r-low { width: 9px; height: 9px; background-color: #397EBE; }
    .gis-pin--r-medium { width: 10px; height: 10px; background-color: #D5A126; }
    .gis-pin--r-elevated { width: 12px; height: 12px; background-color: #D97732; border-width: 1.5px; }
    .gis-pin--r-high { width: 14px; height: 14px; background-color: #C9433B; border-width: 1.5px; box-shadow: 0 2px 5px rgba(130,48,43,0.28); }
    .gis-pin--alert { font-size: 8px; color: #fff; }
    .gis-pin--k-gas::before { content: '燃'; }
    .gis-pin--k-water::before { content: '水'; }
    .gis-pin--k-drain::before { content: '排'; }
    .gis-pin--k-sensor::before { content: '感'; }
    .gis-pin--k-camera::before { content: '摄'; }
    .gis-pin--k-detector::before { content: '探'; }
    .gis-pin--k-fan::before { content: '风'; }
    .gis-pin--alert::before { content: '!'; font-size: inherit; }
    .gis-pin.is-pulse::after {
      content: ''; position: absolute; inset: -5px; border-radius: 50%;
      border: 1.5px solid currentColor; color: #C84740; opacity: 0;
      animation: gis-pulse 2.1s ease-out infinite; pointer-events: none;
    }
    @keyframes gis-pulse { 0%{transform:scale(0.8);opacity:0.38} 72%{transform:scale(1.55);opacity:0} 100%{transform:scale(1.55);opacity:0} }
  `
  document.head.appendChild(style)
}

// ---------------------------------------------------------------------------
// 覆盖物分组容器
// ---------------------------------------------------------------------------

export class OverlayGroup {
  constructor() {
    this.items = []
    this.map = null
  }
  setMap(map) { this.map = map }
  clear() {
    if (this.map) this.items.forEach(({ overlay }) => this.map.removeOverlay(overlay))
    this.items = []
  }
  add(overlay, feature, cfg, props) {
    if (this.map) this.map.addOverlay(overlay)
    this.items.push({ overlay, feature, cfg, props })
  }
  has(overlay) { return this.items.some((x) => x.overlay === overlay) }
}
