<script setup lang="ts">
import FitContent from '../components/FitContent.vue'
</script>

<template>
  <div class="slidev-layout josh-center">
    <FitContent align="center" origin="center">
      <div class="center-body">
        <slot />
      </div>
    </FitContent>
  </div>
</template>

<style scoped>
.josh-center {
  padding: 4rem 5rem;
  text-align: center;
  height: 100%;
  overflow: hidden;
}

.center-body {
  max-width: 28ch;
  margin: 0 auto;
}

.center-body :deep(h1) {
  font-size: 3.5rem !important;
  font-weight: 500;
  line-height: 1.15;
  letter-spacing: -0.02em;
}

.center-body :deep(h2) {
  font-size: 2rem !important;
  color: var(--josh-fg-soft);
  font-weight: 400;
}

.center-body :deep(p) {
  font-size: 1.6rem;
  line-height: 1.5;
}
</style>
