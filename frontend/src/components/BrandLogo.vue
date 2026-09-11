<template>
  <img :class="['brand-logo', `brand-logo--${size}`]" src="/ChatGPTlogo.png" alt="食愿 FoodLink" />
</template>

<script setup>
defineProps({
  size: {
    type: String,
    default: 'medium',
    validator: (value) => ['small', 'medium', 'large'].includes(value)
  }
})
</script>

<style scoped>
.brand-logo { display: block; width: auto; object-fit: contain; }
.brand-logo--small { height: 46px; }
.brand-logo--medium { height: 68px; }
.brand-logo--large { height: 86px; }
</style>
