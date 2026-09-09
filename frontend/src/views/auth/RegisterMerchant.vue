<template>
  <div class="auth-wrap">
    <div class="auth-card card">
      <h2 class="card-title" style="text-align:center">商家入驻</h2>
      <form @submit.prevent="submit">
        <div class="form-item">
          <label>店名</label>
          <input class="input" v-model.trim="form.shop_name" placeholder="请输入店铺名称" />
        </div>

        <div class="form-item">
          <label>营业执照</label>
          <div class="license-row">
            <label class="license-upload" :class="{ filled: !!form.license_img }">
              <template v-if="form.license_img"><img :src="form.license_img" alt="营业执照" /></template>
              <template v-else><span>拍照 / 上传<br />营业执照</span></template>
              <input type="file" accept="image/*" @change="onFile" hidden />
            </label>
          </div>
        </div>

        <div class="form-item">
          <label>店铺位置（地图选点）</label>
          <MapPicker v-model="coords" />
        </div>
        <div class="form-item">
          <label>详细地址</label>
          <input class="input" v-model.trim="form.location" placeholder="请填写详细地址（如：XX大学南门15米）" />
        </div>

        <div class="form-item">
          <label>账号</label>
          <input class="input" v-model.trim="form.login_name" placeholder="设置登录账号" />
        </div>
        <div class="form-item">
          <label>联系方式</label>
          <input class="input" v-model.trim="form.phone" placeholder="请输入手机号" />
        </div>
        <div class="form-item">
          <label>密码</label>
          <input class="input" type="password" v-model="form.password" placeholder="设置密码" />
        </div>
        <div class="form-item">
          <label>确认密码</label>
          <input class="input" type="password" v-model="confirm" placeholder="再次输入密码" />
        </div>

        <p class="notice">入驻信息提交后需经平台审核，审核通过后方可登录发布商品。</p>
        <button class="btn btn-primary btn-block" type="submit" :disabled="loading">
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
import MapPicker from '../../components/MapPicker.vue'
import { register } from '../../api/auth'
import { toast } from '../../utils/toast'

const router = useRouter()
const loading = ref(false)
const confirm = ref('')
const coords = ref({ lat: null, lng: null })
const form = reactive({ shop_name: '', license_img: '', location: '', login_name: '', phone: '', password: '' })

function onFile(e) {
  const file = e.target.files && e.target.files[0]
  if (!file) return
  if (file.size > 2 * 1024 * 1024) { toast('图片过大（最大2MB）', 'error'); e.target.value = ''; return }
  const reader = new FileReader()
  reader.onload = () => { form.license_img = reader.result }
  reader.readAsDataURL(file)
}

async function submit() {
  if (!form.shop_name || !form.license_img || !form.location || !form.login_name || !form.phone || !form.password) {
    toast('请填写完整信息并上传营业执照', 'error'); return
  }
  if (!coords.value.lat || !coords.value.lng) { toast('请在地图上选择店铺位置', 'error'); return }
  if (form.password !== confirm.value) { toast('两次输入的密码不一致', 'error'); return }
  if (!/^1\d{10}$/.test(form.phone)) { toast('请输入正确的手机号', 'error'); return }
  loading.value = true
  try {
    await register({ role: 2, ...form, lat: coords.value.lat, lng: coords.value.lng })
    toast('提交成功，等待商家资质审核')
    router.push('/login')
  } catch (e) { /* 拦截器已提示 */ } finally { loading.value = false }
}
</script>

<style scoped>
.auth-wrap { display: flex; justify-content: center; padding-top: 4vh; }
.auth-card { width: 100%; max-width: 440px; }
.license-row { display: flex; }
.license-upload { width: 140px; height: 96px; border: 1px dashed var(--border); border-radius: 8px; display: flex; align-items: center; justify-content: center; color: var(--muted); font-size: 13px; text-align: center; cursor: pointer; background: #fafafa; overflow: hidden; }
.license-upload.filled { border-style: solid; }
.license-upload img { width: 100%; height: 100%; object-fit: cover; }
.notice { font-size: 12px; color: var(--muted); margin: 4px 0 12px; }
.auth-links { margin-top: 16px; text-align: center; font-size: 14px; color: var(--muted); }
.auth-links a { color: var(--primary); text-decoration: none; }
</style>