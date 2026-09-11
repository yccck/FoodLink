<template>
  <div class="auth-wrap">
    <div class="auth-card card">
      <BrandLogo size="medium" class="auth-brand" />
      <h1 class="auth-title">忘记密码</h1>
      <p class="hint">验证身份通过后，密码将被重置为 <b>123456</b></p>

      <div class="tabs auth-role-tabs">
        <button v-for="r in roles" :key="r.value" type="button" class="tab" :class="{ active: role === r.value }" @click="role = r.value">
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

        <button class="btn btn-primary btn-block auth-submit" type="submit" :disabled="loading">
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
.hint { color: var(--muted); font-size: 13px; text-align: center; margin: 0 0 8px; }
</style>
