<script setup>
import { computed } from 'vue'

const props = defineProps({
  spec: { type: Object, required: true },
  // 'aspect' (default): wrapper locks itself to the spec's w/h aspect ratio
  // (current behavior — width: 100% drives height). 'container': wrapper
  // takes 100% × 100% of its parent and the SVG's preserveAspectRatio scales
  // the drawing to fit. Use 'container' when a sized flex/grid cell or a
  // height: <X>rem wrapper is providing the bounds and the default 16:9 would
  // overflow underneath a slide title or footer.
  fit: { type: String, default: 'aspect' },
})

const viewBox = computed(() => {
  const w = props.spec.w ?? 960
  const h = props.spec.h ?? 540
  return { w, h, attr: `0 0 ${w} ${h}` }
})

function anchorOffset(anchor, w, h) {
  if (anchor == null || anchor === 'top-left') return [0, 0]
  switch (anchor) {
    case 'top':          return [-w / 2, 0]
    case 'top-right':    return [-w,     0]
    case 'left':         return [0,     -h / 2]
    case 'center':       return [-w / 2, -h / 2]
    case 'right':        return [-w,     -h / 2]
    case 'bottom-left':  return [0,      -h]
    case 'bottom':       return [-w / 2, -h]
    case 'bottom-right': return [-w,     -h]
    default: throw new Error(`Diagram: unknown anchor "${anchor}"`)
  }
}

function applyAnchor(b) {
  const [dx, dy] = anchorOffset(b.anchor, b.w, b.h)
  return dx || dy ? { ...b, x: b.x + dx, y: b.y + dy } : b
}

function normalize(arr, rawLookup) {
  const resolved = new Map()
  const items = arr ?? []
  function resolve(b) {
    if (b.id && resolved.has(b.id)) return resolved.get(b.id)
    const anchored = applyAnchor(b)
    let { x, y } = anchored
    if (b.parent) {
      const p = rawLookup.get(b.parent)
      if (!p) throw new Error(`Diagram: unknown parent "${b.parent}"`)
      const pr = resolve(p)
      x += pr.x
      y += pr.y
    }
    const out = { ...anchored, x, y }
    if (b.id) resolved.set(b.id, out)
    return out
  }
  return items.map(resolve)
}

const rawLookup = computed(() => {
  const m = new Map()
  for (const b of props.spec.boxes ?? []) if (b.id) m.set(b.id, b)
  for (const g of props.spec.groups ?? []) if (g.id) m.set(g.id, g)
  return m
})

const boxes = computed(() => normalize(props.spec.boxes, rawLookup.value))
const groups = computed(() => normalize(props.spec.groups, rawLookup.value))
const connectors = computed(() => props.spec.connectors ?? [])

const lookup = computed(() => {
  const m = new Map()
  for (const b of boxes.value) if (b.id) m.set(b.id, b)
  for (const g of groups.value) if (g.id) m.set(g.id, g)
  return m
})

function snap(ref) {
  const [id, side = 'center'] = String(ref).split('.')
  const b = lookup.value.get(id)
  if (!b) throw new Error(`Diagram: unknown id "${id}"`)
  const { x, y, w, h } = b
  switch (side) {
    case 'top':    return [x + w / 2, y]
    case 'bottom': return [x + w / 2, y + h]
    case 'left':   return [x, y + h / 2]
    case 'right':  return [x + w, y + h / 2]
    case 'center': return [x + w / 2, y + h / 2]
    default: throw new Error(`Diagram: unknown side "${side}"`)
  }
}

function resolvePoint(p) {
  if (Array.isArray(p)) return [p[0], p[1]]
  if (typeof p === 'string') return snap(p)
  if (p && typeof p === 'object' && p.snap) {
    const [x, y] = snap(p.snap)
    return [x + (p.dx ?? 0), y + (p.dy ?? 0)]
  }
  throw new Error(`Diagram: cannot resolve point ${JSON.stringify(p)}`)
}

function resolveAxis(v, axis) {
  if (v == null) return null
  if (typeof v === 'number') return v
  if (typeof v === 'string') return snap(v)[axis]
  if (typeof v === 'object' && v.snap) return snap(v.snap)[axis] + (v.offset ?? 0)
  throw new Error(`Diagram: cannot resolve axis ${JSON.stringify(v)}`)
}

const ROUTE_ALIASES = {
  vh: 'VH', 'vertical-horizontal': 'VH',
  hv: 'HV', 'horizontal-vertical': 'HV',
}
function canonicalRoute(r) {
  if (r == null) return null
  const key = String(r).toLowerCase()
  if (ROUTE_ALIASES[key]) return ROUTE_ALIASES[key]
  throw new Error(`Diagram: unknown route "${r}" (use "VH"/"HV" or "vertical-horizontal"/"horizontal-vertical")`)
}

const SIDE_NORMAL = {
  top:    [0, -1],
  right:  [1,  0],
  bottom: [0,  1],
  left:   [-1, 0],
}

function snapInfo(ref) {
  // Extract { id, side } from a snap reference, or null if `ref` isn't snap-like.
  // Works for both bare "id.side" strings and { snap: "id.side", dx, dy } objects.
  let raw = null
  if (typeof ref === 'string') raw = ref
  else if (ref && typeof ref === 'object' && typeof ref.snap === 'string') raw = ref.snap
  if (!raw) return null
  const [id, side = 'center'] = raw.split('.')
  return { id, side }
}

function pickOutset(outset, end) {
  if (outset == null) return 0
  if (typeof outset === 'number') return outset
  if (typeof outset === 'object') return outset[end] ?? 0
  return 0
}

function pathFor(c) {
  if (c.d) return c.d
  const start = resolvePoint(c.from)
  const end = resolvePoint(c.to)

  // `outset` pushes each snapped endpoint perpendicular to its face by N px
  // before routing — matches PowerPoint's "bent connector" leave/arrive style
  // and lets self-loops on adjacent sides auto-route around the shape's corner.
  const fromSnap = snapInfo(c.from)
  const toSnap = snapInfo(c.to)
  const fromNormal = fromSnap ? SIDE_NORMAL[fromSnap.side] : null
  const toNormal = toSnap ? SIDE_NORMAL[toSnap.side] : null
  const fromOut = pickOutset(c.outset, 'from')
  const toOut = pickOutset(c.outset, 'to')
  const fromStub = (fromOut && fromNormal)
    ? [start[0] + fromNormal[0] * fromOut, start[1] + fromNormal[1] * fromOut]
    : null
  const toStub = (toOut && toNormal)
    ? [end[0] + toNormal[0] * toOut, end[1] + toNormal[1] * toOut]
    : null

  const points = [start]
  if (fromStub) points.push(fromStub)

  // route/via operate between the stubs (when present), so the perpendicular
  // approach segments are preserved at both ends.
  const innerStart = fromStub ?? start
  const innerEnd = toStub ?? end
  const route = canonicalRoute(c.route)
  if (route === 'VH') points.push([innerStart[0], innerEnd[1]])
  else if (route === 'HV') points.push([innerEnd[0], innerStart[1]])
  for (const v of c.via ?? []) {
    const [px, py] = points[points.length - 1]
    points.push([resolveAxis(v.x, 0) ?? px, resolveAxis(v.y, 1) ?? py])
  }

  // Self-loop auto-corner: from and to snap to the same shape on perpendicular
  // sides, with both stubs and no explicit route/via. The corner sits at the
  // intersection of the two stubs' axes — outside the shape, naturally.
  const selfLoop = fromSnap && toSnap
    && fromSnap.id === toSnap.id
    && fromNormal && toNormal
    && fromNormal[0] * toNormal[0] + fromNormal[1] * toNormal[1] === 0  // perpendicular
  if (selfLoop && !route && !(c.via && c.via.length) && fromStub && toStub) {
    const fromIsHoriz = fromNormal[0] !== 0
    const cornerX = fromIsHoriz ? fromStub[0] : toStub[0]
    const cornerY = fromIsHoriz ? toStub[1] : fromStub[1]
    points.push([cornerX, cornerY])
  }

  if (toStub) points.push(toStub)
  points.push(end)
  let path = `M ${points[0][0]} ${points[0][1]}`
  for (let i = 1; i < points.length; i++) {
    const [px, py] = points[i - 1]
    const [cx, cy] = points[i]
    if (cx === px && cy === py) continue
    if (cx === px) path += ` V ${cy}`
    else if (cy === py) path += ` H ${cx}`
    else path += ` L ${cx} ${cy}`
  }
  return path
}

function arrowMarkers(c) {
  // Normalize the connector's `arrow` field into { start, end } booleans.
  // Backwards-compatible defaults: unspecified or `true` → end-only (the
  // current behavior); `false` or `"none"` → no markers.
  const a = c.arrow
  let start = false, end = true
  if (a === false || a === 'none') { start = false; end = false }
  else if (a === true || a == null || a === 'forward') { start = false; end = true }
  else if (a === 'reverse') { start = true; end = false }
  else if (a === 'both') { start = true; end = true }
  else if (a && typeof a === 'object') { start = !!a.start; end = !!a.end }
  else throw new Error(`Diagram: unknown arrow "${a}" (use true/false/"forward"/"reverse"/"both"/"none")`)
  return {
    start: start ? 'url(#diagram-arrow-start)' : null,
    end: end ? 'url(#diagram-arrow)' : null,
  }
}

function clickDirective(item) {
  // Slidev's v-click normalizes `undefined`/`true`/`null` to `'+1'`, which
  // *consumes a sequential click* — so every always-visible box would steal a
  // click and balloon the slide's click count. Return `false` so the directive
  // becomes a no-op (resolveClick → calculate(false) → null → mounted returns).
  if (item.reveal && item.reveal.from != null) {
    // Slidev uses a half-open `[start, end)` range, so we map our inclusive
    // `to` to `to + 1`. `{from: 1, to: 1}` → `[1, 2]` → visible at click 1 only.
    return item.reveal.to != null
      ? [item.reveal.from, item.reveal.to + 1]
      : item.reveal.from
  }
  if (item.revealAt != null)
    return item.revealAt
  return false
}

// Multi-line text. Author can write either `lines: ["a", "b"]`, `text: ["a", "b"]`,
// or `text: "a\nb"` — all become an array of strings. Single-string text returns
// `[text]`. `null`/`undefined`/empty returns `[]` (text node is then skipped).
function textLines(item) {
  if (Array.isArray(item.lines)) return item.lines.filter(s => s != null)
  if (Array.isArray(item.text)) return item.text.filter(s => s != null)
  if (typeof item.text === 'string') {
    if (!item.text) return []
    return item.text.split('\n')
  }
  return []
}

// First-tspan dy that centers a block of N lines on the wrapper's y coordinate.
// dominant-baseline: middle puts each tspan's middle at its (x, y+dy). For an
// odd count (1, 3, …) the middle line sits on y; for an even count (2, 4, …)
// the centerline sits between two tspans.
function firstDy(n) {
  if (n <= 1) return 0
  return `${-((n - 1) / 2) * 1.2}em`
}

const wrapStyle = computed(() => {
  if (props.fit === 'container') return null
  // 'aspect' (default): lock wrapper to spec's aspect ratio so width drives height.
  return { aspectRatio: `${viewBox.value.w} / ${viewBox.value.h}` }
})
</script>

<template>
<div class="diagram" :class="`diagram--fit-${fit}`" :style="wrapStyle">
<svg :viewBox="viewBox.attr" preserveAspectRatio="xMidYMid meet">
<defs>
<marker id="diagram-arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M 0 0 L 10 5 L 0 10 Z" fill="currentColor" /></marker>
<marker id="diagram-arrow-start" viewBox="0 0 10 10" refX="1" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M 10 0 L 0 5 L 10 10 Z" fill="currentColor" /></marker>
</defs>
<g v-for="g in groups" :key="`g-${g.id}`" v-click="clickDirective(g)" :class="['group', g.style ? `group-${g.style}` : null]">
<ellipse v-if="g.shape === 'ellipse'" :cx="g.x + g.w / 2" :cy="g.y + g.h / 2" :rx="g.w / 2" :ry="g.h / 2" />
<rect v-else :x="g.x" :y="g.y" :width="g.w" :height="g.h" :rx="g.rx ?? 4" />
<text v-if="textLines(g).length" :x="g.x + g.w / 2" :y="g.y + g.h / 2">
<tspan v-for="(line, i) in textLines(g)" :key="i" :x="g.x + g.w / 2" :dy="i === 0 ? firstDy(textLines(g).length) : '1.2em'">{{ line }}</tspan>
</text>
</g>
<g v-for="(c, i) in connectors" :key="`c-${i}`" v-click="clickDirective(c)" :class="['connector', c.style ? `connector-${c.style}` : null]">
<path :d="pathFor(c)" :marker-start="arrowMarkers(c).start" :marker-end="arrowMarkers(c).end" />
</g>
<g v-for="b in boxes" :key="`b-${b.id}`" v-click="clickDirective(b)" :class="['box', b.style ? `box-${b.style}` : null]">
<ellipse v-if="b.shape === 'ellipse'" :cx="b.x + b.w / 2" :cy="b.y + b.h / 2" :rx="b.w / 2" :ry="b.h / 2" :style="b.fill ? { fill: b.fill } : null" />
<rect v-else :x="b.x" :y="b.y" :width="b.w" :height="b.h" :rx="b.rx ?? 3" :style="b.fill ? { fill: b.fill } : null" />
<text v-if="textLines(b).length" :x="b.x + b.w / 2" :y="b.y + b.h / 2">
<tspan v-for="(line, i) in textLines(b)" :key="i" :x="b.x + b.w / 2" :dy="i === 0 ? firstDy(textLines(b).length) : '1.2em'">{{ line }}</tspan>
</text>
</g>
</svg>
</div>
</template>

<style scoped>
.diagram { width: 100%; }
/* fit=container: take 100% of the parent's height. Parent must constrain it
   (e.g. a flex column with min-height: 0, or an explicit height). The SVG's
   preserveAspectRatio="xMidYMid meet" scales the drawing to fit. */
.diagram--fit-container { height: 100%; min-height: 0; min-width: 0; }
.diagram svg { width: 100%; height: 100%; display: block; }
.diagram text {
  fill: currentColor;
  text-anchor: middle;
  dominant-baseline: middle;
  font-family: inherit;
  font-size: 18px;
}
.diagram .box rect,
.diagram .box ellipse,
.diagram .group rect,
.diagram .group ellipse {
  fill: var(--slidev-theme-bg, transparent);
  stroke: currentColor;
  stroke-width: 1.5;
}
.diagram .group rect,
.diagram .group ellipse {
  stroke-dasharray: 4 4;
  opacity: 0.6;
}
.diagram .group text {
  font-size: 14px;
  letter-spacing: 0.15em;
  opacity: 0.6;
}
.diagram .connector path {
  fill: none;
  stroke: currentColor;
  stroke-width: 1.5;
}
</style>
