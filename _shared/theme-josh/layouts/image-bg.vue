<script setup lang="ts">
import { computed } from 'vue'

const props = withDefaults(defineProps<{
  image: string
  alt?: string
  align?: 'left' | 'center'
  darken?: number
  position?: 'top' | 'center' | 'bottom'
  tint?: string
}>(), {
  alt: '',
  align: 'center',
  darken: 0.6,
  position: 'center',
})

// Clamp opacity into a sane range so authors who pass 0 or 1 don't get
// surprising results (e.g. fully opaque scrim hides the image entirely).
const clamped = computed(() => Math.max(0, Math.min(1, props.darken)))

// The scrim is a vertical linear-gradient over a tint color. Top/bottom
// fades are slightly weaker than the middle, so text always sits on the
// darkest part of the image.
const scrimStyle = computed(() => {
  const tint = props.tint ?? 'var(--josh-bg)'
  const mid = clamped.value
  const edge = Math.max(0, mid - 0.15)
  const toRgba = (color: string, a: number) =>
    `color-mix(in oklab, ${color} ${Math.round(a * 100)}%, transparent)`
  return {
    background: `linear-gradient(180deg, ${toRgba(tint, edge)} 0%, ${toRgba(tint, mid)} 50%, ${toRgba(tint, edge)} 100%)`,
  }
})
</script>

<template>
  <div class="slidev-layout josh-image-bg" :class="[`align-${align}`, `pos-${position}`]">
    <img class="bg-img" :src="image" :alt="alt" />
    <div class="bg-scrim" :style="scrimStyle" aria-hidden="true" />

    <div class="bg-content">
      <div class="content-inner">
        <slot />
      </div>
    </div>
  </div>
</template>

<style scoped>
.josh-image-bg {
  position: relative;
  padding: 0;
  height: 100%;
  overflow: hidden;
  display: block;
}

.bg-img {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  object-fit: cover;
  z-index: 0;
}

.bg-scrim {
  position: absolute;
  inset: 0;
  z-index: 1;
  pointer-events: none;
}

.bg-content {
  position: relative;
  z-index: 2;
  height: 100%;
  display: flex;
  flex-direction: column;
  padding: 3rem 4rem 4rem;
}

.josh-image-bg.pos-top    .bg-content { justify-content: flex-start; }
.josh-image-bg.pos-center .bg-content { justify-content: center; }
.josh-image-bg.pos-bottom .bg-content { justify-content: flex-end; }

.josh-image-bg.align-center .bg-content { align-items: center; text-align: center; }
.josh-image-bg.align-left   .bg-content { align-items: flex-start; text-align: left; }

.content-inner {
  max-width: 32ch;
}

.josh-image-bg.align-left .content-inner {
  max-width: 36ch;
}

.content-inner :deep(h1) {
  color: var(--josh-fg);
  font-size: 3rem;
  font-weight: 500;
  line-height: 1.1;
  letter-spacing: -0.02em;
  margin: 0 0 1rem;
  max-width: 22ch;
  text-shadow: 0 2px 24px rgba(0, 0, 0, 0.45);
}

.content-inner :deep(h1 em),
.content-inner :deep(h1 strong) {
  color: var(--josh-accent);
}

.content-inner :deep(p) {
  color: var(--josh-fg-soft);
  font-size: 1.3rem;
  line-height: 1.5;
  margin: 0 0 0.8rem;
  max-width: 32ch;
  text-shadow: 0 2px 18px rgba(0, 0, 0, 0.45);
}

.content-inner :deep(p:last-child) {
  margin-bottom: 0;
}

.josh-image-bg.align-center .content-inner :deep(p),
.josh-image-bg.align-center .content-inner :deep(h1) {
  margin-left: auto;
  margin-right: auto;
}
</style>
