<script setup>
// The textbook overfitting picture: training loss keeps falling while
// validation loss bottoms out and climbs. Shapes follow the original slide.
// The default slot is a callout drawn in the middle of the plot.
const W = 640, H = 300, L = 60, B = 40, T = 20
const xs = e => L + (e / 100) * (W - L - 20)
const ys = v => T + (1 - v) * (H - T - B)
const train = e => 0.06 + 0.86 * Math.exp(-e / 28) + 0.04 * (1 - e / 100)
const val = e => 0.3 + 0.62 * Math.exp(-e / 18) + 0.000045 * Math.max(0, e - 45) ** 2.2
const pts = f => Array.from({ length: 101 }, (_, e) => `${xs(e).toFixed(1)},${ys(f(e)).toFixed(1)}`).join(' ')
</script>

<template>
  <div class="lc">
    <svg :viewBox="`0 0 ${W} ${H}`" role="img" aria-label="Loss by epoch: training loss keeps falling while validation loss falls, levels off, then rises">
      <line :x1="L" :y1="T" :x2="L" :y2="H - B" class="axis" />
      <line :x1="L" :y1="H - B" :x2="W - 10" :y2="H - B" class="axis" />
      <text :x="L - 14" :y="(T + H - B) / 2" class="lbl" text-anchor="end">Loss</text>
      <text :x="(L + W) / 2" :y="H - 10" class="lbl" text-anchor="middle">Epoch</text>
      <polyline :points="pts(val)" class="val" />
      <polyline :points="pts(train)" class="train" />
      <text :x="W - 20" :y="ys(val(100)) - 10" class="lg v" text-anchor="end">Validation data</text>
      <text :x="W - 20" :y="ys(train(100)) - 10" class="lg t" text-anchor="end">Training data</text>
    </svg>
    <div v-if="$slots.default" class="callout"><slot /></div>
  </div>
</template>

<style scoped>
.lc { position: relative; width: 100%; max-width: 760px; margin: 0 auto; }
svg { width: 100%; }
.axis { stroke: var(--fenbrook-fg, #eee); stroke-width: 2; }
.lbl { fill: var(--fenbrook-fg-soft, #ccc); font-size: 14px; }
.train { fill: none; stroke: #e8a33a; stroke-width: 3; }
.val { fill: none; stroke: #5b8fd6; stroke-width: 3; }
.lg { font-size: 13px; }
.lg.t { fill: #e8a33a; }
.lg.v { fill: #5b8fd6; }
.callout { position: absolute; left: 50%; top: 22%; transform: translateX(-30%); max-width: 16rem; padding: 0.5rem 0.9rem; border: 1.5px solid var(--fenbrook-fg, #eee); background: var(--fenbrook-bg, #111); font-size: 0.95rem; text-align: center; }
</style>
