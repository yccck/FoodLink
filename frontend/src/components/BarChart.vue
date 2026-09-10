<template>
  <div class="chart" :class="{ horizontal }">
    <!-- 横排条形图 -->
    <div v-if="horizontal" class="hbars">
      <div v-for="item in data" :key="item.label" class="hrow">
        <span class="h-label">{{ item.label }}</span>
        <div class="h-track"><div class="h-fill" :style="{ width: pct(item.value) + '%', background: item.color || color }"></div></div>
        <span class="h-value">{{ item.value }}</span>
      </div>
    </div>
    <!-- 竖排柱状图 -->
    <div v-else class="vbars">
      <div class="v-stage">
        <div v-for="item in data" :key="item.label" class="vcol">
          <span class="v-value">{{ item.value }}</span>
          <div class="v-track"><div class="v-fill" :style="{ height: pct(item.value) + '%', background: item.color || color }"></div></div>
        </div>
      </div>
      <div class="v-labels">
        <span v-for="item in data" :key="item.label" class="v-label">{{ labelOf(item) }}</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  data: { type: Array, default: () => [] },
  horizontal: { type: Boolean, default: false },
  color: { type: String, default: '#f97316' }
})
const max = computed(() => Math.max(1, ...props.data.map(d => Number(d.value) || 0)))
function pct(v) { return Math.round(((Number(v) || 0) / max.value) * 100) }
function labelOf(item) { return item.shortLabel || item.label }
</script>

<style scoped>
.hbars { display: flex; flex-direction: column; gap: 10px; }
.hrow { display: flex; align-items: center; gap: 8px; font-size: 13px; }
.h-label { width: 56px; color: var(--muted); text-align: right; flex-shrink: 0; }
.h-track { flex: 1; height: 12px; background: #f3f4f6; border-radius: 6px; overflow: hidden; }
.h-fill { height: 100%; border-radius: 6px; transition: width .4s; }
.h-value { width: 24px; text-align: right; font-weight: 600; }

.vbars { width: 100%; }
.v-stage { display: flex; align-items: flex-end; gap: 8px; height: 160px; }
.vcol { flex: 1; display: flex; flex-direction: column; align-items: center; gap: 4px; height: 100%; justify-content: flex-end; }
.v-value { font-size: 12px; font-weight: 600; color: var(--text); }
.v-track { width: 60%; height: 100%; background: #f3f4f6; border-radius: 6px 6px 0 0; overflow: hidden; display: flex; align-items: flex-end; }
.v-fill { width: 100%; border-radius: 6px 6px 0 0; transition: height .4s; }
.v-labels { display: flex; gap: 8px; margin-top: 6px; }
.v-label { flex: 1; text-align: center; font-size: 11px; color: var(--muted); }
</style>