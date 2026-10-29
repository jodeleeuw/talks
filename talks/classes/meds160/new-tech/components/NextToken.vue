<script setup>
// Next-token prediction demo: reveal a (made-up) probability distribution,
// reshape it with a temperature slider, and sample from it. The slide drives
// the reveal (`:revealed="$clicks > 0"`) so a normal advance shows the bars.
import { computed, ref } from 'vue'

const props = defineProps({
  revealed: { type: Boolean, default: false },
  prompt: { type: String, default: 'Every morning, the first thing I check is my' },
  // Illustrative base probabilities (T = 1). Normalized on use.
  options: {
    type: Array,
    default: () => [
      ['phone', 0.46], ['email', 0.21], ['messages', 0.09], ['calendar', 0.06],
      ['horoscope', 0.03], ['bank account', 0.02],
    ],
  },
})

const temperature = ref(1)
const picked = ref(null)
const history = ref([])

// p_i(T) ∝ p_i^(1/T): T < 1 sharpens toward the favorite, T > 1 flattens.
const dist = computed(() => {
  const w = props.options.map(([, p]) => Math.pow(p, 1 / temperature.value))
  const z = w.reduce((a, b) => a + b, 0)
  return props.options.map(([word], i) => ({ word, p: w[i] / z }))
})
const maxP = computed(() => Math.max(...dist.value.map(d => d.p)))

function sample() {
  let r = Math.random()
  for (const d of dist.value) {
    r -= d.p
    if (r <= 0) return finish(d.word)
  }
  finish(dist.value.at(-1).word)
}
function finish(word) {
  picked.value = word
  history.value = [word, ...history.value].slice(0, 8)
}
function reset() {
  picked.value = null
  history.value = []
  temperature.value = 1
}
// Keep keyboard focus off controls so Slidev's arrow/space shortcuts keep working.
const blur = e => e.currentTarget.blur()
</script>

<template>
  <div class="nt">
    <p class="prompt">
      {{ prompt }}
      <span class="slot" :class="{ filled: picked }">{{ picked ?? '___' }}</span>
    </p>

    <p v-if="!revealed" class="hint">What's the next word? Shout it out.</p>

    <template v-else>
      <div class="bars">
        <div v-for="d in dist" :key="d.word" class="row" :class="{ hit: d.word === picked }">
          <span class="word">{{ d.word }}</span>
          <span class="track"><span class="fill" :style="{ width: (d.p / maxP) * 100 + '%' }" /></span>
          <span class="pct">{{ d.p < 0.001 ? '<0.1' : (d.p * 100).toFixed(d.p < 0.01 ? 1 : 0) }}%</span>
        </div>
      </div>

      <div class="controls">
        <label>
          temperature <b>{{ temperature.toFixed(1) }}</b>
          <input v-model.number="temperature" type="range" min="0.2" max="2.5" step="0.1" @change="blur">
        </label>
        <button @click="sample(); blur($event)">Sample a word</button>
        <button class="ghost" @click="reset(); blur($event)">Reset</button>
      </div>
      <p v-if="history.length" class="history">samples: {{ history.join(' · ') }}</p>
    </template>
  </div>
</template>

<style scoped>
.nt { font-size: 0.95rem; }
.prompt { font-size: 1.5rem; margin: 0 0 1rem; color: var(--fenbrook-fg); }
.slot { color: var(--fenbrook-muted); border-bottom: 2px dashed var(--fenbrook-rule); padding: 0 0.2em; }
.slot.filled { color: var(--fenbrook-accent); border-bottom-color: var(--fenbrook-accent); }
.hint { margin: 0; color: var(--fenbrook-fg-soft); }
.bars { display: grid; gap: 0.35rem; max-width: 40rem; }
.row { display: grid; grid-template-columns: 8.5rem 1fr 3.5rem; align-items: center; gap: 0.8rem; }
.word { text-align: right; color: var(--fenbrook-fg-soft); }
.track { height: 1.1rem; background: var(--fenbrook-bg-elev); border-radius: 3px; overflow: hidden; }
.fill { display: block; height: 100%; background: var(--fenbrook-accent); opacity: 0.55; transition: width 0.35s ease; }
.row.hit .fill { opacity: 1; }
.row.hit .word { color: var(--fenbrook-accent); font-weight: 600; }
.pct { font-family: 'JetBrains Mono', monospace; font-size: 0.8rem; color: var(--fenbrook-muted); }
.controls { display: flex; align-items: center; gap: 1rem; margin-top: 1rem; font-size: 0.85rem; color: var(--fenbrook-fg-soft); }
.controls label { display: flex; align-items: center; gap: 0.5rem; }
.controls input { width: 9rem; accent-color: var(--fenbrook-accent); }
.history { margin: 0.6rem 0 0; font-size: 0.8rem; color: var(--fenbrook-fg-soft); }
button {
  font: inherit; font-size: 0.85rem; cursor: pointer;
  padding: 0.35rem 0.9rem; border-radius: 6px;
  border: 1px solid var(--fenbrook-accent); background: var(--fenbrook-accent); color: var(--fenbrook-bg);
}
button.ghost { background: transparent; color: var(--fenbrook-fg-soft); border-color: var(--fenbrook-rule); }
</style>
