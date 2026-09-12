<template>
  <div id="layout">
    <header class="topbar" v-if="authStore.isLoggedIn && route.path !== '/'">
      <div class="topbar-inner">
        <span class="brand"><img src="/ChatGPTlogo.png" alt="食愿" style="height:40px;width:auto;display:block;" /></span>
        <button class="nav-toggle" type="button" aria-label="打开导航菜单" :aria-expanded="navOpen" @click="navOpen = !navOpen">
          <span></span><span></span><span></span>
        </button>
        <div class="nav-area" :class="{ open: navOpen }">
          <nav class="topnav" v-if="role === 1" @click="navOpen = false">
            <router-link to="/home">首页</router-link>
            <router-link to="/orders">我的订单</router-link>
            <router-link to="/favorites">我的收藏</router-link>
            <router-link to="/profile">个人中心</router-link>
          </nav>
          <nav class="topnav" v-else-if="role === 2" @click="navOpen = false">
            <router-link to="/merchant/home">商品管理</router-link>
            <router-link to="/merchant/publish">发布商品</router-link>
            <router-link to="/merchant/orders">订单管理</router-link>
          </nav>
          <nav class="topnav" v-else-if="role === 3" @click="navOpen = false">
            <router-link to="/admin/dashboard">数据看板</router-link>
            <router-link to="/admin/audit">商家审核</router-link>
            <router-link to="/admin/risk-logs">风控日志</router-link>
            <router-link to="/admin/refunds">退款审核</router-link>
          </nav>
          <div class="grow"></div>
          <span class="hello">你好，{{ authStore.user?.name || '' }}</span>
          <button class="btn btn-ghost logout-button" @click="logout">退出登录</button>
        </div>
        <button v-if="navOpen" class="nav-backdrop" type="button" aria-label="关闭导航菜单" @click="navOpen = false"></button>
      </div>
    </header>
    <main :class="['page', { full: route.meta && route.meta.full, wide: ['/home', '/orders', '/favorites', '/profile', '/profile/edit', '/merchant/home', '/merchant/orders', '/admin/dashboard'].includes(route.path) }]">
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
const navOpen = ref(false)
watch(() => route.fullPath, () => { navOpen.value = false })
function logout() { navOpen.value = false; authStore.logout() }
</script>
