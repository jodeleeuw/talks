<script setup lang="ts">
import { useSlots } from 'vue'
import FitContent from '../components/FitContent.vue'

withDefaults(defineProps<{
  mark?: string
  notesLabel?: string
}>(), {
  mark: '?',
  notesLabel: 'On your list',
})

const slots = useSlots()
</script>

<template>
  <div class="slidev-layout josh-outro" :class="{ 'has-notes': slots.next }">
    <div class="bigmark" aria-hidden="true">{{ mark }}</div>

    <section class="outro-main">
      <div class="outro-body">
        <FitContent align="center" origin="left center">
          <div class="outro-inner">
            <slot />
          </div>
        </FitContent>
      </div>
    </section>

    <aside v-if="slots.next" class="outro-notes">
      <div class="notes-label">{{ notesLabel }}</div>
      <div class="notes-body">
        <FitContent align="top" origin="top left">
          <div class="notes-inner">
            <slot name="next" />
          </div>
        </FitContent>
      </div>
    </aside>
  </div>
</template>

<style scoped>
.josh-outro {
  display: grid;
  grid-template-columns: 1fr;
  gap: 3rem;
  padding: 3rem 4rem 4rem;
  height: 100%;
  overflow: hidden;
  position: relative;
}

.josh-outro.has-notes {
  grid-template-columns: 1.45fr 1fr;
  gap: 3.5rem;
}

.bigmark {
  position: absolute;
  bottom: -2rem;
  left: -3rem;
  font-family: 'Fraunces', 'Source Serif Pro', Georgia, serif;
  font-size: 32rem;
  line-height: 0.85;
  font-weight: 500;
  font-style: italic;
  font-variation-settings: 'opsz' 144, 'SOFT' 30;
  color: transparent;
  -webkit-text-stroke: 2px var(--josh-accent);
  opacity: 0.28;
  pointer-events: none;
  user-select: none;
  z-index: 0;
}

.outro-main,
.outro-notes {
  position: relative;
  z-index: 1;
  display: flex;
  flex-direction: column;
  min-height: 0;
  min-width: 0;
}

.outro-body,
.notes-body {
  flex: 1 1 0;
  min-height: 0;
  overflow: hidden;
}

.outro-inner :deep(h1) {
  font-size: 3rem;
  font-weight: 500;
  line-height: 1.15;
  letter-spacing: -0.02em;
  color: var(--josh-fg);
  margin: 0 0 1.4rem;
  max-width: 22ch;
}

.outro-inner :deep(h1 em),
.outro-inner :deep(h1 strong) {
  color: var(--josh-accent);
  font-weight: 500;
}

.outro-inner :deep(p) {
  font-size: 1.3rem;
  line-height: 1.5;
  color: var(--josh-fg-soft);
  max-width: 36ch;
  margin: 0 0 0.9rem;
}

.outro-inner :deep(p:last-child) {
  margin-bottom: 0;
}

.outro-inner :deep(em) {
  color: var(--josh-fg);
  font-style: italic;
}

.outro-notes {
  border-left: 2px solid color-mix(in oklab, var(--josh-accent) 45%, transparent);
  padding-left: 2rem;
}

.notes-label {
  flex: 0 0 auto;
  font-family: 'JetBrains Mono', ui-monospace, monospace;
  font-size: 0.8rem;
  text-transform: uppercase;
  letter-spacing: 0.14em;
  color: var(--josh-accent);
  margin-bottom: 1.5rem;
}

.notes-inner :deep(ul),
.notes-inner :deep(ol) {
  list-style: none;
  padding: 0;
  margin: 0;
}

.notes-inner :deep(li) {
  position: relative;
  font-size: 1.05rem;
  line-height: 1.45;
  color: var(--josh-fg-soft);
  margin: 0 0 0.95rem;
  padding-left: 1.4rem;
}

.notes-inner :deep(li):last-child {
  margin-bottom: 0;
}

.notes-inner :deep(li)::before {
  content: '→';
  position: absolute;
  left: 0;
  top: 0;
  color: var(--josh-accent);
  font-family: 'JetBrains Mono', ui-monospace, monospace;
}

.notes-inner :deep(li strong) {
  color: var(--josh-fg);
  font-weight: 600;
}

.notes-inner :deep(li em) {
  color: var(--josh-fg);
  font-style: italic;
}

.notes-inner :deep(p) {
  font-size: 1.05rem;
  line-height: 1.45;
  color: var(--josh-fg-soft);
  margin: 0 0 0.8rem;
}
</style>
