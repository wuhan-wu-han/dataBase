import * as echarts from 'echarts'

export const PALETTE = ['#409eff', '#67c23a', '#e6a23c', '#f56c6c', '#909399', '#8e7cc3', '#3aa272']

// 告警等级配色
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
  const chart = echarts.init(el)
  // 未激活页签 / 未展开弹窗中的容器宽度为 0，可见后需重算尺寸才能正常绘制
  const ro = new ResizeObserver(() => {
    if (!chart.isDisposed() && el.offsetWidth > 0) chart.resize()
  })
  ro.observe(el)
  return chart
}

/** 告警等级环形图（固定 高 → 中 → 低 顺序） */
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

/** 通用环形图（状态 / 区域 / 类型等） */
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

/** 多指标历史曲线（沉降式时序监测） */
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

/** 被盗轨迹回放：经纬度折线 + 序号标记，highlight 为当前播放点 */
export function trackOption(points: { lng: number; lat: number; label: string }[], highlight = -1) {
  return {
    tooltip: { trigger: 'item', formatter: (p: any) => `${p.data[2] ?? p.name}<br/>经度 ${p.data[0]}　纬度 ${p.data[1]}` },
    grid: { left: 12, right: 24, top: 24, bottom: 20, containLabel: true },
    xAxis: { type: 'value', scale: true, name: '经度', nameTextStyle: { fontSize: 11, color: '#909399' }, ...AXIS_STYLE },
    yAxis: { type: 'value', scale: true, name: '纬度', nameTextStyle: { fontSize: 11, color: '#909399' }, ...AXIS_STYLE },
    series: [
      {
        type: 'line', showSymbol: true, symbolSize: 9, smooth: false,
        lineStyle: { color: '#f56c6c', width: 2, type: 'dashed' },
        itemStyle: { color: '#f56c6c' },
        label: { show: true, position: 'top', fontSize: 10, color: '#909399', formatter: (p: any) => p.dataIndex + 1 },
        data: points.map(p => [p.lng, p.lat, p.label])
      },
      ...(highlight >= 0 && points[highlight]
        ? [{
            type: 'scatter', symbolSize: 18, z: 10,
            itemStyle: { color: '#409eff', borderColor: '#fff', borderWidth: 2 },
            label: { show: true, position: 'top', fontSize: 11, color: '#409eff', formatter: '当前' },
            data: [[points[highlight].lng, points[highlight].lat]]
          }]
        : [])
    ]
  }
}
