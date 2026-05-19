<script setup lang="ts">
import { inject, computed, type ComputedRef } from 'vue'

const props = defineProps<{
  // [x, y, w, h] in the parent <AnnotatedImage>'s viewbox space.
  at: [number, number, number, number]
  revealAt?: number
  reveal?: { from?: number; to?: number; until?: number }
  // Most common control for masks: shown by default, vanishes on click N to
  // reveal what's underneath.
  hideAt?: number
  // 'solid' (default): opaque slide-bg fill (looks like the slide eating a hole
  // in the image). 'dim': translucent darken — content stays faintly visible.
  // 'blur': frosted glass — shape readable, detail not.
  variant?: string
  // Override the base color used by every variant. Accepts any CSS color
  // ('#222', 'rgb(...)', 'oklch(...)', or a CSS var like 'var(--josh-accent)').
  // Composes with `variant`: 'dim' becomes 70% of this color, 'blur' 25% + blur.
  // Defaults to `var(--josh-bg)`.
  color?: string
}>()

const viewbox = inject<ComputedRef<{ w: number; h: number }> | null>(
  'annotated-viewbox',
  null,
)
if (!viewbox) {
  throw new Error('<Mask> must be nested inside <AnnotatedImage>')
}

const maskStyle = computed(() => {
  const [x, y, w, h] = props.at
  const { w: vw, h: vh } = viewbox.value
  const s: Record<string, string> = {
    left: `${(x / vw) * 100}%`,
    top: `${(y / vh) * 100}%`,
    width: `${(w / vw) * 100}%`,
    height: `${(h / vh) * 100}%`,
  }
  if (props.color) s['--mask-color'] = props.color
  return s
})

const clickValue = computed(() => {
  if (props.reveal?.from != null) {
    if (props.reveal.until != null) return [props.reveal.from, props.reveal.until]
    if (props.reveal.to != null) return [props.reveal.from, props.reveal.to + 1]
    return props.reveal.from
  }
  if (props.revealAt != null) return props.revealAt
  return false
})

const isHideMode = computed(() => props.hideAt != null)
</script>

<template>
  <div
    v-if="isHideMode"
    v-click-hide="hideAt"
    class="annotated-mask"
    :class="variant ? `annotated-mask-${variant}` : null"
    :style="maskStyle"
  />
  <div
    v-else
    v-click="clickValue"
    class="annotated-mask"
    :class="variant ? `annotated-mask-${variant}` : null"
    :style="maskStyle"
  />
</template>

<style scoped>
.annotated-mask {
  position: absolute;
  background: var(--mask-color, var(--josh-bg));
  pointer-events: none;
}

.annotated-mask.annotated-mask-dim {
  background: color-mix(in oklab, var(--mask-color, var(--josh-bg)) 70%, transparent);
}

.annotated-mask.annotated-mask-blur {
  background: color-mix(in oklab, var(--mask-color, var(--josh-bg)) 25%, transparent);
  backdrop-filter: blur(14px);
  -webkit-backdrop-filter: blur(14px);
}
</style>
