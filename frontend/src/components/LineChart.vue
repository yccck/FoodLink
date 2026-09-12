<template>
  <div class="line-chart">
    <div class="lc-wrap">
      <svg class="lc-svg" viewBox="0 0 100 100" preserveAspectRatio="none" aria-hidden="true">
        <defs>
          <linearGradient id="lc-grad" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" :stop-color="color" stop-opacity="0.28"/>
            <stop offset="100%" :stop-color="color" stop-opacity="0"/>
          </linearGradient>
        </defs>
        <path v-if="points.length >= 2" :d="areaPath" fill="url(#lc-grad)"/>
        <polyline :points="linePoints" fill="none" :stroke="color" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"/>
      </svg>
      <span v-for="(pt, i) in points" :key="i" class="lc-dot"
        :style="{ left: pt.x + '%', top: pt.y + '%', background: color }"></span>
    </div>
    <div class="lc-labels" v-if="data.length">
      <span v-for="item in data" :key="item.label" class="lc-label">{{ labelOf(item) }}</span>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  data: { type: Array, default: () => [] },
  color: { type: String, default: '#f97316' }
})
const values = computed(() => props.data.map(d => Number(d.value) || 0))
const max = computed(() => Math.max(1, ...values.value))
const points = computed(() => {
  const n = props.data.length
  const top = 12
  const bottom = 88
  return props.data.map((d, i) => {
    const x = n <= 1 ? 50 : (100 * i) / (n - 1)
    const y = bottom - ((Number(d.value) || 0) / max.value) * (bottom - top)
    return { x, y }
  })
})
const linePoints = computed(() => points.value.map(p => `${p.x},${p.y}`).join(' '))
const areaPath = computed(() => {
  if (points.value.length < 2) return ''
  const p = points.value
  return 'M ' + p[0].x + ',100 L ' + p.map(q => q.x + ',' + q.y).join(' L ') + ' L ' + p[p.length - 1].x + ',100 Z'
})
function labelOf(item) { return item.shortLabel || item.label }
</script>

<style scoped>
.line-chart { width: 100%; }
.lc-wrap { position: relative; width: 100%; height: 190px; }
.lc-svg { position: absolute; inset: 0; width: 100%; height: 100%; display: block; }
.lc-dot {
  position: absolute; width: 9px; height: 9px; border-radius: 50%;
  border: 2px solid #fff; box-shadow: 0 1px 3px rgba(0,0,0,.22);
  transform: translate(-50%, -50%);
}
.lc-labels { display: flex; gap: 8px; margin-top: 8px; }
.lc-label { flex: 1; text-align: center; font-size: 11px; color: var(--muted); }
</style>