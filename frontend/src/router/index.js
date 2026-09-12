import { createRouter, createWebHistory } from 'vue-router'

const roleHome = { 1: '/home', 2: '/merchant/home', 3: '/admin/dashboard' }

const routes = [
  { path: '/home', name: 'Home', component: () => import('../views/home/Home.vue'), meta: { auth: true, roles: [1] } },
  { path: '/', name: 'Landing', component: () => import('../views/Landing.vue'), meta: { public: true, full: true } },
  { path: '/login', name: 'Login', component: () => import('../views/auth/Login.vue'), meta: { public: true, full: true } },
  { path: '/register/student', name: 'RegisterStudent', component: () => import('../views/auth/RegisterStudent.vue'), meta: { public: true, full: true } },
  { path: '/register/merchant', name: 'RegisterMerchant', component: () => import('../views/auth/RegisterMerchant.vue'), meta: { public: true, full: true } },
  { path: '/register/admin', name: 'RegisterAdmin', component: () => import('../views/auth/RegisterAdmin.vue'), meta: { public: true, full: true } },
  { path: '/forgot', name: 'ForgotPassword', component: () => import('../views/auth/ForgotPassword.vue'), meta: { public: true, full: true } },

  { path: '/profile', name: 'Profile', component: () => import('../views/user/Profile.vue'), meta: { auth: true, roles: [1] } },
  { path: '/profile/edit', name: 'ProfileEdit', component: () => import('../views/user/ProfileEdit.vue'), meta: { auth: true, roles: [1], hideTopbar: true } },
  { path: '/favorites', name: 'Favorites', component: () => import('../views/user/Favorites.vue'), meta: { auth: true, roles: [1] } },
  { path: '/orders', name: 'OrderList', component: () => import('../views/order/OrderList.vue'), meta: { auth: true, roles: [1] } },
  { path: '/product/:id', name: 'ProductDetail', component: () => import('../views/product/Detail.vue'), meta: { auth: true, roles: [1] } },
  { path: '/order/pickup', name: 'Pickup', component: () => import('../views/order/Pickup.vue'), meta: { auth: true, roles: [1] } },

  { path: '/merchant/home', name: 'MerchantHome', component: () => import('../views/merchant/MerchantHome.vue'), meta: { auth: true, roles: [2] } },
  { path: '/merchant/publish', name: 'MerchantPublish', component: () => import('../views/merchant/MerchantPublish.vue'), meta: { auth: true, roles: [2] } },
  { path: '/merchant/orders', name: 'MerchantOrders', component: () => import('../views/merchant/MerchantOrders.vue'), meta: { auth: true, roles: [2] } },

  { path: '/admin/dashboard', name: 'AdminDashboard', component: () => import('../views/admin/AdminDashboard.vue'), meta: { auth: true, roles: [3] } },
  { path: '/admin/audit', name: 'AdminAudit', component: () => import('../views/admin/AdminAudit.vue'), meta: { auth: true, roles: [3] } },
  { path: '/admin/risk-logs', name: 'AdminRiskLogs', component: () => import('../views/admin/AdminRiskLogs.vue'), meta: { auth: true, roles: [3] } },
  { path: '/admin/refunds', name: 'AdminRefunds', component: () => import('../views/admin/AdminRefunds.vue'), meta: { auth: true, roles: [3] } },
  { path: '/admin/consumption', name: 'AdminConsumption', component: () => import('../views/admin/AdminConsumption.vue'), meta: { auth: true, roles: [3] } },

  { path: '/:pathMatch(.*)*', redirect: '/' }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// 全局守卫：未登录跳登录页；角色不匹配跳回本角色首页
router.beforeEach((to) => {
  const token = localStorage.getItem('shiyuan_token')
  let user = null
  try { user = JSON.parse(localStorage.getItem('shiyuan_user') || 'null') } catch (e) { user = null }

  if (!to.meta?.public && !token) {
    return { name: 'Login', query: { redirect: to.fullPath } }
  }
  if (!to.meta?.public && Array.isArray(to.meta?.roles) && to.meta.roles.length && user) {
    if (!to.meta.roles.includes(user.role)) {
      return roleHome[user.role] || '/home'
    }
  }
  return true
})

export default router
