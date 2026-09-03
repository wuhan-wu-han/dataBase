import { computed, reactive } from 'vue'

/**
 * 联调阶段的 Mock 回退登记器
 *
 * 背景：部分子模块后端接口仍在联调，接口异常时页面回退到 Mock 数据以保证可展示。
 * 这里集中记录「哪个模块正在使用演示数据」，供顶栏提示条展示，并在控制台打印醒目警告，
 * 避免演示数据被误当成真实数据。
 *
 * TODO(第二阶段): 后端逐个接入真实数据库后，删除对应 api 模块中的 fallback 调用与 Mock 数据源。
 */

const registry = reactive({})

const STYLE_TAG = 'color:#fff;background:#E6A23C;padding:2px 6px;border-radius:3px;font-weight:600'
const STYLE_TEXT = 'color:#E6A23C'

function describeError(err) {
  const status = err?.status || err?.response?.status
  const url = err?.config?.url || err?.response?.config?.url
  const parts = []
  if (status) parts.push(`HTTP ${status}`)
  if (url) parts.push(url)
  if (!status && !url) parts.push(err?.message || '网络异常')
  return parts.join(' · ')
}

/** 接口连通：清除该模块的 Mock 标记 */
export function markLive(key) {
  if (registry[key]?.mock) registry[key] = { mock: false }
}

/** 接口异常并回退到演示数据 */
export function markMock(key, label, err) {
  const entry = { mock: true, label, at: new Date().toLocaleTimeString() }
  if (registry[key]?.label !== label || !registry[key]?.mock) {
    console.warn(`%c[MOCK MODE]%c ${label} 接口未连通（${describeError(err)}），已回退演示数据。`
      + '该模块数据非真实后端数据。', STYLE_TAG, STYLE_TEXT)
  }
  registry[key] = entry
}

/**
 * 生成带登记能力的 fallback 包装器，签名与原 fallback 一致，
 * 因此各 api 模块的调用点无需改动。
 */
export function createMockFallback(key, label) {
  return (promise, mockValue) =>
    Promise.resolve(promise)
      .then((data) => {
        markLive(key)
        return data
      })
      .catch((err) => {
        markMock(key, label, err)
        return typeof mockValue === 'function' ? mockValue() : mockValue
      })
}

/** 当前处于演示数据模式的模块列表（供提示条渲染） */
export const mockModules = computed(() =>
  Object.values(registry).filter((item) => item?.mock))

export const hasMockData = computed(() => mockModules.value.length > 0)
