<template>
  <div class="auth-wrap">
    <div class="auth-card card">
      <BrandLogo size="medium" class="auth-brand" />
      <h1 class="auth-title">管理员注册</h1>
      <p class="auth-description">请填写所属学校及有效联系方式。</p>

      <form @submit.prevent="submit">
        <section class="form-section form-section-green">
          <h2 class="form-section-title">管理员信息</h2>
          <div class="form-item">
            <label>学校名称</label>
            <input v-model.trim="form.school" class="input" placeholder="请输入学校名称" />
          </div>
          <div class="form-item">
            <label>联系方式</label>
            <input v-model.trim="form.phone" class="input" placeholder="请输入手机号或邮箱" />
          </div>
        </section>

        <div class="form-item">
          <label>管理员账号</label>
          <input v-model.trim="form.login_name" class="input" placeholder="设置管理员登录账号" autocomplete="username" />
        </div>
        <div class="form-item">
          <label>密码</label>
          <input v-model="form.password" class="input" type="password" placeholder="设置密码" autocomplete="new-password" />
        </div>
        <div class="form-item">
          <label>确认密码</label>
          <input v-model="confirmPassword" class="input" type="password" placeholder="再次输入密码" autocomplete="new-password" />
        </div>

        <button class="btn btn-primary btn-block auth-submit" type="submit" :disabled="loading">
          {{ loading ? '提交中…' : '提交注册' }}
        </button>
      </form>

      <div class="auth-links">已有账号？<router-link to="/login">返回登录</router-link></div>
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
const confirmPassword = ref('')
const form = reactive({ school: '', phone: '', login_name: '', password: '' })

function isValidContact(value) {
  return /^\d{8,11}$/.test(value) || /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value)
}

async function submit() {
  if (!form.school || !form.phone || !form.login_name || !form.password) {
    toast('请填写完整的管理员注册信息', 'error')
    return
  }
  if (!isValidContact(form.phone)) {
    toast('请输入正确的手机号或邮箱', 'error')
    return
  }
  if (form.password.length < 6) {
    toast('密码至少需要6位', 'error')
    return
  }
  if (form.password !== confirmPassword.value) {
    toast('两次输入的密码不一致', 'error')
    return
  }

  loading.value = true
  try {
    await register({ role: 3, ...form })
    toast('管理员注册成功，请登录')
    router.push('/login')
  } catch (e) {
    /* 错误由请求拦截器统一提示 */
  } finally {
    loading.value = false
  }
}
</script>
