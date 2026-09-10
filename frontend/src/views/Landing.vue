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
/* 入口卡片：橙色文字 + 略深白底突显卡片 */
.ds-hero-cta-block,
.ds-hero-cta-title { color: #f97316 !important; }
.ds-hero-cta-block {
  background: rgba(255,255,255,0.55) !important;
  border: 1px solid rgba(0,0,0,0.06);
  box-shadow: 0 1px 3px rgba(0,0,0,0.04);
}

.ds-clone [style*="opacity"] { transition: opacity .5s ease, transform .5s ease; }
</style>