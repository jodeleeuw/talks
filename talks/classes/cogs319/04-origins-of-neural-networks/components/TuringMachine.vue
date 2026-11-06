<script setup>
// A Turing machine that turns the first y it meets into an x, then halts.
// Slide clicks step it. Geometry follows the original Google Slides deck
// (960×540 coordinates).
//
// mode="diagram" (clicks 0–7): empty tape → symbols → head → state label →
//   state diagram → head steps right twice → writes x, moves, halts.
// mode="table"   (clicks 0–3): same run with the rule table instead of the
//   state diagram, starting from the head over the first x.
import { computed } from 'vue'
import { useSlideContext } from '@slidev/client'

const props = defineProps({
  mode: { type: String, default: 'diagram' },
})

const { $clicks } = useSlideContext()

const CELL_X0 = 114.6
const CELL_DX = 81.55
const CELL_W = 78.5
const TAPE_Y = 106
const START = ['', '', 'y', 'x', 'x', 'y', 'x', '', '']
const cellX = i => CELL_X0 + i * CELL_DX

const s = computed(() => {
  const c = $clicks.value
  if (props.mode === 'table') {
    const k = Math.min(c, 3)
    return { filled: true, head: 3 + k, label: k >= 3 ? 'HALT' : '0', halted: k >= 3, machine: true }
  }
  return {
    filled: c >= 1,
    head: c < 2 ? null : c <= 4 ? 3 : c - 2,
    label: c < 3 ? '' : c >= 7 ? 'HALT' : '0',
    halted: c >= 7,
    machine: c >= 4,
  }
})

const tape = computed(() => {
  const t = START.map(v => (s.value.filled ? v : ''))
  if (s.value.halted) t[5] = 'x'
  return t
})

const headX = computed(() => cellX(s.value.head ?? 3) + CELL_W / 2)

// state circles
const R = 63.8
const S0 = { x: 316.9, y: 355.7 }
const HALT = { x: 613.9, y: 355.7 }
</script>

<template>
  <svg viewBox="40 20 870 420" class="tm" role="img"
    aria-label="Turing machine: a tape of cells, a read/write head, and its rules">
    <defs>
      <marker id="tm-arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7"
        orient="auto-start-reverse">
        <path d="M0,0 L10,5 L0,10 z" class="tm-arrowhead" />
      </marker>
    </defs>

    <!-- tape: the arrows say it goes on forever -->
    <path class="tm-edge" d="M63.5,131.7 l14,-11 v6 h14 v10 h-14 v6 z" />
    <path class="tm-edge" d="M886.6,130.1 l-14,-11 v6 h-14 v10 h14 v6 z" />
    <g v-for="(v, i) in tape" :key="i">
      <rect :x="cellX(i)" :y="TAPE_Y" :width="CELL_W" :height="CELL_W" class="tm-cell" />
      <text :x="cellX(i) + CELL_W / 2" :y="TAPE_Y + CELL_W / 2 + 2" class="tm-sym"
        :class="{ changed: s.halted && i === 5 }">{{ v }}</text>
    </g>

    <!-- head -->
    <g class="tm-head" :class="{ on: s.head !== null }"
      :style="{ transform: `translateX(${headX}px)` }">
      <rect x="-19" y="40.6" width="38" height="27.1" rx="5" class="tm-head-box" />
      <text x="0" y="55" class="tm-head-label" :class="{ small: s.label === 'HALT' }">{{ s.label }}</text>
      <path d="M-8,67.7 h16 v20 h10 l-18,17 l-18,-17 h10 z" class="tm-head-box" />
    </g>

    <!-- state diagram -->
    <g v-if="mode === 'diagram'" class="tm-machine" :class="{ on: s.machine }">
      <path d="M266,318 C222,268 268,232 286,298" class="tm-link" marker-end="url(#tm-arrow)" />
      <path d="M338,295 C410,258 520,258 588,297" class="tm-link" marker-end="url(#tm-arrow)" />
      <text class="tm-rule">
        <tspan x="166" y="292">Read x;</tspan>
        <tspan x="166" y="314">Write x;</tspan>
        <tspan x="166" y="336">Move R;</tspan>
      </text>
      <text class="tm-rule">
        <tspan x="437" y="284">Read y;</tspan>
        <tspan x="437" y="306">Write x;</tspan>
        <tspan x="437" y="328">Move R;</tspan>
      </text>
      <circle :cx="S0.x" :cy="S0.y" :r="R" class="tm-state" :class="{ active: !s.halted }" />
      <text :x="S0.x" :y="S0.y + 2" class="tm-state-label" :class="{ active: !s.halted }">0</text>
      <circle :cx="HALT.x" :cy="HALT.y" :r="R" class="tm-state" :class="{ active: s.halted }" />
      <text :x="HALT.x" :y="HALT.y + 2" class="tm-state-label" :class="{ active: s.halted }">HALT</text>
    </g>

    <!-- rule table -->
    <text v-else class="tm-table">
      <tspan x="129" y="250">State: 0, Read: x, Write: x, Move: R, New State: 0</tspan>
      <tspan x="129" y="276">State: 0, Read: y, Write: x, Move: R, New State: HALT</tspan>
    </text>
  </svg>
</template>

<style scoped>
.tm { width: 100%; }
.tm-cell { fill: none; stroke: var(--fenbrook-fg); stroke-width: 1.2; }
.tm-edge { fill: none; stroke: var(--fenbrook-fg); stroke-width: 1.2; stroke-linejoin: round; }
.tm-sym {
  fill: var(--fenbrook-fg); font-size: 40px; text-anchor: middle; dominant-baseline: middle;
  transition: fill 0.3s;
}
.tm-sym.changed { fill: var(--fenbrook-accent); }
.tm-head { opacity: 0; transition: transform 0.45s ease, opacity 0.3s; }
.tm-head.on { opacity: 1; }
.tm-head-box { fill: var(--fenbrook-bg); stroke: var(--fenbrook-accent); stroke-width: 2; stroke-linejoin: round; }
.tm-head-label {
  fill: var(--fenbrook-accent); font-family: 'JetBrains Mono', monospace; font-size: 15px;
  text-anchor: middle; dominant-baseline: middle;
}
.tm-head-label.small { font-size: 9px; }
.tm-machine { opacity: 0; transition: opacity 0.4s; }
.tm-machine.on { opacity: 1; }
.tm-link { fill: none; stroke: var(--fenbrook-fg); stroke-width: 1.5; }
.tm-arrowhead { fill: var(--fenbrook-fg); }
.tm-rule { fill: var(--fenbrook-fg); font-size: 16px; }
.tm-state { fill: var(--fenbrook-bg); stroke: var(--fenbrook-fg); stroke-width: 6; transition: fill 0.35s; }
.tm-state.active { fill: var(--fenbrook-accent); }
.tm-state-label {
  fill: var(--fenbrook-fg); font-family: 'JetBrains Mono', monospace; font-size: 22px;
  text-anchor: middle; dominant-baseline: middle; transition: fill 0.35s;
}
.tm-state-label.active { fill: var(--fenbrook-bg); }
.tm-table { fill: var(--fenbrook-fg); font-family: 'JetBrains Mono', monospace; font-size: 17px; }
</style>
