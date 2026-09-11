<template>
  <div class="home" @pointerdown="onPullStart" @pointermove="onPullMove" @pointerup="onPullEnd" @pointercancel="onPullEnd">
    <div class="home-head">
      <div class="head-left">
        <div class="head-title">✨ 为你推荐</div>
        <div class="head-reason">{{ recommendReason || '基于你的偏好与历史行为推荐' }}</div>
      </div>
      <button class="head-refresh" title="刷新" @click="refresh">⟳</button>
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
import { ref, onMounted, onBeforeUnmount } from 'vue'
import ProductCard from '../../components/ProductCard.vue'
import { getRecommend } from '../../api/recommend'
import { toast } from '../../utils/toast'

const PAGE_SIZE = 6
const PULL_THRESHOLD = 70

const list = ref([])
const page = ref(0)
const hasMore = ref(true)
const loading = ref(false)
const recommendReason = ref('')

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
.home { min-height: 100vh; }
.home-head { display: flex; align-items: flex-start; justify-content: space-between; gap: 12px; margin-bottom: 16px; }
.head-title { font-size: 22px; font-weight: 800; }
.head-reason { color: var(--muted); font-size: 12px; margin-top: 4px; }
.head-refresh { border: 1px solid var(--border); background: #fff; border-radius: 8px; width: 34px; height: 34px; font-size: 18px; cursor: pointer; color: var(--muted); }

.pull-tip {
  height: 0; overflow: hidden; text-align: center; transition: height .15s, opacity .15s;
  color: var(--muted); font-size: 12px;
}
.pull-tip.show { height: 34px; line-height: 34px; }

.masonry { columns: 4; column-gap: 14px; }
.sentinel { text-align: center; color: var(--muted); font-size: 12px; padding: 16px 0 8px; }
.no-more { color: #d1d5db; }
</style>