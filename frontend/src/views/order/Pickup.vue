<template>
  <div>
    <div v-if="order" class="card pickup-code">
      <p class="rc-title">取货成功，请出示凭证码</p>
      <div class="code">{{ order.pickup_code }}</div>
      <p class="rc-sub">到店出示此码完成核销领取</p>

      <div class="card" style="margin:18px 0 0; padding:14px">
        <div class="row"><span class="k">商品</span><span class="v">{{ order.product_title }}</span></div>
        <div class="row"><span class="k">店铺</span><span class="v">{{ order.shop_name }}</span></div>
        <div class="row"><span class="k">金额</span><span class="v price">¥{{ order.price }}</span></div>
        <div class="row"><span class="k">取货地址</span><span class="v">{{ order.location || '-' }}</span></div>
        <div class="row"><span class="k">下单时间</span><span class="v">{{ order.created_at }}</span></div>
        <div class="row"><span class="k">有效期至</span><span class="v">{{ order.expire_time }}</span></div>
      </div>
    </div>
    <div v-else class="empty"><div class="big">🎫</div>没有待展示的取货凭证</div>

    <button class="btn btn-primary btn-block" @click="$router.push('/orders')">查看我的订单</button>
    <div style="height:10px"></div>
    <button class="btn btn-block" @click="$router.push('/profile')">返回个人中心</button>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'

const order = ref(null)
try {
  const raw = sessionStorage.getItem('shiyuan_last_order')
  if (raw) order.value = JSON.parse(raw)
} catch (e) { /* ignore */ }
</script>

<style scoped>
.pickup-code { text-align: center; padding: 28px 20px; }
.rc-title { margin: 0 0 12px; font-size: 16px; color: var(--muted); }
.code { font-size: 52px; font-weight: 800; letter-spacing: 10px; color: var(--primary); }
.rc-sub { margin: 8px 0 0; font-size: 13px; color: var(--muted); }
</style>