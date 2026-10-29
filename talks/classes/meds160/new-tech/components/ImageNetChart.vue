<script setup>
// ImageNet (ILSVRC) winning top-5 accuracy (100 − top-5 error) by year. Slide clicks: 0 = the
// pre-deep-learning years plus their trend, 1 = AlexNet, 2 = what followed
// and the human benchmark. Data: Russakovsky et al. (2015); later winners.
import { computed } from 'vue'
import { useSlideContext } from '@slidev/client'

const PTS = [
  { yr: 2010, e: 28.2, who: 'NEC-UIUC', at: 0 },
  { yr: 2011, e: 25.8, who: 'XRCE', at: 0 },
  { yr: 2012, e: 15.3, who: 'AlexNet', at: 1 },
  { yr: 2013, e: 11.7, who: '', at: 2 },
  { yr: 2014, e: 6.7, who: '', at: 2 },
  { yr: 2015, e: 3.6, who: '', at: 2 },
  { yr: 2016, e: 3.0, who: '', at: 2 },
  { yr: 2017, e: 2.3, who: '2017', at: 2 },
]
const HUMAN = 5.1
const acc = e => +(100 - e).toFixed(1)

const { $clicks } = useSlideContext()
const L = 56, R = 500, T = 16, B = 270
const x = yr => L + ((yr - 2010) / 7) * (R - L)
// y axis: accuracy, 60–100%
const y = a => B - ((a - 60) / 40) * (B - T)
const shown = computed(() => PTS.filter(p => $clicks.value >= p.at))
const path = computed(() => shown.value.map((p, i) => `${i ? 'L' : 'M'}${x(p.yr)},${y(acc(p.e))}`).join(' '))
// 2010→2011 pace (+2.4 points/year) carried forward
const trendEnd = acc(25.8) + 2.4 * 6
</script>

<template>
  <svg viewBox="0 0 520 310" class="inc">
    <!-- axes -->
    <g class="axis">
      <line :x1="L" :y1="B" :x2="R" :y2="B" />
      <line :x1="L" :y1="T" :x2="L" :y2="B" />
      <g v-for="a in [60, 70, 80, 90, 100]" :key="a">
        <line :x1="L - 5" :y1="y(a)" :x2="L" :y2="y(a)" />
        <text :x="L - 10" :y="y(a) + 5" class="tick" style="font-size:13px; text-anchor:end">{{ a }}%</text>
      </g>
      <text v-for="yr in [2010, 2011, 2012, 2013, 2014, 2015, 2016, 2017]" :key="yr" :x="x(yr)" :y="B + 22" class="tick" style="font-size:13px; text-anchor:middle">{{ String(yr).slice(2) === '10' ? yr : `’${String(yr).slice(2)}` }}</text>
      <text :x="14" :y="(T + B) / 2" class="lab" style="font-size:13px" :transform="`rotate(-90 14 ${(T + B) / 2})`">accuracy (top 5)</text>
    </g>

    <!-- the old pace, extended -->
    <g class="trend">
      <line :x1="x(2011)" :y1="y(acc(25.8))" :x2="x(2017)" :y2="y(trendEnd)" />
      <text :x="x(2017)" :y="y(trendEnd) + 34" style="font-size:13px; text-anchor:end">at the old pace</text>
    </g>

    <!-- human benchmark -->
    <g :class="['human', { on: $clicks >= 2 }]">
      <line :x1="L" :y1="y(acc(HUMAN))" :x2="R" :y2="y(acc(HUMAN))" />
      <text :x="L + 8" :y="y(acc(HUMAN)) - 7" style="font-size:13px">a careful human: {{ acc(HUMAN) }}%</text>
    </g>

    <path :d="path" class="line" />
    <g v-for="p in shown" :key="p.yr" :class="['pt', { alex: p.yr === 2012 }]">
      <circle :cx="x(p.yr)" :cy="y(acc(p.e))" :r="p.yr === 2012 ? 7 : 5" />
      <text v-if="p.who && p.yr < 2017" :x="x(p.yr) + 10" :y="y(acc(p.e)) + 20" style="font-size:13px">{{ p.who }} {{ acc(p.e) }}%</text>
      <text v-else-if="p.who" :x="x(p.yr)" :y="y(acc(p.e)) - 12" style="font-size:13px; text-anchor:end">{{ acc(p.e) }}%</text>
    </g>
  </svg>
</template>

<style scoped>
.inc { width: 100%; max-height: 18rem; }
.axis line { stroke: var(--fenbrook-rule); stroke-width: 1.5; }
.tick, .lab { fill: var(--fenbrook-muted); font-family: 'JetBrains Mono', monospace; }
.lab { text-anchor: middle; }
.trend line { stroke: var(--fenbrook-fg-soft); stroke-width: 2; stroke-dasharray: 5 6; }
.trend text { fill: var(--fenbrook-fg-soft); }
.human { opacity: 0; transition: opacity 0.4s; }
.human.on { opacity: 1; }
.human line { stroke: var(--fenbrook-fg); stroke-width: 1; stroke-dasharray: 2 4; }
.human text { fill: var(--fenbrook-fg); }
.line { fill: none; stroke: var(--fenbrook-fg); stroke-width: 2.5; }
.pt circle { fill: var(--fenbrook-fg); }
.pt text { fill: var(--fenbrook-fg-soft); }
.pt.alex circle { fill: var(--fenbrook-accent); }
.pt.alex text { fill: var(--fenbrook-accent); font-weight: 600; }
</style>
