<template>
  <div>
    <button class="btn btn-sm" @click="$router.back()">← 返回</button>

    <div v-if="product" class="card">
      <div class="img-corner">
        <template v-if="product.image"><img :src="product.image" alt="" /></template>
        <span v-else class="img-ph">🍱</span>
      </div>
      <h2 class="p-title">{{ product.title }}</h2>
      <div class="p-tags">
        <span class="tag">{{ category }}</span>
        <span class="tag tag-muted">距 {{ product.distance }} km</span>
        <span v-if="nearExpiry" class="tag" style="background:#fee2e2;color:#dc2626">即将过期</span>
      </div>
      <div class="p-price">
        <span class="price current">¥{{ product.discount_price }}</span>
        <span class="price-old">¥{{ product.original_price }}</span>
        <span class="discount">{{ discountText }}</span>
      </div>
      <p class="p-desc">{{ product.description || '暂无描述' }}</p>

      <div class="card" style="margin:14px 0 0; padding:14px">
        <div class="row"><span class="k">剩余数量</span><span class="v">{{ product.quantity }} 份</span></div>
        <div class="row"><span class="k">取货地点</span><span class="v">{{ product.location }}</span></div>
        <div class="row"><span class="k">营业时间</span><span class="v">{{ businessHours }}</span></div>
        <div class="row"><span class="k">截止有效期</span><span class="v">{{ product.expire_time }}</span></div>
        <div class="row"><span class="k">店铺</span><span class="v">{{ product.merchant?.shop_name || '-' }}</span></div>
        <div class="row"><span class="k">已售 / 收藏</span><span class="v">{{ product.order_count }} 单 / {{ product.fav_count }} 收藏</span></div>
      </div>
    </div>
    <div v-else-if="loading" class="empty">加载中…</div>

    <div v-if="product" class="action-bar">
      <button class="btn btn-outline action-fav" :class="{ faved: product.is_favorite }" @click="toggleFav">
        {{ product.is_favorite ? '♥ 已收藏' : '♡ 收藏' }}
      </button>
      <button class="btn btn-primary action-order" @click="orderNow" :disabled="paying || product.quantity <= 0">
        {{ paying ? '支付处理中…' : product.quantity <= 0 ? '已售罄' : '立即下单' }}
      </button>
    </div>

    <WeChatPayDialog
      :open="paymentOpen"
      :amount="product?.discount_price || 0"
      :merchant="product?.merchant?.shop_name || ''"
      :product="product?.title || ''"
      :status="paymentStatus"
      :error="paymentError"
      @cancel="closePayment"
      @confirm="confirmPayment"
      @done="showPickupCode"
    />
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import WeChatPayDialog from '../../components/WeChatPayDialog.vue'
import { getProduct, setFavorite } from '../../api/product'
import { createOrder } from '../../api/order'
import { toast } from '../../utils/toast'
import { isProductExpired } from '../../utils/productAvailability'

const route = useRoute()
const router = useRouter()
const product = ref(null)
const loading = ref(false)
const paymentOpen = ref(false)
const paymentStatus = ref('idle')
const paymentError = ref('')
const createdOrder = ref(null)
const paying = computed(() => paymentStatus.value === 'processing')

const CAT = { 简餐: '简餐', 饮品: '饮品', 烘焙: '烘焙', 水果: '水果', 其他: '其他' }
const category = computed(() => product.value ? (CAT[product.value.category] || product.value.category || '其他') : '')
const businessHours = computed(() => product.value
  ? `${product.value.business_open_time || '08:00'}–${product.value.business_close_time || '22:00'}`
  : '')
const nearExpiry = computed(() => {
  if (!product.value?.expire_time) return false
  const diff = new Date(product.value.expire_time).getTime() - Date.now()
  return diff > 0 && diff < 3 * 3600 * 1000
})
const discountText = computed(() => {
  if (!product.value?.original_price || !product.value?.discount_price) return ''
  const d = (product.value.discount_price / product.value.original_price) * 10
  return d.toFixed(1) + ' 折'
})

async function load() {
  loading.value = true
  try {
    const data = await getProduct(route.params.id)
    if (isProductExpired(data)) {
      toast('该商品已过期', 'error')
      router.replace('/home')
      return
    }
    product.value = data
  } catch (e) {
    if (String(e?.message || '').includes('过期')) router.replace('/home')
  } finally { loading.value = false }
}

async function toggleFav() {
  if (!product.value) return
  const next = !product.value.is_favorite
  try {
    const data = await setFavorite(product.value.id, next)
    product.value.is_favorite = data.favorite
    product.value.fav_count = data.fav_count
    toast(next ? '已收藏' : '已取消收藏')
  } catch (e) { /* 拦截器处理 */ }
}

function orderNow() {
  if (!product.value || product.value.quantity <= 0) {
    toast('商品库存不足', 'error')
    return
  }
  paymentError.value = ''
  paymentStatus.value = 'idle'
  paymentOpen.value = true
}

function closePayment() {
  if (paying.value) return
  paymentOpen.value = false
  paymentError.value = ''
}

async function confirmPayment() {
  if (paying.value || !product.value) return
  paymentStatus.value = 'processing'
  paymentError.value = ''
  try {
    await new Promise(resolve => setTimeout(resolve, 700))
    const o = await createOrder({ product_id: product.value.id, quantity: 1 })
    createdOrder.value = { ...o, payment_method: 'wechat' }
    product.value.quantity = Math.max(0, Number(product.value.quantity) - 1)
    paymentStatus.value = 'success'
  } catch (e) {
    paymentStatus.value = 'idle'
    paymentError.value = e?.message || '支付未完成，请重试'
  }
}

function showPickupCode() {
  if (!createdOrder.value) return
  try {
    const o = createdOrder.value
    sessionStorage.setItem('shiyuan_last_order', JSON.stringify(o))
    paymentOpen.value = false
    toast('支付成功，订单已创建')
    router.push('/order/pickup')
  } finally {
    paymentStatus.value = 'idle'
    paymentError.value = ''
  }
}

onMounted(load)
</script>

<style scoped>
.img-corner { width: 100%; height: 200px; border-radius: 8px; background: #f3f4f6; display: flex; align-items: center; justify-content: center; font-size: 64px; overflow: hidden; }
.img-corner img { width: 100%; height: 100%; object-fit: cover; }
.p-title { font-size: 22px; margin: 14px 0 8px; }
.p-tags { margin-bottom: 10px; }
.p-price { display: flex; align-items: baseline; gap: 10px; margin-bottom: 10px; }
.price.current { font-size: 26px; }
.price-old { color: var(--muted); text-decoration: line-through; font-size: 15px; }
.discount { background: var(--primary); color: #fff; font-size: 12px; padding: 2px 8px; border-radius: 6px; }
.p-desc { color: var(--muted); font-size: 14px; }
.action-bar { position: sticky; bottom: 0; background: var(--card); border-top: 1px solid var(--border); padding: 12px; margin: 16px -16px -48px; display: flex; gap: 12px; }
.action-fav { flex: 1; }
.action-fav.faved { border-color: #f43f5e; color: #f43f5e; }
.action-order { flex: 2; }
</style>
