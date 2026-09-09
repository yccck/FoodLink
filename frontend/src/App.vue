<template>
  <div id="layout">
    <header class="topbar" v-if="authStore.isLoggedIn">
      <div class="topbar-inner">
        <span class="brand">食愿</span>
        <nav class="topnav">
          <router-link to="/profile">个人中心</router-link>
          <router-link to="/orders">我的订单</router-link>
        </nav>
        <div class="grow"></div>
        <span class="hello">你好，{{ authStore.user?.name || '' }}</span>
        <button class="btn btn-ghost" @click="logout">退出</button>
      </div>
    </header>
    <main class="page">
      <router-view />
    </main>
  </div>
</template>

<script setup>
import { useAuthStore } from './stores/user'

const authStore = useAuthStore()
function logout() {
  authStore.logout()
}
</script>