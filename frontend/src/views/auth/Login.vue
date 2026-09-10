<template>
  <div class="auth-wrap">
    <div class="auth-card card">
      <h1 class="brand-large">食愿</h1>
      <p class="brand-sub">校园餐饮帮扶平台</p>

      <div class="tabs" style="margin-top:20px">
        <button v-for="r in roles" :key="r.value" class="tab" :class="{ active: role === r.value }" @click="switchRole(r.value)">
          {{ r.label }}
        </button>
      </div>

      <form @submit.prevent="submit">
        <div class="form-item">
          <label>{{ role === 1 ? '学号' : role === 2 ? '账号' : '账号（admin）' }}</label>
          <input class="input" v-model.trim="form.login_name" :placeholder="role === 1 ? '请输入学号' : '请输入账号'" />
        </div>
        <div class="form-item">
          <label>密码</label>
          <input class="input" type="password" v-model="form.password" placeholder="请输入密码" />
        </div>
        <button class="btn btn-primary btn-block" type="submit" :disabled="loading">
          {{ loading ? '登录中…' : '登 录' }}
        </button>
      </form>

      <div class="auth-links">
        <router-link to="/forgot">忘记密码</router-link>
        <span class="sep">|</span>
        <router-link v-if="role === 1" to="/register/student">学生注册</router-link>
        <router-link v-else-if="role === 2" to="/register/merchant">商家入驻</router-link>
      </div>
    </div>
  </div>
</template>

<script setup>
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../../stores/user'
import { toast } from '../../utils/toast'

const roles = [
  { label: '学生', value: 1 },
  { label: '商家', value: 2 },
  { label: '管理员', value: 3 }
]

const router = useRouter()
const authStore = useAuthStore()
const role = ref(1)
const loading = ref(false)
const form = reactive({ login_name: '', password: '' })

function switchRole(value) {
  role.value = value
  form.login_name = ''
}

async function submit() {
  if (!form.login_name || !form.password) { toast('请输入账号和密码', 'error'); return }
  loading.value = true
  try {
    const user = await authStore.login({ login_name: form.login_name, password: form.password, role: role.value })
    toast('登录成功，欢迎回来')
    const home = { 1: '/home', 2: '/merchant/home', 3: '/admin/dashboard' }
    router.push(home[user.role] || '/home')
  } catch (e) {
    /* 错误已由拦截器提示 */
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.auth-wrap { display: flex; justify-content: center; padding-top: 8vh; }
.auth-card { width: 100%; max-width: 400px; text-align: center; }
.brand-large { color: var(--primary); font-size: 40px; margin: 0 0 4px; }
.brand-sub { color: var(--muted); margin: 0 0 8px; }
.auth-links { margin-top: 16px; font-size: 14px; }
.auth-links a { color: var(--primary); text-decoration: none; }
.sep { color: var(--border); margin: 0 8px; }
</style>