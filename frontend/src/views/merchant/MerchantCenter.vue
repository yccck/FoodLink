<template>
  <div class="center-page">

    <div class="tabs center-tabs" role="tablist">
      <button class="tab" :class="{ active: tab === 'orders' }" @click="tab = 'orders'">订单管理</button>
      <button class="tab" :class="{ active: tab === 'shop' }" @click="tab = 'shop'">店铺信息</button>
    </div>

    <!-- 店铺信息 -->
    <section v-if="tab === 'shop'" class="shop-tab">
      <div v-if="loading" class="empty">加载中…</div>

      <template v-else>
        <!-- 待审核提示 -->
        <div v-if="profile.pending" class="pending-banner">
          ⏳ 资料更新正在等待超管审核，审核通过后生效
        </div>

        <!-- 编辑表单 -->
        <div v-if="editing" class="card edit-card">
          <h3 class="card-title">编辑店铺资料</h3>
          <label class="field"><span>店铺名称</span><input class="input" v-model.trim="form.shop_name" placeholder="请输入店铺名称" /></label>
          <label class="field"><span>联系人</span><input class="input" v-model.trim="form.name" placeholder="请输入联系人姓名" /></label>
          <label class="field"><span>联系方式</span><input class="input" v-model.trim="form.phone" placeholder="请输入手机号" /></label>
          <label class="field"><span>取货点 / 地址</span><input class="input" v-model.trim="form.location" placeholder="请输入取货点地址" /></label>

          <label class="field">
            <span>营业执照</span>
            <input class="input" type="file" accept="image/*" @change="onLicense" />
            <img v-if="form.license_img" class="license-preview" :src="form.license_img" alt="营业执照预览" />
          </label>

          <div class="field">
            <span>经营品类</span>
            <div class="chip-pool">
              <button v-for="cat in CATEGORIES" :key="cat" type="button" class="chip"
                :class="{ on: form.categories.includes(cat) }" @click="toggleCat(cat)">{{ cat }}</button>
            </div>
          </div>

          <div class="edit-actions">
            <button class="btn btn-sm" @click="editing = false">取消</button>
            <button class="save-button" type="button" :disabled="saving" @click="save">{{ saving ? '提交中…' : '提交待审核' }}</button>
          </div>
        </div>

        <!-- 查看信息 -->
        <template v-else>
          <div class="card info-card">
            <div class="info-row"><span>店铺状态</span><em class="badge" :class="profile.pending ? 'pending' : 'ok'">{{ profile.pending ? '待审核' : '已生效' }}</em></div>
            <div class="info-row"><span>店铺名称</span><strong>{{ infoOf('shop_name') }}</strong></div>
            <div class="info-row"><span>联系人</span><strong>{{ infoOf('name') }}</strong></div>
            <div class="info-row"><span>联系方式</span><strong>{{ infoOf('phone') }}</strong></div>
            <div class="info-row"><span>取货点 / 地址</span><strong>{{ infoOf('location') }}</strong></div>
            <div class="info-row"><span>经营品类</span><strong><span v-for="c in catsOf()" :key="c" class="cat-tag">{{ c }}</span></strong></div>
            <button class="btn btn-primary center-edit" @click="startEdit">编辑资料</button>
          </div>

          <div v-if="profile.pending" class="card info-card pending-old">
            <h4>当前生效信息</h4>
            <div class="info-row"><span>店铺名称</span><strong>{{ profile.shop_name }}</strong></div>
            <div class="info-row"><span>联系人</span><strong>{{ profile.name }}</strong></div>
            <div class="info-row"><span>联系方式</span><strong>{{ profile.phone }}</strong></div>
            <div class="info-row"><span>经营品类</span><strong><span v-for="c in profile.categories" :key="c" class="cat-tag">{{ c }}</span></strong></div>
          </div>
        </template>
      </template>
    </section>

    <!-- 订单管理 -->
    <MerchantOrders v-else-if="tab === 'orders'" embedded />
  </div>
</template>

<script setup>
import { reactive, ref, computed } from 'vue'
import { getMerchantProfile, updateMerchantProfile } from '../../api/merchant'
import { toast } from '../../utils/toast'
import MerchantOrders from './MerchantOrders.vue'

const CATEGORIES = [
  '中式快餐', '家常菜', '面食', '粥粉', '夜宵',
  '甜品饮品', '咖啡茶饮', '烘焙糕点', '果切果汁',
  '熟食卤味', '烧烤炸串', '麻辣烫', '火锅',
  '日料寿司', '韩式餐饮', '西式简餐', '意面披萨', '轻食沙拉',
  '煎饼炸物', '便利店零食'
]

const tab = ref('orders')
const loading = ref(false)
const saving = ref(false)
const editing = ref(false)
const profile = ref({ shop_name: '', name: '', phone: '', location: '', license_img: '', categories: [], pending: null })
const form = reactive({ shop_name: '', name: '', phone: '', location: '', license_img: '', categories: [] })

const pending = computed(() => profile.value.pending)
function infoOf(key) {
  return pending.value ? pending.value[key] : profile.value[key]
}
function catsOf() {
  return pending.value ? pending.value.categories : profile.value.categories
}

function onLicense(e) {
  const file = e.target.files && e.target.files[0]
  if (!file) return
  const reader = new FileReader()
  reader.onload = () => { form.license_img = reader.result }
  reader.readAsDataURL(file)
}
function toggleCat(cat) {
  const i = form.categories.indexOf(cat)
  if (i >= 0) form.categories.splice(i, 1)
  else form.categories.push(cat)
}

async function load() {
  loading.value = true
  try { profile.value = await getMerchantProfile() } catch (e) { /* 拦截器 */ } finally { loading.value = false }
}

function startEdit() {
  const src = pending.value || profile.value
  form.shop_name = src.shop_name || ''
  form.name = src.name || ''
  form.phone = src.phone || ''
  form.location = src.location || ''
  form.license_img = src.license_img || ''
  form.categories = (Array.isArray(src.categories) ? src.categories : []).slice()
  editing.value = true
}

async function save() {
  if (!form.shop_name.trim() || !form.name.trim() || !form.phone.trim() || !form.location.trim()) {
    toast('请填写完整店铺资料', 'error'); return
  }
  if (!/^1\d{10}$/.test(form.phone)) { toast('请输入正确的手机号', 'error'); return }
  saving.value = true
  try {
    await updateMerchantProfile({
      shop_name: form.shop_name, name: form.name, phone: form.phone, location: form.location,
      license_img: form.license_img, categories: form.categories
    })
    await load()
    editing.value = false
    toast('资料已提交，等待超管审核')
  } catch (e) { /* 拦截器 */ } finally { saving.value = false }
}

load()
</script>

<style scoped>
.center-head { margin-bottom: 12px; }
.center-head p { margin: 0 0 2px; color: var(--muted); font-size: 11px; font-weight: 800; letter-spacing: .08em; }
.page-title { margin: 0; }
.center-tabs { display: flex; gap: 10px; margin-bottom: 16px; }
.center-tabs .tab { min-width: 96px; padding: 9px 18px; border: 1px solid var(--border); border-radius: 8px; background: #fff; color: var(--muted); cursor: pointer; }
.center-tabs .tab.active {
  border-color: #2f855a;
  background: linear-gradient(100deg, #125f3b 0%, #23784c 52%, #3b9162 100%);
  color: #fff;
  box-shadow: 0 7px 16px rgba(24, 105, 65, .16);
}

.pending-banner { margin-bottom: 14px; padding: 11px 14px; border: 1px solid #fde08a; background: #fff8e3; color: #a16207; border-radius: 9px; font-size: 13px; font-weight: 600; }
.card-title { margin: 0 0 14px; font-size: 17px; }
.info-card { padding: 20px 22px; }
.info-row { display: grid; grid-template-columns: 96px minmax(0, 1fr); gap: 10px; padding: 8px 0; border-bottom: 1px dashed var(--border); font-size: 14px; align-items: center; }
.info-row > span { color: var(--muted); }
.info-row strong { font-weight: 600; word-break: break-word; }
.badge { font-style: normal; padding: 2px 10px; border-radius: 10px; font-size: 12px; font-weight: 700; width: fit-content; }
.badge.ok { background: #dcfce7; color: #15803d; }
.badge.pending { background: #fef3c7; color: #b45309; }
.cat-tag { display: inline-block; margin: 2px 6px 2px 0; padding: 3px 10px; border-radius: 999px; background: #e4f2e9; color: #17633a; font-size: 12px; }
.center-edit { margin-top: 16px; }
.pending-old { margin-top: 14px; background: #fffdf7; }
.pending-old h4 { margin: 0 0 6px; color: var(--muted); font-size: 13px; }

.edit-card { padding: 20px 22px; }
.field { display: block; margin-bottom: 14px; }
.field > span { display: block; margin-bottom: 6px; color: var(--muted); font-size: 13px; font-weight: 600; }
.input { width: 100%; }
.license-preview { display: block; margin-top: 8px; width: 120px; height: 84px; object-fit: cover; border-radius: 8px; border: 1px solid var(--border); }
.chip-pool { display: flex; flex-wrap: wrap; gap: 8px; }
.chip { padding: 6px 13px; border: 1px solid var(--border); border-radius: 999px; background: #fff; color: var(--muted); font-size: 13px; cursor: pointer; }
.chip.on { background: #0A5A3E; border-color: #0A5A3E; color: #fff; }
.edit-actions { display: flex; justify-content: flex-end; gap: 10px; margin-top: 18px; }
.save-button { padding: 10px 18px; border: 0; border-radius: 8px; background: #16a34a; color: #fff; font-size: 14px; font-weight: 700; cursor: pointer; }
.save-button:disabled { opacity: .6; }
</style>
