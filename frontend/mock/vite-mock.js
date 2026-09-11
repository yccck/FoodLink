// 开发期 Mock 服务：模拟 Spring Boot 后端的 /api 接口，方便前端先行联调。
// 后端就绪后：置 .env.development 的 VITE_USE_MOCK=false 即可关闭。

function readBody(req) {
  return new Promise((resolve) => {
    let data = ''
    req.on('data', (c) => { data += c })
    req.on('end', () => {
      try { resolve(data ? JSON.parse(data) : {}) } catch { resolve({}) }
    })
    req.on('error', () => resolve({}))
  })
}

function pad(n) { return String(n).padStart(2, '0') }
function fmt(d) {
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}:${pad(d.getSeconds())}`
}
function hoursFromNow(h) { return fmt(new Date(Date.now() + h * 3600 * 1000)) }

const DEFAULT_BUSINESS_OPEN_TIME = '08:00'
const DEFAULT_BUSINESS_CLOSE_TIME = '22:00'
const BUSINESS_TIME_PATTERN = /^(?:[01]\d|2[0-3]):[0-5]\d$/
const PLATFORM_FEE_RATE = 0.001
const PLATFORM_FEE_RATE_TEXT = '0.1%'
const REFUND_WINDOW_SECONDS = 5 * 60

function parseApiTime(value) {
  const timestamp = new Date(String(value || '').replace(' ', 'T')).getTime()
  return Number.isFinite(timestamp) ? timestamp : NaN
}
function isProductExpired(product) {
  const timestamp = parseApiTime(product && product.expire_time)
  return Number.isFinite(timestamp) && timestamp <= Date.now()
}
function isProductAvailable(product) {
  return product.status === 1 && !Number(product.risk_flag) && !isProductExpired(product)
}
function toMoney(value) { return (Math.round((Number(value) + Number.EPSILON) * 100) / 100).toFixed(2) }
function nextClosingTime(reference, closeTime) {
  const value = BUSINESS_TIME_PATTERN.test(closeTime || '') ? closeTime : DEFAULT_BUSINESS_CLOSE_TIME
  const [hours, minutes] = value.split(':').map(Number)
  const closing = new Date(reference)
  closing.setHours(hours, minutes, 0, 0)
  if (closing.getTime() <= reference.getTime()) closing.setDate(closing.getDate() + 1)
  return closing
}
function pickupDeadline(o) {
  const explicit = parseApiTime(o.pickup_deadline)
  if (Number.isFinite(explicit)) return new Date(explicit)
  const createdAt = parseApiTime(o.created_at)
  if (!Number.isFinite(createdAt)) return new Date()
  const product = productOf(o.product_id)
  const closing = nextClosingTime(new Date(createdAt), product?.business_close_time)
  const expiry = parseApiTime(product?.expire_time)
  return Number.isFinite(expiry) && expiry < closing.getTime() ? new Date(expiry) : closing
}
function deadlineReason(o) {
  if (o.deadline_reason) return o.deadline_reason
  const createdAt = parseApiTime(o.created_at)
  const product = productOf(o.product_id)
  const expiry = parseApiTime(product?.expire_time)
  if (!Number.isFinite(createdAt) || !Number.isFinite(expiry)) return 'business_close'
  const closing = nextClosingTime(new Date(createdAt), product?.business_close_time)
  return expiry < closing.getTime() ? 'product_expired' : 'business_close'
}
function settleOrder(o, completionType, completedAt = new Date()) {
  if (o.status !== 0) return false
  o.status = 1
  o.picked_at = fmt(completedAt)
  o.completion_type = completionType
  o.payment_status = 'settled'
  o.close_reason = null
  o.closed_at = null
  return true
}
function closeOrder(o, reason, paymentStatus, closedAt = new Date()) {
  if (o.status !== 0) return false
  o.status = 2
  o.picked_at = null
  o.completion_type = null
  o.payment_status = paymentStatus
  o.close_reason = reason
  o.closed_at = fmt(closedAt)
  return true
}
function autoCompleteOrders() {
  const now = Date.now()
  orders.forEach((o) => {
    const deadline = pickupDeadline(o)
    if (o.status !== 0 || deadline.getTime() > now) return
    if (deadlineReason(o) === 'product_expired') closeOrder(o, 'product_expired', 'settled', deadline)
    else settleOrder(o, 'auto_timeout', deadline)
  })
}

// ---------- 内存数据 ----------
let seq = { user: 5, product: 0, order: 6, risk: 3, refund: 1 }

const users = [
  { id: 1, role: 1, login_name: '2021001', password: '123456', name: '张三',
    school: '澳门科技大学', student_id: '2021001', phone: '13800000000', avatar: '',
    preferences: { cuisine: ['川菜', '家常菜'], taste: ['麻辣', '清淡'], meal_time: ['午餐', '晚餐'] },
    taboo: { allergens: ['花生'], dislikes: ['香菜'] }, monthly_budget: 1500, status: 1 },
  { id: 2, role: 2, login_name: 'shop001', password: '123456', name: '店铺账号', phone: '13811112222',
    school: '', student_id: '', status: 1 },
  { id: 3, role: 3, login_name: 'admin', password: '123456', name: '超级管理员', phone: '00000000000', status: 1 },
  { id: 4, role: 1, login_name: '2022002', password: '123456', name: '李四',
    school: '澳门科技大学', student_id: '2022002', phone: '13900000000', avatar: '',
    preferences: { cuisine: ['粤菜'], taste: ['清淡'], meal_time: ['午餐'] },
    taboo: { allergens: [], dislikes: [] }, monthly_budget: 800, status: 1 },
  { id: 5, role: 2, login_name: 'shop002', password: '123456', name: '店铺账号', phone: '13822223333',
    school: '', student_id: '', status: 1 }
]
const merchants = [
  { id: 1, user_id: 2, shop_name: '科大风味小厨', license_img: '', location: '澳门科技大学学生餐厅取货点',
    lat: 22.1496, lng: 113.565, audit_status: 1, created_at: hoursFromNow(-48) },
  { id: 2, user_id: 5, shop_name: '王记轻食', license_img: '', location: '澳门科技大学N座旁取货点',
    lat: 22.1512, lng: 113.5665, audit_status: 0, created_at: hoursFromNow(-5) }
]

const products = []
const orders = []
const refundApplications = []
const favorites = new Map()
const behaviors = []
const behaviorLog = []
const riskLogs = [
  { id: 1, product_id: 4, merchant_id: 2, risk_type: 1, risk_detail: '折扣价高于原价，已人工修正', is_resolved: 1, created_at: hoursFromNow(-48) },
  { id: 2, product_id: 11, merchant_id: 2, risk_type: 2, risk_detail: '命中违禁词：特效', is_resolved: 0, created_at: hoursFromNow(-24) },
  { id: 3, product_id: 8, merchant_id: 2, risk_type: 3, risk_detail: '可售时长不足1小时', is_resolved: 0, created_at: hoursFromNow(-5) }
]

// demo_type 仅用于演示子模块标注（guess 猜你喜欢 / prefer 为你优选），真实后端由 AI 计算。
function addProduct(p) {
  seq.product += 1
  const prod = {
    id: seq.product, merchant_id: p.merchant_id || 2, title: p.title || '',
    description: p.description || '', category: p.category || '简餐',
    image: p.image || '', original_price: p.original_price || 0,
    discount_price: p.discount_price || 0, quantity: p.quantity ?? 10,
    expire_time: p.expire_time || hoursFromNow(18),
    business_open_time: p.business_open_time || DEFAULT_BUSINESS_OPEN_TIME,
    business_close_time: p.business_close_time || DEFAULT_BUSINESS_CLOSE_TIME,
    location: p.location || '澳门科技大学学生餐厅取货点', lat: p.lat || 22.1496, lng: p.lng || 113.565,
    status: p.status ?? 1, view_count: p.view_count || 0, fav_count: p.fav_count || 0,
    order_count: p.order_count || 0, risk_flag: p.risk_flag || 0,
    distance: p.distance ?? 0.5, demo_type: p.demo_type || '',
    gradient: p.gradient || '#ff9a56', emoji: p.emoji || '🍱',
    created_at: hoursFromNow(-(seq.product * 6))
  }
  products.push(prod)
  return prod
}
addProduct({ title: '水煮鱼片 超值套餐', description: '鲜嫩鱼片，麻辣入味，配米饭一份。', category: '简餐', image: '/images/products/water-boiled-fish.jpg', original_price: 28, discount_price: 8.8, quantity: 9, expire_time: hoursFromNow(18), view_count: 96, fav_count: 12, order_count: 8, distance: 0.3, demo_type: 'guess', gradient: '#f06292', emoji: '🐟' })
addProduct({ title: '麻辣香锅 单人份', description: '自选配菜现炒，价格实惠。', category: '简餐', image: '/images/products/spicy-hot-pot.jpg', original_price: 22, discount_price: 9.9, quantity: 4, expire_time: hoursFromNow(22), view_count: 60, fav_count: 6, order_count: 4, distance: 0.8, demo_type: 'prefer', gradient: '#e53935', emoji: '🌶' })
addProduct({ title: '现烤蛋挞 甜香四溢', description: '每日新鲜烘焙，外酥里嫩。', category: '烘焙', image: '/images/products/egg-tarts.jpg', original_price: 18, discount_price: 5.9, quantity: 20, expire_time: hoursFromNow(2), view_count: 42, fav_count: 9, order_count: 11, distance: 1.2, demo_type: '', gradient: '#ffb74d', emoji: '🥧' })
addProduct({ title: '宫保鸡丁 盖浇饭', description: '微辣下饭，分量充足。', category: '家常菜', image: '/images/products/kung-pao-chicken.jpg', original_price: 26, discount_price: 8.9, quantity: 7, expire_time: hoursFromNow(6), view_count: 33, fav_count: 3, order_count: 2, distance: 0.5, demo_type: 'prefer', gradient: '#8d6e63', emoji: '🍛' })
addProduct({ title: '重庆小面', description: '麻辣鲜香，地道川味。', category: '川菜', image: '/images/products/chongqing-noodles.jpg', original_price: 16, discount_price: 6.9, quantity: 15, expire_time: hoursFromNow(26), view_count: 120, fav_count: 22, order_count: 18, distance: 1.0, demo_type: 'guess', gradient: '#fb8c00', emoji: '🍜' })
addProduct({ title: '酸菜鱼 大份', description: '酸辣开胃，两人份。', category: '川菜', image: '/images/products/pickled-fish.jpg', original_price: 32, discount_price: 9.9, quantity: 6, expire_time: hoursFromNow(30), view_count: 88, fav_count: 15, order_count: 9, distance: 1.5, demo_type: 'prefer', gradient: '#43a047', emoji: '🐠' })
addProduct({ title: '鲜芋奶茶', description: '现煮芋圆，奶香浓郁。', category: '饮品', image: '/images/orders/milk-tea.jpg', original_price: 15, discount_price: 5.9, quantity: 30, expire_time: hoursFromNow(8), view_count: 55, fav_count: 8, order_count: 20, distance: 0.9, demo_type: '', gradient: '#d4a5a5', emoji: '🧋' })
addProduct({ title: '水果拼盘', description: '时令水果，每日现切。', category: '水果', image: '/images/orders/fruit-box.jpg', original_price: 20, discount_price: 7.9, quantity: 11, expire_time: hoursFromNow(0.5), view_count: 20, fav_count: 2, order_count: 1, distance: 1.1, demo_type: '', gradient: '#66bb6a', emoji: '🍉' })
addProduct({ title: '番茄牛腩饭', description: '酸甜浓郁，牛肉软烂。', category: '家常菜', image: '/images/products/tomato-beef-rice.jpg', original_price: 27, discount_price: 8.9, quantity: 7, expire_time: hoursFromNow(14), view_count: 44, fav_count: 5, order_count: 3, distance: 2.0, demo_type: 'prefer', gradient: '#ef5350', emoji: '🥘' })
addProduct({ title: '红糖糍粑', description: '现做甜点，软糯拉丝。', category: '其他', image: '/images/products/brown-sugar-ciba.jpg', original_price: 12, discount_price: 4.9, quantity: 18, expire_time: hoursFromNow(9), view_count: 26, fav_count: 4, order_count: 6, distance: 1.3, demo_type: '', gradient: '#a1887f', emoji: '🍡' })
addProduct({ title: '特效降温套餐', description: '自称药膳，含违禁夸大宣传词，演示用被拦截商品。', category: '其他', original_price: 20, discount_price: 9, quantity: 3, expire_time: hoursFromNow(4), status: 3, risk_flag: 1, distance: 1.0, demo_type: '', gradient: '#9e9e9e', emoji: '🚫' })
addProduct({ title: '昨日烘焙盲盒', description: '商品领取期限已结束，订单已自动关闭并结算。', category: '食品盲盒', image: '/images/products/egg-tarts.jpg', original_price: 16, discount_price: 4.9, quantity: 0, expire_time: hoursFromNow(-1), status: 0, distance: 0.4, gradient: '#c8a46b', emoji: '🥐' })

behaviors.push({ user_id: 1, product_id: 1, behavior_type: 3, created_at: hoursFromNow(-30) })
behaviors.push({ user_id: 1, product_id: 5, behavior_type: 2, created_at: hoursFromNow(-20) })
behaviors.push({ user_id: 1, product_id: 3, behavior_type: 1, created_at: hoursFromNow(-6) })

orders.push({ id: 1, user_id: 1, product_id: 1, quantity: 1, status: 0, pickup_code: '483920', created_at: hoursFromNow(-2), picked_at: null })
orders.push({ id: 2, user_id: 1, product_id: 7, quantity: 1, status: 1, pickup_code: '774201', created_at: hoursFromNow(-20), picked_at: hoursFromNow(-19), completion_type: 'merchant_confirmed' })
orders.push({ id: 3, user_id: 4, product_id: 2, quantity: 1, status: 0, pickup_code: '512388', created_at: hoursFromNow(-3), picked_at: null })
orders.push({ id: 4, user_id: 4, product_id: 8, quantity: 1, status: 0, pickup_code: '900123', created_at: hoursFromNow(-4), picked_at: null })
// 已到领取截止时间的待领取订单会在首次查询时自动完成，用于比赛现场展示自动结算。
orders.push({ id: 5, user_id: 1, product_id: 4, quantity: 1, status: 0, pickup_code: '665544', created_at: hoursFromNow(-7), pickup_deadline: hoursFromNow(-1), deadline_reason: 'business_close', picked_at: null })
orders.push({ id: 6, user_id: 1, product_id: 12, quantity: 1, status: 2, pickup_code: '308615', created_at: hoursFromNow(-6), pickup_deadline: hoursFromNow(-1), deadline_reason: 'product_expired', close_reason: 'product_expired', closed_at: hoursFromNow(-1), picked_at: null, payment_status: 'settled' })
refundApplications.push({ id: 1, order_id: 2, user_id: 1, reason: '饮品有明显异味，已停止饮用并保留了现场照片。', evidence_image: '', status: 0, admin_remark: '', created_at: hoursFromNow(-18), reviewed_at: null })

function merchantOf(userId) { return merchants.find(m => m.user_id === userId) }
function merchantById(id) { return merchants.find(m => m.id === Number(id)) }
function productOf(id) { return products.find(p => p.id === Number(id)) }
function orderMoney(o) {
  const p = productOf(o.product_id)
  const unitPrice = Number(o.price ?? (p ? p.discount_price : 0))
  const total = Number(toMoney(unitPrice * Number(o.quantity || 1)))
  const fee = Number(toMoney(total * PLATFORM_FEE_RATE))
  return { total, fee, merchantReceivable: Number(toMoney(total - fee)) }
}
function isThisMonth(value) {
  const timestamp = parseApiTime(value)
  if (!Number.isFinite(timestamp)) return false
  const date = new Date(timestamp)
  const now = new Date()
  return date.getFullYear() === now.getFullYear() && date.getMonth() === now.getMonth()
}
function orderSummary(user) {
  autoCompleteOrders()
  const mine = user.role === 2
    ? orders.filter(o => productOf(o.product_id)?.merchant_id === user.id)
    : orders.filter(o => o.user_id === user.id)
  const monthly = mine.filter(o => o.payment_status !== 'refunded' && isThisMonth(o.created_at))
  const completed = monthly.filter(o => o.status === 1 || o.close_reason === 'product_expired')
  const sum = (list, field) => list.reduce((total, order) => total + orderMoney(order)[field], 0)
  const monthlyTotal = sum(monthly, 'total')
  return {
    role: user.role,
    monthly_sales: toMoney(user.role === 2 ? monthlyTotal : 0),
    monthly_spending: toMoney(user.role === 1 ? monthlyTotal : 0),
    monthly_income: toMoney(user.role === 2 ? sum(completed, 'merchantReceivable') : 0),
    monthly_platform_fee: toMoney(user.role === 2 ? sum(completed, 'fee') : 0),
    monthly_order_count: monthly.length,
    monthly_item_count: monthly.reduce((total, order) => total + Number(order.quantity || 0), 0),
    monthly_completed_count: completed.length
  }
}
function findUser(login, pwd, role) {
  return users.find(u =>
    u.login_name === login && u.password === pwd &&
    (role === undefined || u.role === Number(role)))
}

function responder(res) {
  return (payload, status = 200) => {
    res.statusCode = status
    res.setHeader('Content-Type', 'application/json; charset=utf-8')
    res.end(JSON.stringify(payload))
  }
}
function ok(send, data) { send({ code: 0, message: 'success', data }) }
function fail(send, code, message) { send({ code, message, data: null }) }

function withAuth(req, send, handler) {
  const token = (req.headers['authorization'] || '').replace(/^Bearer\s+/i, '')
  if (!token || !token.startsWith('mock-token-')) { send({ code: 401, message: '未登录或登录已过期', data: null }, 401); return }
  const user = users.find(u => u.login_name === token.replace('mock-token-', ''))
  if (!user) { send({ code: 401, message: '未登录或登录已过期', data: null }, 401); return }
  handler(user)
}
function withRole(req, send, roles, handler) {
  withAuth(req, send, (user) => {
    if (!roles.includes(user.role)) { fail(send, 403, '无权限操作'); return }
    handler(user)
  })
}

function userView(u, withToken) {
  const m = merchantOf(u.id)
  const view = {
    id: u.id, role: u.role, login_name: u.login_name, name: u.name,
    avatar: u.avatar || '', school: u.school || '', student_id: u.student_id || '',
    phone: u.phone || '', preferences: u.preferences || null, taboo: u.taboo || null,
    monthly_budget: u.monthly_budget ?? null, status: u.status,
    shop_name: m ? m.shop_name : '', license_img: m ? m.license_img : '',
    location: m ? m.location : '', lat: m ? m.lat : null, lng: m ? m.lng : null,
    audit_status: m ? m.audit_status : -1
  }
  if (withToken) return { token: 'mock-token-' + u.login_name, user: view }
  return view
}

function productCard(p, user) {
  const fav = favorites.get(user ? user.id : -1)
  return {
    id: p.id, merchant_id: p.merchant_id, title: p.title, description: p.description,
    category: p.category, image: p.image, original_price: p.original_price,
    discount_price: p.discount_price, quantity: p.quantity, expire_time: p.expire_time,
    business_open_time: p.business_open_time,
    business_close_time: p.business_close_time,
    location: p.location, lat: p.lat, lng: p.lng, status: p.status,
    view_count: p.view_count, fav_count: p.fav_count, order_count: p.order_count,
    risk_flag: p.risk_flag, distance: p.distance, recommend_type: p.demo_type || '',
    gradient: p.gradient || '', emoji: p.emoji || '🍱',
    is_favorite: !!(fav && fav.has(p.id))
  }
}

function studentView(o) {
  const u = users.find(x => x.id === o.user_id)
  return { student_name: u ? u.name : '-', student_id: u ? u.student_id : '-', phone: u ? u.phone : '-' }
}
function orderView(o, withStudent) {
  const p = productOf(o.product_id)
  const m = p ? merchantOf(p.merchant_id) : null
  const unitPrice = Number(o.price ?? (p ? p.discount_price : 0))
  const originalPrice = Number(o.original_price ?? (p ? p.original_price : 0))
  const total = unitPrice * Number(o.quantity || 1)
  const fee = Math.round((total * PLATFORM_FEE_RATE + Number.EPSILON) * 100) / 100
  const deadline = pickupDeadline(o)
  const refundDeadline = new Date(Math.min(
    parseApiTime(o.created_at) + REFUND_WINDOW_SECONDS * 1000,
    deadline.getTime()
  ))
  const refunded = o.payment_status === 'refunded' || ['student_refund', 'admin_refund'].includes(o.close_reason)
  const settled = o.status === 1 || (o.status === 2 && !refunded)
  const settledAt = settled ? (o.picked_at ?? o.closed_at ?? null) : null
  const payoutAt = settledAt ? new Date(parseApiTime(settledAt) + 24 * 60 * 60 * 1000) : null
  const payoutCompleted = payoutAt && payoutAt.getTime() <= Date.now()
  return {
    id: o.id, product_id: o.product_id,
    product_title: p ? p.title : '商品', product_image: p ? p.image : '',
    shop_name: m ? m.shop_name : '科大风味小厨',
    original_price: toMoney(originalPrice), price: toMoney(unitPrice),
    total_amount: toMoney(total),
    quantity: o.quantity, status: o.status, pickup_code: o.pickup_code,
    expire_time: p ? p.expire_time : '',
    business_open_time: p?.business_open_time || DEFAULT_BUSINESS_OPEN_TIME,
    business_close_time: p?.business_close_time || DEFAULT_BUSINESS_CLOSE_TIME,
    pickup_deadline: fmt(deadline),
    remaining_seconds: o.status === 0 ? Math.max(0, Math.ceil((deadline.getTime() - Date.now()) / 1000)) : 0,
    refund_deadline: fmt(refundDeadline),
    refundable: o.status === 0 && Date.now() <= refundDeadline.getTime(),
    location: p ? p.location : '',
    created_at: o.created_at, picked_at: o.picked_at ?? null,
    payment_status: settled ? 'settled' : refunded ? 'refunded' : 'paid',
    platform_fee_rate: PLATFORM_FEE_RATE_TEXT,
    platform_fee: refunded ? '0.00' : toMoney(fee),
    merchant_receivable: refunded ? '0.00' : toMoney(total - fee),
    settled_at: settledAt,
    merchant_payout_status: refunded ? 'refunded' : settled ? (payoutCompleted ? 'paid' : 'scheduled') : 'pending',
    merchant_payout_at: payoutAt ? fmt(payoutAt) : null,
    completion_type: o.status === 1 ? (o.completion_type || 'merchant_confirmed') : null,
    close_reason: o.close_reason || null,
    closed_at: o.closed_at || null,
    ...(withStudent ? studentView(o) : {})
  }
}

function refundApplicationView(application) {
  const order = orders.find(o => o.id === application.order_id)
  const product = order && productOf(order.product_id)
  const merchant = product && merchantOf(product.merchant_id)
  const student = users.find(user => user.id === application.user_id)
  return {
    id: application.id,
    order_id: application.order_id,
    product_title: product?.title || '商品',
    product_image: product?.image || '',
    shop_name: merchant?.shop_name || '商家',
    student_name: student?.name || '学生',
    student_id: student?.student_id || '',
    total_amount: toMoney(order ? orderMoney(order).total : 0),
    reason: application.reason,
    evidence_image: application.evidence_image || '',
    status: application.status,
    admin_remark: application.admin_remark || '',
    created_at: application.created_at,
    reviewed_at: application.reviewed_at || null
  }
}

function paginate(list, q) {
  const page = Math.max(1, parseInt(q.get('page'), 10) || 1)
  const pageSize = Math.min(20, parseInt(q.get('pageSize'), 10) || 6)
  const start = (page - 1) * pageSize
  return { list: list.slice(start, start + pageSize), total: list.length, page, page_size: pageSize, has_more: start + pageSize < list.length }
}

// ---- 发布风控（演示轻量规则） ----
const BANNED = ['药', '特效', '根治', '丰胸', '代购', '违禁']
function riskCheck(body) {
  const text = (body.title || '') + (body.description || '')
  if (body.discount_price >= body.original_price) return { type: 1, code: 41001, msg: '价格异常：折扣价不得高于或等于原价' }
  if (BANNED.some(w => text.includes(w))) return { type: 2, code: 41002, msg: '发布内容命中违禁词，已被 AI 风控拦截' }
  const ms = new Date(body.expire_time).getTime()
  if (!isFinite(ms)) return { type: 3, code: 41003, msg: '有效期格式错误' }
  if (ms - Date.now() < 30 * 60 * 1000) return { type: 3, code: 41003, msg: '距过期不足30分钟，暂不可发布' }
  return null
}
const RISK_TYPE_NAME = { 1: '价格异常', 2: '敏感词', 3: '有效期异常' }

export function mockPlugin() {
  return {
    name: 'shiyuan-mock',
    configureServer(server) {
      server.middlewares.use(async (req, res, next) => {
        if (!req.url || !req.url.startsWith('/api')) return next()
        const send = responder(res)
        const url = new URL(req.url, 'http://localhost')
        const path = url.pathname
        const q = url.searchParams
        const method = (req.method || 'GET').toUpperCase()

        // ---- 认证 ----
        if (path === '/api/auth/login' && method === 'POST') {
          const body = await readBody(req)
          const u = findUser(body.login_name, body.password, body.role)
          if (!u) return fail(send, 20001, '账号或密码错误')
          if (u.status !== 1) return fail(send, 20002, '账号已被禁用')
          const m = merchantOf(u.id)
          if (u.role === 2 && (!m || m.audit_status !== 1)) return fail(send, 20003, '商家账号待审核或未通过，暂无法登录')
          return ok(send, userView(u, true))
        }
        if (path === '/api/auth/register' && method === 'POST') {
          const body = await readBody(req)
          if (users.some(u => u.login_name === (body.login_name || body.student_id))) return fail(send, 20005, '该账号已注册')
          if (users.some(u => u.phone === body.phone)) return fail(send, 20006, '该手机号已注册')
          seq.user += 1
          const role = Number(body.role || 1)
          if (role === 1) {
            const u = { id: seq.user, role: 1, login_name: body.student_id, password: body.password,
              name: body.name, school: body.school, student_id: body.student_id, phone: body.phone,
              avatar: '', preferences: null, taboo: null, monthly_budget: null, status: 1 }
            users.push(u); return ok(send, { id: u.id })
          }
          const u = { id: seq.user, role: 2, login_name: body.login_name, password: body.password,
            name: body.shop_name, phone: body.phone, status: 1 }
          users.push(u)
          merchants.push({ id: merchants.length + 1, user_id: u.id, shop_name: body.shop_name, license_img: body.license_img || '',
            location: body.location, lat: body.lat, lng: body.lng, audit_status: 0, created_at: hoursFromNow(0) })
          return ok(send, { id: u.id, audit_status: 0 })
        }
        if (path === '/api/auth/reset-password' && method === 'POST') {
          const body = await readBody(req)
          const role = Number(body.role || 1)
          let target
          if (role === 1) target = users.find(u => u.student_id === body.student_id && u.name === body.name && u.phone === body.phone)
          else target = users.find(u => u.login_name === body.login_name && (merchantOf(u.id)?.shop_name) === body.shop_name && u.phone === body.phone)
          if (!target) return fail(send, 20004, '验证信息不匹配')
          target.password = '123456'
          return ok(send, { message: '密码已重置为123456' })
        }

        // ---- 用户 ----
        if (path === '/api/user/profile' && method === 'GET') return withAuth(req, send, u => ok(send, userView(u)))
        if (path === '/api/user/profile' && method === 'PUT') {
          return withAuth(req, send, async (u) => {
            const body = await readBody(req)
            ;['name', 'phone', 'avatar'].forEach(k => { if (body[k] !== undefined) u[k] = body[k] })
            ;['preferences', 'taboo'].forEach(k => { if (body[k] !== undefined) u[k] = body[k] })
            if (body.monthly_budget !== undefined) u.monthly_budget = Number(body.monthly_budget)
            return ok(send, userView(u))
          })
        }
        if (path === '/api/user/behavior' && method === 'POST') {
          return withAuth(req, send, async (u) => {
            const body = await readBody(req)
            behaviorLog.push({ user_id: u.id, product_id: body.product_id, behavior_type: body.behavior_type })
            return ok(send, { id: behaviorLog.length })
          })
        }

        // ---- 推荐 ----
        if (path === '/api/products/recommend' && method === 'GET') {
          return withAuth(req, send, u => {
            const order = { guess: 0, prefer: 1, '': 2 }
            const sorted = [...products.filter(isProductAvailable)].sort((a, b) => order[a.demo_type] - order[b.demo_type])
            ok(send, { recommend_reason: '基于你的饮食偏好（川菜、家常菜、麻辣）与生活费等综合排序', ...paginate(sorted.map(p => productCard(p, u)), q) })
          })
        }
        if (path === '/api/products/guess-you-like' && method === 'GET') {
          return withAuth(req, send, u => ok(send, {
            recommend_reason: '和您一样喜欢川菜的同学也在买',
            ...paginate(products.filter(p => isProductAvailable(p) && p.demo_type === 'guess').map(p => productCard(p, u)), q)
          }))
        }
        if (path === '/api/products/nearby' && method === 'GET') {
          return withAuth(req, send, u => ok(send, paginate(products.filter(isProductAvailable).sort((a, b) => a.distance - b.distance).map(p => productCard(p, u)), q), 200))
        }

        // ---- 商品（商家） ----
        if (path === '/api/products/mine' && method === 'GET') {
          return withRole(req, send, [2], (u) => {
            const m = merchantOf(u.id)
            ok(send, products.filter(p => p.merchant_id === (m ? m.user_id : u.id) && !isProductExpired(p)).map(p => productCard(p, u)))
          })
        }
        if (path === '/api/products' && method === 'POST') {
          return withRole(req, send, [2], async (u) => {
            const m = merchantOf(u.id)
            const body = await readBody(req)
            if (!m || m.audit_status !== 1) return fail(send, 20003, '商家未通过审核')
            if (!body.title || body.original_price == null || body.discount_price == null || !body.expire_time) return fail(send, 400, '请填写完整商品信息')
            const openTime = body.business_open_time || DEFAULT_BUSINESS_OPEN_TIME
            const closeTime = body.business_close_time || DEFAULT_BUSINESS_CLOSE_TIME
            if (!BUSINESS_TIME_PATTERN.test(openTime) || !BUSINESS_TIME_PATTERN.test(closeTime)) return fail(send, 400, '营业时间格式应为 HH:mm')
            if (openTime === closeTime) return fail(send, 400, '开门时间和关门时间不能相同')
            const risk = riskCheck(body)
            if (risk) {
              const prod = addProduct({ merchant_id: u.id, title: body.title, description: body.description, category: body.category, original_price: body.original_price, discount_price: body.discount_price, quantity: body.quantity, expire_time: body.expire_time, business_open_time: openTime, business_close_time: closeTime, location: body.location, lat: body.lat, lng: body.lng, image: body.image || '', status: 3, risk_flag: 1 })
              riskLogs.unshift({ id: riskLogs.length + 1, product_id: prod.id, merchant_id: u.id, risk_type: risk.type, risk_detail: risk.msg, is_resolved: 0, created_at: hoursFromNow(0), risk_code: risk.code })
              return fail(send, risk.code, risk.msg)
            }
            const prod = addProduct({ merchant_id: u.id, title: body.title, description: body.description, category: body.category, original_price: body.original_price, discount_price: body.discount_price, quantity: body.quantity, expire_time: body.expire_time, business_open_time: openTime, business_close_time: closeTime, location: body.location, lat: body.lat, lng: body.lng, image: body.image || '', status: 1, risk_flag: 0 })
            ok(send, productCard(prod, u))
          })
        }
        const prodMatch = path.match(/^\/api\/products\/(\d+)$/)
        if (prodMatch && method === 'GET') {
          return withAuth(req, send, u => {
            const p = productOf(prodMatch[1])
            if (!p) return fail(send, 404, '商品不存在')
            if (isProductExpired(p)) return fail(send, 41004, '该商品已过期')
            p.view_count = (p.view_count || 0) + 1
            const m = merchantOf(p.merchant_id)
            ok(send, { ...productCard(p, u), merchant: { shop_name: m ? m.shop_name : '' } })
          })
        }
        const offlineMatch = path.match(/^\/api\/products\/(\d+)\/offline$/)
        if (offlineMatch && method === 'PUT') {
          return withRole(req, send, [2, 3], (u) => {
            const p = productOf(offlineMatch[1])
            if (!p) return fail(send, 404, '商品不存在')
            if (Number(p.risk_flag) === 1 || Number(p.status) === 3) return fail(send, 41004, '风控拦截商品需由超管误判恢复后才能操作')
            p.status = p.status === 0 ? 1 : 0
            ok(send, productCard(p, u))
          })
        }
        const favMatch = path.match(/^\/api\/products\/(\d+)\/favorite$/)
        if (favMatch && method === 'POST') {
          return withAuth(req, send, async (u) => {
            const body = await readBody(req)
            const p = productOf(favMatch[1])
            if (!p) return fail(send, 404, '商品不存在')
            let fav = favorites.get(u.id) || new Set()
            const want = body.favorite === true || body.favorite === undefined
            if (want) { fav.add(p.id); p.fav_count = (p.fav_count || 0) + 1 } else { fav.delete(p.id); p.fav_count = Math.max(0, (p.fav_count || 0) - 1) }
            favorites.set(u.id, fav)
            return ok(send, { favorite: want, fav_count: p.fav_count })
          })
        }

        // ---- 订单 ----
        if (path === '/api/orders' && method === 'GET') {
          autoCompleteOrders()
          return withAuth(req, send, u => {
            if (u.role === 2) {
              const m = merchantOf(u.id)
              const mine = orders.filter(o => productOf(o.product_id) && (m ? m.user_id : u.id) === productOf(o.product_id).merchant_id)
              const status = q.get('status'); let list = mine
              if (status !== null && status !== '') list = list.filter(o => o.status === Number(status))
              ok(send, list.map(o => orderView(o, true)))
            } else {
              const status = q.get('status'); let list = orders.filter(o => o.user_id === u.id)
              if (status !== null && status !== '') list = list.filter(o => o.status === Number(status))
              ok(send, list.map(o => orderView(o)))
            }
          })
        }
        if (path === '/api/orders/summary' && method === 'GET') {
          return withRole(req, send, [1, 2], u => ok(send, orderSummary(u)))
        }
        if (path === '/api/orders/refund-requests' && method === 'GET') {
          return withRole(req, send, [1], u => {
            ok(send, refundApplications.filter(item => item.user_id === u.id).map(refundApplicationView))
          })
        }
        if (path === '/api/orders' && method === 'POST') {
          return withRole(req, send, [1], async (u) => {
            const body = await readBody(req)
            const p = productOf(body.product_id)
            if (!p || p.status !== 1 || Number(p.risk_flag) === 1) return fail(send, 400, '商品已售罄、已下架或被风控拦截')
            if (isProductExpired(p)) return fail(send, 400, '商品已过期，无法下单')
            const quantity = Number(body.quantity || 1)
            if (!Number.isInteger(quantity) || quantity < 1 || quantity > 99 || p.quantity < quantity) return fail(send, 400, '商品库存不足')
            seq.order += 1
            const code = String(Math.floor(100000 + Math.random() * 900000))
            const createdAt = new Date()
            const closing = nextClosingTime(createdAt, p.business_close_time)
            const expiry = parseApiTime(p.expire_time)
            const productExpiresFirst = Number.isFinite(expiry) && expiry < closing.getTime()
            const pickupDeadline = productExpiresFirst ? new Date(expiry) : closing
            const o = {
              id: seq.order, user_id: u.id, product_id: p.id,
              quantity,
              original_price: toMoney(p.original_price), price: toMoney(p.discount_price),
              status: 0, pickup_code: code, created_at: fmt(createdAt),
              pickup_deadline: fmt(pickupDeadline),
              deadline_reason: productExpiresFirst ? 'product_expired' : 'business_close',
              picked_at: null, payment_status: 'paid'
            }
            orders.push(o)
            p.quantity -= o.quantity
            p.order_count = Number(p.order_count || 0) + 1
            if (p.quantity === 0) p.status = 2
            return ok(send, orderView(o))
          })
        }
        const refundMatch = path.match(/^\/api\/orders\/(\d+)\/refund$/)
        if (refundMatch && method === 'PUT') {
          return withRole(req, send, [1], (u) => {
            autoCompleteOrders()
            const o = orders.find(x => x.id === Number(refundMatch[1]))
            if (!o) return fail(send, 404, '订单不存在')
            if (o.user_id !== u.id) return fail(send, 403, '无权退款该订单')
            if (o.status !== 0) return fail(send, 400, '订单已完成或关闭，无法退款')
            const refundDeadline = Math.min(
              parseApiTime(o.created_at) + REFUND_WINDOW_SECONDS * 1000,
              pickupDeadline(o).getTime()
            )
            if (Date.now() > refundDeadline) return fail(send, 400, '5 分钟自行退款时限已过；实际领取后如有食品问题，可提交管理员审核')

            closeOrder(o, 'student_refund', 'refunded')
            const p = productOf(o.product_id)
            if (p) {
              p.quantity += Number(o.quantity || 0)
              p.order_count = Math.max(0, Number(p.order_count || 0) - 1)
              if (p.status === 2 && !isProductExpired(p)) p.status = 1
            }
            return ok(send, orderView(o))
          })
        }
        const refundRequestMatch = path.match(/^\/api\/orders\/(\d+)\/refund-request$/)
        if (refundRequestMatch && method === 'POST') {
          return withRole(req, send, [1], async (u) => {
            const body = await readBody(req)
            const o = orders.find(x => x.id === Number(refundRequestMatch[1]))
            if (!o) return fail(send, 404, '订单不存在')
            if (o.user_id !== u.id) return fail(send, 403, '无权为该订单提交售后')
            if (o.status !== 1 || o.completion_type !== 'merchant_confirmed') {
              if (o.status === 1) return fail(send, 400, '未按时领取而自动完成的订单不支持退款')
              return fail(send, 400, '只有实际领取后发现食品问题才能提交管理员审核')
            }
            if (refundApplications.some(item => item.order_id === o.id)) return fail(send, 400, '该订单已经提交过售后申请')
            const reason = String(body.reason || '').trim()
            if (reason.length < 5 || reason.length > 500) return fail(send, 400, '请填写 5 至 500 字的问题说明')
            seq.refund += 1
            const application = {
              id: seq.refund,
              order_id: o.id,
              user_id: u.id,
              reason,
              evidence_image: body.evidence_image || '',
              status: 0,
              admin_remark: '',
              created_at: fmt(new Date()),
              reviewed_at: null
            }
            refundApplications.unshift(application)
            return ok(send, refundApplicationView(application))
          })
        }
        if (path === '/api/orders/verify' && method === 'POST') {
          return withRole(req, send, [2, 3], async (u) => {
            autoCompleteOrders()
            const body = await readBody(req)
            const o = orders.find(x => x.status === 0 && x.pickup_code === String(body.pickup_code || ''))
            if (!o) return fail(send, 400, '取货码无效或订单已处理')
            settleOrder(o, 'merchant_confirmed')
            return ok(send, orderView(o, true))
          })
        }
        const pickupMatch = path.match(/^\/api\/orders\/(\d+)\/pickup$/)
        if (pickupMatch && method === 'PUT') {
          return withRole(req, send, [2, 3], (u) => {
            autoCompleteOrders()
            const o = orders.find(x => x.id === Number(pickupMatch[1]))
            if (!o) return fail(send, 404, '订单不存在')
            if (u.role === 2 && productOf(o.product_id) && productOf(o.product_id).merchant_id !== merchantOf(u.id).user_id) return fail(send, 403, '无权核销该订单')
            if (o.status !== 0) return fail(send, 400, '订单已完成，请勿重复操作')
            settleOrder(o, 'merchant_confirmed')
            return ok(send, orderView(o, true))
          })
        }

        // ---- 超管：商家审核 ----
        if (path === '/api/admin/merchants/pending' && method === 'GET') {
          return withRole(req, send, [3], () => {
            ok(send, merchants.filter(m => m.audit_status === 0).map(m => {
              const u = users.find(x => x.id === m.user_id) || {}
              return { id: m.id, user_id: m.user_id, shop_name: m.shop_name, license_img: m.license_img, location: m.location, lat: m.lat, lng: m.lng, login_name: u.login_name, phone: u.phone || '', name: u.name || '', created_at: m.created_at }
            }))
          })
        }
        const auditMatch = path.match(/^\/api\/admin\/merchants\/(\d+)\/audit$/)
        if (auditMatch && method === 'PUT') {
          return withRole(req, send, [3], async (u) => {
            const body = await readBody(req)
            const m = merchantById(auditMatch[1])
            if (!m) return fail(send, 404, '商家不存在')
            m.audit_status = Number(body.audit_status)
            m.audit_reason = body.reason || ''
            return ok(send, { id: m.id, shop_name: m.shop_name, audit_status: m.audit_status })
          })
        }

        // ---- 超管：食品问题退款审核 ----
        if (path === '/api/admin/refund-requests' && method === 'GET') {
          return withRole(req, send, [3], () => {
            const rawStatus = q.get('status')
            let list = [...refundApplications]
            if (rawStatus !== null && rawStatus !== '') list = list.filter(item => item.status === Number(rawStatus))
            ok(send, list.map(refundApplicationView))
          })
        }
        const refundAuditMatch = path.match(/^\/api\/admin\/refund-requests\/(\d+)\/audit$/)
        if (refundAuditMatch && method === 'PUT') {
          return withRole(req, send, [3], async () => {
            const body = await readBody(req)
            const application = refundApplications.find(item => item.id === Number(refundAuditMatch[1]))
            if (!application) return fail(send, 404, '退款申请不存在')
            if (application.status !== 0) return fail(send, 400, '该退款申请已经审核，请勿重复操作')
            const auditStatus = Number(body.audit_status)
            const remark = String(body.admin_remark || '').trim()
            if (![1, 2].includes(auditStatus)) return fail(send, 400, 'audit_status 仅支持 1（通过）或 2（驳回）')
            if (auditStatus === 2 && !remark) return fail(send, 400, '驳回申请时请填写审核说明')
            if (auditStatus === 1) {
              const o = orders.find(order => order.id === application.order_id)
              if (!o || o.status !== 1 || o.completion_type !== 'merchant_confirmed') return fail(send, 400, '订单状态已变化，当前无法执行退款')
              o.status = 2
              o.payment_status = 'refunded'
              o.close_reason = 'admin_refund'
              o.closed_at = fmt(new Date())
            }
            application.status = auditStatus
            application.admin_remark = remark || '食品质量问题审核通过，款项原路退回'
            application.reviewed_at = fmt(new Date())
            return ok(send, refundApplicationView(application))
          })
        }

        // ---- 超管：风控日志 ----
        if (path === '/api/admin/risk-logs' && method === 'GET') {
          return withRole(req, send, [3], () => {
            const logs = [...riskLogs].reverse().map(l => {
              const p = productOf(l.product_id)
              const m = merchantOf(l.merchant_id)
              return { ...l, risk_type_name: RISK_TYPE_NAME[l.risk_type] || '未知', product_title: p ? p.title : '已删除商品', shop_name: m ? m.shop_name : '-' }
            })
            const onlyResolved = q.get('resolved')
            if (onlyResolved === '1') return ok(send, logs.filter(l => l.is_resolved === 1))
            if (onlyResolved === '0') return ok(send, logs.filter(l => l.is_resolved === 0))
            ok(send, logs)
          })
        }
        const resolveMatch = path.match(/^\/api\/admin\/risk-logs\/(\d+)\/resolve$/)
        if (resolveMatch && method === 'PUT') {
          return withRole(req, send, [3], async (u) => {
            const body = await readBody(req)
            const l = riskLogs.find(x => x.id === Number(resolveMatch[1]))
            if (!l) return fail(send, 404, '风控日志不存在')
            l.is_resolved = 1
            if (body.restore !== false) { const p = productOf(l.product_id); if (p) { p.status = 1; p.risk_flag = 0 } }
            return ok(send, { id: l.id, is_resolved: 1 })
          })
        }

        // ---- 超管：数据看板 ----
        if (path === '/api/admin/statistics' && method === 'GET') {
          return withRole(req, send, [3], () => {
            const studentCount = users.filter(u => u.role === 1).length
            const merchantCount = users.filter(u => u.role === 2).length
            const adminCount = users.filter(u => u.role === 3).length
            const pickupCount = orders.filter(o => o.status === 1).length
            const pendingCount = orders.filter(o => o.status === 0).length
            const lowIncome = users.filter(u => u.role === 1 && u.monthly_budget && u.monthly_budget < 1200).length
            const unpaid = merchants.filter(m => m.audit_status === 0).length

            const days = Array.from({ length: 7 }, (_, i) => { const d = new Date(Date.now() - (6 - i) * 86400000); return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}` })
            const ordersByDay = days.map(date => ({ date, count: orders.filter(o => String(o.created_at).slice(0, 10) === date).length }))

            const riskByType = [1, 2, 3].map(t => ({ label: RISK_TYPE_NAME[t], value: riskLogs.filter(l => l.risk_type === t).length }))
            const riskResolved = riskLogs.filter(l => l.is_resolved === 1).length

            ok(send, {
              total_users: users.length,
              total_orders: orders.length,
              student_count: studentCount,
              merchant_count: merchantCount,
              admin_count: adminCount,
              pending_merchants: unpaid,
              help: { low_income_user_count: lowIncome, pickup_count: pickupCount, pending_count: pendingCount, total_fav: products.reduce((s, p) => s + (p.fav_count || 0), 0) },
              risk: { total: riskLogs.length, resolved: riskResolved, active: riskLogs.length - riskResolved },
              users_by_role: [{ label: '学生', value: studentCount }, { label: '商家', value: merchantCount }, { label: '超管', value: adminCount }],
              orders_by_day: ordersByDay,
              risk_by_type: riskByType
            })
          })
        }

        return fail(send, 404, '接口不存在：' + method + ' ' + path)
      })
    }
  }
}
