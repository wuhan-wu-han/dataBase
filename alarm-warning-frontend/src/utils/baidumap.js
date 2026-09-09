/**
 * 百度地图前端工具集（仅负责渲染层）
 *
 * 本模块只处理浏览器端的地图渲染相关：
 * - waitBMap: 等待 BMap SDK 加载完成
 * - buildMarkerIcon / buildClusterIcon: 生成 Marker 的 SVG data URI 图标
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
// Marker 图标：SVG data URI
//
// BMap v3.0 的 BMap.Icon 只认图片地址，不支持 _html 注入 DOM，
// 因此点位与聚合气泡都画成 SVG 再转成 data URI 交给 Icon。
// ---------------------------------------------------------------------------

/** 点位统一画布边长，锚点居中，保证各等级点击热区一致。 */
const PIN_CANVAS = 30

/** 与 config/gisLayers.js 的 RISK_LEVELS 保持一致。 */
const RISK_COLOR = {
  high: '#C9433B',
  elevated: '#D97732',
  medium: '#D5A126',
  low: '#397EBE',
  normal: '#668477'
}

const RISK_RADIUS = { high: 7, elevated: 6, medium: 5, low: 4.5, normal: 3.5 }

function svgIconUrl(body, size) {
  const svg = `<svg xmlns="http://www.w3.org/2000/svg" width="${size}" height="${size}" viewBox="0 0 ${size} ${size}">${body}</svg>`
  return `data:image/svg+xml;charset=utf-8,${encodeURIComponent(svg)}`
}

/**
 * 构建点位 Marker 图标：颜色与半径由归一化后的四级风险决定，
 * 只有声明了 pulse 的图层在高风险时叠加一圈扩散动画，其余等级保持静止。
 */
export function buildMarkerIcon(cfg, props) {
  const risk = props._risk || 'normal'
  const color = RISK_COLOR[risk] || RISK_COLOR.normal
  const radius = RISK_RADIUS[risk] || RISK_RADIUS.normal
  const center = PIN_CANVAS / 2
  const parts = []

  if (cfg.pulse === true && risk === 'high') {
    parts.push(
      `<circle cx="${center}" cy="${center}" r="${radius}" fill="none" stroke="${color}" stroke-width="1.5">`
      + `<animate attributeName="r" values="${radius};${center - 1}" dur="2.1s" repeatCount="indefinite"/>`
      + `<animate attributeName="opacity" values="0.55;0" dur="2.1s" repeatCount="indefinite"/>`
      + `</circle>`
    )
  }

  parts.push(
    `<circle cx="${center}" cy="${center}" r="${radius}" fill="${color}" stroke="#ffffff" stroke-opacity="0.92" stroke-width="1.4"/>`
  )

  return {
    width: PIN_CANVAS,
    height: PIN_CANVAS,
    anchor: { x: center, y: center },
    url: svgIconUrl(parts.join(''), PIN_CANVAS)
  }
}

/** 构建低缩放级别的聚合气泡图标。 */
export function buildClusterIcon(count, isDanger = false) {
  const size = Math.round(28 + Math.min(8, count * 1.5))
  const center = size / 2
  const fill = isDanger ? 'rgba(190,69,62,0.86)' : 'rgba(229,182,94,0.84)'
  const textColor = isDanger ? '#ffffff' : '#6B4B1D'
  const body = `<circle cx="${center}" cy="${center}" r="${center - 2}" fill="${fill}" stroke="#ffffff" stroke-opacity="0.92" stroke-width="2"/>`
    + `<text x="${center}" y="${center}" dy="4" text-anchor="middle" font-family="Arial,Helvetica,sans-serif" font-size="11" font-weight="700" fill="${textColor}">${count}</text>`
  return { width: size, height: size, anchor: { x: center, y: center }, url: svgIconUrl(body, size) }
}

/** 单色圆点图标，用于搜索结果等临时标记。 */
export function buildDotIcon(color = '#1A73E8', size = 24) {
  const center = size / 2
  const body = `<circle cx="${center}" cy="${center}" r="${center - 3}" fill="${color}" stroke="#ffffff" stroke-width="2.5"/>`
  return { width: size, height: size, anchor: { x: center, y: center }, url: svgIconUrl(body, size) }
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
