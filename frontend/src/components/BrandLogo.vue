<template>
  <div :class="['brand-logo', `brand-logo--${size}`]">
    <img class="brand-logo__image" src="/foodlink-logo.png" alt="食愿 FoodLink" />
  </div>
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
