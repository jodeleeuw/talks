<script setup>
// <img> for files in public/: prefixes the deploy base so paths keep working
// when the talk is served from a subdirectory (see CLAUDE.md, Deploy).
defineProps({
  src: { type: String, required: true }, // e.g. 'images/turing.png'
  alt: { type: String, default: '' },
})
const base = import.meta.env.BASE_URL
</script>

<template>
  <img :src="base + src" :alt="alt" />
</template>
