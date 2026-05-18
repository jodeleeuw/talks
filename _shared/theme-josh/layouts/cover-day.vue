<script setup lang="ts">
import { useSlots } from 'vue'
import { configs } from '@slidev/client'
import FitContent from '../components/FitContent.vue'

defineProps<{ day?: string }>()

const tc = (configs.themeConfig ?? {}) as Record<string, string>
const slots = useSlots()
</script>

<template>
  <div class="slidev-layout josh-day">
    <div class="bignum" aria-hidden="true">{{ day || '01' }}</div>

    <header class="topbar">
      <span v-if="tc.course" class="course">{{ tc.course }}</span>
      <span v-if="day" class="sep">·</span>
      <span v-if="day" class="day-tag">DAY {{ day }}</span>
    </header>

    <div class="title">
      <FitContent align="center" origin="left center">
        <slot />
      </FitContent>
    </div>

    <div v-if="slots.discussion" class="discussion">
      <div class="cue">
        <span class="arrow">↓</span> Start here
      </div>
      <div class="discussion-body">
        <FitContent align="top">
          <slot name="discussion" />
        </FitContent>
      </div>
    </div>
  </div>
</template>

<style scoped>
.josh-day {
  display: flex;
  flex-direction: column;
  padding: 2.5rem 4rem 3rem;
  gap: 1.5rem;
  position: relative;
  overflow: hidden;
}

.bignum {
  position: absolute;
  bottom: -5rem;
  right: -3rem;
  font-family: 'Inter', sans-serif;
  font-size: 38rem;
  font-weight: 700;
  line-height: 0.8;
  letter-spacing: -0.06em;
  color: transparent;
  -webkit-text-stroke: 2px var(--josh-accent);
  opacity: 0.18;
  pointer-events: none;
  user-select: none;
  z-index: 0;
}

.topbar,
.title,
.discussion {
  position: relative;
  z-index: 1;
}

.topbar {
  flex: 0 0 auto;
  display: flex;
  align-items: center;
  gap: 0.7rem;
  font-family: 'JetBrains Mono', ui-monospace, monospace;
  font-size: 0.95rem;
  letter-spacing: 0.05em;
}

.course { color: var(--josh-muted); }
.sep { color: var(--josh-muted); }
.day-tag { color: var(--josh-fg-soft); }

.title {
  flex: 1 1 0;
  min-height: 0;
  display: flex;
  align-items: center;
}

.title :deep(h1) {
  font-family: 'Fraunces', 'Source Serif Pro', Georgia, serif !important;
  font-size: 6.25rem !important;
  font-style: italic;
  font-weight: 450;
  line-height: 1.02;
  letter-spacing: -0.02em;
  font-variation-settings: 'opsz' 144, 'SOFT' 30;
  color: var(--josh-fg);
  margin: 0;
  max-width: 15ch;
}

.title :deep(h1 em),
.title :deep(h1 strong) {
  font-style: italic;
  color: var(--josh-accent);
  font-weight: 500;
}

.discussion {
  flex: 0 1 auto;
  max-height: 50%;
  display: flex;
  flex-direction: column;
  min-height: 0;
  max-width: 60ch;
}

.cue {
  flex: 0 0 auto;
  font-family: 'JetBrains Mono', ui-monospace, monospace;
  font-size: 0.85rem;
  color: var(--josh-accent);
  letter-spacing: 0.14em;
  text-transform: uppercase;
  margin-bottom: 1rem;
}

.arrow {
  display: inline-block;
  margin-right: 0.3em;
  animation: bob 2.4s ease-in-out infinite;
}

@keyframes bob {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(4px); }
}

.discussion-body {
  flex: 1 1 auto;
  min-height: 0;
  overflow: hidden;
}

.discussion-body :deep(p) {
  font-size: 1.55rem !important;
  color: var(--josh-fg) !important;
  line-height: 1.45;
  margin: 0 0 0.5rem;
}

.discussion-body :deep(p:last-child) {
  margin-bottom: 0;
}
</style>
