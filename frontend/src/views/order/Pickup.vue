<template>
  <div>
    <div v-if="order" class="card pickup-code">
      <template v-if="order.status === 0">
        <p class="rc-title">支付成功，请出示取货码</p>
        <div class="code-line">
          <div class="code">{{ order.pickup_code }}</div>
          <span class="credential-status">待领取</span>
        </div>
        <p class="rc-sub">到店向商家出示取货码和订单详情即可领取</p>
      </template>
      <template v-else-if="order.status === 1 && order.completion_type !== 'auto_timeout'">
        <div class="complete-mark">✓</div>
        <p class="complete-title">已领取</p>
        <p class="rc-sub">订单已完成</p>
      </template>
      <template v-else-if="order.status === 1">
        <div class="complete-mark closed-mark">!</div>
        <p class="complete-title closed-title">未领取</p>
        <p class="rc-sub">本单领取时间已结束</p>
      </template>
      <template v-else-if="order.close_reason === 'student_refund'">
        <div class="complete-mark closed-mark">×</div>
        <p class="complete-title closed-title">订单已退款</p>
        <p class="rc-sub">取货码已失效，款项将原路退回</p>
      </template>
      <template v-else>
        <div class="complete-mark closed-mark">!</div>
        <p class="complete-title closed-title">未领取</p>
        <p class="rc-sub">本单领取时间已结束</p>
      </template>

      <div class="order-details">
        <div class="row"><span class="k">商品</span><span class="v">{{ order.product_title }}</span></div>
        <div class="row"><span class="k">店铺</span><span class="v">{{ order.shop_name }}</span></div>
        <div class="row"><span class="k">实付金额</span><span class="v price">¥{{ orderTotal(order) }}</span></div>
        <div class="row"><span class="k">支付状态</span><span class="v escrow">{{ paymentText(order) }}</span></div>
        <div class="row"><span class="k">取货地址</span><span class="v">{{ order.location || '-' }}</span></div>
        <div class="row"><span class="k">商家营业时间</span><span class="v">{{ businessHoursText(order) }}</span></div>
        <div class="row"><span class="k">下单时间</span><span class="v">{{ order.created_at }}</span></div>
      </div>
    </div>
    <div v-else class="empty"><div class="big">🎫</div>没有待展示的取货凭证</div>

    <button class="btn btn-primary btn-block" @click="$router.push('/orders')">查看我的订单</button>
    <div style="height:10px"></div>
    <button class="btn btn-block" @click="$router.push('/profile')">返回个人中心</button>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'
import { getOrders } from '../../api/order'
import { orderTotal, useOrderCountdown } from '../../utils/orderCountdown'

const order = ref(null)
const { now, remainingSeconds } = useOrderCountdown()
let lastOverdueRefresh = 0
function paymentText(value) {
  if (value?.payment_status === 'refunded') return '已退款'
  return '已支付'
}
function businessHoursText(value) {
  const open = String(value?.business_open_time || '').match(/\d{1,2}:\d{2}/)?.[0]
  const close = String(value?.business_close_time || '').match(/\d{1,2}:\d{2}/)?.[0]
  if (open && close) return `${open} - ${close}`
  if (close) return `营业至 ${close}`
  return '以商家当日营业时间为准'
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
.code-line { display: flex; align-items: center; justify-content: center; gap: 13px; }
.credential-status { display: inline-flex; min-height: 32px; flex-shrink: 0; align-items: center; padding: 5px 12px; border-radius: 16px; background: #fff1e8; color: var(--primary-dark); font-size: 15px; font-weight: 750; }
.rc-title { margin: 0 0 12px; font-size: 16px; color: var(--muted); }
.code { font-size: 52px; font-weight: 800; letter-spacing: 10px; color: var(--primary); }
.rc-sub { margin: 8px 0 0; font-size: 13px; color: var(--muted); }
.complete-mark { display: flex; align-items: center; justify-content: center; width: 58px; height: 58px; margin: 0 auto 12px; border-radius: 50%; background: var(--success); color: #fff; font-size: 34px; }
.complete-title { margin: 0; color: var(--success); font-size: 20px; font-weight: 700; }
.closed-mark { background: #64748b; }
.closed-title { color: #52606d; }
.order-details { margin-top: 18px; padding: 14px; border: 1px solid var(--border); border-radius: 8px; background: #fff; }
.escrow { color: var(--success) !important; font-weight: 700; }
@media (max-width: 480px) { .code-line { gap: 8px; } .code { font-size: 34px; letter-spacing: 6px; } .credential-status { min-height: 29px; padding: 4px 9px; font-size: 14px; } }
</style>
