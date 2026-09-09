<template>
  <div>
    <div class="card profile-head">
      <div class="avatar">
        <img v-if="user.avatar" :src="user.avatar" alt="" />
        <template v-else>{{ initial }}</template>
      </div>
      <div class="head-info">
        <div class="name">{{ user.name || '-' }}</div>
        <div class="muted">学号：{{ user.student_id || '-' }} ｜ {{ user.school || '-' }}</div>
      </div>
      <button class="btn btn-outline btn-sm" @click="go('/profile/edit')">编辑资料</button>
    </div>

    <div class="card">
      <h3 class="card-title">个人资料</h3>
      <div class="row"><span class="k">联系方式</span><span class="v">{{ user.phone || '-' }}</span></div>
      <div class="row"><span class="k">每月生活费</span><span class="v">{{ user.monthly_budget != null ? '¥' + user.monthly_budget : '-' }}</span></div>
      <div class="row"><span class="k">饮食爱好</span><span class="v tags"><span v-for="t in cuisines" :key="t" class="tag">{{ t }}</span><template v-if="!cuisines.length">-</template></span></div>
      <div class="row"><span class="k">喜欢的口味</span><span class="v tags"><span v-for="t in tastes" :key="t" class="tag">{{ t }}</span><template v-if="!tastes.length">-</template></span></div>
      <div class="row"><span class="k">用餐时段</span><span class="v tags"><span v-for="t in mealTimes" :key="t" class="tag">{{ t }}</span><template v-if="!mealTimes.length">-</template></span></div>
      <div class="row"><span class="k">过敏原</span><span class="v tags"><span v-for="t in allergens" :key="t" class="tag tag-muted">{{ t }}</span><template v-if="!allergens.length">-</template></span></div>
      <div class="row"><span class="k">忌口食物</span><span class="v">{{ dislikes.join('、') || '-' }}</span></div>
    </div>

    <button class="btn btn-primary btn-block" @click="go('/orders')">我的订单</button>
    <div style="height:10px"></div>
    <button class="btn btn-block" @click="logout">退出登录</button>
  </div>
</template>

<script setup>
import { computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../../stores/user'
import { toast } from '../../utils/toast'

const router = useRouter()
const authStore = useAuthStore()
const user = computed(() => authStore.user || {})
const initial = computed(() => (user.value.name || '?').charAt(0))

function arr(v) { return Array.isArray(v) ? v : [] }
const cuisines = computed(() => arr(user.value.preferences?.cuisine))
const tastes = computed(() => arr(user.value.preferences?.taste))
const mealTimes = computed(() => arr(user.value.preferences?.meal_time))
const allergens = computed(() => arr(user.value.taboo?.allergens))
const dislikes = computed(() => arr(user.value.taboo?.dislikes))

function go(path) { router.push(path) }
function logout() {
  toast('已退出登录')
  authStore.logout()
}

onMounted(async () => {
  try { await authStore.refreshProfile() } catch (e) { /* 拦截器处理 */ }
})
</script>

<style scoped>
.profile-head { display: flex; align-items: center; gap: 16px; }
.head-info { flex: 1; }
.name { font-size: 20px; font-weight: 700; }
.muted { color: var(--muted); font-size: 14px; margin-top: 4px; }
.tags { text-align: right; }
</style>