<script setup lang="ts">
import { inject, computed, type ComputedRef } from 'vue'

const props = defineProps<{
  // [x, y] point — width auto, top-left anchor — or [x, y, w, h] for a sized
  // bounding box that wraps content. Coordinates are in the parent
  // <AnnotatedImage>'s viewbox space.
  at: [number, number] | [number, number, number, number]
  revealAt?: number
  reveal?: { from?: number; to?: number; until?: number }
  hideAt?: number
  variant?: string
  align?: 'left' | 'center' | 'right'
}>()

const viewbox = inject<ComputedRef<{ w: number; h: number }> | null>(
  'annotated-viewbox',
  null,
)
if (!viewbox) {
  throw new Error('<Label> must be nested inside <AnnotatedImage>')
}

const labelStyle = computed(() => {
  const { w: vw, h: vh } = viewbox.value
  const at = props.at
  if (at.length === 4) {
    const [x, y, w, h] = at
    return {
      left: `${(x / vw) * 100}%`,
      top: `${(y / vh) * 100}%`,
      width: `${(w / vw) * 100}%`,
      height: `${(h / vh) * 100}%`,
    }
  }
  const [x, y] = at
  return {
    left: `${(x / vw) * 100}%`,
    top: `${(y / vh) * 100}%`,
  }
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
    class="annotated-label"
    :class="[variant ? `annotated-label-${variant}` : null, align ? `align-${align}` : null]"
    :style="labelStyle"
  >
    <slot />
  </div>
  <div
    v-else
    v-click="clickValue"
    class="annotated-label"
    :class="[variant ? `annotated-label-${variant}` : null, align ? `align-${align}` : null]"
    :style="labelStyle"
  >
    <slot />
  </div>
</template>

<style scoped>
.annotated-label {
  position: absolute;
  color: var(--josh-fg);
  font-size: 1rem;
  line-height: 1.3;
  font-family: inherit;
}
.annotated-label.align-center { text-align: center; }
.annotated-label.align-right { text-align: right; }
</style>
