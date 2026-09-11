<template>
  <div>
    <div v-if="order" class="card pickup-code">
      <template v-if="order.status === 0">
        <p class="rc-title">支付成功，请出示取货码</p>
        <div class="code">{{ order.pickup_code }}</div>
        <p class="rc-sub">到店出示此码，由商家完成核销</p>
        <div class="pickup-deadline">
          <span>领取倒计时</span>
          <strong>{{ countdownText(order) }}</strong>
          <small>截止 {{ order.pickup_deadline }}（商家关门时间），到时系统自动完成</small>
        </div>
      </template>
      <template v-else>
        <div class="complete-mark">✓</div>
        <p class="complete-title">{{ completionText(order) }}</p>
        <p class="rc-sub">订单已完成并结算给商家</p>
      </template>

      <div class="card" style="margin:18px 0 0; padding:14px">
        <div class="row"><span class="k">商品</span><span class="v">{{ order.product_title }}</span></div>
        <div class="row"><span class="k">店铺</span><span class="v">{{ order.shop_name }}</span></div>
        <div class="row"><span class="k">实付金额</span><span class="v price">¥{{ orderTotal(order) }}</span></div>
        <div class="row"><span class="k">资金状态</span><span class="v escrow">{{ order.payment_status === 'settled' ? '已结算' : '平台托管中' }}</span></div>
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
import { ref, watch } from 'vue'
import { getOrders } from '../../api/order'
import { completionText, orderTotal, useOrderCountdown } from '../../utils/orderCountdown'

const order = ref(null)
const { now, remainingSeconds, countdownText } = useOrderCountdown()
let lastOverdueRefresh = 0
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
.pickup-deadline { margin-top: 18px; padding: 14px; border-left: 3px solid var(--primary); background: #fff7ed; text-align: left; }
.pickup-deadline span { display: block; color: var(--primary-dark); font-size: 13px; font-weight: 700; }
.pickup-deadline strong { display: block; margin: 3px 0; color: var(--primary-dark); font-size: 30px; font-variant-numeric: tabular-nums; text-align: center; }
.pickup-deadline small { display: block; color: var(--muted); font-size: 11px; text-align: center; }
.complete-mark { display: flex; align-items: center; justify-content: center; width: 58px; height: 58px; margin: 0 auto 12px; border-radius: 50%; background: var(--success); color: #fff; font-size: 34px; }
.complete-title { margin: 0; color: var(--success); font-size: 20px; font-weight: 700; }
.escrow { color: var(--success) !important; font-weight: 700; }
</style>
