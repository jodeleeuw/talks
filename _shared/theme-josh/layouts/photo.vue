<script setup lang="ts">
import FitContent from '../components/FitContent.vue'

withDefaults(defineProps<{
  image: string
  alt?: string
  side?: 'left' | 'right'
  fit?: 'cover' | 'contain'
  bleed?: boolean
  caption?: string
}>(), {
  side: 'right',
  fit: 'cover',
  bleed: false,
  alt: '',
})
</script>

<template>
  <div
    class="slidev-layout josh-photo"
    :class="[`side-${side}`, bleed ? 'bleed' : 'padded']"
  >
    <div class="photo-text">
      <FitContent align="center" origin="left center">
        <div class="text-inner">
          <slot />
        </div>
      </FitContent>
    </div>

    <div class="photo-media" :style="{ '--fit': fit }">
      <img :src="image" :alt="alt" />
      <div v-if="caption" class="photo-caption">{{ caption }}</div>
    </div>
  </div>
</template>

<style scoped>
.josh-photo {
  display: grid;
  grid-template-columns: 1fr 1.15fr;
  gap: 3rem;
  height: 100%;
  overflow: hidden;
}

.josh-photo.padded {
  padding: 3rem 4rem 3.5rem;
}

.josh-photo.bleed {
  padding: 3rem 0 3.5rem 4rem;
  gap: 3.5rem;
}

.josh-photo.side-left {
  grid-template-columns: 1.15fr 1fr;
}
.josh-photo.side-left .photo-text { order: 2; }
.josh-photo.side-left .photo-media { order: 1; }
.josh-photo.side-left.bleed {
  padding: 3rem 4rem 3.5rem 0;
}

.photo-text {
  min-height: 0;
  min-width: 0;
}

.text-inner :deep(h1) {
  font-size: 3.2rem;
  font-weight: 500;
  line-height: 1.12;
  letter-spacing: -0.02em;
  color: var(--josh-fg);
  margin: 0 0 1.5rem;
  max-width: 18ch;
}

.text-inner :deep(h1 em),
.text-inner :deep(h1 strong) {
  color: var(--josh-accent);
}

.text-inner :deep(p) {
  font-size: 1.3rem;
  line-height: 1.5;
  color: var(--josh-fg-soft);
  margin: 0 0 0.9rem;
  max-width: 34ch;
}

.text-inner :deep(p:last-child) {
  margin-bottom: 0;
}

.text-inner :deep(em) {
  color: var(--josh-fg);
  font-style: italic;
}

.text-inner :deep(strong) {
  color: var(--josh-accent);
  font-weight: 600;
}

.photo-media {
  position: relative;
  min-height: 0;
  min-width: 0;
  display: flex;
  flex-direction: column;
  justify-content: center;
}

.photo-media img {
  width: 100%;
  height: 100%;
  object-fit: var(--fit, cover);
  border-radius: 6px;
}

.josh-photo.bleed .photo-media img {
  border-radius: 0;
}

.photo-caption {
  position: absolute;
  bottom: -1.6rem;
  right: 0;
  font-family: 'JetBrains Mono', ui-monospace, monospace;
  font-size: 0.7rem;
  color: var(--josh-muted);
  letter-spacing: 0.02em;
}
</style>
