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
import { LineChart, PieChart, BarChart } from 'echarts/charts'
import {
  TooltipComponent, GridComponent, LegendComponent
} from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'

// 按需注册：仅 Dashboard 折线图与 FailurePrediction 环形图所需组件
// 未引入 TitleComponent/DatasetComponent 等未使用模块以减小打包体积
echarts.use([
  LineChart, PieChart, BarChart,
  TooltipComponent, GridComponent, LegendComponent,
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

  onMounted(() => {
    const el = elRef.value
    if (!el) return
    chart.value = echarts.init(el, null, { renderer: 'canvas' })

    // ResizeObserver 监听容器尺寸变化（侧边栏折叠/窗口 resize 均触发）
    if (typeof ResizeObserver !== 'undefined') {
      ro = new ResizeObserver(() => {
        chart.value && chart.value.resize()
      })
      ro.observe(el)
    }
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

  // 设置/合并配置项
  function setOption(option, opts) {
    if (chart.value) chart.value.setOption(option, opts)
  }

  // 手动触发 resize
  function resize() {
    chart.value && chart.value.resize()
  }

  // 获取底层实例（用于高级操作）
  function getInstance() {
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
