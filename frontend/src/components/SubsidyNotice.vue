<template>
  <div class="subsidy-entry">
    <button
      class="bulb-btn"
      type="button"
      :class="{ has: unread > 0 }"
      :title="unread > 0 ? `你有 ${unread} 条优惠通知` : '我的优惠通知'"
      :aria-label="unread > 0 ? `你有 ${unread} 条优惠通知` : '我的优惠通知'"
      @click="toggle"
    >
      <svg viewBox="0 0 24 24" width="19" height="19" aria-hidden="true">
        <path
          d="M12 2.6a6.2 6.2 0 0 0-3.6 11.2c.5.4.8 1 .8 1.6v.6h5.6v-.6c0-.6.3-1.2.8-1.6A6.2 6.2 0 0 0 12 2.6z"
          fill="currentColor"
        />
        <rect x="9.4" y="17.4" width="5.2" height="1.8" rx=".9" fill="currentColor" />
        <rect x="10.5" y="20" width="3" height="1.7" rx=".85" fill="currentColor" />
      </svg>
      <span v-if="unread > 0" class="badge">{{ unread > 99 ? '99+' : unread }}</span>
    </button>

    <div v-if="open" class="notice-panel">
      <div class="panel-head">
        <span>我的优惠通知</span>
        <span v-if="unread" class="unread-tip">{{ unread }} 条未读</span>
        <button class="panel-close" type="button" aria-label="关闭" @click="open = false">×</button>
      </div>

      <div class="panel-body">
        <div class="reward-account">
          <div>
            <span>奖励金账户</span>
            <small>下单时自动优先抵扣</small>
          </div>
          <strong>¥{{ money(rewardBalance) }}</strong>
        </div>
        <div v-if="!list.length" class="empty">
          <div class="empty-icon">💡</div>
          <p>暂无优惠通知</p>
          <p class="empty-sub">管理员发放优惠后，这里会第一时间收到提醒</p>
        </div>

        <div v-for="n in list" :key="n.id" class="notice-item" :class="{ read: n.is_read }">
          <div class="n-top">
            <span class="n-tag">🎉 {{ n.title || '本月暖心帮扶对象' }}</span>
            <span v-if="n.is_read" class="n-read-tag">已读</span>
            <span class="n-time">{{ n.created_at }}</span>
          </div>
          <p class="n-msg">亲爱的{{ name }}，感谢您的忠诚使用，为您发放优惠额度！</p>
          <div class="n-amt">¥{{ money(n.amount) }}</div>
          <div class="n-actions">
            <span class="n-tip">奖励金已存入账户，下单可直接使用</span>
            <button v-if="!n.is_read" class="n-ok" type="button" @click="read(n)">知道啦</button>
          </div>
        </div>
      </div>

      <button v-if="unread > 1" class="read-all" type="button" @click="readAll">全部标记已读</button>
    </div>
  </div>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import { useAuthStore } from '../stores/user'
import { getSubsidyNotices, readSubsidyNotice } from '../api/user'

const authStore = useAuthStore()
const list = ref([])
const open = ref(false)
let timer = null

const unread = computed(() => list.value.filter(n => !n.is_read).length)
const name = computed(() => authStore.user?.name || '同学')
const rewardBalance = computed(() => Number(authStore.user?.reward_balance || 0))

function money(v) {
  return Number(v || 0).toFixed(2)
}

async function load() {
  if (!authStore.isLoggedIn || authStore.user?.role !== 1) return
  const [notices] = await Promise.allSettled([
    getSubsidyNotices(),
    authStore.refreshProfile()
  ])
  if (notices.status === 'fulfilled') {
    list.value = Array.isArray(notices.value) ? notices.value : []
  }
}

function toggle() {
  open.value = !open.value
  if (open.value) load()
}

function onDocClick(e) {
  if (!open.value) return
  if (!e.target.closest || !e.target.closest('.subsidy-entry')) open.value = false
}

async function read(n) {
  n.is_read = 1
  try { await readSubsidyNotice(n.id) } catch (e) { /* 忽略 */ }
}

async function readAll() {
  const all = list.value.filter(n => !n.is_read)
  all.forEach(n => { n.is_read = 1 })
  for (const n of all) {
    try { await readSubsidyNotice(n.id) } catch (e) { /* 忽略 */ }
  }
}

onMounted(() => {
  load()
  document.addEventListener('click', onDocClick)
  // 管理端发放后自动更新小红点，无需刷新页面
  timer = setInterval(load, 30000)
})
onBeforeUnmount(() => {
  document.removeEventListener('click', onDocClick)
  if (timer) clearInterval(timer)
})
defineExpose({ load })
</script>

<style scoped>
.subsidy-entry { position: relative; display: inline-flex; align-items: center; }

.bulb-btn {
  position: relative;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 34px;
  height: 34px;
  margin: 0 2px;
  padding: 0;
  border: 1px solid #e8dfd2;
  border-radius: 999px;
  background: #fffdf8;
  color: #b3a795;
  cursor: pointer;
  transition: all .18s ease;
}
.bulb-btn:hover { border-color: #f0c98a; color: #d99b3f; background: #fff8ea; }
.bulb-btn.has {
  color: #f0a63a;
  border-color: #f5cf8d;
  background: linear-gradient(135deg, #fff6e2, #ffe9c4);
  box-shadow: 0 0 0 3px rgba(245, 190, 110, .18);
  animation: glow 1.8s ease-in-out infinite;
}
@keyframes glow {
  0%, 100% { box-shadow: 0 0 0 3px rgba(245, 190, 110, .18); }
  50% { box-shadow: 0 0 0 6px rgba(245, 190, 110, .10); }
}
.badge {
  position: absolute;
  top: -4px;
  right: -4px;
  min-width: 16px;
  height: 16px;
  padding: 0 4px;
  border-radius: 999px;
  background: #e2543d;
  color: #fff;
  font-size: 10px;
  font-weight: 800;
  line-height: 16px;
  text-align: center;
}

.notice-panel {
  position: fixed;
  top: 62px;
  right: 14px;
  z-index: 120;
  width: min(330px, calc(100vw - 24px));
  max-height: 70vh;
  display: flex;
  flex-direction: column;
  border-radius: 16px;
  background: #fffdf8;
  border: 1px solid #f3e2c7;
  box-shadow: 0 18px 46px rgba(70, 50, 30, .22);
  overflow: hidden;
  animation: pop .18s ease-out;
}
@keyframes pop {
  from { opacity: 0; transform: translateY(-8px); }
  to { opacity: 1; transform: none; }
}
.panel-head {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 14px;
  border-bottom: 1px solid #f4ead9;
  font-size: 14px;
  font-weight: 800;
  color: #4b4034;
}
.unread-tip { font-size: 12px; font-weight: 600; color: #d9623d; }
.panel-close {
  margin-left: auto;
  border: 0;
  background: transparent;
  font-size: 20px;
  line-height: 1;
  color: #b3a795;
  cursor: pointer;
}
.panel-body { padding: 10px 12px; overflow-y: auto; }
.reward-account { display: flex; align-items: center; justify-content: space-between; gap: 12px; margin-bottom: 10px; padding: 11px 12px; border: 1px solid #f1d8ae; border-radius: 10px; background: #fff8e9; }
.reward-account div { display: flex; min-width: 0; flex-direction: column; }
.reward-account span { color: #5c5145; font-size: 13px; font-weight: 750; }
.reward-account small { margin-top: 2px; color: #a2978a; font-size: 10px; }
.reward-account strong { flex-shrink: 0; color: #d65f14; font-size: 20px; font-variant-numeric: tabular-nums; }

.empty { padding: 26px 0; text-align: center; color: #a2978a; font-size: 13px; }
.empty-icon { font-size: 30px; margin-bottom: 6px; }
.empty p { margin: 0; }
.empty-sub { margin-top: 6px !important; font-size: 11px; color: #bcb2a4; line-height: 1.5; }

.notice-item {
  padding: 12px;
  margin-bottom: 10px;
  border-radius: 14px;
  background: linear-gradient(135deg, #fff8ec, #fff1dc);
  border: 1px solid #f6e3c2;
}
.notice-item:last-child { margin-bottom: 0; }
.notice-item.read {
  background: #faf8f4;
  border-color: #eee8de;
}
.notice-item.read .n-tag { color: #8a8378; }
.n-read-tag {
  padding: 1px 6px;
  border-radius: 999px;
  background: #ece7de;
  color: #9c9486;
  font-size: 10px;
}
.n-top { display: flex; align-items: center; gap: 8px; margin-bottom: 8px; }
.n-tag { font-size: 13px; font-weight: 800; color: #2f7d55; }
.n-time { margin-left: auto; font-size: 11px; color: #a99c8b; }
.n-msg { margin: 0 0 8px; font-size: 13px; line-height: 1.6; color: #5c5145; }
.n-amt {
  margin-bottom: 10px;
  padding: 10px;
  border-radius: 12px;
  background: linear-gradient(135deg, #fff1d6, #ffe3bd);
  color: #d9623d;
  font-size: 18px;
  font-weight: 800;
  text-align: center;
}
.notice-item.read .n-amt { background: #f1ece3; color: #9c9486; }
.notice-item.read .n-msg { color: #8f8779; }
.n-actions { display: flex; align-items: center; gap: 8px; }
.n-tip { flex: 1; font-size: 11px; color: #9a8f80; line-height: 1.4; }
.n-ok {
  flex: none;
  min-height: 32px;
  padding: 0 14px;
  border: 0;
  border-radius: 999px;
  background: #2f7d55;
  color: #fff;
  font-size: 13px;
  font-weight: 800;
  cursor: pointer;
}
.n-ok:hover { opacity: .92; }

.read-all {
  border: 0;
  border-top: 1px solid #f4ead9;
  padding: 11px;
  background: #fffdf8;
  color: #8a7f70;
  font-size: 13px;
  cursor: pointer;
}
.read-all:hover { background: #faf4e9; color: #5c5145; }

@media (max-width: 540px) {
  .notice-panel { top: 56px; right: 10px; left: 10px; width: auto; }
}
</style>
