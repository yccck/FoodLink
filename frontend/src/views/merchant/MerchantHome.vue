<template>
  <div>
    <div class="head">
      <div>
        <div class="title">我的商品 <small class="count">共 {{ visibleProducts.length }} 件</small></div>
      </div>
      <button class="btn btn-primary btn-publish" @click="$router.push('/merchant/publish')">＋ 发布商品</button>
    </div>

    <div v-if="loading" class="empty">加载中…</div>
    <div v-else-if="!visibleProducts.length" class="empty"><div class="big">📦</div>还没有可展示的商品，点击右上角发布</div>

    <div v-else class="prod-grid">
    <div v-for="p in visibleProducts" :key="p.id" class="card prod">
      <div class="thumb"><img v-if="p.image" :src="p.image" alt="" /><span v-else>{{ p.emoji || '🍱' }}</span></div>
      <div class="info">
        <div class="prod-title">
          <span class="prod-name">{{ p.title }}</span>
          <span class="product-labels">
            <span class="tag category-tag">{{ p.category }}</span>
            <span class="st" :class="statusClass(p)">{{ statusText(p) }}</span>
          </span>
        </div>
        <div class="meta-row">
          <span class="price">¥{{ p.discount_price }}</span>
          <span class="line">¥{{ p.original_price }}</span>
        </div>
        <div class="meta-row muted">
          剩余 {{ p.quantity }} 份 · 有效期至 {{ p.expire_time }}
        </div>
        <div class="meta-row muted">营业时间 {{ p.business_open_time || '08:00' }}–{{ p.business_close_time || '22:00' }}</div>
        <div v-if="isRiskBlocked(p)" class="risk-note">⛔ 已被风控拦截，可在超管端“误判恢复”</div>
      </div>
      <button
        class="btn btn-sm"
        :class="{ 'risk-disabled': isRiskBlocked(p) }"
        :disabled="isRiskBlocked(p)"
        :title="isRiskBlocked(p) ? '风控拦截商品需由超管误判恢复' : ''"
        @click="toggle(p)"
      >{{ p.status === 0 ? '上架' : '下架' }}</button>
    </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onBeforeUnmount, onMounted } from 'vue'

import { getMyProducts, toggleOffline } from '../../api/merchant'
import { toast } from '../../utils/toast'
import { isProductExpired } from '../../utils/productAvailability'

const products = ref([])
const loading = ref(false)
const now = ref(Date.now())
const visibleProducts = computed(() => products.value.filter(product => !isProductExpired(product, now.value)))
let expiryTimer = null

function statusText(p) {
  if (isRiskBlocked(p)) return '风控拦截'
  return { 1: '在售', 0: '已下架', 2: '售罄' }[p.status] || '未知'
}
function isRiskBlocked(p) { return Number(p?.risk_flag) === 1 || p?.risk_flag === true || Number(p?.status) === 3 }
function statusClass(p) { return isRiskBlocked(p) ? 'st-risk' : ({ 1: 'st-on', 0: 'st-off' }[p.status] || '') }

async function load() {
  loading.value = true
  try { products.value = await getMyProducts() } catch (e) { /* 拦截器 */ } finally { loading.value = false }
}
async function toggle(p) {
  if (isRiskBlocked(p)) return
  try {
    await toggleOffline(p.id)
    toast(p.status === 0 ? '已上架' : '已下架')
    await load()
  } catch (e) { /* 拦截器 */ }
}
onMounted(() => {
  expiryTimer = setInterval(() => { now.value = Date.now() }, 1000)
  load()
})
onBeforeUnmount(() => { if (expiryTimer) clearInterval(expiryTimer) })
</script>

<style scoped>
.head { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }
.title { font-size: 22px; font-weight: 800; }
.count { color: var(--muted); font-size: 12px; font-weight: 600; margin-left: 8px; }
.btn-publish { padding: 12px 24px; border-radius: 10px; font-size: 17px; }
.prod-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 14px; }
.prod { display: flex; gap: 12px; align-items: center; }
.thumb { width: 70px; height: 70px; border-radius: 8px; background: #f3f4f6; display: flex; align-items: center; justify-content: center; font-size: 26px; flex-shrink: 0; overflow: hidden; }
.thumb img { width: 100%; height: 100%; object-fit: cover; }
.info { flex: 1; }
.prod-title { display: flex; flex-wrap: wrap; align-items: center; gap: 6px 10px; margin-bottom: 4px; font-weight: 600; }
.prod-name { min-width: 0; }
.product-labels { display: inline-flex; flex-shrink: 0; align-items: center; gap: 8px; }
.category-tag { margin: 0; white-space: nowrap; }
.st { padding: 1px 6px; border-radius: 6px; font-size: 11px; white-space: nowrap; }
.st-on { background: #dcfce7; color: #16a34a; }
.st-off { background: #f3f4f6; color: #9ca3af; }
.st-risk { background: #fee2e2; color: #dc2626; }
.meta-row { font-size: 13px; margin-top: 2px; }
.line { text-decoration: line-through; color: #9ca3af; margin-left: 6px; font-size: 12px; }
.price { color: var(--primary); font-weight: 700; }
.muted { color: var(--muted); }
.risk-note { color: #dc2626; font-size: 12px; margin-top: 4px; }
.risk-disabled, .risk-disabled:hover { border-color: #e5e7eb; background: #f3f4f6; color: #a1a1aa; cursor: not-allowed; opacity: 1; }

@media (max-width: 640px) { .prod-grid { grid-template-columns: 1fr; } }
</style>
