<template>
  <div class="auth-wrap">
    <div class="auth-card auth-card-wide card">
      <BrandLogo size="medium" class="auth-brand" />

      <h1 class="auth-title">商家入驻</h1>

      <p class="auth-description">
        填写真实资料，让校园里的每一份好食物都被好好接住。
      </p>

      <form @submit.prevent="submit">
        <section class="form-section form-section-green">
          <h2 class="form-section-title">店铺信息</h2>

          <div class="form-grid">
            <div class="form-item">
              <label>店铺名称</label>
              <input
                v-model.trim="form.shop_name"
                class="input"
                placeholder="请输入店铺名称"
              />
            </div>

            <div class="form-item">
              <label>联系方式</label>
              <input
                v-model.trim="form.phone"
                class="input"
                placeholder="手机号或邮箱"
              />
            </div>

            <div class="form-item form-item-full">
              <label>详细地址</label>
              <input
                v-model.trim="form.location"
                class="input"
                placeholder="例如：XX大学南门15米"
              />
            </div>
          </div>
        </section>

        <div class="form-item">
          <label>店铺位置（地图选点）</label>
          <MapPicker v-model="coords" />
        </div>

        <section class="qualification-section">
          <div class="section-heading-row">
            <h2 class="form-section-title">经营资质</h2>
            <span class="upload-format">支持 JPG、PNG 等图片</span>
          </div>

          <div class="upload-grid">
            <label
              v-for="item in uploadFields"
              :key="item.key"
              class="upload-card"
              :class="{ filled: !!form[item.key] }"
            >
              <input
                type="file"
                accept="image/*"
                hidden
                @change="onFile(item.key, $event)"
              />

              <div
                v-if="form[item.key]"
                class="upload-preview"
              >
                <img
                  :src="form[item.key]"
                  :alt="item.label"
                />

                <span class="upload-replace">
                  点击重新上传
                </span>
              </div>

              <template v-else>
                <span class="upload-icon">
                  {{ item.icon }}
                </span>

                <span class="upload-content">
                  <strong>{{ item.label }}</strong>
                  <small>{{ item.hint }}</small>
                </span>
              </template>
            </label>
          </div>
        </section>

        <div class="review-notice">
          <span class="review-notice-icon">◷</span>

          <div>
            <strong>审核时间一般为1–3天</strong>
            <p>
              资料仅用于平台资质审核，请确保上传内容真实、清晰并且在有效期内。
            </p>
          </div>
        </div>

        <section class="form-section">
          <h2 class="form-section-title">账号信息</h2>

          <div class="form-grid">
            <div class="form-item">
              <label>商家账号</label>
              <input
                v-model.trim="form.login_name"
                class="input"
                placeholder="设置登录账号"
                autocomplete="username"
              />
            </div>

            <div class="form-item">
              <label>密码</label>
              <input
                v-model="form.password"
                class="input"
                type="password"
                placeholder="设置密码"
                autocomplete="new-password"
              />
            </div>

            <div class="form-item form-item-full">
              <label>确认密码</label>
              <input
                v-model="confirmPassword"
                class="input"
                type="password"
                placeholder="再次输入密码"
                autocomplete="new-password"
              />
            </div>
          </div>
        </section>

        <button
          class="btn btn-primary btn-block auth-submit"
          type="submit"
          :disabled="loading"
        >
          {{ loading ? '提交中…' : '提交入驻申请' }}
        </button>
      </form>

      <div class="auth-links">
        已有账号？
        <router-link to="/login">返回登录</router-link>
      </div>
    </div>
  </div>
</template>

<script setup>
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import BrandLogo from '../../components/BrandLogo.vue'
import MapPicker from '../../components/MapPicker.vue'
import { register } from '../../api/auth'
import { toast } from '../../utils/toast'

const router = useRouter()

const loading = ref(false)
const confirmPassword = ref('')

const coords = ref({
  lat: null,
  lng: null
})

const form = reactive({
  shop_name: '',
  phone: '',
  location: '',
  login_name: '',
  password: '',

  // 商家资质材料
  storefront_img: '',
  legal_person_id_img: '',
  license_img: '',
  permit_img: '',
  bank_card_img: ''
})

const uploadFields = [
  {
    key: 'storefront_img',
    label: '实体店铺图',
    hint: '上传店铺门面清晰照片',
    icon: '🏪'
  },
  {
    key: 'legal_person_id_img',
    label: '法人身份证',
    hint: '确保证件信息完整可辨',
    icon: '🪪'
  },
  {
    key: 'license_img',
    label: '营业执照',
    hint: '上传有效期内的营业执照',
    icon: '📄'
  },
  {
    key: 'permit_img',
    label: '许可证',
    hint: '上传食品经营等相关许可证',
    icon: '✅'
  },
  {
    key: 'bank_card_img',
    label: '法人或公司账户银行卡',
    hint: '用于核验收款账户信息',
    icon: '💳'
  }
]

function isValidContact(value) {
  const phonePattern = /^\d{8,11}$/
  const emailPattern = /^[^\s@]+@[^\s@]+\.[^\s@]+$/

  return phonePattern.test(value) || emailPattern.test(value)
}

function onFile(field, event) {
  const file = event.target.files?.[0]

  if (!file) return

  if (!file.type.startsWith('image/')) {
    toast('请上传图片文件', 'error')
    event.target.value = ''
    return
  }

  if (file.size > 5 * 1024 * 1024) {
    toast('单张图片不能超过5MB', 'error')
    event.target.value = ''
    return
  }

  const reader = new FileReader()

  reader.onload = () => {
    form[field] = reader.result
  }

  reader.readAsDataURL(file)
}

function allQualificationsUploaded() {
  return uploadFields.every((item) => Boolean(form[item.key]))
}

async function submit() {
  if (
    !form.shop_name ||
    !form.phone ||
    !form.location ||
    !form.login_name ||
    !form.password
  ) {
    toast('请填写完整的店铺与账号信息', 'error')
    return
  }

  if (!isValidContact(form.phone)) {
    toast('请输入正确的手机号或邮箱', 'error')
    return
  }

  if (!allQualificationsUploaded()) {
    toast('请上传全部商家资质材料', 'error')
    return
  }

  if (coords.value.lat == null || coords.value.lng == null) {
    toast('请在地图上选择店铺位置', 'error')
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
    await register({
      role: 2,
      ...form,
      lat: coords.value.lat,
      lng: coords.value.lng
    })

    toast('提交成功，平台将在1–3天内完成审核')
    router.push('/login')
  } catch (error) {
    // 接口错误由请求拦截器统一处理
  } finally {
    loading.value = false
  }
}
</script>