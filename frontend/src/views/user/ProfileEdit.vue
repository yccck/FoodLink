<template>
  <div>
    <button class="btn btn-sm" @click="$router.back()">← 返回</button>
    <h2 class="page-title">修改个人资料</h2>

    <div class="card">
      <div class="row avatar-row">
        <span class="k">头像</span>
        <label class="avatar-up">
          <div class="avatar">
            <img v-if="form.avatar" :src="form.avatar" alt="" />
            <template v-else>{{ initial }}</template>
          </div>
          <span class="up-tip">点击更换头像</span>
          <input type="file" accept="image/*" hidden @change="onAvatar" />
        </label>
      </div>
      <div class="row"><span class="k">姓名</span><input class="input list-input" v-model.trim="form.name" /></div>
      <div class="row"><span class="k">联系方式</span><input class="input list-input" v-model.trim="form.phone" /></div>
      <div class="row"><span class="k">每月生活费</span><input class="input list-input" type="number" min="0" v-model.number="form.monthly_budget" placeholder="元/月" /></div>

      <div class="section-label">饮食爱好</div>
      <div class="chips">
        <span v-for="o in CUISINE" :key="o" class="chip" :class="{ active: pref.cuisine.includes(o) }" @click="toggle(pref.cuisine, o)">{{ o }}</span>
      </div>

      <div class="section-label">喜欢的口味</div>
      <div class="chips">
        <span v-for="o in TASTE" :key="o" class="chip" :class="{ active: pref.taste.includes(o) }" @click="toggle(pref.taste, o)">{{ o }}</span>
      </div>

      <div class="section-label">常用用餐时段</div>
      <div class="chips">
        <span v-for="o in MEAL" :key="o" class="chip" :class="{ active: pref.meal_time.includes(o) }" @click="toggle(pref.meal_time, o)">{{ o }}</span>
      </div>

      <div class="section-label">过敏原</div>
      <div class="chips">
        <span v-for="o in ALLERGEN" :key="o" class="chip" :class="{ active: taboo.allergens.includes(o) }" @click="toggle(taboo.allergens, o)">{{ o }}</span>
      </div>

      <div class="section-label">忌口食物</div>
      <input class="input" v-model="dislikeText" placeholder="多个用逗号分隔，如：香菜,苦瓜" />
    </div>

    <button class="btn btn-primary btn-block" :disabled="saving" @click="submit">{{ saving ? '保存中…' : '保存修改' }}</button>
    <div style="height:16px"></div>
  </div>
</template>

<script setup>
import { reactive, ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { getProfile, updateProfile } from '../../api/user'
import { toast } from '../../utils/toast'

const CUISINE = ['川菜', '粤菜', '西餐', '日料', '烘焙', '家常菜']
const TASTE = ['麻辣', '酸甜', '清淡', '重口']
const MEAL = ['早餐', '午餐', '晚餐', '夜宵']
const ALLERGEN = ['花生', '海鲜', '乳制品', '麸质', '坚果']

const router = useRouter()
const saving = ref(false)
const initial = ref('?')
const form = reactive({ name: '', phone: '', avatar: '', monthly_budget: null })
const pref = reactive({ cuisine: [], taste: [], meal_time: [] })
const taboo = reactive({ allergens: [], dislikes: [] })
const dislikeText = ref('')

function toggle(list, item) {
  const i = list.indexOf(item)
  if (i >= 0) list.splice(i, 1)
  else list.push(item)
}

async function load() {
  const u = await getProfile()
  initial.value = (u.name || '?').charAt(0)
  form.name = u.name || ''
  form.phone = u.phone || ''
  form.avatar = u.avatar || ''
  form.monthly_budget = u.monthly_budget ?? null
  pref.cuisine = (u.preferences?.cuisine || []).slice()
  pref.taste = (u.preferences?.taste || []).slice()
  pref.meal_time = (u.preferences?.meal_time || []).slice()
  taboo.allergens = (u.taboo?.allergens || []).slice()
  taboo.dislikes = (u.taboo?.dislikes || []).slice()
  dislikeText.value = taboo.dislikes.join('，')
}

function onAvatar(e) {
  const file = e.target.files && e.target.files[0]
  if (!file) return
  if (file.size > 2 * 1024 * 1024) { toast('图片过大（最大2MB）', 'error'); e.target.value = ''; return }
  const reader = new FileReader()
  reader.onload = () => { form.avatar = reader.result }
  reader.readAsDataURL(file)
}

async function submit() {
  if (!form.name) { toast('请填写姓名', 'error'); return }
  if (!/^1\d{10}$/.test(form.phone)) { toast('请输入正确的手机号', 'error'); return }
  taboo.dislikes = dislikeText.value.split(/[,，]/).map(s => s.trim()).filter(Boolean)
  saving.value = true
  try {
    await updateProfile({
      name: form.name,
      phone: form.phone,
      avatar: form.avatar,
      monthly_budget: form.monthly_budget,
      preferences: { ...pref },
      taboo: { ...taboo }
    })
    toast('资料已更新')
    router.back()
  } catch (e) { /* 拦截器处理 */ } finally { saving.value = false }
}

load().catch(() => {})
</script>

<style scoped>
.page-title { margin: 4px 0 16px; }
.avatar-row { align-items: flex-start; padding: 6px 0; }
.avatar-up { display: flex; flex-direction: column; align-items: center; gap: 6px; cursor: pointer; }
.up-tip { font-size: 12px; color: var(--muted); }
.list-input { width: auto; max-width: 240px; padding: 6px 10px; }
</style>