<script setup lang="ts">
import { useSlots } from 'vue'
import FitContent from '../components/FitContent.vue'

const slots = useSlots()
</script>

<template>
  <div class="slidev-layout josh-quote">
    <div class="bigmark" aria-hidden="true">&ldquo;</div>

    <div class="quote-stack">
      <div class="quote-body">
        <FitContent align="center" origin="left center">
          <div class="quote-inner">
            <slot />
          </div>
        </FitContent>
      </div>

      <div v-if="slots.attribution" class="attribution">
        <span class="dash" aria-hidden="true">—</span>
        <div class="attribution-text">
          <slot name="attribution" />
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.josh-quote {
  display: flex;
  flex-direction: column;
  justify-content: center;
  padding: 4rem 6rem 4.5rem;
  height: 100%;
  position: relative;
  overflow: hidden;
}

.bigmark {
  position: absolute;
  top: -3rem;
  left: -1.5rem;
  font-family: 'Fraunces', 'Source Serif Pro', Georgia, serif;
  font-size: 28rem;
  line-height: 1;
  font-weight: 500;
  font-style: italic;
  font-variation-settings: 'opsz' 144, 'SOFT' 30;
  color: transparent;
  -webkit-text-stroke: 2px var(--josh-accent);
  opacity: 0.35;
  pointer-events: none;
  user-select: none;
  z-index: 0;
}

.quote-stack {
  position: relative;
  z-index: 1;
  display: flex;
  flex-direction: column;
  gap: 1.8rem;
  min-height: 0;
  max-width: 78ch;
  flex: 1 1 0;
  justify-content: center;
}

.quote-body {
  flex: 0 1 auto;
  min-height: 0;
  overflow: hidden;
}

.quote-inner :deep(p) {
  font-size: 1.5rem;
  line-height: 1.55;
  color: var(--josh-fg);
  margin: 0 0 0.9rem;
}

.quote-inner :deep(p:last-child) {
  margin-bottom: 0;
}

.quote-inner :deep(em) {
  color: var(--josh-fg);
  font-style: italic;
}

.quote-inner :deep(strong) {
  color: var(--josh-fg);
  font-weight: 600;
}

.attribution {
  flex: 0 0 auto;
  display: flex;
  align-items: baseline;
  gap: 0.6rem;
  font-family: 'JetBrains Mono', ui-monospace, monospace;
  font-size: 0.8rem;
  letter-spacing: 0.02em;
  color: var(--josh-muted);
}

.attribution .dash {
  color: var(--josh-accent);
  font-weight: 500;
}

.attribution-text :deep(*) {
  display: inline;
  margin: 0;
}

.attribution-text :deep(em) {
  color: var(--josh-fg-soft);
  font-style: italic;
}
</style>
