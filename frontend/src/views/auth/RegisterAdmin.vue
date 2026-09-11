<template>
  <div class="auth-page">
    <div class="auth-card">
      <BrandLogo size="medium" class="auth-logo" />
      <p class="auth-kicker">校园管理伙伴</p>
      <h1>管理员注册</h1>
      <p class="auth-note">填写所属学校和联系方式，提交注册申请。</p>

      <form @submit.prevent="submit">
        <div class="soft-panel">
          <div class="form-item">
            <label>学校名称</label>
            <input v-model.trim="form.school" class="input" placeholder="请输入所属学校" />
          </div>
          <div class="form-item">
            <label>联系方式</label>
            <input v-model.trim="form.phone" class="input" placeholder="请输入手机号" />
          </div>
        </div>

        <div class="form-item">
          <label>管理员账号</label>
          <input v-model.trim="form.login_name" class="input" placeholder="设置管理员账号" autocomplete="username" />
        </div>
        <div class="form-grid">
          <div class="form-item">
            <label>密码</label>
            <input v-model="form.password" class="input" type="password" placeholder="设置密码" autocomplete="new-password" />
          </div>
          <div class="form-item">
            <label>确认密码</label>
            <input v-model="confirm" class="input" type="password" placeholder="再次输入密码" autocomplete="new-password" />
          </div>
        </div>

        <button class="submit-button" type="submit">提交注册申请</button>
      </form>
      <p class="back-link">已有账号？<router-link to="/login?role=3">返回登录</router-link></p>
    </div>
  </div>
</template>

<script setup>
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import BrandLogo from '../../components/BrandLogo.vue'
import { toast } from '../../utils/toast'

const router = useRouter()
const confirm = ref('')
const form = reactive({ school: '', phone: '', login_name: '', password: '' })

function submit() {
  if (!form.school || !form.phone || !form.login_name || !form.password) {
    toast('请填写完整信息', 'error')
    return
  }
  if (!/^1\d{10}$/.test(form.phone)) {
    toast('请输入正确的手机号', 'error')
    return
  }
  if (form.password !== confirm.value) {
    toast('两次输入的密码不一致', 'error')
    return
  }

  localStorage.setItem('shiyuan_admin_application', JSON.stringify({
    school: form.school,
    phone: form.phone,
    login_name: form.login_name,
    submitted_at: new Date().toISOString()
  }))
  toast('注册申请已保存，请等待平台联系')
  router.push('/login?role=3')
}
</script>

<style scoped>
.auth-page { min-height: 100vh; display: grid; place-items: center; padding: 42px 18px; background: radial-gradient(circle at 14% 18%, rgba(255,190,91,.28), transparent 25%), radial-gradient(circle at 86% 12%, rgba(39,125,87,.18), transparent 24%), #fffaf0; }
.auth-card { width: min(100%, 520px); padding: 30px; border: 1px solid #ecddc8; border-radius: 30px; background: rgba(255,255,250,.97); box-shadow: 0 26px 70px rgba(78,57,34,.14); }
.auth-logo { margin: 0 auto 8px; }
.auth-kicker { margin: 0; color: #e46f45; font-size: 13px; font-weight: 800; text-align: center; }
h1 { margin: 6px 0; color: #40382f; font-size: 28px; text-align: center; }
.auth-note { margin: 0 0 22px; color: #796f65; font-size: 14px; text-align: center; }
.soft-panel { margin-bottom: 18px; padding: 17px; border-radius: 20px; background: #eef5e8; }
.soft-panel .form-item:last-child { margin-bottom: 0; }
.form-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
.input { min-height: 47px; padding: 11px 14px; border-radius: 15px; border-color: #dfd1bd; }
.input:focus { border-color: #e97950; box-shadow: 0 0 0 4px rgba(233,121,80,.1); }
.submit-button { width: 100%; min-height: 49px; border: 0; border-radius: 999px; background: #e97950; color: #fff; font-size: 16px; font-weight: 800; cursor: pointer; }
.back-link { margin: 18px 0 0; color: #7b7066; font-size: 14px; text-align: center; }
.back-link a { color: #d9623d; font-weight: 700; text-decoration: none; }
@media (max-width: 540px) { .auth-card { padding: 24px 18px; } .form-grid { grid-template-columns: 1fr; gap: 0; } }
</style>
