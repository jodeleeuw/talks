<script setup lang="ts">
import FitContent from '../components/FitContent.vue'

defineProps<{ number?: string | number }>()
</script>

<template>
  <div class="slidev-layout josh-section">
    <div v-if="number !== undefined" class="section-number">
      §{{ number }}
    </div>
    <div class="section-body">
      <FitContent align="center" origin="center">
        <div class="section-inner">
          <slot />
        </div>
      </FitContent>
    </div>
  </div>
</template>

<style scoped>
.josh-section {
  display: flex;
  flex-direction: column;
  padding: 4rem 5rem;
  height: 100%;
}

.section-number {
  flex: 0 0 auto;
  font-family: 'JetBrains Mono', ui-monospace, monospace;
  font-size: 1rem;
  color: var(--josh-accent);
  letter-spacing: 0.05em;
  margin-bottom: 1.2rem;
}

.section-body {
  flex: 1 1 0;
  min-height: 0;
  overflow: hidden;
}

.section-body :deep(h1) {
  font-size: 4rem !important;
  font-weight: 500;
  line-height: 1.05;
  letter-spacing: -0.025em;
  max-width: 18ch;
  margin: 0;
}

.section-body :deep(p) {
  font-size: 1.4rem;
  color: var(--josh-fg-soft);
  max-width: 32ch;
  margin-top: 1.5rem;
}
</style>
