<script setup lang="ts">
import FitContent from '../components/FitContent.vue'

withDefaults(defineProps<{
  source?: string
  // Where the big number sits horizontally. Default 'center' for the classic
  // impact-stat look; 'left' for a more editorial / data-journalism feel where
  // the caption flows beside the number on a wide slide.
  align?: 'left' | 'center'
}>(), {
  align: 'center',
})
</script>

<template>
  <div class="slidev-layout josh-fact" :class="`align-${align}`">
    <div class="fact-body">
      <FitContent align="center" :origin="align === 'left' ? 'left center' : 'center center'">
        <div class="fact-inner">
          <slot />
        </div>
      </FitContent>
    </div>

    <div v-if="source" class="fact-source">{{ source }}</div>
  </div>
</template>

<style scoped>
.josh-fact {
  display: flex;
  flex-direction: column;
  padding: 3rem 5rem 3.5rem;
  height: 100%;
  overflow: hidden;
}

.fact-body {
  flex: 1 1 0;
  min-height: 0;
  display: flex;
  align-items: center;
}

.josh-fact.align-center .fact-inner { text-align: center; margin: 0 auto; max-width: 26ch; }
.josh-fact.align-left   .fact-inner { text-align: left;   max-width: 32ch; }

/* The h1 is the headline number (or short phrase). Fraunces italic at a
   poster scale — distinct from default's sans h1 so the "fact" reads as a
   featured impact moment, not a body slide title. */
.fact-inner :deep(h1) {
  font-family: 'Fraunces', 'Source Serif Pro', Georgia, serif !important;
  font-size: 9rem !important;
  font-style: italic;
  font-weight: 500;
  line-height: 0.95;
  letter-spacing: -0.04em;
  font-variation-settings: 'opsz' 144, 'SOFT' 30;
  color: var(--josh-accent);
  margin: 0 0 1.2rem;
}

/* Anything after the number — h2 or p — is the explanatory caption. Keep
   it readable but small enough that the number stays the visual anchor. */
.fact-inner :deep(h2),
.fact-inner :deep(p) {
  font-size: 1.5rem !important;
  font-weight: 400;
  line-height: 1.4;
  color: var(--josh-fg-soft);
  margin: 0 0 0.7rem;
}

.fact-inner :deep(h2:last-child),
.fact-inner :deep(p:last-child) {
  margin-bottom: 0;
}

.fact-inner :deep(em),
.fact-inner :deep(strong) {
  color: var(--josh-fg);
}

/* Citation rail above the footer — same vibe as media's .media-caption but
   anchored to the slide bottom-right rather than under a figure. */
.fact-source {
  flex: 0 0 auto;
  align-self: flex-end;
  font-family: 'JetBrains Mono', ui-monospace, monospace;
  font-size: 0.72rem;
  color: var(--josh-muted);
  letter-spacing: 0.02em;
  margin-top: 1rem;
  max-width: 50ch;
  text-align: right;
}
</style>
