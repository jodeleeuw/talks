<script setup lang="ts">
import { inject, computed, type ComputedRef } from 'vue'

const props = withDefaults(defineProps<{
  src: string
  // [x, y, w, h] in the parent <AnnotatedImage>'s viewbox space. Omit for a
  // full-bleed layer that fills the wrapper.
  at?: [number, number, number, number]
  revealAt?: number
  reveal?: { from?: number; to?: number; until?: number }
  hideAt?: number
  fit?: 'cover' | 'contain'
}>(), {
  fit: 'cover',
})

const viewbox = inject<ComputedRef<{ w: number; h: number }> | null>(
  'annotated-viewbox',
  null,
)
if (!viewbox) {
  throw new Error('<Layer> must be nested inside <AnnotatedImage>')
}

const layerStyle = computed(() => {
  const { w: vw, h: vh } = viewbox.value
  if (props.at) {
    const [x, y, w, h] = props.at
    return {
      left: `${(x / vw) * 100}%`,
      top: `${(y / vh) * 100}%`,
      width: `${(w / vw) * 100}%`,
      height: `${(h / vh) * 100}%`,
      objectFit: props.fit,
    }
  }
  return {
    inset: '0',
    width: '100%',
    height: '100%',
    objectFit: props.fit,
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
  <img
    v-if="isHideMode"
    v-click-hide="hideAt"
    :src="src"
    class="annotated-layer"
    :style="layerStyle"
  />
  <img
    v-else
    v-click="clickValue"
    :src="src"
    class="annotated-layer"
    :style="layerStyle"
  />
</template>

<style scoped>
.annotated-layer {
  position: absolute;
  display: block;
}
</style>
