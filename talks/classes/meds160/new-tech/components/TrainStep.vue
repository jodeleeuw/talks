<script setup>
// One-word training demo. Each "learning step" is a real gradient step on the
// cross-entropy loss with respect to the logits: logit_i -= lr * (p_i - y_i).
import { computed, ref } from 'vue'

const props = defineProps({
  prompt: { type: String, default: 'The capital of France is' },
  answer: { type: String, default: 'Paris' },
  // Illustrative starting probabilities for an untrained-ish model.
  start: {
    type: Array,
    default: () => [
      ['the', 0.24], ['a', 0.19], ['located', 0.15], ['beautiful', 0.13],
      ['Paris', 0.08], ['not', 0.07], ['Lyon', 0.06], ['banana', 0.04], ['very', 0.04],
    ],
  },
  lr: { type: Number, default: 0.6 },
})

const words = props.start.map(([w]) => w)
const initLogits = () => props.start.map(([, p]) => Math.log(p))
const logits = ref(initLogits())
const steps = ref(0)

const probs = computed(() => {
  const m = Math.max(...logits.value)
  const e = logits.value.map(l => Math.exp(l - m))
  const z = e.reduce((a, b) => a + b, 0)
  return e.map(x => x / z)
})
const pAnswer = computed(() => probs.value[words.indexOf(props.answer)])
const guess = computed(() => words[probs.value.indexOf(Math.max(...probs.value))])

function learn() {
  const p = probs.value
  logits.value = logits.value.map((l, i) => l - props.lr * (p[i] - (words[i] === props.answer ? 1 : 0)))
  steps.value++
}
function reset() {
  logits.value = initLogits()
  steps.value = 0
}
const blur = e => e.currentTarget.blur()
</script>

<template>
  <div class="ts">
    <p class="prompt">{{ prompt }} <span class="guess">{{ guess }}</span></p>

    <div class="bars">
      <div v-for="(w, i) in words" :key="w" class="row" :class="{ ans: w === answer }">
        <span class="word">{{ w }}<span v-if="w === answer" class="tick"> ✓</span></span>
        <span class="track"><span class="fill" :style="{ width: probs[i] * 100 + '%' }" /></span>
        <span class="pct">{{ (probs[i] * 100).toFixed(0) }}%</span>
      </div>
    </div>

    <div class="controls">
      <button @click="learn(); blur($event)">Learning step</button>
      <button class="ghost" @click="reset(); blur($event)">Reset</button>
      <span class="stat">steps: <b>{{ steps }}</b> · P({{ answer }}) = <b>{{ (pAnswer * 100).toFixed(0) }}%</b></span>
    </div>
  </div>
</template>

<style scoped>
.ts { font-size: 0.95rem; }
.prompt { font-size: 1.5rem; margin: 0 0 1rem; color: var(--fenbrook-fg); }
.guess { color: var(--fenbrook-accent); text-decoration: underline; text-decoration-thickness: 2px; text-underline-offset: 0.2em; }
.bars { display: grid; gap: 0.3rem; max-width: 40rem; }
.row { display: grid; grid-template-columns: 8.5rem 1fr 3rem; align-items: center; gap: 0.8rem; }
.word { text-align: right; color: var(--fenbrook-fg-soft); }
.track { height: 1rem; background: var(--fenbrook-bg-elev); border-radius: 3px; overflow: hidden; }
.fill { display: block; height: 100%; background: var(--fenbrook-fg-soft); opacity: 0.45; transition: width 0.45s ease; }
.row.ans .fill { background: var(--fenbrook-accent); opacity: 1; }
.row.ans .word { color: var(--fenbrook-accent); font-weight: 600; }
.tick { color: var(--fenbrook-accent); }
.pct { font-family: 'JetBrains Mono', monospace; font-size: 0.8rem; color: var(--fenbrook-muted); }
.controls { display: flex; align-items: center; gap: 1rem; margin-top: 1rem; }
.stat { font-family: 'JetBrains Mono', monospace; font-size: 0.8rem; color: var(--fenbrook-fg-soft); }
.stat b { color: var(--fenbrook-fg); }
button {
  font: inherit; font-size: 0.85rem; cursor: pointer;
  padding: 0.35rem 0.9rem; border-radius: 6px;
  border: 1px solid var(--fenbrook-accent); background: var(--fenbrook-accent); color: var(--fenbrook-bg);
}
button.ghost { background: transparent; color: var(--fenbrook-fg-soft); border-color: var(--fenbrook-rule); }
</style>
