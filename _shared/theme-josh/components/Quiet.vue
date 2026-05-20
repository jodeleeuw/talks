<script setup lang="ts">
withDefaults(defineProps<{
  // 'muted' (default): same color as surrounding text but soft + lower opacity,
  // for de-emphasizing context around a <Hi> highlight in the same sentence.
  // 'strike': adds a strikethrough, useful when the text is being negated.
  variant?: 'muted' | 'strike'
}>(), {
  variant: 'muted',
})
</script>

<template>
  <span class="josh-quiet" :class="`josh-quiet--${variant}`">
    <slot />
  </span>
</template>

<style scoped>
.josh-quiet {
  color: var(--josh-fg-soft);
  opacity: 0.45;
}

.josh-quiet--strike {
  text-decoration: line-through;
  text-decoration-color: color-mix(in oklab, var(--josh-fg-soft) 60%, transparent);
}
</style>
