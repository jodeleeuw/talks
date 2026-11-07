// Small helpers shared by the plotting widgets.

// Colours for up to six data series on the dark fenbrook background.
export const SERIES = ['#e0a87a', '#8fbcd4', '#a3c98a', '#d68fb0', '#b8a0e0', '#c8c2b6']

// Linear scale: maps [d0, d1] onto [r0, r1].
export const scale = (d0, d1, r0, r1) => v => r0 + ((v - d0) / (d1 - d0)) * (r1 - r0)

// SVG path through points [[x, y], …] (already in pixels).
export const path = pts => pts.map((p, i) => (i ? 'L' : 'M') + p[0].toFixed(1) + ',' + p[1].toFixed(1)).join('')

// Seeded random numbers, so "random" data look the same every time a slide
// is shown. mulberry32.
export function rng(seed = 1) {
  let a = seed >>> 0
  return () => {
    a = (a + 0x6d2b79f5) >>> 0
    let t = a
    t = Math.imul(t ^ (t >>> 15), t | 1)
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61)
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296
  }
}
// Standard normal draw from a uniform source.
export const gauss = r => Math.sqrt(-2 * Math.log(r() || 1e-12)) * Math.cos(2 * Math.PI * r())

// "Nice" tick values covering [lo, hi].
export function ticks(lo, hi, n = 5) {
  const span = hi - lo
  const step0 = span / n
  const mag = 10 ** Math.floor(Math.log10(step0))
  const step = [1, 2, 2.5, 5, 10].map(m => m * mag).find(s => s >= step0)
  const out = []
  for (let v = Math.ceil(lo / step) * step; v <= hi + 1e-9; v += step) out.push(+v.toFixed(10))
  return out
}
