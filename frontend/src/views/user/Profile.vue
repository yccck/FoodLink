<template>
  <div class="profile-page">
    <section class="profile-summary">
      <div class="summary-person">
        <div class="avatar profile-avatar">
          <img v-if="user.avatar" :src="user.avatar" alt="个人头像" />
          <template v-else>{{ initial }}</template>
        </div>
        <div>
          <p>PERSONAL CENTER</p>
          <h2>{{ user.name || '同学' }}</h2>
          <span>学号 {{ user.student_id || '-' }} · {{ user.school || '学校信息未填写' }}</span>
        </div>
      </div>
      <button class="edit-button" type="button" @click="go('/profile/edit')">编辑资料</button>
    </section>

    <section class="quick-grid" aria-label="个人中心快捷入口">
      <button type="button" @click="go('/orders')">
        <span class="quick-icon orange">🧾</span>
        <span><strong>我的订单</strong><small>查看购买与领取记录</small></span>
        <i>›</i>
      </button>
      <button type="button" @click="go('/favorites')">
        <span class="quick-icon green">♡</span>
        <span><strong>我的收藏</strong><small>找回收藏过的好食</small></span>
        <i>›</i>
      </button>
    </section>

    <div class="profile-grid">
      <section class="profile-card">
        <header><div><p>基本信息</p><span>你的校园身份与联系方式</span></div></header>
        <dl>
          <div><dt>姓名</dt><dd>{{ user.name || '-' }}</dd></div>
          <div><dt>联系方式</dt><dd>{{ user.phone || '-' }}</dd></div>
          <div><dt>学校</dt><dd>{{ user.school || '-' }}</dd></div>
          <div><dt>每月生活费</dt><dd>{{ user.monthly_budget != null ? '¥' + user.monthly_budget : '-' }}</dd></div>
        </dl>
      </section>

      <section class="profile-card preference-card">
        <header><div><p>饮食偏好</p><span>用于改善首页推荐结果</span></div></header>
        <div class="preference-group">
          <strong>饮食爱好</strong>
          <div class="tag-list"><span v-for="t in cuisines" :key="t">{{ t }}</span><em v-if="!cuisines.length">暂未填写</em></div>
        </div>
        <div class="preference-group">
          <strong>喜欢的口味</strong>
          <div class="tag-list"><span v-for="t in tastes" :key="t">{{ t }}</span><em v-if="!tastes.length">暂未填写</em></div>
        </div>
        <div class="preference-group">
          <strong>常用用餐时段</strong>
          <div class="tag-list"><span v-for="t in mealTimes" :key="t">{{ t }}</span><em v-if="!mealTimes.length">暂未填写</em></div>
        </div>
        <div class="preference-group allergen-group">
          <strong>过敏原</strong>
          <div class="tag-list"><span v-for="t in allergens" :key="t">{{ t }}</span><em v-if="!allergens.length">无或暂未填写</em></div>
        </div>
      </section>
    </div>

    <button class="logout-wide" type="button" @click="logout">退出当前账号</button>
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

function arr(value) { return Array.isArray(value) ? value : [] }
const cuisines = computed(() => arr(user.value.preferences?.cuisine))
const tastes = computed(() => arr(user.value.preferences?.taste))
const mealTimes = computed(() => arr(user.value.preferences?.meal_time))
const allergens = computed(() => arr(user.value.taboo?.allergens))

function go(path) { router.push(path) }
function logout() {
  toast('已退出登录')
  authStore.logout()
}

onMounted(async () => {
  try { await authStore.refreshProfile() } catch (e) { /* 请求拦截器统一提示 */ }
})
</script>

<style scoped>
.profile-page { --ink: #17211c; }
.profile-summary { display: flex; align-items: center; justify-content: space-between; gap: 22px; margin-bottom: 18px; padding: 25px 27px; border-radius: 18px; background: linear-gradient(135deg,#fff0cb 0%,#f4ebcb 52%,#e5f1dc 100%); border: 1px solid #ecd9b9; color: #2e3a34; box-shadow: 0 14px 34px rgba(93,68,39,.08); }
.summary-person { display: flex; align-items: center; gap: 17px; min-width: 0; }
.profile-avatar { width: 72px; height: 72px; flex: 0 0 72px; border: 3px solid rgba(255,255,255,.15); background: #ed7b45; }
.summary-person p { margin: 0 0 2px; color: #a06a2f; font-size: 11px; font-weight: 800; letter-spacing: .08em; }
.summary-person h2 { margin: 0; font-size: 28px; color: #2e3a34; }
.summary-person span { display: block; margin-top: 5px; color: #6c7a72; font-size: 14px; }
.edit-button { flex-shrink: 0; padding: 9px 15px; border: 1px solid #16a34a; border-radius: 8px; background: #16a34a; color: #fff; cursor: pointer; font-size: 14px; font-weight: 600; }
.edit-button:hover { background: #15803d; }
.quick-grid { display: grid; grid-template-columns: repeat(2,minmax(0,1fr)); gap: 14px; margin-bottom: 18px; }
.quick-grid button { display: flex; align-items: center; gap: 13px; padding: 16px 18px; border: 1px solid #e0e5e2; border-radius: 10px; background: #fff; color: #26332b; cursor: pointer; text-align: left; box-shadow: 0 7px 20px rgba(31,41,55,.045); }
.quick-grid button:hover { border-color: #c9d5ce; transform: translateY(-1px); }
.quick-icon { display: grid; width: 44px; height: 44px; flex: 0 0 44px; place-items: center; border-radius: 10px; font-size: 21px; font-style: normal; }
.quick-icon.orange { background: #fff0e6; }.quick-icon.green { background: #e4f2e9; color: #17633a; font-size: 29px; }
.quick-grid button > span:nth-child(2) { display: flex; min-width: 0; flex: 1; flex-direction: column; }
.quick-grid strong { font-size: 15px; }.quick-grid small { margin-top: 2px; color: #8a938e; font-size: 12px; }
.quick-grid i { color: #a5ada8; font-size: 24px; font-style: normal; }
.profile-grid { display: grid; grid-template-columns: .85fr 1.15fr; gap: 16px; }
.profile-card { padding: 20px 22px; border: 1px solid #e0e5e2; border-radius: 10px; background: #fff; box-shadow: 0 7px 20px rgba(31,41,55,.04); }
.profile-card header { margin-bottom: 14px; padding-bottom: 13px; border-bottom: 1px solid #edf0ee; }
.profile-card header p { margin: 0; color: #243129; font-size: 19px; font-weight: 800; }
.profile-card header span { color: #909993; font-size: 12px; }
.profile-card dl { margin: 0; }
.profile-card dl div { display: flex; justify-content: space-between; gap: 20px; padding: 12px 0; border-bottom: 1px dashed #e7ebe8; }
.profile-card dl div:last-child { border-bottom: 0; }
.profile-card dt { color: #8a938e; font-size: 14px; }.profile-card dd { margin: 0; color: #243129; font-size: 14px; font-weight: 650; text-align: right; }
.preference-group { display: grid; grid-template-columns: 110px minmax(0,1fr); align-items: start; gap: 12px; padding: 10px 0; }
.preference-group > strong { color: #66716b; font-size: 14px; }
.tag-list { display: flex; flex-wrap: wrap; gap: 6px; }
.tag-list span { padding: 4px 10px; border-radius: 999px; background: #fff0df; color: #a75021; font-size: 13px; }
.allergen-group .tag-list span { background: #eef1f3; color: #5e6a64; }
.tag-list em { color: #a2aaa5; font-size: 13px; font-style: normal; }
.logout-wide { display: block; margin: 18px 0 0 auto; padding: 8px 12px; border: 0; background: transparent; color: #9b4e43; cursor: pointer; font-size: 13px; }
@media (max-width: 760px) { .profile-grid { grid-template-columns: 1fr; } }
@media (max-width: 560px) { .profile-summary { align-items: flex-start; flex-direction: column; padding: 21px; } .quick-grid { grid-template-columns: 1fr; } .summary-person { align-items: flex-start; } .preference-group { grid-template-columns: 1fr; gap: 6px; } }
</style>
