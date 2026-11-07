<script setup>
// A tachistoscope on a slide: flash a display for a few tens of
// milliseconds, cover it with a mask, then ask a question. Built for the
// Reicher–Wheeler word superiority task, but any brief-exposure demo works.
//
//   <FlashTrial :trials="[
//     { stimulus: 'WORK', mask: '####', cue: 3, question: 'M or K?' },
//     { stimulus: 'VRMK', mask: '####', cue: 3, question: 'M or K?' },
//   ]" :step="$clicks" />
//
// With :step, click n plays trial n (0 shows a blank screen). Without it,
// a "Next trial" button steps through. "Again" replays the current trial.
// The exposure time is adjustable; screens refresh every ~16 ms, so
// durations are rounded to whole frames by the browser.
import { computed, onUnmounted, ref, watch } from 'vue'

const props = defineProps({
  trials: { type: Array, required: true }, // [{ stimulus, mask?, cue?, question? }]
  step: { type: Number, default: undefined },
  duration: { type: Number, default: 60 }, // ms the stimulus is visible
  fixation: { type: Number, default: 700 }, // ms of "+" before the stimulus
  controls: { type: Boolean, default: true },
})

const own = ref(0)
const idx = computed(() => (props.step ?? own.value))
const trial = computed(() => props.trials[idx.value - 1] || null)
const phase = ref('blank') // blank | fixation | stimulus | mask
const ms = ref(props.duration)
const timers = []
const clear = () => { while (timers.length) clearTimeout(timers.pop()) }

function play() {
  clear()
  if (!trial.value) { phase.value = 'blank'; return }
  phase.value = 'fixation'
  timers.push(setTimeout(() => {
    // wait for the next frame so the stimulus is painted before timing starts
    requestAnimationFrame(() => {
      phase.value = 'stimulus'
      requestAnimationFrame(() => {
        timers.push(setTimeout(() => { phase.value = 'mask' }, Math.max(0, ms.value - 16)))
      })
    })
  }, props.fixation))
}
watch(idx, play)
onUnmounted(clear)
function next() { own.value = (own.value % props.trials.length) + 1 }

const spaced = str => [...str]
const maskText = computed(() => trial.value?.mask ?? '#'.repeat(trial.value?.stimulus.length || 4))
</script>

<template>
  <div class="ft">
    <div class="ft-screen" :aria-live="phase === 'mask' ? 'polite' : 'off'">
      <span v-if="phase === 'fixation'" class="ft-fix">+</span>
      <span v-else-if="phase === 'stimulus' && trial" class="ft-str">
        <span v-for="(c, i) in spaced(trial.stimulus)" :key="i" class="ft-ch" :class="{ blank: c === '_' }">{{ c === '_' ? '' : c }}</span>
      </span>
      <template v-else-if="phase === 'mask' && trial">
        <span class="ft-str">
          <span v-for="(c, i) in spaced(maskText)" :key="i" class="ft-ch" :class="{ cue: trial.cue === i }">{{ c }}</span>
        </span>
        <span v-if="trial.question" class="ft-q">{{ trial.question }}</span>
      </template>
    </div>
    <div v-if="controls" class="cd-controls ft-controls">
      <button v-if="step === undefined" class="cd-btn primary" @click="next">Next trial</button>
      <button class="cd-btn" :disabled="!trial" @click="play">Again</button>
      <label class="cd-slider">exposure <input v-model.number="ms" type="range" min="16" max="300" step="16"><b>{{ ms }} ms</b></label>
      <span v-if="trial">trial {{ idx }} of {{ trials.length }}</span>
    </div>
  </div>
</template>

<style scoped>
.ft { display: flex; flex-direction: column; align-items: center; gap: 1.2rem; width: 100%; }
.ft-screen { height: 220px; width: 100%; display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 1rem; }
.ft-fix { font-size: 3rem; color: var(--fenbrook-fg, currentColor); font-weight: 300; }
.ft-str { display: flex; gap: 1.1rem; font-family: 'JetBrains Mono', monospace; font-size: 3.2rem; font-weight: 700; color: var(--fenbrook-fg, currentColor); }
.ft-ch { width: 1.1em; text-align: center; line-height: 1.2; border: 2px solid transparent; }
.ft-ch.cue { border-color: var(--fenbrook-fg, currentColor); }
.ft-q { font-size: 1.2rem; color: var(--fenbrook-fg, currentColor); }
.ft-controls { opacity: 0.55; }
.ft-controls:hover { opacity: 1; }
</style>
