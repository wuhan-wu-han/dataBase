/**
 * ECharts 通用 composable
 * 用途：自动绑定 DOM ref、ResizeObserver 自适应（侧边栏折叠时图表会自动 resize）、组件卸载时 dispose
 * 使用：
 *   const chartRef = ref(null)
 *   const { setOption, resize } = useEChart(chartRef)
 *   onMounted(() => setOption({...}))
 */
import { onBeforeUnmount, onMounted, shallowRef } from 'vue'
import * as echarts from 'echarts/core'
import { LineChart, PieChart, BarChart, GaugeChart } from 'echarts/charts'
import {
  TooltipComponent, GridComponent, LegendComponent, TitleComponent
} from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'

// 按需注册：Dashboard 折线图 / FailurePrediction 环形图 / 燃气风控仪表盘
echarts.use([
  LineChart, PieChart, BarChart, GaugeChart,
  TooltipComponent, GridComponent, LegendComponent, TitleComponent,
  CanvasRenderer
])

/**
 * 创建并管理一个 ECharts 实例
 * @param {import('vue').Ref<HTMLElement|null>} elRef 模板 ref
 * @returns {{ setOption, resize, getInstance, dispose }}
 */
export function useEChart(elRef) {
  // shallowRef 避免 echarts 实例被深度响应化
  const chart = shallowRef(null)
  let ro = null

  // 懒初始化：确保 chart 实例存在（onMounted 可能因 DOM 时序错过）
  function ensureInit() {
    if (chart.value) return true
    const el = elRef.value
    if (!el) return false
    chart.value = echarts.init(el, null, { renderer: 'canvas' })
    if (typeof ResizeObserver !== 'undefined') {
      ro = new ResizeObserver(() => chart.value && chart.value.resize())
      ro.observe(el)
    }
    return true
  }

  onMounted(() => {
    ensureInit()
  })

  onBeforeUnmount(() => {
    if (ro) {
      ro.disconnect()
      ro = null
    }
    if (chart.value) {
      chart.value.dispose()
      chart.value = null
    }
  })

  // 设置/合并配置项（首次调用时自动初始化）
  function setOption(option, opts) {
    if (!ensureInit()) return
    chart.value.setOption(option, opts)
  }

  // 手动触发 resize
  function resize() {
    if (!ensureInit()) return
    chart.value.resize()
  }

  // 获取底层实例（用于高级操作）
  function getInstance() {
    ensureInit()
    return chart.value
  }

  // 主动销毁（一般无需手动调用，onBeforeUnmount 会处理）
  function dispose() {
    if (chart.value) {
      chart.value.dispose()
      chart.value = null
    }
  }

  return { setOption, resize, getInstance, dispose }
}

export default { useEChart }
