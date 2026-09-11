<template>
  <div v-if="open" class="mask" @click.self="close">
    <div class="dialog" role="dialog" aria-modal="true">
      <span class="icon" aria-hidden>{{ icon }}</span>
      <h3>{{ title }}</h3>
      <p v-for="(line, i) in lines" :key="i" class="line">{{ line }}</p>
      <slot />
      <button class="confirm" type="button" @click="close">{{ confirmText }}</button>
    </div>
  </div>
</template>

<script setup>
defineProps({
  open: { type: Boolean, default: false },
  icon: { type: String, default: '✅' },
  title: { type: String, default: '操作成功' },
  lines: { type: Array, default: () => [] },
  confirmText: { type: String, default: '知道了' }
})
const emit = defineEmits(['close'])
function close() { emit('close') }
</script>

<style scoped>
.mask { position: fixed; inset: 0; z-index: 999; display: grid; place-items: center; padding: 20px; background: rgba(52,38,24,.45); backdrop-filter: blur(2px); }
.dialog { width: min(100%, 380px); padding: 28px 24px 22px; border-radius: 26px; background: #fffdf7; box-shadow: 0 26px 70px rgba(60,42,25,.3); text-align: center; animation: pop .18s ease-out; }
.icon { display: grid; width: 56px; height: 56px; margin: 0 auto 12px; place-items: center; border-radius: 50%; background: #eef7e8; font-size: 27px; }
h3 { margin: 0 0 10px; color: #3d352b; font-size: 19px; }
.line { margin: 0 0 6px; color: #6f665c; font-size: 14px; line-height: 1.7; }
.confirm { width: 100%; min-height: 46px; margin-top: 14px; border: 0; border-radius: 999px; background: #e97950; color: #fff; font-size: 15px; font-weight: 800; cursor: pointer; }
.confirm:hover { background: #e26a3f; }
@keyframes pop { from { transform: scale(.94); opacity: 0 } to { transform: scale(1); opacity: 1 } }
</style>
