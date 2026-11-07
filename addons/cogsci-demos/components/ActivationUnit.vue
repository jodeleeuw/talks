<script setup>
// One unit from an interactive activation network, and how its activation
// moves over time under steady input. Uses the update rule from the
// interactive activation model (McClelland & Rumelhart, 1981):
//
//   n(t)   = excitation − inhibition
//   e(t)   = n (max − a)  if n > 0,   n (a − min)  if n < 0
//   a(t+1) = a − decay (a − rest) + e
//
//   <ActivationUnit />
//   <ActivationUnit :excitation="0.2" :inhibition="0" :decay="0.07" />
//
// Sliders set the inputs and constants; the plot redraws instantly. The
// input can be switched off partway through to show decay back to rest.
import { computed, reactive } from 'vue'
import { path, scale } from '../lib/plot.js'

const props = defineProps({
  excitation: { type: Number, default: 0.2 },
  inhibition: { type: Number, default: 0 },
  decay: { type: Number, default: 0.07 },
  rest: { type: Number, default: -0.1 },
  max: { type: Number, default: 1 },
  min: { type: Number, default: -0.2 },
  cycles: { type: Number, default: 60 },
})
const p = reactive({ exc: props.excitation, inh: props.inhibition, decay: props.decay, rest: props.rest, off: false })

const traj = computed(() => {
  let a = p.rest
  const out = [a]
  for (let t = 1; t <= props.cycles; t++) {
    const on = !p.off || t <= props.cycles / 2
    const n = on ? p.exc - p.inh : 0
    const e = n > 0 ? n * (props.max - a) : n * (a - props.min)
    a = a - p.decay * (a - p.rest) + e
    out.push(a)
  }
  return out
})
// fixed point with input on: a* where decay(a − rest) = e(a)
const equilibrium = computed(() => {
  const n = p.exc - p.inh
  if (n > 0) return (p.decay * p.rest + n * props.max) / (p.decay + n)
  if (n < 0) return (p.decay * p.rest - n * props.min) / (p.decay - n)
  return p.rest
})

const W = 520, H = 230, L = 46, T = 12, B = 30
const xs = computed(() => scale(0, props.cycles, L, W - 10))
const ys = scale(props.min - 0.05, props.max, H - B, T)
const d = computed(() => path(traj.value.map((a, t) => [xs.value(t), ys(a)])))
const fmt = v => (v >= 0 ? '+' : '−') + Math.abs(v).toFixed(2)
</script>

<template>
  <div class="au">
    <svg :viewBox="`0 0 ${W} ${H}`" class="au-plot" role="img" aria-label="Activation of one unit over time">
      <line v-for="t in [props.min, 0, 0.5, props.max]" :key="t" :x1="L" :x2="W - 10" :y1="ys(t)" :y2="ys(t)" class="cd-grid" />
      <text v-for="t in [props.min, 0, 0.5, props.max]" :key="'l' + t" :x="L - 6" :y="ys(t) + 4" class="cd-tick" text-anchor="end">{{ t }}</text>
      <line :x1="L" :x2="W - 10" :y1="ys(p.rest)" :y2="ys(p.rest)" class="rest" />
      <text :x="W - 12" :y="ys(p.rest) + 14" class="cd-tick" text-anchor="end">resting level</text>
      <line v-if="!p.off" :x1="L" :x2="W - 10" :y1="ys(equilibrium)" :y2="ys(equilibrium)" class="eq" />
      <line v-if="p.off" :x1="xs(props.cycles / 2)" :x2="xs(props.cycles / 2)" :y1="T" :y2="H - B" class="cd-grid" />
      <text v-if="p.off" :x="xs(props.cycles / 2) + 5" :y="T + 12" class="cd-tick">input off</text>
      <path :d="d" class="traj" />
      <text :x="W - 10" :y="H - 8" class="cd-tick" text-anchor="end">time (cycles)</text>
      <text :x="12" :y="T + 4" class="cd-label" transform-origin="12 12">a(t)</text>
    </svg>
    <div class="au-side cd-controls">
      <label class="cd-slider">excitatory input <input v-model.number="p.exc" type="range" min="0" max="0.5" step="0.01"><b>{{ p.exc.toFixed(2) }}</b></label>
      <label class="cd-slider">inhibitory input <input v-model.number="p.inh" type="range" min="0" max="0.5" step="0.01"><b>{{ p.inh.toFixed(2) }}</b></label>
      <label class="cd-slider">decay rate <input v-model.number="p.decay" type="range" min="0" max="0.5" step="0.01"><b>{{ p.decay.toFixed(2) }}</b></label>
      <label class="cd-slider">resting level <input v-model.number="p.rest" type="range" min="-0.2" max="0.2" step="0.01"><b>{{ fmt(p.rest) }}</b></label>
      <label class="cd-check"><input v-model="p.off" type="checkbox">turn input off halfway</label>
      <p class="cd-note">net input <b>{{ fmt(p.exc - p.inh) }}</b> · settles at <b>{{ equilibrium.toFixed(2) }}</b></p>
    </div>
  </div>
</template>

<style scoped>
.au { display: grid; grid-template-columns: minmax(0, 1.35fr) minmax(0, 1fr); gap: 1.5rem; align-items: center; width: 100%; }
.au-plot { width: 100%; max-height: 300px; }
.au-side { flex-direction: column; align-items: flex-start; }
.au-side .cd-slider { display: grid; grid-template-columns: 8.5em 1fr 3.5em; width: 100%; }
.au-side .cd-slider input { width: 100%; }
.rest { stroke: var(--fenbrook-muted, #888); stroke-dasharray: 4 5; }
.eq { stroke: var(--fenbrook-accent, orange); stroke-dasharray: 2 4; opacity: 0.6; }
.traj { fill: none; stroke: var(--fenbrook-accent, orange); stroke-width: 2.6; }
</style>
