<script setup>
// McCulloch & Pitts (1943) neuron: all-or-none, fires when at least θ
// excitatory inputs are active, and any active inhibitory input blocks it.
// The three nets are their Figure 1b (or), 1c (and), 1d (A and not B).
import { computed, ref } from 'vue'

const NETS = {
  or: { label: 'A or B', theta: 1, b: 'exc', fig: '1b' },
  and: { label: 'A and B', theta: 2, b: 'exc', fig: '1c' },
  andNot: { label: 'A and not B', theta: 1, b: 'inh', fig: '1d' },
}

const a = ref(false)
const b = ref(false)
const net = ref('or')
const cfg = computed(() => NETS[net.value])

function fires(av, bv, c) {
  if (c.b === 'inh' && bv) return false
  const exc = (av ? 1 : 0) + (c.b === 'exc' && bv ? 1 : 0)
  return exc >= c.theta
}
const out = computed(() => fires(a.value, b.value, cfg.value))
const rows = computed(() => [[0, 0], [0, 1], [1, 0], [1, 1]].map(([x, y]) => [x, y, fires(!!x, !!y, cfg.value) ? 1 : 0]))
const isRow = ([x, y]) => x === +a.value && y === +b.value

const blur = e => e.currentTarget.blur()
</script>

<template>
  <div class="mp">
    <svg viewBox="0 0 520 260" class="net">
      <!-- synapses -->
      <line x1="95" y1="70" x2="368" y2="122" :class="['wire', { on: a }]" />
      <line x1="95" y1="190" x2="368" y2="138" :class="['wire', { on: b }]" />
      <circle cx="368" cy="122" r="6" :class="['exc', { on: a }]" />
      <circle v-if="cfg.b === 'exc'" cx="368" cy="138" r="6" :class="['exc', { on: b }]" />
      <circle v-else cx="368" cy="138" r="7" :class="['inh', { on: b }]" />
      <!-- axon -->
      <line x1="460" y1="130" x2="505" y2="130" :class="['wire', 'axon', { on: out }]" />
      <polygon points="505,122 518,130 505,138" :class="['head', { on: out }]" />

      <!-- input neurons (click to toggle) -->
      <g class="in" @click="a = !a">
        <circle cx="70" cy="70" r="28" :class="{ on: a }" />
        <text x="70" y="77" style="font-size:20px">A</text>
      </g>
      <g class="in" @click="b = !b">
        <circle cx="70" cy="190" r="28" :class="{ on: b }" />
        <text x="70" y="197" style="font-size:20px">B</text>
      </g>

      <!-- output neuron -->
      <circle cx="415" cy="130" r="45" :class="['cell', { on: out }]" />
      <text x="415" y="128" class="theta" style="font-size:20px">θ = {{ cfg.theta }}</text>
      <text x="415" y="150" class="state" style="font-size:12px">{{ out ? 'fires' : 'silent' }}</text>

      <text x="290" y="92" class="lbl" style="font-size:11px">excite</text>
      <text x="290" y="176" class="lbl" style="font-size:11px">{{ cfg.b === 'inh' ? 'inhibit' : 'excite' }}</text>
    </svg>

    <div class="side">
      <div class="nets">
        <button v-for="(c, k) in NETS" :key="k" :class="{ on: net === k }" @click="net = k; blur($event)">{{ c.label }}</button>
      </div>
      <table class="tt">
        <thead><tr><th>A</th><th>B</th><th>fires?</th></tr></thead>
        <tbody>
          <tr v-for="r in rows" :key="r.join()" :class="{ cur: isRow(r) }">
            <td>{{ r[0] }}</td><td>{{ r[1] }}</td><td :class="{ yes: r[2] }">{{ r[2] ? 'yes' : 'no' }}</td>
          </tr>
        </tbody>
      </table>
      <p class="fig">their Figure {{ cfg.fig }}</p>
    </div>
  </div>
</template>

<style scoped>
.mp { display: grid; grid-template-columns: 1fr 15rem; gap: 2rem; align-items: center; }
.net { width: 100%; max-height: 17rem; }
.wire { stroke: var(--fenbrook-rule); stroke-width: 3; transition: stroke 0.2s; }
.wire.on { stroke: var(--fenbrook-accent); }
.exc { fill: var(--fenbrook-fg-soft); }
.exc.on { fill: var(--fenbrook-accent); }
.inh { fill: var(--fenbrook-bg); stroke: var(--fenbrook-fg-soft); stroke-width: 3; }
.inh.on { stroke: #e06c6c; }
.head { fill: var(--fenbrook-rule); }
.head.on { fill: var(--fenbrook-accent); }
.in { cursor: pointer; }
.in circle { fill: var(--fenbrook-bg-elev); stroke: var(--fenbrook-rule); stroke-width: 2; transition: fill 0.2s; }
.in circle.on { fill: var(--fenbrook-accent); stroke: var(--fenbrook-accent); }
.in text { fill: var(--fenbrook-fg); text-anchor: middle; font-family: 'JetBrains Mono', monospace; font-weight: 700; pointer-events: none; }
.cell { fill: var(--fenbrook-bg-elev); stroke: var(--fenbrook-fg-soft); stroke-width: 2; transition: fill 0.2s; }
.cell.on { fill: var(--fenbrook-accent); stroke: var(--fenbrook-accent); }
.theta, .state, .lbl { text-anchor: middle; font-family: 'JetBrains Mono', monospace; }
.theta { fill: var(--fenbrook-fg); }
.cell.on ~ .theta, .cell.on ~ .state { fill: var(--fenbrook-bg); }
.state { fill: var(--fenbrook-muted); }
.lbl { fill: var(--fenbrook-muted); }
.side { display: grid; gap: 0.8rem; }
.nets { display: grid; gap: 0.4rem; }
.nets button {
  font: inherit; font-size: 0.9rem; cursor: pointer; padding: 0.4rem 0.8rem; border-radius: 8px; text-align: left;
  border: 1px solid var(--fenbrook-rule); background: transparent; color: var(--fenbrook-fg-soft);
}
.nets button.on { background: var(--fenbrook-accent); border-color: var(--fenbrook-accent); color: var(--fenbrook-bg); }
.tt { border-collapse: collapse; font-family: 'JetBrains Mono', monospace; font-size: 0.85rem; width: 100%; }
.tt :is(thead, tbody, tr) { background: transparent !important; }
.tt th, .tt td { border: none; padding: 0.2rem 0.5rem; text-align: center; color: var(--fenbrook-fg-soft); text-transform: none; }
.tt th { color: var(--fenbrook-muted); font-weight: 400; }
.tt tr.cur td { color: var(--fenbrook-fg); background: var(--fenbrook-bg-elev); }
.tt td.yes { color: var(--fenbrook-accent); }
.fig { margin: 0; font-family: 'JetBrains Mono', monospace; font-size: 0.7rem; color: var(--fenbrook-muted); }
</style>
