<template>
  <div>
    <button class="btn btn-sm" @click="$router.back()">← 返回</button>
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
        <div class="form-item"><label>原价（元）</label><input class="input" type="number" min="0" step="0.01" v-model.number="form.original_price" placeholder="28" /></div>
        <div class="form-item"><label>折扣价（元）</label><input class="input" type="number" min="0" step="0.01" v-model.number="form.discount_price" placeholder="12" /></div>
      </div>

      <div class="row2">
        <div class="form-item"><label>数量（份）</label><input class="input" type="number" min="1" v-model.number="form.quantity" placeholder="10" /></div>
        <div class="form-item"><label>截止有效期</label><input class="input" type="datetime-local" v-model="form.expire_time" /></div>
      </div>

      <div class="form-item">
        <label>取货位置（地图选点）</label>
        <MapPicker v-model="coords" />
      </div>
      <div class="form-item">
        <label>取货地址</label>
        <input class="input" v-model.trim="form.location" placeholder="如：XX大学南门15米" />
      </div>

      <p v-if="riskNote" class="risk-banner">⛔ {{ riskNote }}</p>
      <button class="btn btn-primary btn-block" :disabled="saving" @click="submit">{{ saving ? '发布中…' : '发布商品（自动风控）' }}</button>
    </div>
  </div>
</template>

<script setup>
import { computed, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import MapPicker from '../../components/MapPicker.vue'
import { publishProduct } from '../../api/merchant'
import { toast } from '../../utils/toast'

const MODES = [
  { value: 'regular', label: '普通商品' },
  { value: 'blind_box', label: '惊喜盲盒' }
]
const CONTENT_TYPES = ['食品', '饮品']
const router = useRouter()
const saving = ref(false)
const riskNote = ref('')
const coords = ref({ lat: null, lng: null })
const saleMode = ref('regular')
const contentType = ref('食品')
const form = reactive({ title: '', description: '', image: '', original_price: null, discount_price: null, quantity: 1, expire_time: '', location: '' })
const category = computed(() => saleMode.value === 'blind_box' ? `${contentType.value}盲盒` : contentType.value)
const defaultBlindBoxTitle = computed(() => `${contentType.value}惊喜盲盒`)
const titlePlaceholder = computed(() => saleMode.value === 'blind_box' ? `留空将显示“${defaultBlindBoxTitle.value}”` : '如：水煮鱼片超值套餐')
const descriptionPlaceholder = computed(() => saleMode.value === 'blind_box' ? '可填写份量范围、过敏原等信息' : '可填写口味、份量等信息')

function onImage(e) {
  const file = e.target.files && e.target.files[0]
  if (!file) return
  if (file.size > 2 * 1024 * 1024) { toast('图片过大（最大2MB）', 'error'); e.target.value = ''; return }
  const r = new FileReader()
  r.onload = () => { form.image = r.result }
  r.readAsDataURL(file)
}

async function submit() {
  riskNote.value = ''
  const title = form.title || (saleMode.value === 'blind_box' ? defaultBlindBoxTitle.value : '')
  if (!title || form.original_price == null || form.discount_price == null || !form.expire_time || !form.location) {
    toast('请填写完整信息并选择取货位置', 'error'); return
  }
  if (form.discount_price >= form.original_price) { riskNote.value = '价格异常：折扣价不得高于或等于原价'; return }
  if (!coords.value.lat || !coords.value.lng) { toast('请在地图上选择取货点', 'error'); return }
  const expire = form.expire_time.replace('T', ' ')
  saving.value = true
  try {
    await publishProduct({ ...form, title, category: category.value, expire_time: expire, lat: coords.value.lat, lng: coords.value.lng })
    toast('发布成功')
    router.push('/merchant/home')
  } catch (e) {
    riskNote.value = e.message || '发布失败'
  } finally { saving.value = false }
}
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
.row2 { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
.upload { width: 120px; height: 90px; border: 1px dashed var(--border); border-radius: 8px; display: flex; align-items: center; justify-content: center; color: var(--muted); font-size: 13px; text-align: center; background: #fafafa; cursor: pointer; overflow: hidden; }
.upload img { width: 100%; height: 100%; object-fit: cover; }
.risk-banner { background: #fee2e2; color: #dc2626; border-radius: 8px; padding: 10px 12px; font-size: 13px; margin: 0 0 12px; }
</style>
