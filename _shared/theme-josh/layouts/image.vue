<script setup lang="ts">
withDefaults(defineProps<{
  image: string
  alt?: string
  caption?: string
  captionPosition?: 'bottom' | 'top'
  fit?: 'contain' | 'cover'
  bleed?: boolean
}>(), {
  alt: '',
  captionPosition: 'bottom',
  fit: 'contain',
  bleed: false,
})
</script>

<template>
  <div class="slidev-layout josh-image" :class="[{ bleed }, `caption-${captionPosition}`]">
    <div v-if="caption && captionPosition === 'top'" class="image-caption">{{ caption }}</div>
    <div class="image-wrap" :style="{ '--fit': fit }">
      <img :src="image" :alt="alt" />
    </div>
    <div v-if="caption && captionPosition === 'bottom'" class="image-caption">{{ caption }}</div>
  </div>
</template>

<style scoped>
.josh-image {
  display: flex;
  flex-direction: column;
  align-items: stretch;
  justify-content: center;
  padding: 3rem 4rem 3.5rem;
  height: 100%;
  overflow: hidden;
  gap: 0.75rem;
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

/* Caption styling — matches the `media` layout's .media-caption vibe but
   sits in its own row (above or below the image) with a subtle scrim so
   it stays readable over any underlying image edge. */
.image-caption {
  flex: 0 0 auto;
  font-family: 'JetBrains Mono', ui-monospace, monospace;
  font-size: 0.72rem;
  color: var(--josh-muted);
  letter-spacing: 0.02em;
  text-align: center;
  padding: 0.5rem 1.5rem;
  background: color-mix(in oklab, var(--josh-bg) 70%, transparent);
  border-radius: 4px;
  max-width: 80ch;
  margin: 0 auto;
}

/* In bleed mode, sit the caption flush against the image edge with no
   horizontal margin — the scrim is what keeps it legible. */
.josh-image.bleed .image-caption {
  border-radius: 0;
  max-width: none;
  margin: 0;
}
</style>
