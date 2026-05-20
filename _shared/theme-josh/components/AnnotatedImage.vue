<script setup lang="ts">
import { provide, computed } from 'vue'

const props = withDefaults(defineProps<{
  src?: string
  // Source-pixel coordinate system [w, h] — every child's `:at` tuple lives in
  // this space. Defaults to the standard 960×540 deck size.
  viewbox?: [number, number]
  // How the base image fills the wrapper.
  fit?: 'cover' | 'contain'
  // 'aspect' (default): self-size from the viewbox aspect ratio. Fits the
  // available parent space like an <img object-fit:contain> — neither
  // dimension overflows.
  // 'container': fill the parent (which must already be sized).
  layout?: 'aspect' | 'container'
  // Optional explicit size constraints. Accepts CSS lengths (`'400px'`,
  // `'60vh'`, `'36rem'`) or plain numbers (treated as px). Use these to
  // cap the image when the default fit-to-parent behavior is too greedy,
  // e.g. inside a `default` layout where the parent has no defined height.
  width?: string | number
  maxWidth?: string | number
  maxHeight?: string | number
}>(), {
  viewbox: () => [960, 540] as [number, number],
  fit: 'cover',
  layout: 'aspect',
})

// Provide the viewbox as a reactive getter so child components (Box, Label,
// Layer, Mask) can compute their percent-based positions.
provide('annotated-viewbox', computed(() => ({
  w: props.viewbox[0],
  h: props.viewbox[1],
})))

const toLen = (v: string | number | undefined): string | undefined =>
  v == null ? undefined : typeof v === 'number' ? `${v}px` : v

const wrapStyle = computed(() => {
  const s: Record<string, string> = {}
  if (props.layout !== 'container') {
    s.aspectRatio = `${props.viewbox[0]} / ${props.viewbox[1]}`
  }
  const w = toLen(props.width)
  const mw = toLen(props.maxWidth)
  const mh = toLen(props.maxHeight)
  if (w) s.width = w
  if (mw) s.maxWidth = mw
  if (mh) s.maxHeight = mh
  return s
})
</script>

<template>
  <div class="annotated-image" :class="`layout-${layout}`" :style="wrapStyle">
    <img v-if="src" :src="src" class="annotated-base" :style="{ objectFit: fit }" />
    <slot />
  </div>
</template>

<style scoped>
/* Default sizing: behave like an <img> with object-fit:contain — fill the
   parent on whichever axis is more constraining, never overflow.
   - `width: 100%` gives the cross-axis a definite value (cross-axis stretch
     resolves after flex-basis, which is too late for aspect-ratio transfer,
     so we set it explicitly).
   - `aspect-ratio` (inline) derives the missing dimension.
   - `max-height: 100%` caps the height in flex columns; modern browsers
     recompute width from aspect-ratio when this clamps.
   - `min-*: 0` lets the element shrink below content-derived intrinsic size
     in flex layouts. */
.annotated-image {
  position: relative;
  margin: 0 auto;
  overflow: hidden;
  display: block;
  width: 100%;
  max-width: 100%;
  max-height: 100%;
  min-width: 0;
  min-height: 0;
}

.annotated-image.layout-container {
  width: 100%;
  height: 100%;
  max-width: none;
  max-height: none;
}

.annotated-base {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  display: block;
}
</style>
