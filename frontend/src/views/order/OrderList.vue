<template>
  <div>
    <button class="btn btn-sm" @click="$router.push('/profile')">← 个人中心</button>
    <h2 class="page-title">我的订单</h2>

    <div class="tabs">
      <button v-for="t in tabs" :key="t.label" class="tab" :class="{ active: status === t.status }"
        @click="changeTab(t.status)">{{ t.label }}</button>
    </div>

    <div v-if="loading" class="empty">加载中…</div>
    <div v-else-if="!orders.length" class="empty"><div class="big">🛒</div>暂无{{ currentLabel }}订单</div>

    <div v-for="o in orders" :key="o.id" class="card order-card">
      <div class="order-top">
        <span class="shop">{{ o.shop_name }}</span>
        <span :class="statusClass(o.status)">{{ statusText(o.status) }}</span>
      </div>
      <div class="order-body">
        <div class="thumb"><template v-if="o.product_image"><img :src="o.product_image" alt="" /></template><span v-else>🍱</span></div>
        <div class="order-info">
          <div class="title">{{ o.product_title }}</div>
          <div class="meta">下单时间：{{ o.created_at }} ｜ 数量：{{ o.quantity }}</div>
          <div class="meta">取货处：{{ o.location }}</div>
        </div>
      </div>
      <div class="order-foot">
        <span class="amount"><span class="price">¥{{ o.price }}</span></span>
        <button v-if="o.status === 0" class="btn btn-primary btn-sm" @click="showCode(o)">查看取货凭证</button>
        <span v-else-if="o.status === 0" class="code-hint">凭证码：{{ o.pickup_code }}</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { getOrders } from '../../api/order'

const tabs = [
  { label: '全部', status: null },
  { label: '待领取', status: 0 },
  { label: '已领取', status: 1 },
  { label: '已过期', status: 2 }
]

const router = useRouter()
const status = ref(null)
const orders = ref([])
const loading = ref(false)
const currentLabel = computed(() => tabs.find(t => t.status === status.value)?.label || '')

async function load() {
  loading.value = true
  try {
    orders.value = await getOrders({ status: status.value === null ? '' : status.value })
  } catch (e) { /* 拦截器处理 */ } finally { loading.value = false }
}

function changeTab(s) { status.value = s; load() }

function statusText(s) { return { 0: '待领取', 1: '已领取', 2: '已过期' }[s] || '未知' }
function statusClass(s) { return { 0: 'st-pending', 1: 'st-picked', 2: 'st-expired' }[s] || '' }

function showCode(o) {
  sessionStorage.setItem('shiyuan_last_order', JSON.stringify(o))
  router.push('/order/pickup')
}

load()
</script>

<style scoped>
.page-title { margin: 4px 0 16px; }
.order-card { padding: 16px; }
.order-top { display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; }
.shop { font-weight: 700; }
.order-body { display: flex; gap: 12px; }
.thumb { width: 64px; height: 64px; border-radius: 8px; background: #f3f4f6; display: flex; align-items: center; justify-content: center; font-size: 22px; overflow: hidden; flex-shrink: 0; }
.thumb img { width: 100%; height: 100%; object-fit: cover; }
.order-info { flex: 1; }
.title { font-weight: 600; }
.meta { color: var(--muted); font-size: 12px; margin-top: 3px; }
.order-foot { display: flex; justify-content: space-between; align-items: center; margin-top: 12px; padding-top: 8px; border-top: 1px dashed var(--border); }
</style>