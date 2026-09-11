<template>
  <div id="layout">
    <header class="topbar" v-if="authStore.isLoggedIn">
      <div class="topbar-inner">
        <router-link class="brand" :to="roleHome" aria-label="返回食愿首页">
          <span class="brand-symbol" aria-hidden="true">愿</span>
          <span class="brand-copy"><strong>食愿</strong><small>FoodLink</small></span>
        </router-link>
        <span class="mobile-page-title">{{ currentPageTitle }}</span>
        <button
          class="nav-toggle"
          type="button"
          :aria-label="menuOpen ? '关闭导航菜单' : '打开导航菜单'"
          title="导航菜单"
          :aria-expanded="menuOpen"
          aria-controls="primary-navigation"
          @click="menuOpen = !menuOpen"
        >
          <span></span><span></span><span></span>
        </button>
        <div id="primary-navigation" class="nav-area" :class="{ open: menuOpen }">
          <nav class="topnav" v-if="role === 1" aria-label="学生端导航">
            <router-link to="/home">首页</router-link>
            <router-link to="/profile">个人中心</router-link>
            <router-link to="/orders">我的订单</router-link>
          </nav>
          <nav class="topnav" v-else-if="role === 2" aria-label="商家端导航">
            <router-link to="/merchant/home">商品管理</router-link>
            <router-link to="/merchant/publish">发布商品</router-link>
            <router-link to="/merchant/orders">订单管理</router-link>
          </nav>
          <nav class="topnav" v-else-if="role === 3" aria-label="管理员导航">
            <router-link to="/admin/dashboard">数据看板</router-link>
            <router-link to="/admin/audit">商家审核</router-link>
            <router-link to="/admin/risk-logs">风控日志</router-link>
          </nav>
          <div class="grow"></div>
          <span class="hello">你好，{{ authStore.user?.name || '' }}</span>
          <button class="btn btn-ghost logout-button" type="button" @click="logout">退出登录</button>
        </div>
      </div>
    </header>
    <button v-if="menuOpen" class="nav-backdrop" aria-label="关闭导航菜单" @click="menuOpen = false"></button>
    <main :class="['page', { full: route.meta && route.meta.full }]">
      <router-view />
    </main>
  </div>
</template>

<script setup>
import { computed, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { useAuthStore } from './stores/user'

const authStore = useAuthStore()
const route = useRoute()
const role = computed(() => authStore.user?.role)
const menuOpen = ref(false)
const homeByRole = { 1: '/home', 2: '/merchant/home', 3: '/admin/dashboard' }
const pageNames = {
  '/home': '首页',
  '/profile': '个人中心',
  '/profile/edit': '编辑资料',
  '/orders': '我的订单',
  '/order/pickup': '取货凭证',
  '/merchant/home': '商品管理',
  '/merchant/publish': '发布商品',
  '/merchant/orders': '订单管理',
  '/admin/dashboard': '数据看板',
  '/admin/audit': '商家审核',
  '/admin/risk-logs': '风控日志'
}
const roleHome = computed(() => homeByRole[role.value] || '/')
const currentPageTitle = computed(() => pageNames[route.path] || (route.path.startsWith('/product/') ? '商品详情' : '食愿'))

function logout() {
  menuOpen.value = false
  authStore.logout()
}

watch(() => route.fullPath, () => { menuOpen.value = false })
</script>
