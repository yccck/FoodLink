<template>
  <!-- 一比一复刻 DeepSeek 官网：真实 HTML + 官网原生 CSS，零自定义排布 -->
  <div class="ds-clone" ref="root" v-html="html"></div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import html from './deepseek-home.html?raw'
import '../assets/deepseek.css'

const root = ref(null)
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
})
</script>

<style>
/* 落地页：整体白底，承接官网 HTML 结构 */
.ds-clone { background: #ffffff; }
/* hero 斜向淡橙光：静止，点缀白底 */
.ds-glow-bg {
  background-color: #ffffff;
  background-image:
    linear-gradient(118deg,
      transparent 30%,
      rgba(255,150,80,0.13) 43%,
      rgba(255,120,45,0.17) 52%,
      rgba(255,160,95,0.11) 61%,
      transparent 74%),
    linear-gradient(118deg,
      transparent 56%,
      rgba(255,140,60,0.09) 67%,
      rgba(255,120,45,0.12) 78%,
      transparent 92%);
  background-size: 260% 260%;
  background-repeat: repeat;
  background-position: 22% 14%;
}
/* 顶栏品牌名：logo 图标位留空，仅显示文字“食愿”（深橙色） */
.ds-brand-name {
  font-size: 22px;
  font-weight: 700;
  letter-spacing: 1px;
  line-height: 1;
  color: #ea580c;
}
/* 入口卡片：橙色文字 + 略深白底突显卡片 */
.ds-hero-cta-block,
.ds-hero-cta-title { color: #f97316 !important; }
.ds-hero-cta-block {
  background: #f4f4f2 !important;
  border: 1px solid rgba(0,0,0,0.05);
  box-shadow: 0 1px 3px rgba(0,0,0,0.05);
}

.ds-clone [style*="opacity"] { transition: opacity .5s ease, transform .5s ease; }
</style>