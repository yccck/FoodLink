<template>
  <div class="auth-wrap merchant-auth">
    <div class="auth-card card">
      <BrandLogo size="medium" class="auth-logo" />
      <p class="auth-kicker">把好味道分享给更多同学</p>
      <h1 class="auth-title">商家注册</h1>
      <p class="auth-description">请填写真实店铺信息并上传清晰的经营资质。</p>
      <form @submit.prevent="submit">
        <section class="form-panel green-panel">
          <h2>店铺信息</h2>
          <div class="form-grid">
            <div class="form-item">
              <label>店铺名称</label>
              <input class="input" v-model.trim="form.shop_name" placeholder="请输入店铺名称" />
            </div>
            <div class="form-item">
              <label>法人或负责人姓名</label>
              <input class="input" v-model.trim="form.name" placeholder="请输入真实姓名" />
            </div>
            <div class="form-item">
              <label>联系方式</label>
              <input class="input" v-model.trim="form.phone" placeholder="请输入手机号" />
            </div>
            <div class="form-item">
              <label>商家账号</label>
              <input class="input" v-model.trim="form.login_name" placeholder="设置登录账号" />
            </div>
            <div class="form-item">
              <label>密码</label>
              <input class="input" type="password" v-model="form.password" placeholder="设置密码" autocomplete="new-password" />
            </div>
            <div class="form-item">
              <label>确认密码</label>
              <input class="input" type="password" v-model="confirm" placeholder="再次输入密码" autocomplete="new-password" />
            </div>
          </div>
        </section>

        <section class="qualification-section">
          <div class="section-row"><h2>经营资质</h2><span>支持 JPG、PNG 图片</span></div>
          <div class="upload-grid">
            <label v-for="item in uploadFields" :key="item.key" class="upload-card" :class="{ filled: !!documents[item.key] }">
              <input type="file" accept="image/*" hidden @change="onFile(item.key, $event)" />
              <img v-if="documents[item.key]" :src="documents[item.key]" :alt="item.label" />
              <span v-else class="upload-icon" aria-hidden>{{ item.icon }}</span>
              <span class="upload-copy"><strong>{{ item.label }}</strong><small>{{ documents[item.key] ? '已上传，点击可更换' : item.hint }}</small></span>
            </label>
          </div>
        </section>

        <div class="form-item">
          <label>默认商铺位置（地图选点）</label>
          <div class="locate-row">
            <span class="locate-hint">点击右侧按钮定位，会自动列出周边 500m 内的地点供选择</span>
            <button class="locate-button" type="button" :disabled="locating" @click="locateMe">
              {{ locating ? '定位中…' : '📍 获取当前位置' }}
            </button>
          </div>

          <div class="search-row">
            <input
              class="input mini"
              v-model.trim="keyword"
              placeholder="搜索地点名称（可留空，直接看周边）"
              @keyup.enter="searchNearby"
            />
            <button class="locate-button" type="button" :disabled="searching || !coords.lat" @click="searchNearby">
              {{ searching ? '搜索中…' : '搜索' }}
            </button>
          </div>

          <div v-if="pois.length" class="poi-list">
            <button
              v-for="p in pois"
              :key="p.id"
              type="button"
              class="poi-item"
              :class="{ active: selectedPoiId === p.id }"
              @click="pickPoi(p)"
            >
              <span class="poi-name">{{ p.name }}</span>
              <span class="poi-meta">
                <span class="poi-tag">{{ p.category }}</span>
                <span class="poi-dist">{{ p.distance }}m</span>
              </span>
              <span v-if="p.address" class="poi-addr">{{ p.address }}</span>
            </button>
          </div>
          <p v-else-if="searched" class="field-hint">周边暂未找到地点，换个关键词再试一次。</p>

          <MapPicker v-model="coords" :readonly="true" :radius="500" />
          <p v-if="selectedPoi" class="field-hint">已选择：<strong>{{ selectedPoi.name }}</strong>（{{ selectedPoi.lat }}，{{ selectedPoi.lng }}）</p>
        </div>
        <div class="form-item">
          <label>商铺详细地址</label>
          <input class="input" v-model.trim="form.location" placeholder="请填写详细地址（如：澳门科技大学N座旁取货点）" />
          <p class="field-hint">发布商品时会自动使用这里作为取货地址，单次发布仍可更改。</p>
        </div>

        <div class="review-notice"><span aria-hidden>◷</span><p><strong>审核时间一般为1–3天</strong><br />入驻信息提交后需经平台审核，审核通过后方可登录发布商品。</p></div>
        <button class="submit-button" type="submit" :disabled="loading">
          {{ loading ? '提交中…' : '提交注册申请' }}
        </button>
      </form>
      <div class="auth-links">已有账号？<router-link to="/login">去登录</router-link></div>
    </div>
  </div>
</template>

<script setup>
import { computed, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import BrandLogo from '../../components/BrandLogo.vue'
import MapPicker from '../../components/MapPicker.vue'
import { register } from '../../api/auth'
import { searchAround } from '../../utils/place'
import { toast } from '../../utils/toast'

const router = useRouter()
const loading = ref(false)
const locating = ref(false)
const confirm = ref('')
const coords = ref({ lat: null, lng: null })
const form = reactive({ shop_name: '', name: '', location: '', login_name: '', phone: '', password: '' })
const documents = reactive({ storefront_img: '', legal_person_id_front: '', legal_person_id_back: '', license_img: '', permit_img: '', bank_card_img: '' })
const uploadFields = [
  { key: 'storefront_img', label: '实体店铺图', hint: '上传清晰的店铺门面照片', icon: '🏪' },
  { key: 'legal_person_id_front', label: '法人身份证（正面）', hint: '上传身份证人像面照片', icon: '🪪' },
  { key: 'legal_person_id_back', label: '法人身份证（背面）', hint: '上传身份证国徽面照片', icon: '🪪' },
  { key: 'license_img', label: '营业执照', hint: '上传有效期内的营业执照', icon: '📄' },
  { key: 'permit_img', label: '许可证', hint: '上传食品经营等相关许可证', icon: '✅' },
  { key: 'bank_card_img', label: '法人或公司账户银行卡', hint: '上传用于核验的银行卡照片', icon: '💳' }
]

function onFile(field, e) {
  const file = e.target.files && e.target.files[0]
  if (!file) return
  if (file.size > 2 * 1024 * 1024) { toast('图片过大（最大2MB）', 'error'); e.target.value = ''; return }
  const reader = new FileReader()
  reader.onload = () => { documents[field] = reader.result }
  reader.readAsDataURL(file)
}

const RADIUS = 500
const keyword = ref('')
const pois = ref([])
const searching = ref(false)
const searched = ref(false)
const selectedPoiId = ref('')
const selectedPoi = computed(() => pois.value.find(p => p.id === selectedPoiId.value) || null)

// ---- 定位：浏览器精确定位 → 失败自动降级网络（IP）粗定位 → 仍失败则手动填经纬度 ----
function browserLocation() {
  return new Promise((resolve, reject) => {
    if (!navigator.geolocation || !window.isSecureContext) {
      reject(new Error('unsupported'))
      return
    }
    navigator.geolocation.getCurrentPosition(resolve, reject, {
      enableHighAccuracy: true,
      timeout: 8000,
      maximumAge: 30000
    })
  })
}

async function fetchJson(url, ms = 6000) {
  const ctrl = new AbortController()
  const timer = setTimeout(() => ctrl.abort(), ms)
  try {
    const res = await fetch(url, { signal: ctrl.signal })
    return await res.json()
  } finally {
    clearTimeout(timer)
  }
}

// 免费 https 源，返回城市级坐标，够用来把地图挪到大致区域，再手动微调
async function ipLocation() {
  const sources = [
    async () => {
      const d = await fetchJson('https://ipapi.co/json/')
      return Number.isFinite(d.latitude) && Number.isFinite(d.longitude)
        ? { lat: d.latitude, lng: d.longitude }
        : null
    },
    async () => {
      const d = await fetchJson('https://ipinfo.io/json')
      const loc = String(d.loc || '').split(',')
      return loc.length === 2 && Number.isFinite(Number(loc[0])) && Number.isFinite(Number(loc[1]))
        ? { lat: Number(loc[0]), lng: Number(loc[1]) }
        : null
    }
  ]
  for (const source of sources) {
    try {
      const hit = await source()
      if (hit) return hit
    } catch (e) { /* 换下一个源 */ }
  }
  return null
}

async function locateMe() {
  if (locating.value) return
  locating.value = true
  try {
    const pos = await browserLocation()
    coords.value = {
      lat: Number(pos.coords.latitude.toFixed(6)),
      lng: Number(pos.coords.longitude.toFixed(6))
    }
    locating.value = false
    toast('定位成功，正在查找周边地点')
    await searchNearby()
    return
  } catch (e) { /* 精确定位不可用，继续尝试网络定位 */ }

  const ip = await ipLocation()
  locating.value = false
  if (ip) {
    coords.value = { lat: Number(ip.lat.toFixed(6)), lng: Number(ip.lng.toFixed(6)) }
    toast('已按网络位置粗略定位，正在查找周边地点')
    await searchNearby()
    return
  }
  toast('定位失败，请在上方输入地点名称搜索，或稍后重试', 'error')
}

async function searchNearby() {
  if (!coords.value.lat || !coords.value.lng) {
    toast('请先点击「获取当前位置」', 'error')
    return
  }
  searching.value = true
  searched.value = false
  selectedPoiId.value = ''
  try {
    pois.value = await searchAround({
      lat: coords.value.lat,
      lng: coords.value.lng,
      radius: RADIUS,
      keyword: keyword.value
    })
    searched.value = true
    if (!pois.value.length) toast('周边暂未找到地点，换个关键词试试', 'error')
  } catch (e) {
    pois.value = []
    toast('地点搜索失败，请稍后重试', 'error')
  } finally {
    searching.value = false
  }
}

function pickPoi(p) {
  selectedPoiId.value = p.id
  coords.value = { lat: p.lat, lng: p.lng }
  if (!form.location) form.location = p.address || p.name
  toast(`已选择「${p.name}」`)
}

async function submit() {
  if (!form.shop_name || !form.name || !form.location || !form.login_name || !form.phone || !form.password) {
    toast('请填写完整的店铺与账号信息', 'error'); return
  }
  if (uploadFields.some(item => !documents[item.key])) {
    toast('请上传完整的经营资质材料', 'error'); return
  }
  if (!coords.value.lat || !coords.value.lng) { toast('请在地图上选择店铺位置', 'error'); return }
  if (form.password !== confirm.value) { toast('两次输入的密码不一致', 'error'); return }
  if (!/^1\d{10}$/.test(form.phone)) { toast('请输入正确的手机号', 'error'); return }
  loading.value = true
  try {
    await register({ role: 2, ...form, license_img: documents.license_img, lat: coords.value.lat, lng: coords.value.lng })
    toast('提交成功，审核时间一般为1–3天')
    router.push('/login')
  } catch (e) { /* 拦截器已提示 */ } finally { loading.value = false }
}
</script>

<style scoped>
.auth-wrap { min-height: 100vh; display: flex; justify-content: center; padding: 38px 18px; background: radial-gradient(circle at 12% 14%, rgba(255,190,91,.25), transparent 24%), radial-gradient(circle at 88% 10%, rgba(39,125,87,.15), transparent 24%), #fffaf0; }
.auth-card { width: min(100%, 780px); padding: 30px; border-color: #ecddc8; border-radius: 30px; background: rgba(255,255,250,.98); box-shadow: 0 25px 70px rgba(78,57,34,.13); }
.auth-logo { margin: 0 auto 5px; }
.auth-kicker { margin: 0; color: #e16f47; font-size: 13px; font-weight: 800; text-align: center; }
.auth-title { margin: 5px 0; color: #40382f; font-size: 29px; text-align: center; }
.auth-description { margin: 0 0 24px; color: #7b7168; font-size: 14px; text-align: center; }
.form-panel { margin-bottom: 22px; padding: 18px; border-radius: 22px; }
.green-panel { background: #edf5e7; }
.form-panel h2, .qualification-section h2 { margin: 0 0 14px; color: #455447; font-size: 15px; }
.form-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
.form-grid .form-item { margin-bottom: 0; }
.input { min-height: 47px; padding: 11px 14px; border-color: #dfd1bd; border-radius: 15px; }
.input:focus { border-color: #e97950; box-shadow: 0 0 0 4px rgba(233,121,80,.1); }
.qualification-section { margin: 22px 0; }
.section-row { display: flex; align-items: flex-end; justify-content: space-between; gap: 12px; }
.section-row span { color: #8b8178; font-size: 12px; }
.upload-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
.upload-card { min-height: 96px; display: flex; align-items: center; gap: 12px; padding: 14px; border: 1px dashed #deb98b; border-radius: 19px; background: #fff8e9; cursor: pointer; transition: .16s; }
.upload-card:hover { transform: translateY(-2px); border-color: #df7048; }
.upload-card.filled { border-style: solid; border-color: #a8c392; background: #f1f7eb; }
.upload-card img { width: 56px; height: 56px; flex: 0 0 56px; border-radius: 13px; object-fit: cover; }
.upload-icon { display: grid; width: 46px; height: 46px; flex: 0 0 46px; place-items: center; border-radius: 15px; background: #fff; font-size: 21px; box-shadow: 0 4px 12px rgba(78,57,34,.07); }
.upload-copy strong, .upload-copy small { display: block; }
.upload-copy strong { color: #493f35; font-size: 14px; }
.upload-copy small { margin-top: 4px; color: #82776d; font-size: 12px; line-height: 1.5; }
.field-hint { margin: 6px 0 0; color: var(--muted); font-size: 12px; line-height: 1.5; }
.locate-row { display: flex; align-items: center; justify-content: flex-end; gap: 10px; margin-bottom: 10px; }
.locate-hint { margin-right: auto; color: var(--muted); font-size: 12px; line-height: 1.5; }
.locate-button {
  flex: none;
  min-height: 40px;
  padding: 0 16px;
  border: 1px solid #dfd1bd;
  border-radius: 999px;
  background: #fff;
  color: #5c5145;
  font-size: 13px;
  font-weight: 700;
  white-space: nowrap;
  cursor: pointer;
  transition: .16s;
}
.locate-button:hover:not(:disabled) { border-color: #e97950; color: #d8613d; background: #fff6ef; }
.locate-button:disabled { opacity: .6; cursor: default; }
.search-row { display: flex; align-items: center; gap: 8px; margin-bottom: 10px; }
.input.mini { flex: 1; min-height: 40px; padding: 8px 12px; font-size: 13px; border-radius: 12px; }
.poi-list { max-height: 208px; overflow-y: auto; margin-bottom: 10px; border: 1px solid #eadfcd; border-radius: 16px; background: #fffdf8; }
.poi-item {
  display: block;
  width: 100%;
  padding: 10px 13px;
  border: 0;
  border-bottom: 1px solid #f4ecdf;
  background: transparent;
  text-align: left;
  cursor: pointer;
  transition: .14s;
}
.poi-item:last-child { border-bottom: 0; }
.poi-item:hover { background: #fff5e9; }
.poi-item.active { background: #edf5e7; box-shadow: inset 3px 0 0 #2f7d55; }
.poi-name { display: block; color: #40382f; font-size: 14px; font-weight: 700; }
.poi-meta { display: flex; align-items: center; gap: 8px; margin-top: 3px; }
.poi-tag { padding: 1px 7px; border-radius: 999px; background: #f3ece0; color: #8a7f70; font-size: 11px; }
.poi-dist { color: #d8613d; font-size: 12px; font-weight: 700; }
.poi-addr { display: block; margin-top: 3px; color: var(--muted); font-size: 12px; line-height: 1.4; }
.review-notice { display: flex; gap: 11px; margin: 20px 0; padding: 15px; border: 1px solid #ecd38f; border-radius: 19px; background: #fff4cb; color: #765c28; }
.review-notice > span { font-size: 22px; }
.review-notice p { margin: 0; font-size: 13px; line-height: 1.7; }
.submit-button { width: 100%; min-height: 50px; border: 0; border-radius: 999px; background: #e97950; color: #fff; font-size: 16px; font-weight: 800; cursor: pointer; }
.submit-button:disabled { opacity: .55; }
.auth-links { margin-top: 16px; text-align: center; font-size: 14px; color: var(--muted); }
.auth-links a { color: #d8613d; font-weight: 700; text-decoration: none; }
@media (max-width: 620px) {
  .auth-card { padding: 24px 18px; }
  .form-grid, .upload-grid { grid-template-columns: 1fr; }
  .locate-row { flex-wrap: wrap; }
  .locate-hint { margin-right: 0; flex: 1 1 100%; }
  .locate-button { width: 100%; justify-content: center; }
}
</style>
