<script setup lang="ts">
withDefaults(defineProps<{
  variant?: 'marker' | 'solid' | 'box'
}>(), {
  variant: 'marker',
})
</script>

<template>
  <span class="josh-hi" :class="`josh-hi--${variant}`">
    <slot />
  </span>
</template>

<style scoped>
.josh-hi {
  color: var(--josh-accent);
  font-weight: 500;
}

.josh-hi--marker {
  background-image: linear-gradient(
    to top,
    color-mix(in oklab, var(--josh-accent) 25%, transparent) 0%,
    color-mix(in oklab, var(--josh-accent) 25%, transparent) 30%,
    transparent 30%
  );
  background-repeat: no-repeat;
  background-size: 100% 100%;
  padding: 0 0.1em;
}

.josh-hi--solid {
  color: var(--josh-accent);
}

.josh-hi--box {
  border: 1px solid var(--josh-accent);
  padding: 0.05em 0.35em;
  border-radius: 3px;
}
</style>
