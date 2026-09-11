<template>
  <div class="merchant-orders-page">
    <div class="page-heading">
      <button class="back-button" aria-label="返回商品管理" title="返回商品管理" @click="$router.push('/merchant/home')">←</button>
      <div>
        <p>MERCHANT CENTER</p>
        <h2 class="page-title">订单与资金</h2>
      </div>
    </div>

    <section class="merchant-wallet" aria-label="商家钱包与本月经营概览">
      <div class="wallet-main">
        <div class="balance-block">
          <span class="wallet-label"><i></i>商家钱包</span>
          <div class="balance"><small>¥</small><strong>{{ money(summary.available_balance) }}</strong></div>
          <p>已结算可用余额</p>
          <div class="wallet-actions">
            <button type="button" @click="openWallet('recharge')"><span aria-hidden="true">＋</span>充值</button>
            <button type="button" @click="openWallet('withdraw')"><span aria-hidden="true">↗</span>提现</button>
          </div>
        </div>
        <div class="sales-block">
          <span>本月销售额</span>
          <strong>¥{{ money(summary.monthly_sales) }}</strong>
          <small>{{ summary.monthly_order_count }} 笔订单</small>
        </div>
      </div>
      <div class="business-grid">
        <div><span>待结算</span><strong>¥{{ money(summary.escrow_amount) }}</strong></div>
        <div><span>本月销量</span><strong>{{ summary.monthly_item_count }}<small> 份</small></strong></div>
        <div><span>本月已完成</span><strong>{{ summary.monthly_completed_count }}<small> 笔</small></strong></div>
        <div><span>本月净收入</span><strong>¥{{ money(summary.monthly_income) }}</strong></div>
      </div>
      <div class="wallet-footnote">
        <span>平台服务费 0.1%</span>
        <span>本月累计 ¥{{ money(summary.monthly_platform_fee) }}</span>
      </div>
      <div v-if="summaryLoading" class="summary-loading">正在更新经营数据…</div>
    </section>

    <div class="verify-tool">
      <div class="verify-copy">
        <strong>取货核销</strong>
        <span>输入学生出示的 6 位取货码</span>
      </div>
      <div class="verify-form">
        <input class="input vinput" v-model.trim="code" inputmode="numeric" maxlength="6" autocomplete="one-time-code" aria-label="6位取货码" placeholder="000000" @keyup.enter="doVerify" />
        <button class="btn btn-primary btn-sm" @click="doVerify" :disabled="verifying">{{ verifying ? '核销中…' : '确认核销' }}</button>
      </div>
    </div>

    <div class="list-heading">
      <div><strong>订单记录</strong><span>查看领取与结算进度</span></div>
    </div>
    <div class="tabs order-tabs" role="tablist" aria-label="订单状态">
      <button v-for="t in tabs" :key="t.label" class="tab" :class="{ active: status === t.status }" @click="status = t.status; load()">{{ t.label }}</button>
    </div>

    <div v-if="loading" class="empty">加载中…</div>
    <div v-else-if="!orders.length" class="empty"><div class="big">🧾</div>暂无订单</div>

    <div v-for="o in orders" :key="o.id" class="card oder">
      <div class="o-top">
        <span class="order-number">订单号 {{ orderNumber(o) }}</span>
        <span class="status-badge" :class="statusClass(o.status)">{{ statusText(o) }}</span>
      </div>
      <div class="o-main">
        <div class="order-thumb">
          <img v-if="o.product_image" :src="o.product_image" :alt="o.product_title" />
          <span v-else>食愿</span>
        </div>
        <div class="o-content">
          <strong class="product-title">{{ o.product_title }}</strong>
          <div class="o-stud"><span>取货学生</span>{{ o.student_name }}（{{ o.student_id }}）</div>
          <div class="o-stud"><span>联系方式</span>{{ o.phone }}</div>
          <div class="o-info"><span class="price">¥{{ orderTotal(o) }}</span><small>{{ o.quantity }} 份 · {{ o.created_at }}</small></div>
        </div>
      </div>
      <div v-if="o.status === 0" class="settlement-panel pending">
        <div class="settlement-head"><span>平台托管中</span><strong>{{ countdownText(o) }}</strong></div>
        <div>请在 {{ o.business_close_time || '22:00' }} 关门前核销 · 到时系统自动完成</div>
        <div>完成后：平台服务费 ¥{{ o.platform_fee }}（{{ o.platform_fee_rate }}） · 商家到账 ¥{{ o.merchant_receivable }}</div>
      </div>
      <div v-else-if="o.status === 1" class="settlement-panel settled">
        <div class="settlement-head"><span>已结算给商家</span><strong>¥{{ o.merchant_receivable }}</strong></div>
        <div>{{ completionText(o) }} · 平台服务费 ¥{{ o.platform_fee }} · {{ o.settled_at }}</div>
      </div>
      <div class="o-foot">
        <span class="code">取货码：<b>{{ o.pickup_code || '—' }}</b></span>
        <button v-if="o.status === 0" class="btn btn-primary btn-sm" @click="pickup(o)">核销领取</button>
        <span v-else-if="o.status === 1" class="picked">{{ completionText(o) }}</span>
      </div>
    </div>

    <WalletActionDialog
      :open="walletDialogOpen"
      :action="walletAction"
      :balance="summary.available_balance"
      :loading="walletSubmitting"
      @close="walletDialogOpen = false"
      @submit="submitWalletAction"
    />
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'
import { getOrders, getOrderSummary, pickupOrder, rechargeWallet, verifyOrder, withdrawWallet } from '../../api/order'
import WalletActionDialog from '../../components/WalletActionDialog.vue'
import { toast } from '../../utils/toast'
import { completionText, orderTotal, useOrderCountdown } from '../../utils/orderCountdown'

const tabs = [{ label: '全部', status: null }, { label: '待领取', status: 0 }, { label: '已完成', status: 1 }]
const status = ref(null)
const orders = ref([])
const loading = ref(false)
const summaryLoading = ref(false)
const walletDialogOpen = ref(false)
const walletAction = ref('withdraw')
const walletSubmitting = ref(false)
const summary = ref({
  available_balance: '0.00',
  escrow_amount: '0.00',
  monthly_sales: '0.00',
  monthly_income: '0.00',
  monthly_platform_fee: '0.00',
  monthly_order_count: 0,
  monthly_item_count: 0,
  monthly_completed_count: 0
})
const code = ref('')
const verifying = ref(false)
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
async function pickup(o) {
  try {
    const settled = await pickupOrder(o.id)
    toast(`核销成功，已结算 ¥${settled.merchant_receivable}`)
    load()
  }
  catch (e) { /* 拦截器 */ }
}
async function doVerify() {
  if (!/^\d{6}$/.test(code.value)) { toast('请输入6位取货码', 'error'); return }
  verifying.value = true
  try { const o = await verifyOrder(code.value); toast(`核销成功，已结算 ¥${o.merchant_receivable}`); code.value = ''; status.value = null; load() }
  catch (e) { /* 拦截器 */ } finally { verifying.value = false }
}
function statusText(order) {
  if (order.status === 1) return order.completion_type === 'auto_timeout' ? '超时自动完成' : '已领取'
  return ({ 0: '待领取', 2: '已关闭' }[order.status] || '')
}
function statusClass(s) { return ({ 0: 'st-pending', 1: 'st-picked' }[s] || '') }
function money(value) { return Number(value || 0).toFixed(2) }
function orderNumber(order) { return `FL${String(order.id).padStart(6, '0')}` }

function openWallet(action) {
  walletAction.value = action
  walletDialogOpen.value = true
}

async function submitWalletAction(payload) {
  walletSubmitting.value = true
  try {
    const result = walletAction.value === 'withdraw'
      ? await withdrawWallet(payload)
      : await rechargeWallet(payload)
    summary.value.available_balance = result.available_balance
    walletDialogOpen.value = false
    toast(`${walletAction.value === 'withdraw' ? '提现' : '充值'}成功，当前余额 ¥${result.available_balance}`)
  } catch (e) { /* 请求拦截器统一提示 */ } finally { walletSubmitting.value = false }
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
.merchant-orders-page { --ink: #17211c; --mint: #79d19d; }
.page-heading { display: flex; align-items: center; gap: 12px; margin-bottom: 18px; }
.page-heading p { margin: 0 0 2px; color: #8a938e; font-size: 10px; font-weight: 700; letter-spacing: 0; }
.page-title { margin: 0; font-size: 25px; line-height: 1.2; }
.back-button { width: 36px; height: 36px; flex: 0 0 36px; border: 1px solid var(--border); border-radius: 8px; background: #fff; color: var(--text); font-size: 18px; cursor: pointer; }
.back-button:hover { border-color: #b8c1bc; background: #f9faf9; }
.merchant-wallet { position: relative; overflow: hidden; margin-bottom: 18px; border-radius: 8px; background: var(--ink); color: #fff; box-shadow: 0 16px 34px rgba(23, 33, 28, .17); }
.merchant-wallet::before { content: ''; position: absolute; right: -32px; top: -62px; width: 180px; height: 180px; border: 34px solid rgba(255,255,255,.035); border-radius: 50%; pointer-events: none; }
.wallet-main { position: relative; z-index: 1; display: grid; grid-template-columns: 1.25fr .75fr; gap: 20px; padding: 22px; }
.wallet-label { display: inline-flex; align-items: center; gap: 7px; color: #dce5e0; font-size: 13px; font-weight: 600; }
.wallet-label i { width: 7px; height: 7px; border-radius: 50%; background: var(--mint); box-shadow: 0 0 0 4px rgba(121, 209, 157, .12); }
.balance { display: flex; align-items: flex-start; gap: 5px; margin-top: 12px; font-variant-numeric: tabular-nums; }
.balance small { margin-top: 8px; color: #b7c4bd; font-size: 15px; }
.balance strong { font-size: 36px; line-height: 1; }
.balance-block p { margin: 7px 0 0; color: #94a39b; font-size: 12px; }
.wallet-actions { display: flex; gap: 7px; margin-top: 15px; }
.wallet-actions button { display: inline-flex; min-width: 72px; height: 32px; align-items: center; justify-content: center; gap: 4px; padding: 0 10px; border: 1px solid rgba(255,255,255,.18); border-radius: 7px; background: rgba(255,255,255,.08); color: #f6faf7; font-size: 11px; font-weight: 700; cursor: pointer; }
.wallet-actions button:first-child { border-color: var(--mint); background: var(--mint); color: #173221; }
.wallet-actions button:hover { background: rgba(255,255,255,.14); }
.wallet-actions button:first-child:hover { background: #8bdbaa; }
.wallet-actions button span { font-size: 14px; line-height: 1; }
.sales-block { align-self: end; padding-left: 20px; border-left: 1px solid rgba(255,255,255,.12); }
.sales-block span, .sales-block small { display: block; color: #94a39b; font-size: 11px; }
.sales-block strong { display: block; margin: 6px 0 4px; color: #fff3dc; font-size: 22px; font-variant-numeric: tabular-nums; }
.business-grid { position: relative; z-index: 1; display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); border-top: 1px solid rgba(255,255,255,.1); border-bottom: 1px solid rgba(255,255,255,.1); background: rgba(255,255,255,.025); }
.business-grid > div { min-width: 0; padding: 14px 16px; border-right: 1px solid rgba(255,255,255,.09); }
.business-grid > div:last-child { border-right: 0; }
.business-grid span { display: block; color: #94a39b; font-size: 10px; }
.business-grid strong { display: block; margin-top: 5px; overflow-wrap: anywhere; font-size: 15px; font-variant-numeric: tabular-nums; }
.business-grid small { color: #aab7b0; font-size: 10px; }
.wallet-footnote { display: flex; justify-content: space-between; gap: 16px; padding: 10px 22px; color: #839188; font-size: 10px; }
.summary-loading { position: absolute; right: 22px; top: 8px; color: #78877f; font-size: 10px; }
.verify-tool { display: flex; align-items: center; justify-content: space-between; gap: 18px; margin-bottom: 26px; padding: 15px 16px; border: 1px solid #dfe4e1; border-radius: 8px; background: #fff; }
.verify-copy strong, .verify-copy span { display: block; }
.verify-copy strong { font-size: 14px; }
.verify-copy span { margin-top: 2px; color: var(--muted); font-size: 11px; }
.verify-form { display: flex; align-items: center; gap: 8px; }
.vinput { width: 142px; height: 36px; padding: 7px 10px; font-weight: 700; font-variant-numeric: tabular-nums; text-align: center; }
.list-heading { display: flex; justify-content: space-between; margin-bottom: 12px; }
.list-heading strong, .list-heading span { display: block; }
.list-heading strong { font-size: 17px; }
.list-heading span { margin-top: 2px; color: var(--muted); font-size: 11px; }
.order-tabs { width: max-content; max-width: 100%; gap: 2px; padding: 3px; border: 1px solid var(--border); border-radius: 8px; background: #fff; }
.order-tabs .tab { min-width: 76px; padding: 7px 12px; border: 0; border-radius: 6px; background: transparent; }
.order-tabs .tab.active { background: var(--ink); color: #fff; }
.oder { overflow: hidden; padding: 17px; border-color: #e0e5e2; border-radius: 8px; box-shadow: 0 7px 20px rgba(31, 41, 55, .045); transition: border-color .16s, box-shadow .16s, transform .16s; }
.oder:hover { border-color: #cfd8d2; box-shadow: 0 12px 28px rgba(31, 41, 55, .08); transform: translateY(-1px); }
.o-top { display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; }
.order-number { color: #98a09b; font-size: 9px; font-variant-numeric: tabular-nums; }
.status-badge { padding: 3px 8px; border-radius: 6px; background: #f4f5f4; font-size: 11px; font-weight: 700; }
.status-badge.st-pending { background: #fff4df; }
.status-badge.st-picked { background: #dff2e7; }
.o-main { display: flex; gap: 15px; }
.order-thumb { width: 94px; height: 94px; flex: 0 0 94px; overflow: hidden; display: flex; align-items: center; justify-content: center; border-radius: 8px; background: #edf0ee; color: #8a938e; font-size: 12px; font-weight: 700; }
.order-thumb img { width: 100%; height: 100%; object-fit: cover; }
.o-content { min-width: 0; flex: 1; }
.product-title { display: block; margin-bottom: 7px; overflow-wrap: anywhere; font-size: 16px; }
.o-stud { display: grid; grid-template-columns: 58px minmax(0, 1fr); margin-top: 4px; color: #59635d; font-size: 11px; }
.o-stud span { color: #9aa29d; }
.o-info { display: flex; align-items: baseline; gap: 9px; margin-top: 7px; font-size: 13px; }
.o-info small { min-width: 0; overflow-wrap: anywhere; color: var(--muted); font-size: 10px; }
.settlement-panel { margin-top: 10px; padding: 10px 12px; border-left: 3px solid; border-radius: 0 6px 6px 0; font-size: 12px; line-height: 1.7; }
.settlement-panel.pending { border-color: var(--warn); background: #fffbeb; color: #92400e; }
.settlement-panel.settled { border-color: var(--success); background: #f0fdf4; color: #166534; }
.settlement-head { display: flex; align-items: center; justify-content: space-between; gap: 12px; font-weight: 700; }
.settlement-head strong { font-size: 18px; font-variant-numeric: tabular-nums; }
.code { color: var(--text); font-size: 14px; }
.o-foot { display: flex; justify-content: space-between; align-items: center; margin-top: 10px; padding-top: 8px; border-top: 1px dashed var(--border); }
.picked { color: var(--success); font-size: 12px; }
@media (max-width: 600px) {
  .merchant-orders-page { width: 100%; max-width: 100%; }
  .wallet-main { grid-template-columns: 1fr; padding: 18px; }
  .balance strong { font-size: 31px; }
  .sales-block { padding: 13px 0 0; border-top: 1px solid rgba(255,255,255,.1); border-left: 0; }
  .business-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .business-grid > div:nth-child(2) { border-right: 0; }
  .business-grid > div:nth-child(-n+2) { border-bottom: 1px solid rgba(255,255,255,.09); }
  .verify-tool { align-items: stretch; flex-direction: column; gap: 12px; }
  .verify-form { width: 100%; }
  .vinput { flex: 1 1 0; width: 0; min-width: 0; }
  .verify-form .btn { flex: 0 0 auto; }
  .order-tabs { width: 100%; }
  .order-tabs .tab { flex: 1; min-width: 0; }
  .order-thumb { width: 82px; height: 82px; flex-basis: 82px; }
  .product-title { font-size: 14px; }
  .o-stud { grid-template-columns: 53px minmax(0, 1fr); font-size: 10px; }
  .o-info { align-items: flex-start; flex-direction: column; gap: 2px; }
}
</style>
