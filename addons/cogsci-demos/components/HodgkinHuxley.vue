<script setup>
// Hodgkin–Huxley neuron, simulated live in the browser.
//
//   <HodgkinHuxley />
//
// The membrane potential scrolls across the screen like an oscilloscope.
// "Stimulate" delivers a short current pulse (its size set by the slider), so
// small pulses fizzle and big ones fire a spike. "Steady current" holds a
// constant input, which above about 6.3 µA/cm² makes the cell fire
// repeatedly, faster as the current grows. Optionally plots the m, h and n
// gates underneath.
//
// Standard 1952 squid-axon parameters, shifted so rest sits at −65 mV, and
// integrated with 4th-order Runge–Kutta at 0.01 ms. The simulation only runs
// while the slide is on screen.
import { computed, onMounted, onUnmounted, reactive, ref } from 'vue'

const props = defineProps({
  window: { type: Number, default: 100 }, // ms of trace shown
  speed: { type: Number, default: 25 }, // simulated ms per real second
  gates: { type: Boolean, default: false }, // show the gating plot at first
  current: { type: Number, default: 0 }, // initial steady current, µA/cm²
  pulse: { type: Number, default: 10 }, // initial pulse size, µA/cm²
})

// ---- model ----------------------------------------------------------------
const C = 1
const G_NA = 120, G_K = 36, G_L = 0.3
const E_NA = 50, E_K = -77, E_L = -54.387
const PULSE_MS = 1
const DT = 0.01
const SAMPLE = 0.1 // ms between plotted samples

const vtrap = (x, y) => (Math.abs(x / y) < 1e-6 ? y * (1 - x / y / 2) : x / (Math.exp(x / y) - 1))
const am = V => 0.1 * vtrap(-(V + 40), 10)
const bm = V => 4 * Math.exp(-(V + 65) / 18)
const ah = V => 0.07 * Math.exp(-(V + 65) / 20)
const bh = V => 1 / (1 + Math.exp(-(V + 35) / 10))
const an = V => 0.01 * vtrap(-(V + 55), 10)
const bn = V => 0.125 * Math.exp(-(V + 65) / 80)

function deriv([V, m, h, n], I) {
  const iNa = G_NA * m ** 3 * h * (V - E_NA)
  const iK = G_K * n ** 4 * (V - E_K)
  const iL = G_L * (V - E_L)
  return [
    (I - iNa - iK - iL) / C,
    am(V) * (1 - m) - bm(V) * m,
    ah(V) * (1 - h) - bh(V) * h,
    an(V) * (1 - n) - bn(V) * n,
  ]
}
function rk4(y, I) {
  const add = (a, b, k) => a.map((v, i) => v + k * b[i])
  const k1 = deriv(y, I)
  const k2 = deriv(add(y, k1, DT / 2), I)
  const k3 = deriv(add(y, k2, DT / 2), I)
  const k4 = deriv(add(y, k3, DT), I)
  return y.map((v, i) => v + (DT / 6) * (k1[i] + 2 * k2[i] + 2 * k3[i] + k4[i]))
}
const V0 = -65
const steady = V => [V, am(V) / (am(V) + bm(V)), ah(V) / (ah(V) + bh(V)), an(V) / (an(V) + bn(V))]

// ---- state ------------------------------------------------------------------
const ctl = reactive({ current: props.current, pulse: props.pulse, gates: props.gates })
const playing = ref(true)
const N = Math.round(props.window / SAMPLE)
let y = steady(V0)
let t = 0
let pulseUntil = -1
let sinceSample = 0
const buf = { V: new Float32Array(N).fill(V0), m: new Float32Array(N), h: new Float32Array(N), n: new Float32Array(N), I: new Float32Array(N) }
buf.m.fill(y[1]); buf.h.fill(y[2]); buf.n.fill(y[3])
let head = 0 // next write index
const frame = ref(0) // bumps every animation frame to redraw

function advance(ms) {
  const steps = Math.round(ms / DT)
  for (let s = 0; s < steps; s++) {
    const I = ctl.current + (t < pulseUntil ? ctl.pulse : 0)
    y = rk4(y, I)
    t += DT
    sinceSample += DT
    if (sinceSample >= SAMPLE - 1e-9) {
      sinceSample = 0
      buf.V[head] = y[0]; buf.m[head] = y[1]; buf.h[head] = y[2]; buf.n[head] = y[3]; buf.I[head] = I
      head = (head + 1) % N
    }
  }
}
function stimulate() { pulseUntil = t + PULSE_MS; if (!playing.value) playing.value = true }
function reset() {
  y = steady(V0); t = 0; pulseUntil = -1; ctl.current = 0
  buf.V.fill(V0); buf.m.fill(y[1]); buf.h.fill(y[2]); buf.n.fill(y[3]); buf.I.fill(0)
  frame.value++
}

// run only while visible
const root = ref(null)
let visible = false
let raf = 0
let lastTs = 0
function tick(ts) {
  raf = requestAnimationFrame(tick)
  const dt = lastTs ? Math.min(ts - lastTs, 50) : 16
  lastTs = ts
  if (!visible || !playing.value) return
  advance((dt / 1000) * props.speed)
  frame.value++
}
let io
onMounted(() => {
  io = new IntersectionObserver(([e]) => { visible = e.isIntersecting; lastTs = 0 })
  io.observe(root.value)
  raf = requestAnimationFrame(tick)
})
onUnmounted(() => { cancelAnimationFrame(raf); io?.disconnect() })

// ---- drawing -----------------------------------------------------------------
const W = 760
const PAD_L = 56
const PLOT_W = W - PAD_L - 10
const VH = 230 // voltage plot height
const V_MIN = -90, V_MAX = 60
const vy = V => 10 + ((V_MAX - V) / (V_MAX - V_MIN)) * VH
const GH = 90 // gate plot height
const GY0 = VH + 50
const gy = g => GY0 + (1 - g) * GH
const xAt = k => PAD_L + (k / (N - 1)) * PLOT_W
function line(arr, f) {
  void frame.value
  let s = ''
  for (let k = 0; k < N; k++) {
    const v = arr[(head + k) % N]
    s += `${xAt(k).toFixed(1)},${f(v).toFixed(1)} `
  }
  return s
}
const vLine = computed(() => line(buf.V, vy))
const mLine = computed(() => (ctl.gates ? line(buf.m, gy) : ''))
const hLine = computed(() => (ctl.gates ? line(buf.h, gy) : ''))
const nLine = computed(() => (ctl.gates ? line(buf.n, gy) : ''))
// stimulus marks along the bottom of the voltage plot
const stimSegs = computed(() => {
  void frame.value
  const segs = []
  let start = null
  for (let k = 0; k < N; k++) {
    const on = buf.I[(head + k) % N] > ctl.current + 1e-9
    if (on && start === null) start = k
    if ((!on || k === N - 1) && start !== null) { segs.push([xAt(start), xAt(k)]); start = null }
  }
  return segs
})
const spikes = computed(() => {
  void frame.value
  let c = 0
  for (let k = 1; k < N; k++) if (buf.V[(head + k - 1) % N] < 0 && buf.V[(head + k) % N] >= 0) c++
  return c
})
const vNow = computed(() => { void frame.value; return y[0] })
const height = computed(() => (ctl.gates ? GY0 + GH + 30 : VH + 40))
const TICKS = [-80, -40, 0, 40]
</script>

<template>
  <div ref="root" class="hh">
    <svg :viewBox="`0 0 ${W} ${height}`" class="hh-plot" role="img"
      aria-label="Membrane potential of a simulated Hodgkin-Huxley neuron over the last 100 milliseconds">
      <!-- voltage axes -->
      <line :x1="PAD_L" :y1="vy(V_MAX)" :x2="PAD_L" :y2="vy(V_MIN)" class="axis" />
      <g v-for="v in TICKS" :key="v">
        <line :x1="PAD_L - 5" :y1="vy(v)" :x2="PAD_L" :y2="vy(v)" class="axis" />
        <text :x="PAD_L - 9" :y="vy(v)" class="tick">{{ v }}</text>
      </g>
      <line :x1="PAD_L" :y1="vy(V0)" :x2="PAD_L + PLOT_W" :y2="vy(V0)" class="rest" />
      <line :x1="PAD_L" :y1="vy(0)" :x2="PAD_L + PLOT_W" :y2="vy(0)" class="zero" />
      <text :x="14" :y="vy(-15)" class="ylab" :transform="`rotate(-90 14 ${vy(-15)})`">mV</text>
      <rect v-for="(s, i) in stimSegs" :key="'s' + i" :x="s[0]" :y="vy(V_MIN) + 2" :width="Math.max(2, s[1] - s[0])"
        height="6" class="stim" />
      <polyline :points="vLine" class="trace v" />
      <text :x="PAD_L + PLOT_W" :y="vy(V_MIN) + 24" class="xlab">last {{ window }} ms</text>

      <!-- gates -->
      <g v-if="ctl.gates">
        <line :x1="PAD_L" :y1="gy(1)" :x2="PAD_L" :y2="gy(0)" class="axis" />
        <text :x="PAD_L - 9" :y="gy(1)" class="tick">1</text>
        <text :x="PAD_L - 9" :y="gy(0)" class="tick">0</text>
        <polyline :points="mLine" class="trace m" />
        <polyline :points="hLine" class="trace h" />
        <polyline :points="nLine" class="trace n" />
        <text :x="PAD_L + 8" :y="gy(0) + 22" class="key m">m (Na⁺ opens)</text>
        <text :x="PAD_L + 150" :y="gy(0) + 22" class="key h">h (Na⁺ inactivates)</text>
        <text :x="PAD_L + 330" :y="gy(0) + 22" class="key n">n (K⁺ opens)</text>
      </g>
    </svg>

    <div class="hh-controls">
      <button class="primary" @click="stimulate">⚡ Stimulate</button>
      <label>pulse <input v-model.number="ctl.pulse" type="range" min="0" max="30" step="0.5"> <b>{{ ctl.pulse.toFixed(1) }}</b></label>
      <label>steady current <input v-model.number="ctl.current" type="range" min="0" max="20" step="0.1"> <b>{{ ctl.current.toFixed(1) }}</b> µA/cm²</label>
    </div>
    <div class="hh-controls small">
      <button @click="playing = !playing">{{ playing ? '⏸ Pause' : '▶ Play' }}</button>
      <button @click="reset">⏮ Reset</button>
      <label><input v-model="ctl.gates" type="checkbox"> show gates</label>
      <span class="readout">{{ vNow.toFixed(1) }} mV · {{ spikes }} spike{{ spikes === 1 ? '' : 's' }} on screen</span>
    </div>
  </div>
</template>

<style scoped>
.hh { width: 100%; }
.hh-plot { width: 100%; max-height: 290px; display: block; }
.axis { stroke: var(--fenbrook-fg, currentColor); stroke-width: 1.2; }
.rest { stroke: var(--fenbrook-muted, #888); stroke-dasharray: 4 5; stroke-width: 1; }
.zero { stroke: var(--fenbrook-rule, #444); stroke-width: 1; }
.tick { fill: var(--fenbrook-muted, #999); font-size: 13px; text-anchor: end; dominant-baseline: middle; }
.ylab, .xlab { fill: var(--fenbrook-muted, #999); font-size: 13px; }
.ylab { text-anchor: middle; }
.xlab { text-anchor: end; }
.trace { fill: none; stroke-width: 2; stroke-linejoin: round; }
.trace.v { stroke: var(--fenbrook-accent, orange); stroke-width: 2.5; }
.trace.m, .key.m { stroke: #8ec5e8; fill: none; }
.trace.h, .key.h { stroke: #e88e8e; }
.trace.n, .key.n { stroke: #a8d89a; }
.key { font-size: 13px; stroke: none !important; }
.key.m { fill: #8ec5e8; }
.key.h { fill: #e88e8e; }
.key.n { fill: #a8d89a; }
.stim { fill: var(--fenbrook-fg, currentColor); opacity: 0.8; }

.hh-controls {
  display: flex; flex-wrap: wrap; gap: 0.6rem 1.2rem; align-items: center; justify-content: center;
  margin-top: 0.4rem; font-size: 0.9rem; color: var(--fenbrook-fg-soft, currentColor);
}
.hh-controls.small { font-size: 0.8rem; }
.hh-controls label { display: inline-flex; align-items: center; gap: 0.4rem; }
.hh-controls b { color: var(--fenbrook-fg, currentColor); font-weight: 500; min-width: 3ch; font-variant-numeric: tabular-nums; }
.hh-controls input[type="range"] { width: 130px; accent-color: var(--fenbrook-accent, orange); }
.hh-controls input[type="checkbox"] { accent-color: var(--fenbrook-accent, orange); }
.hh-controls button {
  font: inherit; padding: 0.25rem 0.75rem; border-radius: 6px; cursor: pointer;
  background: transparent; color: var(--fenbrook-fg, currentColor); border: 1px solid var(--fenbrook-rule, #555);
}
.hh-controls button:hover { border-color: var(--fenbrook-accent, orange); }
.hh-controls button.primary { border-color: var(--fenbrook-accent, orange); color: var(--fenbrook-accent, orange); }
.readout { font-family: 'JetBrains Mono', monospace; color: var(--fenbrook-muted, #999); font-variant-numeric: tabular-nums; }
</style>
