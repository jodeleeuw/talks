<script setup>
// Backpropagation through the smallest possible "deep" network: three
// layers that each multiply by one weight, then a squared-error loss.
//
//   a = i0·w0,  b = a·w1,  y' = b·w2,  L = (y − y')²
//
//   <BackpropChain />                                  i0 = 2, w = .5, −1, 2, y = 1
//   <BackpropChain :step="$clicks" :controls="false" />   reveal gradients on clicks
//   <BackpropChain :i0="1" :w="[2, .5, -1]" :y="-1" blanks />   exercise version
//
// step n reveals the first n of: dL/dy', dL/dw2, dy'/db, dL/dw1, db/da,
// dL/dw0 (the order the slides work through them). With controls, a
// "wiggle" readout compares the finite-difference slope for w0 with the
// backprop answer, and "Gradient step" moves every weight downhill.
import { computed, reactive, ref, watch } from 'vue'

const props = defineProps({
  i0: { type: Number, default: 2 },
  w: { type: Array, default: () => [0.5, -1, 2] },
  y: { type: Number, default: 1 },
  step: { type: Number, default: undefined }, // gradients revealed
  values: { type: Boolean, default: true }, // false: names only
  blanks: { type: Boolean, default: false }, // show "= ?" for unrevealed gradients
  wiggle: { type: Number, default: 0 }, // > 0: show w0 nudged by this much
  controls: { type: Boolean, default: true },
})

const s = reactive({ w: [...props.w], i0: props.i0, y: props.y })
watch(() => [props.w, props.i0, props.y], () => { s.w = [...props.w]; s.i0 = props.i0; s.y = props.y; losses.value = [] }, { deep: true })
const h = ref(0.1)
const lr = ref(0.01)
const losses = ref([])
const own = ref(6)
const shown = computed(() => (props.step ?? (props.controls ? own.value : 6)))

const fwd = (w0, w1, w2) => {
  const a = s.i0 * w0, b = a * w1, yp = b * w2
  return { a, b, yp, L: (s.y - yp) ** 2 }
}
const nudge = computed(() => props.wiggle)
const F = computed(() => fwd(s.w[0] + nudge.value, s.w[1], s.w[2]))
const base = computed(() => fwd(...s.w))
const g = computed(() => {
  const { a, b, yp } = base.value
  const dLdy = 2 * (yp - s.y)
  return { dLdy, dLdw2: dLdy * b, dydb: s.w[2], dLdw1: dLdy * s.w[2] * a, dbda: s.w[1], dLdw0: dLdy * s.w[2] * s.w[1] * s.i0 }
})
const finite = computed(() => (fwd(s.w[0] + h.value, s.w[1], s.w[2]).L - base.value.L) / h.value)

function descend() {
  if (!losses.value.length) losses.value = [base.value.L]
  const G = g.value
  s.w = [s.w[0] - lr.value * G.dLdw0, s.w[1] - lr.value * G.dLdw1, s.w[2] - lr.value * G.dLdw2]
  losses.value = [...losses.value, base.value.L]
}
function reset() { s.w = [...props.w]; losses.value = [] }

// ---- layout --------------------------------------------------------------
const TOP = 70, BOT = 186, R = 31, r = 13
const X = { i0: 50, m1: 135, a: 220, m2: 305, b: 390, m3: 475, yp: 560, se: 650, L: 745 }
const num = v => {
  const t = Math.round(v * 100) / 100
  return Object.is(t, -0) ? '0' : String(t)
}
const val = (v, extra = '') => (props.values ? num(v) + extra : '')
const PILLS = computed(() => [
  { key: 'dLdy', x: X.yp, y: BOT, label: "dL / dy'" },
  { key: 'dLdw2', x: X.b, y: TOP, label: 'dL / dw₂' },
  { key: 'dydb', x: X.b, y: BOT, label: "dy' / db" },
  { key: 'dLdw1', x: X.a, y: TOP, label: 'dL / dw₁' },
  { key: 'dbda', x: X.a, y: BOT, label: 'db / da' },
  { key: 'dLdw0', x: X.i0, y: TOP, label: 'dL / dw₀' },
])
const pills = computed(() => PILLS.value.map((p, k) => ({ ...p, on: k < shown.value, text: k < shown.value ? `${p.label} = ${num(g.value[p.key])}` : `${p.label} = ?` }))
  .filter(p => p.on || props.blanks))
const wtop = [X.i0, X.a, X.b]
const spark = computed(() => {
  const L = losses.value
  if (L.length < 2) return ''
  const mx = Math.max(...L)
  return L.map((v, i) => `${i ? 'L' : 'M'}${(i / (L.length - 1)) * 120},${34 - (v / mx) * 30}`).join('')
})
</script>

<template>
  <div class="bp">
    <svg viewBox="0 -8 800 262" class="bp-net" role="img" aria-label="Computation graph: input times three weights, then squared error">
      <g class="wires">
        <path :d="`M${X.i0 + R},${BOT} H${X.m1 - r} M${X.m1 + r},${BOT} H${X.a - R} M${X.a + R},${BOT} H${X.m2 - r} M${X.m2 + r},${BOT} H${X.b - R} M${X.b + R},${BOT} H${X.m3 - r} M${X.m3 + r},${BOT} H${X.yp - R} M${X.yp + R},${BOT} H${X.se - r} M${X.se + r},${BOT} H${X.L - R - 6}`" />
        <path v-for="(x, k) in wtop" :key="k" :d="`M${x + R},${TOP} H${[X.m1, X.m2, X.m3][k]} V${BOT - r}`" />
        <path :d="`M${X.yp + R},${TOP} H${X.se} V${BOT - r}`" />
      </g>
      <!-- weights and target -->
      <g v-for="(x, k) in wtop" :key="'w' + k">
        <circle :cx="x" :cy="TOP" :r="R" class="node" />
        <rect :x="x - 12" :y="TOP - R - 16" width="24" height="18" rx="3" class="tag" />
        <text :x="x" :y="TOP - R - 3" class="tagt" text-anchor="middle">w{{ ['₀', '₁', '₂'][k] }}</text>
        <text :x="x" :y="TOP + 6" class="v" text-anchor="middle">{{ k === 0 && wiggle ? val(s.w[0], '+' + wiggle) : val(s.w[k]) }}</text>
      </g>
      <circle :cx="X.yp" :cy="TOP" :r="R" class="node target" />
      <text :x="X.yp" :y="TOP + 6" class="v" text-anchor="middle">{{ values ? num(s.y) : 'y' }}</text>
      <!-- chain -->
      <g v-for="n in [['i0', 'i₀', s.i0], ['a', 'a', F.a], ['b', 'b', F.b], ['yp', 'y\'', F.yp]]" :key="n[0]">
        <circle :cx="X[n[0]]" :cy="BOT" :r="R" class="node" />
        <rect :x="X[n[0]] - 12" :y="BOT - R - 16" width="24" height="18" rx="3" class="tag" />
        <text :x="X[n[0]]" :y="BOT - R - 3" class="tagt" text-anchor="middle">{{ n[1] }}</text>
        <text :x="X[n[0]]" :y="BOT + 6" class="v" text-anchor="middle">{{ val(n[2]) }}</text>
      </g>
      <g v-for="m in ['m1', 'm2', 'm3']" :key="m"><circle :cx="X[m]" :cy="BOT" :r="r" class="node" /><text :x="X[m]" :y="BOT + 5" class="op" text-anchor="middle">*</text></g>
      <circle :cx="X.se" :cy="BOT" :r="r + 2" class="node" /><text :x="X.se" :y="BOT + 4" class="opt" text-anchor="middle">se</text>
      <circle :cx="X.L" :cy="BOT" :r="R + 6" class="node" />
      <rect :x="X.L - 10" :y="BOT - R - 22" width="20" height="18" rx="3" class="tag" />
      <text :x="X.L" :y="BOT - R - 9" class="tagt" text-anchor="middle">L</text>
      <text :x="X.L" :y="BOT + 6" class="v" text-anchor="middle">{{ values ? num(F.L) : 'loss' }}</text>
      <text v-for="(lab, k) in ['Layer 1', 'Layer 2', 'Layer 3']" :key="lab" :x="[X.m1, X.m2, X.m3][k]" :y="BOT + 34" class="layer" text-anchor="middle">{{ lab }}</text>
      <!-- gradients -->
      <g v-for="p in pills" :key="p.key" :class="{ blank: !p.on }">
        <rect :x="p.x - 52" :y="p.y + R - 4" width="104" height="20" rx="5" class="pill" />
        <text :x="p.x" :y="p.y + R + 10" class="pillt" text-anchor="middle">{{ p.text }}</text>
      </g>
    </svg>
    <div v-if="controls" class="cd-controls bp-controls">
      <button v-if="step === undefined" class="cd-btn" @click="own = own >= 6 ? 0 : own + 1">{{ own >= 6 ? 'Hide gradients' : 'Next gradient' }}</button>
      <span>wiggle w₀ by <select v-model.number="h" class="bp-sel"><option :value="0.1">0.1</option><option :value="0.01">0.01</option><option :value="0.001">0.001</option></select>:
        slope <b class="cd-num">{{ finite.toFixed(2) }}</b> vs. backprop <b class="cd-num">{{ num(g.dLdw0) }}</b></span>
      <label class="cd-slider">learning rate <input v-model.number="lr" type="range" min="0.002" max="0.06" step="0.002"><b>{{ lr.toFixed(3) }}</b></label>
      <button class="cd-btn primary" @click="descend">Gradient step</button>
      <button class="cd-btn" @click="reset">Reset</button>
      <svg v-if="spark" viewBox="-2 0 124 38" class="spark" aria-label="Loss after each step"><path :d="spark" /></svg>
    </div>
  </div>
</template>

<style scoped>
.bp { display: flex; flex-direction: column; gap: 0.5rem; width: 100%; }
.bp-net { width: 100%; max-height: 300px; }
.wires path { fill: none; stroke: var(--fenbrook-fg, #eee); stroke-width: 1.4; }
.node { fill: var(--fenbrook-bg, #111); stroke: var(--fenbrook-fg, #eee); stroke-width: 2; }
.node.target { stroke: #e06c4c; stroke-width: 2.6; }
.tag { fill: var(--fenbrook-bg, #111); stroke: var(--fenbrook-fg-soft, #bbb); stroke-width: 1; }
.tagt { fill: var(--fenbrook-fg, #eee); font-size: 11px; }
.v { fill: var(--fenbrook-fg, #eee); font-size: 16px; font-family: 'JetBrains Mono', monospace; }
.op { fill: var(--fenbrook-fg, #eee); font-size: 16px; }
.opt { fill: var(--fenbrook-fg, #eee); font-size: 11px; }
.layer { fill: var(--fenbrook-fg-soft, #bbb); font-size: 12px; }
.pill { fill: var(--fenbrook-bg-elev, #1a1a1a); stroke: var(--fenbrook-accent, orange); stroke-width: 1.3; }
.pillt { fill: var(--fenbrook-fg, #eee); font-size: 11.5px; font-family: 'JetBrains Mono', monospace; }
.blank .pill { stroke: var(--fenbrook-fg-soft, #bbb); }
.bp-controls { font-size: 0.8rem; }
.bp-sel { background: transparent; color: inherit; border: 1px solid var(--fenbrook-rule, #555); border-radius: 4px; font: inherit; }
.spark { width: 90px; height: 28px; }
.spark path { fill: none; stroke: var(--fenbrook-accent, orange); stroke-width: 2; }
</style>
