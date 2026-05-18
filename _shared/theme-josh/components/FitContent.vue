<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'

const props = withDefaults(defineProps<{
  origin?: string
  minScale?: number
  align?: 'top' | 'center' | 'bottom'
}>(), {
  minScale: 0.3,
  align: 'top',
})

// When the inner element is taller than the wrapper, the flex alignment puts
// part of it offscreen — so the scale pivot must match the alignment to keep
// content in view. Callers can override with the `origin` prop.
const computedOrigin = computed(() => {
  if (props.origin) return props.origin
  if (props.align === 'center') return 'center center'
  if (props.align === 'bottom') return 'bottom left'
  return 'top left'
})

const wrapper = ref<HTMLElement | null>(null)
const inner = ref<HTMLElement | null>(null)
const scale = ref(1)

let ro: ResizeObserver | null = null
let queued = false

function measure() {
  queued = false
  const w = wrapper.value
  const i = inner.value
  if (!w || !i) return

  // scrollWidth/scrollHeight reflect the element's *layout* dimensions,
  // ignoring the CSS transform we apply — so they give the natural,
  // unscaled extent of the slot content.
  const naturalW = i.scrollWidth
  const naturalH = i.scrollHeight
  const availW = w.clientWidth
  const availH = w.clientHeight

  if (naturalW <= 0 || naturalH <= 0 || availW <= 0 || availH <= 0) {
    return
  }

  const s = Math.min(1, availW / naturalW, availH / naturalH)
  scale.value = Math.max(props.minScale, s)
}

function schedule() {
  if (queued) return
  queued = true
  requestAnimationFrame(measure)
}

onMounted(() => {
  measure()
  ro = new ResizeObserver(schedule)
  if (wrapper.value) ro.observe(wrapper.value)
  if (inner.value) ro.observe(inner.value)
})

onBeforeUnmount(() => {
  ro?.disconnect()
  ro = null
})
</script>

<template>
  <div ref="wrapper" class="josh-fit" :class="`josh-fit--${align}`">
    <div
      ref="inner"
      class="josh-fit-inner"
      :style="{ transform: `scale(${scale})`, transformOrigin: computedOrigin }"
    >
      <slot />
    </div>
  </div>
</template>

<style scoped>
.josh-fit {
  width: 100%;
  height: 100%;
  overflow: hidden;
  display: flex;
}
.josh-fit--top    { align-items: flex-start; }
.josh-fit--center { align-items: center; }
.josh-fit--bottom { align-items: flex-end; }

.josh-fit-inner {
  width: 100%;
  display: block;
}
</style>
