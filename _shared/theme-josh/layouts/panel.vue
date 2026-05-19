<script setup lang="ts">
withDefaults(defineProps<{
  align?: 'left' | 'center'
  gap?: string
}>(), {
  align: 'left',
  gap: '1.5rem',
})
</script>

<template>
  <div
    class="slidev-layout josh-panel"
    :class="`align-${align}`"
    :style="{ '--panel-gap': gap }"
  >
    <slot />
  </div>
</template>

<style scoped>
/* Top-anchored layout: title sits at the top, content region fills the rest.
   Overrides the .slidev-layout base's `justify-content: center` so the first
   child (h1) does not get vertically centered off the top of the viewport. */
.josh-panel {
  justify-content: flex-start;
  gap: var(--panel-gap, 1.5rem);
  overflow: hidden;
}

.josh-panel.align-center {
  align-items: center;
  text-align: center;
}

/* The h1 is the implicit first child — keep it flush to the top by zeroing
   its top margin. Otherwise it inherits the global heading margin and feels
   detached from the slide top edge. */
.josh-panel :deep(h1) {
  font-size: 3.2rem;
  font-weight: 600;
  line-height: 1.1;
  letter-spacing: -0.02em;
  color: var(--josh-fg);
  margin: 0 0 0;
  flex: 0 0 auto;
}

.josh-panel.align-center :deep(h1) {
  margin-left: auto;
  margin-right: auto;
}

/* Everything after the h1 becomes the "body" — give it room to grow but
   never push past the slide. Children (DataTable, Diagram, charts, etc.)
   manage their own internal layout. */
.josh-panel :deep(> *:not(h1)) {
  flex: 0 1 auto;
  min-height: 0;
}

/* The last body element gets the remaining height — useful when authors
   put a single large element (table, diagram) under the title. */
.josh-panel :deep(> *:last-child:not(h1)) {
  flex: 1 1 0;
  min-height: 0;
}

/* Same ol/ul fix as `default` — UnoCSS preflight strips list markers, so
   re-assert them here too. */
.josh-panel :deep(ol) {
  list-style: decimal;
  padding-left: 1.5rem;
}

.josh-panel :deep(ul) {
  list-style: disc;
  padding-left: 1.5rem;
}

.josh-panel :deep(ol li),
.josh-panel :deep(ul li) {
  margin: 0.6rem 0;
  line-height: 1.5;
  font-size: 1.35rem;
  color: var(--josh-fg);
}

.josh-panel :deep(ol li::marker),
.josh-panel :deep(ul li::marker) {
  color: var(--josh-fg-soft);
}
</style>
