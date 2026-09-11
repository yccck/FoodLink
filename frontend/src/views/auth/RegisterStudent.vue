<template>
  <div class="auth-wrap">
    <div class="auth-card card">
      <BrandLogo size="medium" class="auth-brand" />
      <h1 class="auth-title">学生注册</h1>
      <p class="auth-description">使用真实的学校和学号信息完成注册。</p>
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
        <button class="btn btn-primary btn-block auth-submit" type="submit" :disabled="loading">
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
