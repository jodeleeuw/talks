<script setup>
// What one training step does: take a batch of training examples, run them
// forward through the network, compare the predictions with the targets
// (the loss), and backpropagate. A pass over every example is one epoch.
//
//   <TrainingBatches :step="$clicks" :batch-size="1" phases />
//   <TrainingBatches :batch-size="3" />          buttons, no diagram clicks
//
// The strip shows the training set; the current batch is lit. With
// `phases`, each batch takes two steps (forward, then backprop); otherwise
// one. `loop` toggles the network diagram under the strip.
import { computed, onUnmounted, ref, watch } from 'vue'

const props = defineProps({
  n: { type: Number, default: 13 },
  batchSize: { type: Number, default: 1 },
  step: { type: Number, default: undefined }, // 0 = whole training set lit
  phases: { type: Boolean, default: false },
  loop: { type: Boolean, default: true },
  controls: { type: Boolean, default: true },
})

const bs = ref(props.batchSize)
watch(() => props.batchSize, v => { bs.value = v })
const own = ref(0)
const k = computed(() => props.step ?? own.value)
const perBatch = computed(() => (props.phases ? 2 : 1))
const nb = computed(() => Math.ceil(props.n / bs.value))
const batch = computed(() => (k.value > 0 ? Math.floor((k.value - 1) / perBatch.value) % nb.value : -1))
const epoch = computed(() => (k.value > 0 ? Math.floor((k.value - 1) / perBatch.value / nb.value) + 1 : 0))
const backprop = computed(() => k.value > 0 && (!props.phases || (k.value - 1) % 2 === 1))
const lit = i => batch.value < 0 || Math.floor(i / bs.value) === batch.value

let timer = null
const running = ref(false)
function run() {
  if (running.value) { running.value = false; return clearInterval(timer) }
  running.value = true
  timer = setInterval(() => own.value++, 500)
}
onUnmounted(() => clearInterval(timer))
function setBs(v) { bs.value = v; own.value = 0 }

const W = 860, CELL = W / props.n
const BX = computed(() => (batch.value < 0 ? 0 : batch.value * bs.value * CELL + 4))
</script>

<template>
  <div class="tb">
    <svg :viewBox="`0 0 ${W} ${loop ? 250 : 50}`" class="tb-svg" role="img" aria-label="Training set split into batches, with the forward pass and backprop">
      <rect v-for="i in n" :key="i" :x="(i - 1) * CELL + 2" y="4" :width="CELL - 4" height="40" rx="5" :class="['ex', { lit: lit(i - 1) }]" />
      <g v-if="loop && batch >= 0" class="loop">
        <path :d="`M${BX + 10},44 V160 H340`" class="flow" marker-end="url(#tb-a)" />
        <text x="320" y="152" class="lbl" text-anchor="end">x (input data)</text>
        <rect x="340" y="132" width="220" height="56" class="net" />
        <text x="450" y="157" class="netl" text-anchor="middle">fancy neural network</text>
        <line x1="380" y1="172" x2="520" y2="172" class="flow" marker-end="url(#tb-a)" />
        <path d="M560,160 H668" class="flow" marker-end="url(#tb-a)" />
        <text x="614" y="152" class="lbl" text-anchor="middle">y' (prediction)</text>
        <rect x="668" y="140" width="44" height="40" class="loss" />
        <text x="690" y="164" class="lbl" text-anchor="middle">loss</text>
        <path :d="`M${BX + bs * CELL - 16},44 V100 H${W - 30} V160 H712`" class="flow" marker-end="url(#tb-a)" />
        <text :x="W - 36" y="152" class="lbl" text-anchor="end">y (target output)</text>
        <path v-if="backprop" d="M690,180 V222 H450 V190" class="bp" marker-end="url(#tb-b)" />
        <text v-if="backprop" x="570" y="240" class="bpl" text-anchor="middle">backprop</text>
      </g>
      <defs>
        <marker id="tb-a" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto"><path d="M0,0 L10,5 L0,10 z" class="ah" /></marker>
        <marker id="tb-b" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto"><path d="M0,0 L10,5 L0,10 z" class="ahb" /></marker>
      </defs>
    </svg>
    <div class="cd-controls tb-controls">
      <template v-if="controls">
        <span>batch size</span>
        <button v-for="v in [1, 3, n]" :key="v" class="cd-btn" :class="{ on: bs === v }" @click="setBs(v)">{{ v === n ? 'all' : v }}</button>
        <button class="cd-btn" @click="own++">Step</button>
        <button class="cd-btn primary" @click="run">{{ running ? 'Pause' : 'Run' }}</button>
      </template>
      <span v-if="epoch">epoch <b class="cd-num">{{ epoch }}</b> · batch <b class="cd-num">{{ batch + 1 }}</b> of {{ nb }} · backprop runs <b class="cd-num">{{ Math.floor(k / perBatch) }}</b></span>
    </div>
  </div>
</template>

<style scoped>
.tb { display: flex; flex-direction: column; gap: 0.6rem; width: 100%; }
.tb-svg { width: 100%; }
.ex { fill: #3a3836; transition: fill 0.25s; }
.ex.lit { fill: #dcdcdc; }
.flow { fill: none; stroke: #a8c8f0; stroke-width: 1.6; }
.ah { fill: #a8c8f0; }
.net { fill: none; stroke: #a8c8f0; stroke-width: 1.8; }
.netl { fill: #a8c8f0; font-size: 15px; }
.loss { fill: none; stroke: #a8c8f0; stroke-width: 1.6; }
.lbl { fill: #a8c8f0; font-size: 12px; }
.bp { fill: none; stroke: #f0b070; stroke-width: 2.2; }
.ahb { fill: #f0b070; }
.bpl { fill: #f0b070; font-size: 14px; }
.tb-controls { justify-content: center; }
</style>
