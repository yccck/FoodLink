<template>
  <div>
    <button class="btn btn-sm" @click="$router.push('/merchant/home')">← 返回</button>
    <h2 class="page-title">订单管理</h2>

    <div class="card verify-bar">
      <span class="vlabel">输入取货码核销：</span>
      <input class="input vinput" v-model.trim="code" maxlength="6" placeholder="6位取货码" />
      <button class="btn btn-primary btn-sm" @click="doVerify" :disabled="verifying">{{ verifying ? '核销中…' : '核销' }}</button>
    </div>

    <div class="tabs">
      <button v-for="t in tabs" :key="t.label" class="tab" :class="{ active: status === t.status }" @click="status = t.status; load()">{{ t.label }}</button>
    </div>

    <div v-if="loading" class="empty">加载中…</div>
    <div v-else-if="!orders.length" class="empty"><div class="big">🧾</div>暂无订单</div>

    <div v-for="o in orders" :key="o.id" class="card oder">
      <div class="o-top">
        <div class="o-prod"><span class="tag">{{ o.product_title }}</span></div>
        <span :class="statusClass(o.status)">{{ statusText(o.status) }}</span>
      </div>
      <div class="o-stud">学生：{{ o.student_name }}（{{ o.student_id }}）· {{ o.phone }}</div>
      <div class="o-info">
        <span class="price">¥{{ o.price }}</span> × {{ o.quantity }} · 下单 {{ o.created_at }}
      </div>
      <div class="o-foot">
        <span class="code">取货码：<b>{{ o.pickup_code || '—' }}</b></span>
        <button v-if="o.status === 0" class="btn btn-primary btn-sm" @click="pickup(o)">核销领取</button>
        <span v-else-if="o.status === 1" class="picked">已核销 {{ o.picked_at }}</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { getOrders, pickupOrder, verifyOrder } from '../../api/order'
import { toast } from '../../utils/toast'

const tabs = [{ label: '全部', status: null }, { label: '待领取', status: 0 }, { label: '已领取', status: 1 }]
const status = ref(null)
const orders = ref([])
const loading = ref(false)
const code = ref('')
const verifying = ref(false)

async function load() {
  loading.value = true
  try { orders.value = await getOrders({ status: status.value === null ? '' : status.value }) }
  catch (e) { /* 拦截器 */ } finally { loading.value = false }
}
async function pickup(o) {
  try { await pickupOrder(o.id); toast('已核销 ' + o.student_name); load() }
  catch (e) { /* 拦截器 */ }
}
async function doVerify() {
  if (!/^\d{6}$/.test(code.value)) { toast('请输入6位取货码', 'error'); return }
  verifying.value = true
  try { const o = await verifyOrder(code.value); toast(`核销成功：${o.student_name} 购买 ${o.product_title}`); code.value = ''; status.value = null; load() }
  catch (e) { /* 拦截器 */ } finally { verifying.value = false }
}
function statusText(s) { return ({ 0: '待领取', 1: '已领取', 2: '已过期' }[s] || '') }
function statusClass(s) { return ({ 0: 'st-pending', 1: 'st-picked' }[s] || '') }

load()
</script>

<style scoped>
.page-title { margin: 4px 0 16px; }
.verify-bar { display: flex; align-items: center; gap: 10px; }
.vlabel { font-size: 14px; color: var(--muted); flex-shrink: 0; }
.vinput { flex: 1; max-width: 200px; }
.o-top { display: flex; justify-content: space-between; align-items: center; }
.o-stud { color: var(--muted); font-size: 13px; margin: 8px 0 4px; }
.o-info { font-size: 13px; }
.code { color: var(--text); font-size: 14px; }
.o-foot { display: flex; justify-content: space-between; align-items: center; margin-top: 10px; padding-top: 8px; border-top: 1px dashed var(--border); }
.picked { color: var(--success); font-size: 12px; }
</style>