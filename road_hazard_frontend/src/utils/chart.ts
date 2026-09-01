import * as echarts from 'echarts'

export const PALETTE = ['#409eff', '#67c23a', '#e6a23c', '#f56c6c', '#909399', '#8e7cc3', '#3aa272']
export const RISK_COLORS: Record<string, string> = {
  '高风险': '#f56c6c',
  '中风险': '#e6a23c',
  '低风险': '#67c23a'
}

export const AXIS_STYLE = {
  axisLine: { lineStyle: { color: '#c0c4cc' } },
  axisLabel: { color: '#606266', fontSize: 11 },
  splitLine: { lineStyle: { color: '#ebeef5' } }
}

export const PIE_LABEL = {
  color: '#606266',
  fontSize: 11
}

export function initChart(el: HTMLElement) {
  return echarts.init(el)
}

export function riskPieOption(data: { name: string; value: number }[], title?: string) {
  const ordered = ['高风险', '中风险', '低风险']
    .map(n => data.find(d => d.name === n))
    .filter(Boolean) as { name: string; value: number }[]
  data.forEach(d => { if (!ordered.includes(d)) ordered.push(d) })
  return {
    title: title ? { text: title, left: 'center', textStyle: { fontSize: 13, color: '#303133' } } : undefined,
    tooltip: { trigger: 'item', formatter: '{b}: {c} ({d}%)' },
    legend: { bottom: 0, textStyle: { fontSize: 11 } },
    color: ordered.map(d => RISK_COLORS[d.name] || '#909399'),
    series: [{
      type: 'pie', radius: ['38%', '62%'], center: ['50%', '48%'],
      label: PIE_LABEL, data: ordered
    }]
  }
}

export function barOption(data: { name: string; value: number }[], color = '#409eff', horizontal = false) {
  const names = data.map(d => d.name)
  const values = data.map(d => d.value)
  return {
    tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
    grid: { left: 8, right: 16, top: 20, bottom: 8, containLabel: true },
    xAxis: horizontal
      ? { type: 'value', ...AXIS_STYLE }
      : { type: 'category', data: names, ...AXIS_STYLE },
    yAxis: horizontal
      ? { type: 'category', data: names, ...AXIS_STYLE }
      : { type: 'value', ...AXIS_STYLE },
    series: [{
      type: 'bar', data: values, barMaxWidth: 26,
      itemStyle: { color, borderRadius: horizontal ? [0, 4, 4, 0] : [4, 4, 0, 0] },
      label: { show: true, position: horizontal ? 'right' : 'top', color: '#909399', fontSize: 10 }
    }]
  }
}
