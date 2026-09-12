<template>
  <!-- 一比一复刻 DeepSeek 官网：真实 HTML + 官网原生 CSS，零自定义排布 -->
  <div class="ds-clone" ref="root" v-html="renderedHtml"></div>
</template>

<script setup>
import { onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import html from './deepseek-home.html?raw'
const baseUrl = import.meta.env.BASE_URL || '/'
const renderedHtml = html.replace(/(src=["'])\//g, `$1${baseUrl}`)
import '../assets/deepseek.css'
import { useAuthStore } from '../stores/user'
import { toast } from '../utils/toast'

const root = ref(null)
const router = useRouter()
const authStore = useAuthStore()
let removeScroll = null

// 入口卡片 href -> 所需角色
const ENTRY_ROLE = { '/home': 1, '/merchant/home': 2, '/admin/dashboard': 3 }
const ROLE_NAME = { 1: '学生', 2: '商家', 3: '管理员' }

onMounted(() => {
  const clone = root.value
  if (!clone) return
  // 官网内容默认 innerHTML 里 opacity:0，靠官网 JS 点亮；此处等价地把透明内容恢复可见（不改任何布局外观）
  clone.querySelectorAll('[style*="opacity"]').forEach((el) => {
    if (el.style.opacity === '0') {
      el.style.opacity = '1'
      if (el.style.transform) el.style.transform = 'translateY(0)'
    }
  })
  // 灵动岛：下滑超过阈值时，整个顶栏（logo + 登录态）收缩为居中胶囊浮岛
  const bar = clone.querySelector('.ds-header-bar')
  const onScroll = () => {
    if (!bar) return
    const y = window.pageYOffset || document.documentElement.scrollTop || 0
    bar.classList.toggle('is-scrolled', y > 40)
  }
  window.addEventListener('scroll', onScroll, { passive: true })
  onScroll()
  removeScroll = () => window.removeEventListener('scroll', onScroll)

  ensureHeaderUser(clone)
  bindEntryLinks(clone)
})

// 入口卡片原本是原生 <a href>，未登录时会被守卫统一弹到登录页（且不带身份），
// 导致三个入口看起来是同一个界面。这里改为带身份的 SPA 跳转。
function bindEntryLinks(clone) {
  clone.querySelectorAll('a.ds-hero-cta-block[href]').forEach((a) => {
    const target = a.getAttribute('href')
    const role = ENTRY_ROLE[target]
    if (!role) return
    a.addEventListener('click', (e) => {
      e.preventDefault()
      const user = authStore.user
      if (!authStore.isLoggedIn) {
        router.push({ path: '/login', query: { role, redirect: target } })
        return
      }
      if (user?.role === role) {
        router.push(target)
      } else {
        toast(`当前登录身份是${ROLE_NAME[user?.role] || '其他'}，请先退出登录再进入${ROLE_NAME[role]}入口`, 'error')
      }
    })
  })
}

function ensureHeaderUser(clone) {
  const bar = clone.querySelector('.ds-header-bar')
  if (!bar) return
  let cluster = bar.querySelector('.ds-header-user')
  if (authStore.isLoggedIn) {
    if (!cluster) {
      cluster = document.createElement('div')
      cluster.className = 'ds-header-user'
      bar.appendChild(cluster)
    }
    const name = authStore.user?.name || ''
    cluster.innerHTML =
      '<span class="ds-hello">你好，' + name + '</span>' +
      '<button type="button" class="ds-logout">退出登录</button>'
    const btn = cluster.querySelector('.ds-logout')
    btn.onclick = () => authStore.logout()
  } else if (cluster) {
    cluster.remove()
  }
}

watch(
  () => [authStore.isLoggedIn, authStore.user?.name || ''],
  () => { if (root.value) ensureHeaderUser(root.value) }
)

onBeforeUnmount(() => {
  if (removeScroll) removeScroll()
})
</script>

<style>
/* 落地页：整体白底，承接官网 HTML 结构 */
.ds-clone { background: #ffffff; }
/* hero 橙色圆形光斑：静止，点缀白底 */
.ds-glow-bg {
  background-color: #ffffff;
  background-image:
    radial-gradient(circle at center, rgba(255,151,60,0.32) 0%, transparent 58%),
    radial-gradient(circle at center, rgba(255,122,40,0.24) 0%, transparent 55%);
  background-size: 640px 640px, 560px 560px;
  background-repeat: no-repeat;
  background-position: 12% 8%, 86% 16%;
}
/* 顶栏品牌名：logo 图标位留空，仅显示文字“食愿”（深橙色） */
.ds-brand-name {
  font-size: 22px;
  font-weight: 700;
  letter-spacing: 1px;
  line-height: 1;
  color: #ea580c;
}
/* 入口卡片：深绿色文字 + 略深白底突显卡片 */
.ds-hero-cta-block,
.ds-hero-cta-title { color: #0A5A3E !important; }
.ds-hero-cta-block {
  background: rgba(255,255,255,0.55) !important;
  border: 1px solid rgba(0,0,0,0.06);
  box-shadow: 0 1px 3px rgba(0,0,0,0.04);
}

/* 顶栏登录态：并入同一顶栏，随灵动岛一起收缩 */
.ds-header-user { display: flex; align-items: center; gap: 12px; white-space: nowrap; }
.ds-hello { font-size: 14px; font-weight: 600; color: #3f4a45; }
.ds-logout {
  font-size: 13px; color: #0A5A3E; background: rgba(255,255,255,0.6);
  border: 1px solid rgba(10,90,62,0.28); padding: 5px 14px; border-radius: 999px; cursor: pointer;
}
.ds-logout:hover { opacity: .9; }

.ds-clone [style*="opacity"] { transition: opacity .5s ease, transform .5s ease; }
</style>