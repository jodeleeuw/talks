<script setup>
// A one-unit perceptron with two inputs, for showing what a single straight
// line can and can't separate.
//
//   <PerceptronPlayground problem="xor" />
//
// Sliders set w₁, w₂ and the bias b; the unit outputs 1 where
// w₁x₁ + w₂x₂ + b ≥ 0 (shaded) and 0 elsewhere. Points are the four input
// patterns, coloured by the answer we want; a red ring marks each one the
// current weights get wrong. "Try every setting" sweeps a grid of weights
// and reports the best score any line can get (4 of 4 for AND and OR,
// 3 of 4 for XOR), and "Train" runs the perceptron learning rule, which
// settles on AND and OR and cycles forever on XOR.
import { computed, onUnmounted, reactive, ref } from 'vue'

const props = defineProps({
  problem: { type: String, default: 'xor' }, // 'and' | 'or' | 'xor'
  problems: { type: Array, default: () => ['and', 'or', 'xor'] }, // buttons shown
  w1: { type: Number, default: 1 },
  w2: { type: Number, default: 1 },
  b: { type: Number, default: -0.5 },
})

const TARGETS = {
  and: [0, 0, 0, 1],
  or: [0, 1, 1, 1],
  xor: [0, 1, 1, 0],
}
const NAMES = { and: 'AND', or: 'OR', xor: 'XOR' }
const INPUTS = [[0, 0], [0, 1], [1, 0], [1, 1]]

const p = reactive({ w1: props.w1, w2: props.w2, b: props.b, problem: props.problem })
const net = (x, w = p) => w.w1 * x[0] + w.w2 * x[1] + w.b
const out = (x, w = p) => (net(x, w) >= 0 ? 1 : 0)
const targets = computed(() => TARGETS[p.problem])
const points = computed(() => INPUTS.map((x, i) => ({ x, t: targets.value[i], ok: out(x) === targets.value[i] })))
const correct = computed(() => points.value.filter(q => q.ok).length)

// ---- plot geometry: data space [-0.5, 1.5]² ------------------------------
const S = 360
const PAD = 34
const LO = -0.5, HI = 1.5
const sx = v => PAD + ((v - LO) / (HI - LO)) * S
const sy = v => PAD + ((HI - v) / (HI - LO)) * S
// the part of the plot where the unit outputs 1, as a polygon
const region = computed(() => {
  const box = [[LO, LO], [HI, LO], [HI, HI], [LO, HI]]
  const inside = q => net(q) >= 0
  const outPts = []
  for (let i = 0; i < box.length; i++) {
    const a = box[i], c = box[(i + 1) % box.length]
    const ia = inside(a), ic = inside(c)
    if (ia) outPts.push(a)
    if (ia !== ic) {
      const fa = net(a), fc = net(c)
      const t = fa / (fa - fc)
      outPts.push([a[0] + t * (c[0] - a[0]), a[1] + t * (c[1] - a[1])])
    }
  }
  return outPts.map(q => `${sx(q[0])},${sy(q[1])}`).join(' ')
})
// the boundary line w₁x + w₂y + b = 0, clipped to the plot
const boundary = computed(() => {
  const { w1, w2, b } = p
  const pts = []
  if (Math.abs(w2) > 1e-9) for (const x of [LO, HI]) pts.push([x, -(w1 * x + b) / w2])
  if (Math.abs(w1) > 1e-9) for (const y of [LO, HI]) pts.push([-(w2 * y + b) / w1, y])
  const ins = pts.filter(([x, y]) => x >= LO - 1e-9 && x <= HI + 1e-9 && y >= LO - 1e-9 && y <= HI + 1e-9)
  if (ins.length < 2) return null
  ins.sort((a, c) => a[0] - c[0] || a[1] - c[1])
  const [a, c] = [ins[0], ins[ins.length - 1]]
  return { x1: sx(a[0]), y1: sy(a[1]), x2: sx(c[0]), y2: sy(c[1]) }
})

// ---- exhaustive search ---------------------------------------------------
const best = ref(null) // { problem, score }
function search() {
  stopTrain()
  let top = -1, arg = null
  const G = []
  for (let v = -3; v <= 3.0001; v += 0.25) G.push(+v.toFixed(2))
  for (const w1 of G) for (const w2 of G) for (const b of G) {
    const w = { w1, w2, b }
    const s = INPUTS.filter((x, i) => out(x, w) === targets.value[i]).length
    if (s > top) { top = s; arg = w }
  }
  best.value = { problem: p.problem, score: top, tried: G.length ** 3 }
  Object.assign(p, arg)
}
const bestNote = computed(() => (best.value && best.value.problem === p.problem ? best.value : null))

// ---- perceptron learning rule --------------------------------------------
const training = ref(false)
const epoch = ref(0)
const lastErrors = ref(null)
let timer = null
const LR = 0.25
function trainEpoch() {
  let errs = 0
  INPUTS.forEach((x, i) => {
    const e = targets.value[i] - out(x)
    if (e !== 0) {
      errs++
      p.w1 = +(p.w1 + LR * e * x[0]).toFixed(2)
      p.w2 = +(p.w2 + LR * e * x[1]).toFixed(2)
      p.b = +(p.b + LR * e).toFixed(2)
    }
  })
  epoch.value++
  lastErrors.value = errs
  if (errs === 0) stopTrain()
}
function startTrain() {
  if (training.value) return stopTrain()
  best.value = null
  epoch.value = 0
  lastErrors.value = null
  training.value = true
  timer = setInterval(trainEpoch, 450)
}
function stopTrain() { training.value = false; clearInterval(timer) }
onUnmounted(stopTrain)
function pick(name) { stopTrain(); best.value = null; p.problem = name; epoch.value = 0; lastErrors.value = null }
function reset() { stopTrain(); best.value = null; Object.assign(p, { w1: props.w1, w2: props.w2, b: props.b }); epoch.value = 0; lastErrors.value = null }
const fmt = v => (v >= 0 ? ' ' : '') + v.toFixed(2)
</script>

<template>
  <div class="pp">
    <svg :viewBox="`-46 0 ${S + 2 * PAD + 46} ${S + 2 * PAD}`" class="pp-plot" role="img"
      :aria-label="`Plot of the four input patterns for ${NAMES[p.problem]}, with the perceptron's decision boundary`">
      <rect :x="PAD" :y="PAD" :width="S" :height="S" class="frame" />
      <polygon v-if="region" :points="region" class="on-region" />
      <line v-if="boundary" v-bind="boundary" class="boundary" />
      <line :x1="sx(0)" :y1="sy(LO)" :x2="sx(0)" :y2="sy(HI)" class="axis" />
      <line :x1="sx(LO)" :y1="sy(0)" :x2="sx(HI)" :y2="sy(0)" class="axis" />
      <text :x="sx(1)" :y="sy(LO) + 22" class="tick">x₁ = 1</text>
      <text :x="sx(0)" :y="sy(LO) + 22" class="tick">0</text>
      <text :x="sx(LO) - 8" :y="sy(1)" class="tick end">x₂ = 1</text>
      <g v-for="(q, i) in points" :key="i">
        <circle v-if="!q.ok" :cx="sx(q.x[0])" :cy="sy(q.x[1])" r="24" class="wrong" />
        <circle :cx="sx(q.x[0])" :cy="sy(q.x[1])" r="15" :class="q.t ? 'one' : 'zero'" />
        <text :x="sx(q.x[0])" :y="sy(q.x[1]) + 1" class="pt" :class="q.t ? 'one' : 'zero'">{{ q.t }}</text>
      </g>
    </svg>

    <div class="pp-side">
      <div v-if="problems.length > 1" class="pp-tabs">
        <button v-for="n in problems" :key="n" :class="{ on: p.problem === n }" @click="pick(n)">{{ NAMES[n] }}</button>
      </div>
      <p class="pp-rule">output 1 if w₁x₁ + w₂x₂ + b ≥ 0</p>
      <label><span>w₁</span><input v-model.number="p.w1" type="range" min="-3" max="3" step="0.05"><b>{{ fmt(p.w1) }}</b></label>
      <label><span>w₂</span><input v-model.number="p.w2" type="range" min="-3" max="3" step="0.05"><b>{{ fmt(p.w2) }}</b></label>
      <label><span>b</span><input v-model.number="p.b" type="range" min="-3" max="3" step="0.05"><b>{{ fmt(p.b) }}</b></label>
      <p class="pp-score" :class="{ perfect: correct === 4 }">{{ correct }} of 4 correct</p>
      <div class="pp-buttons">
        <button @click="search">Try every setting</button>
        <button @click="startTrain">{{ training ? '⏸ Stop' : 'Train' }}</button>
        <button @click="reset">Reset</button>
      </div>
      <p v-if="bestNote" class="pp-note">
        Best of {{ bestNote.tried.toLocaleString() }} settings: <b>{{ bestNote.score }} of 4</b>.
        <template v-if="bestNote.score < 4">No straight line separates {{ NAMES[p.problem] }}.</template>
      </p>
      <p v-else-if="epoch" class="pp-note">
        Epoch {{ epoch }}: {{ lastErrors }} error{{ lastErrors === 1 ? '' : 's' }}<template v-if="lastErrors === 0">, learned it</template>
      </p>
    </div>
  </div>
</template>

<style scoped>
.pp { display: grid; grid-template-columns: minmax(0, 1fr) minmax(0, 0.9fr); gap: 2rem; align-items: center; width: 100%; }
.pp-plot { width: 100%; max-height: 400px; display: block; }
.frame { fill: none; stroke: var(--fenbrook-rule, #444); }
.on-region { fill: color-mix(in srgb, var(--fenbrook-accent, orange) 18%, transparent); }
.boundary { stroke: var(--fenbrook-accent, orange); stroke-width: 2.5; }
.axis { stroke: var(--fenbrook-muted, #888); stroke-width: 1; }
.tick { fill: var(--fenbrook-muted, #999); font-size: 13px; text-anchor: middle; }
.tick.end { text-anchor: end; dominant-baseline: middle; }
circle.zero { fill: var(--fenbrook-bg, #111); stroke: var(--fenbrook-fg, currentColor); stroke-width: 2; }
circle.one { fill: var(--fenbrook-fg, currentColor); }
.pt { font-family: 'JetBrains Mono', monospace; font-size: 14px; text-anchor: middle; dominant-baseline: middle; }
.pt.zero { fill: var(--fenbrook-fg, currentColor); }
.pt.one { fill: var(--fenbrook-bg, #111); }
.wrong { fill: none; stroke: #e06c6c; stroke-width: 3; stroke-dasharray: 5 4; }

.pp-side { display: flex; flex-direction: column; gap: 0.55rem; font-size: 0.95rem; }
.pp-side p { margin: 0; }
.pp-rule { font-family: 'JetBrains Mono', monospace; font-size: 0.85rem; color: var(--fenbrook-fg-soft, currentColor); }
.pp-side label { display: grid; grid-template-columns: 2.2em 1fr 3.8em; align-items: center; gap: 0.6rem; }
.pp-side label span { font-style: italic; }
.pp-side label b { font-family: 'JetBrains Mono', monospace; font-weight: 400; white-space: pre; text-align: right; }
.pp-side input[type="range"] { width: 100%; accent-color: var(--fenbrook-accent, orange); }
.pp-score { font-size: 1.25rem; font-weight: 600; }
.pp-score.perfect { color: var(--fenbrook-accent, orange); }
.pp-note { font-size: 0.85rem; color: var(--fenbrook-fg-soft, currentColor); }
.pp-note b { color: var(--fenbrook-fg, currentColor); }
.pp-tabs, .pp-buttons { display: flex; gap: 0.4rem; flex-wrap: wrap; }
.pp-side button {
  font: inherit; font-size: 0.85rem; padding: 0.25rem 0.7rem; border-radius: 6px; cursor: pointer;
  background: transparent; color: var(--fenbrook-fg, currentColor); border: 1px solid var(--fenbrook-rule, #555);
}
.pp-side button:hover { border-color: var(--fenbrook-accent, orange); }
.pp-tabs button.on { border-color: var(--fenbrook-accent, orange); color: var(--fenbrook-accent, orange); }
</style>
