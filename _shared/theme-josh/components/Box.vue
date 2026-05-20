<script setup lang="ts">
import { inject, computed, type ComputedRef } from 'vue'

const props = defineProps<{
  // [x, y, w, h] in the parent <AnnotatedImage>'s source-pixel viewbox.
  at: [number, number, number, number]
  revealAt?: number
  reveal?: { from?: number; to?: number; until?: number }
  hideAt?: number
  variant?: string
}>()

const viewbox = inject<ComputedRef<{ w: number; h: number }> | null>(
  'annotated-viewbox',
  null,
)
if (!viewbox) {
  throw new Error('<Box> must be nested inside <AnnotatedImage>')
}

const boxStyle = computed(() => {
  const [x, y, w, h] = props.at
  const { w: vw, h: vh } = viewbox.value
  return {
    left: `${(x / vw) * 100}%`,
    top: `${(y / vh) * 100}%`,
    width: `${(w / vw) * 100}%`,
    height: `${(h / vh) * 100}%`,
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
    class="annotated-box"
    :class="variant ? `annotated-box-${variant}` : null"
    :style="boxStyle"
  />
  <div
    v-else
    v-click="clickValue"
    class="annotated-box"
    :class="variant ? `annotated-box-${variant}` : null"
    :style="boxStyle"
  />
</template>

<style scoped>
.annotated-box {
  position: absolute;
  box-sizing: border-box;
  border: 2px solid var(--josh-accent);
  border-radius: 4px;
  pointer-events: none;
}
</style>
