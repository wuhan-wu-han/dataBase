import * as echarts from 'echarts'

export const PALETTE = ['#409eff', '#67c23a', '#e6a23c', '#f56c6c', '#909399', '#8e7cc3', '#3aa272']

export const LEVEL_COLORS: Record<string, string> = {
  '高': '#f56c6c',
  '中': '#e6a23c',
  '低': '#67c23a'
}

export const AXIS_STYLE = {
  axisLine: { lineStyle: { color: '#c0c4cc' } },
  axisLabel: { color: '#606266', fontSize: 11 },
  splitLine: { lineStyle: { color: '#ebeef5' } }
}

export const PIE_LABEL = { color: '#606266', fontSize: 11 }

export function initChart(el: HTMLElement) {
  return echarts.init(el)
}

/** 告警等级环形图 */
export function levelPieOption(data: { name: string; value: number }[], title?: string) {
  const ordered = ['高', '中', '低']
    .map(n => data.find(d => d.name === n))
    .filter(Boolean) as { name: string; value: number }[]
  data.forEach(d => { if (!ordered.includes(d)) ordered.push(d) })
  return {
    title: title ? { text: title, left: 'center', textStyle: { fontSize: 13, color: '#303133' } } : undefined,
    tooltip: { trigger: 'item', formatter: '{b}: {c} ({d}%)' },
    legend: { bottom: 0, textStyle: { fontSize: 11 } },
    color: ordered.map(d => LEVEL_COLORS[d.name] || '#909399'),
    series: [{ type: 'pie', radius: ['38%', '62%'], center: ['50%', '48%'], label: PIE_LABEL, data: ordered }]
  }
}

/** 通用环形图 */
export function pieOption(data: { name: string; value: number }[], title?: string) {
  return {
    title: title ? { text: title, left: 'center', textStyle: { fontSize: 13, color: '#303133' } } : undefined,
    tooltip: { trigger: 'item', formatter: '{b}: {c} ({d}%)' },
    legend: { bottom: 0, textStyle: { fontSize: 11 } },
    color: PALETTE,
    series: [{ type: 'pie', radius: ['38%', '62%'], center: ['50%', '48%'], label: PIE_LABEL, data }]
  }
}

export function barOption(data: { name: string; value: number }[], color = '#409eff', horizontal = false) {
  const names = data.map(d => d.name)
  const values = data.map(d => d.value)
  return {
    tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
    grid: { left: 8, right: 16, top: 20, bottom: 8, containLabel: true },
    xAxis: horizontal ? { type: 'value', ...AXIS_STYLE } : { type: 'category', data: names, ...AXIS_STYLE },
    yAxis: horizontal ? { type: 'category', data: names, ...AXIS_STYLE } : { type: 'value', ...AXIS_STYLE },
    series: [{
      type: 'bar', data: values, barMaxWidth: 26,
      itemStyle: { color, borderRadius: horizontal ? [0, 4, 4, 0] : [4, 4, 0, 0] },
      label: { show: true, position: horizontal ? 'right' : 'top', color: '#909399', fontSize: 10 }
    }]
  }
}

/** 近 7 日告警趋势（按等级堆叠） */
export function trendStackOption(days: string[], series: { name: string; data: number[] }[]) {
  return {
    tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
    legend: { bottom: 0, textStyle: { fontSize: 11 } },
    grid: { left: 8, right: 16, top: 20, bottom: 30, containLabel: true },
    xAxis: { type: 'category', data: days, ...AXIS_STYLE },
    yAxis: { type: 'value', minInterval: 1, ...AXIS_STYLE },
    color: series.map(s => LEVEL_COLORS[s.name] || '#409eff'),
    series: series.map(s => ({
      name: s.name, type: 'bar', stack: 'alarm', data: s.data, barMaxWidth: 26,
      emphasis: { focus: 'series' }
    }))
  }
}

/** 多指标历史曲线 */
export function historyLineOption(times: string[], series: { name: string; data: (number | null)[] }[]) {
  return {
    tooltip: { trigger: 'axis' },
    legend: { bottom: 0, textStyle: { fontSize: 11 } },
    grid: { left: 8, right: 18, top: 20, bottom: 30, containLabel: true },
    xAxis: { type: 'category', data: times, ...AXIS_STYLE },
    yAxis: { type: 'value', ...AXIS_STYLE },
    color: PALETTE,
    series: series.map(s => ({
      name: s.name, type: 'line', data: s.data, smooth: true,
      symbolSize: 5, connectNulls: true
    }))
  }
}

/** 水质链路流向图（横向节点） */
export function chainOption(nodes: { name: string; kind: string; status: string; value: string }[]) {
  return {
    tooltip: { trigger: 'item', formatter: (p: any) => `${p.name}<br/>${p.data.tip}` },
    grid: { left: 30, right: 30, top: 30, bottom: 30 },
    xAxis: { type: 'value', show: false, max: Math.max(nodes.length, 1) },
    yAxis: { type: 'category', show: false, data: nodes.map(n => n.name) },
    series: [{
      type: 'graph', layout: 'none', symbolSize: 46,
      label: { show: true, fontSize: 10, color: '#fff' },
      edgeSymbol: ['none', 'arrow'], edgeSymbolSize: 8,
      lineStyle: { color: '#409eff', width: 2, curveness: 0 },
      data: nodes.map((n, i) => ({
        name: n.name, x: i, y: 0, tip: `${n.kind} · ${n.value}`,
        itemStyle: { color: n.status === '异常' ? '#f56c6c' : '#409eff' }
      })),
      links: nodes.slice(1).map((n, i) => ({ source: nodes[i].name, target: n.name }))
    }]
  }
}
