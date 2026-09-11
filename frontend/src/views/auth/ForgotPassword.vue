<template>
  <div class="auth-wrap forgot-auth">
    <div class="auth-card card">
      <BrandLogo size="medium" class="auth-logo" />
      <h1 class="auth-title">找回密码</h1>
      <p class="hint">验证身份通过后，密码将被重置为 <b>123456</b></p>

      <div class="role-tabs">
        <button v-for="r in roles" :key="r.value" type="button" :class="{ active: role === r.value }" @click="role = r.value">
          {{ r.label }}
        </button>
      </div>

      <form @submit.prevent="submit">
        <template v-if="role === 1">
          <div class="form-item"><label>学号</label><input class="input" v-model.trim="form.student_id" placeholder="请输入学号" /></div>
          <div class="form-item"><label>姓名</label><input class="input" v-model.trim="form.name" placeholder="请输入姓名" /></div>
        </template>
        <template v-else>
          <div class="form-item"><label>账号</label><input class="input" v-model.trim="form.login_name" placeholder="请输入账号" /></div>
          <div class="form-item"><label>店名</label><input class="input" v-model.trim="form.shop_name" placeholder="请输入店名" /></div>
        </template>
        <div class="form-item"><label>联系方式</label><input class="input" v-model.trim="form.phone" placeholder="请输入手机号" /></div>

        <button class="submit-button" type="submit" :disabled="loading">
          {{ loading ? '提交中…' : '验证并重置密码' }}
        </button>
      </form>

      <div class="auth-links">记得密码了？<router-link to="/login">去登录</router-link></div>
    </div>
  </div>
</template>

<script setup>
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import BrandLogo from '../../components/BrandLogo.vue'
import { resetPassword } from '../../api/auth'
import { toast } from '../../utils/toast'

const roles = [{ label: '学生', value: 1 }, { label: '商家', value: 2 }]
const router = useRouter()
const role = ref(1)
const loading = ref(false)
const form = reactive({ student_id: '', login_name: '', name: '', shop_name: '', phone: '' })

async function submit() {
  if (!form.phone || (role.value === 1 ? (!form.student_id || !form.name) : (!form.login_name || !form.shop_name))) {
    toast('请填写完整验证信息', 'error'); return
  }
  loading.value = true
  try {
    const data = await resetPassword({ role: role.value, ...form })
    toast(data.message || '密码已重置为123456')
    router.push('/login')
  } catch (e) { /* 拦截器已提示 */ } finally { loading.value = false }
}
</script>

<style scoped>
.auth-wrap { min-height: 100vh; display: grid; place-items: center; padding: 38px 18px; background: radial-gradient(circle at 14% 18%, rgba(255,190,91,.27), transparent 25%), radial-gradient(circle at 86% 12%, rgba(39,125,87,.16), transparent 24%), #fffaf0; }
.auth-card { width: min(100%, 500px); padding: 30px; border-color: #ecddc8; border-radius: 30px; background: rgba(255,255,250,.98); box-shadow: 0 25px 70px rgba(78,57,34,.13); }
.auth-logo { margin: 0 auto 6px; }
.auth-title { margin: 5px 0 8px; color: #40382f; font-size: 28px; text-align: center; }
.hint { color: var(--muted); font-size: 13px; text-align: center; margin: 0 0 18px; }
.role-tabs { display: grid; grid-template-columns: 1fr 1fr; gap: 6px; margin-bottom: 20px; padding: 6px; border-radius: 17px; background: #f7ecda; }
.role-tabs button { min-height: 41px; border: 0; border-radius: 13px; background: transparent; color: #7c7269; font-weight: 700; cursor: pointer; }
.role-tabs button.active { background: #fff; color: #d9623f; box-shadow: 0 3px 10px rgba(78,57,34,.08); }
.input { min-height: 47px; padding: 11px 14px; border-color: #dfd1bd; border-radius: 15px; }
.input:focus { border-color: #e97950; box-shadow: 0 0 0 4px rgba(233,121,80,.1); }
.submit-button { width: 100%; min-height: 50px; border: 0; border-radius: 999px; background: #e97950; color: #fff; font-size: 16px; font-weight: 800; cursor: pointer; }
.submit-button:disabled { opacity: .55; }
.auth-links { margin-top: 16px; text-align: center; font-size: 14px; color: var(--muted); }
.auth-links a { color: #d8613d; font-weight: 700; text-decoration: none; }
@media (max-width: 520px) { .auth-card { padding: 24px 18px; } }
</style>
