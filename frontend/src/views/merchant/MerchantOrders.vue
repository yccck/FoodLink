<template>
  <div class="merchant-orders-page">
    <div v-if="!embedded" class="page-heading">
      <div>
        <p>MERCHANT CENTER</p>
        <h2 class="page-title">订单管理</h2>
      </div>
    </div>

    <section class="merchant-overview" aria-label="本月经营概览">
      <div class="overview-main">
        <div class="sales-total">
          <span class="overview-label"><i></i>本月经营概览</span>
          <div class="sales-value"><small>¥</small><strong>{{ money(summary.monthly_sales) }}</strong></div>
          <p>本月销售额</p>
        </div>
        <div class="order-snapshot">
          <span>本月订单</span>
          <strong>{{ summary.monthly_order_count }}<small> 笔</small></strong>
          <p>按自然月统计</p>
        </div>
      </div>
      <div class="business-grid">
        <div><span>本月订单</span><strong>{{ summary.monthly_order_count }}<small> 笔</small></strong></div>
        <div><span>本月销量</span><strong>{{ summary.monthly_item_count }}<small> 份</small></strong></div>
        <div><span>本月已完成</span><strong>{{ summary.monthly_completed_count }}<small> 笔</small></strong></div>
        <div><span>本月净收入</span><strong>¥{{ money(summary.monthly_income) }}</strong></div>
      </div>
      <div class="overview-footnote">
        <span>平台服务费 0.1%</span>
        <span>本月累计 ¥{{ money(summary.monthly_platform_fee) }}</span>
      </div>
      <div v-if="summaryLoading" class="summary-loading">正在更新经营数据…</div>
    </section>

    <div class="list-heading">
      <div><strong>订单记录</strong><span>查看领取状态与收入记录</span></div>
    </div>
    <div class="tabs order-tabs" role="tablist" aria-label="订单状态">
      <button v-for="t in tabs" :key="t.label" class="tab" :class="{ active: status === t.status }" @click="status = t.status; load()">{{ t.label }}</button>
    </div>

    <div class="order-toolbar" aria-label="订单筛选">
      <label class="search-box">
        <span aria-hidden="true">⌕</span>
        <input v-model.trim="searchKeyword" type="search" placeholder="搜索商品名称" aria-label="搜索商品名称" />
        <button v-if="searchKeyword" type="button" class="clear-search" aria-label="清除搜索" @click="searchKeyword = ''">×</button>
      </label>
      <select v-model="productFilter" class="input product-filter" aria-label="按商品筛选">
        <option value="">全部商品</option>
        <option v-for="option in productOptions" :key="option.key" :value="option.key">{{ option.title }}</option>
      </select>
    </div>
    <p v-if="orders.length" class="filter-result">显示 {{ orderGroups.length }} 个商品 · {{ filteredOrders.length }} 笔订单</p>

    <div v-if="loading" class="empty">加载中…</div>
    <div v-else-if="!orderGroups.length" class="empty"><div class="big">🧾</div>{{ orders.length ? '没有匹配订单' : '暂无订单' }}</div>

    <div v-else class="order-groups">
      <section v-for="group in orderGroups" :key="group.key" class="order-group">
        <button type="button" class="group-summary" :aria-expanded="isGroupExpanded(group.key)" @click="toggleGroup(group.key)">
          <span class="group-thumb">
            <img v-if="group.image" :src="group.image" :alt="group.title" />
            <span v-else>食愿</span>
          </span>
          <span class="group-copy">
            <strong>{{ group.title }}</strong>
            <small>{{ group.totalQuantity }} 份 · {{ group.orders.length }} 笔订单</small>
          </span>
          <span class="group-total">¥{{ money(group.totalAmount) }}<small>{{ isGroupExpanded(group.key) ? '收起详情' : '展开详情' }}</small></span>
          <span class="group-chevron" :class="{ open: isGroupExpanded(group.key) }" aria-hidden="true">⌄</span>
        </button>

        <div v-if="isGroupExpanded(group.key)" class="group-details">
          <div class="order-grid">
            <article v-for="o in group.orders" :key="o.id" class="card order-card">
              <div class="o-top">
                <span class="order-number">订单号 {{ orderNumber(o) }}</span>
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
                  <div v-if="o.status === 0" class="pickup-code"><span>核销码</span><strong>{{ o.pickup_code }}</strong></div>
                  <div class="o-info"><span class="price">¥{{ orderTotal(o) }}</span><small>{{ o.quantity }} 份 · {{ o.created_at }}</small></div>
                </div>
              </div>
              <div v-if="o.status === 0" class="settlement-panel pending">
                <div class="settlement-head">
                  <span>学生已支付，等待领取</span>
                  <div class="settlement-action">
                    <button
                      class="confirm-pickup-button"
                      type="button"
                      :disabled="confirmingId !== null"
                      @click="confirmPickup(o)"
                    >{{ confirmingId === o.id ? '确认中…' : '确认领取' }}</button>
                  </div>
                </div>
                <div>领取截止：{{ o.pickup_deadline || '以订单详情为准' }}</div>
                <div class="payout-note">订单完成后，收入实时记账，微信次日自动到账</div>
              </div>
              <div v-else-if="o.status === 1" class="settlement-panel settled">
                <div class="settlement-head"><span>收入已实时记账</span><strong>{{ statusText(o) }}</strong></div>
                <div>{{ completionText(o) }} · {{ payoutAtText(o) }}</div>
              </div>
              <div v-else class="settlement-panel closed">
                <div v-if="isRefunded(o)" class="settlement-head"><span>{{ o.close_reason === 'student_refund' ? '学生在 5 分钟内取消' : '食品问题审核通过' }}</span><strong>已退款</strong></div>
                <div v-else class="settlement-head"><span>超过食品领取期限未取</span><strong>订单已关闭</strong></div>
                <div v-if="o.close_reason === 'student_refund'">库存已恢复，款项已原路退回学生</div>
                <div v-else-if="o.close_reason === 'admin_refund'">管理员已执行原路退款，收入记录已冲回</div>
                <div v-else>收入已实时记账 · {{ payoutAtText(o) }}</div>
              </div>
              <div class="o-foot">
                <span class="student-status">{{ orderHandlingText(o) }}</span>
                <span v-if="o.status === 1" class="picked">{{ completionText(o) }}</span>
                <span v-else-if="o.status === 2" class="closed-label">{{ statusText(o) }}</span>
              </div>
            </article>
          </div>
        </div>
      </section>
    </div>
  </div>
</template>

<script setup>
import { computed, ref, watch } from 'vue'
import { getOrders, getOrderSummary, pickupOrder } from '../../api/order'
import { completionText, orderTotal, useOrderCountdown } from '../../utils/orderCountdown'
import { toast } from '../../utils/toast'

const props = defineProps({ embedded: { type: Boolean, default: false } })

const tabs = [{ label: '全部', status: null }, { label: '待领取', status: 0 }, { label: '已完成', status: 1 }, { label: '已关闭', status: 2 }]
const status = ref(null)
const orders = ref([])
const loading = ref(false)
const summaryLoading = ref(false)
const summary = ref({
  monthly_sales: '0.00',
  monthly_income: '0.00',
  monthly_platform_fee: '0.00',
  monthly_order_count: 0,
  monthly_item_count: 0,
  monthly_completed_count: 0
})
const searchKeyword = ref('')
const productFilter = ref('')
const expandedGroups = ref({})
const confirmingId = ref(null)
const { now, remainingSeconds } = useOrderCountdown()
let lastOverdueRefresh = 0

const productOptions = computed(() => {
  const options = new Map()
  orders.value.forEach((order) => {
    const key = String(order.product_id || order.product_title || order.id)
    if (!options.has(key)) options.set(key, { key, title: order.product_title || '商品' })
  })
  return [...options.values()].sort((a, b) => a.title.localeCompare(b.title, 'zh-CN'))
})

const filteredOrders = computed(() => {
  const keyword = searchKeyword.value.toLowerCase()
  return orders.value.filter((order) => {
    const key = String(order.product_id || order.product_title || order.id)
    const matchesProduct = !productFilter.value || key === productFilter.value
    const matchesKeyword = !keyword || String(order.product_title || '').toLowerCase().includes(keyword)
    return matchesProduct && matchesKeyword
  })
})

const orderGroups = computed(() => {
  const groups = new Map()
  filteredOrders.value.forEach((order) => {
    const key = String(order.product_id || order.product_title || order.id)
    if (!groups.has(key)) {
      groups.set(key, {
        key,
        title: order.product_title || '商品',
        image: order.product_image || '',
        orders: [],
        totalQuantity: 0,
        totalAmount: 0
      })
    }
    const group = groups.get(key)
    group.orders.push(order)
    group.totalQuantity += Number(order.quantity || 0)
    group.totalAmount += Number(orderTotal(order))
  })
  return [...groups.values()]
})

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
function toggleGroup(key) {
  expandedGroups.value = { ...expandedGroups.value, [key]: !isGroupExpanded(key) }
}
function isGroupExpanded(key) { return expandedGroups.value[key] === true }
async function confirmPickup(order) {
  if (confirmingId.value !== null) return
  const confirmed = window.confirm(`确认 ${order.student_name || '该学生'} 已领取“${order.product_title || '商品'}”吗？`)
  if (!confirmed) return
  confirmingId.value = order.id
  try {
    await pickupOrder(order.id)
    toast('已确认领取')
    await load(true)
  } catch (e) { /* 请求拦截器统一提示 */ } finally {
    confirmingId.value = null
  }
}
function statusText(order) {
  if (order.status === 1) return order.completion_type === 'auto_timeout' ? '超时自动完成' : '已领取'
  if (order.status === 2) return isRefunded(order) ? '已退款' : '已过期'
  return ({ 0: '待领取' }[order.status] || '')
}
function isRefunded(order) { return ['student_refund', 'admin_refund'].includes(order?.close_reason) }
function money(value) { return Number(value || 0).toFixed(2) }
function orderNumber(order) { return `FL${String(order.id).padStart(6, '0')}` }
function payoutAtText(order) {
  if (order.merchant_payout_at) {
    return order.merchant_payout_status === 'paid'
      ? `已于 ${order.merchant_payout_at} 自动到账`
      : `预计 ${order.merchant_payout_at} 自动到账`
  }
  const source = order.settled_at || order.closed_at
  if (!source) return '微信支付次日自动到账'
  const date = new Date(String(source).replace(' ', 'T'))
  if (Number.isNaN(date.getTime())) return '微信支付次日自动到账'
  date.setDate(date.getDate() + 1)
  const pad = (value) => String(value).padStart(2, '0')
  return `预计 ${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())} ${pad(date.getHours())}:${pad(date.getMinutes())} 自动到账`
}
function orderHandlingText(order) {
  if (order.status === 0) return '学生凭取货凭证领取'
  if (order.status === 1) return '无需商家手动输入核销码'
  return '订单已结束'
}

watch(orderGroups, (groups) => {
  const next = { ...expandedGroups.value }
  groups.forEach((group, index) => {
    if (!(group.key in next)) next[group.key] = index === 0
  })
  expandedGroups.value = next
}, { immediate: true })

watch(now, () => {
  const hasOverdue = orders.value.some(order => order.status === 0 && remainingSeconds(order) === 0)
  if (!hasOverdue || Date.now() - lastOverdueRefresh < 5000) return
  lastOverdueRefresh = Date.now()
  load(true)
})

load()
</script>

<style scoped>
.merchant-orders-page { --ink: #17211c; --mint: #79d19d; --panel-border: transparent; --panel-border-strong: transparent; }
.page-heading { display: flex; align-items: center; gap: 12px; margin-bottom: 18px; }
.page-heading p { margin: 0 0 2px; color: #8a938e; font-size: 10px; font-weight: 700; letter-spacing: 0; }
.page-title { margin: 0; font-size: 25px; line-height: 1.2; }
.merchant-overview { position: relative; overflow: hidden; margin-bottom: 18px; border: 1px solid var(--panel-border-strong); border-radius: 8px; background: linear-gradient(135deg, #ffe2b5 0%, #f5e4c3 48%, #d5e9d3 100%); color: #2e3a34; box-shadow: 0 14px 34px rgba(93, 68, 39, .08); }
.overview-main { position: relative; z-index: 1; display: grid; grid-template-columns: 1.25fr .75fr; gap: 20px; padding: 22px; }
.overview-label { display: inline-flex; align-items: center; gap: 7px; color: #6d715f; font-size: 13px; font-weight: 700; }
.overview-label i { width: 7px; height: 7px; border-radius: 50%; background: #31915d; box-shadow: 0 0 0 4px rgba(49, 145, 93, .12); }
.sales-value { display: flex; align-items: flex-start; gap: 5px; margin-top: 12px; font-variant-numeric: tabular-nums; }
.sales-value small { margin-top: 8px; color: #9b6735; font-size: 15px; }
.sales-value strong { font-size: 36px; line-height: 1; }
.sales-total p { margin: 7px 0 0; color: #776f63; font-size: 12px; }
.order-snapshot { align-self: end; padding-left: 20px; border-left: 1px solid rgba(78, 113, 71, .18); }
.order-snapshot span, .order-snapshot p { display: block; margin: 0; color: #6c786e; font-size: 11px; }
.order-snapshot strong { display: block; margin: 6px 0 4px; color: #2e3a34; font-size: 22px; font-variant-numeric: tabular-nums; }
.order-snapshot small { font-size: 11px; }
.business-grid { position: relative; z-index: 1; display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); border-top: 1px solid rgba(78, 113, 71, .14); border-bottom: 1px solid rgba(78, 113, 71, .14); background: rgba(255,255,255,.42); }
.business-grid > div { min-width: 0; padding: 14px 16px; border-right: 1px solid rgba(78, 113, 71, .13); }
.business-grid > div:last-child { border-right: 0; }
.business-grid span { display: block; color: #74786c; font-size: 10px; }
.business-grid strong { display: block; margin-top: 5px; overflow-wrap: anywhere; color: #2e3a34; font-size: 15px; font-variant-numeric: tabular-nums; }
.business-grid small { color: #778178; font-size: 10px; }
.overview-footnote { display: flex; justify-content: space-between; gap: 16px; padding: 10px 22px; color: #74786c; font-size: 10px; }
.summary-loading { position: absolute; right: 22px; top: 8px; color: #74786c; font-size: 10px; }
.list-heading { display: flex; justify-content: space-between; margin-bottom: 12px; }
.list-heading strong, .list-heading span { display: block; }
.list-heading strong { font-size: 23px; }
.list-heading span { margin-top: 2px; color: var(--muted); font-size: 11px; }
.order-tabs { width: max-content; max-width: 100%; gap: 2px; padding: 3px; border: 1px solid var(--panel-border); border-radius: 8px; background: #fff; }
.order-tabs .tab { min-width: 76px; padding: 7px 12px; border: 0; border-radius: 6px; background: transparent; }
.order-tabs .tab.active { background: var(--ink); color: #fff; }
.order-toolbar { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); align-items: center; gap: 10px; margin: 12px 0 6px; }
.search-box { position: relative; display: flex; width: 100%; min-width: 0; align-items: center; height: 40px; border: 1px solid var(--panel-border); border-radius: 7px; background: #fff; color: #8b958f; }
.search-box > span { padding-left: 12px; font-size: 20px; line-height: 1; transform: translateY(-1px); }
.search-box input { min-width: 0; flex: 1; height: 100%; padding: 0 10px; border: 0; outline: 0; background: transparent; font-size: 13px; }
.search-box:focus-within { border-color: var(--primary); box-shadow: 0 0 0 3px rgba(234, 111, 29, .1); }
.clear-search { width: 30px; height: 30px; margin-right: 4px; border: 0; border-radius: 5px; background: transparent; color: #89938d; font-size: 20px; line-height: 1; cursor: pointer; }
.clear-search:hover { background: #f3f5f4; color: var(--text); }
.product-filter { width: 100%; min-width: 0; height: 40px; border-color: var(--panel-border); }
.filter-result { margin: 0 0 10px; color: #8c9690; font-size: 11px; }
.order-groups { display: grid; gap: 12px; }
.order-group { overflow: hidden; border: 1px solid var(--panel-border-strong); border-radius: 8px; background: #fff; box-shadow: 0 5px 16px rgba(31, 41, 55, .035); }
.group-summary { display: grid; width: 100%; grid-template-columns: 56px minmax(0, 1fr) auto 22px; align-items: center; gap: 12px; padding: 12px 14px; border: 0; background: #fff; color: var(--text); text-align: left; cursor: pointer; }
.group-summary:hover { background: #fcfdfc; }
.group-summary:focus-visible { outline: 3px solid rgba(249, 115, 22, .18); outline-offset: -3px; }
.group-thumb { width: 56px; height: 56px; overflow: hidden; display: flex; align-items: center; justify-content: center; border-radius: 7px; background: #edf0ee; color: #8a938e; font-size: 11px; font-weight: 700; }
.group-thumb img { width: 100%; height: 100%; object-fit: cover; }
.group-copy { min-width: 0; }
.group-copy strong, .group-copy small, .group-total small { display: block; }
.group-copy strong { overflow: hidden; font-size: 14px; text-overflow: ellipsis; white-space: nowrap; }
.group-copy small { margin-top: 4px; color: var(--muted); font-size: 11px; }
.group-total { min-width: 82px; color: var(--primary-dark); font-size: 15px; font-weight: 750; text-align: right; font-variant-numeric: tabular-nums; }
.group-total small { margin-top: 3px; color: #9aa29d; font-size: 10px; font-weight: 500; }
.group-chevron { color: #8a938e; font-size: 19px; line-height: 1; transition: transform .16s ease; }
.group-chevron.open { transform: rotate(180deg); }
.group-details { padding: 0 12px 12px; border-top: 1px solid #edf0ee; background: #fbfcfb; }
.group-details .order-grid { padding-top: 12px; }
.order-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 16px; }
.order-card { overflow: hidden; padding: 17px; border-color: var(--panel-border); border-radius: 8px; box-shadow: 0 7px 20px rgba(31, 41, 55, .045); transition: border-color .16s, box-shadow .16s, transform .16s; }
.order-card:hover { border-color: #cfd8d2; box-shadow: 0 12px 28px rgba(31, 41, 55, .08); transform: translateY(-1px); }
.o-top { display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; }
.order-number { color: #98a09b; font-size: 9px; font-variant-numeric: tabular-nums; }
.confirm-pickup-button { min-width: 76px; min-height: 29px; padding: 4px 10px; border: 1px solid #e9a47f; border-radius: 6px; background: #fff0e6; color: #a84d25; font-size: 13px; font-weight: 700; cursor: pointer; }
.confirm-pickup-button:hover { border-color: #df8a5e; background: #ffe4d5; }
.confirm-pickup-button:focus-visible { outline: 3px solid rgba(233, 121, 80, .2); outline-offset: 2px; }
.confirm-pickup-button:disabled { opacity: .6; cursor: wait; }
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
.settlement-panel.closed { border-color: #94a3b8; background: #f8fafc; color: #536170; }
.settlement-head { display: flex; align-items: flex-start; justify-content: space-between; gap: 12px; font-weight: 700; }
.settlement-head strong { font-size: 13px; font-variant-numeric: tabular-nums; }
.settlement-action { display: flex; flex: 0 0 auto; flex-direction: column; align-items: flex-end; gap: 5px; }
.pickup-code { display: flex; align-items: center; gap: 8px; margin-top: 7px; }
.pickup-code span { color: #9aa29d; font-size: 11px; }
.pickup-code strong { padding: 2px 7px; border: 1px solid #fed7aa; border-radius: 5px; background: #fff7ed; color: var(--primary-dark); font-size: 14px; letter-spacing: 0; font-variant-numeric: tabular-nums; }
.o-foot { display: flex; justify-content: space-between; align-items: center; margin-top: 10px; padding-top: 8px; border-top: 1px dashed var(--border); }
.student-status { color: #7d8981; font-size: 11px; }
.payout-note { margin-top: 3px; color: #8a6b27; font-size: 11px; }
.picked { color: var(--success); font-size: 12px; }
.closed-label { color: #64748b; font-size: 12px; font-weight: 650; }
@media (max-width: 600px) {
  .merchant-orders-page { width: 100%; max-width: 100%; }
  .order-grid { grid-template-columns: 1fr; }
  .overview-main { grid-template-columns: 1fr; padding: 18px; }
  .sales-value strong { font-size: 31px; }
  .order-snapshot { padding: 13px 0 0; border-top: 1px solid rgba(78, 113, 71, .18); border-left: 0; }
  .business-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .business-grid > div:nth-child(2) { border-right: 0; }
  .business-grid > div:nth-child(-n+2) { border-bottom: 1px solid rgba(78, 113, 71, .13); }
  .order-toolbar { grid-template-columns: 1fr; align-items: stretch; }
  .product-filter { width: 100%; }
  .order-tabs { width: 100%; }
  .order-tabs .tab { flex: 1; min-width: 0; }
  .order-thumb { width: 82px; height: 82px; flex-basis: 82px; }
  .product-title { font-size: 14px; }
  .o-stud { grid-template-columns: 53px minmax(0, 1fr); font-size: 10px; }
  .o-info { align-items: flex-start; flex-direction: column; gap: 2px; }
  .group-summary { grid-template-columns: 48px minmax(0, 1fr) auto 18px; gap: 9px; padding-inline: 10px; }
  .group-thumb { width: 48px; height: 48px; }
  .group-total { min-width: 66px; font-size: 13px; }
  .group-copy strong { font-size: 13px; }
  .group-details { padding-inline: 8px; }
}
</style>
