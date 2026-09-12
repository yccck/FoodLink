<template>
  <div class="auth-wrap student-auth">
    <div class="auth-card card">
      <BrandLogo size="small" class="auth-logo" />
      <p class="auth-kicker">加入食愿，一起珍惜好味道</p>
      <h1 class="auth-title">学生注册</h1>

      <template v-if="!result">
        <form class="student-form" @submit.prevent="submit">
          <div class="form-item form-item--full">
            <label>姓名</label>
            <input class="input" v-model.trim="form.name" placeholder="请输入姓名" />
          </div>
          <p class="auth-hint">学号、手机号与登录密码将由系统自动生成</p>
          <button class="submit-button" type="submit" :disabled="loading">
            {{ loading ? '提交中…' : '注册' }}
          </button>
        </form>
      </template>

      <template v-else>
        <div class="cred-card">
          <div class="cred-emoji">🎉</div>
          <h2 class="cred-title">注册成功</h2>
          <p class="cred-sub">你的登录账号信息如下，请妥善保存：</p>
          <div class="cred-row"><span>学号（登录账号）</span><b>{{ result.student_id }}</b></div>
          <div class="cred-row"><span>系统手机号</span><b>{{ result.phone }}</b></div>
          <div class="cred-row"><span>初始密码</span><b>{{ result.password }}</b></div>
          <p class="cred-tip">首次登录后可在「个人中心」修改密码。</p>
          <button class="submit-button" type="button" @click="goLogin">去登录</button>
        </div>
      </template>

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
const form = reactive({ name: '' })
const result = ref(null)

async function submit() {
  if (!form.name) { toast('请填写姓名', 'error'); return }
  loading.value = true
  try {
    result.value = await register({ role: 1, name: form.name })
  } catch (e) { /* 拦截器已提示 */ } finally { loading.value = false }
}

function goLogin() { router.push('/login') }
</script>

<style scoped>
.auth-wrap { min-height: 100vh; min-height: 100svh; display: grid; place-items: center; padding: 16px 18px; background: radial-gradient(circle at 14% 18%, rgba(255,190,91,.27), transparent 25%), radial-gradient(circle at 86% 12%, rgba(39,125,87,.16), transparent 24%), #fffaf0; }
.auth-card { width: min(100%, 720px); padding: 22px 26px; border-color: #ecddc8; border-radius: 30px; background: rgba(255,255,250,.98); box-shadow: 0 25px 70px rgba(78,57,34,.13); }
.auth-logo { margin: 0 auto 4px; }
.auth-kicker { margin: 0; color: #e16f47; font-size: 13px; font-weight: 800; text-align: center; }
.auth-title { margin: 3px 0 14px; color: #40382f; font-size: 27px; text-align: center; }
.student-form { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 10px 14px; }
.student-form .form-item { min-width: 0; margin: 0; }
.form-item--full { grid-column: 1 / -1; }
.student-form .form-item label { margin-bottom: 4px; font-size: 13px; }
.auth-hint { grid-column: 1 / -1; margin: 2px 0 0; font-size: 13px; color: var(--muted); text-align: center; }
.input { min-height: 42px; padding: 8px 12px; border-color: #dfd1bd; border-radius: 12px; }
.input:focus { border-color: #e97950; box-shadow: 0 0 0 4px rgba(233,121,80,.1); }
.submit-button { grid-column: 1 / -1; width: 100%; min-height: 44px; margin-top: 2px; border: 0; border-radius: 999px; background: #e97950; color: #fff; font-size: 16px; font-weight: 800; cursor: pointer; }
.submit-button:disabled { opacity: .55; }
.auth-links { margin-top: 10px; text-align: center; font-size: 14px; color: var(--muted); }
.auth-links a { color: #d8613d; font-weight: 700; text-decoration: none; }
.cred-card { display: grid; gap: 6px; padding: 8px 4px; text-align: center; }
.cred-emoji { font-size: 38px; line-height: 1; }
.cred-title { margin: 2px 0; font-size: 22px; color: #40382f; }
.cred-sub { margin: 0; font-size: 14px; color: var(--muted); }
.cred-row { display: flex; justify-content: space-between; align-items: center; gap: 12px; padding: 10px 14px; border: 1px dashed #e3cdb2; border-radius: 12px; background: #fff7ec; font-size: 14px; }
.cred-row span { color: var(--muted); }
.cred-row b { color: #d8613d; font-size: 16px; letter-spacing: .5px; word-break: break-all; }
.cred-tip { margin: 2px 0 4px; font-size: 12px; color: var(--muted); }
@media (max-width: 600px) {
  .auth-wrap { padding: 12px 10px; }
  .auth-card { padding: 18px; }
  .student-form { grid-template-columns: 1fr; gap: 8px; }
  .auth-links { margin-top: 7px; font-size: 12px; }
}
@media (max-width: 600px) and (max-height: 700px) {
  .auth-wrap { padding-block: 6px; }
  .auth-card { padding: 10px 14px; }
  .auth-logo { height: 38px; margin-bottom: 2px; }
  .auth-kicker { font-size: 11px; }
  .auth-title { margin: 1px 0 7px; font-size: 22px; }
}
</style>
