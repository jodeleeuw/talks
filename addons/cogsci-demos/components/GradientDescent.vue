<script setup>
// Gradient descent on a one-weight loss curve: from where we stand we only
// know the local slope, so we hop downhill by learningRate × slope.
//
//   <GradientDescent />
//   <GradientDescent :curve="false" :tangent="$clicks >= 1" :step="$clicks >= 2 ? 1 : 0" :controls="false" />
//
// The curve has a shallow local minimum on the left and a deeper one on the
// right, so a small learning rate settles in the near dip and a large one
// hops over the hump (or bounces around). Click anywhere on the plot to
// start from that weight. :curve="false" hides the curve and shows only
// the current point (and tangent), which is all the learner can see.
import { computed, onUnmounted, ref, watch } from 'vue'
import { path, scale } from '../lib/plot.js'

const props = defineProps({
  start: { type: Number, default: 1.2 },
  lr: { type: Number, default: 0.1 },
  step: { type: Number, default: undefined },
  curve: { type: Boolean, default: true },
  tangent: { type: Boolean, default: true },
  controls: { type: Boolean, default: true },
  hint: { type: String, default: '' }, // optional caption drawn on the plot
})

const f = w => 0.06 * (w - 7.5) ** 2 + 2.2 * Math.exp(-((w - 3.8) ** 2) / 0.9) - 0.9 * Math.exp(-((w - 2.2) ** 2) / 0.3) + 1
const df = w => (f(w + 1e-4) - f(w - 1e-4)) / 2e-4
const W0 = 0, W1 = 10

const lr = ref(props.lr)
const w0 = ref(props.start)
const own = ref(0)
const n = computed(() => props.step ?? own.value)
const pts = computed(() => {
  const out = [w0.value]
  for (let k = 0; k < n.value; k++) {
    const w = out[out.length - 1] - lr.value * df(out[out.length - 1])
    out.push(Math.min(W1, Math.max(W0, w)))
  }
  return out
})
const cur = computed(() => pts.value[pts.value.length - 1])

const W = 700, H = 320, L = 50, T = 14, B = 34
const xs = scale(W0, W1, L, W - 12)
const ys = scale(0.5, 4.6, H - B, T)
const curveD = (() => {
  const p = []
  for (let w = W0; w <= W1 + 1e-9; w += 0.05) p.push([xs(w), ys(f(w))])
  return path(p)
})()
const tan = computed(() => {
  const w = cur.value, s = df(w), dw = 0.9
  return { x1: xs(w - dw), y1: ys(f(w) - s * dw), x2: xs(w + dw), y2: ys(f(w) + s * dw) }
})
const hops = computed(() => pts.value.slice(1).map((w, k) => {
  const a = pts.value[k]
  const x1 = xs(a), y1 = ys(f(a)), x2 = xs(w), y2 = ys(f(w))
  const lift = Math.min(60, 12 + Math.abs(x2 - x1) * 0.35)
  return `M${x1},${y1} Q${(x1 + x2) / 2},${Math.min(y1, y2) - lift} ${x2},${y2}`
}))

let timer = null
const running = ref(false)
function run() {
  if (running.value) return stop()
  running.value = true
  timer = setInterval(() => { own.value++; if (own.value > 60) stop() }, 380)
}
function stop() { running.value = false; clearInterval(timer) }
onUnmounted(stop)
function reset() { stop(); own.value = 0 }
watch(lr, () => { if (props.step === undefined) reset() })
const svg = ref(null)
function pick(e) {
  if (!props.controls) return
  const r = svg.value.getBoundingClientRect()
  const x = ((e.clientX - r.left) / r.width) * W
  const w = W0 + ((x - L) / (W - 12 - L)) * (W1 - W0)
  if (w < W0 || w > W1) return
  w0.value = +w.toFixed(2); reset()
}
</script>

<template>
  <div class="gd">
    <svg ref="svg" :viewBox="`0 0 ${W} ${H}`" class="gd-plot" role="img" aria-label="Loss as a function of one weight, with gradient descent steps" @click="pick">
      <line :x1="L" :y1="T" :x2="L" :y2="H - B" class="cd-axis" />
      <line :x1="L" :y1="H - B" :x2="W - 12" :y2="H - B" class="cd-axis" />
      <text :x="L - 10" :y="(T + H - B) / 2" class="cd-label" text-anchor="end">loss</text>
      <text :x="(L + W) / 2" :y="H - 8" class="cd-label" text-anchor="middle">weight</text>
      <path v-if="curve" :d="curveD" class="curve" />
      <path v-for="(d, k) in hops" :key="k" :d="d" class="hop" />
      <circle v-for="(w, k) in pts.slice(0, -1)" :key="'p' + k" :cx="xs(w)" :cy="ys(f(w))" r="4" class="past" />
      <line v-if="tangent" v-bind="tan" class="tan" />
      <circle :cx="xs(cur)" :cy="ys(f(cur))" r="7" class="now" />
      <text v-if="hint" :x="xs(cur) + 16" :y="ys(f(cur)) - 14" class="cd-tick">{{ hint }}</text>
    </svg>
    <div v-if="controls" class="cd-controls">
      <label class="cd-slider">learning rate <input v-model.number="lr" type="range" min="0.02" max="3" step="0.02"><b>{{ lr.toFixed(2) }}</b></label>
      <button class="cd-btn" :disabled="running" @click="own++">Step</button>
      <button class="cd-btn primary" @click="run">{{ running ? 'Pause' : 'Run' }}</button>
      <button class="cd-btn" @click="reset">Reset</button>
      <span>step <b class="cd-num">{{ n }}</b> · weight <b class="cd-num">{{ cur.toFixed(2) }}</b> · slope <b class="cd-num">{{ df(cur).toFixed(2) }}</b> · loss <b class="cd-num">{{ f(cur).toFixed(2) }}</b></span>
      <span class="cd-note">click the plot to pick a starting weight</span>
    </div>
  </div>
</template>

<style scoped>
.gd { display: flex; flex-direction: column; gap: 0.5rem; width: 100%; }
.gd-plot { width: 100%; max-height: 330px; cursor: crosshair; }
.curve { fill: none; stroke: #e8a33a; stroke-width: 2.4; }
.hop { fill: none; stroke: var(--fenbrook-fg-soft, #bbb); stroke-width: 1.4; stroke-dasharray: 4 4; }
.past { fill: var(--fenbrook-fg-soft, #bbb); }
.now { fill: var(--fenbrook-fg, #fff); }
.tan { stroke: #5b8fd6; stroke-width: 2.4; }
</style>
