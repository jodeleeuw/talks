<script setup>
// Cat-vs-dog network. Slide clicks build it up (layers at clicks 0–3); at
// `runAt`, activity flows layer by layer from the pixels to the dog unit.
// Activations are made up for the demo. Click the net to replay.
import { computed, onUnmounted, ref, watch } from 'vue'
import { useSlideContext } from '@slidev/client'

const props = defineProps({
  runAt: { type: Number, default: 4 },
  step: { type: Number, default: 650 }, // ms per layer
})

const { $clicks } = useSlideContext()

const X = [140, 380, 620, 860]
const LAYERS = [
  { ys: [50, 200, 350], act: [0.9, 0.45, 0.75], label: 'pixels' },
  { ys: [50, 150, 250, 350], act: [0.85, 0.2, 0.6, 0.95], label: 'hidden' },
  { ys: [50, 150, 250, 350], act: [0.25, 0.9, 0.7, 0.1], label: 'hidden' },
  { ys: [50, 350], act: [0.03, 0.97], label: 'output' },
]
const OUT = [['cat', '3%'], ['dog', '97%']]

const nodes = LAYERS.flatMap((L, l) => L.ys.map((y, i) => ({ l, i, x: X[l], y, a: L.act[i] })))
const edges = LAYERS.slice(1).flatMap((L, k) =>
  LAYERS[k].ys.flatMap((y1, i) => L.ys.map((y2, j) => ({
    l: k + 1, x1: X[k] + 23, y1, x2: X[k + 1] - 23, y2,
    // a signal is strong when the sender is active and the receiver ends up active
    a: LAYERS[k].act[i] * L.act[j],
  }))),
)

// stage: -1 idle, 0 inputs lit, 1–3 edges into layer l then layer l lit, 4 answer shown
const stage = ref(-1)
let timer = null
function run() {
  clearInterval(timer)
  stage.value = 0
  timer = setInterval(() => {
    stage.value++
    if (stage.value >= LAYERS.length) clearInterval(timer)
  }, props.step)
}
function stop() {
  clearInterval(timer)
  stage.value = -1
}
watch(() => $clicks.value >= props.runAt, on => (on ? run() : stop()), { immediate: true })
onUnmounted(() => clearInterval(timer))

const shown = l => $clicks.value >= l
const lit = l => stage.value >= l
const flowing = l => stage.value === l
const done = computed(() => stage.value >= LAYERS.length)
const replay = () => { if ($clicks.value >= props.runAt) run() }
</script>

<template>
  <svg viewBox="0 0 1060 440" class="cdn" @click="replay">
    <g v-for="(e, k) in edges" :key="'e' + k" :class="['layer', { on: shown(e.l) }]">
      <line :x1="e.x1" :y1="e.y1" :x2="e.x2" :y2="e.y2" class="edge" />
      <line
        v-if="lit(e.l)"
        :x1="e.x1" :y1="e.y1" :x2="e.x2" :y2="e.y2"
        :class="['sig', { flow: flowing(e.l) }]"
        :style="{ opacity: 0.15 + 0.85 * e.a, strokeWidth: 1 + 2.5 * e.a }"
      />
    </g>

    <g v-for="n in nodes" :key="`n${n.l}-${n.i}`" :class="['layer', { on: shown(n.l) }]">
      <circle :cx="n.x" :cy="n.y" r="23" class="unit" />
      <circle :cx="n.x" :cy="n.y" r="23" class="fill" :style="{ opacity: lit(n.l) ? n.a : 0 }" />
    </g>

    <text v-for="(L, l) in LAYERS" :key="'t' + l" :x="X[l]" y="410" :class="['lbl', 'layer', { on: shown(l) }]" style="font-size:16px">{{ L.label }}</text>

    <g v-for="([name, p], i) in OUT" :key="name" :class="['layer', { on: shown(3) }]">
      <text x="975" :y="LAYERS[3].ys[i] + 8" :class="['out', { win: done && i === 1 }]" style="font-size:22px">
        {{ done ? `${name} ${p}` : name }}
      </text>
    </g>
  </svg>
</template>

<style scoped>
.cdn { width: 100%; cursor: pointer; }
.layer { opacity: 0; transition: opacity 0.3s; }
.layer.on { opacity: 1; }
.edge { stroke: var(--fenbrook-fg); stroke-width: 1; opacity: 0.25; }
.sig { stroke: var(--fenbrook-accent); stroke-linecap: round; }
.sig.flow { stroke-dasharray: 10 14; animation: flow 0.5s linear infinite; }
@keyframes flow { to { stroke-dashoffset: -24; } }
.unit { fill: var(--fenbrook-bg); stroke: var(--fenbrook-fg); stroke-width: 1.5; }
.fill { fill: var(--fenbrook-accent); transition: opacity 0.35s; }
.lbl { fill: var(--fenbrook-muted); text-anchor: middle; }
.out { fill: var(--fenbrook-muted); text-anchor: middle; transition: fill 0.3s; }
.out.win { fill: var(--fenbrook-accent); font-weight: 600; }
</style>
