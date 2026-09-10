<template>
  <div class="orders-page">
    <div class="page-heading">
      <button class="back-button" aria-label="返回个人中心" title="返回个人中心" @click="$router.push('/profile')">←</button>
      <div>
        <p>STUDENT WALLET</p>
        <h2 class="page-title">我的订单</h2>
      </div>
    </div>

    <section class="wallet-panel" aria-label="学生钱包概览">
      <div class="wallet-top">
        <div>
          <div class="wallet-label"><span></span>食愿钱包</div>
          <div class="wallet-balance"><small>¥</small><strong>{{ money(summary.available_balance) }}</strong></div>
          <p>可用余额</p>
        </div>
        <div class="wallet-brand">FoodLink</div>
      </div>
      <div class="wallet-stats">
        <div>
          <span>平台托管</span>
          <strong>¥{{ money(summary.escrow_amount) }}</strong>
        </div>
        <div>
          <span>本月消费</span>
          <strong>¥{{ money(summary.monthly_spending) }}</strong>
        </div>
        <div>
          <span>本月订单</span>
          <strong>{{ summary.monthly_order_count }}<small> 笔</small></strong>
        </div>
      </div>
      <div v-if="summaryLoading" class="summary-loading">正在更新资金数据…</div>
    </section>

    <div class="section-heading">
      <div>
        <span>订单记录</span>
        <small>购买、领取与结算状态</small>
      </div>
    </div>

    <div class="tabs order-tabs" role="tablist" aria-label="订单状态">
      <button v-for="t in tabs" :key="t.label" class="tab" :class="{ active: status === t.status }"
        @click="changeTab(t.status)">{{ t.label }}</button>
    </div>

    <div v-if="loading" class="empty">加载中…</div>
    <div v-else-if="!orders.length" class="empty"><div class="big">🛒</div>暂无{{ currentLabel }}订单</div>

    <div v-for="o in orders" :key="o.id" class="card order-card">
      <div class="order-top">
        <span class="shop">{{ o.shop_name }}</span>
        <span class="status-badge" :class="statusClass(o.status)">{{ statusText(o) }}</span>
      </div>
      <div class="order-body">
        <div class="thumb"><template v-if="o.product_image"><img :src="o.product_image" alt="" /></template><span v-else>🍱</span></div>
        <div class="order-info">
          <div class="title">{{ o.product_title }}</div>
          <div class="meta">下单时间：{{ o.created_at }} ｜ 数量：{{ o.quantity }}</div>
          <div class="meta">取货处：{{ o.location }}</div>
        </div>
      </div>
      <div v-if="o.status === 0" class="pickup-timer">
        <div>
          <span>领取倒计时</span>
          <small>请在 {{ o.pickup_deadline }} 前领取</small>
        </div>
        <strong>{{ countdownText(o) }}</strong>
      </div>
      <div class="payment-state">
        <span><i></i>{{ o.payment_status === 'settled' ? '已结算' : '平台托管中' }}</span>
        <small v-if="o.status === 0">超时后系统自动完成并结算给商家</small>
        <small v-else-if="o.status === 1">{{ completionText(o) }} · {{ o.settled_at }}</small>
      </div>
      <div class="order-foot">
        <span class="amount">实付 <span class="price">¥{{ orderTotal(o) }}</span></span>
        <button v-if="o.status === 0" class="btn btn-primary btn-sm" @click="showCode(o)">查看取货凭证</button>
        <span v-else-if="o.status === 1" class="completion-label">{{ completionText(o) }}</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { useRouter } from 'vue-router'
import { getOrders, getOrderSummary } from '../../api/order'
import { completionText, orderTotal, useOrderCountdown } from '../../utils/orderCountdown'

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
const summaryLoading = ref(false)
const summary = ref({
  available_balance: '0.00',
  escrow_amount: '0.00',
  monthly_spending: '0.00',
  monthly_order_count: 0
})
const currentLabel = computed(() => tabs.find(t => t.status === status.value)?.label || '')
const { now, remainingSeconds, countdownText } = useOrderCountdown()
let lastOverdueRefresh = 0

async function load(quiet = false) {
  if (!quiet) loading.value = true
  summaryLoading.value = true
  const [orderResult, summaryResult] = await Promise.allSettled([
    getOrders({ status: status.value === null ? '' : status.value }),
    getOrderSummary()
  ])
  if (orderResult.status === 'fulfilled') orders.value = orderResult.value
  if (summaryResult.status === 'fulfilled') summary.value = summaryResult.value
  if (!quiet) loading.value = false
  summaryLoading.value = false
}

function changeTab(s) { status.value = s; load() }

function statusText(order) {
  if (order.status === 1) return order.completion_type === 'auto_timeout' ? '超时完成' : '已领取'
  return { 0: '待领取', 2: '已关闭' }[order.status] || '未知'
}
function statusClass(s) { return { 0: 'st-pending', 1: 'st-picked', 2: 'st-expired' }[s] || '' }
function money(value) { return Number(value || 0).toFixed(2) }

function showCode(o) {
  sessionStorage.setItem('shiyuan_last_order', JSON.stringify(o))
  router.push('/order/pickup')
}

watch(now, () => {
  const hasOverdue = orders.value.some(order => order.status === 0 && remainingSeconds(order) === 0)
  if (!hasOverdue || Date.now() - lastOverdueRefresh < 5000) return
  lastOverdueRefresh = Date.now()
  load(true)
})

load()
</script>

<style scoped>
.orders-page { --ink: #17211c; --soft-green: #dff2e7; }
.page-heading { display: flex; align-items: center; gap: 12px; margin-bottom: 18px; }
.page-heading p { margin: 0 0 2px; color: #8a938e; font-size: 10px; font-weight: 700; letter-spacing: 0; }
.page-title { margin: 0; font-size: 25px; line-height: 1.2; }
.back-button { width: 36px; height: 36px; flex: 0 0 36px; border: 1px solid var(--border); border-radius: 8px; background: #fff; color: var(--text); font-size: 18px; cursor: pointer; }
.back-button:hover { border-color: #b8c1bc; background: #f9faf9; }
.wallet-panel { position: relative; overflow: hidden; margin-bottom: 28px; padding: 22px; border-radius: 8px; background: var(--ink); color: #fff; box-shadow: 0 16px 34px rgba(23, 33, 28, .16); }
.wallet-panel::after { content: ''; position: absolute; right: -24px; top: -52px; width: 150px; height: 150px; border: 30px solid rgba(255,255,255,.035); border-radius: 50%; pointer-events: none; }
.wallet-top { position: relative; z-index: 1; display: flex; align-items: flex-start; justify-content: space-between; gap: 20px; }
.wallet-label { display: flex; align-items: center; gap: 7px; color: #dce5e0; font-size: 13px; font-weight: 600; }
.wallet-label span { width: 7px; height: 7px; border-radius: 50%; background: #79d19d; box-shadow: 0 0 0 4px rgba(121, 209, 157, .12); }
.wallet-balance { display: flex; align-items: flex-start; gap: 5px; margin-top: 12px; font-variant-numeric: tabular-nums; }
.wallet-balance small { margin-top: 8px; color: #b7c4bd; font-size: 15px; }
.wallet-balance strong { font-size: 36px; line-height: 1; font-weight: 700; }
.wallet-top p { margin: 7px 0 0; color: #94a39b; font-size: 12px; }
.wallet-brand { color: #91a098; font-size: 12px; font-weight: 700; }
.wallet-stats { position: relative; z-index: 1; display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); margin-top: 24px; padding-top: 16px; border-top: 1px solid rgba(255,255,255,.11); }
.wallet-stats > div { min-width: 0; padding: 0 14px; border-right: 1px solid rgba(255,255,255,.1); }
.wallet-stats > div:first-child { padding-left: 0; }
.wallet-stats > div:last-child { padding-right: 0; border-right: 0; }
.wallet-stats span { display: block; color: #94a39b; font-size: 11px; }
.wallet-stats strong { display: block; margin-top: 5px; overflow-wrap: anywhere; color: #f8faf9; font-size: 16px; font-variant-numeric: tabular-nums; }
.wallet-stats small { color: #b7c4bd; font-size: 11px; font-weight: 500; }
.summary-loading { position: absolute; right: 20px; bottom: 6px; color: #78877f; font-size: 10px; }
.section-heading { display: flex; align-items: flex-end; justify-content: space-between; margin-bottom: 12px; }
.section-heading span { display: block; font-size: 17px; font-weight: 700; }
.section-heading small { display: block; margin-top: 2px; color: var(--muted); font-size: 11px; }
.order-tabs { width: max-content; max-width: 100%; gap: 2px; padding: 3px; border: 1px solid var(--border); border-radius: 8px; background: #fff; }
.order-tabs .tab { min-width: 64px; padding: 7px 12px; border: 0; border-radius: 6px; background: transparent; }
.order-tabs .tab.active { background: var(--ink); color: #fff; }
.order-card { padding: 16px; border-radius: 8px; box-shadow: 0 5px 16px rgba(31, 41, 55, .035); }
.order-top { display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; }
.shop { font-weight: 700; }
.status-badge { padding: 3px 8px; border-radius: 6px; background: #f4f5f4; font-size: 11px; font-weight: 700; }
.status-badge.st-pending { background: #fff4df; }
.status-badge.st-picked { background: var(--soft-green); }
.order-body { display: flex; gap: 12px; }
.thumb { width: 64px; height: 64px; border-radius: 8px; background: #f3f4f6; display: flex; align-items: center; justify-content: center; font-size: 22px; overflow: hidden; flex-shrink: 0; }
.thumb img { width: 100%; height: 100%; object-fit: cover; }
.order-info { flex: 1; }
.title { font-weight: 600; }
.meta { color: var(--muted); font-size: 12px; margin-top: 3px; }
.pickup-timer { display: flex; align-items: center; justify-content: space-between; gap: 12px; margin-top: 12px; padding: 10px 12px; border-left: 3px solid var(--primary); border-radius: 0 6px 6px 0; background: #fff7ed; }
.pickup-timer span { display: block; color: var(--primary-dark); font-size: 13px; font-weight: 700; }
.pickup-timer small { display: block; margin-top: 2px; color: var(--muted); font-size: 11px; }
.pickup-timer strong { flex-shrink: 0; color: var(--primary-dark); font-size: 20px; font-variant-numeric: tabular-nums; }
.payment-state { display: flex; align-items: baseline; justify-content: space-between; gap: 10px; margin-top: 10px; color: var(--muted); font-size: 12px; }
.payment-state > span { display: inline-flex; align-items: center; gap: 5px; color: var(--success); font-weight: 700; }
.payment-state i { width: 6px; height: 6px; border-radius: 50%; background: currentColor; }
.payment-state small { text-align: right; }
.order-foot { display: flex; justify-content: space-between; align-items: center; margin-top: 12px; padding-top: 8px; border-top: 1px dashed var(--border); }
.completion-label { color: var(--success); font-size: 12px; font-weight: 600; }
@media (max-width: 520px) {
  .orders-page { width: calc(100vw - 32px); max-width: 100%; }
  .wallet-panel { padding: 18px; }
  .wallet-balance strong { font-size: 31px; }
  .wallet-stats > div { padding: 0 8px; }
  .wallet-stats strong { font-size: 14px; }
  .order-tabs { width: 100%; }
  .order-tabs .tab { flex: 1; min-width: 0; padding-inline: 7px; }
  .payment-state { align-items: flex-start; flex-direction: column; gap: 3px; }
  .payment-state small { text-align: left; }
}
@media (max-width: 600px) {
  :global(.topbar-inner) { width: 100vw; gap: 9px; padding: 10px 12px; }
  :global(.topbar .brand) { flex-shrink: 0; font-size: 17px; }
  :global(.topbar .topnav) { flex: 0 1 auto; min-width: 0; gap: 10px; }
  :global(.topbar .topnav a) { white-space: nowrap; font-size: 11px; }
  :global(.topbar .grow), :global(.topbar .hello) { display: none; }
  :global(.topbar .btn-ghost) { flex-shrink: 0; padding: 4px; font-size: 11px; }
}
</style>
