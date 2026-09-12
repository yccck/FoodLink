<template>
  <div>
    <div v-if="loading" class="empty">加载中…</div>

    <template v-else>
      <div class="metrics">
        <div class="metric"><div class="mv">{{ s.total_users }}</div><div class="ml">用户总数</div></div>
        <div class="metric"><div class="mv">{{ s.total_orders }}</div><div class="ml">订单总量</div></div>
        <div class="metric"><div class="mv">{{ s.help.low_income_user_count }}</div><div class="ml">帮扶学生</div></div>
        <div class="metric"><div class="mv">{{ s.help.pickup_count }}</div><div class="ml">已领取订单</div></div>
        <div class="metric"><div class="mv">{{ s.pending_merchants }}</div><div class="ml">待审商家</div></div>
        <div class="metric"><div class="mv">{{ s.risk.active }}</div><div class="ml">未处理风控</div></div>
      </div>

      <div class="card">
        <h3 class="card-title">用户构成</h3>
        <div class="roles-grid">
          <div v-for="r in s.users_by_role" :key="r.label" class="role-card">
            <div class="rv">{{ r.value }}</div>
            <div class="rl">{{ r.label }}</div>
          </div>
        </div>
      </div>

      <div class="card">
        <h3 class="card-title">近7日订单量</h3>
        <LineChart :data="s.orders_by_day.map(d => ({ label: d.date.slice(5), shortLabel: d.date.slice(8), value: d.count }))" color="#3b82f6" />
      </div>

      <div class="card">
        <h3 class="card-title">风控拦截统计</h3>
        <div class="risk-row">
          <div class="info-card"><div class="iv">{{ s.risk.total }}</div><div class="il">总拦截</div></div>
          <div class="info-card"><div class="iv succ">{{ s.risk.resolved }}</div><div class="il">已恢复</div></div>
          <div class="info-card"><div class="iv warn">{{ s.risk.active }}</div><div class="il">未处理</div></div>
        </div>
        <div class="risk-types">
          <div v-for="t in s.risk_by_type" :key="t.label" class="type-card">
            <div class="tv" :style="{ color: riskColor(t.label) }">{{ t.value }}</div>
            <div class="tl">{{ t.label }}</div>
          </div>
        </div>
      </div>
    </template>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import LineChart from '../../components/LineChart.vue'
import { getStatistics } from '../../api/admin'

const s = ref({
  total_users: 0, total_orders: 0, pending_merchants: 0,
  help: { low_income_user_count: 0, pickup_count: 0 },
  risk: { total: 0, resolved: 0, active: 0 },
  users_by_role: [], orders_by_day: [], risk_by_type: []
})
const loading = ref(false)

function riskColor(label) {
  const t = label || ''
  if (t.includes('价格') || t.includes('折扣')) return '#dc2626'
  if (t.includes('敏感') || t.includes('违禁')) return '#ea580c'
  if (t.includes('有效期') || t.includes('时长') || t.includes('时间')) return '#f43f5e'
  return '#dc2626'
}

async function load() {
  loading.value = true
  try { s.value = await getStatistics() } catch (e) { /* 拦截器 */ } finally { loading.value = false }
}
onMounted(load)
</script>

<style scoped>
.page-title { margin: 4px 0 0; }
.sub { color: var(--muted); font-size: 13px; margin: 2px 0 16px; }
.metrics { display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; margin-bottom: 16px; }
.metric { background: #fff; border: 1px solid var(--border); border-radius: 12px; padding: 16px; text-align: center; }
.mv { font-size: 26px; font-weight: 800; color: var(--primary); }
.ml { color: var(--muted); font-size: 12px; margin-top: 2px; }
.risk-row { display: flex; gap: 12px; }
.info-card { flex: 1; background: #fff; border: 1px solid var(--border); border-radius: 10px; padding: 14px; text-align: center; }
.iv { font-size: 22px; font-weight: 800; color: #111827; }
.iv.succ { color: var(--success); }
.iv.warn { color: var(--warn); }
.il { color: var(--muted); font-size: 12px; margin-top: 2px; }

.roles-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; }
.role-card { background: #fff; border: 1px solid var(--border); border-radius: 12px; padding: 16px; text-align: center; }
.rv { font-size: 26px; font-weight: 800; color: var(--primary); }
.rl { color: var(--muted); font-size: 12px; margin-top: 2px; }
.risk-types { display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; margin-top: 16px; }
.type-card { background: #fff; border: 1px solid var(--border); border-radius: 12px; padding: 16px; text-align: center; }
.tv { font-size: 22px; font-weight: 800; color: #111827; }
.tl { color: var(--muted); font-size: 12px; margin-top: 2px; white-space: nowrap; }
</style>