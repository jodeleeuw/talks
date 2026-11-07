<script setup>
// A fully connected feed-forward network drawn as circles and lines, with
// arrows coming into the first layer and leaving the last. Coordinates are in
// the original deck's 960×540 space; pass each layer's x and the y of each
// node's centre.
import { computed } from 'vue'

const props = defineProps({
  // [{ x, ys: [...], label?, labelY? }]
  layers: { type: Array, required: true },
  r: { type: Number, default: 40 },
  arrow: { type: Number, default: 100 }, // length of the in/out arrows
  viewBox: { type: String, required: true },
})

const edges = computed(() =>
  props.layers.slice(1).flatMap((L, k) => {
    const P = props.layers[k]
    return P.ys.flatMap(y1 => L.ys.map(y2 => ({
      x1: P.x + props.r, y1, x2: L.x - props.r, y2,
    })))
  }),
)
const first = computed(() => props.layers[0])
const last = computed(() => props.layers[props.layers.length - 1])
</script>

<template>
  <svg :viewBox="viewBox" class="net" role="img" aria-label="Diagram of a feed-forward neural network">
    <defs>
      <marker id="net-arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto">
        <path d="M0,0 L10,5 L0,10 z" class="head" />
      </marker>
    </defs>
    <line v-for="(e, i) in edges" :key="'e' + i" v-bind="e" class="edge" />
    <line v-for="y in first.ys" :key="'in' + y" :x1="first.x - r - arrow" :y1="y" :x2="first.x - r" :y2="y"
      class="edge" marker-end="url(#net-arrow)" />
    <line v-for="y in last.ys" :key="'out' + y" :x1="last.x + r" :y1="y" :x2="last.x + r + arrow" :y2="y"
      class="edge" marker-end="url(#net-arrow)" />
    <g v-for="(L, l) in layers" :key="'l' + l">
      <circle v-for="y in L.ys" :key="y" :cx="L.x" :cy="y" :r="r" class="node" />
      <text v-if="L.label" :x="L.x" :y="L.labelY" class="lbl">{{ L.label }}</text>
    </g>
  </svg>
</template>

<style scoped>
.net { width: 100%; }
.edge { stroke: var(--fenbrook-fg); stroke-width: 1.5; }
.head { fill: var(--fenbrook-fg); }
.node { fill: var(--fenbrook-bg); stroke: var(--fenbrook-fg); stroke-width: 2; }
.lbl { fill: var(--fenbrook-fg-soft); font-size: 15px; text-anchor: middle; }
</style>
