<script setup>
// PASCAL VOC classification, best mean AP each year (comp1: trained on that
// year's VOC data). Computed from the official results tables. The test set
// grew each year, so years aren't perfectly comparable (hence the 2008 dip).
const PTS = [
  { yr: 2007, m: 59.4, who: 'INRIA' },
  { yr: 2008, m: 54.9, who: 'Surrey/UvA' },
  { yr: 2009, m: 66.5, who: 'NEC-UIUC' },
  { yr: 2010, m: 73.8, who: 'NUS' },
  { yr: 2011, m: 78.6, who: 'NUS' },
  { yr: 2012, m: 82.2, who: 'NUS' },
]
const L = 56, R = 500, T = 16, B = 270
const x = yr => L + ((yr - 2007) / 5) * (R - L)
const y = m => B - ((m - 40) / 60) * (B - T)
const path = PTS.map((p, i) => `${i ? 'L' : 'M'}${x(p.yr)},${y(p.m)}`).join(' ')
</script>

<template>
  <svg viewBox="0 0 520 310" class="voc">
    <g class="axis">
      <line :x1="L" :y1="B" :x2="R" :y2="B" />
      <line :x1="L" :y1="T" :x2="L" :y2="B" />
      <g v-for="m in [40, 60, 80, 100]" :key="m">
        <line :x1="L - 5" :y1="y(m)" :x2="L" :y2="y(m)" />
        <text :x="L - 10" :y="y(m) + 5" class="tick" style="font-size:13px; text-anchor:end">{{ m }}</text>
      </g>
      <text v-for="p in PTS" :key="p.yr" :x="x(p.yr)" :y="B + 22" class="tick" style="font-size:13px; text-anchor:middle">{{ p.yr }}</text>
      <text :x="14" :y="(T + B) / 2" class="tick" style="font-size:13px; text-anchor:middle" :transform="`rotate(-90 14 ${(T + B) / 2})`">score (mean AP)</text>
    </g>
    <path :d="path" class="line" />
    <g v-for="p in PTS" :key="'p' + p.yr" class="pt">
      <circle :cx="x(p.yr)" :cy="y(p.m)" r="5" />
      <text :x="x(p.yr)" :y="y(p.m) + (p.yr === 2008 ? 24 : -12)" style="font-size:13px; text-anchor:middle">{{ p.m }}</text>
    </g>
  </svg>
</template>

<style scoped>
.voc { width: 100%; max-height: 18rem; }
.axis line { stroke: var(--fenbrook-rule); stroke-width: 1.5; }
.tick { fill: var(--fenbrook-muted); font-family: 'JetBrains Mono', monospace; }
.line { fill: none; stroke: var(--fenbrook-fg); stroke-width: 2.5; }
.pt circle { fill: var(--fenbrook-fg); }
.pt text { fill: var(--fenbrook-fg-soft); }
</style>
