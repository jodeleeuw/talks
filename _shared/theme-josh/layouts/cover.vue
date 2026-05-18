<script setup lang="ts">
import { configs } from '@slidev/client'
import FitContent from '../components/FitContent.vue'

const tc = (configs.themeConfig ?? {}) as Record<string, string>
</script>

<template>
  <div class="slidev-layout josh-cover">
    <div class="cover-mark">
      <span class="sq" />
      <span class="initials">{{ tc.initials || 'jdl' }}</span>
    </div>

    <div class="cover-body">
      <FitContent align="center" origin="center">
        <div class="cover-inner">
          <slot />
        </div>
      </FitContent>
    </div>

    <div class="cover-meta">
      <div v-if="tc.course" class="meta-line">{{ tc.course }}</div>
      <div v-if="tc.event" class="meta-line">{{ tc.event }}</div>
      <div v-if="tc.date" class="meta-line meta-date">{{ tc.date }}</div>
    </div>
  </div>
</template>

<style scoped>
.josh-cover {
  display: grid;
  grid-template-rows: auto 1fr auto;
  background: var(--josh-bg);
  padding: 3rem 5rem;
}

.cover-mark {
  display: flex;
  align-items: center;
  gap: 0.6rem;
  font-family: 'JetBrains Mono', ui-monospace, monospace;
  font-size: 0.95rem;
  color: var(--josh-muted);
  letter-spacing: 0.04em;
}

.sq {
  display: inline-block;
  width: 0.8rem;
  height: 0.8rem;
  background: var(--josh-accent);
}

.cover-body {
  min-height: 0;
  overflow: hidden;
}

.cover-body :deep(h1) {
  font-size: 4.5rem !important;
  font-weight: 600;
  line-height: 1.05;
  letter-spacing: -0.025em;
  margin: 0 0 1rem;
  max-width: 18ch;
}

.cover-body :deep(h2),
.cover-body :deep(p) {
  font-size: 1.6rem !important;
  color: var(--josh-fg-soft);
  font-weight: 400;
  margin: 0;
  max-width: 32ch;
}

.cover-meta {
  display: flex;
  flex-direction: column;
  gap: 0.3rem;
  font-family: 'JetBrains Mono', ui-monospace, monospace;
  font-size: 0.95rem;
  color: var(--josh-muted);
  letter-spacing: 0.02em;
}

.meta-date {
  color: var(--josh-fg-soft);
}
</style>
