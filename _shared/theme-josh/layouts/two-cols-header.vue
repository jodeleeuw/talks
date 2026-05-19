<script setup lang="ts">
import { useSlots } from 'vue'

withDefaults(defineProps<{
  // Column width ratio. 'equal' (default) is a clean 1:1 split for symmetric
  // compare/contrast slides. 'left-wide' / 'right-wide' bias 60/40 when one
  // column carries the argument and the other a supporting figure or list.
  cols?: 'equal' | 'left-wide' | 'right-wide'
  gap?: string
}>(), {
  cols: 'equal',
  gap: '3rem',
})

const slots = useSlots()
</script>

<template>
  <div
    class="slidev-layout josh-tch"
    :class="`cols-${cols}`"
    :style="{ '--tch-gap': gap }"
  >
    <header class="tch-header">
      <slot />
    </header>

    <div class="tch-grid">
      <div v-if="slots.left" class="tch-col tch-left">
        <slot name="left" />
      </div>
      <div v-if="slots.right" class="tch-col tch-right">
        <slot name="right" />
      </div>
    </div>
  </div>
</template>

<style scoped>
/* Top-anchored like `panel`: header sits at the top, the two-column grid
   takes the remaining height. Override the .slidev-layout base's
   justify-content: center so the header stays flush to the top edge. */
.josh-tch {
  justify-content: flex-start;
  padding: 3rem 4rem 3.5rem;
  height: 100%;
  overflow: hidden;
  gap: 1.5rem;
}

.tch-header :deep(h1) {
  font-size: 2.6rem;
  font-weight: 500;
  line-height: 1.15;
  letter-spacing: -0.02em;
  color: var(--josh-fg);
  margin: 0;
  max-width: 28ch;
}

.tch-header :deep(h1 em) {
  font-style: italic;
  color: var(--josh-accent);
  font-weight: 500;
}

.tch-grid {
  flex: 1 1 0;
  min-height: 0;
  display: grid;
  gap: var(--tch-gap, 3rem);
  align-items: start;
}

.josh-tch.cols-equal      .tch-grid { grid-template-columns: 1fr 1fr; }
.josh-tch.cols-left-wide  .tch-grid { grid-template-columns: 1.5fr 1fr; }
.josh-tch.cols-right-wide .tch-grid { grid-template-columns: 1fr 1.5fr; }

.tch-col {
  min-width: 0;
  min-height: 0;
}

/* Column body typography mirrors `default`'s body so authors can write the
   same markdown they'd put in a default slide. Each column is its own
   reading column. */
.tch-col :deep(h2) {
  font-family: 'JetBrains Mono', ui-monospace, monospace;
  font-size: 0.8rem;
  text-transform: uppercase;
  letter-spacing: 0.12em;
  color: var(--josh-accent);
  margin: 0 0 1rem;
  font-weight: 500;
}

.tch-col :deep(p) {
  font-size: 1.25rem;
  line-height: 1.5;
  color: var(--josh-fg);
  margin: 0 0 0.9rem;
}

.tch-col :deep(p:last-child) {
  margin-bottom: 0;
}

.tch-col :deep(em) {
  color: var(--josh-fg);
  font-style: italic;
}

.tch-col :deep(strong) {
  color: var(--josh-accent);
  font-weight: 600;
}

/* Re-assert list markers (UnoCSS preflight strips them — same fix as the
   default/panel/center layouts). */
.tch-col :deep(ol) {
  list-style: decimal;
  padding-left: 1.4rem;
}

.tch-col :deep(ul) {
  list-style: disc;
  padding-left: 1.4rem;
}

.tch-col :deep(ol li),
.tch-col :deep(ul li) {
  margin: 0.5rem 0;
  font-size: 1.2rem;
  line-height: 1.5;
  color: var(--josh-fg);
}

.tch-col :deep(ol li::marker),
.tch-col :deep(ul li::marker) {
  color: var(--josh-fg-soft);
}
</style>
