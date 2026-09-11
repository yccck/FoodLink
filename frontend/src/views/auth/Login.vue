<template>
  <div class="auth-wrap auth-wrap-login">
    <div class="auth-card card">
      <BrandLogo size="large" class="auth-brand" />

      <h1 class="auth-title">欢迎回来</h1>

      <div class="tabs auth-role-tabs">
        <button
          v-for="item in roles"
          :key="item.value"
          type="button"
          class="tab"
          :class="{ active: role === item.value }"
          @click="switchRole(item.value)"
        >
          {{ item.label }}
        </button>
      </div>

      <form @submit.prevent="submit">
        <div class="form-item">
          <label>
            {{ role === 1 ? '学号' : role === 2 ? '商家账号' : '管理员账号' }}
          </label>

          <input
            v-model.trim="form.login_name"
            class="input"
            :placeholder="accountPlaceholder"
            autocomplete="username"
          />
        </div>

        <div class="form-item">
          <label>密码</label>

          <input
            v-model="form.password"
            class="input"
            type="password"
            placeholder="请输入密码"
            autocomplete="current-password"
          />
        </div>

        <button
          class="btn btn-primary btn-block auth-submit"
          type="submit"
          :disabled="loading"
        >
          {{ loading ? '登录中…' : '登录' }}
        </button>
      </form>

      <!-- 注意：忘记密码必须放在注册前面 -->
      <div class="auth-links">
        <router-link to="/forgot">忘记密码</router-link>

        <span class="sep">|</span>

        <router-link
          v-if="role === 1"
          to="/register/student"
        >
          学生注册
        </router-link>

        <router-link
          v-else-if="role === 2"
          to="/register/merchant"
        >
          商家入驻
        </router-link>

        <router-link
          v-else
          to="/register/admin"
        >
          管理员注册
        </router-link>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import BrandLogo from '../../components/BrandLogo.vue'
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

const form = reactive({
  login_name: '',
  password: ''
})

const accountPlaceholder = computed(() => {
  if (role.value === 1) return '请输入学号'
  if (role.value === 2) return '请输入商家账号'
  return '请输入管理员账号'
})

function switchRole(value) {
  role.value = value
  form.login_name = ''
  form.password = ''
}

async function submit() {
  if (!form.login_name || !form.password) {
    toast('请输入账号和密码', 'error')
    return
  }

  loading.value = true

  try {
    const user = await authStore.login({
      login_name: form.login_name,
      password: form.password,
      role: role.value
    })

    toast('登录成功，欢迎回来')

    if (user.role === 1) {
      router.push('/profile')
    } else if (user.role === 2) {
      toast('商家端页面建设中')
    } else {
      toast('管理端页面建设中')
    }
  } catch (error) {
    // 接口错误会由请求拦截器统一显示
  } finally {
    loading.value = false
  }
}
</script>