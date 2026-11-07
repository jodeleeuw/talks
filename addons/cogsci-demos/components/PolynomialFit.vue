<script setup>
// The bias–variance tradeoff with polynomial regression. Noisy points come
// from a smooth curve; fit them with a polynomial of a chosen degree.
//
//   <PolynomialFit :degree="1" />
//   <PolynomialFit :degree="7" :samples="$clicks >= 2 ? 8 : 1" :controls="false" />
//
// Low degree: the fit misses the shape the same way every time (bias).
// High degree: the fit chases the noise, so fits to different samples
// disagree wildly (variance). "Overlay samples" draws the fits to several
// fresh samples at once; "Error by degree" averages training and test error
// over many samples for every degree. Ridge (L2) regularization shrinks the
// coefficients.
import { computed, reactive, watch } from 'vue'
import { gauss, path, rng, scale } from '../lib/plot.js'

const props = defineProps({
  degree: { type: Number, default: 1 },
  n: { type: Number, default: 20 }, // points per sample
  noise: { type: Number, default: 0.09 },
  samples: { type: Number, default: 1 }, // fits drawn (1 = just this sample)
  ridge: { type: Number, default: 0 },
  showPoints: { type: Boolean, default: true },
  showFit: { type: Boolean, default: true },
  equation: { type: Boolean, default: true },
  controls: { type: Boolean, default: true },
  seed: { type: Number, default: 4 },
})

const s = reactive({ degree: props.degree, seed: props.seed, samples: props.samples, ridge: props.ridge, tradeoff: false })
watch(() => [props.degree, props.samples, props.ridge], ([d, n, r]) => { s.degree = d; s.samples = n; s.ridge = r })
const truth = x => 0.3 + 0.45 * x + 0.13 * Math.sin(9 * x)

function sample(seed, n = props.n) {
  const r = rng(seed)
  return Array.from({ length: n }, () => { const x = r(); return [x, truth(x) + props.noise * gauss(r)] }).sort((a, b) => a[0] - b[0])
}
// least squares on t = 2x − 1 with optional ridge penalty (not on intercept)
function fit(data, d, lambda) {
  const m = d + 1
  const A = Array.from({ length: m }, () => new Array(m).fill(0)), b = new Array(m).fill(0)
  for (const [x, y] of data) {
    const t = 2 * x - 1, pw = [1]
    for (let k = 1; k < m; k++) pw.push(pw[k - 1] * t)
    for (let i = 0; i < m; i++) { b[i] += pw[i] * y; for (let j = 0; j < m; j++) A[i][j] += pw[i] * pw[j] }
  }
  for (let i = 1; i < m; i++) A[i][i] += lambda * data.length + 1e-10
  A[0][0] += 1e-10
  // Gaussian elimination with partial pivoting
  for (let c = 0; c < m; c++) {
    let p = c
    for (let r = c + 1; r < m; r++) if (Math.abs(A[r][c]) > Math.abs(A[p][c])) p = r;
    [A[c], A[p]] = [A[p], A[c]]; [b[c], b[p]] = [b[p], b[c]]
    for (let r = c + 1; r < m; r++) {
      const f = A[r][c] / A[c][c]
      for (let k = c; k < m; k++) A[r][k] -= f * A[c][k]
      b[r] -= f * b[c]
    }
  }
  const w = new Array(m).fill(0)
  for (let i = m - 1; i >= 0; i--) { let v = b[i]; for (let k = i + 1; k < m; k++) v -= A[i][k] * w[k]; w[i] = v / A[i][i] }
  return x => { const t = 2 * x - 1; let v = 0; for (let k = m - 1; k >= 0; k--) v = v * t + w[k]; return v }
}
const mse = (f, data) => data.reduce((a, [x, y]) => a + (f(x) - y) ** 2, 0) / data.length
const test = sample(9999, 400)

const data = computed(() => sample(s.seed))
const fits = computed(() => Array.from({ length: s.samples }, (_, k) => fit(k === 0 ? data.value : sample(s.seed * 97 + k), s.degree, s.ridge)))
const trainErr = computed(() => mse(fits.value[0], data.value))
const testErr = computed(() => mse(fits.value[0], test))
const curve = computed(() => {
  if (!s.tradeoff) return null
  const rows = []
  for (let d = 0; d <= 9; d++) {
    let tr = 0, te = 0
    for (let k = 0; k < 30; k++) { const D = sample(500 + k), f = fit(D, d, s.ridge); tr += mse(f, D); te += mse(f, test) }
    rows.push({ d, tr: tr / 30, te: te / 30 })
  }
  return rows
})

// ---- geometry --------------------------------------------------------------
const W = 560, H = 330, L = 40, T = 16, B = 32
const xs = scale(0, 1, L + 10, W - 14)
const ys = scale(-0.1, 1.15, H - B, T)
const clampY = v => Math.max(T - 30, Math.min(H - B + 30, ys(v)))
const fitPath = f => { const p = []; for (let x = 0; x <= 1.0001; x += 0.005) p.push([xs(x), clampY(f(x))]); return path(p) }
const sup = ['', '', '²', '³', '⁴', '⁵', '⁶', '⁷', '⁸', '⁹']
const sub = ['₀', '₁', '₂', '₃', '₄', '₅', '₆', '₇', '₈', '₉']
const eq = computed(() => 'y = ' + Array.from({ length: s.degree + 1 }, (_, k) => `b${sub[k]}${k ? 'x' + sup[k] : ''}`).join(' + '))

const CW = 300, CH = 170, CL = 34, CB = 26, CT = 10
const ce = computed(() => {
  if (!curve.value) return null
  const mx = Math.min(0.06, Math.max(...curve.value.map(r => r.te)))
  const cx = scale(0, 9, CL, CW - 8), cy = scale(0, mx, CH - CB, CT)
  const cl = v => cy(Math.min(v, mx))
  return { cx, tr: path(curve.value.map(r => [cx(r.d), cl(r.tr)])), te: path(curve.value.map(r => [cx(r.d), cl(r.te)])) }
})
</script>

<template>
  <div class="pf" :class="{ wide: !controls }">
    <svg :viewBox="`0 0 ${W} ${H}`" class="pf-plot" role="img" :aria-label="`Polynomial fit of degree ${s.degree}`">
      <defs><clipPath id="pf-clip"><rect :x="L" :y="T - 6" :width="W - L" :height="H - B - T + 6" /></clipPath></defs>
      <line :x1="L" :y1="T" :x2="L" :y2="H - B" class="cd-axis" />
      <line :x1="L" :y1="H - B" :x2="W - 10" :y2="H - B" class="cd-axis" />
      <text :x="L - 14" :y="(T + H - B) / 2" class="cd-label" text-anchor="middle">y</text>
      <text :x="(L + W) / 2" :y="H - 8" class="cd-label" text-anchor="middle">x</text>
      <g v-if="showFit" clip-path="url(#pf-clip)">
        <path v-for="(f, k) in fits" :key="k" :d="fitPath(f)" class="fit" :class="{ extra: k > 0 }" />
      </g>
      <g v-if="showPoints">
        <circle v-for="(q, k) in data" :key="k" :cx="xs(q[0])" :cy="ys(q[1])" r="6" class="pt" />
      </g>
      <g v-if="equation">
        <rect :x="W - 14 - Math.max(120, eq.length * 7.4)" :y="T - 8" :width="Math.max(120, eq.length * 7.4)" height="30" class="eqbox" />
        <text :x="W - 14 - Math.max(120, eq.length * 7.4) / 2" :y="T + 12" class="eqt" text-anchor="middle">{{ eq }}</text>
      </g>
    </svg>
    <div v-if="controls" class="pf-side cd-controls">
      <label class="cd-slider">degree <input v-model.number="s.degree" type="range" min="0" max="9" step="1"><b>{{ s.degree }}</b></label>
      <label class="cd-slider">ridge λ <input v-model.number="s.ridge" type="range" min="0" max="0.02" step="0.0005"><b>{{ s.ridge.toFixed(4) }}</b></label>
      <div class="cd-row">
        <button class="cd-btn" @click="s.seed++">New sample</button>
        <button class="cd-btn" :class="{ on: s.samples > 1 }" @click="s.samples = s.samples > 1 ? 1 : 10">Overlay samples</button>
        <button class="cd-btn" :class="{ on: s.tradeoff }" @click="s.tradeoff = !s.tradeoff">Error by degree</button>
      </div>
      <p class="cd-note">training error <b>{{ trainErr.toFixed(4) }}</b> · error on new data <b>{{ testErr.toFixed(4) }}</b></p>
      <svg v-if="ce" :viewBox="`0 0 ${CW} ${CH}`" class="pf-curve" role="img" aria-label="Average training and test error by polynomial degree">
        <line :x1="CL" :y1="CT" :x2="CL" :y2="CH - CB" class="cd-axis" />
        <line :x1="CL" :y1="CH - CB" :x2="CW - 8" :y2="CH - CB" class="cd-axis" />
        <text v-for="d in [0, 3, 6, 9]" :key="d" :x="ce.cx(d)" :y="CH - CB + 14" class="cd-tick" text-anchor="middle">{{ d }}</text>
        <text :x="(CL + CW) / 2" :y="CH - 1" class="cd-tick" text-anchor="middle">degree</text>
        <text :x="CL - 6" :y="(CT + CH - CB) / 2" class="cd-tick" text-anchor="end">error</text>
        <line :x1="ce.cx(s.degree)" :x2="ce.cx(s.degree)" :y1="CT" :y2="CH - CB" class="cd-grid" />
        <path :d="ce.tr" class="c-train" /><path :d="ce.te" class="c-test" />
        <text :x="CW - 8" :y="CT + 10" class="lg test" text-anchor="end">new data</text>
        <text :x="CW - 8" :y="CT + 24" class="lg train" text-anchor="end">training data</text>
      </svg>
    </div>
  </div>
</template>

<style scoped>
.pf { display: grid; grid-template-columns: minmax(0, 1.3fr) minmax(0, 1fr); gap: 1.4rem; align-items: center; width: 100%; }
.pf.wide { grid-template-columns: 1fr; }
.pf-plot { width: 100%; max-height: 360px; }
.pt { fill: #d68fb0; stroke: #fff; stroke-width: 1.4; }
.fit { fill: none; stroke: #f3d98c; stroke-width: 2.6; }
.fit.extra { stroke-width: 1.6; opacity: 0.75; }
.eqbox { fill: var(--fenbrook-bg, #111); stroke: var(--fenbrook-fg, #eee); stroke-width: 1.2; }
.eqt { fill: var(--fenbrook-fg, #eee); font-size: 12.5px; }
.pf-side { flex-direction: column; align-items: flex-start; }
.pf-side .cd-slider { display: grid; grid-template-columns: 4.5em 1fr 4em; width: 100%; }
.pf-side .cd-slider input { width: 100%; }
.pf-curve { width: 100%; max-height: 170px; }
.c-train { fill: none; stroke: #e8a33a; stroke-width: 2; }
.c-test { fill: none; stroke: #5b8fd6; stroke-width: 2; }
.lg { font-size: 11px; }
.lg.train { fill: #e8a33a; }
.lg.test { fill: #5b8fd6; }
</style>
