<template>
  <div class="auth-wrap merchant-auth">
    <div class="auth-card card">
      <BrandLogo size="medium" class="auth-logo" />
      <p class="auth-kicker">把好味道分享给更多同学</p>
      <h1 class="auth-title">商家入驻</h1>
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
          <MapPicker v-model="coords" />
        </div>
        <div class="form-item">
          <label>商铺详细地址</label>
          <input class="input" v-model.trim="form.location" placeholder="请填写详细地址（如：XX大学南门15米）" />
          <p class="field-hint">发布商品时会自动使用这里作为取货地址，单次发布仍可更改。</p>
        </div>

        <div class="form-grid password-grid">
          <div class="form-item">
            <label>密码</label>
            <input class="input" type="password" v-model="form.password" placeholder="设置密码" />
          </div>
          <div class="form-item">
            <label>确认密码</label>
            <input class="input" type="password" v-model="confirm" placeholder="再次输入密码" />
          </div>
        </div>

        <div class="review-notice"><span aria-hidden>◷</span><p><strong>审核时间一般为1–3天</strong><br />入驻信息提交后需经平台审核，审核通过后方可登录发布商品。</p></div>
        <button class="submit-button" type="submit" :disabled="loading">
          {{ loading ? '提交中…' : '提交入驻申请' }}
        </button>
      </form>
      <div class="auth-links">已有账号？<router-link to="/login">去登录</router-link></div>
    </div>
  </div>
</template>

<script setup>
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import BrandLogo from '../../components/BrandLogo.vue'
import MapPicker from '../../components/MapPicker.vue'
import { register } from '../../api/auth'
import { toast } from '../../utils/toast'

const router = useRouter()
const loading = ref(false)
const confirm = ref('')
const coords = ref({ lat: null, lng: null })
const form = reactive({ shop_name: '', name: '', location: '', login_name: '', phone: '', password: '' })
const documents = reactive({ storefront_img: '', legal_person_id_img: '', license_img: '', permit_img: '', bank_card_img: '' })
const uploadFields = [
  { key: 'storefront_img', label: '实体店铺图', hint: '上传清晰的店铺门面照片', icon: '🏪' },
  { key: 'legal_person_id_img', label: '法人身份证', hint: '上传清晰的身份证照片', icon: '🪪' },
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
.password-grid { margin-top: 18px; }
.field-hint { margin: 6px 0 0; color: var(--muted); font-size: 12px; line-height: 1.5; }
.review-notice { display: flex; gap: 11px; margin: 20px 0; padding: 15px; border: 1px solid #ecd38f; border-radius: 19px; background: #fff4cb; color: #765c28; }
.review-notice > span { font-size: 22px; }
.review-notice p { margin: 0; font-size: 13px; line-height: 1.7; }
.submit-button { width: 100%; min-height: 50px; border: 0; border-radius: 999px; background: #e97950; color: #fff; font-size: 16px; font-weight: 800; cursor: pointer; }
.submit-button:disabled { opacity: .55; }
.auth-links { margin-top: 16px; text-align: center; font-size: 14px; color: var(--muted); }
.auth-links a { color: #d8613d; font-weight: 700; text-decoration: none; }
@media (max-width: 620px) { .auth-card { padding: 24px 18px; } .form-grid, .upload-grid { grid-template-columns: 1fr; } }
</style>
