<template>
  <div class="home" @pointerdown="onPullStart" @pointermove="onPullMove" @pointerup="onPullEnd" @pointercancel="onPullEnd">
    <section class="welcome-hero">
      <div class="hero-copy">
        <p class="hello-line">🍚 晚上好，{{ userName }}</p>
        <h1>今天也一起，把好味道<br />送到真正需要的人手里</h1>
        <p class="hero-note">附近的剩余好食已经为你整理好，按口味、距离和生活费预算温柔推荐。</p>
        <div class="hero-tags"><span>🌱 减少浪费</span><span>🧡 校园互助</span><span>🥡 安心领取</span></div>
      </div>
      <div class="hero-impact">
        <span class="impact-icon">🌏</span>
        <p>本月一起减少浪费</p>
        <strong>386 kg</strong>
        <small>来自 23 家校园周边商户</small>
      </div>
      <span class="hero-doodle leaf" aria-hidden>🌿</span>
      <span class="hero-doodle orange" aria-hidden>🍊</span>
    </section>

    <section class="stats-grid" aria-label="食愿平台统计">
      <article><span class="stat-icon green">🥡</span><div><p>今日可领取</p><strong>{{ availableCount }} 份</strong></div></article>
      <article><span class="stat-icon orange-bg">✨</span><div><p>今日上新</p><strong>{{ totalProducts }} 份</strong></div></article>
      <article><span class="stat-icon yellow">🏪</span><div><p>附近参与商家</p><strong>{{ merchantCount }} 家</strong></div></article>
      <article><span class="stat-icon peach">💚</span><div><p>累计挽救好食</p><strong>3,842 份</strong></div></article>
    </section>

    <div class="home-head">
      <div class="head-left">
        <div class="head-title">今晚吃点好的</div>
        <div class="head-reason">{{ recommendReason || '基于你的偏好与历史行为推荐' }}</div>
      </div>
      <button class="head-refresh" title="刷新推荐" aria-label="刷新推荐" @click="refresh">⟳</button>
    </div>

    <!-- 下拉刷新指示 -->
    <div class="pull-tip" :class="{ show: pullDistance > 0 }">
      <span>{{ pullDistance >= PULL_THRESHOLD ? '松开刷新' : '下拉刷新' }}</span>
    </div>

    <div class="masonry">
      <ProductCard v-for="item in list" :key="item.id" :product="item" />
    </div>

    <div ref="sentinel" class="sentinel">
      <span v-if="loading">加载中…</span>
      <span v-else-if="!list.length && !loading">暂无推荐商品</span>
      <span v-else-if="!hasMore" class="no-more">没有更多了</span>
    </div>
  </div>
</template>

<script setup>
import { computed, ref, onMounted, onBeforeUnmount } from 'vue'
import ProductCard from '../../components/ProductCard.vue'
import { getRecommend } from '../../api/recommend'
import { toast } from '../../utils/toast'
import { useAuthStore } from '../../stores/user'

const PAGE_SIZE = 6
const PULL_THRESHOLD = 70

const list = ref([])
const page = ref(0)
const hasMore = ref(true)
const loading = ref(false)
const recommendReason = ref('')
const total = ref(0)
const authStore = useAuthStore()

const userName = computed(() => authStore.user?.name || '同学')
const availableCount = computed(() => list.value.reduce((sum, item) => sum + Math.max(0, Number(item.quantity) || 0), 0))
const totalProducts = computed(() => total.value || list.value.length)
const merchantCount = 5

// 滚动加载
const sentinel = ref(null)
let observer = null

async function load() {
  if (loading.value || !hasMore.value) return
  loading.value = true
  try {
    const data = await getRecommend({ page: page.value + 1, pageSize: PAGE_SIZE })
    page.value = data.page || page.value + 1
    hasMore.value = !!data.has_more
    total.value = Number(data.total) || total.value
    recommendReason.value = data.recommend_reason || recommendReason.value
    list.value = [...list.value, ...(data.list || [])]
  } catch (e) { /* 拦截器提示 */ } finally { loading.value = false }
}

async function refresh() {
  page.value = 0
  hasMore.value = true
  list.value = []
  recommendReason.value = ''
  await load()
}

// 下拉刷新（指针：支持触屏与鼠标）
let pullStartY = null
let pulling = false
const pullDistance = ref(0)
const ENABLE_PULL = true

function onPullStart(e) {
  if (!ENABLE_PULL) return
  if (window.scrollY > 0) return
  pullStartY = e.clientY
  pulling = true
}
function onPullMove(e) {
  if (!pulling || pullStartY == null) return
  const dy = e.clientY - pullStartY
  if (dy <= 0 || window.scrollY > 0) { pullDistance.value = 0; return }
  pullDistance.value = Math.min(120, dy * 0.4)
}
async function onPullEnd() {
  if (!pulling || pullStartY == null) return
  pulling = false
  const d = pullDistance.value
  pullDistance.value = 0
  pullStartY = null
  if (d >= PULL_THRESHOLD) {
    toast('正在刷新')
    await refresh()
  }
}

onMounted(() => {
  observer = new IntersectionObserver((entries) => {
    if (entries[0].isIntersecting) load()
  }, { rootMargin: '120px' })
  if (sentinel.value) observer.observe(sentinel.value)
  refresh()
})
onBeforeUnmount(() => { if (observer) observer.disconnect() })
</script>

<style scoped>
.home { min-height: 100vh; padding-bottom: 36px; }
.welcome-hero { position: relative; display: grid; grid-template-columns: 1.4fr .6fr; gap: 28px; overflow: hidden; margin-bottom: 18px; padding: 34px 38px; border: 1px solid #ecd9b9; border-radius: 30px; background: linear-gradient(135deg,#fff0cb 0%,#f4ebcb 52%,#e5f1dc 100%); box-shadow: 0 14px 40px rgba(93,68,39,.08); }
.hero-copy, .hero-impact { position: relative; z-index: 1; }
.hello-line { margin: 0 0 10px; color: #8b6745; font-size: 14px; font-weight: 800; }
.hero-copy h1 { margin: 0; color: #3f382f; font-size: clamp(29px,3.2vw,42px); line-height: 1.24; letter-spacing: -.045em; }
.hero-note { max-width: 680px; margin: 15px 0 0; color: #776b60; font-size: 15px; line-height: 1.75; }
.hero-tags { display: flex; flex-wrap: wrap; gap: 8px; margin-top: 20px; }
.hero-tags span { padding: 8px 11px; border: 1px solid rgba(77,107,70,.10); border-radius: 13px; background: rgba(255,255,255,.70); color: #576557; font-size: 13px; font-weight: 700; }
.hero-impact { align-self: center; padding: 22px; border: 1px solid rgba(78,113,71,.12); border-radius: 24px; background: rgba(255,255,255,.68); backdrop-filter: blur(8px); }
.impact-icon { font-size: 34px; }
.hero-impact p { margin: 10px 0 2px; color: #687565; font-size: 13px; }
.hero-impact strong { display: block; color: #4e754d; font-size: 33px; line-height: 1.25; }
.hero-impact small { color: #7b8778; font-size: 12px; }
.hero-doodle { position: absolute; opacity: .18; }
.hero-doodle.leaf { right: 24%; top: -26px; font-size: 96px; transform: rotate(12deg); }
.hero-doodle.orange { right: -15px; bottom: -28px; font-size: 100px; }
.stats-grid { display: grid; grid-template-columns: repeat(4,1fr); gap: 12px; margin-bottom: 34px; }
.stats-grid article { display: flex; align-items: center; gap: 12px; min-width: 0; padding: 17px; border: 1px solid #ebe0d2; border-radius: 20px; background: #fff; box-shadow: 0 8px 24px rgba(77,58,38,.05); }
.stat-icon { display: grid; width: 43px; height: 43px; flex: 0 0 43px; place-items: center; border-radius: 15px; font-size: 20px; }
.stat-icon.green { background: #e8f2df; }.stat-icon.orange-bg { background: #fff0cf; }.stat-icon.yellow { background: #fff5dc; }.stat-icon.peach { background: #ffe8de; }
.stats-grid p { margin: 0 0 2px; overflow: hidden; color: #82776d; font-size: 12px; text-overflow: ellipsis; white-space: nowrap; }
.stats-grid strong { color: #443a32; font-size: 18px; white-space: nowrap; }
.home-head { display: flex; align-items: flex-end; justify-content: space-between; gap: 12px; margin-bottom: 18px; }
.head-title { color: #3f382f; font-size: 25px; font-weight: 800; letter-spacing: -.03em; }
.head-reason { color: var(--muted); font-size: 13px; margin-top: 5px; }
.head-refresh { border: 1px solid #e7d9c6; background: #fffdf8; border-radius: 13px; width: 40px; height: 40px; font-size: 20px; cursor: pointer; color: #7a7168; box-shadow: 0 5px 14px rgba(77,58,38,.05); }

.pull-tip {
  height: 0; overflow: hidden; text-align: center; transition: height .15s, opacity .15s;
  color: var(--muted); font-size: 12px;
}
.pull-tip.show { height: 34px; line-height: 34px; }

.masonry { columns: 4; column-gap: 16px; transform: translateZ(0); will-change: transform; }
.sentinel { text-align: center; color: var(--muted); font-size: 12px; padding: 16px 0 8px; }
.no-more { color: #d1d5db; }
@media (max-width: 900px) { .welcome-hero { grid-template-columns: 1fr; } .hero-impact { max-width: 330px; } .stats-grid { grid-template-columns: repeat(2,1fr); } .masonry { columns: 3; } }
@media (max-width: 680px) { .welcome-hero { padding: 26px 22px; border-radius: 24px; } .hero-copy h1 { font-size: 29px; } .hero-impact { padding: 17px; } .stats-grid { gap: 9px; margin-bottom: 28px; } .stats-grid article { padding: 13px; } .stat-icon { width: 38px; height: 38px; flex-basis: 38px; } .stats-grid strong { font-size: 16px; } .masonry { columns: 2; column-gap: 10px; } }
@media (max-width: 420px) { .stats-grid { grid-template-columns: 1fr 1fr; } .stats-grid article { align-items: flex-start; flex-direction: column; gap: 8px; } .hero-tags span { font-size: 12px; } }
</style>
