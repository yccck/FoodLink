<template>
  <div>
    <h2 class="page-title">风控日志</h2>

    <div class="tabs">
      <button v-for="t in tabs" :key="t.label" class="tab" :class="{ active: filter === t.value }" @click="filter = t.value; load()">{{ t.label }}</button>
    </div>

    <div v-if="loading" class="empty">加载中…</div>
    <div v-else-if="!logs.length" class="empty"><div class="big">🛡</div>暂无风控日志</div>

    <div v-else class="risk-grid">
      <div v-for="l in logs" :key="l.id" class="card risk">
        <div class="r-head">
          <div class="r-tags">
            <span class="r-type" :class="typeClass(l.risk_type)">{{ l.risk_type_name }}</span>
            <span class="r-source" :class="l.risk_source === 'ai' ? 'src-ai' : 'src-rule'">{{ l.risk_source === 'ai' ? 'AI' : '规则' }}</span>
          </div>
          <span :class="reviewClass(l.review_status)" class="r-review">{{ reviewText(l.review_status) }}</span>
        </div>
        <button class="r-prod" type="button" @click="openDetail(l)">{{ l.product_title }} · {{ l.shop_name }}</button>
        <div class="r-detail">原因：{{ l.risk_detail }}</div>
        <div class="r-meta">{{ l.created_at }}<span v-if="l.risk_code"> · code={{ l.risk_code }}</span></div>
        <div class="r-actions">
          <button class="btn btn-outline btn-sm" @click="openDetail(l)">查看商品详情</button>
          <template v-if="!l.is_resolved">
            <button class="btn btn-outline btn-sm danger" @click="resolve(l)">误判恢复</button>
            <button class="btn btn-sm danger-solid" :class="{ 'is-loading': l.confirming }" :disabled="l.confirming" @click="confirmBlock(l)">{{ l.confirming ? '确认中…' : '确认拦截' }}</button>
          </template>
          <span v-else :class="l.review_status === 1 ? 'done done-block' : 'done'">{{ l.review_status === 1 ? '✓ 已确认拦截' : '✓ 已误判恢复' }}</span>
        </div>
      </div>
    </div>

    <!-- 商品详情弹窗 -->
    <div v-if="detailOpen" class="mask" @click.self="detailOpen = false">
      <div class="modal">
        <div class="m-head">
          <h3>商品详情</h3>
          <button class="m-close" type="button" @click="detailOpen = false">×</button>
        </div>

        <div v-if="detailLoading" class="m-body empty">加载中…</div>
        <div v-else-if="!detail" class="m-body empty">未找到该商品，可能已被商家删除</div>
        <div v-else class="m-body">
          <div class="d-cover" :style="coverStyle">
            <img v-if="detail.image" :src="detail.image" :alt="detail.title" />
            <span v-else class="cover-emoji">{{ detail.emoji || '🍱' }}</span>
            <span v-if="detail.risk_flag" class="d-risk-badge">风控处理中</span>
          </div>

          <div class="d-title-row">
            <h4 class="d-title">{{ detail.title }}</h4>
            <span class="d-cat">{{ detail.category || '未分类' }}</span>
          </div>

          <div class="d-prices">
            <span class="d-price">¥{{ money(detail.discount_price) }}</span>
            <span class="d-origin">原价 ¥{{ money(detail.original_price) }}</span>
            <span class="d-off">省 ¥{{ money(Number(detail.original_price || 0) - Number(detail.discount_price || 0)) }}</span>
          </div>

          <p v-if="detail.description" class="d-desc">{{ detail.description }}</p>

          <div class="d-grid">
            <div class="d-item"><span class="d-k">剩余库存</span><span class="d-v">{{ detail.quantity }} 份</span></div>
            <div class="d-item"><span class="d-k">商品状态</span><span class="d-v">{{ statusText(detail.status) }}</span></div>
            <div class="d-item"><span class="d-k">领取截止</span><span class="d-v">{{ detail.expire_time }}</span></div>
            <div class="d-item"><span class="d-k">取货时间</span><span class="d-v">{{ detail.business_open_time }} - {{ detail.business_close_time }}</span></div>
            <div class="d-item"><span class="d-k">浏览量</span><span class="d-v">{{ detail.view_count ?? 0 }}</span></div>
            <div class="d-item"><span class="d-k">收藏数</span><span class="d-v">{{ detail.fav_count ?? 0 }}</span></div>
            <div class="d-item"><span class="d-k">已售</span><span class="d-v">{{ detail.order_count ?? 0 }}</span></div>
            <div class="d-item"><span class="d-k">发布时间</span><span class="d-v">{{ detail.created_at || '-' }}</span></div>
          </div>

          <div class="d-block">
            <div class="d-block-t">取货位置</div>
            <div class="d-block-c">{{ detail.location || '-' }}</div>
          </div>
          <div class="d-block">
            <div class="d-block-t">所属商家</div>
            <div class="d-block-c">
              {{ detail.merchant?.shop_name || currentLog?.shop_name || '-' }}
              <span v-if="detail.merchant?.location" class="d-sub">（{{ detail.merchant.location }}）</span>
            </div>
          </div>
        </div>

        <div class="m-foot">
          <button class="btn btn-ghost" type="button" @click="detailOpen = false">关闭</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, ref, onMounted } from 'vue'
import { getRiskLogs, resolveRiskLog, confirmRiskLog } from '../../api/admin'
import { getProduct } from '../../api/product'
import { toast } from '../../utils/toast'

const tabs = [{ label: '全部', value: '' }, { label: '未处理', value: '0' }, { label: '已处理', value: '1' }]
const filter = ref('')
const logs = ref([])
const loading = ref(false)

const detailOpen = ref(false)
const detailLoading = ref(false)
const detail = ref(null)
const currentLog = ref(null)

async function load() {
  loading.value = true
  try { logs.value = await getRiskLogs({ resolved: filter.value }) } catch (e) { /* 拦截器 */ } finally { loading.value = false }
}
async function resolve(l) {
  try { await resolveRiskLog(l.id); toast('已误判恢复，商品重新上架'); await load() }
  catch (e) { /* 拦截器 */ }
}

async function confirmBlock(l) {
  l.confirming = true
  try { await confirmRiskLog(l.id); toast('已确认拦截，商品维持风控挂起'); await load() }
  catch (e) { /* 拦截器 */ }
  finally { l.confirming = false }
}

function typeClass(t) { return { 1: 't-price', 2: 't-word', 3: 't-expire' }[t] || '' }
function reviewClass(rs) { return { 0: 'r-pending', 1: 'r-confirmed', 2: 'r-released' }[rs] || 'r-pending' }
function reviewText(rs) { return { 0: '待人工复核', 1: '已确认拦截', 2: '已误判恢复' }[rs] || '待人工复核' }
function money(v) { return Number(v || 0).toFixed(2) }
function statusText(s) {
  return { 0: '已售罄', 1: '在售', 2: '已下架', 3: '风控拦截' }[s] || '未知'
}

async function openDetail(l) {
  currentLog.value = l
  detail.value = null
  detailOpen.value = true
  detailLoading.value = true
  try { detail.value = await getProduct(l.product_id) }
  catch (e) { detail.value = null }
  finally { detailLoading.value = false }
}

const coverStyle = computed(() => ({
  background: `linear-gradient(135deg, ${detail.value?.gradient || '#ff9a56'} 0%, #f0f0f0 100%)`
}))

onMounted(load)
</script>

<style scoped>
.page-title { margin: 4px 0 16px; }

/* 双列分布 */
.risk-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 16px; align-items: start; }
.risk-grid .card { margin-bottom: 0; }

.r-head { display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; }
.r-tags { display: flex; align-items: center; gap: 6px; }
.r-type { font-size: 12px; padding: 2px 10px; border-radius: 10px; color: #fff; }
.t-price { background: #ef4444; }
.t-word { background: #8b5cf6; }
.t-expire { background: #f59e0b; }
.r-source { font-size: 11px; padding: 2px 8px; border-radius: 10px; font-weight: 600; letter-spacing: .3px; }
.src-ai { background: #eef2ff; color: #4f46e5; border: 1px solid #c7d2fe; }
.src-rule { background: #f1f5f9; color: #64748b; border: 1px solid #e2e8f0; }
.done { color: var(--success); font-size: 12px; }
.undone { color: var(--warn); font-size: 12px; }
.r-prod {
  display: block; width: 100%; text-align: left; font-weight: 600; font-size: 15px;
  background: none; border: 0; padding: 0; color: var(--text); cursor: pointer;
  font-family: inherit; line-height: 1.4;
}
.r-prod:hover { color: #d8613d; text-decoration: underline; }
.r-detail, .r-meta { color: var(--muted); font-size: 13px; margin-top: 4px; }
.r-actions { margin-top: 10px; display: flex; align-items: center; gap: 8px; flex-wrap: wrap; }
.btn-solid.is-loading { opacity: .7; cursor: progress; }

/* 人工复核状态徽标 */
.r-review { font-size: 12px; padding: 2px 10px; border-radius: 10px; font-weight: 600; }
.r-pending { background: #fffbeb; color: #b45309; border: 1px solid #fde68a; }
.r-confirmed { background: #fef2f2; color: #b91c1c; border: 1px solid #fecaca; }
.r-released { background: #ecfdf5; color: #047857; border: 1px solid #a7f3d0; }
.done-block { color: var(--warn); }

/* 复核动作按钮 */
.danger-solid { background: #ef4444; border-color: #ef4444; color: #fff; }
.danger-solid:hover { opacity: .92; }
.danger { color: #ef4444; border-color: #ef4444; }
.danger:hover { background: #ef4444; color: #fff; }

/* 弹窗 */
.mask { position: fixed; inset: 0; background: rgba(0,0,0,.45); display: flex; align-items: center; justify-content: center; z-index: 1000; padding: 20px; }
.modal { background: #fff; border-radius: 16px; width: 100%; max-width: 560px; max-height: 86vh; display: flex; flex-direction: column; overflow: hidden; }
.m-head { display: flex; align-items: center; justify-content: space-between; padding: 16px 20px; border-bottom: 1px solid var(--border); }
.m-head h3 { margin: 0; font-size: 17px; }
.m-close { background: none; border: 0; font-size: 24px; line-height: 1; cursor: pointer; color: var(--muted); }
.m-body { padding: 20px; overflow-y: auto; }
.m-foot { padding: 12px 20px; border-top: 1px solid var(--border); display: flex; justify-content: flex-end; }

.d-cover { position: relative; height: 180px; border-radius: 12px; overflow: hidden; display: flex; align-items: center; justify-content: center; }
.d-cover img { width: 100%; height: 100%; object-fit: cover; }
.cover-emoji { font-size: 56px; opacity: .9; }
.d-risk-badge {
  position: absolute; left: 0; top: 10px; color: #fff; font-size: 12px;
  padding: 4px 12px; border-radius: 0 10px 10px 0; background: linear-gradient(90deg,#f97316,#ef4444);
}
.d-title-row { display: flex; align-items: baseline; gap: 10px; margin: 14px 0 6px; }
.d-title { margin: 0; font-size: 18px; }
.d-cat { font-size: 12px; color: var(--muted); background: #f5f1ea; padding: 2px 8px; border-radius: 8px; }
.d-prices { display: flex; align-items: baseline; gap: 10px; }
.d-price { color: #e2603f; font-size: 22px; font-weight: 700; }
.d-origin { color: var(--muted); font-size: 13px; text-decoration: line-through; }
.d-off { font-size: 12px; color: var(--success); }
.d-desc { margin: 10px 0 0; color: var(--text); font-size: 14px; line-height: 1.6; }

.d-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-top: 16px; }
.d-item { background: #faf7f2; border-radius: 10px; padding: 8px 12px; display: flex; flex-direction: column; gap: 2px; }
.d-k { font-size: 12px; color: var(--muted); }
.d-v { font-size: 14px; font-weight: 600; }

.d-block { margin-top: 12px; }
.d-block-t { font-size: 12px; color: var(--muted); margin-bottom: 4px; }
.d-block-c { font-size: 14px; background: #faf7f2; border-radius: 10px; padding: 8px 12px; }
.d-sub { color: var(--muted); font-size: 12px; }

@media (max-width: 860px) {
  .risk-grid { grid-template-columns: 1fr; }
  .d-grid { grid-template-columns: 1fr; }
}
</style>
