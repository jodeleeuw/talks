<script setup>
// One model neuron: inputs → weights → sum → activation function → output.
// Geometry follows the original Google Slides deck (960×540 coordinates).
//
// With `build`, slide clicks reveal the parts (0: bare neuron, 1: weights,
// 2: sum, 3: activation function, 4: threshold + output). Without it the
// whole neuron shows at once, labelled with whatever props are passed, which
// is how the "What's the output?" exercises use it.
import { computed } from 'vue'
import { useSlideContext } from '@slidev/client'

const props = defineProps({
  build: { type: Boolean, default: false },
  inputs: { type: Array, default: () => ['i₁', 'i₂', 'i₃'] },
  weights: { type: Array, default: () => ['w₁', 'w₂', 'w₃'] },
  // lines of text in the activation box once it's fully built
  activation: { type: Array, default: () => ['1 if X ≥ T', '0 if X < T'] },
  output: { type: String, default: 'signal' },
})

const { $clicks } = useSlideContext()
const stage = computed(() => (props.build ? $clicks.value : 4))
const symbolicInputs = computed(() => props.inputs[0] === 'i₁')

const BODY = { x: 389, y: 335.5, r: 140.1 }
const W = [
  { x: 245.25, y: 236.05 },
  { x: 214.65, y: 338.75 },
  { x: 250.05, y: 441.45 },
]
const WR = 34.15
const LINES = [
  { y: 236, x2: 211.1 },
  { y: 338.7, x2: 180.6 },
  { y: 441.4, x2: 215.9 },
]
const ACT = { x: 482, y: 307.4, w: 164, h: 56.5 }
const actLines = computed(() => (stage.value >= 4 ? props.activation : stage.value >= 3 ? ['f(X)'] : []))
</script>

<template>
  <svg viewBox="80 140 820 330" class="neuron" role="img"
    aria-label="A model neuron: inputs times weights are summed, passed through an activation function, and sent on as output">
    <!-- column headers -->
    <text x="89" y="172" class="hdr">Inputs</text>
    <text x="204" y="172" class="hdr" :class="{ off: stage < 1 }">Weights</text>
    <text x="356" y="172" class="hdr" :class="{ off: stage < 2 }">Sum</text>
    <text x="517" y="164" class="hdr" :class="{ off: stage < 3 }">
      <tspan x="517" dy="0">Activation</tspan><tspan x="517" dy="19">Function</tspan>
    </text>
    <text x="780" y="172" class="hdr" :class="{ off: stage < 4 }">Output</text>

    <!-- inputs -->
    <g v-for="(L, i) in LINES" :key="'in' + i">
      <line x1="89.8" :y1="L.y" :x2="L.x2" :y2="L.y" class="wire" />
      <text x="93" :y="L.y - 10" class="in" :class="{ sym: symbolicInputs }">{{ inputs[i] }}</text>
    </g>

    <!-- cell body and sum -->
    <circle :cx="BODY.x" :cy="BODY.y" :r="BODY.r" class="body" />
    <text :x="BODY.x" :y="BODY.y" class="mid" :class="{ off: stage < 2 }">X = i₁w₁ + i₂w₂ + … + b</text>

    <!-- weights -->
    <g v-for="(c, i) in W" :key="'w' + i">
      <circle :cx="c.x" :cy="c.y" :r="WR" class="body" />
      <text :x="c.x" :y="c.y" class="mid" :class="{ off: stage < 1 }">{{ weights[i] }}</text>
    </g>

    <!-- activation function and output -->
    <rect :x="ACT.x" :y="ACT.y" :width="ACT.w" :height="ACT.h" class="body" />
    <text :x="ACT.x + ACT.w / 2" :y="ACT.y + ACT.h / 2" class="mid">
      <tspan v-for="(t, i) in actLines" :key="t + i" :x="ACT.x + ACT.w / 2"
        :dy="i === 0 ? -(actLines.length - 1) * 9 : 18" :class="{ fx: t === 'f(X)' }">{{ t }}</tspan>
    </text>
    <line x1="646" y1="335.6" x2="783.5" y2="335.6" class="wire" />
    <text x="790" y="336" class="out" :class="{ off: stage < 4 }">{{ output }}</text>
  </svg>
</template>

<style scoped>
.neuron { width: 100%; }
text { fill: var(--fenbrook-fg); transition: opacity 0.3s; }
.off { opacity: 0; }
.hdr { font-size: 15px; fill: var(--fenbrook-fg-soft); }
.in { font-size: 22px; }
.in.sym { font-size: 20px; font-style: italic; }
.mid { font-size: 15px; text-anchor: middle; dominant-baseline: middle; }
.fx { font-style: italic; }
.out { font-size: 16px; dominant-baseline: middle; }
.wire { stroke: var(--fenbrook-fg); stroke-width: 2.5; }
.body { fill: var(--fenbrook-bg); stroke: var(--fenbrook-fg); stroke-width: 1.8; }
</style>
