<template>
  <div class="edit-page">
    <header class="edit-heading">
      <div>
        <button type="button" @click="$router.back()">← 返回个人中心</button>
        <p>PROFILE SETTINGS</p>
        <h2>修改个人资料</h2>
      </div>
      <span>完善偏好后，首页推荐会更贴近你的需要。</span>
    </header>

    <form @submit.prevent="submit">
      <div class="edit-grid">
        <section class="form-card">
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

          <fieldset>
            <legend>饮食爱好</legend>
            <div class="chips">
              <button v-for="option in CUISINE" :key="option" type="button" class="chip" :class="{ active: pref.cuisine.includes(option) }" :aria-pressed="pref.cuisine.includes(option)" @click="toggle(pref.cuisine, option)">{{ option }}</button>
            </div>
            <label class="custom-input"><span>其他饮食爱好</span><input class="input" v-model="cuisineText" placeholder="多个内容请用逗号分隔，如：湘菜、素食" /></label>
          </fieldset>

          <fieldset>
            <legend>喜欢的口味</legend>
            <div class="chips">
              <button v-for="option in TASTE" :key="option" type="button" class="chip" :class="{ active: pref.taste.includes(option) }" :aria-pressed="pref.taste.includes(option)" @click="toggle(pref.taste, option)">{{ option }}</button>
            </div>
          </fieldset>

          <fieldset>
            <legend>常用用餐时段</legend>
            <div class="chips">
              <button v-for="option in MEAL" :key="option" type="button" class="chip" :class="{ active: pref.meal_time.includes(option) }" :aria-pressed="pref.meal_time.includes(option)" @click="toggle(pref.meal_time, option)">{{ option }}</button>
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
.edit-page { --ink: #17211c; }
.edit-heading { display: flex; align-items: flex-end; justify-content: space-between; gap: 22px; margin-bottom: 18px; padding: 23px 25px; border-radius: 12px; background: var(--ink); color: #fff; box-shadow: 0 16px 34px rgba(23,33,28,.16); }
.edit-heading button { margin-bottom: 14px; padding: 0; border: 0; background: transparent; color: #f5a675; cursor: pointer; font-size: 13px; }
.edit-heading p { margin: 0 0 2px; color: #96a89e; font-size: 10px; font-weight: 800; letter-spacing: .08em; }
.edit-heading h2 { margin: 0; font-size: 27px; }.edit-heading > span { max-width: 360px; color: #bdc8c2; font-size: 14px; text-align: right; }
.edit-grid { display: grid; grid-template-columns: .72fr 1.28fr; gap: 16px; align-items: start; }
.form-card { padding: 21px; border: 1px solid #e0e5e2; border-radius: 10px; background: #fff; box-shadow: 0 7px 20px rgba(31,41,55,.04); }
.form-card > header { margin-bottom: 18px; padding-bottom: 13px; border-bottom: 1px solid #edf0ee; }
.form-card > header h3 { margin: 0; font-size: 19px; }.form-card > header p { margin: 2px 0 0; color: #8a938e; font-size: 12px; }
.avatar-up { display: flex; width: max-content; align-items: center; gap: 11px; margin-bottom: 20px; color: #7f8983; cursor: pointer; font-size: 13px; }
.edit-avatar { width: 64px; height: 64px; background: #ed7b45; }
.field, .custom-input { display: block; margin-top: 14px; }.field > span, .custom-input > span { display: block; margin-bottom: 6px; color: #66716b; font-size: 14px; font-weight: 650; }
.field .input, .custom-input .input { min-height: 43px; font-size: 15px; }
fieldset { margin: 0; padding: 0 0 19px; border: 0; }.preference-form fieldset + fieldset { padding-top: 17px; border-top: 1px dashed #e1e6e3; }
legend { margin-bottom: 10px; color: #344139; font-size: 15px; font-weight: 750; }
.chips { gap: 7px; }.chip { min-height: 36px; padding: 7px 13px; border-radius: 8px; font-size: 14px; }.chip.active { background: #1f6b45; border-color: #1f6b45; }
.allergen-fieldset .chip.active { background: #59665f; border-color: #59665f; }
.custom-input { margin-top: 12px; }.custom-input > span { color: #8a938e; font-size: 13px; font-weight: 600; }
.save-bar { display: flex; justify-content: flex-end; gap: 9px; margin-top: 16px; padding: 13px 15px; border: 1px solid #e0e5e2; border-radius: 9px; background: #fff; }
.save-bar button { min-width: 92px; padding: 9px 14px; border: 1px solid #dce2de; border-radius: 7px; background: #fff; color: #5f6a64; cursor: pointer; font-size: 14px; }
.save-bar .save-button { border-color: #ed743b; background: #ed743b; color: #fff; font-weight: 700; }.save-bar button:disabled { opacity: .6; cursor: wait; }
@media (max-width: 820px) { .edit-grid { grid-template-columns: 1fr; } }
@media (max-width: 600px) { .edit-heading { align-items: flex-start; flex-direction: column; padding: 21px; }.edit-heading > span { text-align: left; }.save-bar { position: sticky; bottom: 10px; } }
</style>
