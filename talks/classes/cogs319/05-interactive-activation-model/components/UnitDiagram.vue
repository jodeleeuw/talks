<script setup>
// The letter unit A and its neighbours, built up click by click: feature
// units below (/ excites A, | inhibits it), a rival letter B beside it, and
// word units above (ABLE excites A, BALL inhibits it). White arrows are
// excitatory, red ones inhibitory. `step` is how many parts are shown.
defineProps({ step: { type: Number, default: 0 } })
</script>

<template>
  <svg viewBox="0 0 470 420" class="ud" role="img" aria-label="Letter unit A with feature, letter and word connections">
    <defs>
      <marker id="ud-w" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto"><path d="M0,0 L10,5 L0,10 z" fill="#e8e3d8" /></marker>
      <marker id="ud-r" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto"><path d="M0,0 L10,5 L0,10 z" fill="#e0453a" /></marker>
    </defs>
    <g v-if="step >= 3">
      <ellipse cx="200" cy="40" rx="78" ry="32" class="n" /><text x="200" y="47" class="t" text-anchor="middle">ABLE</text>
      <ellipse cx="400" cy="40" rx="66" ry="32" class="n" /><text x="400" y="47" class="t" text-anchor="middle">BALL</text>
      <path d="M200,72 C200,105 196,118 196,148" class="exc" marker-end="url(#ud-w)" />
      <path d="M380,72 C360,120 280,120 226,158" class="inh" marker-end="url(#ud-r)" />
    </g>
    <g v-if="step >= 2">
      <circle cx="80" cy="190" r="34" class="n" /><text x="80" y="198" class="t" text-anchor="middle">B</text>
      <path d="M80,156 C90,120 140,126 162,160" class="inh" marker-end="url(#ud-r)" />
    </g>
    <g v-if="step >= 1">
      <circle cx="110" cy="365" r="34" class="n" /><text x="110" y="373" class="t" text-anchor="middle">/</text>
      <circle cx="270" cy="365" r="34" class="n" /><text x="270" y="373" class="t" text-anchor="middle">|</text>
      <path d="M110,331 C110,280 170,270 180,226" class="exc" marker-end="url(#ud-w)" />
      <path d="M270,331 C270,280 220,270 212,226" class="inh" marker-end="url(#ud-r)" />
    </g>
    <circle cx="196" cy="190" r="36" class="n" /><text x="196" y="198" class="t" text-anchor="middle">A</text>
  </svg>
</template>

<style scoped>
.ud { width: 100%; max-height: 400px; }
.n { fill: var(--fenbrook-bg, #111); stroke: var(--fenbrook-fg, #eee); stroke-width: 2.4; }
.t { fill: var(--fenbrook-fg, #eee); font-family: 'JetBrains Mono', monospace; font-weight: 700; font-size: 22px; }
.exc { fill: none; stroke: #e8e3d8; stroke-width: 2; }
.inh { fill: none; stroke: #e0453a; stroke-width: 2; }
</style>
