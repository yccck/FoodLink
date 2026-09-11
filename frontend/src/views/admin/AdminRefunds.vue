<template>
  <div class="refund-review-page">
    <div class="page-heading">
      <div>
        <p>AFTER-SALES REVIEW</p>
        <h2>退款审核</h2>
      </div>
      <span>{{ status === 0 ? `${requests.length} 笔待处理` : statusText(status) }}</span>
    </div>

    <div class="tabs review-tabs" role="tablist" aria-label="退款审核状态">
      <button v-for="tab in tabs" :key="tab.label" class="tab" :class="{ active: status === tab.status }" @click="changeTab(tab.status)">{{ tab.label }}</button>
    </div>

    <div v-if="loading" class="empty">加载中…</div>
    <div v-else-if="!requests.length" class="empty"><div class="empty-mark">✓</div>暂无{{ currentLabel }}申请</div>

    <article v-for="item in requests" :key="item.id" class="card review-card">
      <header>
        <div>
          <small>订单 FL{{ String(item.order_id).padStart(6, '0') }}</small>
          <h3>{{ item.product_title }}</h3>
          <p>{{ item.shop_name }} · {{ item.student_name }} {{ item.student_id }}</p>
        </div>
        <span class="review-status" :class="`status-${item.status}`">{{ statusText(item.status) }}</span>
      </header>

      <div class="review-content">
        <div class="product-image">
          <img v-if="item.product_image" :src="item.product_image" :alt="item.product_title" />
          <span v-else>食愿</span>
        </div>
        <div class="claim-detail">
          <span>学生说明</span>
          <p>{{ item.reason }}</p>
          <small>提交时间 {{ item.created_at }} · 退款金额 ¥{{ money(item.total_amount) }}</small>
        </div>
        <a v-if="item.evidence_image" class="evidence" :href="item.evidence_image" target="_blank" rel="noreferrer">
          <img :src="item.evidence_image" alt="学生提交的食品问题照片" />
          <span>查看凭证</span>
        </a>
        <div v-else class="no-evidence">未附照片</div>
      </div>

      <div v-if="item.status === 0" class="audit-panel">
        <label :for="`remark-${item.id}`">审核说明</label>
        <textarea :id="`remark-${item.id}`" v-model="remarks[item.id]" class="input" maxlength="500" placeholder="驳回时必须填写原因" />
        <div>
          <button class="btn btn-sm" :disabled="auditingId === item.id" @click="audit(item, 2)">驳回</button>
          <button class="btn btn-primary btn-sm" :disabled="auditingId === item.id" @click="audit(item, 1)">{{ auditingId === item.id ? '处理中…' : '通过并退款' }}</button>
        </div>
      </div>
      <div v-else class="audit-result">
        <strong>{{ item.status === 1 ? '款项已原路退回' : '订单保持已结算' }}</strong>
        <span>{{ item.admin_remark || '无审核说明' }} · {{ item.reviewed_at }}</span>
      </div>
    </article>
  </div>
</template>

<script setup>
import { computed, ref } from 'vue'
import { auditRefundRequest, getRefundRequests } from '../../api/admin'
import { toast } from '../../utils/toast'

const tabs = [
  { label: '待审核', status: 0 },
  { label: '已通过', status: 1 },
  { label: '已驳回', status: 2 },
  { label: '全部', status: null }
]
const status = ref(0)
const requests = ref([])
const loading = ref(false)
const auditingId = ref(null)
const remarks = ref({})
const currentLabel = computed(() => tabs.find(tab => tab.status === status.value)?.label || '')

function money(value) { return Number(value || 0).toFixed(2) }
function statusText(value) { return ['待审核', '已通过', '已驳回'][value] || '未知' }

async function load() {
  loading.value = true
  try {
    requests.value = await getRefundRequests({ status: status.value === null ? '' : status.value })
  } catch (e) { /* 请求拦截器统一提示 */ } finally { loading.value = false }
}

function changeTab(value) {
  status.value = value
  load()
}

async function audit(item, auditStatus) {
  const remark = String(remarks.value[item.id] || '').trim()
  if (auditStatus === 2 && !remark) { toast('驳回时请填写审核说明', 'error'); return }
  auditingId.value = item.id
  try {
    await auditRefundRequest(item.id, auditStatus, remark)
    toast(auditStatus === 1 ? '审核通过，款项已原路退回' : '已驳回退款申请')
    await load()
  } catch (e) { /* 请求拦截器统一提示 */ } finally { auditingId.value = null }
}

load()
</script>

<style scoped>
.refund-review-page { --ink: #17211c; }
.page-heading { display: flex; align-items: flex-end; justify-content: space-between; gap: 18px; margin-bottom: 18px; }
.page-heading p { margin: 0 0 2px; color: #909a94; font-size: 10px; font-weight: 750; }
.page-heading h2 { margin: 0; font-size: 25px; }
.page-heading > span { padding-bottom: 3px; color: #a45a21; font-size: 12px; font-weight: 700; }
.review-tabs { width: max-content; max-width: 100%; gap: 2px; padding: 3px; border: 1px solid var(--border); border-radius: 8px; background: #fff; }
.review-tabs .tab { min-width: 70px; padding: 7px 12px; border: 0; border-radius: 6px; background: transparent; }
.review-tabs .tab.active { background: var(--ink); color: #fff; }
.empty-mark { margin-bottom: 6px; color: #a6b0aa; font-size: 30px; }
.review-card { padding: 18px; border-radius: 8px; }
.review-card header { display: flex; align-items: flex-start; justify-content: space-between; gap: 14px; }
.review-card header small { color: #9ca49f; font-size: 9px; }
.review-card h3 { margin: 2px 0 0; font-size: 17px; }
.review-card header p { margin: 3px 0 0; color: var(--muted); font-size: 11px; }
.review-status { flex: 0 0 auto; padding: 4px 9px; border-radius: 6px; background: #fff4df; color: #9a5d0b; font-size: 11px; font-weight: 700; }
.review-status.status-1 { background: #eaf8ef; color: #17713e; }
.review-status.status-2 { background: #f1f3f4; color: #66716b; }
.review-content { display: grid; grid-template-columns: 76px minmax(0, 1fr) 82px; gap: 13px; margin-top: 14px; padding-top: 14px; border-top: 1px solid #edf0ee; }
.product-image { display: flex; width: 76px; height: 76px; align-items: center; justify-content: center; overflow: hidden; border-radius: 7px; background: #eef1ef; color: #89938d; font-size: 11px; font-weight: 700; }
.product-image img { width: 100%; height: 100%; object-fit: cover; }
.claim-detail { min-width: 0; }
.claim-detail > span { color: #949d98; font-size: 10px; }
.claim-detail p { margin: 3px 0 6px; overflow-wrap: anywhere; color: #3f4943; font-size: 13px; line-height: 1.6; }
.claim-detail small { color: #929b96; font-size: 10px; }
.evidence { position: relative; display: block; width: 82px; height: 76px; overflow: hidden; border-radius: 7px; color: #fff; text-decoration: none; }
.evidence img { width: 100%; height: 100%; object-fit: cover; }
.evidence span { position: absolute; right: 0; bottom: 0; left: 0; padding: 3px; background: rgba(19, 27, 23, .68); font-size: 9px; text-align: center; }
.no-evidence { display: flex; width: 82px; height: 76px; align-items: center; justify-content: center; border: 1px dashed #d5dbd7; border-radius: 7px; color: #9ba39f; font-size: 10px; }
.audit-panel { margin-top: 14px; padding: 13px; background: #f7f9f8; }
.audit-panel label { display: block; margin-bottom: 5px; color: #68726c; font-size: 11px; font-weight: 700; }
.audit-panel textarea { min-height: 68px; font-size: 12px; }
.audit-panel > div { display: flex; justify-content: flex-end; gap: 8px; margin-top: 9px; }
.audit-result { display: flex; align-items: baseline; justify-content: space-between; gap: 12px; margin-top: 14px; padding: 10px 12px; background: #f7f9f8; }
.audit-result strong { color: #3b4841; font-size: 12px; }
.audit-result span { color: #858f89; font-size: 10px; text-align: right; }
@media (max-width: 560px) {
  .review-tabs { width: 100%; }
  .review-tabs .tab { flex: 1; min-width: 0; padding-inline: 5px; }
  .review-content { grid-template-columns: 66px minmax(0, 1fr); }
  .product-image { width: 66px; height: 66px; }
  .evidence, .no-evidence { grid-column: 2; width: 100%; height: 116px; }
  .audit-result { align-items: flex-start; flex-direction: column; gap: 3px; }
  .audit-result span { text-align: left; }
}
</style>
