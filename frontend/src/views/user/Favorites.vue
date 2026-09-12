<template>
  <div class="favorites-page">
    <header class="page-heading">
      <div>
        <p>FAVORITES</p>
        <h2>我的收藏</h2>
        <span>把喜欢的好食先收好，需要时随时回来看看。</span>
      </div>
      <div class="favorite-count"><strong>{{ favorites.length }}</strong><span>份收藏</span></div>
    </header>

    <div class="tabs favorite-tabs" role="tablist" aria-label="收藏状态">
      <button v-for="tab in tabs" :key="tab.value" class="tab" :class="{ active: currentTab === tab.value }" @click="currentTab = tab.value">
        {{ tab.label }} <span>{{ tabCount(tab.value) }}</span>
      </button>
    </div>

    <div v-if="loading" class="empty">正在整理你的收藏…</div>
    <div v-else-if="!visibleFavorites.length" class="empty-state">
      <div>♡</div>
      <h3>{{ currentTab === 'available' ? '暂时没有可领取的收藏' : '还没有收藏任何好食' }}</h3>
      <p>在商品详情页点击“收藏”，之后就能在这里找到。</p>
      <button class="btn btn-primary" @click="$router.push('/home')">去首页看看</button>
    </div>

    <div v-else class="favorite-grid">
      <article v-for="item in visibleFavorites" :key="item.id" class="favorite-card" :class="{ inactive: !isAvailable(item) }">
        <button class="favorite-cover" type="button" :disabled="!isAvailable(item)" @click="openProduct(item)">
          <img v-if="item.image" :src="item.image" :alt="item.title" />
          <span v-else>{{ item.emoji || '🍱' }}</span>
          <i v-if="!isAvailable(item)">{{ unavailableText(item) }}</i>
        </button>
        <div class="favorite-body">
          <div class="favorite-shop">{{ item.location || '校园周边商家' }}</div>
          <h3>{{ item.title }}</h3>
          <div class="favorite-meta">
            <strong>¥{{ money(item.discount_price) }}</strong>
            <span v-if="item.original_price">¥{{ money(item.original_price) }}</span>
          </div>
          <div class="favorite-actions">
            <button v-if="isAvailable(item)" type="button" @click="openProduct(item)">查看详情</button>
            <button class="remove" type="button" :disabled="removingId === item.id" @click="removeFavorite(item)">
              {{ removingId === item.id ? '正在移除…' : '取消收藏' }}
            </button>
          </div>
        </div>
      </article>
    </div>
  </div>
</template>

<script setup>
import { computed, ref } from 'vue'
import { useRouter } from 'vue-router'
import { getFavorites } from '../../api/user'
import { setFavorite } from '../../api/product'
import { toast } from '../../utils/toast'

const router = useRouter()
const favorites = ref([])
const loading = ref(false)
const removingId = ref(null)
const currentTab = ref('all')
const tabs = [
  { label: '全部', value: 'all' },
  { label: '可领取', value: 'available' },
  { label: '已失效', value: 'inactive' }
]

function isAvailable(item) {
  const expiry = item.expire_time ? new Date(item.expire_time).getTime() : Infinity
  return Number(item.status) === 1 && Number(item.quantity) > 0 && expiry > Date.now()
}

const visibleFavorites = computed(() => {
  if (currentTab.value === 'available') return favorites.value.filter(isAvailable)
  if (currentTab.value === 'inactive') return favorites.value.filter(item => !isAvailable(item))
  return favorites.value
})

function tabCount(value) {
  if (value === 'available') return favorites.value.filter(isAvailable).length
  if (value === 'inactive') return favorites.value.filter(item => !isAvailable(item)).length
  return favorites.value.length
}

function unavailableText(item) {
  if (item.expire_time && new Date(item.expire_time).getTime() <= Date.now()) return '食品已过期'
  if (Number(item.quantity) <= 0 || Number(item.status) === 2) return '已售罄'
  return '已下架'
}

function money(value) {
  const amount = Number(value || 0)
  return Number.isInteger(amount) ? String(amount) : amount.toFixed(2)
}

function openProduct(item) {
  if (isAvailable(item)) router.push(`/product/${item.id}`)
}

async function removeFavorite(item) {
  removingId.value = item.id
  try {
    await setFavorite(item.id, false)
    favorites.value = favorites.value.filter(product => product.id !== item.id)
    toast('已取消收藏')
  } catch (e) { /* 请求拦截器统一提示 */ } finally {
    removingId.value = null
  }
}

async function load() {
  loading.value = true
  try {
    favorites.value = await getFavorites()
  } catch (e) { /* 请求拦截器统一提示 */ } finally {
    loading.value = false
  }
}

load()
</script>

<style scoped>
.favorites-page { --ink: #17211c; }
.page-heading { display: flex; align-items: flex-end; justify-content: space-between; gap: 20px; margin-bottom: 24px; padding: 24px 26px; border-radius: 12px; background: var(--ink); color: #fff; box-shadow: 0 16px 34px rgba(23,33,28,.16); }
.page-heading p { margin: 0 0 3px; color: #98aaa0; font-size: 11px; font-weight: 800; letter-spacing: .08em; }
.page-heading h2 { margin: 0; font-size: 28px; }
.page-heading > div > span { display: block; margin-top: 7px; color: #b8c4bd; font-size: 14px; }
.favorite-count { display: flex; align-items: baseline; gap: 7px; flex-shrink: 0; }
.favorite-count strong { color: #ffad65; font-size: 34px; }
.favorite-count span { color: #c5d0ca; font-size: 13px; }
.favorite-tabs { width: max-content; max-width: 100%; gap: 3px; padding: 4px; border: 1px solid #dfe5e1; border-radius: 9px; background: #fff; }
.favorite-tabs .tab { border: 0; border-radius: 7px; background: transparent; }
.favorite-tabs .tab.active { background: var(--ink); color: #fff; }
.favorite-tabs .tab span { margin-left: 4px; opacity: .65; }
.favorite-grid { display: grid; grid-template-columns: repeat(3,minmax(0,1fr)); gap: 16px; }
.favorite-card { overflow: hidden; border: 1px solid #e0e5e2; border-radius: 12px; background: #fff; box-shadow: 0 8px 24px rgba(31,41,55,.055); }
.favorite-card.inactive { background: #fafafa; }
.favorite-cover { position: relative; display: grid; width: 100%; aspect-ratio: 16/10; overflow: hidden; padding: 0; place-items: center; border: 0; background: #edf0ee; cursor: pointer; font-size: 48px; }
.favorite-cover:disabled { cursor: default; }
.favorite-cover img { width: 100%; height: 100%; object-fit: cover; }
.favorite-cover i { position: absolute; inset: 0; display: grid; place-items: center; background: rgba(23,33,28,.58); color: #fff; font-size: 14px; font-style: normal; font-weight: 800; }
.favorite-body { padding: 16px; }
.favorite-shop { overflow: hidden; color: #8a938e; font-size: 12px; text-overflow: ellipsis; white-space: nowrap; }
.favorite-body h3 { margin: 5px 0 10px; font-size: 17px; }
.favorite-meta { display: flex; align-items: baseline; gap: 8px; }
.favorite-meta strong { color: #e76527; font-size: 20px; }
.favorite-meta span { color: #a4aaa6; font-size: 12px; text-decoration: line-through; }
.favorite-actions { display: flex; gap: 8px; margin-top: 14px; }
.favorite-actions button { flex: 1; padding: 8px 10px; border: 1px solid #d9e0dc; border-radius: 7px; background: #fff; color: #344139; cursor: pointer; }
.favorite-actions button:first-child { border-color: #e9773e; color: #d65f26; }
.favorite-actions button.remove { color: #7b8580; }
.favorite-actions button:disabled { opacity: .55; cursor: wait; }
.empty-state { padding: 70px 20px; text-align: center; }
.empty-state > div { color: #e9895c; font-size: 46px; }
.empty-state h3 { margin: 8px 0 5px; }
.empty-state p { margin: 0 0 18px; color: #7b8580; font-size: 14px; }
@media (max-width: 860px) { .favorite-grid { grid-template-columns: repeat(2,minmax(0,1fr)); } }
@media (max-width: 560px) { .page-heading { align-items: flex-start; flex-direction: column; padding: 21px; } .favorite-grid { grid-template-columns: 1fr; } }
</style>
