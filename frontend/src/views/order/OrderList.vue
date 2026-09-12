<template>
  <div class="orders-page">
    <div class="section-heading">
      <div class="section-heading-row">
        <span class="section-title">订单记录</span>
        <div class="inline-summary" aria-label="本月订单概览" :aria-busy="summaryLoading">
          <span class="summary-stat">
            <em>本月消费</em>
            <strong>¥{{ money(summary.monthly_spending) }}</strong>
          </span>
          <span class="summary-stat">
            <em>本月订单</em>
            <strong>{{ summary.monthly_order_count }}<small> 笔</small></strong>
          </span>
        </div>
      </div>
    </div>

    <div class="tabs order-tabs" role="tablist" aria-label="订单状态">
      <button v-for="t in tabs" :key="t.label" class="tab" :class="{ active: status === t.status }"
        @click="changeTab(t.status)">{{ t.label }}</button>
    </div>

    <div v-if="loading" class="empty">加载中…</div>
    <div v-else-if="!orders.length" class="empty"><div class="big">🛒</div>暂无{{ currentLabel }}订单</div>

    <div v-else class="order-grid">
    <div v-for="o in orders" :key="o.id" class="card order-card">
      <div class="order-top">
        <div class="shop-block">
          <span class="shop">{{ o.shop_name }}</span>
          <small>订单号 {{ orderNumber(o) }}</small>
        </div>
        <span class="status-badge" :class="statusClass(o)">{{ statusText(o) }}</span>
      </div>
      <div class="order-body">
        <div class="thumb"><template v-if="o.product_image"><img :src="o.product_image" :alt="o.product_title" /></template><span v-else>食愿</span></div>
        <div class="order-info">
          <div class="title">{{ o.product_title }}</div>
          <div class="item-price">¥{{ money(o.price) }} <span>× {{ o.quantity }} 份</span></div>
          <div class="meta"><span>下单时间</span>{{ o.created_at }}</div>
          <div class="meta"><span>取货地点</span>{{ o.location }}</div>
          <div class="meta"><span>营业时间</span>{{ businessHoursText(o) }}</div>
        </div>
      </div>
      <div class="payment-state">
        <span :class="{ refunded: o.payment_status === 'refunded' }"><i></i>{{ paymentText(o) }}</span>
        <small v-if="o.status === 0 && canRefund(o)">付款后 {{ refundCountdownText(o) }} 内可取消，之后商品将为你保留</small>
        <small v-else-if="o.status === 0">商品已为你保留，请在领取时间内到店取货</small>
        <small v-else-if="o.status === 1 && o.completion_type === 'auto_timeout'">未在领取时间内取货，本单已结束</small>
        <small v-else-if="o.status === 1">已领取 · {{ o.settled_at }}</small>
        <small v-else-if="o.close_reason === 'product_expired'">本单未领取，领取时间已结束</small>
        <small v-else-if="o.close_reason === 'student_refund'">款项已原路退回</small>
        <small v-else-if="o.close_reason === 'admin_refund'">食品问题审核通过，款项已原路退回</small>
      </div>
      <div v-if="refundRequestFor(o)" class="after-sale-state" :class="`review-${refundRequestFor(o).status}`">
        <strong>{{ refundRequestText(refundRequestFor(o)) }}</strong>
        <span>{{ refundRequestDetail(refundRequestFor(o)) }}</span>
      </div>
      <div class="amount-bar" aria-label="订单金额">
        <div>
          <span>订单金额</span>
          <small>{{ o.quantity }} 份 · {{ paymentText(o) }}</small>
        </div>
        <strong>¥{{ orderTotal(o) }}</strong>
      </div>
      <div class="order-foot">
        <div v-if="o.status === 0" class="order-actions">
          <button v-if="canRefund(o)" class="refund-button" type="button" @click="refundTarget = o">申请退款</button>
          <button class="btn btn-primary btn-sm" @click="showCode(o)">查看取货凭证</button>
        </div>
        <div v-else-if="o.status === 1" class="order-actions">
          <button v-if="canRequestQualityRefund(o)" class="refund-button" type="button" @click="openQualityDialog(o)">食品问题售后</button>
          <span v-else class="completion-label">{{ studentCompletionText(o) }}</span>
        </div>
        <span v-else-if="o.close_reason === 'admin_refund'" class="completion-label">管理员审核退款</span>
      </div>
    </div>
    </div>

    <Teleport to="body">
      <div v-if="refundTarget" class="refund-backdrop" @click.self="closeRefundDialog">
        <section class="refund-dialog" role="dialog" aria-modal="true" aria-labelledby="refund-title">
          <button class="refund-close" type="button" aria-label="关闭退款确认" :disabled="refunding" @click="closeRefundDialog">×</button>
          <span class="refund-kicker">ORDER CANCELLATION</span>
          <h3 id="refund-title">确认取消这笔订单？</h3>
          <p>{{ refundTarget.product_title }}</p>
          <div class="refund-rule">
            <strong>¥{{ orderTotal(refundTarget) }} 将原路退回</strong>
            <span>取消后取货码立即失效，商品库存将恢复。超过付款后 5 分钟将不能自行退款。</span>
          </div>
          <div class="refund-actions">
            <button type="button" :disabled="refunding" @click="closeRefundDialog">继续保留</button>
            <button type="button" :disabled="refunding" @click="submitRefund">{{ refunding ? '退款处理中…' : '确认退款' }}</button>
          </div>
        </section>
      </div>
      <div v-if="qualityTarget" class="refund-backdrop" @click.self="closeQualityDialog">
        <section class="refund-dialog quality-dialog" role="dialog" aria-modal="true" aria-labelledby="quality-title">
          <button class="refund-close" type="button" aria-label="关闭售后申请" :disabled="submittingQuality" @click="closeQualityDialog">×</button>
          <span class="refund-kicker">QUALITY REVIEW</span>
          <h3 id="quality-title">食品问题售后</h3>
          <p>{{ qualityTarget.product_title }} · 订单 {{ orderNumber(qualityTarget) }}</p>
          <div class="quality-policy">
            <strong>提交后由管理员审核</strong>
            <span>仅处理实际领取后发现的食品质量问题。未按时领取不属于退款范围。</span>
          </div>
          <label class="quality-field">
            <span>问题说明</span>
            <textarea v-model="qualityReason" class="input" maxlength="500" placeholder="请描述食品存在的问题" />
            <small>{{ qualityReason.trim().length }}/500</small>
          </label>
          <div class="quality-field">
            <span>问题照片（可选）</span>
            <label class="evidence-picker" for="quality-evidence">{{ qualityEvidenceName || '选择照片' }}</label>
            <input id="quality-evidence" type="file" accept="image/*" @change="readEvidence" />
            <div v-if="qualityEvidence" class="evidence-preview">
              <img :src="qualityEvidence" alt="食品问题凭证" />
              <button type="button" @click="clearEvidence">移除</button>
            </div>
          </div>
          <div class="refund-actions">
            <button type="button" :disabled="submittingQuality" @click="closeQualityDialog">暂不提交</button>
            <button type="button" :disabled="submittingQuality || qualityReason.trim().length < 5" @click="submitQualityRefund">{{ submittingQuality ? '正在提交…' : '提交管理员审核' }}</button>
          </div>
        </section>
      </div>
    </Teleport>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { useRouter } from 'vue-router'
import { createRefundRequest, getOrders, getOrderSummary, getRefundRequests, refundOrder } from '../../api/order'
import { orderTotal, parseApiTime, useOrderCountdown } from '../../utils/orderCountdown'
import { toast } from '../../utils/toast'

const tabs = [
  { label: '全部', status: 'all' },
  { label: '待领取', status: 'pending' },
  { label: '已领取', status: 'picked' },
  { label: '未领取', status: 'unclaimed' },
  { label: '已退款', status: 'refunded' }
]

const router = useRouter()
const status = ref('all')
const allOrders = ref([])
const loading = ref(false)
const summaryLoading = ref(false)
const refundTarget = ref(null)
const refunding = ref(false)
const refundRequests = ref([])
const qualityTarget = ref(null)
const qualityReason = ref('')
const qualityEvidence = ref('')
const qualityEvidenceName = ref('')
const submittingQuality = ref(false)
const summary = ref({
  monthly_spending: '0.00',
  monthly_order_count: 0
})
const currentLabel = computed(() => tabs.find(t => t.status === status.value)?.label || '')
const orders = computed(() => allOrders.value.filter(order => matchesOrderFilter(order, status.value)))
const { now, remainingSeconds } = useOrderCountdown()
let lastOverdueRefresh = 0

async function load(quiet = false) {
  if (!quiet) loading.value = true
  summaryLoading.value = true
  const [orderResult, summaryResult, refundRequestResult] = await Promise.allSettled([
    getOrders({ status: '' }),
    getOrderSummary(),
    getRefundRequests()
  ])
  if (orderResult.status === 'fulfilled') allOrders.value = orderResult.value
  if (summaryResult.status === 'fulfilled') summary.value = summaryResult.value
  if (refundRequestResult.status === 'fulfilled') refundRequests.value = refundRequestResult.value
  if (!quiet) loading.value = false
  summaryLoading.value = false
}

function changeTab(s) { status.value = s }

function statusText(order) {
  if (order.status === 1) return order.completion_type === 'auto_timeout' ? '未领取' : '已领取'
  if (order.status === 2) {
    if (isRefundedOrder(order)) return '已退款'
    return '未领取'
  }
  return { 0: '待领取' }[order.status] || '未知'
}
function isRefundedOrder(order) {
  return order.payment_status === 'refunded'
    || ['student_refund', 'admin_refund'].includes(order.close_reason)
}
function isUnclaimed(order) {
  return (order.status === 1 && order.completion_type === 'auto_timeout')
    || (order.status === 2 && !isRefundedOrder(order))
}
function matchesOrderFilter(order, filter) {
  if (filter === 'pending') return order.status === 0
  if (filter === 'picked') return order.status === 1 && order.completion_type !== 'auto_timeout'
  if (filter === 'unclaimed') return isUnclaimed(order)
  if (filter === 'refunded') return isRefundedOrder(order)
  return true
}
function statusClass(order) {
  if (isUnclaimed(order)) return 'st-unclaimed'
  return { 0: 'st-pending', 1: 'st-picked', 2: 'st-expired' }[order.status] || ''
}
function studentCompletionText(order) { return isUnclaimed(order) ? '未领取' : '已领取' }
function money(value) { return Number(value || 0).toFixed(2) }
function orderNumber(order) { return `FL${String(order.id).padStart(6, '0')}` }

function paymentText(order) {
  if (order.payment_status === 'refunded') return '已退款'
  return '已支付'
}

function businessHoursText(order) {
  const open = String(order?.business_open_time || '').match(/\d{1,2}:\d{2}/)?.[0]
  const close = String(order?.business_close_time || '').match(/\d{1,2}:\d{2}/)?.[0]
  if (open && close) return `${open} - ${close}`
  if (close) return `营业至 ${close}`
  return '以商家当日营业时间为准'
}

function refundRemainingSeconds(order) {
  const deadline = parseApiTime(order?.refund_deadline)
  if (!Number.isFinite(deadline)) return 0
  return Math.max(0, Math.ceil((deadline - now.value) / 1000))
}

function canRefund(order) {
  return order?.status === 0 && order?.refundable !== false && refundRemainingSeconds(order) > 0
}

function refundCountdownText(order) {
  const seconds = refundRemainingSeconds(order)
  return `${String(Math.floor(seconds / 60)).padStart(2, '0')}:${String(seconds % 60).padStart(2, '0')}`
}

function closeRefundDialog() {
  if (!refunding.value) refundTarget.value = null
}

function refundRequestFor(order) {
  return refundRequests.value.find(item => item.order_id === order.id) || null
}

function refundRequestText(request) {
  return ['管理员审核中', '食品问题退款已通过', '食品问题退款未通过'][request.status] || '售后状态未知'
}

function refundRequestDetail(request) {
  if (request.status === 0) return `提交于 ${request.created_at}`
  return request.admin_remark || (request.status === 1 ? '款项已原路退回' : '管理员已驳回申请')
}

function canRequestQualityRefund(order) {
  return order?.status === 1 && order?.completion_type === 'merchant_confirmed' && !refundRequestFor(order)
}

function openQualityDialog(order) {
  qualityTarget.value = order
  qualityReason.value = ''
  clearEvidence()
}

function closeQualityDialog() {
  if (!submittingQuality.value) {
    qualityTarget.value = null
    qualityReason.value = ''
    clearEvidence()
  }
}

function clearEvidence() {
  qualityEvidence.value = ''
  qualityEvidenceName.value = ''
}

function readEvidence(event) {
  const file = event.target.files?.[0]
  event.target.value = ''
  if (!file) return
  if (!file.type.startsWith('image/')) { toast('请选择图片文件', 'error'); return }
  if (file.size > 2 * 1024 * 1024) { toast('图片大小不能超过 2MB', 'error'); return }
  const reader = new FileReader()
  reader.onload = () => {
    qualityEvidence.value = String(reader.result || '')
    qualityEvidenceName.value = file.name
  }
  reader.readAsDataURL(file)
}

async function submitQualityRefund() {
  const reason = qualityReason.value.trim()
  if (!qualityTarget.value || reason.length < 5) return
  submittingQuality.value = true
  try {
    await createRefundRequest(qualityTarget.value.id, {
      reason,
      evidence_image: qualityEvidence.value || null
    })
    qualityTarget.value = null
    qualityReason.value = ''
    clearEvidence()
    toast('售后申请已提交，等待管理员审核')
    await load(true)
  } catch (e) { /* 请求拦截器统一提示 */ } finally { submittingQuality.value = false }
}

async function submitRefund() {
  if (!refundTarget.value) return
  refunding.value = true
  try {
    await refundOrder(refundTarget.value.id)
    refundTarget.value = null
    toast('退款申请成功，款项将原路退回')
    await load()
  } catch (e) { /* 请求拦截器统一提示 */ } finally { refunding.value = false }
}

function showCode(o) {
  sessionStorage.setItem('shiyuan_last_order', JSON.stringify(o))
  router.push('/order/pickup')
}

watch(now, () => {
  const hasOverdue = allOrders.value.some(order => order.status === 0 && remainingSeconds(order) === 0)
  if (!hasOverdue || Date.now() - lastOverdueRefresh < 5000) return
  lastOverdueRefresh = Date.now()
  load(true)
})

load()
</script>

<style scoped>
.orders-page { --ink: #17211c; --soft-green: #dff2e7; }
.section-heading { margin-bottom: 12px; }
.section-heading-row { display: flex; align-items: baseline; gap: 18px; }
.section-title { flex-shrink: 0; font-size: 23px; font-weight: 750; }
.inline-summary { display: flex; min-width: 0; align-items: baseline; }
.summary-stat { display: inline-flex; min-width: 0; align-items: baseline; gap: 6px; padding: 0 14px; white-space: nowrap; }
.summary-stat:first-child { padding-left: 0; }
.summary-stat + .summary-stat { border-left: 1px solid #dfe5e1; }
.summary-stat em { color: #87908b; font-size: 11px; font-style: normal; font-weight: 500; }
.summary-stat strong { color: var(--ink); font-size: 15px; font-variant-numeric: tabular-nums; }
.summary-stat:first-child strong { color: var(--primary-dark); }
.summary-stat small { color: #87908b; font-size: 10px; }
.order-tabs { width: max-content; max-width: 100%; gap: 2px; padding: 3px; border: 1px solid var(--border); border-radius: 8px; background: #fff; }
.order-tabs .tab { min-width: 64px; padding: 7px 12px; border: 0; border-radius: 6px; background: transparent; }
.order-tabs .tab.active { background: var(--ink); color: #fff; }
.order-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 16px; }
.order-card { overflow: hidden; padding: 17px; border-color: #e0e5e2; border-radius: 8px; box-shadow: 0 7px 20px rgba(31, 41, 55, .045); transition: border-color .16s, box-shadow .16s, transform .16s; }
.order-card:hover { border-color: #cfd8d2; box-shadow: 0 12px 28px rgba(31, 41, 55, .08); transform: translateY(-1px); }
.order-top { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 12px; }
.shop-block { display: flex; min-width: 0; flex-direction: column; }
.shop-block small { margin-top: 2px; color: #9aa29d; font-size: 9px; font-variant-numeric: tabular-nums; }
.shop { font-weight: 700; }
.status-badge { padding: 3px 8px; border-radius: 6px; background: #f4f5f4; font-size: 11px; font-weight: 700; }
.status-badge.st-pending { background: #fff4df; }
.status-badge.st-picked { background: var(--soft-green); }
.status-badge.st-unclaimed { background: #f1f3f2; color: #657069; }
.order-body { display: flex; gap: 15px; }
.thumb { width: 92px; height: 92px; border-radius: 8px; background: #edf0ee; display: flex; align-items: center; justify-content: center; color: #8a938e; font-size: 12px; font-weight: 700; overflow: hidden; flex-shrink: 0; }
.thumb img { width: 100%; height: 100%; object-fit: cover; }
.order-info { min-width: 0; flex: 1; }
.title { overflow-wrap: anywhere; font-size: 16px; font-weight: 700; }
.item-price { margin-top: 5px; color: #d75d16; font-size: 15px; font-weight: 700; font-variant-numeric: tabular-nums; }
.item-price span { color: #8c958f; font-size: 11px; font-weight: 500; }
.meta { display: grid; grid-template-columns: 55px minmax(0, 1fr); margin-top: 5px; color: #68716c; font-size: 11px; }
.meta span { color: #a0a7a3; }
.payment-state { display: flex; align-items: baseline; justify-content: space-between; gap: 10px; margin-top: 10px; color: var(--muted); font-size: 12px; }
.payment-state > span { display: inline-flex; align-items: center; gap: 5px; color: var(--success); font-weight: 700; }
.payment-state > span.refunded { color: #64748b; }
.payment-state i { width: 6px; height: 6px; border-radius: 50%; background: currentColor; }
.payment-state small { text-align: right; }
.amount-bar { display: flex; align-items: center; justify-content: space-between; gap: 12px; min-height: 48px; margin-top: 12px; padding: 9px 12px; border: 1px solid #f4d8bd; border-radius: 7px; background: #fff8f0; }
.amount-bar div { min-width: 0; }
.amount-bar span, .amount-bar small { display: block; }
.amount-bar span { color: #7b4b2b; font-size: 12px; font-weight: 700; }
.amount-bar small { margin-top: 2px; color: #a28b79; font-size: 10px; }
.amount-bar strong { flex-shrink: 0; color: var(--primary-dark); font-size: 19px; font-variant-numeric: tabular-nums; }
.order-foot { display: flex; justify-content: flex-end; align-items: center; min-height: 40px; margin-top: 8px; padding-top: 8px; border-top: 1px dashed var(--border); }
.completion-label { color: var(--success); font-size: 12px; font-weight: 600; }
.order-actions { display: flex; align-items: center; justify-content: flex-end; gap: 8px; }
.refund-button { min-height: 32px; padding: 0 11px; border: 1px solid #d8dedb; border-radius: 7px; background: #fff; color: #5d6862; font-size: 12px; font-weight: 650; cursor: pointer; }
.refund-button:hover { border-color: #bcc6c0; background: #f8faf9; }
.refund-backdrop { position: fixed; inset: 0; z-index: 10020; display: flex; align-items: center; justify-content: center; padding: 18px; background: rgba(16, 24, 20, .48); }
.refund-dialog { position: relative; width: min(390px, 100%); padding: 25px; border-radius: 8px; background: #fff; box-shadow: 0 24px 64px rgba(17, 25, 21, .25); }
.refund-close { position: absolute; top: 13px; right: 13px; width: 32px; height: 32px; border: 0; border-radius: 6px; background: #f4f6f5; color: #59635d; font-size: 22px; line-height: 1; cursor: pointer; }
.refund-kicker { color: #8b958f; font-size: 9px; font-weight: 800; }
.refund-dialog h3 { margin: 6px 36px 5px 0; font-size: 21px; }
.refund-dialog > p { margin: 0; color: #7a847e; font-size: 13px; }
.refund-rule { margin-top: 18px; padding: 14px; border-left: 3px solid var(--primary); background: #fff7ed; }
.refund-rule strong, .refund-rule span { display: block; }
.refund-rule strong { color: #9a4514; font-size: 15px; }
.refund-rule span { margin-top: 5px; color: #716963; font-size: 12px; line-height: 1.6; }
.refund-actions { display: grid; grid-template-columns: 1fr 1.25fr; gap: 9px; margin-top: 20px; }
.refund-actions button { min-height: 42px; border: 1px solid #d9dfdc; border-radius: 7px; background: #fff; font-size: 13px; font-weight: 700; cursor: pointer; }
.refund-actions button:last-child { border-color: #d95f17; background: var(--primary); color: #fff; }
.refund-actions button:disabled, .refund-close:disabled { opacity: .5; cursor: default; }
.after-sale-state { display: flex; align-items: center; justify-content: space-between; gap: 12px; margin-top: 10px; padding: 9px 11px; border-left: 3px solid #f59e0b; background: #fffbeb; color: #87570d; font-size: 11px; }
.after-sale-state strong { font-size: 12px; }
.after-sale-state span { text-align: right; }
.after-sale-state.review-1 { border-color: #16a34a; background: #f0fdf4; color: #166534; }
.after-sale-state.review-2 { border-color: #94a3b8; background: #f8fafc; color: #586575; }
.quality-dialog { max-height: min(720px, calc(100vh - 36px)); overflow-y: auto; }
.quality-policy { margin-top: 17px; padding: 12px 14px; border-left: 3px solid #f59e0b; background: #fffbeb; }
.quality-policy strong, .quality-policy span { display: block; }
.quality-policy strong { color: #8a5410; font-size: 13px; }
.quality-policy span { margin-top: 3px; color: #766954; font-size: 11px; line-height: 1.55; }
.quality-field { display: block; margin-top: 15px; }
.quality-field > span { display: block; margin-bottom: 6px; color: #4f5a54; font-size: 12px; font-weight: 700; }
.quality-field textarea { min-height: 94px; font-size: 13px; }
.quality-field > small { display: block; margin-top: 3px; color: #9aa29d; font-size: 10px; text-align: right; }
.quality-field > input[type='file'] { position: absolute; width: 1px; height: 1px; overflow: hidden; opacity: 0; pointer-events: none; }
.evidence-picker { display: inline-flex; min-height: 36px; max-width: 100%; align-items: center; padding: 7px 12px; overflow: hidden; border: 1px dashed #cdd5d0; border-radius: 7px; color: #67716b; font-size: 12px; text-overflow: ellipsis; white-space: nowrap; cursor: pointer; }
.evidence-preview { position: relative; width: 112px; margin-top: 9px; }
.evidence-preview img { display: block; width: 112px; height: 86px; border-radius: 6px; object-fit: cover; }
.evidence-preview button { position: absolute; right: 4px; bottom: 4px; padding: 3px 6px; border: 0; border-radius: 4px; background: rgba(17, 24, 39, .76); color: #fff; font-size: 10px; cursor: pointer; }
@media (max-width: 520px) {
  .orders-page { width: 100%; max-width: 100%; }
  .section-heading-row { gap: 10px; }
  .inline-summary { flex: 1; }
  .summary-stat { flex: 1; justify-content: center; gap: 4px; padding-inline: 6px; }
  .summary-stat em { font-size: 9px; }
  .summary-stat strong { font-size: 13px; }
  .order-grid { grid-template-columns: 1fr; }
  .order-tabs { width: 100%; }
  .order-tabs .tab { flex: 1; min-width: 0; padding-inline: 7px; }
  .payment-state { align-items: flex-start; flex-direction: column; gap: 3px; }
  .payment-state small { text-align: left; }
  .after-sale-state { align-items: flex-start; flex-direction: column; gap: 2px; }
  .after-sale-state span { text-align: left; }
  .thumb { width: 82px; height: 82px; }
  .title { font-size: 14px; }
  .meta { grid-template-columns: 50px minmax(0, 1fr); font-size: 10px; }
}
@media (max-width: 360px) {
  .section-heading-row { gap: 7px; }
  .section-title { font-size: 21px; }
  .summary-stat { gap: 2px; padding-inline: 4px; }
  .summary-stat em { font-size: 8px; }
  .summary-stat strong { font-size: 12px; }
  .order-foot { align-items: flex-start; flex-direction: column; gap: 9px; }
  .order-actions { width: 100%; }
  .order-actions .btn, .refund-button { flex: 1; }
}
</style>
