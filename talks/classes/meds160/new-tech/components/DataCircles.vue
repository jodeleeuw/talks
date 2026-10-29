<script setup>
// Training data as circle areas (area ∝ words), nested and bottom-aligned.
// Each slide click adds the next circle and zooms out so it fits; all
// circles always share one scale. Numbers: Frank (2023); Llama 3 team (2024).
import { computed, onUnmounted, ref, watch } from 'vue'
import { useSlideContext } from '@slidev/client'

const ITEMS = [
  { name: 'A 20-year-old', note: 'up to 400 million words', v: 4e8, cls: 'human' },
  { name: 'GPT-3 (2020)', note: '500 billion tokens', v: 5e11, cls: 'gpt' },
  { name: 'Llama 3 (2024)', note: '15.6 trillion tokens', v: 1.56e13, cls: 'llama' },
]
const W = 820, BASE = 470, CX = 240
const FIT = 230 // radius of the newest (largest) circle

const { $clicks } = useSlideContext()
const level = computed(() => Math.min(Math.max($clicks.value, 0), ITEMS.length - 1))

// scale k: r = k·√v. Tween log k so each zoom-out feels even.
const target = lvl => FIT / Math.sqrt(ITEMS[lvl].v)
const logK = ref(Math.log(target(level.value)))
let raf = null
watch(level, (lvl) => {
  cancelAnimationFrame(raf)
  const from = logK.value, to = Math.log(target(lvl)), t0 = performance.now(), dur = 1400
  const tick = (t) => {
    const u = Math.min((t - t0) / dur, 1), e = u < 0.5 ? 2 * u * u : 1 - (-2 * u + 2) ** 2 / 2
    logK.value = from + (to - from) * e
    if (u < 1) raf = requestAnimationFrame(tick)
  }
  raf = requestAnimationFrame(tick)
})
onUnmounted(() => cancelAnimationFrame(raf))

const circles = computed(() => ITEMS.map((it, i) => {
  const r = Math.exp(logK.value) * Math.sqrt(it.v)
  const inside = r > 120
  // outside labels stack in a column right of the biggest circle, each on a
  // leader from its circle's upper-right edge
  const ax = CX + r * 0.707, ay = BASE - r - r * 0.707
  return { ...it, i, r, inside, ax, ay, lx: CX + FIT + 40, ly: BASE - 40 - 75 * i }
}))
const ratio = computed(() => Math.round(ITEMS[level.value].v / ITEMS[0].v).toLocaleString())
</script>

<template>
  <div class="dc">
    <svg :viewBox="`0 0 ${W} ${BASE + 10}`">
      <g v-for="c in [...circles].reverse()" :key="c.name" :class="['c', c.cls, { on: c.i <= level }]">
        <circle :cx="CX" :cy="BASE - c.r" :r="Math.max(c.r, 1.5)" />
        <template v-if="c.inside">
          <text :x="CX" :y="BASE - 2 * c.r + 46" class="name" style="font-size:24px">{{ c.name }}</text>
          <text :x="CX" :y="BASE - 2 * c.r + 72" class="note" style="font-size:16px">{{ c.note }}</text>
        </template>
        <template v-else>
          <polyline :points="`${c.ax},${c.ay} ${c.lx - 6},${c.ly + 6}`" class="lead" />
          <text :x="c.lx" :y="c.ly" class="name out" style="font-size:20px">{{ c.name }}</text>
          <text :x="c.lx" :y="c.ly + 20" class="note out" style="font-size:14px">{{ c.note }}</text>
        </template>
      </g>
    </svg>
    <p class="ratio" :class="{ on: level > 0 }"><b>{{ ratio }}×</b> more than the 20-year-old</p>
  </div>
</template>

<style scoped>
.dc { width: 100%; display: grid; grid-template-columns: 1fr 15rem; align-items: center; gap: 1rem; }
svg { width: 100%; height: 18.5rem; }
.c { opacity: 0; transition: opacity 0.5s; }
.c.on { opacity: 1; }
.c circle { stroke-width: 2; }
.human circle { fill: var(--fenbrook-fg); stroke: var(--fenbrook-fg); }
.gpt circle { fill: color-mix(in srgb, var(--fenbrook-fg-soft) 22%, transparent); stroke: var(--fenbrook-fg-soft); }
.llama circle { fill: color-mix(in srgb, var(--fenbrook-accent) 18%, transparent); stroke: var(--fenbrook-accent); }
.name { text-anchor: middle; font-weight: 600; fill: var(--fenbrook-fg); }
.note { text-anchor: middle; fill: var(--fenbrook-fg-soft); }
.human .name.out, .human .note.out { fill: var(--fenbrook-fg); }
.out { text-anchor: start; }
.human .name:not(.out) { fill: var(--fenbrook-bg); }
.human .note:not(.out) { fill: var(--fenbrook-bg); opacity: 0.8; }
.llama .name { fill: var(--fenbrook-accent); }
.lead { fill: none; stroke: var(--fenbrook-muted); stroke-width: 1.5; }
.ratio { white-space: nowrap; margin: 0 0 1rem; font-size: 1rem; color: var(--fenbrook-fg-soft); opacity: 0; transition: opacity 0.5s; }
.ratio.on { opacity: 1; }
.ratio b { display: block; font-size: 2.2rem; color: var(--fenbrook-accent); font-variant-numeric: tabular-nums; }
</style>
