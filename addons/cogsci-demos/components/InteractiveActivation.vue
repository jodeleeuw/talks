<script setup>
// McClelland & Rumelhart's (1981) interactive activation model, running live.
//
//   <InteractiveActivation />                       presets + free play
//   <InteractiveActivation word="WORK" :hide="{ 3: [0, 1, 7, 10] }" />
//
// Four letters are drawn in a 14-segment font; click a segment to cover it
// up (the model then gets no evidence about that segment). Type any four
// letters, or "_" for an empty position. "Flash, then mask" shows the
// display for a few cycles and then replaces it with a #### mask, as in the
// Reicher–Wheeler task. The plots show the letter units in one position
// (pick it with the 1–4 buttons) and the most active word units, cycle by
// cycle; each run's peak for the probed letter is listed so runs can be
// compared (word vs. nonword vs. letter alone). The model itself is in
// ../lib/iam.js.
import { computed, onUnmounted, reactive, ref } from 'vue'
import { createModel, FONT, LETTERS, SEGMENTS } from '../lib/iam.js'
import { SERIES, path, scale } from '../lib/plot.js'

const props = defineProps({
  word: { type: String, default: 'WORK' },
  hide: { type: Object, default: () => ({}) }, // { position: [segment, …] }
  probe: { type: Number, default: 3 }, // 0-based letter position to plot
  mask: { type: Number, default: 0 }, // cycles before the mask; 0 = no mask
  cycles: { type: Number, default: 50 },
  interval: { type: Number, default: 45 }, // ms per cycle when running
  presets: { type: Boolean, default: true },
})

const PRESETS = [
  { label: 'WOR? (K or R?)', word: 'WORK', hide: { 3: [0, 1, 7, 10] }, probe: 3, mask: 0 },
  { label: 'WORK', word: 'WORK', hide: {}, probe: 3, mask: 12 },
  { label: 'VRMK', word: 'VRMK', hide: {}, probe: 3, mask: 12 },
  { label: 'K alone', word: '___K', hide: {}, probe: 3, mask: 12 },
  { label: 'MAVE', word: 'MAVE', hide: {}, probe: 3, mask: 12 },
]

const s = reactive({
  word: props.word.toUpperCase(),
  hide: Object.fromEntries(Object.entries(props.hide).map(([k, v]) => [k, [...v]])),
  probe: props.probe,
  mask: props.mask,
})
const typed = ref(s.word)
const model = createModel()
const trace = ref([]) // per cycle: { letters: [4][26], words: Map name→a }
const running = ref(false)
const results = ref([])
let timer = null

const display = computed(() => [...s.word.padEnd(4, '_').slice(0, 4)].map((c, i) =>
  FONT[c] ? { letter: c, hidden: s.hide[i] || [] } : null))
const masked = computed(() => s.mask > 0 && trace.value.length >= s.mask)
const shown = computed(() => (masked.value ? display.value.map(() => ({ letter: '#', hidden: [] })) : display.value))

function snapshot() {
  const letters = [0, 1, 2, 3].map(p => LETTERS.map(l => model.letter(p, l)))
  const words = new Map(model.topWords(12).map(w => [w.name, w.a]))
  return { letters, words }
}
function reset() {
  stop()
  model.reset()
  model.setDisplay(display.value)
  trace.value = [snapshot()]
}
function step() {
  if (trace.value.length > props.cycles) return stop()
  model.setDisplay(shown.value)
  model.step()
  trace.value = [...trace.value, snapshot()]
  if (trace.value.length > props.cycles) { stop(); record() }
}
function record() {
  const c = s.word[s.probe]
  if (!FONT[c]) return
  const li = LETTERS.indexOf(c)
  const peak = Math.max(...trace.value.map(t => t.letters[s.probe][li]))
  const label = s.word.replace(/_/g, '·') + (s.mask ? ' (masked)' : '')
  results.value = [{ label, letter: c, peak }, ...results.value.filter(r => r.label !== label)].slice(0, 4)
}
function run() {
  if (running.value) return stop()
  if (trace.value.length > props.cycles) reset()
  running.value = true
  timer = setInterval(step, props.interval)
}
function stop() { running.value = false; clearInterval(timer) }
onUnmounted(stop)

function use(p) {
  s.word = p.word; typed.value = p.word; s.probe = p.probe; s.mask = p.mask
  s.hide = Object.fromEntries(Object.entries(p.hide).map(([k, v]) => [k, [...v]]))
  reset(); run()
}
function onType() {
  const w = typed.value.toUpperCase().replace(/[^A-Z_ ]/g, '').replace(/ /g, '_').slice(0, 4)
  typed.value = w
  if (w.length === 4) { s.word = w; s.hide = {}; reset() }
}
function toggle(pos, seg) {
  if (masked.value) return
  const h = new Set(s.hide[pos] || [])
  h.has(seg) ? h.delete(seg) : h.add(seg)
  s.hide = { ...s.hide, [pos]: [...h] }
  reset()
}
reset()

// ---- glyphs ----------------------------------------------------------------
const GS = 5.2 // px per font unit
const glyphX = i => 8 + i * 64
function segState(i, seg) {
  const d = shown.value[i]
  if (!d) return 'empty'
  if ((d.hidden || []).includes(seg)) return 'hidden'
  const on = d.letter === '#' || FONT[d.letter].includes(seg)
  return on ? 'on' : 'off'
}

// ---- plots ------------------------------------------------------------------
const PW = 330, PH = 150, PL = 34, PT = 8
const xs = computed(() => scale(0, props.cycles, PL, PL + PW))
const ys = scale(-0.2, 1, PT + PH, PT)
const letterLines = computed(() => {
  const p = s.probe
  const peak = LETTERS.map((_, li) => Math.max(...trace.value.map(t => t.letters[p][li])))
  const top = LETTERS.map((l, li) => ({ l, li, m: peak[li] })).sort((a, b) => b.m - a.m).slice(0, 4)
  return top.map((t, k) => {
    const pts = trace.value.map((tr, c) => [xs.value(c), ys(tr.letters[p][t.li])])
    return { name: t.l, d: path(pts), color: SERIES[k], end: pts[pts.length - 1], a: trace.value.at(-1).letters[p][t.li] }
  })
})
const wordLines = computed(() => {
  const best = new Map()
  for (const t of trace.value) for (const [w, a] of t.words) best.set(w, Math.max(best.get(w) ?? -1, a))
  const top = [...best.entries()].sort((a, b) => b[1] - a[1]).slice(0, 5).map(e => e[0])
  return top.map((w, k) => {
    const pts = []
    trace.value.forEach((t, c) => { if (t.words.has(w)) pts.push([xs.value(c), ys(t.words.get(w))]) })
    return { name: w, d: path(pts), color: SERIES[k], end: pts[pts.length - 1] || [PL, ys(0)] }
  })
})
// stagger end labels so they don't overlap
function labelYs(lines) {
  const sorted = lines.map((l, i) => ({ i, y: l.end[1] })).sort((a, b) => a.y - b.y)
  for (let k = 1; k < sorted.length; k++) if (sorted[k].y - sorted[k - 1].y < 13) sorted[k].y = sorted[k - 1].y + 13
  const out = []
  for (const t of sorted) out[t.i] = t.y
  return out
}
const yTicks = [0, 0.5, 1]
</script>

<template>
  <div class="iam">
    <div class="iam-left">
      <svg class="glyphs" viewBox="0 0 264 86" role="img" :aria-label="`Display: ${masked ? '####' : s.word}`">
        <g v-for="i in 4" :key="i" :transform="`translate(${glyphX(i - 1)}, 6)`" :class="{ probe: i - 1 === s.probe }">
          <rect x="-4" y="-3" width="60" height="80" rx="5" class="cell" />
          <line v-for="(g, k) in SEGMENTS" :key="k" :x1="g[0] * GS" :y1="g[1] * GS" :x2="g[2] * GS" :y2="g[3] * GS"
            :class="['seg', segState(i - 1, k)]" @click="toggle(i - 1, k)" />
        </g>
      </svg>
      <div class="cd-row">
        <input v-model="typed" class="iam-input cd-mono" maxlength="4" spellcheck="false" aria-label="Four letters to show" @input="onType">
        <label class="cd-check"><input v-model.number="s.mask" type="checkbox" :true-value="12" :false-value="0" @change="reset">flash, then mask</label>
      </div>
      <div v-if="presets" class="cd-row">
        <button v-for="p in PRESETS" :key="p.label" class="cd-btn" @click="use(p)">{{ p.label }}</button>
      </div>
      <div class="cd-row">
        <button class="cd-btn primary" @click="run">{{ running ? 'Pause' : 'Run' }}</button>
        <button class="cd-btn" :disabled="running" @click="step">Step</button>
        <button class="cd-btn" @click="reset">Reset</button>
        <span class="cd-note">cycle <b>{{ trace.length - 1 }}</b><template v-if="masked"> · masked</template></span>
      </div>
      <ul v-if="results.length" class="iam-results cd-note">
        <li v-for="r in results" :key="r.label"><span class="cd-mono">{{ r.label }}</span>: {{ r.letter }} peaks at <b>{{ r.peak.toFixed(2) }}</b></li>
      </ul>
    </div>

    <div class="iam-right">
      <div class="iam-plot-head">
        <span>Letters in position</span>
        <button v-for="p in 4" :key="p" class="cd-btn" :class="{ on: s.probe === p - 1 }" @click="s.probe = p - 1">{{ p }}</button>
      </div>
      <svg :viewBox="`0 0 ${PL + PW + 52} ${PH + PT + 18}`" class="iam-plot" role="img" aria-label="Letter activations over time">
        <line v-for="t in yTicks" :key="t" :x1="PL" :x2="PL + PW" :y1="ys(t)" :y2="ys(t)" class="cd-grid" />
        <text v-for="t in yTicks" :key="'t' + t" :x="PL - 6" :y="ys(t) + 4" class="cd-tick" text-anchor="end">{{ t }}</text>
        <text :x="PL + PW" :y="PT + PH + 15" class="cd-tick" text-anchor="end">cycles</text>
        <path v-for="l in letterLines" :key="l.name" :d="l.d" :stroke="l.color" class="line" />
        <text v-for="(l, k) in letterLines" :key="'n' + l.name" :x="l.end[0] + 6" :y="labelYs(letterLines)[k] + 4" :fill="l.color" class="lname">{{ l.name }}</text>
      </svg>
      <div class="iam-plot-head"><span>Most active words</span></div>
      <svg :viewBox="`0 0 ${PL + PW + 52} ${PH + PT + 18}`" class="iam-plot" role="img" aria-label="Word activations over time">
        <line v-for="t in yTicks" :key="t" :x1="PL" :x2="PL + PW" :y1="ys(t)" :y2="ys(t)" class="cd-grid" />
        <text v-for="t in yTicks" :key="'t' + t" :x="PL - 6" :y="ys(t) + 4" class="cd-tick" text-anchor="end">{{ t }}</text>
        <text :x="PL + PW" :y="PT + PH + 15" class="cd-tick" text-anchor="end">cycles</text>
        <path v-for="l in wordLines" :key="l.name" :d="l.d" :stroke="l.color" class="line" />
        <text v-for="(l, k) in wordLines" :key="'n' + l.name" :x="l.end[0] + 6" :y="labelYs(wordLines)[k] + 4" :fill="l.color" class="lname">{{ l.name }}</text>
      </svg>
    </div>
  </div>
</template>

<style scoped>
.iam { display: grid; grid-template-columns: minmax(0, 0.95fr) minmax(0, 1.05fr); gap: 1.6rem; align-items: start; width: 100%; }
.iam-left { display: flex; flex-direction: column; gap: 0.6rem; }
.iam-right { display: flex; flex-direction: column; gap: 0.15rem; }
.glyphs { width: 100%; max-width: 330px; }
.cell { fill: none; stroke: var(--fenbrook-rule, #333); }
.probe .cell { stroke: var(--fenbrook-accent, orange); }
.seg { stroke-linecap: round; cursor: pointer; }
.seg.on { stroke: var(--fenbrook-fg, #eee); stroke-width: 4.5; }
.seg.off { stroke: var(--fenbrook-rule, #333); stroke-width: 2.5; }
.seg.off:hover { stroke: var(--fenbrook-muted, #888); }
.seg.hidden { stroke: var(--fenbrook-muted, #888); stroke-width: 9; opacity: 0.45; }
.seg.empty { stroke: transparent; stroke-width: 2; cursor: default; }
.iam-input {
  width: 5.5em; font-size: 1rem; letter-spacing: 0.25em; text-transform: uppercase; padding: 0.15rem 0.4rem;
  background: transparent; color: var(--fenbrook-fg, currentColor); border: 1px solid var(--fenbrook-rule, #555); border-radius: 6px;
}
.iam-results { margin: 0.2rem 0 0; padding: 0; list-style: none; display: flex; flex-direction: column; gap: 0.1rem; }
.iam-plot-head { display: flex; align-items: center; gap: 0.35rem; font-size: 0.82rem; color: var(--fenbrook-fg-soft, currentColor); }
.iam-plot-head .cd-btn { padding: 0.05rem 0.45rem; }
.iam-plot { width: 100%; max-height: 175px; }
.line { fill: none; stroke-width: 2.2; }
.lname { font-family: 'JetBrains Mono', monospace; font-size: 12px; }
</style>
