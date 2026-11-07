<script setup>
// A Turing machine you can run on a slide.
//
//   <TuringMachine tape="__yxxyx__" :head="3" start="0"
//     :rules="[['0','x','x','R','0'], ['0','y','x','R','HALT']]" />
//
// Rules are [state, read, write, move, next] (or objects with those keys);
// move is L, R or N (stay). `_` is the blank symbol and is drawn empty. The
// machine halts when it enters a state listed in `halt`, or when no rule
// matches what it reads.
//
// Driving it:
// - On its own it shows Reset / Back / Step / Run buttons.
// - Pass `:step="$clicks"` to step it with slide clicks instead (buttons hide).
// - Pass `:reveal` too for a build-up before the run starts: 0 empty tape,
//   1 symbols, 2 head, 3 state in the head, 4 rules (diagram or table).
//   e.g. clicks: 7, :reveal="$clicks" :step="Math.max(0, $clicks - 4)".
//
// `editable` adds a box for typing a different starting tape.
//
// `view` picks how the rules are shown: 'diagram' (state graph), 'table',
// 'both', or 'none'. `labels` sets the diagram's edge labels: 'short'
// (x → x, R) or 'long' (Read x; Write x; Move R;).
import { computed, onUnmounted, ref } from 'vue'

const props = defineProps({
  tape: { type: [String, Array], required: true },
  head: { type: Number, default: 0 },
  start: { type: String, default: '0' },
  rules: { type: Array, required: true },
  halt: { type: Array, default: () => ['HALT'] },
  blank: { type: String, default: '_' },
  view: { type: String, default: 'diagram' },
  labels: { type: String, default: 'short' },
  cells: { type: Number, default: 9 },
  // which tape index sits in the leftmost visible cell at the start
  windowStart: { type: Number, default: 0 },
  step: { type: Number, default: undefined },
  reveal: { type: Number, default: Infinity },
  interval: { type: Number, default: 700 }, // ms per step when running
  maxSteps: { type: Number, default: 500 },
  // show a box for typing a new starting tape (head stays at `head`)
  editable: { type: Boolean, default: false },
})

const RULES = computed(() =>
  props.rules.map((r, i) => {
    const [state, read, write, move, next] = Array.isArray(r) ? r : [r.state, r.read, r.write, r.move, r.next]
    return { i, state: String(state), read: String(read), write: String(write), move: String(move).toUpperCase(), next: String(next) }
  }),
)
const isHalt = s => props.halt.includes(s)
const findRule = (state, sym) => RULES.value.find(r => r.state === state && r.read === sym)

// ---- simulation: replay from the start, so stepping back is free ----------
const typed = ref(null) // tape typed into the edit box, if any
const tapeIn = computed(() => typed.value ?? (Array.isArray(props.tape) ? props.tape.join('') : props.tape))
function simulate(n) {
  const init = typed.value !== null ? [...typed.value] : Array.isArray(props.tape) ? props.tape : [...props.tape]
  const tape = new Map(init.map((s, i) => [i, String(s)]))
  const read = i => tape.get(i) ?? props.blank
  let head = props.head
  let state = props.start
  let win = props.windowStart
  let last = null // { rule, at, changed }
  let k = 0
  const shift = () => {
    if (head < win + 1) win = head - 1
    if (head > win + props.cells - 2) win = head - props.cells + 2
  }
  shift()
  for (; k < n; k++) {
    if (isHalt(state)) break
    const rule = findRule(state, read(head))
    if (!rule) break
    const at = head
    const changed = read(head) !== rule.write
    tape.set(head, rule.write)
    head += rule.move === 'L' ? -1 : rule.move === 'R' ? 1 : 0
    state = rule.next
    last = { rule, at, changed }
    shift()
  }
  const pending = isHalt(state) ? null : findRule(state, read(head))
  return { tape, read, head, state, win, last, steps: k, pending, halted: !pending }
}

// ---- who drives it ----------------------------------------------------------
const external = computed(() => props.step !== undefined)
const own = ref(0)
const running = ref(false)
let timer = null
const stepCount = computed(() => (external.value ? Math.max(0, props.step) : own.value))
const m = computed(() => simulate(stepCount.value))

function stop() { running.value = false; clearInterval(timer) }
function forward() { if (!m.value.halted && own.value < props.maxSteps) own.value++ }
function back() { stop(); own.value = Math.max(0, own.value - 1) }
function reset() { stop(); own.value = 0 }
function setTape(e) { typed.value = e.target.value.replace(/\s/g, props.blank); reset() }
function toggleRun() {
  if (running.value) return stop()
  if (m.value.halted) own.value = 0
  running.value = true
  timer = setInterval(() => {
    forward()
    if (m.value.halted) stop()
  }, props.interval)
}
onUnmounted(stop)

// ---- what's shown -------------------------------------------------------------
const show = computed(() => ({
  symbols: props.reveal >= 1,
  head: props.reveal >= 2,
  label: props.reveal >= 3,
  rules: props.reveal >= 4,
}))

const VB_W = 900
const CW = computed(() => Math.min(78.5, 720 / props.cells)) // cell size
const GAP = 3
const TAPE_X0 = computed(() => (VB_W - props.cells * (CW.value + GAP) + GAP) / 2)
const TAPE_Y = 100
const cellX = j => TAPE_X0.value + j * (CW.value + GAP)
const visible = computed(() =>
  Array.from({ length: props.cells }, (_, j) => {
    const idx = m.value.win + j
    const s = m.value.read(idx)
    return {
      j, idx,
      sym: show.value.symbols && s !== props.blank ? s : '',
      fresh: m.value.last?.at === idx && m.value.last.changed,
    }
  }),
)
const headX = computed(() => cellX(m.value.head - m.value.win) + CW.value / 2)
const headLabel = computed(() => (show.value.label ? m.value.state : ''))
const symSize = computed(() => CW.value * 0.5)

// state diagram: states in a row, start first, halt states last
const STATES = computed(() => {
  const seen = [props.start]
  for (const r of RULES.value) for (const s of [r.state, r.next]) if (!seen.includes(s)) seen.push(s)
  return [...seen.filter(s => !isHalt(s)), ...seen.filter(isHalt)]
})
const SR = 52
const SY = 385
const stateX = computed(() => {
  const n = STATES.value.length
  const span = Math.min(VB_W - 260, (n - 1) * 300)
  const x0 = VB_W / 2 - span / 2
  return Object.fromEntries(STATES.value.map((s, i) => [s, n === 1 ? VB_W / 2 : x0 + (i * span) / (n - 1)]))
})

const ruleLines = r => (props.labels === 'long'
  ? [`Read ${r.read};`, `Write ${r.write};`, `Move ${r.move};`]
  : [`${r.read} → ${r.write}, ${r.move}`])

const edges = computed(() => {
  const groups = new Map()
  for (const r of RULES.value) {
    const key = `${r.state}→${r.next}`
    if (!groups.has(key)) groups.set(key, { from: r.state, to: r.next, rules: [] })
    groups.get(key).rules.push(r)
  }
  const y = SY
  return [...groups.values()].map((g) => {
    const lines = g.rules.flatMap(ruleLines)
    const ruleIdx = g.rules.map(r => r.i)
    const x1 = stateX.value[g.from]
    const x2 = stateX.value[g.to]
    if (g.from === g.to) {
      // loop over the top, label above it
      const a1 = (-120 * Math.PI) / 180
      const a2 = (-60 * Math.PI) / 180
      const p1 = [x1 + SR * Math.cos(a1), y + SR * Math.sin(a1)]
      const p2 = [x1 + SR * Math.cos(a2), y + SR * Math.sin(a2)]
      const d = `M${p1} C${p1[0] - 35},${p1[1] - 80} ${p2[0] + 35},${p2[1] - 80} ${p2}`
      return { ...g, d, lines, ruleIdx, lx: x1, ly: y - SR - 72, anchor: 'middle', dir: -1 }
    }
    const fwd = x2 > x1
    const sgn = fwd ? -1 : 1 // forward arcs above, backward below
    // arcs that jump over states go higher, clear of those states' loops
    const skipped = Math.abs(STATES.value.indexOf(g.to) - STATES.value.indexOf(g.from)) - 1
    const lift = 40 + Math.abs(x2 - x1) * 0.08 + skipped * 75
    const a1 = ((fwd ? -35 : 145) * Math.PI) / 180
    const a2 = ((fwd ? -145 : 35) * Math.PI) / 180
    const p1 = [x1 + SR * Math.cos(a1), y + SR * Math.sin(a1)]
    const p2 = [x2 + SR * Math.cos(a2), y + SR * Math.sin(a2)]
    const cy = y + sgn * (SR + lift)
    const d = `M${p1} C${p1[0] + (x2 - x1) * 0.25},${cy} ${p2[0] - (x2 - x1) * 0.25},${cy} ${p2}`
    const apex = 0.125 * p1[1] + 0.75 * cy + 0.125 * p2[1]
    return { ...g, d, lines, ruleIdx, lx: (x1 + x2) / 2, ly: apex + sgn * 10, anchor: 'middle', dir: sgn }
  })
})
const lineH = computed(() => (props.labels === 'long' ? 20 : 22))
// first-line y for a label block, growing away from its edge
const labelY0 = e => (e.dir < 0 ? e.ly - (e.lines.length - 1) * lineH.value
  : e.dir > 0 ? e.ly + 16 : e.ly - ((e.lines.length - 1) * lineH.value) / 2)
const activeEdge = e => m.value.pending && e.ruleIdx.includes(m.value.pending.i)

const hasBack = computed(() => RULES.value.some(r => stateX.value[r.next] < stateX.value[r.state]))
const diagramBottom = computed(() => SY + SR + (hasBack.value ? 110 : 20))
const tableY = computed(() => (props.view === 'both' ? diagramBottom.value + 30 : 250))
const ruleText = r => `State: ${r.state}, Read: ${r.read}, Write: ${r.write}, Move: ${r.move}, New State: ${r.next}`
const viewH = computed(() => {
  if (props.view === 'none') return 200
  if (props.view === 'table') return tableY.value + RULES.value.length * 28
  if (props.view === 'both') return tableY.value + RULES.value.length * 28
  return diagramBottom.value
})
const status = computed(() => {
  const s = m.value
  if (isHalt(s.state)) return `halted after ${s.steps} step${s.steps === 1 ? '' : 's'}`
  if (s.halted) return `stuck: no rule for state ${s.state} reading ${s.read(s.head) === props.blank ? 'blank' : s.read(s.head)}`
  return `step ${s.steps} · state ${s.state}`
})
</script>

<template>
  <div class="tm-wrap">
    <svg :viewBox="`0 20 ${VB_W} ${viewH - 20}`" class="tm" role="img"
      aria-label="Turing machine: a tape of cells, a read/write head, and its rules">
      <defs>
        <marker id="tm-arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7"
          orient="auto-start-reverse">
          <path d="M0,0 L10,5 L0,10 z" class="tm-arrowhead" />
        </marker>
        <marker id="tm-arrow-on" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7"
          orient="auto-start-reverse">
          <path d="M0,0 L10,5 L0,10 z" class="tm-arrowhead on" />
        </marker>
      </defs>

      <!-- tape: the arrows say it goes on forever -->
      <path class="tm-edge" :d="`M${cellX(0) - 51},${TAPE_Y + CW / 2} l14,-11 v6 h14 v10 h-14 v6 z`" />
      <path class="tm-edge"
        :d="`M${cellX(cells - 1) + CW + 51},${TAPE_Y + CW / 2} l-14,-11 v6 h-14 v10 h14 v6 z`" />
      <g v-for="c in visible" :key="c.j">
        <rect :x="cellX(c.j)" :y="TAPE_Y" :width="CW" :height="CW" class="tm-cell" />
        <text :x="cellX(c.j) + CW / 2" :y="TAPE_Y + CW / 2 + 2" class="tm-sym" :class="{ fresh: c.fresh }"
          :style="{ fontSize: symSize + 'px' }">{{ c.sym }}</text>
      </g>

      <!-- head -->
      <g class="tm-head" :class="{ on: show.head }" :style="{ transform: `translateX(${headX}px)` }">
        <rect x="-24" y="40" width="48" height="28" rx="5" class="tm-head-box" />
        <text x="0" y="55" class="tm-head-label" :class="{ small: headLabel.length > 2 }">{{ headLabel }}</text>
        <path d="M-8,68 h16 v14 h10 l-18,16 l-18,-16 h10 z" class="tm-head-box" />
      </g>

      <!-- state diagram -->
      <g v-if="view === 'diagram' || view === 'both'" class="tm-fade" :class="{ on: show.rules }">
        <g v-for="(e, k) in edges" :key="'e' + k" :class="{ live: activeEdge(e) }">
          <path :d="e.d" class="tm-link" :marker-end="activeEdge(e) ? 'url(#tm-arrow-on)' : 'url(#tm-arrow)'" />
          <text class="tm-rule" :text-anchor="e.anchor">
            <tspan v-for="(t, i) in e.lines" :key="i" :x="e.lx" :y="labelY0(e) + i * lineH">{{ t }}</tspan>
          </text>
        </g>
        <g v-for="s in STATES" :key="s">
          <circle :cx="stateX[s]" :cy="SY" :r="SR" class="tm-state" :class="{ active: s === m.state, halt: isHalt(s) }" />
          <circle v-if="isHalt(s)" :cx="stateX[s]" :cy="SY" :r="SR - 7" class="tm-state-inner" />
          <text :x="stateX[s]" :y="SY + 2" class="tm-state-label" :class="{ active: s === m.state }">{{ s }}</text>
        </g>
      </g>

      <!-- rule table -->
      <g v-if="view === 'table' || view === 'both'" class="tm-fade" :class="{ on: show.rules }">
        <g v-for="(r, i) in RULES" :key="'r' + i" :class="{ live: m.pending?.i === r.i }">
          <rect :x="TAPE_X0 - 8" :y="tableY + i * 28 - 18" :width="VB_W - 2 * TAPE_X0 + 16" height="26" rx="4" class="tm-row" />
          <text :x="TAPE_X0" :y="tableY + i * 28" class="tm-table">{{ ruleText(r) }}</text>
        </g>
      </g>
    </svg>

    <div v-if="!external" class="tm-controls">
      <button @click="reset" title="Reset">⏮ Reset</button>
      <button @click="back" :disabled="own === 0" title="Back one step">◀ Back</button>
      <button @click="stop(); forward()" :disabled="m.halted" title="One step">Step ▶</button>
      <button @click="toggleRun" class="primary">{{ running ? '⏸ Pause' : '▶▶ Run' }}</button>
      <label v-if="editable" class="tm-edit">tape <input :value="tapeIn" spellcheck="false" @change="setTape"></label>
      <span class="tm-status">{{ status }}</span>
    </div>
  </div>
</template>

<style scoped>
.tm-wrap { width: 100%; }
.tm { width: 100%; display: block; }
.tm-cell { fill: none; stroke: var(--fenbrook-fg, currentColor); stroke-width: 1.2; }
.tm-edge { fill: none; stroke: var(--fenbrook-fg, currentColor); stroke-width: 1.2; stroke-linejoin: round; }
.tm-sym {
  fill: var(--fenbrook-fg, currentColor); text-anchor: middle; dominant-baseline: middle;
  transition: fill 0.3s;
}
.tm-sym.fresh { fill: var(--fenbrook-accent, orange); }
.tm-head { opacity: 0; transition: transform 0.45s ease, opacity 0.3s; }
.tm-head.on { opacity: 1; }
.tm-head-box {
  fill: var(--fenbrook-bg, #111); stroke: var(--fenbrook-accent, orange); stroke-width: 2; stroke-linejoin: round;
}
.tm-head-label {
  fill: var(--fenbrook-accent, orange); font-family: 'JetBrains Mono', monospace; font-size: 15px;
  text-anchor: middle; dominant-baseline: middle;
}
.tm-head-label.small { font-size: 10px; }
.tm-fade { opacity: 0; transition: opacity 0.4s; }
.tm-fade.on { opacity: 1; }
.tm-link { fill: none; stroke: var(--fenbrook-fg, currentColor); stroke-width: 1.5; transition: stroke 0.3s; }
.tm-arrowhead { fill: var(--fenbrook-fg, currentColor); }
.tm-arrowhead.on { fill: var(--fenbrook-accent, orange); }
.live .tm-link { stroke: var(--fenbrook-accent, orange); stroke-width: 2.5; }
.tm-rule { fill: var(--fenbrook-fg, currentColor); font-size: 16px; transition: fill 0.3s; }
.live .tm-rule { fill: var(--fenbrook-accent, orange); }
.tm-state {
  fill: var(--fenbrook-bg, #111); stroke: var(--fenbrook-fg, currentColor); stroke-width: 5; transition: fill 0.35s;
}
.tm-state.active { fill: var(--fenbrook-accent, orange); }
.tm-state-inner { fill: none; stroke: var(--fenbrook-fg, currentColor); stroke-width: 1.5; }
.tm-state-label {
  fill: var(--fenbrook-fg, currentColor); font-family: 'JetBrains Mono', monospace; font-size: 22px;
  text-anchor: middle; dominant-baseline: middle; transition: fill 0.35s;
}
.tm-state-label.active { fill: var(--fenbrook-bg, #111); }
.tm-row { fill: transparent; transition: fill 0.3s; }
.live .tm-row { fill: color-mix(in srgb, var(--fenbrook-accent, orange) 22%, transparent); }
.tm-table { fill: var(--fenbrook-fg, currentColor); font-family: 'JetBrains Mono', monospace; font-size: 17px; }

.tm-controls { display: flex; gap: 0.5rem; align-items: center; justify-content: center; margin-top: 0.5rem; }
.tm-controls button {
  font: inherit; font-size: 0.85rem; padding: 0.3rem 0.8rem; border-radius: 6px; cursor: pointer;
  background: transparent; color: var(--fenbrook-fg, currentColor);
  border: 1px solid var(--fenbrook-rule, #555);
}
.tm-controls button:hover:not(:disabled) { border-color: var(--fenbrook-accent, orange); }
.tm-controls button:disabled { opacity: 0.35; cursor: default; }
.tm-controls button.primary { border-color: var(--fenbrook-accent, orange); color: var(--fenbrook-accent, orange); }
.tm-edit { display: inline-flex; align-items: center; gap: 0.4rem; font-size: 0.8rem; color: var(--fenbrook-muted, #999); }
.tm-edit input {
  font-family: 'JetBrains Mono', monospace; font-size: 0.85rem; width: 12ch; padding: 0.2rem 0.4rem;
  background: transparent; color: var(--fenbrook-fg, currentColor); border: 1px solid var(--fenbrook-rule, #555); border-radius: 4px;
}
.tm-status {
  margin-left: 0.75rem; font-family: 'JetBrains Mono', monospace; font-size: 0.8rem;
  color: var(--fenbrook-muted, #999); min-width: 16ch;
}
</style>
