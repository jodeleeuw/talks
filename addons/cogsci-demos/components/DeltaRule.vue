<script setup>
// A one-layer pattern associator trained with the delta rule,
//   Δw_ij = learningRate × (desired_j − output_j) × input_i,
// drawn the way the COGS 319 slides draw it: input units along the bottom,
// output units on top, and each output's incoming weights in a row of small
// cells under it. Outputs are linear (the weighted sum of the inputs).
//
//   <DeltaRule :inputs="[1, 1, -1, -1]" :desired="[1, -1, -1, 1]" />
//   <DeltaRule :weights="[[1, .5, 1, 1], [-1, -1, .5, .5]]" :desired="null" :show-outputs="$clicks >= 1" :controls="false" />
//   <DeltaRule :desired="[1, -1, -1, 1]" :step="$clicks" :controls="false" />
//
// With :step, the network shows the weights after that many updates (one
// update = one pass of the rule over every weight). Otherwise the buttons
// apply updates. Click an input or a desired value to flip its sign.
import { computed, ref, watch } from 'vue'

const props = defineProps({
  inputs: { type: Array, default: () => [1, 1, -1, -1] },
  desired: { type: Array, default: () => [1, -1, -1, 1] }, // null hides the row
  weights: { type: Array, default: null }, // [output][input]; default all 0
  lr: { type: Number, default: 0.25 },
  step: { type: Number, default: undefined },
  showOutputs: { type: Boolean, default: true },
  controls: { type: Boolean, default: true },
  showLr: { type: Boolean, default: true },
})

const nIn = computed(() => x.value.length)
const nOut = computed(() => (props.weights ? props.weights.length : (props.desired?.length ?? 4)))
const x = ref([...props.inputs])
const target = ref(props.desired ? [...props.desired] : null)
const start = () => (props.weights ? props.weights.map(r => [...r]) : Array.from({ length: nOut.value }, () => new Array(props.inputs.length).fill(0)))
let history = [start()] // plain array: weights after 0, 1, 2, … updates
const version = ref(0) // bumped whenever history is rebuilt
const updates = ref(0)

const out = (W, j) => W[j].reduce((s, w, i) => s + w * x.value[i], 0)
function applyOnce(W) {
  return W.map((row, j) => {
    const err = (target.value?.[j] ?? 0) - out(W, j)
    return row.map((w, i) => +(w + props.lr * err * x.value[i]).toFixed(6))
  })
}
const shown = computed(() => props.step ?? updates.value)
const W = computed(() => {
  version.value // eslint-disable-line no-unused-expressions
  while (history.length <= shown.value) history.push(applyOnce(history.at(-1)))
  return history[shown.value]
})
const prevW = computed(() => (W.value, shown.value > 0 ? history[shown.value - 1] : null))
const outputs = computed(() => W.value.map((_, j) => out(W.value, j)))
const sse = computed(() => (target.value ? outputs.value.reduce((s, o, j) => s + (target.value[j] - o) ** 2, 0) : null))

function rebuild() { history = [start()]; version.value++ }
watch(() => [props.weights, props.inputs], () => { x.value = [...props.inputs]; rebuild() }, { deep: true })
function flipInput(i) { x.value[i] = -x.value[i]; rebuild(); if (props.step === undefined) updates.value = 0 }
function flipTarget(j) { if (!target.value) return; target.value[j] = -target.value[j]; rebuild(); if (props.step === undefined) updates.value = 0 }
function reset() { updates.value = 0; x.value = [...props.inputs]; target.value = props.desired ? [...props.desired] : null; rebuild() }

// ---- geometry ----------------------------------------------------------------
const BW = 132, CH = 28, GAP = 22
const totalW = computed(() => Math.max(nOut.value, nIn.value) * (BW + GAP) - GAP)
const outX = j => j * (BW + GAP)
const inX = i => i * (BW + GAP)
const Y_DES = 16, Y_OUT = 34, OH = 46, Y_IN = 250, IH = 46
const cellW = computed(() => BW / nIn.value)
const cellX = (j, i) => outX(j) + i * cellW.value
const fmt = v => {
  const r = Math.round(v * 1000) / 1000
  if (Object.is(r, -0) || r === 0) return '0'
  const s = String(r)
  return s.replace(/^0\./, '.').replace(/^-0\./, '-.')
}
const changed = (j, i) => prevW.value && Math.abs(prevW.value[j][i] - W.value[j][i]) > 1e-9
</script>

<template>
  <div class="dr">
    <svg :viewBox="`-80 0 ${totalW + 90} ${Y_IN + IH + 6}`" class="dr-net" role="img" aria-label="Pattern associator: inputs, weights and outputs">
      <!-- connections: input i → weight cell i of every output -->
      <g class="links">
        <template v-for="(_, j) in W" :key="'l' + j">
          <line v-for="(_, i) in x" :key="i" :x1="inX(i) + BW / 2" :y1="Y_IN" :x2="cellX(j, i) + cellW / 2" :y2="Y_OUT + OH + CH" />
        </template>
      </g>
      <text v-if="target" x="-12" :y="Y_DES + 4" class="cd-label" text-anchor="end">Desired:</text>
      <g v-for="(_, j) in W" :key="j">
        <text v-if="target" :x="outX(j) + BW / 2" :y="Y_DES + 4" class="des" text-anchor="middle" @click="flipTarget(j)">{{ target[j] }}</text>
        <rect :x="outX(j)" :y="Y_OUT" :width="BW" :height="OH" class="box" :class="{ hit: target && showOutputs && Math.abs(target[j] - outputs[j]) < 1e-9 }" />
        <text :x="outX(j) + BW / 2" :y="Y_OUT + OH / 2 + 7" class="val" text-anchor="middle">{{ showOutputs ? fmt(outputs[j]) : '?' }}</text>
        <g v-for="(w, i) in W[j]" :key="i">
          <rect :x="cellX(j, i)" :y="Y_OUT + OH" :width="cellW" :height="CH" class="cell" :class="{ changed: changed(j, i) }" />
          <text :x="cellX(j, i) + cellW / 2" :y="Y_OUT + OH + CH / 2 + 5" class="w" text-anchor="middle">{{ fmt(w) }}</text>
        </g>
      </g>
      <g v-for="(v, i) in x" :key="'in' + i" class="input" @click="flipInput(i)">
        <rect :x="inX(i)" :y="Y_IN" :width="BW" :height="IH" class="box" />
        <text :x="inX(i) + BW / 2" :y="Y_IN + IH / 2 + 7" class="val" text-anchor="middle">{{ v }}</text>
      </g>
    </svg>
    <div class="cd-controls dr-controls">
      <template v-if="controls">
        <button class="cd-btn primary" @click="updates++">Apply delta rule</button>
        <button class="cd-btn" @click="reset">Reset</button>
        <span>updates: <b class="cd-num">{{ shown }}</b></span>
      </template>
      <span v-if="showLr">learningRate = {{ lr }}</span>
      <span v-if="controls && sse !== null">squared error: <b class="cd-num">{{ fmt(sse) }}</b></span>
    </div>
  </div>
</template>

<style scoped>
.dr { display: flex; flex-direction: column; gap: 0.5rem; width: 100%; }
.dr-net { width: 100%; max-height: 330px; }
.links line { stroke: var(--fenbrook-fg-soft, #bbb); stroke-width: 1; opacity: 0.7; }
.box { fill: var(--fenbrook-bg, #111); stroke: var(--fenbrook-fg, #eee); stroke-width: 1.6; }
.box.hit { stroke: var(--fenbrook-accent, orange); stroke-width: 2.4; }
.cell { fill: var(--fenbrook-bg, #111); stroke: var(--fenbrook-fg, #eee); stroke-width: 1; transition: fill 0.3s; }
.cell.changed { fill: color-mix(in srgb, var(--fenbrook-accent, orange) 28%, transparent); }
.val { fill: var(--fenbrook-fg, #eee); font-size: 22px; font-family: 'JetBrains Mono', monospace; }
.w { fill: var(--fenbrook-fg, #eee); font-size: 12px; font-family: 'JetBrains Mono', monospace; }
.des { fill: var(--fenbrook-fg, #eee); font-size: 18px; font-family: 'JetBrains Mono', monospace; cursor: pointer; }
.input { cursor: pointer; }
.dr-controls { justify-content: flex-end; }
</style>
