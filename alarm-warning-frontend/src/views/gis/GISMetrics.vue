<template>
  <section class="gis-metrics" aria-label="GIS 关键业务指标">
    <article v-for="item in items" :key="item.key" class="gis-metric">
      <span class="gis-metric__icon" :class="`is-${item.tone || 'blue'}`" aria-hidden="true">
        <component :is="iconOf(item.icon)" />
      </span>
      <span class="gis-metric__content">
        <span class="gis-metric__label">{{ item.label }}</span>
        <strong>{{ item.value }}<small v-if="item.unit">{{ item.unit }}</small></strong>
        <span class="gis-metric__note">{{ item.note }}</span>
      </span>
    </article>
  </section>
</template>

<script setup>
import { DataLine, Monitor, Warning, Bell, Location } from '@element-plus/icons-vue'

defineProps({ items: { type: Array, default: () => [] } })

const ICONS = { pipeline: DataLine, device: Monitor, risk: Warning, alarm: Bell, point: Location }
function iconOf(name) { return ICONS[name] || DataLine }
</script>

<style scoped>
.gis-metrics {
  display: grid;
  grid-template-columns: repeat(5, minmax(0, 1fr));
  gap: 10px;
  flex: 0 0 clamp(126px, 15vh, 160px);
  min-width: 0;
  padding-top: 12px;
}
.gis-metric {
  display: flex;
  align-items: center;
  gap: 11px;
  min-width: 0;
  padding: 13px 14px;
  background: rgba(255, 255, 255, 0.96);
  border: 1px solid var(--app-border, #e7eaee);
  border-radius: 13px;
  box-shadow: 0 3px 14px rgba(39, 54, 68, 0.04);
}
.gis-metric__icon { display: grid; place-items: center; flex: none; width: 34px; height: 34px; color: #3d7db5; background: #eef5fb; border-radius: 10px; }
.gis-metric__icon :deep(svg) { width: 17px; height: 17px; }
.gis-metric__icon.is-orange { color: #c97834; background: #fff4ea; }
.gis-metric__icon.is-red { color: #bf4d47; background: #fdf0ef; }
.gis-metric__icon.is-green { color: #538b70; background: #edf7f1; }
.gis-metric__content { display: flex; flex-direction: column; min-width: 0; }
.gis-metric__label { color: var(--app-text-3, #707985); font-size: 10px; }
.gis-metric strong { margin-top: 2px; color: var(--app-text-1, #282e35); font-size: 20px; line-height: 1.15; font-variant-numeric: tabular-nums; }
.gis-metric strong small { margin-left: 3px; color: var(--app-text-3, #7c858f); font-size: 10px; font-weight: 500; }
.gis-metric__note { overflow: hidden; margin-top: 3px; color: var(--app-text-4, #9aa1aa); font-size: 9px; text-overflow: ellipsis; white-space: nowrap; }

@media (max-width: 1280px) {
  .gis-metrics { grid-template-columns: repeat(4, minmax(0, 1fr)); }
  .gis-metric:nth-child(5) { display: none; }
}

@media (max-width: 1024px) {
  .gis-metrics { grid-template-columns: repeat(2, minmax(0, 1fr)); flex-basis: auto; }
  .gis-metric:nth-child(5) { display: flex; }
}
</style>
