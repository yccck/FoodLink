<template>
  <div class="login-page">
    <div class="login-shell">
      <section class="welcome-panel">
        <div class="welcome-brand">
          <BrandLogo size="large" />
        </div>
        <div class="welcome-copy">
          <span class="welcome-tag">校园里的温暖好食光</span>
          <h1>每一份好食物<br />都值得被好好接住</h1>
          <p>连接校园、商家与同学，让剩余食物找到需要它的人。</p>
        </div>
        <div class="welcome-points">
          <span>🍱 减少浪费</span>
          <span>🌱 温暖互助</span>
          <span>🧡 安心领取</span>
        </div>
        <span class="doodle doodle-one" aria-hidden>🌿</span>
        <span class="doodle doodle-two" aria-hidden>🍊</span>
      </section>

      <section class="login-card">
        <div class="mobile-brand">
          <BrandLogo size="medium" />
        </div>
        <p class="login-kicker">欢迎回到食愿</p>
        <h2>登录账号</h2>

        <div class="role-tabs">
          <button v-for="r in roles" :key="r.value" type="button" :class="{ active: role === r.value }" @click="switchRole(r.value)">
            {{ r.label }}
          </button>
        </div>

        <form @submit.prevent="submit">
          <div class="form-item">
            <label>{{ role === 1 ? '学号' : role === 2 ? '商家账号' : '管理员账号' }}</label>
            <input class="input login-input" v-model.trim="form.login_name" :placeholder="role === 1 ? '请输入学号' : role === 2 ? '请输入商家账号' : '请输入管理员账号'" autocomplete="username" />
          </div>
          <div class="form-item">
            <label>密码</label>
            <input class="input login-input" type="password" v-model="form.password" placeholder="请输入密码" autocomplete="current-password" />
          </div>
          <button class="login-button" type="submit" :disabled="loading">
            {{ loading ? '登录中…' : '登录' }}
          </button>
        </form>

        <div class="auth-links">
          <router-link to="/forgot">忘记密码</router-link>
          <span class="sep">|</span>
          <router-link v-if="role === 1" to="/register/student">注册新账号</router-link>
          <router-link v-else-if="role === 2" to="/register/merchant">商家注册</router-link>
          <router-link v-else to="/register/admin">管理员注册</router-link>
        </div>
      </section>
    </div>
  </div>
</template>

<script setup>
import { reactive, ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import BrandLogo from '../../components/BrandLogo.vue'
import { useAuthStore } from '../../stores/user'
import { toast } from '../../utils/toast'

const roles = [
  { label: '学生', value: 1 },
  { label: '商家', value: 2 },
  { label: '管理员', value: 3 }
]

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()
const role = ref(1)
const loading = ref(false)
const form = reactive({ login_name: '', password: '' })

onMounted(() => {
  const r = Number(route.query.role)
  if ([1, 2, 3].includes(r)) switchRole(r)
})

function switchRole(value) {
  role.value = value
  form.login_name = ''
  form.password = ''
}

async function submit() {
  if (!form.login_name || !form.password) { toast('请输入账号和密码', 'error'); return }
  loading.value = true
  try {
    const user = await authStore.login({ login_name: form.login_name, password: form.password, role: role.value })
    toast('登录成功，欢迎回来')
    const home = { 1: '/home', 2: '/merchant/home', 3: '/admin/dashboard' }
    const redirect = typeof route.query.redirect === 'string' && route.query.redirect.startsWith('/')
      ? route.query.redirect
      : ''
    router.push(redirect || home[user.role] || '/home')
  } catch (e) {
    /* 错误已由拦截器提示 */
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-page { min-height: 100vh; display: grid; background: radial-gradient(circle at 10% 18%, rgba(255,187,78,.30), transparent 24%), radial-gradient(circle at 88% 12%, rgba(42,126,89,.18), transparent 24%), #fff9ed; }
.login-shell { width: 100%; min-height: 100vh; display: grid; grid-template-columns: 1.05fr .95fr; background: #fffef9; }
.welcome-panel { position: relative; display: flex; flex-direction: column; justify-content: space-between; overflow: hidden; padding: 40px; background: linear-gradient(150deg,#e8f2de 0%,#fff0c8 100%); }
.welcome-brand { display: flex; width: 100%; justify-content: center; transform: translateX(-10px); }
.welcome-copy { position: relative; z-index: 1; }
.welcome-tag { display: inline-flex; padding: 7px 12px; border-radius: 999px; background: rgba(255,255,255,.72); color: #12634c; font-size: 13px; font-weight: 800; }
.welcome-copy h1 { margin: 22px 0 14px; color: #2f4033; font-size: clamp(31px,4vw,45px); line-height: 1.2; letter-spacing: -.045em; }
.welcome-copy p { max-width: 390px; margin: 0; color: #667064; font-size: 16px; line-height: 1.8; }
.welcome-points { position: relative; z-index: 1; display: flex; flex-wrap: wrap; gap: 8px; }
.welcome-points span { padding: 9px 12px; border: 1px solid rgba(53,105,68,.10); border-radius: 14px; background: rgba(255,255,255,.72); color: #4b5d4e; font-size: 13px; font-weight: 700; }
.doodle { position: absolute; opacity: .18; filter: saturate(.8); }
.doodle-one { right: -20px; top: 90px; font-size: 118px; transform: rotate(15deg); }
.doodle-two { right: 42px; bottom: 88px; font-size: 70px; }
.login-card { display: flex; flex-direction: column; justify-content: center; padding: 46px; }
.mobile-brand { display: none; width: 100%; justify-content: center; margin-bottom: 10px; }
.login-kicker { margin: 0 0 5px; color: #df7048; font-size: 14px; font-weight: 800; }
.login-card h2 { margin: 0 0 24px; color: #40382f; font-size: 30px; letter-spacing: -.03em; }
.role-tabs { display: grid; grid-template-columns: repeat(3,1fr); gap: 6px; margin-bottom: 24px; padding: 6px; border-radius: 18px; background: #f7ecda; }
.role-tabs button { min-height: 42px; border: 0; border-radius: 14px; background: transparent; color: #7b7168; font-size: 14px; font-weight: 700; cursor: pointer; }
.role-tabs button.active { background: #fff; color: #db6c46; box-shadow: 0 4px 12px rgba(86,62,38,.08); }
.login-input { min-height: 49px; padding: 11px 15px; border-color: #e3d5c1; border-radius: 16px; }
.login-input:focus { border-color: #e97950; box-shadow: 0 0 0 4px rgba(233,121,80,.10); }
.login-button { width: 100%; min-height: 50px; margin-top: 4px; border: 0; border-radius: 999px; background: #e97950; color: #fff; font-size: 16px; font-weight: 800; cursor: pointer; box-shadow: 0 8px 18px rgba(218,98,61,.20); }
.login-button:disabled { opacity: .55; cursor: not-allowed; }
.auth-links { margin-top: 20px; color: #d8c7b2; font-size: 14px; text-align: center; }
.auth-links a { color: #d8623e; font-weight: 700; text-decoration: none; }
.sep { margin: 0 12px; color: #ddcebb; }
@media (max-width: 760px) { .login-shell { grid-template-columns: 1fr; } .welcome-panel { display: none; } .login-card { padding: 34px 28px; } .mobile-brand { display: flex; } .login-kicker, .login-card h2 { text-align: center; } }
@media (max-width: 420px) { .login-card { padding: 28px 18px; } .role-tabs button { font-size: 13px; } }
</style>
