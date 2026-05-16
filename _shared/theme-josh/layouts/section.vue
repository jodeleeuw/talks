<script setup lang="ts">
defineProps<{ number?: string | number }>()
</script>

<template>
  <div class="slidev-layout josh-section">
    <div v-if="number !== undefined" class="section-number">
      §{{ number }}
    </div>
    <div class="section-body">
      <slot />
    </div>
  </div>
</template>

<style scoped>
.josh-section {
  display: flex;
  flex-direction: column;
  justify-content: center;
  padding: 4rem 5rem;
}

.section-number {
  font-family: 'JetBrains Mono', ui-monospace, monospace;
  font-size: 1rem;
  color: var(--josh-accent);
  letter-spacing: 0.05em;
  margin-bottom: 1.2rem;
}

.section-body :slotted(h1) {
  font-size: 4rem !important;
  font-weight: 500;
  line-height: 1.05;
  letter-spacing: -0.025em;
  max-width: 18ch;
  margin: 0;
}

.section-body :slotted(p) {
  font-size: 1.4rem;
  color: var(--josh-fg-soft);
  max-width: 32ch;
  margin-top: 1.5rem;
}
</style>
