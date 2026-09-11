<template>
  <div class="auth-wrap student-auth">
    <div class="auth-card card">
      <BrandLogo size="medium" class="auth-logo" />
      <p class="auth-kicker">加入食愿，一起珍惜好味道</p>
      <h1 class="auth-title">学生注册</h1>
      <form @submit.prevent="submit">
        <div class="form-item">
          <label>学校</label>
          <input class="input" v-model.trim="form.school" placeholder="请输入学校名称" />
        </div>
        <div class="form-item">
          <label>学号（将作为登录账号）</label>
          <input class="input" v-model.trim="form.student_id" placeholder="请输入学号" />
        </div>
        <div class="form-item">
          <label>姓名</label>
          <input class="input" v-model.trim="form.name" placeholder="请输入姓名" />
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
        <button class="submit-button" type="submit" :disabled="loading">
          {{ loading ? '提交中…' : '注册' }}
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
import { register } from '../../api/auth'
import { toast } from '../../utils/toast'

const router = useRouter()
const loading = ref(false)
const confirm = ref('')
const form = reactive({ school: '', student_id: '', name: '', phone: '', password: '' })

async function submit() {
  if (!form.school || !form.student_id || !form.name || !form.phone || !form.password) {
    toast('请填写完整信息', 'error'); return
  }
  if (form.password !== confirm.value) { toast('两次输入的密码不一致', 'error'); return }
  if (!/^1\d{10}$/.test(form.phone)) { toast('请输入正确的手机号', 'error'); return }
  loading.value = true
  try {
    await register({ role: 1, ...form })
    toast('注册成功，请登录')
    router.push('/login')
  } catch (e) { /* 拦截器已提示 */ } finally { loading.value = false }
}
</script>

<style scoped>
.auth-wrap { min-height: 100vh; display: grid; place-items: center; padding: 38px 18px; background: radial-gradient(circle at 14% 18%, rgba(255,190,91,.27), transparent 25%), radial-gradient(circle at 86% 12%, rgba(39,125,87,.16), transparent 24%), #fffaf0; }
.auth-card { width: min(100%, 500px); padding: 30px; border-color: #ecddc8; border-radius: 30px; background: rgba(255,255,250,.98); box-shadow: 0 25px 70px rgba(78,57,34,.13); }
.auth-logo { margin: 0 auto 6px; }
.auth-kicker { margin: 0; color: #e16f47; font-size: 13px; font-weight: 800; text-align: center; }
.auth-title { margin: 5px 0 22px; color: #40382f; font-size: 28px; text-align: center; }
.input { min-height: 47px; padding: 11px 14px; border-color: #dfd1bd; border-radius: 15px; }
.input:focus { border-color: #e97950; box-shadow: 0 0 0 4px rgba(233,121,80,.1); }
.submit-button { width: 100%; min-height: 50px; border: 0; border-radius: 999px; background: #e97950; color: #fff; font-size: 16px; font-weight: 800; cursor: pointer; }
.submit-button:disabled { opacity: .55; }
.auth-links { margin-top: 16px; text-align: center; font-size: 14px; color: var(--muted); }
.auth-links a { color: #d8613d; font-weight: 700; text-decoration: none; }
@media (max-width: 520px) { .auth-card { padding: 24px 18px; } }
</style>
