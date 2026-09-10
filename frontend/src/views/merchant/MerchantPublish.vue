<template>
  <div>
    <button class="btn btn-sm" @click="$router.back()">← 返回</button>
    <h2 class="page-title">发布商品</h2>

    <div class="card">
      <div class="form-item"><label>商品名称</label><input class="input" v-model.trim="form.title" placeholder="如：水煮鱼片 超值套餐" /></div>

      <div class="form-item">
        <label>品类</label>
        <select class="select" v-model="form.category">
          <option v-for="c in CATS" :key="c" :value="c">{{ c }}</option>
        </select>
      </div>

      <div class="form-item">
        <label>商品描述</label>
        <textarea class="input" v-model.trim="form.description" placeholder="描述口味、份量等"></textarea>
      </div>

      <div class="form-item">
        <label>商品图片</label>
        <label class="upload">
          <img v-if="form.image" :src="form.image" alt="" />
          <template v-else><span>上传商品图<br />（可选）</span></template>
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
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import MapPicker from '../../components/MapPicker.vue'
import { publishProduct } from '../../api/merchant'
import { toast } from '../../utils/toast'

const CATS = ['简餐', '饮品', '烘焙', '水果', '家常菜', '川菜', '粤菜', '其他']
const router = useRouter()
const saving = ref(false)
const riskNote = ref('')
const coords = ref({ lat: null, lng: null })
const form = reactive({ title: '', category: '简餐', description: '', image: '', original_price: null, discount_price: null, quantity: 1, expire_time: '', location: '' })

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
  if (!form.title || form.original_price == null || form.discount_price == null || !form.expire_time || !form.location) {
    toast('请填写完整信息并选择取货位置', 'error'); return
  }
  if (form.discount_price >= form.original_price) { riskNote.value = '价格异常：折扣价不得高于或等于原价'; return }
  if (!coords.value.lat || !coords.value.lng) { toast('请在地图上选择取货点', 'error'); return }
  const expire = form.expire_time.replace('T', ' ')
  saving.value = true
  try {
    await publishProduct({ ...form, expire_time: expire, lat: coords.value.lat, lng: coords.value.lng })
    toast('发布成功')
    router.push('/merchant/home')
  } catch (e) {
    riskNote.value = e.message || '发布失败'
  } finally { saving.value = false }
}
</script>

<style scoped>
.page-title { margin: 4px 0 16px; }
.row2 { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
.upload { width: 120px; height: 90px; border: 1px dashed var(--border); border-radius: 8px; display: flex; align-items: center; justify-content: center; color: var(--muted); font-size: 13px; text-align: center; background: #fafafa; cursor: pointer; overflow: hidden; }
.upload img { width: 100%; height: 100%; object-fit: cover; }
.risk-banner { background: #fee2e2; color: #dc2626; border-radius: 8px; padding: 10px 12px; font-size: 13px; margin: 0 0 12px; }
</style>