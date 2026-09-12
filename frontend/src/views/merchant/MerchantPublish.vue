<template>
  <div>
    <h2 class="page-title">发布商品</h2>

    <div class="card">
      <div class="form-item">
        <label>商品形式</label>
        <div class="option-group" role="group" aria-label="商品形式">
          <button
            v-for="mode in MODES"
            :key="mode.value"
            type="button"
            class="option-button"
            :class="{ active: saleMode === mode.value }"
            @click="saleMode = mode.value"
          >
            {{ mode.label }}
          </button>
        </div>
      </div>

      <div class="form-item">
        <label>商品内容</label>
        <div class="option-group" role="group" aria-label="商品内容类型">
          <button
            v-for="type in CONTENT_TYPES"
            :key="type"
            type="button"
            class="option-button"
            :class="{ active: contentType === type }"
            @click="contentType = type"
          >
            {{ type }}
          </button>
        </div>
      </div>

      <div class="form-item">
        <label>商品名称{{ saleMode === 'blind_box' ? '（可选）' : '' }}</label>
        <input class="input" v-model.trim="form.title" :placeholder="titlePlaceholder" />
      </div>

      <div class="form-item">
        <label>商品描述（可选）</label>
        <textarea class="input" v-model.trim="form.description" :placeholder="descriptionPlaceholder"></textarea>
      </div>

      <div class="form-item">
        <label>商品图片（可选）</label>
        <label class="upload">
          <img v-if="form.image" :src="form.image" alt="" />
          <template v-else><span>上传商品图</span></template>
          <input type="file" accept="image/*" hidden @change="onImage" />
        </label>
      </div>

      <div class="row2">
        <div class="form-item"><label>原价（元）</label><input class="input price-input" type="number" min="0" step="0.01" v-model.number="form.original_price" placeholder="请输入原价" /></div>
        <div class="form-item"><label>折扣价（元）</label><input class="input price-input" type="number" min="0" step="0.01" v-model.number="form.discount_price" placeholder="请输入折扣价" /></div>
      </div>

      <div class="row2">
        <div class="form-item"><label>数量（份）</label><input class="input" type="number" min="1" v-model.number="form.quantity" placeholder="10" /></div>
        <div class="form-item">
          <label>截止有效期</label>
          <div class="date-confirm-row">
            <input class="input" type="datetime-local" v-model="form.expire_time" aria-label="截止有效期" @input="dateConfirmed = false" @change="dateConfirmed = false" />
            <button class="date-confirm" type="button" :class="{ confirmed: dateConfirmed }" :disabled="!form.expire_time || dateConfirmed" @click="confirmExpireTime">
              {{ dateConfirmed ? '已确认' : '确认' }}
            </button>
          </div>
          <p v-if="dateConfirmed" class="field-confirmed">有效期已确认</p>
        </div>
      </div>

      <div class="form-item">
        <label>每日营业时间</label>
        <div class="business-hours">
          <label><span>开门</span><input class="input" type="time" v-model="form.business_open_time" /></label>
          <span class="time-separator">至</span>
          <label><span>关门</span><input class="input" type="time" v-model="form.business_close_time" /></label>
        </div>
        <p class="field-hint">学生下单后须在本营业日关门前领取；商品更早到期时，以有效期为准。</p>
      </div>

      <div class="form-item pickup-location-section">
        <label>取货地址</label>
        <div v-if="locationLoading" class="location-loading">正在读取商铺默认位置…</div>
        <template v-else>
          <div class="pickup-summary">
            <div class="pickup-copy">
              <span>{{ usingDefaultLocation ? '商铺默认位置' : '本次取货位置' }}</span>
              <strong>{{ form.location || '尚未设置取货地址' }}</strong>
              <small v-if="hasCoordinates">位置已标记，可直接发布</small>
            </div>
            <button type="button" class="location-change" @click="toggleLocationEditor">
              {{ editingLocation ? '完成' : (hasCoordinates ? '更改取货地址' : '设置取货地址') }}
            </button>
          </div>

          <div v-if="editingLocation" class="location-editor">
            <MapPicker v-model="coords" />
            <label class="address-label">详细地址</label>
            <input class="input" v-model.trim="form.location" placeholder="如：澳门科技大学学生餐厅取货点" />
            <button v-if="hasDefaultLocation" type="button" class="restore-location" @click="useDefaultLocation">
              使用商铺默认位置
            </button>
          </div>
        </template>
      </div>

      <p v-if="riskNote" class="risk-banner">⛔ {{ riskNote }}</p>
      <button class="btn btn-primary btn-block" :disabled="saving" @click="submit">{{ saving ? '发布中…' : '发布商品（自动风控）' }}</button>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import MapPicker from '../../components/MapPicker.vue'
import { publishProduct } from '../../api/merchant'
import { useAuthStore } from '../../stores/user'
import { toast } from '../../utils/toast'

const MODES = [
  { value: 'regular', label: '普通商品' },
  { value: 'blind_box', label: '惊喜盲盒' }
]
const CONTENT_TYPES = ['食品', '饮品']
const router = useRouter()
const authStore = useAuthStore()
const saving = ref(false)
const dateConfirmed = ref(false)
const riskNote = ref('')
const coords = ref({ lat: null, lng: null })
const locationLoading = ref(true)
const editingLocation = ref(false)
const defaultLocation = reactive({ location: '', lat: null, lng: null })
const saleMode = ref('regular')
const contentType = ref('食品')
const form = reactive({
  title: '', description: '', image: '', original_price: null, discount_price: null,
  quantity: 1, expire_time: '', business_open_time: '08:00', business_close_time: '22:00', location: ''
})
const category = computed(() => saleMode.value === 'blind_box' ? `${contentType.value}盲盒` : contentType.value)
const defaultBlindBoxTitle = computed(() => `${contentType.value}惊喜盲盒`)
const titlePlaceholder = computed(() => saleMode.value === 'blind_box' ? `留空将显示“${defaultBlindBoxTitle.value}”` : '如：水煮鱼片超值套餐')
const descriptionPlaceholder = computed(() => saleMode.value === 'blind_box' ? '可填写份量范围、过敏原等信息' : '可填写口味、份量等信息')
const hasCoordinates = computed(() => isCoordinate(coords.value.lat) && isCoordinate(coords.value.lng))
const hasDefaultLocation = computed(() => !!defaultLocation.location && isCoordinate(defaultLocation.lat) && isCoordinate(defaultLocation.lng))
const usingDefaultLocation = computed(() => hasDefaultLocation.value && form.location === defaultLocation.location &&
  Number(coords.value.lat) === Number(defaultLocation.lat) && Number(coords.value.lng) === Number(defaultLocation.lng))

function isCoordinate(value) {
  return value !== null && value !== undefined && value !== '' && Number.isFinite(Number(value))
}

function readMerchantLocation(profile) {
  const lat = isCoordinate(profile?.lat) ? Number(profile.lat) : null
  const lng = isCoordinate(profile?.lng) ? Number(profile.lng) : null
  defaultLocation.location = profile?.location || ''
  defaultLocation.lat = lat
  defaultLocation.lng = lng
}

function useDefaultLocation() {
  if (!hasDefaultLocation.value) return
  form.location = defaultLocation.location
  coords.value = { lat: defaultLocation.lat, lng: defaultLocation.lng }
  editingLocation.value = false
}

function toggleLocationEditor() {
  if (editingLocation.value && (!form.location || !hasCoordinates.value)) {
    toast('请填写地址并在地图上标记取货位置', 'error')
    return
  }
  editingLocation.value = !editingLocation.value
}

async function loadDefaultLocation() {
  locationLoading.value = true
  try {
    const profile = await authStore.refreshProfile()
    readMerchantLocation(profile)
  } catch (e) {
    readMerchantLocation(authStore.user)
  } finally {
    if (hasDefaultLocation.value) useDefaultLocation()
    else editingLocation.value = true
    locationLoading.value = false
  }
}

function onImage(e) {
  const file = e.target.files && e.target.files[0]
  if (!file) return
  if (file.size > 2 * 1024 * 1024) { toast('图片过大（最大2MB）', 'error'); e.target.value = ''; return }
  const r = new FileReader()
  r.onload = () => { form.image = r.result }
  r.readAsDataURL(file)
}

function confirmExpireTime() {
  if (!form.expire_time) {
    toast('请先选择商品有效期', 'error')
    return
  }
  const timestamp = new Date(form.expire_time).getTime()
  if (!Number.isFinite(timestamp)) {
    toast('请选择有效的截止时间', 'error')
    return
  }
  dateConfirmed.value = true
}

async function submit() {
  riskNote.value = ''
  if (locationLoading.value) { toast('正在读取商铺位置，请稍候'); return }
  if (!dateConfirmed.value) { toast('请选择截止有效期并点击确认', 'error'); return }
  const title = form.title || (saleMode.value === 'blind_box' ? defaultBlindBoxTitle.value : '')
  if (!title || form.original_price == null || form.discount_price == null || !form.expire_time ||
      !form.business_open_time || !form.business_close_time || !form.location) {
    toast('请填写完整信息并选择取货位置', 'error'); return
  }
  if (form.business_open_time === form.business_close_time) {
    toast('开门时间和关门时间不能相同', 'error'); return
  }
  if (form.discount_price >= form.original_price) { riskNote.value = '价格异常：折扣价不得高于或等于原价'; return }
  if (!hasCoordinates.value) { toast('请在地图上选择取货点', 'error'); return }
  const expireValue = form.expire_time.replace('T', ' ')
  const expire = expireValue.length === 16 ? `${expireValue}:00` : expireValue
  saving.value = true
  try {
    await publishProduct({ ...form, title, category: category.value, expire_time: expire, lat: coords.value.lat, lng: coords.value.lng })
    toast('发布成功')
    router.push('/merchant/home')
  } catch (e) {
    riskNote.value = e.message || '发布失败'
  } finally { saving.value = false }
}

onMounted(loadDefaultLocation)
</script>

<style scoped>
.page-title { margin: 4px 0 16px; }
.option-group { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; }
.option-button {
  min-height: 44px; padding: 9px 12px; border: 1px solid var(--border); border-radius: 8px;
  background: #fff; color: var(--muted); font-size: 14px; font-weight: 600; cursor: pointer;
}
.option-button:hover { border-color: #fdba74; color: var(--primary-dark); }
.option-button.active { border-color: var(--primary); background: #fff7ed; color: var(--primary-dark); box-shadow: inset 0 0 0 1px var(--primary); }
.option-button:focus-visible { outline: 3px solid rgba(249, 115, 22, .2); outline-offset: 2px; }
.price-input::placeholder { color: #cbd3ce; opacity: 1; }
.row2 { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
.date-confirm-row { display: flex; align-items: center; gap: 7px; }
.date-confirm-row .input { min-width: 0; flex: 1; }
.date-confirm { min-height: 42px; padding: 0 10px; border: 1px solid #e5a25f; border-radius: 7px; background: #fffaf2; color: #b85d16; font-size: 12px; font-weight: 700; white-space: nowrap; cursor: pointer; }
.date-confirm:hover:not(:disabled) { background: #fff1df; }
.date-confirm.confirmed { border-color: #a9d6b6; background: #effaf2; color: #267445; }
.date-confirm:disabled { cursor: default; opacity: .78; }
.field-confirmed { margin: 5px 0 0; color: #267445; font-size: 11px; }
.business-hours { display: grid; grid-template-columns: minmax(0, 1fr) auto minmax(0, 1fr); align-items: end; gap: 10px; }
.business-hours label { min-width: 0; }
.business-hours label span { display: block; margin-bottom: 5px; color: var(--muted); font-size: 12px; }
.time-separator { padding-bottom: 10px; color: var(--muted); font-size: 13px; }
.field-hint { margin: 6px 0 0; color: var(--muted); font-size: 12px; line-height: 1.5; }
.upload { width: 120px; height: 90px; border: 1px dashed var(--border); border-radius: 8px; display: flex; align-items: center; justify-content: center; color: var(--muted); font-size: 13px; text-align: center; background: #fafafa; cursor: pointer; overflow: hidden; }
.upload img { width: 100%; height: 100%; object-fit: cover; }
.pickup-location-section { margin-top: 4px; }
.location-loading { min-height: 64px; display: flex; align-items: center; color: var(--muted); font-size: 13px; border-top: 1px solid var(--border); border-bottom: 1px solid var(--border); }
.pickup-summary { min-height: 72px; display: flex; align-items: center; justify-content: space-between; gap: 18px; padding: 11px 0; border-top: 1px solid var(--border); border-bottom: 1px solid var(--border); }
.pickup-copy { min-width: 0; display: flex; flex-direction: column; gap: 3px; }
.pickup-copy span { color: var(--primary-dark); font-size: 12px; font-weight: 700; }
.pickup-copy strong { color: var(--text); font-size: 14px; overflow-wrap: anywhere; }
.pickup-copy small { color: var(--muted); font-size: 12px; }
.location-change, .restore-location { border: 0; background: transparent; color: var(--primary); font-size: 13px; font-weight: 700; cursor: pointer; white-space: nowrap; }
.location-change { flex-shrink: 0; padding: 8px 0 8px 10px; }
.location-editor { padding-top: 12px; }
.address-label { display: block; margin: 12px 0 6px; color: var(--muted); font-size: 12px; }
.restore-location { margin-top: 8px; padding: 5px 0; }
.risk-banner { background: #fee2e2; color: #dc2626; border-radius: 8px; padding: 10px 12px; font-size: 13px; margin: 0 0 12px; }
@media (max-width: 520px) {
  .date-confirm-row { align-items: stretch; }
  .date-confirm { padding-inline: 8px; }
  .pickup-summary { align-items: flex-start; }
  .location-change { max-width: 112px; white-space: normal; text-align: right; line-height: 1.35; }
}
</style>
