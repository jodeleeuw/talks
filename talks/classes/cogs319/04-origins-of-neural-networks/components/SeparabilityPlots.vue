<script setup>
// What a single-layer perceptron can't separate: a curved category boundary
// (left) and exclusive-OR (right). Dot positions and the dotted boundary are
// taken from the original Google Slides deck (960×540 coordinates).
// Each dot is [x, y, category].
const DOTS = [
  [605.1, 263.7, 0],
  [584.1, 295.7, 0],
  [653.1, 260.3, 0],
  [620.7, 321.4, 0],
  [662.7, 310.8, 0],
  [802.6, 432.8, 0],
  [566.4, 336.4, 0],
  [771.2, 413.6, 0],
  [685.1, 276.7, 0],
  [630.2, 288.4, 0],
  [739.9, 413.6, 0],
  [786.0, 382.5, 0],
  [726.1, 381.3, 0],
  [658.5, 402.0, 1],
  [610.7, 413.6, 1],
  [630.3, 380.4, 1],
  [649.5, 435.9, 1],
  [805.5, 254.3, 1],
  [815.5, 321.4, 1],
  [776.8, 286.1, 1],
  [739.9, 273.4, 1],
  [180.6, 263.7, 0],
  [159.6, 295.7, 0],
  [228.6, 260.3, 0],
  [196.2, 321.4, 0],
  [238.2, 310.8, 0],
  [173.8, 350.5, 0],
  [173.8, 379.6, 0],
  [364.5, 373.8, 0],
  [241.1, 391.2, 0],
  [218.6, 427.4, 0],
  [342.1, 343.7, 0],
  [391.3, 295.7, 0],
  [338.7, 282.6, 0],
  [284.8, 427.4, 1],
  [276.2, 333.1, 1],
  [302.8, 377.1, 1],
  [330.6, 404.9, 1],
  [364.8, 427.4, 1],
  [396.8, 427.4, 1],
  [410.2, 391.3, 1],
  [293.8, 299.0, 1],
  [767.9, 333.1, 1],
  [580.7, 391.3, 1],
  [815.5, 402.0, 0],
  [720.4, 336.4, 1],
]
const BOUNDARY = 'M244.2,443.1 C249.2,418.3 257.5,394.2 264.3,369.8 C268.2,355.6 258.5,340.4 260.4,325.9 C263.3,303.4 277.5,274.8 299.7,270.3 C304.2,269.4 307.3,275.7 309.8,279.6 C327.3,307.2 311.7,349.7 332.1,375.2 C341.5,386.9 361.3,400.5 373.8,392.2 C385.3,384.5 392.5,370.1 405.4,365.2 C417.4,360.6 431.0,362.3 443.2,358.3'
</script>

<template>
  <svg viewBox="80 225 805 290" class="sep" role="img"
    aria-label="Two scatter plots of light and dark dots. Left: the two kinds are split by a wavy dotted curve. Right: the light and dark dots sit in alternating quadrants, the exclusive-OR pattern, so no single straight line can split them.">
    <line x1="117.7" y1="233.3" x2="117.7" y2="473.2" class="axis" />
    <line x1="92.3" y1="452.3" x2="443.3" y2="452.3" class="axis" />
    <line x1="542.2" y1="233.3" x2="542.2" y2="473.2" class="axis" />
    <line x1="516.7" y1="452.3" x2="867.7" y2="452.3" class="axis" />
    <path :d="BOUNDARY" class="boundary" />
    <circle v-for="([x, y, c], i) in DOTS" :key="i" :cx="x" :cy="y" r="11.2" :class="c ? 'b' : 'a'" />
    <text x="277" y="500" class="lbl">Non-linear boundary</text>
    <text x="699" y="500" class="lbl">Exclusive-OR (XOR)</text>
  </svg>
</template>

<style scoped>
.sep { width: 100%; }
.axis { stroke: var(--fenbrook-fg); stroke-width: 2; }
.boundary { fill: none; stroke: var(--fenbrook-fg); stroke-width: 3; stroke-dasharray: 0.1 7; stroke-linecap: round; }
.a { fill: var(--fenbrook-fg); }
.b { fill: var(--fenbrook-accent-soft); }
.lbl { fill: var(--fenbrook-fg); font-size: 16px; font-weight: 600; text-anchor: middle; }
</style>
