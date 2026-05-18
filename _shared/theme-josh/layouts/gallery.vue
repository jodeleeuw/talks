<script setup lang="ts">
import { computed, useSlots } from 'vue'

const props = withDefaults(defineProps<{
  cols?: number
  fit?: 'cover' | 'contain'
  gap?: string
  radius?: string
  bleed?: boolean
}>(), {
  fit: 'cover',
  gap: '1rem',
  radius: '6px',
  bleed: false,
})

const SLOT_KEYS = ['a', 'b', 'c', 'd', 'e', 'f'] as const

const slots = useSlots()

const activeSlots = computed(() => SLOT_KEYS.filter((k) => !!slots[k]))

// Heuristic for the number of columns when `cols` is omitted:
// 1→1, 2→2, 3→3, 4→2 (2×2), 5→3 (3+2), 6→3 (3×2).
const COLS_FOR_COUNT: Record<number, number> = {
  1: 1, 2: 2, 3: 3, 4: 2, 5: 3, 6: 3,
}

const resolvedCols = computed(() => {
  if (props.cols && props.cols > 0) return props.cols
  return COLS_FOR_COUNT[activeSlots.value.length] ?? 3
})

const gridStyle = computed(() => ({
  gridTemplateColumns: `repeat(${resolvedCols.value}, 1fr)`,
  gap: props.gap,
  '--josh-gallery-radius': props.bleed ? '0px' : props.radius,
  '--josh-gallery-fit': props.fit,
}))
</script>

<template>
  <div class="slidev-layout josh-gallery" :class="{ bleed }">
    <div class="gallery-grid" :style="gridStyle">
      <div
        v-for="key in activeSlots"
        :key="key"
        class="gallery-cell"
      >
        <slot :name="key" />
      </div>
    </div>

    <div v-if="slots.overlay" class="gallery-overlay">
      <div class="overlay-card">
        <slot name="overlay" />
      </div>
    </div>
  </div>
</template>

<style scoped>
.josh-gallery {
  position: relative;
  padding: 3rem 4rem 3.5rem;
  height: 100%;
  overflow: hidden;
}

.josh-gallery.bleed {
  padding: 0;
}

.gallery-grid {
  display: grid;
  grid-auto-rows: 1fr;
  height: 100%;
  width: 100%;
}

.gallery-cell {
  min-width: 0;
  min-height: 0;
  display: flex;
  flex-direction: column;
}

/* The slot may be a bare <img> or a <figure><img/><figcaption/></figure>.
   We style both shapes so authors can pick either. */
.gallery-cell :deep(figure) {
  margin: 0;
  display: flex;
  flex-direction: column;
  flex: 1 1 0;
  min-height: 0;
  gap: 0.5rem;
}

.gallery-cell :deep(img) {
  width: 100%;
  flex: 1 1 0;
  min-height: 0;
  height: auto;
  object-fit: var(--josh-gallery-fit, cover);
  border-radius: var(--josh-gallery-radius, 6px);
  display: block;
}

/* For bare <img> children (no <figure> wrapper), Markdown wraps them in a <p>.
   Reset that <p> so the img can flex into its cell. */
.gallery-cell :deep(p) {
  margin: 0;
  display: flex;
  flex-direction: column;
  flex: 1 1 0;
  min-height: 0;
}

.gallery-cell :deep(p img) {
  flex: 1 1 0;
}

.gallery-cell :deep(figcaption),
.gallery-cell :deep(.caption) {
  flex: 0 0 auto;
  font-family: 'JetBrains Mono', ui-monospace, monospace;
  font-size: 0.72rem;
  color: var(--josh-muted);
  letter-spacing: 0.02em;
  line-height: 1.4;
  text-align: center;
}

.gallery-cell :deep(figcaption strong),
.gallery-cell :deep(.caption strong) {
  color: var(--josh-accent);
  font-weight: 600;
}

.gallery-overlay {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 3rem 4rem;
  pointer-events: none;
}

.overlay-card {
  pointer-events: auto;
  background: color-mix(in oklab, var(--josh-bg) 88%, transparent);
  border: 1px solid var(--josh-rule);
  border-radius: 8px;
  padding: 1.6rem 2.2rem;
  max-width: 36rem;
  box-shadow: 0 12px 40px rgba(0, 0, 0, 0.4);
  backdrop-filter: blur(6px);
}

.overlay-card :deep(p:first-child) { margin-top: 0; }
.overlay-card :deep(p:last-child) { margin-bottom: 0; }
</style>
