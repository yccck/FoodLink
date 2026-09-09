import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  { path: '/', redirect: '/login' },
  { path: '/login', name: 'Login', component: () => import('../views/auth/Login.vue'), meta: { public: true } },
  { path: '/register/student', name: 'RegisterStudent', component: () => import('../views/auth/RegisterStudent.vue'), meta: { public: true } },
  { path: '/register/merchant', name: 'RegisterMerchant', component: () => import('../views/auth/RegisterMerchant.vue'), meta: { public: true } },
  { path: '/forgot', name: 'ForgotPassword', component: () => import('../views/auth/ForgotPassword.vue'), meta: { public: true } },

  { path: '/profile', name: 'Profile', component: () => import('../views/user/Profile.vue'), meta: { auth: true, roles: [1] } },
  { path: '/profile/edit', name: 'ProfileEdit', component: () => import('../views/user/ProfileEdit.vue'), meta: { auth: true, roles: [1] } },
  { path: '/orders', name: 'OrderList', component: () => import('../views/order/OrderList.vue'), meta: { auth: true, roles: [1] } },
  { path: '/product/:id', name: 'ProductDetail', component: () => import('../views/product/Detail.vue'), meta: { auth: true } },
  { path: '/order/pickup', name: 'Pickup', component: () => import('../views/order/Pickup.vue'), meta: { auth: true, roles: [1] } },
  { path: '/:pathMatch(.*)*', redirect: '/login' }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// 全局守卫：未登录跳登录页
router.beforeEach(async (to) => {
  const auth = to.meta?.public ? null : localStorage.getItem('shiyuan_token')
  if (!to.meta?.public && !auth) {
    return { name: 'Login', query: { redirect: to.fullPath } }
  }
  return true
})

export default router