<script setup lang="ts">
import { computed } from 'vue'
import { configs, useNav } from '@slidev/client'

const tc = (configs.themeConfig ?? {}) as Record<string, string>
const nav = useNav()

const HIDE_ON = new Set(['cover', 'section', 'end', 'day'])

const slideFrontmatter = computed<Record<string, any>>(
  () => (nav.currentSlideRoute.value?.meta as any)?.slide?.frontmatter ?? {},
)

const visible = computed(() => {
  const route = nav.currentSlideRoute.value
  if (!route) return false
  const layout = (route.meta as any)?.layout
  if (layout && HIDE_ON.has(layout)) return false
  if (slideFrontmatter.value.footer === false) return false
  return true
})

const leftText = computed(() => {
  const fm = slideFrontmatter.value
  if (typeof fm.footer === 'string') return fm.footer
  return [tc.course, tc.event].filter(Boolean).join(' · ')
})

const initials = computed(() => tc.initials || 'jdl')
</script>

<template>
  <div v-show="visible" class="josh-footer">
    <div class="footer-left">{{ leftText }}</div>
    <div class="footer-right">
      <span class="page-num">{{ nav.currentSlideNo }} / {{ nav.total }}</span>
      <span class="sig-mark" aria-hidden="true">
        <span class="sq" />
        <span class="sig-initials">{{ initials }}</span>
      </span>
    </div>
  </div>
</template>

<style scoped>
.josh-footer {
  position: absolute;
  inset: auto 0 0 0;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0.9rem 1.5rem;
  font-family: 'JetBrains Mono', ui-monospace, monospace;
  font-size: 0.72rem;
  color: var(--josh-muted);
  letter-spacing: 0.04em;
  pointer-events: none;
  user-select: none;
}

.footer-left {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 60%;
}

.footer-right {
  display: flex;
  align-items: center;
  gap: 1.2rem;
}

.page-num {
  color: var(--josh-muted);
}

.sig-mark {
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
}

.sq {
  display: inline-block;
  width: 0.6rem;
  height: 0.6rem;
  background: var(--josh-accent);
}

.sig-initials {
  color: var(--josh-fg-soft);
  letter-spacing: 0.06em;
}
</style>
