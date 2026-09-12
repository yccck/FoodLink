<template>
  <article class="xhs-card" @click="open">
    <div class="xhs-cover" :style="coverStyle">
      <img v-if="product.image" :src="product.image" :alt="product.title" />
      <span v-else class="cover-emoji">{{ product.emoji || '🍱' }}</span>

      <!-- 折扣标签 -->
      <span v-if="discountText" class="xhs-off">{{ discountText }}</span>

      <!-- 售罄遮罩 -->
      <div v-if="!(product.quantity > 0) || product.status === 2" class="soldout">已售罄</div>
    </div>

    <div class="xhs-body">
      <h3 class="xhs-title">{{ product.title }}</h3>

      <div class="xhs-price-row">
        <span class="xhs-price"><small>¥</small>{{ discountInt }}</span>
        <span v-if="product.original_price" class="xhs-origin">¥{{ product.original_price }}</span>
      </div>

      <div class="xhs-meta">
        <span class="xhs-distance">{{ distanceText }}</span>
      </div>
    </div>
  </article>
</template>

<script setup>
import { computed } from 'vue'
import { useRouter } from 'vue-router'

const props = defineProps({ product: { type: Object, required: true } })
const router = useRouter()

const discountText = computed(() => {
  const { original_price: o, discount_price: d } = props.product
  if (!o || !d) return ''
  const z = (d / o) * 10
  return (z <= 1 ? '1折起' : z < 10 ? z.toFixed(1) + '折' : '')
})
const discountInt = computed(() => {
  const d = Number(props.product.discount_price)
  return Number.isInteger(d) ? String(d) : d.toFixed(2)
})
const distanceText = computed(() => {
  const d = Number(props.product.distance)
  if (d == null || isNaN(d)) return ''
  return d < 1 ? (d * 1000).toFixed(0) + 'm' : d.toFixed(1) + 'km'
})

function coverStyle() {
  return {
    background: `linear-gradient(135deg, ${props.product.gradient || '#ff9a56'} 0%, #f0f0f0 100%)`
  }
}

function open() { router.push(`/product/${props.product.id}`) }
</script>

<style scoped>
.xhs-card {
  background: #fff; border-radius: 12px; overflow: hidden; cursor: pointer;
  box-shadow: 0 1px 3px rgba(0,0,0,.06); min-width: 0; display: block; width: 100%;
}
.xhs-card:hover { box-shadow: 0 4px 12px rgba(0,0,0,.12); }
.xhs-cover {
  position: relative; width: 100%; aspect-ratio: 3 / 4; overflow: hidden; display: flex; align-items: center; justify-content: center;
}
.xhs-cover img { display: block; width: 100%; height: 100%; object-fit: cover; object-position: center; }
.cover-emoji { font-size: 56px; opacity: .9; }
.xhs-off {
  position: absolute; left: 0; top: 8px; background: linear-gradient(90deg,#f97316,#ef4444);
  color: #fff; font-size: 11px; font-weight: 600; padding: 2px 8px; border-radius: 0 8px 8px 0;
}
.soldout { position: absolute; inset: 0; background: rgba(255,255,255,.6); display: flex; align-items: center; justify-content: center; color: #9ca3af; font-size: 16px; letter-spacing: 4px; }
.xhs-body { padding: 8px 10px 12px; }
.xhs-title {
  font-size: 14px; font-weight: 600; line-height: 1.35; margin: 0 0 6px;
  display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden;
}
.xhs-price-row { display: flex; align-items: baseline; gap: 6px; margin-bottom: 4px; }
.xhs-price { color: #ef4444; font-weight: 700; font-size: 17px; }
.xhs-price small { font-size: 11px; }
.xhs-origin { color: #9ca3af; font-size: 12px; text-decoration: line-through; }
.xhs-meta { display: flex; align-items: center; font-size: 11px; color: #9ca3af; }
</style>
