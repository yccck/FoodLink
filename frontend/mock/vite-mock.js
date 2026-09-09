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

// ---------- 内存数据 ----------
let seq = { user: 3, product: 0, order: 2 }

const users = [
  { id: 1, role: 1, login_name: '2021001', password: '123456', name: '张三',
    school: 'XX大学', student_id: '2021001', phone: '13800000000', avatar: '',
    preferences: { cuisine: ['川菜'], taste: ['麻辣'], meal_time: ['午餐', '晚餐'] },
    taboo: { allergens: ['花生'], dislikes: ['香菜'] }, monthly_budget: 1500, status: 1 },
  { id: 2, role: 2, login_name: 'shop001', password: '123456', name: '店铺账号', phone: '13811112222',
    school: '', student_id: '', status: 1 },
  { id: 3, role: 3, login_name: 'admin', password: '123456', name: '超级管理员', phone: '00000000000', status: 1 }
]
const merchants = [
  { user_id: 2, shop_name: 'XX风味小吃', license_img: '', location: 'XX大学南门15米',
    lat: 30.123, lng: 120.123, audit_status: 1 }
]

const products = []
const orders = []
const favorites = new Map() // userId -> Set(productId)
const behaviorLog = []

function addProduct(p) {
  seq.product += 1
  const prod = {
    id: seq.product, merchant_id: 2, title: p.title || '',
    description: p.description || '', category: p.category || '简餐',
    image: p.image || '', original_price: p.original_price || 0,
    discount_price: p.discount_price || 0, quantity: p.quantity || 10,
    expire_time: p.expire_time || '2026-09-30 18:00:00',
    location: p.location || 'XX大学南门', lat: p.lat || 30.123, lng: p.lng || 120.123,
    status: p.status ?? 1, view_count: p.view_count || 0, fav_count: p.fav_count || 0,
    order_count: p.order_count || 0, risk_flag: p.risk_flag || 0,
    created_at: '2026-09-09 10:00:00'
  }
  products.push(prod)
  return prod
}
let shop = merchants.find(m => m.user_id === 2)
addProduct({ title: '水煮鱼片 超值套餐', description: '鲜嫩鱼片，麻辣入味，配米饭一份。', category: '简餐', original_price: 28, discount_price: 12, quantity: 10, expire_time: '2026-09-10 18:00:00', location: shop.location, lat: shop.lat, lng: shop.lng, view_count: 96, fav_count: 12, order_count: 8 })
addProduct({ title: '麻辣香锅 单人份', description: '自选配菜现炒，性价比高。', category: '简餐', original_price: 22, discount_price: 10, quantity: 5, expire_time: '2026-09-10 20:00:00', location: shop.location, lat: shop.lat, lng: shop.lng, view_count: 60, fav_count: 6, order_count: 4 })
addProduct({ title: '现烤蛋挞 甜香四溢', description: '每日新鲜烘焙，外酥里嫩。', category: '烘焙', original_price: 18, discount_price: 8, quantity: 20, expire_time: '2026-09-09 19:00:00', location: shop.location, lat: shop.lat, lng: shop.lng, view_count: 42, fav_count: 9, order_count: 11 })

orders.push({ id: 1, user_id: 1, product_id: 1, quantity: 1, status: 0, pickup_code: '483920', created_at: '2026-09-09 12:10:00', picked_at: null })
orders.push({ id: 2, user_id: 1, product_id: 3, quantity: 1, status: 1, pickup_code: '774201', created_at: '2026-09-09 08:30:00', picked_at: '2026-09-09 09:00:00' })

function merchantOf(userId) { return merchants.find(m => m.user_id === userId) }
function productOf(id) { return products.find(p => p.id === Number(id)) }
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
  const auth = req.headers['authorization'] || ''
  const token = auth.replace(/^Bearer\s+/i, '')
  if (!token || !token.startsWith('mock-token-')) {
    send({ code: 401, message: '未登录或登录已过期', data: null }, 401)
    return
  }
  const loginName = token.replace('mock-token-', '')
  const user = users.find(u => u.login_name === loginName)
  if (!user) { send({ code: 401, message: '未登录或登录已过期', data: null }, 401); return }
  handler(user)
}

function userView(u, withToken) {
  const m = merchantOf(u.id)
  const view = {
    id: u.id, role: u.role, login_name: u.login_name, name: u.name,
    avatar: u.avatar || '', school: u.school || '', student_id: u.student_id || '',
    phone: u.phone || '', preferences: u.preferences || null, taboo: u.taboo || null,
    monthly_budget: u.monthly_budget ?? null, status: u.status,
    shop_name: m ? m.shop_name : '', license_img: m ? m.license_img : '',
    audit_status: m ? m.audit_status : -1
  }
  if (withToken) return { token: 'mock-token-' + u.login_name, user: view }
  return view
}

function orderView(o) {
  const p = productOf(o.product_id)
  const m = p ? merchantOf(p.merchant_id) : null
  return {
    id: o.id, product_id: o.product_id,
    product_title: p ? p.title : '商品', product_image: p ? p.image : '',
    shop_name: m ? m.shop_name : 'XX风味小吃',
    original_price: p ? p.original_price : 0, price: p ? p.discount_price : 0,
    quantity: o.quantity, status: o.status, pickup_code: o.pickup_code,
    expire_time: p ? p.expire_time : '', location: p ? p.location : '',
    created_at: o.created_at, picked_at: o.picked_at ?? null
  }
}

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
            users.push(u)
            return ok(send, { id: u.id })
          }
          const u = { id: seq.user, role: 2, login_name: body.login_name, password: body.password,
            name: body.shop_name, phone: body.phone, status: 1 }
          users.push(u)
          merchants.push({ user_id: u.id, shop_name: body.shop_name, license_img: body.license_img || '',
            location: body.location, lat: body.lat, lng: body.lng, audit_status: 0 })
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

        if (path === '/api/user/profile' && method === 'GET') {
          return withAuth(req, send, (u) => ok(send, userView(u)))
        }
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

        const prodMatch = path.match(/^\/api\/products\/(\d+)$/)
        if (prodMatch && method === 'GET') {
          return withAuth(req, send, (u) => {
            const p = productOf(prodMatch[1])
            if (!p) return fail(send, 404, '商品不存在')
            const m = merchantOf(p.merchant_id)
            p.view_count = (p.view_count || 0) + 1
            const fav = favorites.get(u.id)
            ok(send, { ...p, is_favorite: !!(fav && fav.has(p.id)), merchant: { shop_name: m ? m.shop_name : '' } })
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
            if (want) { fav.add(p.id); p.fav_count = (p.fav_count || 0) + 1 }
            else { fav.delete(p.id); p.fav_count = Math.max(0, (p.fav_count || 0) - 1) }
            favorites.set(u.id, fav)
            return ok(send, { favorite: want, fav_count: p.fav_count })
          })
        }

        if (path === '/api/orders' && method === 'GET') {
          return withAuth(req, send, (u) => {
            const status = q.get('status')
            let list = orders.filter(o => o.user_id === u.id)
            if (status !== null && status !== '') list = list.filter(o => o.status === Number(status))
            ok(send, list.map(orderView))
          })
        }
        if (path === '/api/orders' && method === 'POST') {
          return withAuth(req, send, async (u) => {
            const body = await readBody(req)
            const p = productOf(body.product_id)
            if (!p || p.status !== 1) return fail(send, 400, '商品已售罄或已下架')
            seq.order += 1
            const code = String(Math.floor(100000 + Math.random() * 900000))
            const o = { id: seq.order, user_id: u.id, product_id: p.id,
              quantity: Number(body.quantity || 1), status: 0, pickup_code: code,
              created_at: '2026-09-09 17:30:00', picked_at: null }
            orders.push(o)
            return ok(send, orderView(o))
          })
        }
        const pickupMatch = path.match(/^\/api\/orders\/(\d+)\/pickup$/)
        if (pickupMatch && method === 'PUT') {
          return withAuth(req, send, (u) => {
            const o = orders.find(x => x.id === Number(pickupMatch[1]))
            if (!o) return fail(send, 404, '订单不存在')
            o.status = 1; o.picked_at = '2026-09-09 18:00:00'
            return ok(send, orderView(o))
          })
        }

        return fail(send, 404, '接口不存在：' + method + ' ' + path)
      })
    }
  }
}