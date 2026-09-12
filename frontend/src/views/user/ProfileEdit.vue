<template>
  <div class="edit-page">
    <div class="edit-heading">
      <button type="button" @click="$router.back()">← 返回个人中心</button>
    </div>

    <form @submit.prevent="submit">
      <div class="edit-grid">
        <section class="form-card basic-form">
          <header><h3>基本信息</h3><p>更新头像和联系方式</p></header>
          <label class="avatar-up">
            <div class="avatar edit-avatar">
              <img v-if="form.avatar" :src="form.avatar" alt="头像预览" />
              <template v-else>{{ initial }}</template>
            </div>
            <span>点击更换头像</span>
            <input type="file" accept="image/*" hidden @change="onAvatar" />
          </label>
          <label class="field"><span>姓名</span><input class="input" v-model.trim="form.name" /></label>
          <label class="field"><span>联系方式</span><input class="input" inputmode="tel" v-model.trim="form.phone" /></label>
          <label class="field"><span>每月生活费</span><input class="input" type="number" min="0" v-model.number="form.monthly_budget" placeholder="元/月" /></label>
        </section>

        <section class="form-card preference-form">
          <header><h3>饮食偏好</h3><p>可以点选常用标签，也可以输入其他内容</p></header>

          <fieldset class="cuisine-fieldset">
            <legend>饮食爱好</legend>
            <div class="chips">
              <button v-for="option in CUISINE" :key="option" type="button" class="chip" :class="{ active: pref.cuisine.includes(option) }" :aria-pressed="pref.cuisine.includes(option)" @click="toggle(pref.cuisine, option)">{{ option }}</button>
            </div>
            <label class="custom-input"><span>其他饮食爱好</span><input class="input" v-model="cuisineText" placeholder="多个内容请用逗号分隔，如：湘菜、素食" /></label>
          </fieldset>

          <fieldset>
            <legend>常用用餐时段</legend>
            <div class="chips">
              <button v-for="option in MEAL" :key="option" type="button" class="chip" :class="{ active: pref.meal_time.includes(option) }" :aria-pressed="pref.meal_time.includes(option)" @click="toggle(pref.meal_time, option)">{{ option }}</button>
            </div>
          </fieldset>

          <fieldset>
            <legend>喜欢的口味</legend>
            <div class="chips">
              <button v-for="option in TASTE" :key="option" type="button" class="chip" :class="{ active: pref.taste.includes(option) }" :aria-pressed="pref.taste.includes(option)" @click="toggle(pref.taste, option)">{{ option }}</button>
            </div>
          </fieldset>

          <fieldset class="allergen-fieldset">
            <legend>过敏原</legend>
            <div class="chips">
              <button v-for="option in ALLERGEN" :key="option" type="button" class="chip" :class="{ active: taboo.allergens.includes(option) }" :aria-pressed="taboo.allergens.includes(option)" @click="toggle(taboo.allergens, option)">{{ option }}</button>
            </div>
            <label class="custom-input"><span>其他过敏原</span><input class="input" v-model="allergenText" placeholder="多个内容请用逗号分隔；没有可以留空" /></label>
          </fieldset>
        </section>
      </div>

      <div class="save-bar">
        <button type="button" @click="$router.back()">取消</button>
        <button class="save-button" type="submit" :disabled="saving">{{ saving ? '保存中…' : '保存修改' }}</button>
      </div>
    </form>
  </div>
</template>

<script setup>
import { reactive, ref } from 'vue'
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
const cuisineText = ref('')
const allergenText = ref('')

function toggle(list, item) {
  const index = list.indexOf(item)
  if (index >= 0) list.splice(index, 1)
  else list.push(item)
}

function parseList(value) {
  return String(value || '').split(/[,，、\n]/).map(item => item.trim()).filter(Boolean)
}

function uniqueList(values) {
  return [...new Set(values)]
}

function customItems(values, presets) {
  return values.filter(item => !presets.includes(item)).join('，')
}

async function load() {
  const user = await getProfile()
  initial.value = (user.name || '?').charAt(0)
  form.name = user.name || ''
  form.phone = user.phone || ''
  form.avatar = user.avatar || ''
  form.monthly_budget = user.monthly_budget ?? null
  const cuisines = Array.isArray(user.preferences?.cuisine) ? user.preferences.cuisine : []
  const allergens = Array.isArray(user.taboo?.allergens) ? user.taboo.allergens : []
  pref.cuisine = cuisines.filter(item => CUISINE.includes(item))
  pref.taste = Array.isArray(user.preferences?.taste) ? user.preferences.taste.slice() : []
  pref.meal_time = Array.isArray(user.preferences?.meal_time) ? user.preferences.meal_time.slice() : []
  taboo.allergens = allergens.filter(item => ALLERGEN.includes(item))
  taboo.dislikes = Array.isArray(user.taboo?.dislikes) ? user.taboo.dislikes.slice() : []
  cuisineText.value = customItems(cuisines, CUISINE)
  allergenText.value = customItems(allergens, ALLERGEN)
}

function onAvatar(event) {
  const file = event.target.files?.[0]
  if (!file) return
  if (!file.type.startsWith('image/')) { toast('请选择图片文件', 'error'); return }
  if (file.size > 2 * 1024 * 1024) { toast('图片大小不能超过 2MB', 'error'); event.target.value = ''; return }
  const reader = new FileReader()
  reader.onload = () => { form.avatar = String(reader.result || '') }
  reader.readAsDataURL(file)
}

async function submit() {
  if (!form.name) { toast('请填写姓名', 'error'); return }
  if (!/^1\d{10}$/.test(form.phone)) { toast('请输入正确的手机号', 'error'); return }
  saving.value = true
  try {
    await updateProfile({
      name: form.name,
      phone: form.phone,
      avatar: form.avatar,
      monthly_budget: form.monthly_budget,
      preferences: {
        cuisine: uniqueList([...pref.cuisine, ...parseList(cuisineText.value)]),
        taste: pref.taste.slice(),
        meal_time: pref.meal_time.slice()
      },
      taboo: {
        allergens: uniqueList([...taboo.allergens, ...parseList(allergenText.value)]),
        dislikes: taboo.dislikes.slice()
      }
    })
    toast('资料已更新')
    router.push('/profile')
  } catch (e) { /* 请求拦截器统一提示 */ } finally {
    saving.value = false
  }
}

load().catch(() => {})
</script>

<style scoped>
.edit-page { --ink: #17211c; min-height: calc(100vh - 72px); }
.edit-heading { margin-bottom: 16px; }
.edit-heading button { display: inline-flex; align-items: center; min-height: 36px; padding: 7px 10px; border: 1px solid #e6d5c7; border-radius: 7px; background: #fffaf5; color: #a84d25; cursor: pointer; font-size: 13px; font-weight: 650; }
.edit-heading button:hover { border-color: #dda983; background: #fff1e8; }
.edit-heading button:focus-visible { outline: 3px solid rgba(233,121,80,.18); outline-offset: 2px; }
.edit-grid { display: grid; grid-template-areas: 'basic preference'; grid-template-columns: .72fr 1.28fr; gap: 16px; align-items: start; }
.form-card { padding: 21px; border: 1px solid #e7dccf; border-radius: 10px; background: linear-gradient(145deg, rgba(255,250,241,.96), rgba(255,255,255,.92)); box-shadow: 0 10px 28px rgba(78,57,34,.06); }
.basic-form { grid-area: basic; }
.preference-form { display: grid; grid-area: preference; grid-template-columns: 1fr; gap: 18px; border-color: #d9e4d6; background: linear-gradient(145deg, rgba(255,255,255,.94), rgba(241,248,237,.96)); }
.preference-form > header { grid-column: 1 / -1; }
.form-card > header { margin-bottom: 20px; padding-bottom: 15px; border-bottom: 1px solid #edf0ee; }
.form-card > header h3 { margin: 0; font-size: 19px; }.form-card > header p { margin: 2px 0 0; color: #8a938e; font-size: 12px; }
.avatar-up { display: flex; width: max-content; align-items: center; gap: 11px; margin-bottom: 20px; color: #7f8983; cursor: pointer; font-size: 13px; }
.edit-avatar { width: 64px; height: 64px; background: #ed7b45; }
.field, .custom-input { display: block; margin-top: 14px; }.field > span, .custom-input > span { display: block; margin-bottom: 6px; color: #66716b; font-size: 14px; font-weight: 650; }
.field .input, .custom-input .input { min-height: 43px; font-size: 15px; }
fieldset { min-width: 0; margin: 0; padding: 0; border: 0; }.preference-form fieldset + fieldset { padding-top: 0; border-top: 0; }
legend { margin-bottom: 9px; color: #344139; font-size: 14px; font-weight: 750; }
.chips { gap: 7px; }.chip { min-height: 35px; padding: 6px 12px; border-radius: 8px; font-size: 13px; }.chip.active { background: #ed743b; border-color: #ed743b; }
.custom-input { margin-top: 12px; }.custom-input > span { margin-bottom: 5px; color: #8a938e; font-size: 12px; font-weight: 600; }.custom-input .input { min-height: 41px; font-size: 13px; }
.save-bar { display: flex; justify-content: flex-end; gap: 9px; margin-top: 20px; }
.save-bar button { min-width: 92px; padding: 9px 14px; border: 1px solid #dce2de; border-radius: 7px; background: #fff; color: #5f6a64; cursor: pointer; font-size: 14px; }
.save-bar .save-button { border-color: #ed743b; background: #ed743b; color: #fff; font-weight: 700; }.save-bar button:disabled { opacity: .6; cursor: wait; }
@media (max-width: 820px) { .edit-grid { grid-template-areas: 'basic' 'preference'; grid-template-columns: 1fr; } }
@media (max-width: 680px) { .preference-form { grid-template-columns: 1fr; } .preference-form > header { grid-column: auto; } }
@media (max-width: 600px) { .save-bar { position: static; } }
</style>
