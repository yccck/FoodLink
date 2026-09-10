<template>
  <div>
    <h2 class="page-title">商家入驻审核</h2>
    <p class="sub">待审核商家：{{ list.length }} 家</p>

    <div v-if="loading" class="empty">加载中…</div>
    <div v-else-if="!list.length" class="empty"><div class="big">✅</div>暂无待审核商家</div>

    <div v-for="m in list" :key="m.id" class="card beau">
      <div class="b-head">
        <div class="b-title">{{ m.shop_name }}</div>
        <span class="pending-tag">待审核</span>
      </div>
      <div class="b-license">
        <img v-if="m.license_img" :src="m.license_img" alt="营业执照" />
        <span v-else>营业执照（示例）未上传</span>
      </div>
      <div class="b-meta">位置：{{ m.location }}（{{ m.lat }}, {{ m.lng }}）</div>
      <div class="b-meta">账号：{{ m.login_name }} · 手机：{{ m.phone }}</div>
      <div class="b-meta">提交时间：{{ m.created_at }}</div>
      <div class="b-actions">
        <button class="btn btn-primary btn-sm" @click="audit(m, 1)">通过</button>
        <button class="btn btn-sm" @click="audit(m, 2)">驳回</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { getPendingMerchants, auditMerchant } from '../../api/admin'
import { toast } from '../../utils/toast'

const list = ref([])
const loading = ref(false)

async function load() {
  loading.value = true
  try { list.value = await getPendingMerchants() } catch (e) { /* 拦截器 */ } finally { loading.value = false }
}
async function audit(m, status) {
  const label = status === 1 ? '通过' : '驳回'
  try {
    await auditMerchant(m.id, status)
    toast(`已${label} ${m.shop_name}`)
    await load()
  } catch (e) { /* 拦截器 */ }
}
onMounted(load)
</script>

<style scoped>
.page-title { margin: 4px 0 0; }
.sub { color: var(--muted); font-size: 13px; margin: 2px 0 16px; }
.b-head { display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; }
.b-title { font-size: 18px; font-weight: 700; }
.pending-tag { background: #fef3c7; color: #b45309; font-size: 12px; padding: 2px 10px; border-radius: 10px; }
.b-license { height: 90px; border: 1px dashed var(--border); border-radius: 8px; background: #fafafa; display: flex; align-items: center; justify-content: center; color: var(--muted); font-size: 13px; margin-bottom: 10px; overflow: hidden; }
.b-license img { width: 100%; height: 100%; object-fit: cover; }
.b-meta { color: var(--muted); font-size: 13px; margin-top: 3px; }
.b-actions { display: flex; gap: 10px; margin-top: 12px; }
</style>