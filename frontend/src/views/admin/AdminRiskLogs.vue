<template>
  <div>
    <h2 class="page-title">风控日志</h2>

    <div class="tabs">
      <button v-for="t in tabs" :key="t.label" class="tab" :class="{ active: filter === t.value }" @click="filter = t.value; load()">{{ t.label }}</button>
    </div>

    <div v-if="loading" class="empty">加载中…</div>
    <div v-else-if="!logs.length" class="empty"><div class="big">🛡</div>暂无风控日志</div>

    <div v-for="l in logs" :key="l.id" class="card risk">
      <div class="r-head">
        <span class="r-type" :class="typeClass(l.risk_type)">{{ l.risk_type_name }}</span>
        <span :class="l.is_resolved ? 'done' : 'undone'">{{ l.is_resolved ? '已处理' : '未处理' }}</span>
      </div>
      <div class="r-prod">{{ l.product_title }} · {{ l.shop_name }}</div>
      <div class="r-detail">原因：{{ l.risk_detail }}</div>
      <div class="r-meta">{{ l.created_at }}<span v-if="l.risk_code"> · code={{ l.risk_code }}</span></div>
      <div class="r-actions">
        <button v-if="!l.is_resolved" class="btn btn-outline btn-sm" @click="resolve(l)">误判恢复</button>
        <span v-else class="done">✓ 已恢复商品上架</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { getRiskLogs, resolveRiskLog } from '../../api/admin'
import { toast } from '../../utils/toast'

const tabs = [{ label: '全部', value: '' }, { label: '未处理', value: '0' }, { label: '已处理', value: '1' }]
const filter = ref('')
const logs = ref([])
const loading = ref(false)

async function load() {
  loading.value = true
  try { logs.value = await getRiskLogs({ resolved: filter.value }) } catch (e) { /* 拦截器 */ } finally { loading.value = false }
}
async function resolve(l) {
  try { await resolveRiskLog(l.id); toast('已恢复，商品重新上架'); await load() }
  catch (e) { /* 拦截器 */ }
}
function typeClass(t) { return { 1: 't-price', 2: 't-word', 3: 't-expire' }[t] || '' }
onMounted(load)
</script>

<style scoped>
.page-title { margin: 4px 0 16px; }
.r-head { display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; }
.r-type { font-size: 12px; padding: 2px 10px; border-radius: 10px; color: #fff; }
.t-price { background: #ef4444; }
.t-word { background: #8b5cf6; }
.t-expire { background: #f59e0b; }
.done { color: var(--success); font-size: 12px; }
.undone { color: var(--warn); font-size: 12px; }
.r-prod { font-weight: 600; }
.r-detail, .r-meta { color: var(--muted); font-size: 13px; margin-top: 4px; }
.r-actions { margin-top: 10px; }
</style>