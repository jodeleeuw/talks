<script setup>
// Watch a small neural network overfit. Two classes of points (green and
// pink) are separated by a gently curving boundary, but a few training
// labels are wrong. As training goes on the network bends its boundary
// around those points: training loss keeps falling while loss on new data
// from the same source turns back up.
//
//   <OverfitPlayground />
//   <OverfitPlayground :hidden="30" :points="20" :decay="0" />
//   <OverfitPlayground :show-new="$clicks >= 1" />
//
// Controls: hidden units (model complexity), weight decay (L2
// regularization), and training-set size, which are the three remedies on
// the "How do we avoid overfitting?" slide. "Show new data" draws points the
// network never trained on. The dot on the validation curve marks where
// early stopping would have stopped.
import { computed, onMounted, onUnmounted, reactive, ref, shallowRef, watch } from 'vue'
import { createNet, makeData } from '../lib/mlp.js'
import { path, scale } from '../lib/plot.js'

const props = defineProps({
  hidden: { type: Number, default: 30 },
  points: { type: Number, default: 20 },
  decay: { type: Number, default: 0 },
  epochs: { type: Number, default: 800 },
  lr: { type: Number, default: 0.004 },
  seed: { type: Number, default: 3 },
  autoplay: { type: Boolean, default: false },
  showNew: { type: Boolean, default: false }, // start with new (validation) points drawn
})

const s = reactive({ hidden: props.hidden, points: props.points, decay: props.decay, showNew: props.showNew })
watch(() => props.showNew, v => { s.showNew = v })
const train = shallowRef([])
const val = shallowRef([])
const curves = ref({ train: [], val: [] })
const running = ref(false)
let net = null
let raf = 0

const GREEN = [143, 196, 122], PINK = [204, 128, 168]
const N = 56 // field resolution
const canvas = ref(null)
const contour = ref('')

function init() {
  stop()
  train.value = makeData(props.seed, s.points, 0.15)
  val.value = makeData(1000 + props.seed, 400, 0.15)
  net = createNet(s.hidden, 5)
  curves.value = { train: [net.loss(train.value)], val: [net.loss(val.value)] }
  draw()
}
function tick() {
  if (!running.value) return
  for (let k = 0; k < 6 && net.epoch < props.epochs; k++) {
    net.train(train.value, props.lr, s.decay)
    if (net.epoch % 3 === 0) {
      curves.value.train.push(net.loss(train.value))
      curves.value.val.push(net.loss(val.value))
    }
  }
  curves.value = { ...curves.value }
  draw()
  if (net.epoch >= props.epochs) return stop()
  raf = requestAnimationFrame(tick)
}
function run() {
  if (running.value) return stop()
  if (net.epoch >= props.epochs) init()
  running.value = true
  raf = requestAnimationFrame(tick)
}
function stop() { running.value = false; cancelAnimationFrame(raf) }
watch(() => [s.hidden, s.points, s.decay], init)
onMounted(() => { init(); if (props.autoplay) run() })
onUnmounted(stop)

// ---- decision field + boundary ------------------------------------------------
function draw() {
  const P = []
  for (let i = 0; i <= N; i++) {
    P.push([])
    for (let j = 0; j <= N; j++) P[i].push(net.predict(-1 + (2 * j) / N, 1 - (2 * i) / N))
  }
  const c = canvas.value
  if (c) {
    const ctx = c.getContext('2d')
    const img = ctx.createImageData(N, N)
    for (let i = 0; i < N; i++) for (let j = 0; j < N; j++) {
      const p = P[i][j], col = p >= 0.5 ? PINK : GREEN
      const k = (i * N + j) * 4
      img.data[k] = col[0]; img.data[k + 1] = col[1]; img.data[k + 2] = col[2]
      img.data[k + 3] = 40 + 70 * Math.abs(p - 0.5) * 2
    }
    ctx.putImageData(img, 0, 0)
  }
  // marching squares for p = 0.5
  const segs = []
  const at = (i, j) => P[i][j] - 0.5
  const lerp = (a, b) => a / (a - b)
  for (let i = 0; i < N; i++) for (let j = 0; j < N; j++) {
    const v = [at(i, j), at(i, j + 1), at(i + 1, j + 1), at(i + 1, j)]
    const e = []
    const corners = [[i, j], [i, j + 1], [i + 1, j + 1], [i + 1, j]]
    for (let k = 0; k < 4; k++) {
      const a = v[k], b = v[(k + 1) % 4]
      if ((a < 0) !== (b < 0)) {
        const t = lerp(a, b), [i1, j1] = corners[k], [i2, j2] = corners[(k + 1) % 4]
        e.push([j1 + t * (j2 - j1), i1 + t * (i2 - i1)])
      }
    }
    if (e.length >= 2) segs.push(e[0], e[1])
    if (e.length === 4) segs.push(e[2], e[3])
  }
  const S = PLOT / N
  let d = ''
  for (let k = 0; k < segs.length; k += 2) d += `M${(segs[k][0] * S).toFixed(1)},${(segs[k][1] * S).toFixed(1)}L${(segs[k + 1][0] * S).toFixed(1)},${(segs[k + 1][1] * S).toFixed(1)}`
  contour.value = d
}

// ---- geometry ---------------------------------------------------------------
const PLOT = 330
const px = v => ((v + 1) / 2) * PLOT
const py = v => ((1 - v) / 2) * PLOT
const newPts = computed(() => val.value.slice(0, 40))

const CW = 380, CH = 250, CL = 44, CT = 12, CB = 30
const curveMax = computed(() => Math.min(2.5, Math.max(1, ...curves.value.val, ...curves.value.train)))
const cx = computed(() => scale(0, props.epochs / 3, CL, CW - 8))
const cy = computed(() => scale(0, curveMax.value, CH - CB, CT))
const trainD = computed(() => path(curves.value.train.map((v, k) => [cx.value(k), cy.value(Math.min(v, curveMax.value))])))
const valD = computed(() => path(curves.value.val.map((v, k) => [cx.value(k), cy.value(Math.min(v, curveMax.value))])))
const best = computed(() => {
  const v = curves.value.val
  let k = 0
  for (let i = 1; i < v.length; i++) if (v[i] < v[k]) k = i
  return { k, v: v[k] }
})
const epoch = computed(() => Math.max(0, curves.value.train.length - 1) * 3)
</script>

<template>
  <div class="ov">
    <div class="ov-field">
      <canvas ref="canvas" :width="N" :height="N" class="ov-canvas" />
      <svg :viewBox="`0 0 ${PLOT} ${PLOT}`" class="ov-svg" role="img" aria-label="Training points and the network's decision boundary">
        <path :d="contour" class="boundary" />
        <g v-if="s.showNew">
          <circle v-for="(q, k) in newPts" :key="'v' + k" :cx="px(q[0])" :cy="py(q[1])" r="5" :class="['pt', 'new', q[2] ? 'pink' : 'green']" />
        </g>
        <circle v-for="(q, k) in train" :key="k" :cx="px(q[0])" :cy="py(q[1])" r="10" :class="['pt', q[2] ? 'pink' : 'green']" />
      </svg>
    </div>
    <div class="ov-side">
      <svg :viewBox="`0 0 ${CW} ${CH}`" class="ov-curves" role="img" aria-label="Training and validation loss by epoch">
        <line :x1="CL" :y1="CT" :x2="CL" :y2="CH - CB" class="cd-axis" />
        <line :x1="CL" :y1="CH - CB" :x2="CW - 8" :y2="CH - CB" class="cd-axis" />
        <text :x="CL - 8" :y="CT + 10" class="cd-tick" text-anchor="end">{{ curveMax.toFixed(1) }}</text>
        <text :x="CL - 8" :y="CH - CB" class="cd-tick" text-anchor="end">0</text>
        <text :x="14" :y="(CT + CH - CB) / 2" class="cd-label" :transform="`rotate(-90 14 ${(CT + CH - CB) / 2})`" text-anchor="middle">Loss</text>
        <text :x="(CL + CW) / 2" :y="CH - 6" class="cd-label" text-anchor="middle">Epoch</text>
        <path :d="trainD" class="c-train" />
        <path :d="valD" class="c-val" />
        <circle v-if="curves.val.length > 20 && best.k < curves.val.length - 10" :cx="cx(best.k)" :cy="cy(best.v)" r="5" class="best" />
        <text :x="CW - 10" :y="CT + 12" class="lg val" text-anchor="end">Validation data</text>
        <text :x="CW - 10" :y="CT + 28" class="lg train" text-anchor="end">Training data</text>
      </svg>
      <div class="cd-controls ov-controls">
        <div class="cd-row">
          <button class="cd-btn primary" @click="run">{{ running ? 'Pause' : 'Train' }}</button>
          <button class="cd-btn" @click="init">Reset</button>
          <label class="cd-check"><input v-model="s.showNew" type="checkbox">show new data</label>
          <span>epoch <b class="cd-num">{{ epoch }}</b></span>
        </div>
        <label class="cd-slider">hidden units <input v-model.number="s.hidden" type="range" min="1" max="40" step="1"><b>{{ s.hidden }}</b></label>
        <label class="cd-slider">weight decay <input v-model.number="s.decay" type="range" min="0" max="0.03" step="0.001"><b>{{ s.decay.toFixed(3) }}</b></label>
        <label class="cd-slider">training points <input v-model.number="s.points" type="range" min="10" max="200" step="10"><b>{{ s.points }}</b></label>
      </div>
    </div>
  </div>
</template>

<style scoped>
.ov { display: grid; grid-template-columns: minmax(0, 0.9fr) minmax(0, 1.1fr); gap: 1.6rem; align-items: center; width: 100%; }
.ov-field { position: relative; width: 100%; max-width: 360px; aspect-ratio: 1; justify-self: center; }
.ov-canvas, .ov-svg { position: absolute; inset: 0; width: 100%; height: 100%; border-radius: 6px; }
.ov-canvas { image-rendering: auto; }
.boundary { fill: none; stroke: #fff; stroke-width: 2; stroke-dasharray: 2 4; stroke-linecap: round; }
.pt { stroke: #fff; stroke-width: 1.5; }
.pt.green { fill: #8fc47a; }
.pt.pink { fill: #cc80a8; }
.pt.new { stroke-width: 1; opacity: 0.9; }
.ov-side { display: flex; flex-direction: column; gap: 0.6rem; }
.ov-curves { width: 100%; max-height: 260px; }
.c-train { fill: none; stroke: #e8a33a; stroke-width: 2.2; }
.c-val { fill: none; stroke: #5b8fd6; stroke-width: 2.2; }
.best { fill: none; stroke: var(--fenbrook-fg, #fff); stroke-width: 2; }
.lg { font-size: 12px; }
.lg.train { fill: #e8a33a; }
.lg.val { fill: #5b8fd6; }
.ov-controls { flex-direction: column; align-items: flex-start; }
.ov-controls .cd-slider { display: grid; grid-template-columns: 8em 1fr 3.5em; width: 100%; }
.ov-controls .cd-slider input { width: 100%; }
</style>
