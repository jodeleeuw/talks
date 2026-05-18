<script setup lang="ts">
withDefaults(defineProps<{
  image: string
  alt?: string
  caption?: string
  fit?: 'contain' | 'cover'
  bleed?: boolean
}>(), {
  alt: '',
  fit: 'contain',
  bleed: false,
})
</script>

<template>
  <div class="slidev-layout josh-image" :class="{ bleed }">
    <div class="image-wrap" :style="{ '--fit': fit }">
      <img :src="image" :alt="alt" />
    </div>
    <div v-if="caption" class="image-caption">{{ caption }}</div>
  </div>
</template>

<style scoped>
.josh-image {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 3rem 4rem 3.5rem;
  height: 100%;
  overflow: hidden;
  gap: 1.2rem;
}

.josh-image.bleed {
  padding: 0;
  gap: 0;
}

.image-wrap {
  flex: 1 1 0;
  min-height: 0;
  width: 100%;
  position: relative;
}

.image-wrap img {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  object-fit: var(--fit, contain);
  border-radius: 6px;
}

.josh-image.bleed .image-wrap img {
  border-radius: 0;
}

.image-caption {
  flex: 0 0 auto;
  font-family: 'JetBrains Mono', ui-monospace, monospace;
  font-size: 0.75rem;
  color: var(--josh-muted);
  letter-spacing: 0.02em;
  text-align: center;
  max-width: 60ch;
}
</style>
