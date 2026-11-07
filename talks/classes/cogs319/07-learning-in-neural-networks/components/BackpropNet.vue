<script setup>
// The small network from the backprop slides (inputs i1–i3, two hidden
// layers a and b, one output y′). `step` 1 highlights one weight to wiggle;
// step 2 adds an arrow running backwards from the output.
defineProps({ step: { type: Number, default: 0 } })
const COLS = [
  { x: 90, nodes: [['i1', 70], ['i2', 170], ['i3', 270]] },
  { x: 290, nodes: [['a1', 115], ['a2', 225]] },
  { x: 490, nodes: [['b1', 115], ['b2', 225]] },
  { x: 690, nodes: [["y′", 170]] },
]
const R = 34
const edges = COLS.slice(1).flatMap((C, k) => COLS[k].nodes.flatMap(([, y1], i) => C.nodes.map(([, y2], j) => ({ key: `${k}-${i}-${j}`, x1: COLS[k].x + R, y1, x2: C.x - R, y2 }))))
</script>

<template>
  <svg viewBox="40 20 720 300" class="bn" role="img" aria-label="A network with three inputs, two hidden layers of two units, and one output">
    <defs>
      <marker id="bn-a" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="7" markerHeight="7" orient="auto"><path d="M0,0 L10,5 L0,10 z" fill="#e0a87a" /></marker>
    </defs>
    <line v-for="e in edges" :key="e.key" v-bind="e" class="edge" :class="{ hot: step === 1 && e.key === '0-1-0' }" />
    <g v-for="C in COLS" :key="C.x">
      <g v-for="[t, y] in C.nodes" :key="t">
        <circle :cx="C.x" :cy="y" :r="R" class="node" />
        <text :x="C.x" :y="y + 7" class="lbl" text-anchor="middle">{{ t }}</text>
      </g>
    </g>
    <path v-if="step >= 2" d="M690,240 C640,300 160,310 100,300" class="back" marker-end="url(#bn-a)" />
  </svg>
</template>

<style scoped>
.bn { width: 100%; max-height: 330px; }
.node { fill: var(--fenbrook-bg, #111); stroke: var(--fenbrook-fg, #eee); stroke-width: 2; }
.lbl { fill: var(--fenbrook-fg, #eee); font-size: 20px; font-style: italic; }
.edge { stroke: var(--fenbrook-fg-soft, #ccc); stroke-width: 1.4; transition: stroke 0.3s; }
.edge.hot { stroke: var(--fenbrook-accent, #e0a87a); stroke-width: 4; }
.back { fill: none; stroke: var(--fenbrook-accent, #e0a87a); stroke-width: 2.4; stroke-dasharray: 6 5; }
</style>
