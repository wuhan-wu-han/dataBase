/**
 * 坐标系纯数学转换（WGS84 / GCJ02 / BD09）。
 *
 * 后端 /api/platform/baidu/convert 才是主通道，本模块只作为它不可用时的降级：
 * 算法是公开的偏移公式，不需要百度 AK，因此可以在前端离线完成，
 * 保证演示模式下即使网关不通，地图业务点位仍能落在正确位置。
 */

const PI = Math.PI
const X_PI = (PI * 3000.0) / 180.0
/** 克拉索夫斯基椭球长半轴与偏心率平方，国测局偏移公式使用的常量。 */
const A = 6378245.0
const EE = 0.00669342162296594323

/** 国测局偏移只在中国境内有效，境外坐标原样返回。 */
function outOfChina(lng, lat) {
  return lng < 72.004 || lng > 137.8347 || lat < 0.8293 || lat > 55.8271
}

function transformLat(x, y) {
  let ret = -100.0 + 2.0 * x + 3.0 * y + 0.2 * y * y + 0.1 * x * y + 0.2 * Math.sqrt(Math.abs(x))
  ret += ((20.0 * Math.sin(6.0 * x * PI) + 20.0 * Math.sin(2.0 * x * PI)) * 2.0) / 3.0
  ret += ((20.0 * Math.sin(y * PI) + 40.0 * Math.sin((y / 3.0) * PI)) * 2.0) / 3.0
  ret += ((160.0 * Math.sin((y / 12.0) * PI) + 320 * Math.sin((y * PI) / 30.0)) * 2.0) / 3.0
  return ret
}

function transformLng(x, y) {
  let ret = 300.0 + x + 2.0 * y + 0.1 * x * x + 0.1 * x * y + 0.1 * Math.sqrt(Math.abs(x))
  ret += ((20.0 * Math.sin(6.0 * x * PI) + 20.0 * Math.sin(2.0 * x * PI)) * 2.0) / 3.0
  ret += ((20.0 * Math.sin(x * PI) + 40.0 * Math.sin((x / 3.0) * PI)) * 2.0) / 3.0
  ret += ((150.0 * Math.sin((x / 12.0) * PI) + 300.0 * Math.sin((x / 30.0) * PI)) * 2.0) / 3.0
  return ret
}

/** WGS84（GPS 原始）→ GCJ02（国测局火星坐标） */
export function wgs84ToGcj02(lng, lat) {
  if (outOfChina(lng, lat)) return [lng, lat]
  const radLat = (lat / 180.0) * PI
  let magic = Math.sin(radLat)
  magic = 1 - EE * magic * magic
  const sqrtMagic = Math.sqrt(magic)
  let dLat = transformLat(lng - 105.0, lat - 35.0)
  let dLng = transformLng(lng - 105.0, lat - 35.0)
  dLat = (dLat * 180.0) / (((A * (1 - EE)) / (magic * sqrtMagic)) * PI)
  dLng = (dLng * 180.0) / ((A / sqrtMagic) * Math.cos(radLat) * PI)
  return [lng + dLng, lat + dLat]
}

/** GCJ02 → BD09（百度坐标系） */
export function gcj02ToBd09(lng, lat) {
  const z = Math.sqrt(lng * lng + lat * lat) + 0.00002 * Math.sin(lat * X_PI)
  const theta = Math.atan2(lat, lng) + 0.000003 * Math.cos(lng * X_PI)
  return [z * Math.cos(theta) + 0.0065, z * Math.sin(theta) + 0.006]
}

/** WGS84 → BD09 */
export function wgs84ToBd09(lng, lat) {
  const [gcjLng, gcjLat] = wgs84ToGcj02(lng, lat)
  return gcj02ToBd09(gcjLng, gcjLat)
}

/** 与百度 Convertor API 一致的坐标系编码。 */
const COORD_CODE = { WGS84: 1, GCJ02: 3, BD09: 5 }

/**
 * 本地降级转换：只支持转成 BD09，其他组合返回原坐标。
 * @param {Array<[number, number]>} coords - [lng, lat] 列表
 * @param {number} fromCoord - 1=WGS84, 3=GCJ02
 * @param {number} toCoord - 5=BD09
 * @returns {Array<[number, number]>}
 */
export function convertCoordsLocal(coords, fromCoord = COORD_CODE.WGS84, toCoord = COORD_CODE.BD09) {
  if (toCoord !== COORD_CODE.BD09) return coords
  const convert = fromCoord === COORD_CODE.GCJ02 ? gcj02ToBd09 : fromCoord === COORD_CODE.WGS84 ? wgs84ToBd09 : null
  if (!convert) return coords
  return coords.map(([lng, lat]) => {
    const [outLng, outLat] = convert(Number(lng), Number(lat))
    return [outLng, outLat]
  })
}
