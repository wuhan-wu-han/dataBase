/**
 * 百度地图代理接口（前端 → Python 后端 → 百度 Web API）
 *
 * 职责：
 * 1. 调用后端 /api/platform/baidu/** 系列接口
 * 2. 所有百度 AK 只存在后端，前端完全不接触
 * 3. 坐标转换、POI 搜索、路线规划都走后端代理
 *
 * 后端路由前缀：/api/platform/baidu（Python FastAPI，端口 8000）
 * Vite 代理已将 /api/platform/** 转发到 8000 端口
 */
import { createModuleHttp, MODULE_PREFIX } from './gateway'

const http = createModuleHttp(MODULE_PREFIX.platform, { silentErrors: true })

/**
 * POI 地点搜索
 * @param {string} keyword - 搜索关键词
 * @param {string} city - 限定城市
 * @param {number} pageSize - 每页数量（1-50）
 * @param {number} pageNum - 页码
 * @returns {Promise<{pois: Array<{name,address,lng,lat,district,province}>, total: number}>}
 */
export async function searchPlace(keyword, city = '延安市安塞区', pageSize = 10, pageNum = 0) {
  if (!keyword || !keyword.trim()) return { pois: [], total: 0 }
  try {
    const data = await http.get('/baidu/search', {
      params: { keyword, city, page_size: pageSize, page_num: pageNum }
    })
    return data || { pois: [], total: 0 }
  } catch (err) {
    console.warn('[Baidu] POI 搜索失败:', err?.response?.data?.detail || err.message)
    return { pois: [], total: 0 }
  }
}

/**
 * 批量坐标转换：WGS84 → BD09（百度地图展示坐标系）
 * 后端调用百度 Convertor API。
 *
 * @param {Array<[number, number]>} coords - 坐标列表，每项 [lon, lat]
 * @param {number} fromCoord - 原始坐标系: 1=WGS84(默认), 3=GCJ02
 * @param {number} toCoord - 目标坐标系: 5=BD09(默认)
 * @returns {Promise<Array<[number, number]>>} - 转换后坐标数组
 */
export async function convertCoords(coords, fromCoord = 1, toCoord = 5) {
  if (!Array.isArray(coords) || coords.length === 0) return []
  if (coords.length > 50) {
    // 分批转换（后端单次最多 50 个）
    const batches = []
    for (let i = 0; i < coords.length; i += 50) {
      batches.push(convertCoords(coords.slice(i, i + 50), fromCoord, toCoord))
    }
    const results = await Promise.all(batches)
    return results.flat()
  }
  try {
    const data = await http.post('/baidu/convert', {
      coords: coords.map(([lon, lat]) => [Number(lon), Number(lat)]),
      from_coord: fromCoord,
      to_coord: toCoord
    })
    return data.converted || coords
  } catch (err) {
    console.warn('[Baidu] 坐标转换失败，降级返回原坐标:', err?.response?.data?.detail || err.message)
    return coords
  }
}

/**
 * 单点坐标转换（便捷封装）
 * @returns {Promise<[number, number]>} [lng, lat]
 */
export async function convertPoint(lon, lat, fromCoord = 1, toCoord = 5) {
  const result = await convertCoords([[lon, lat]], fromCoord, toCoord)
  return result[0] || [lon, lat]
}

/**
 * 驾车路线规划
 * 后端调用百度 Directionlite v1/driving 接口
 *
 * @param {number} originLng - 起点经度（BD09）
 * @param {number} originLat - 起点纬度（BD09）
 * @param {number} destLng - 终点经度（BD09）
 * @param {number} destLat - 终点纬度（BD09）
 * @returns {Promise<{distance:string, duration:string, polyline:string, steps:Array}>}
 */
export async function planDriving(originLng, originLat, destLng, destLat) {
  try {
    const data = await http.post('/baidu/direction/driving', {
      origin_lng: originLng,
      origin_lat: originLat,
      dest_lng: destLng,
      dest_lat: destLat
    })
    if (data.ok && data.route) return data.route
    throw new Error(data.detail || '路线规划返回异常')
  } catch (err) {
    console.warn('[Baidu] 路线规划失败:', err?.response?.data?.detail || err.message)
    throw err
  }
}

/**
 * 地理编码（地址 → 坐标）
 */
export async function geocode(address, city = '延安市安塞区') {
  if (!address) return null
  try {
    const data = await http.get('/baidu/geocode', { params: { address, city } })
    return data.ok ? data.result : null
  } catch (err) {
    console.warn('[Baidu] 地理编码失败:', err?.response?.data?.detail || err.message)
    return null
  }
}

/**
 * 逆地理编码（坐标 → 地址）
 */
export async function reverseGeocode(lng, lat) {
  try {
    const data = await http.get('/baidu/reverse', { params: { lng, lat } })
    return data.ok ? data.result : null
  } catch (err) {
    console.warn('[Baidu] 逆地理编码失败:', err?.response?.data?.detail || err.message)
    return null
  }
}
