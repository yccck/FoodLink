<template>
  <div>
    <div v-if="order" class="card pickup-code">
      <template v-if="order.status === 0">
        <p class="rc-title">支付成功，请出示取货码</p>
        <div class="code">{{ order.pickup_code }}</div>
        <p class="rc-sub">到店向商家出示取货码和订单详情即可领取</p>
      </template>
      <template v-else-if="order.status === 1">
        <div class="complete-mark">✓</div>
        <p class="complete-title">{{ completionText(order) }}</p>
        <p class="rc-sub">订单已完成</p>
      </template>
      <template v-else-if="order.close_reason === 'student_refund'">
        <div class="complete-mark closed-mark">×</div>
        <p class="complete-title closed-title">订单已退款</p>
        <p class="rc-sub">取货码已失效，款项将原路退回</p>
      </template>
      <template v-else>
        <div class="complete-mark closed-mark">!</div>
        <p class="complete-title closed-title">领取期限已过</p>
        <p class="rc-sub">订单已按领取规则结束</p>
      </template>

      <div class="order-details">
        <div class="row"><span class="k">商品</span><span class="v">{{ order.product_title }}</span></div>
        <div class="row"><span class="k">店铺</span><span class="v">{{ order.shop_name }}</span></div>
        <div class="row"><span class="k">商品金额</span><span class="v">¥{{ orderTotal(order) }}</span></div>
        <div v-if="rewardAmount > 0" class="row"><span class="k">奖励金抵扣</span><span class="v reward">-¥{{ money(rewardAmount) }}</span></div>
        <div class="row"><span class="k">微信实付</span><span class="v price">¥{{ money(cashAmount) }}</span></div>
        <div class="row"><span class="k">支付状态</span><span class="v escrow">{{ paymentText(order) }}</span></div>
        <div class="row"><span class="k">取货地址</span><span class="v">{{ order.location || '-' }}</span></div>
        <div class="row"><span class="k">下单时间</span><span class="v">{{ order.created_at }}</span></div>
        <div class="row"><span class="k">领取截止</span><span class="v">{{ order.pickup_deadline }}</span></div>
      </div>
    </div>
    <div v-else class="empty"><div class="big">🎫</div>没有待展示的取货凭证</div>

    <button class="btn btn-primary btn-block" @click="$router.push('/orders')">查看我的订单</button>
    <div style="height:10px"></div>
    <button class="btn btn-block" @click="$router.push('/profile')">返回个人中心</button>
  </div>
</template>

<script setup>
import { computed, ref, watch } from 'vue'
import { getOrders } from '../../api/order'
import { completionText, orderTotal, useOrderCountdown } from '../../utils/orderCountdown'

const order = ref(null)
const rewardAmount = computed(() => Math.max(0, Number(order.value?.reward_amount || 0)))
const cashAmount = computed(() => {
  const total = Number(order.value ? orderTotal(order.value) : 0)
  return Math.max(0, Number(order.value?.cash_amount ?? total - rewardAmount.value))
})
const { now, remainingSeconds } = useOrderCountdown()
let lastOverdueRefresh = 0
function money(value) { return Number(value || 0).toFixed(2) }
function paymentText(value) {
  if (value?.payment_status === 'refunded') return '已退款'
  if (value?.payment_status === 'settled') return '已结算'
  return '已支付'
}
try {
  const raw = sessionStorage.getItem('shiyuan_last_order')
  if (raw) order.value = JSON.parse(raw)
} catch (e) { /* ignore */ }

watch(now, async () => {
  if (!order.value || order.value.status !== 0 || remainingSeconds(order.value) > 0) return
  if (Date.now() - lastOverdueRefresh < 5000) return
  lastOverdueRefresh = Date.now()
  try {
    const orders = await getOrders({ status: '' })
    const updated = orders.find(item => item.id === order.value.id)
    if (updated) {
      order.value = updated
      sessionStorage.setItem('shiyuan_last_order', JSON.stringify(updated))
    }
  } catch (e) { /* 请求拦截器提示 */ }
})
</script>

<style scoped>
.pickup-code { text-align: center; padding: 28px 20px; }
.rc-title { margin: 0 0 12px; font-size: 16px; color: var(--muted); }
.code { font-size: 52px; font-weight: 800; letter-spacing: 10px; color: var(--primary); }
.rc-sub { margin: 8px 0 0; font-size: 13px; color: var(--muted); }
.complete-mark { display: flex; align-items: center; justify-content: center; width: 58px; height: 58px; margin: 0 auto 12px; border-radius: 50%; background: var(--success); color: #fff; font-size: 34px; }
.complete-title { margin: 0; color: var(--success); font-size: 20px; font-weight: 700; }
.closed-mark { background: #64748b; }
.closed-title { color: #52606d; }
.order-details { margin-top: 18px; padding: 14px; border: 1px solid var(--border); border-radius: 8px; background: #fff; }
.escrow { color: var(--success) !important; font-weight: 700; }
.reward { color: #d65f14 !important; font-weight: 700; }
</style>
