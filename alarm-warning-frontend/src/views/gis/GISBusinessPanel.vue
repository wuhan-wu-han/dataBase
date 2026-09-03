<template>
  <aside class="gis-business" aria-label="GIS 实时业务态势">
    <section class="gis-business__card gis-business__card--alerts">
      <header class="gis-business__head">
        <div>
          <h3>实时预警</h3>
          <p>按事件时间倒序</p>
        </div>
        <span class="gis-business__summary">今日 {{ todayCount }} 起</span>
      </header>

      <div v-if="alarms.length" class="gis-alarm-list">
        <button
          v-for="alarm in alarms"
          :key="alarm.id"
          type="button"
          class="gis-alarm-item"
          :class="[`is-${alarm.level}`, { 'is-locatable': alarm.locatable }]"
          :title="alarm.locatable ? '点击定位到地图' : '该告警接口暂未提供可关联坐标'"
          @click="$emit('locate', alarm)"
        >
          <span class="gis-alarm-item__signal" aria-hidden="true">
            <svg viewBox="0 0 20 20" fill="none">
              <path d="M10 2.5 18 17H2L10 2.5Z" fill="currentColor" />
              <path d="M10 7v4.4M10 14.2v.2" stroke="#fff" stroke-width="1.6" stroke-linecap="round" />
            </svg>
          </span>
          <span class="gis-alarm-item__content">
            <span class="gis-alarm-item__top">
              <b>{{ alarm.levelLabel }}</b>
              <strong>{{ alarm.title }}</strong>
              <time>{{ alarm.time }}</time>
            </span>
            <span class="gis-alarm-item__meta">
              <span>{{ alarm.area || alarm.device || '未提供区域' }}</span>
              <em v-if="!alarm.locatable">暂无坐标</em>
            </span>
          </span>
        </button>
      </div>
      <div v-else class="gis-business__empty">真实告警接口暂无数据</div>
    </section>

    <section class="gis-business__card gis-business__card--risk">
      <header class="gis-business__head">
        <div>
          <h3>风险统计</h3>
          <p>当前接口风险分布</p>
        </div>
      </header>
      <div v-if="riskTotal > 0" class="gis-risk">
        <div class="gis-risk__donut" :style="{ '--risk-gradient': riskGradient }">
          <div class="gis-risk__center">
            <strong>{{ riskTotal }}</strong>
            <span>总计</span>
          </div>
        </div>
        <div class="gis-risk__legend">
          <div v-for="item in riskItems" :key="item.key" class="gis-risk__row">
            <i :style="{ backgroundColor: item.color }"></i>
            <span>{{ item.label }}</span>
            <b>{{ item.value }}</b>
          </div>
        </div>
      </div>
      <div v-else class="gis-business__empty">暂无可统计的风险等级数据</div>
    </section>

    <section class="gis-business__card gis-business__card--online">
      <header class="gis-business__head">
        <div>
          <h3>设备在线率</h3>
          <p>{{ online.available ? '基于当前设备状态' : '当前接口未提供在线状态' }}</p>
        </div>
        <span class="gis-online__value" :class="{ 'is-empty': !online.available }">
          {{ online.available ? `${online.rate}%` : '--' }}
        </span>
      </header>
      <div v-if="online.available" class="gis-online__track" aria-hidden="true">
        <span :style="{ width: `${online.rate}%` }"></span>
      </div>
      <div class="gis-online__meta">
        <span>在线 {{ online.online ?? '--' }}</span>
        <span>设备 {{ online.total ?? '--' }}</span>
      </div>
      <p class="gis-online__note">
        {{ online.hasHistory ? '最近 24h 状态趋势来自真实历史接口' : '未提供历史状态，因此不生成模拟趋势' }}
      </p>
    </section>
  </aside>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  alarms: { type: Array, default: () => [] },
  todayCount: { type: Number, default: 0 },
  riskItems: { type: Array, default: () => [] },
  online: {
    type: Object,
    default: () => ({ available: false, rate: 0, online: null, total: null, hasHistory: false })
  }
})

defineEmits(['locate'])

const riskTotal = computed(() => props.riskItems.reduce((sum, item) => sum + Number(item.value || 0), 0))

const riskGradient = computed(() => {
  if (!riskTotal.value) return '#E9EDF2 0 100%'
  let cursor = 0
  return props.riskItems.map((item) => {
    const start = cursor
    cursor += Number(item.value || 0) / riskTotal.value * 100
    return `${item.color} ${start.toFixed(2)}% ${cursor.toFixed(2)}%`
  }).join(', ')
})
</script>

<style scoped>
.gis-business {
  display: grid;
  grid-template-rows: minmax(220px, 1.25fr) minmax(190px, 0.9fr) minmax(145px, 0.6fr);
  gap: 12px;
  min-width: 0;
  min-height: 0;
  padding: 0 0 0 12px;
  background: var(--app-bg, #f4f6f8);
  overflow-x: hidden;
  overflow-y: auto;
  scrollbar-width: thin;
}

.gis-business__card {
  min-height: 0;
  overflow: hidden;
  background: rgba(255, 255, 255, 0.96);
  border: 1px solid var(--app-border, #e7eaee);
  border-radius: 14px;
  box-shadow: 0 4px 18px rgba(39, 54, 68, 0.05);
}

.gis-business__head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 10px;
  padding: 14px 15px 12px;
  border-bottom: 1px solid var(--app-border, #edf0f3);
}
.gis-business__head h3 { margin: 0; color: var(--app-text-1, #252a31); font-size: 14px; font-weight: 650; }
.gis-business__head p { margin: 4px 0 0; color: var(--app-text-4, #929aa5); font-size: 11px; }
.gis-business__summary {
  flex: none;
  padding: 4px 8px;
  color: #3974aa;
  background: #eef6fd;
  border-radius: 999px;
  font-size: 11px;
  white-space: nowrap;
}

.gis-alarm-list { height: calc(100% - 61px); overflow: auto; scrollbar-width: thin; }
.gis-alarm-item {
  display: flex;
  gap: 9px;
  width: 100%;
  padding: 11px 14px;
  color: #87909a;
  background: transparent;
  border: 0;
  border-bottom: 1px solid var(--app-border, #edf0f3);
  text-align: left;
  cursor: default;
}
.gis-alarm-item.is-locatable { cursor: pointer; }
.gis-alarm-item.is-locatable:hover { background: #f6f9fc; }
.gis-alarm-item:last-child { border-bottom: 0; }
.gis-alarm-item__signal { flex: none; width: 18px; height: 18px; margin-top: 1px; color: #3b80bf; }
.gis-alarm-item__signal svg { display: block; width: 100%; height: 100%; }
.gis-alarm-item.is-high .gis-alarm-item__signal,
.gis-alarm-item.is-high .gis-alarm-item__top b { color: #c9433b; }
.gis-alarm-item.is-elevated .gis-alarm-item__signal,
.gis-alarm-item.is-elevated .gis-alarm-item__top b { color: #d97732; }
.gis-alarm-item.is-medium .gis-alarm-item__signal,
.gis-alarm-item.is-medium .gis-alarm-item__top b { color: #d5a126; }
.gis-alarm-item__content { flex: 1; min-width: 0; }
.gis-alarm-item__top { display: grid; grid-template-columns: auto minmax(0, 1fr) auto; align-items: baseline; gap: 6px; }
.gis-alarm-item__top b { color: #397ebe; font-size: 11px; white-space: nowrap; }
.gis-alarm-item__top strong { overflow: hidden; color: var(--app-text-1, #2a3037); font-size: 12px; font-weight: 600; text-overflow: ellipsis; white-space: nowrap; }
.gis-alarm-item__top time { color: var(--app-text-4, #9aa1aa); font-size: 10px; font-variant-numeric: tabular-nums; white-space: nowrap; }
.gis-alarm-item__meta { display: flex; justify-content: space-between; gap: 8px; margin-top: 5px; color: var(--app-text-4, #8e97a2); font-size: 10px; }
.gis-alarm-item__meta span { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.gis-alarm-item__meta em { flex: none; color: #a2a8af; font-style: normal; }

.gis-business__empty { display: grid; place-items: center; min-height: 110px; padding: 18px; color: var(--app-text-4, #969ea8); font-size: 12px; text-align: center; }

.gis-risk { display: grid; grid-template-columns: 112px minmax(0, 1fr); align-items: center; gap: 12px; padding: 15px; }
.gis-risk__donut {
  position: relative;
  display: grid;
  place-items: center;
  width: 106px;
  aspect-ratio: 1;
  background: conic-gradient(var(--risk-gradient));
  border-radius: 50%;
}
.gis-risk__donut::after { position: absolute; inset: 20px; content: ''; background: #fff; border-radius: 50%; }
.gis-risk__center { position: relative; z-index: 1; display: flex; flex-direction: column; align-items: center; }
.gis-risk__center strong { color: var(--app-text-1, #262d34); font-size: 25px; line-height: 1; font-variant-numeric: tabular-nums; }
.gis-risk__center span { margin-top: 4px; color: var(--app-text-4, #969ea8); font-size: 10px; }
.gis-risk__legend { display: flex; flex-direction: column; gap: 8px; min-width: 0; }
.gis-risk__row { display: grid; grid-template-columns: 8px minmax(0, 1fr) auto; align-items: center; gap: 7px; color: var(--app-text-3, #68717c); font-size: 11px; }
.gis-risk__row i { width: 7px; height: 7px; border-radius: 50%; }
.gis-risk__row b { color: var(--app-text-1, #2d333a); font-size: 12px; font-variant-numeric: tabular-nums; }

.gis-online__value { color: #3a8c69; font-size: 23px; font-weight: 700; line-height: 1; font-variant-numeric: tabular-nums; }
.gis-online__value.is-empty { color: #aab0b7; }
.gis-online__track { height: 5px; margin: 14px 15px 0; overflow: hidden; background: #edf1f4; border-radius: 999px; }
.gis-online__track span { display: block; height: 100%; background: #4f9a79; border-radius: inherit; }
.gis-online__meta { display: flex; justify-content: space-between; margin: 10px 15px 0; color: var(--app-text-3, #6e7782); font-size: 11px; }
.gis-online__note { margin: 9px 15px 14px; color: var(--app-text-4, #999fa8); font-size: 10px; line-height: 1.45; }

@media (max-width: 1280px) {
  .gis-risk { grid-template-columns: 92px minmax(0, 1fr); gap: 8px; padding-inline: 12px; }
  .gis-risk__donut { width: 88px; }
  .gis-risk__donut::after { inset: 17px; }
}
</style>
