<template>
  <div class="gis-layers">
    <section v-for="grp in grouped" :key="grp.name" class="gis-layers__group">
      <h4 class="gis-layers__group-title">{{ grp.name }}</h4>
      <label
        v-for="layer in grp.items"
        :key="layer.key"
        class="gis-layer"
        :class="{ 'is-off': !layer.visible }"
      >
        <input
          type="checkbox"
          class="gis-layer__cb"
          :checked="layer.visible"
          @change="$emit('toggle', layer.key, $event.target.checked)"
        />
        <span
          class="gis-layer__swatch"
          :class="layer.geometry === 'line' ? 'is-line' : 'is-point'"
          :style="{ '--swatch': layer.color }"
        ></span>
        <span class="gis-layer__name">{{ layer.label }}</span>
        <span class="gis-layer__count">{{ layer.count }}</span>
      </label>
    </section>

    <section class="gis-layers__group">
      <h4 class="gis-layers__group-title">状态图例</h4>
      <div v-for="s in STATUS_OPTIONS" :key="s.value" class="gis-legend-row">
        <span class="gis-legend-dot" :style="{ background: STATUS[s.value].color }"></span>
        <span class="gis-legend-text">{{ STATUS[s.value].label }}</span>
      </div>
      <p class="gis-layers__hint">缩放地图可分级显示：井盖、设备点位在高缩放级别出现。</p>
    </section>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { LAYER_GROUPS, STATUS, STATUS_OPTIONS } from '@/config/gisLayers'

const props = defineProps({
  /** [{ key, label, group, geometry, color, visible, count }] */
  layers: { type: Array, required: true }
})

defineEmits(['toggle'])

const grouped = computed(() =>
  LAYER_GROUPS
    .map((name) => ({ name, items: props.layers.filter((l) => l.group === name) }))
    .filter((g) => g.items.length > 0)
)
</script>

<style scoped>
.gis-layers {
  display: flex;
  flex-direction: column;
  gap: 18px;
  padding: 4px 0 12px;
}

.gis-layers__group {
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-width: 0;
}

.gis-layers__group-title {
  margin: 0 0 6px;
  padding: 0 10px;
  font-size: 11px;
  font-weight: 600;
  letter-spacing: 0.06em;
  color: var(--app-text-4);
  text-transform: none;
  white-space: nowrap;
}

/* 单个图层行 */
.gis-layer {
  display: flex;
  align-items: center;
  gap: 10px;
  min-width: 0;
  padding: 8px 10px;
  border-radius: 12px;
  cursor: pointer;
  user-select: none;
  transition: background-color 0.18s ease, opacity 0.18s ease;
}
.gis-layer:hover {
  background-color: var(--app-hover);
}
.gis-layer.is-off {
  opacity: 0.45;
}

.gis-layer__cb {
  flex-shrink: 0;
  width: 15px;
  height: 15px;
  margin: 0;
  accent-color: var(--app-primary);
  cursor: pointer;
}

/* 图例色块：管线用短横线，点位用圆点 */
.gis-layer__swatch {
  flex-shrink: 0;
  background: var(--swatch);
}
.gis-layer__swatch.is-line {
  width: 18px;
  height: 4px;
  border-radius: 2px;
}
.gis-layer__swatch.is-point {
  width: 11px;
  height: 11px;
  margin: 0 3px;
  border-radius: 50%;
  box-shadow: 0 0 0 2px #fff;
}

.gis-layer__name {
  flex: 1;
  min-width: 0;
  font-size: 13px;
  color: var(--app-text-1);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.gis-layer__count {
  flex-shrink: 0;
  min-width: 24px;
  padding: 1px 7px;
  font-size: 11px;
  font-variant-numeric: tabular-nums;
  text-align: center;
  color: var(--app-text-3);
  background-color: var(--app-hover);
  border-radius: var(--app-radius-tag);
}

/* 状态图例 */
.gis-legend-row {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 5px 10px;
}
.gis-legend-dot {
  width: 9px;
  height: 9px;
  border-radius: 50%;
  box-shadow: 0 0 0 2px #fff;
  flex-shrink: 0;
}
.gis-legend-text {
  font-size: 12px;
  color: var(--app-text-2);
  white-space: nowrap;
}

.gis-layers__hint {
  margin: 8px 10px 0;
  font-size: 11px;
  line-height: 1.6;
  color: var(--app-text-4);
}
</style>
