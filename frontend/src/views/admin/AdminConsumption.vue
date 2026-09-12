<template>
  <div>
    <h2 class="page-title">优惠分配</h2>
    <p class="sub">按消费次数、消费金额降序排列学生，把平台盈利以奖励金形式自动划拨给学生</p>

    <div v-if="loading && !loaded" class="empty">加载中…</div>

    <template v-else>
      <div class="summary">
        <div class="metric"><div class="mv">¥{{ money(pool.platform_profit) }}</div><div class="ml">平台盈利累计</div></div>
        <div class="metric"><div class="mv">¥{{ money(pool.injected) }}</div><div class="ml">平台注入</div></div>
        <div class="metric"><div class="mv">¥{{ money(pool.granted) }}</div><div class="ml">已发放</div></div>
        <div class="metric highlight"><div class="mv">¥{{ money(pool.available) }}</div><div class="ml">可分配余额</div></div>
      </div>

      <div class="actions">
        <button class="btn btn-outline btn-sm" @click="showInject = true">注入补贴资金</button>
        <span class="hint">平台盈利 = 已结算订单服务费（0.1%）；余额不足时可先注入演示资金</span>
      </div>

      <div class="tabs">
        <button class="tab" :class="{ active: tab === 'rank' }" @click="tab = 'rank'">学生消费排行</button>
        <button class="tab" :class="{ active: tab === 'records' }" @click="tab = 'records'; loadGrants()">发放记录</button>
      </div>

      <!-- 学生消费排行 -->
      <template v-if="tab === 'rank'">
        <div class="toolbar">
          <div class="sorts">
            <button v-for="t in sortTabs" :key="t.value" class="tab sm" :class="{ active: sortBy === t.value }" @click="sortBy = t.value">
              {{ t.label }}
            </button>
          </div>
          <div class="grow"></div>
          <button class="btn btn-outline btn-sm" @click="selectTop(10)">帮扶前 10 名</button>
          <button class="btn btn-primary btn-sm" :disabled="!checked.length" @click="openGrant">
            发放优惠{{ checked.length ? `（${checked.length}人）` : '' }}
          </button>
        </div>

        <div v-if="!rows.length" class="empty"><div class="big">📊</div>暂无学生消费记录</div>

        <div v-else class="card table-card">
          <table class="rank-table">
            <thead>
              <tr>
                <th class="c-check">
                  <input type="checkbox" :checked="allChecked" @change="toggleAll" />
                </th>
                <th class="c-rank">排名</th>
                <th>学生</th>
                <th>学校</th>
                <th class="c-num">消费次数</th>
                <th class="c-num">消费金额</th>
                <th class="c-time">最近消费</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(r, i) in rows" :key="r.user_id" :class="{ picked: checked.includes(r.user_id) }">
                <td class="c-check"><input type="checkbox" :value="r.user_id" v-model="checked" /></td>
                <td class="c-rank"><span class="badge" :class="rankClass(i)">{{ i + 1 }}</span></td>
                <td>
                  <div class="name">{{ r.name }}</div>
                  <div class="muted">{{ r.student_id || '—' }}</div>
                </td>
                <td class="muted">{{ r.school || '—' }}</td>
                <td class="c-num strong">{{ r.order_count }}</td>
                <td class="c-num strong price">¥{{ money(r.total_amount) }}</td>
                <td class="c-time muted">{{ r.last_order_at || '—' }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </template>

      <!-- 发放记录 -->
      <template v-else>
        <div v-if="!grants.length" class="empty"><div class="big">🎁</div>暂无发放记录</div>
        <div v-else class="card table-card">
          <table class="rank-table">
            <thead>
              <tr>
                <th>时间</th>
                <th>类型</th>
                <th>对象</th>
                <th>称号</th>
                <th class="c-num">金额</th>
                <th>操作人</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="g in grants" :key="g.id">
                <td class="muted">{{ g.created_at }}</td>
                <td><span class="tag" :class="g.grant_type === 1 ? 't-out' : 't-in'">{{ g.grant_type === 1 ? '发放' : '注入' }}</span></td>
                <td>{{ g.user_name || '—' }}<span class="muted" v-if="g.student_id"> · {{ g.student_id }}</span></td>
                <td>{{ g.title || g.remark || '—' }}</td>
                <td class="c-num strong" :class="g.grant_type === 1 ? 'price' : 'in'">{{ g.grant_type === 1 ? '-' : '+' }}¥{{ money(g.amount) }}</td>
                <td class="muted">{{ g.operator_name || '—' }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </template>
    </template>

    <!-- 发放弹窗 -->
    <div v-if="showGrant" class="modal-mask" @click.self="showGrant = false">
      <div class="modal">
        <h3>发放优惠金额</h3>
        <p class="m-line">已选 <b>{{ checked.length }}</b> 名学生，可分配余额 <b>¥{{ money(pool.available) }}</b></p>
        <label class="f-label">每人发放金额（元）</label>
        <input v-model="grantForm.amount" class="f-input" type="number" min="0.01" step="0.01" placeholder="如 5.00" />
        <label class="f-label">称号（学生端通知展示）</label>
        <input v-model="grantForm.title" class="f-input" placeholder="如：本月暖心帮扶对象" />
        <label class="f-label">备注（可选）</label>
        <input v-model="grantForm.remark" class="f-input" placeholder="如：平台盈利回馈" />
        <div class="preview">
          <div class="preview-label">学生收到的通知</div>
          <div class="preview-body">
            亲爱的{{ previewName }}，感谢您的忠诚使用，为您发放优惠额度！
            <div class="preview-amt">¥{{ grantForm.amount || '0.00' }}</div>
          </div>
        </div>
        <p class="m-tip">合计需发放 ¥{{ totalNeed }}，发放后自动划拨到学生账户余额。</p>
        <div class="m-actions">
          <button class="btn btn-outline" @click="showGrant = false">取消</button>
          <button class="btn btn-primary" :disabled="submitting || !canGrant" @click="submitGrant">
            {{ submitting ? '发放中…' : '确认发放' }}
          </button>
        </div>
      </div>
    </div>

    <!-- 注入弹窗 -->
    <div v-if="showInject" class="modal-mask" @click.self="showInject = false">
      <div class="modal">
        <h3>注入补贴资金</h3>
        <label class="f-label">注入金额（元）</label>
        <input v-model="injectForm.amount" class="f-input" type="number" min="0.01" step="0.01" placeholder="如 100.00" />
        <label class="f-label">备注（可选）</label>
        <input v-model="injectForm.remark" class="f-input" placeholder="如：演示资金" />
        <div class="m-actions">
          <button class="btn btn-outline" @click="showInject = false">取消</button>
          <button class="btn btn-primary" :disabled="submitting" @click="submitInject">确认注入</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import {
  getStudentConsumption,
  getSubsidyPool,
  injectSubsidyPool,
  grantSubsidy,
  getSubsidyGrants
} from '../../api/admin'
import { toast } from '../../utils/toast'

const sortTabs = [
  { label: '按消费次数降序', value: 'count' },
  { label: '按消费金额降序', value: 'amount' }
]

const rows = ref([])
const grants = ref([])
const checked = ref([])
const sortBy = ref('count')
const tab = ref('rank')
const loading = ref(false)
const loaded = ref(false)
const submitting = ref(false)
const showGrant = ref(false)
const showInject = ref(false)
const pool = ref({ platform_profit: 0, injected: 0, granted: 0, available: 0 })
const grantForm = ref({ amount: '5.00', title: '本月暖心帮扶对象', remark: '平台盈利回馈' })
const injectForm = ref({ amount: '100.00', remark: '演示资金' })

const allChecked = computed(() => rows.value.length > 0 && checked.value.length === rows.value.length)
const previewName = computed(() => {
  const first = rows.value.find(r => checked.value.includes(r.user_id))
  return first ? first.name : '同学'
})
const totalNeed = computed(() => (Number(grantForm.value.amount || 0) * checked.value.length).toFixed(2))
const canGrant = computed(
  () => checked.value.length > 0 && Number(grantForm.value.amount) > 0 && Number(totalNeed.value) <= Number(pool.value.available)
)

function money(v) {
  return Number(v || 0).toFixed(2)
}
function rankClass(i) {
  return ['r1', 'r2', 'r3'][i] || ''
}

function sortRows() {
  const list = [...rows.value]
  if (sortBy.value === 'amount') {
    list.sort((a, b) => Number(b.total_amount || 0) - Number(a.total_amount || 0) ||
      Number(b.order_count || 0) - Number(a.order_count || 0))
  } else {
    list.sort((a, b) => Number(b.order_count || 0) - Number(a.order_count || 0) ||
      Number(b.total_amount || 0) - Number(a.total_amount || 0))
  }
  rows.value = list
}

function selectTop(n) {
  checked.value = rows.value.slice(0, n).map((r) => r.user_id)
  openGrant()
}
function toggleAll(e) {
  checked.value = e.target.checked ? rows.value.map((r) => r.user_id) : []
}
function openGrant() {
  if (!checked.value.length) {
    toast('请先勾选要帮扶的学生', 'error')
    return
  }
  showGrant.value = true
}

async function loadPool() {
  try { pool.value = await getSubsidyPool() } catch (e) { /* 拦截器 */ }
}
async function loadRows() {
  try {
    rows.value = await getStudentConsumption({ limit: 200 })
    sortRows()
  } catch (e) { /* 拦截器 */ }
}
async function loadGrants() {
  try { grants.value = await getSubsidyGrants({ limit: 100 }) } catch (e) { /* 拦截器 */ }
}

async function load() {
  loading.value = true
  try { await Promise.all([loadPool(), loadRows()]) } finally {
    loading.value = false
    loaded.value = true
  }
}

async function submitGrant() {
  if (!canGrant.value) {
    toast('金额不合法或可分配余额不足', 'error')
    return
  }
  submitting.value = true
  try {
    await grantSubsidy({
      user_ids: checked.value,
      amount: grantForm.value.amount,
      title: grantForm.value.title,
      remark: grantForm.value.remark
    })
    toast(`已向 ${checked.value.length} 名学生发放奖励金`)
    showGrant.value = false
    checked.value = []
    await Promise.all([loadPool(), loadGrants()])
  } catch (e) { /* 拦截器已提示 */ } finally { submitting.value = false }
}

async function submitInject() {
  if (!(Number(injectForm.value.amount) > 0)) {
    toast('请输入大于 0 的金额', 'error')
    return
  }
  submitting.value = true
  try {
    pool.value = await injectSubsidyPool(injectForm.value.amount, injectForm.value.remark)
    toast('资金已注入')
    showInject.value = false
  } catch (e) { /* 拦截器已提示 */ } finally { submitting.value = false }
}

watch(sortBy, sortRows)
onMounted(load)
</script>

<style scoped>
.page-title { margin: 4px 0 0; }
.sub { color: var(--muted); font-size: 13px; margin: 2px 0 14px; }
.summary { display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; margin-bottom: 12px; }
.metric { background: #fff; border: 1px solid var(--border); border-radius: 12px; padding: 14px; text-align: center; }
.metric.highlight { border-color: #f0c78d; background: #fffaf0; }
.mv { font-size: 22px; font-weight: 800; color: var(--primary); }
.ml { color: var(--muted); font-size: 12px; margin-top: 2px; }
.actions { display: flex; align-items: center; gap: 10px; margin-bottom: 14px; }
.hint { color: var(--muted); font-size: 12px; }
.toolbar { display: flex; align-items: center; gap: 8px; margin: 12px 0; flex-wrap: wrap; }
.sorts { display: flex; gap: 6px; }
.grow { flex: 1; }
.table-card { padding: 0; overflow: hidden; }
.rank-table { width: 100%; border-collapse: collapse; font-size: 14px; }
.rank-table th, .rank-table td { padding: 12px 10px; text-align: left; border-bottom: 1px solid var(--border); }
.rank-table th { background: #faf7f2; color: var(--muted); font-size: 12px; font-weight: 700; }
.rank-table tbody tr:last-child td { border-bottom: 0; }
.rank-table tbody tr.picked { background: #fff8ec; }
.c-check { width: 40px; }
.c-rank { width: 60px; }
.c-num { width: 96px; text-align: right; }
.c-time { width: 150px; }
.name { font-weight: 600; }
.muted { color: var(--muted); font-size: 12px; }
.strong { font-weight: 700; }
.price { color: var(--primary); }
.in { color: var(--success); }
.badge { display: inline-block; min-width: 24px; height: 24px; line-height: 24px; text-align: center; border-radius: 999px; background: #f1ede6; color: #6b6259; font-size: 12px; font-weight: 800; }
.badge.r1 { background: #f59e0b; color: #fff; }
.badge.r2 { background: #94a3b8; color: #fff; }
.badge.r3 { background: #c98a5b; color: #fff; }
.tag { font-size: 12px; padding: 2px 8px; border-radius: 8px; }
.tag.t-out { background: #fdece4; color: #d9623d; }
.tag.t-in { background: #e6f4ea; color: #2f7d55; }
.modal-mask { position: fixed; inset: 0; z-index: 100; display: grid; place-items: center; background: rgba(30, 22, 14, .35); padding: 18px; }
.modal { width: min(420px, 100%); background: #fffdf8; border-radius: 18px; padding: 20px; box-shadow: 0 20px 50px rgba(70, 50, 30, .25); }
.modal h3 { margin: 0 0 10px; font-size: 18px; }
.m-line { margin: 0 0 12px; color: #5c5145; font-size: 13px; }
.f-label { display: block; margin: 10px 0 4px; color: #6b6259; font-size: 12px; font-weight: 700; }
.f-input { width: 100%; min-height: 42px; padding: 10px 12px; border: 1px solid #e5d9c8; border-radius: 12px; font-size: 14px; box-sizing: border-box; }
.m-tip { margin: 12px 0 0; color: var(--muted); font-size: 12px; }
.preview {
  margin-top: 12px;
  padding: 10px 12px;
  border-radius: 12px;
  background: linear-gradient(135deg, #fff8ec, #fff1dc);
  border: 1px solid #f6e3c2;
}
.preview-label { font-size: 11px; color: #a2978a; margin-bottom: 6px; }
.preview-body { font-size: 13px; line-height: 1.6; color: #5c5145; }
.preview-amt {
  margin-top: 6px;
  padding: 8px;
  border-radius: 10px;
  background: linear-gradient(135deg, #fff1d6, #ffe3bd);
  color: #d9623d;
  font-size: 15px;
  font-weight: 800;
  text-align: center;
}
.m-actions { display: flex; gap: 10px; margin-top: 16px; }
.m-actions .btn { flex: 1; }
@media (max-width: 720px) {
  .summary { grid-template-columns: repeat(2, 1fr); }
  .c-time { display: none; }
}
</style>
