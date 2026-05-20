<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{
  src: string
  // PPTX edge insets as percentages (0-100). `l`/`t` are top-left insets,
  // `r`/`b` are bottom-right. Paste straight from the analysis's
  // `✂ crop l=…% t=…% r=…% b=…%` tag.
  crop?: { l?: number; t?: number; r?: number; b?: number }
  // Optional aspect lock for the wrapper. Pass the picture's bbox as [w, h]
  // (also from the analysis) to size the frame. Omit when the wrapper is
  // already constrained by its parent (e.g. inside a gallery cell or a flex
  // column with a fixed height).
  aspect?: [number, number]
  alt?: string
}>()

const wrapStyle = computed(() => {
  if (!props.aspect) return null
  return { aspectRatio: `${props.aspect[0]} / ${props.aspect[1]}` }
})

const imgStyle = computed(() => {
  const l = props.crop?.l ?? 0
  const t = props.crop?.t ?? 0
  const r = props.crop?.r ?? 0
  const b = props.crop?.b ?? 0
  const visibleW = 100 - l - r
  const visibleH = 100 - t - b
  if (visibleW <= 0 || visibleH <= 0) {
    return { width: '100%', height: '100%' }
  }
  return {
    width: `${(10000 / visibleW).toFixed(2)}%`,
    height: `${(10000 / visibleH).toFixed(2)}%`,
    left: `${(-100 * l / visibleW).toFixed(2)}%`,
    top: `${(-100 * t / visibleH).toFixed(2)}%`,
  }
})
</script>

<template>
  <div class="josh-cropped" :style="wrapStyle">
    <img :src="src" :alt="alt" :style="imgStyle" />
  </div>
</template>

<style scoped>
.josh-cropped {
  position: relative;
  overflow: hidden;
  width: 100%;
  height: 100%;
  min-height: 0;
  flex: 1 1 0;
  /* Inherit gallery cell radius when nested; otherwise leave corners sharp. */
  border-radius: var(--josh-gallery-radius, 0);
}

.josh-cropped img {
  position: absolute;
  display: block;
  max-width: none;
  /* Width/height come from inline style (computed from the crop insets) so
     these defaults don't override the visible-region scaling. */
}
</style>
