<template>
  <div>
    <h2 class="page-title">商家审核</h2>
    <p class="sub">待审：{{ joins }} 家入驻 · {{ updates }} 项资料更新</p>

    <div v-if="loading" class="empty">加载中…</div>
    <div v-else-if="!list.length" class="empty"><div class="big">✅</div>暂无待审核商家</div>

    <div v-for="m in list" :key="m.id" class="card beau">
      <div class="b-head">
        <div class="b-title">{{ m.shop_name }}</div>
        <span class="pending-tag" :class="m.audit_type === 'profile' ? 'tag-update' : 'tag-join'">{{ m.audit_type === 'profile' ? '资料更新' : '待入驻' }}</span>
      </div>
      <div v-if="m.audit_type === 'profile'" class="b-old">原店名：{{ m.old_shop_name }}</div>
      <div class="b-license">
        <img v-if="m.license_img" :src="m.license_img" alt="营业执照" />
        <span v-else>营业执照（示例）未上传</span>
      </div>
      <div class="b-meta">位置：{{ m.location }}（{{ m.lat }}, {{ m.lng }}）</div>
      <div class="b-meta">账号：{{ m.login_name }} · 手机：{{ m.phone }}</div>
      <div class="b-meta">提交时间：{{ m.created_at }}</div>
      <div v-if="m.categories && m.categories.length" class="b-meta cats-row"><span v-for="c in m.categories" :key="c" class="cat-tag">{{ c }}</span></div>
      <div class="b-actions">
        <button class="btn btn-primary btn-sm" @click="audit(m, 1)">通过</button>
        <button class="btn btn-sm" @click="audit(m, 2)">驳回</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { getPendingMerchants, auditMerchant } from '../../api/admin'
import { toast } from '../../utils/toast'

const list = ref([])
const loading = ref(false)
const joins = computed(() => list.value.filter(m => m.audit_type !== 'profile').length)
const updates = computed(() => list.value.filter(m => m.audit_type === 'profile').length)

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
.pending-tag { font-size: 12px; padding: 2px 10px; border-radius: 10px; }
.tag-join { background: #fef3c7; color: #b45309; }
.tag-update { background: #a7f3d0; color: #047857; }
.b-old { color: #8a938e; font-size: 12px; margin-bottom: 8px; }
.b-license { height: 90px; border: 1px dashed var(--border); border-radius: 8px; background: #fafafa; display: flex; align-items: center; justify-content: center; color: var(--muted); font-size: 13px; margin-bottom: 10px; overflow: hidden; }
.b-license img { width: 100%; height: 100%; object-fit: cover; }
.b-meta { color: var(--muted); font-size: 13px; margin-top: 3px; }
.cats-row { display: flex; flex-wrap: wrap; gap: 6px; }
.cat-tag { display: inline-block; padding: 2px 10px; border-radius: 999px; background: #e4f2e9; color: #17633a; font-size: 12px; }
.b-actions { display: flex; gap: 10px; margin-top: 12px; }
</style>