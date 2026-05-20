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
  // Treat the first `startAt` clicks of the spec as having already happened.
  // The diagram opens in its click-`startAt` state; subsequent `revealAt: N`
  // values still advance on user clicks (their effective click index becomes
  // `N - startAt`). Lets one spec be reused across multiple slides — the
  // follow-up slide opens with the build-up "frozen" mid-sequence without a
  // duplicate spec. Setting `startAt >= max(revealAt)` freezes at the end
  // state. The slide's click count is `max(revealAt) - startAt`.
  startAt: { type: Number, default: 0 },
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

// --- startAt shifting --------------------------------------------------------
//
// When `startAt > 0`, every reveal/hide/textByClick directive on every item is
// rewritten as if the first `startAt` clicks already happened. Geometry (and
// the parent/raw lookup it feeds) is left untouched — only click bindings
// shift. An item whose revealing window has fully closed is dropped entirely.
//
// `reveal: { from, to | until }` with `from - startAt <= 0` collapses to
// `hideAt`-mode (visible at start, hidden after the upper bound) because the
// existing `clickDirective` requires a `from` when reading `to`/`until`.
//
// `textByClick` keys also shift; the most-recent past entry becomes the new
// click-0 state (either as an explicit `"0"` key when future entries remain,
// or by overwriting the static `text`/`lines` when no future entries do).

function shiftItem(item) {
  if (!props.startAt) return item
  const offset = props.startAt
  // Deep clone via JSON round-trip — spec values are JSON-only (numbers,
  // strings, arrays, plain objects) so this is safe and cheap.
  const out = JSON.parse(JSON.stringify(item))

  if (out.hideAt != null) {
    const s = out.hideAt - offset
    if (s <= 0) return null   // already past the hide point
    out.hideAt = s
  }

  if (out.revealAt != null) {
    const s = out.revealAt - offset
    if (s <= 0) delete out.revealAt   // already visible
    else out.revealAt = s
  }

  if (out.reveal && typeof out.reveal === 'object') {
    const r = out.reveal
    const fromS = r.from != null ? r.from - offset : null
    const toS = r.to != null ? r.to - offset : null
    const untilS = r.until != null ? r.until - offset : null
    if (toS != null && toS < 0) return null
    if (untilS != null && untilS <= 0) return null
    if (fromS == null || fromS <= 0) {
      // No active lower bound — collapse to hideAt form (or always-visible).
      delete out.reveal
      if (toS != null) out.hideAt = toS + 1
      else if (untilS != null) out.hideAt = untilS
    } else {
      const next = { from: fromS }
      if (toS != null) next.to = toS
      if (untilS != null) next.until = untilS
      out.reveal = next
    }
  }

  if (out.textByClick && typeof out.textByClick === 'object') {
    const keys = Object.keys(out.textByClick)
      .map(k => Number(k))
      .filter(n => Number.isFinite(n) && n >= 0)
      .sort((a, b) => a - b)
    const next = {}
    let initial = null
    let hadPast = false
    for (const k of keys) {
      const s = k - offset
      if (s <= 0) {
        initial = out.textByClick[String(k)]
        hadPast = true
      } else {
        next[String(s)] = out.textByClick[String(k)]
      }
    }
    if (Object.keys(next).length > 0) {
      if (hadPast) next['0'] = initial
      out.textByClick = next
    } else {
      delete out.textByClick
      if (hadPast) {
        if (Array.isArray(initial)) {
          out.lines = initial
          delete out.text
        } else if (typeof initial === 'string') {
          out.text = initial
          delete out.lines
        } else if (initial != null) {
          out.text = String(initial)
        }
      }
    }
  }

  return out
}

function shiftList(arr) {
  if (!props.startAt) return arr ?? []
  return (arr ?? []).map(shiftItem).filter(x => x != null)
}

// rawLookup is built from the **unshifted** spec so parent/snap resolution
// stays geometrically correct even when the parent box is dropped by startAt.
// (Coordinates don't depend on click visibility.)
const rawLookup = computed(() => {
  const m = new Map()
  for (const b of props.spec.boxes ?? []) if (b.id) m.set(b.id, b)
  for (const g of props.spec.groups ?? []) if (g.id) m.set(g.id, g)
  return m
})

const boxes = computed(() => normalize(shiftList(props.spec.boxes), rawLookup.value))
const groups = computed(() => normalize(shiftList(props.spec.groups), rawLookup.value))
const connectors = computed(() => shiftList(props.spec.connectors))
// Plain x/y axes for chart-style diagrams. Each axis: `kind` ('vertical' |
// 'horizontal'), the perpendicular coord (`x` for vertical, `y` for
// horizontal), and `from`/`to` along the parallel coord. Optional `label`
// renders at the `labelAt` end (`'from'` default, `'to'`, or a number in
// [0, 1]). Reveal/hide directives are honored like any other item.
const axes = computed(() => shiftList(props.spec.axes))

// `background` (single object) is syntactic sugar that prepends to `backgrounds`.
// Both fields render as <image> elements under groups/connectors/boxes, sharing
// the SVG's viewBox so annotations and raster live in one coordinate system.
const backgrounds = computed(() => {
  const out = []
  if (props.spec.background) out.push(props.spec.background)
  if (Array.isArray(props.spec.backgrounds)) out.push(...props.spec.backgrounds)
  return shiftList(out)
})

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
  // Snap references resolve to the box's bounding-box edges regardless of
  // `shape` (rect, ellipse, arrow, …). Connectors anchored to an arrow box
  // land on the arrow's bbox edges, not on the polygon silhouette — same
  // behavior as ellipse, where snap refs use the enclosing rect not the curve.
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

function axisGeometry(a) {
  if (a.kind === 'vertical') {
    if (a.x == null || a.from == null || a.to == null) {
      throw new Error('Diagram: vertical axis needs x, from, to')
    }
    return { x1: a.x, y1: a.from, x2: a.x, y2: a.to }
  }
  if (a.kind === 'horizontal') {
    if (a.y == null || a.from == null || a.to == null) {
      throw new Error('Diagram: horizontal axis needs y, from, to')
    }
    return { x1: a.from, y1: a.y, x2: a.to, y2: a.y }
  }
  throw new Error(`Diagram: unknown axis kind "${a.kind}" (use "vertical" or "horizontal")`)
}

// Default label end: 'from' for vertical (top), 'to' for horizontal (right) —
// matches the conventional "↑ y-axis" / "x-axis →" reading direction. Override
// with `labelAt: 'from' | 'to'` or a numeric t in [0, 1] for midpoint labels.
function axisLabelInfo(a) {
  if (a.label == null || a.label === '') return null
  const g = axisGeometry(a)
  const at = a.labelAt ?? (a.kind === 'vertical' ? 'from' : 'to')
  const pad = 10
  let x, y, anchor, baseline
  if (a.kind === 'vertical') {
    x = g.x1
    if (at === 'from') { y = Math.min(g.y1, g.y2) - pad; anchor = 'middle'; baseline = 'auto' }
    else if (at === 'to') { y = Math.max(g.y1, g.y2) + pad; anchor = 'middle'; baseline = 'hanging' }
    else if (typeof at === 'number') {
      const t = Math.max(0, Math.min(1, at))
      y = (1 - t) * g.y1 + t * g.y2
      x = g.x1 - pad
      anchor = 'end'; baseline = 'middle'
    } else throw new Error(`Diagram: unknown axis labelAt "${at}"`)
  } else {
    y = g.y1
    if (at === 'from') { x = Math.min(g.x1, g.x2) - pad; anchor = 'end'; baseline = 'middle' }
    else if (at === 'to') { x = Math.max(g.x1, g.x2) + pad; anchor = 'start'; baseline = 'middle' }
    else if (typeof at === 'number') {
      const t = Math.max(0, Math.min(1, at))
      x = (1 - t) * g.x1 + t * g.x2
      y = g.y1 + pad
      anchor = 'middle'; baseline = 'hanging'
    } else throw new Error(`Diagram: unknown axis labelAt "${at}"`)
  }
  const dx = a.labelOffset?.dx ?? 0
  const dy = a.labelOffset?.dy ?? 0
  return { x: x + dx, y: y + dy, anchor, baseline, text: a.label }
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

// --- Reveal / hide directives ------------------------------------------------
//
// Two output channels:
//   * `clickDirective(item)` — value for `v-click` (show-when-active semantics).
//   * `hideDirective(item)`  — value for `v-click-hide` (hide-when-active),
//                              used only when the item asks for hide-from-N
//                              behavior (visible at start, hidden from N on).
//
// `isHideMode(item)` decides which channel renders the item. We render exactly
// one `<g>` per item; the template's `v-if/v-else` picks the directive.
//
// Slidev caveats baked in here:
//   * `v-click` normalizes any value `<= 0` (and `undefined`/`true`/`null`) to
//     `1` with a warning, so we return `false` for always-visible items —
//     resolveClick → calculate(false) → null → the directive becomes a no-op.
//   * Inclusive `to:` is translated to half-open `to + 1` for `v-click` ranges.
//   * `v-click-hide="N"` is hide-when-active, so `hideAt: N` (visible at start,
//     hidden from click N on) maps cleanly to `v-click-hide="N"` — no
//     normalization issue because Slidev only normalizes the value passed in,
//     not the start of the range.

function hideValue(item) {
  // Extract the "hide at this click" value if the item is in hide-mode.
  // Returns `null` if the item is a normal show-mode item.
  if (item.hideAt != null) return item.hideAt
  if (item.reveal && item.reveal.until != null && item.reveal.from == null) {
    return item.reveal.until
  }
  return null
}

function isHideMode(item) {
  return hideValue(item) != null
}

function clickDirective(item) {
  if (item.reveal && item.reveal.from != null) {
    // `reveal: { from: A, until: B }` → half-open `[A, B)` (matches Slidev
    // semantics directly: visible from A through B-1).
    if (item.reveal.until != null) {
      return [item.reveal.from, item.reveal.until]
    }
    // `reveal: { from: A, to: B }` is inclusive — translate to `[A, B + 1]`.
    return item.reveal.to != null
      ? [item.reveal.from, item.reveal.to + 1]
      : item.reveal.from
  }
  if (item.revealAt != null)
    return item.revealAt
  return false
}

function hideDirective(item) {
  // Only invoked from the template when `isHideMode(item)` is true.
  return hideValue(item)
}

// --- Text rendering ----------------------------------------------------------

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

// Coerce a `textByClick` value (string | string[]) into an array of lines.
// Anything else (null/undefined/non-string/non-array) becomes an empty array,
// which renders nothing for that state.
function linesFromValue(v) {
  if (Array.isArray(v)) return v.filter(s => s != null).map(String)
  if (v == null) return []
  if (typeof v === 'string') return v ? v.split('\n') : []
  return [String(v)]
}

// --- Per-click text swaps (`textByClick`) ------------------------------------
//
// `textByClick: { "<N>": <string | string[]>, ... }` swaps the text content of
// a stable box/group as clicks advance. The mapping is last-key-wins: the
// largest key `<= current click` decides what to render. Keys are numbers.
//
//   - Key "0" (if present) replaces the box's static `text`/`lines` as the
//     initial state.
//   - If `text`/`lines` is set and no explicit "0" key exists, the static
//     content fills the click-0 default until the smallest `textByClick` key
//     fires.
//   - If neither is set for click 0, the box renders no text until the first
//     key fires.
//
// Geometry never changes — only the rendered text content. Each state is a
// separate `<g>` with its own `v-click` / `v-click-hide` directive, so total
// click counts are derived automatically (every state's bound participates
// in Slidev's `maxMap`).
function textByClickStates(item) {
  const tbc = item.textByClick
  if (!tbc || typeof tbc !== 'object') return []
  const keys = Object.keys(tbc)
    .map(k => Number(k))
    .filter(n => Number.isFinite(n) && n >= 0)
    .sort((a, b) => a - b)
  if (keys.length === 0) return []

  const states = []

  // Static `text`/`lines` fills the click-0 slot when no explicit "0" key.
  if (keys[0] !== 0) {
    const defaultLines = textLines(item)
    if (defaultLines.length) {
      // Visible from start through (keys[0] - 1) inclusive. Use v-click-hide
      // because v-click clamps `0` to `1` (which would skip click 0).
      states.push({ mode: 'hide-at', value: keys[0], lines: defaultLines })
    }
  }

  for (let i = 0; i < keys.length; i++) {
    const k = keys[i]
    const lines = linesFromValue(tbc[String(k)])
    if (!lines.length) continue
    const isLast = i === keys.length - 1
    if (isLast) {
      if (k === 0) {
        // Only state and it starts at 0 → always visible, no directive.
        states.push({ mode: 'none', lines })
      } else {
        states.push({ mode: 'show-at', value: k, lines })
      }
    } else {
      const next = keys[i + 1]
      if (k === 0) {
        // From start through (next - 1). Same v-click(0) clamp issue → hide-at.
        states.push({ mode: 'hide-at', value: next, lines })
      } else {
        // Half-open [k, next): matches Slidev's range semantics directly.
        states.push({ mode: 'range', value: [k, next], lines })
      }
    }
  }
  return states
}

// First-tspan dy that centers a block of N lines on the wrapper's y coordinate.
// dominant-baseline: middle puts each tspan's middle at its (x, y+dy). For an
// odd count (1, 3, …) the middle line sits on y; for an even count (2, 4, …)
// the centerline sits between two tspans.
function firstDy(n) {
  if (n <= 1) return 0
  return `${-((n - 1) / 2) * 1.2}em`
}

// Rotation transform for text. Author can pass a numeric angle in CSS degrees
// (positive = clockwise) or the shorthands `"vertical-up"` / `"vertical-down"`.
// Returns `null` when no rotation is requested so the attribute is omitted.
function textRotation(item, cx, cy) {
  const r = item.textRotate
  if (r == null) return null
  let deg
  if (typeof r === 'number') deg = r
  else if (r === 'vertical-up') deg = -90
  else if (r === 'vertical-down') deg = 90
  else throw new Error(`Diagram: unknown textRotate "${r}" (use number, "vertical-up", or "vertical-down")`)
  if (!deg) return null
  return `rotate(${deg} ${cx} ${cy})`
}

// --- Arrow shapes ------------------------------------------------------------
//
// `shape: "arrow" | "rightArrow" | "leftArrow" | "upArrow" | "downArrow"`
// renders a PPTX-style chunky arrow (rectangular stem + triangular head).
// Geometry: head occupies 35% of the long dimension, stem the other 65%.
// Stem is 50% of the cross-dimension wide; head is the full cross-dimension.
// The polygon is drawn inside the box's bbox; snap refs still resolve to the
// bbox edges so connectors anchored to an arrow land where you'd expect.

const ARROW_HEAD_FRAC = 0.35
const ARROW_STEM_FRAC = 0.5    // stem width as a fraction of the cross-dimension

function arrowDirection(shape) {
  if (shape === 'arrow' || shape === 'rightArrow') return 'right'
  if (shape === 'leftArrow') return 'left'
  if (shape === 'upArrow') return 'up'
  if (shape === 'downArrow') return 'down'
  return null
}

function isArrowShape(item) {
  return arrowDirection(item.shape) != null
}

// `shape: "roundRect"` renders through the same <rect> branch as the default,
// but with a default `rx` that visibly rounds the corners — matches PPTX's
// `prstGeom prst="roundRect"`. Explicit `rx` on the spec still wins.
// Snap refs continue to resolve to the bbox edges (same as rect/ellipse/arrow).
const ROUND_RECT_RX_FRAC = 0.15
const ROUND_RECT_RX_MAX = 30
function isRoundRect(item) {
  return item.shape === 'roundRect'
}
function rectRx(item, fallback) {
  if (item.rx != null) return item.rx
  if (isRoundRect(item)) {
    return Math.min(Math.min(item.w, item.h) * ROUND_RECT_RX_FRAC, ROUND_RECT_RX_MAX)
  }
  return fallback
}

function arrowPoints(item) {
  const { x, y, w, h } = item
  const dir = arrowDirection(item.shape)
  const head = ARROW_HEAD_FRAC
  const stemHalf = ARROW_STEM_FRAC / 2   // stem extends ±stemHalf from the long axis
  let pts
  if (dir === 'right') {
    // Stem on left, head on right. Long axis = x.
    const sx = x + (1 - head) * w
    const t = y + (0.5 - stemHalf) * h
    const b = y + (0.5 + stemHalf) * h
    pts = [
      [x, t], [sx, t], [sx, y], [x + w, y + h / 2], [sx, y + h], [sx, b], [x, b],
    ]
  } else if (dir === 'left') {
    const sx = x + head * w
    const t = y + (0.5 - stemHalf) * h
    const b = y + (0.5 + stemHalf) * h
    pts = [
      [x + w, t], [sx, t], [sx, y], [x, y + h / 2], [sx, y + h], [sx, b], [x + w, b],
    ]
  } else if (dir === 'down') {
    const sy = y + (1 - head) * h
    const l = x + (0.5 - stemHalf) * w
    const r = x + (0.5 + stemHalf) * w
    pts = [
      [l, y], [l, sy], [x, sy], [x + w / 2, y + h], [x + w, sy], [r, sy], [r, y],
    ]
  } else if (dir === 'up') {
    const sy = y + head * h
    const l = x + (0.5 - stemHalf) * w
    const r = x + (0.5 + stemHalf) * w
    pts = [
      [l, y + h], [l, sy], [x, sy], [x + w / 2, y], [x + w, sy], [r, sy], [r, y + h],
    ]
  }
  return pts.map(([px, py]) => `${px},${py}`).join(' ')
}

// Text inside an arrow centers within the stem area (not the head triangle),
// so labels on vertical arrows don't drift into the arrowhead.
function textCenter(item) {
  const { x, y, w, h } = item
  const dir = arrowDirection(item.shape)
  if (!dir) return { cx: x + w / 2, cy: y + h / 2 }
  const head = ARROW_HEAD_FRAC
  if (dir === 'right') return { cx: x + (1 - head) / 2 * w, cy: y + h / 2 }
  if (dir === 'left')  return { cx: x + head * w + (1 - head) / 2 * w, cy: y + h / 2 }
  if (dir === 'down')  return { cx: x + w / 2, cy: y + (1 - head) / 2 * h }
  if (dir === 'up')    return { cx: x + w / 2, cy: y + head * h + (1 - head) / 2 * h }
  return { cx: x + w / 2, cy: y + h / 2 }
}

// --- Wrapped text (foreignObject) -------------------------------------------
//
// When `wrap: true` (or `maxWidth: <px>` is set), text is rendered via
// `<foreignObject>` + a centered `<div>` so the browser handles word-wrap.
// Backward compat: without `wrap`/`maxWidth`, fall through to the existing
// `<text>` + `<tspan>` rendering so existing decks render byte-identically.

const WRAP_PADDING = 8   // px breathing room inside the box

function isWrapped(item) {
  return item.wrap === true || item.maxWidth != null
}

function wrapBounds(item) {
  const { x, y, w, h } = item
  const padX = WRAP_PADDING
  const padY = WRAP_PADDING / 2
  const innerW = item.maxWidth != null
    ? Math.min(item.maxWidth, w - padX * 2)
    : w - padX * 2
  const fx = x + (w - innerW) / 2
  return { fx, fy: y + padY, fw: Math.max(0, innerW), fh: Math.max(0, h - padY * 2) }
}

function wrapText(item) {
  // Same source-of-truth as textLines, but joined with explicit <br/>s so
  // author-controlled line breaks survive wrapping.
  return textLines(item)
}

// --- Connector labels --------------------------------------------------------
//
// `label: "<string>"` on a connector renders a plain `<text>` along the path.
// Position is controlled by `labelAt`:
//   - `'start'`  → at the path's start tip (the `from` end).
//   - `'end'`    → at the path's end tip (the `to` end). Default.
//   - <number>   → fraction t in [0, 1] along the straight line between the
//                  two terminal coords. Suitable for straight/orthogonal paths.
//
// `labelOffset: { dx?, dy? }` shifts the anchor from the computed point.
// Defaults: `'end'` → `{ dx: 8, dy: 0 }`, `'start'` → `{ dx: -8, dy: 0 }`,
// numeric → `{ dx: 0, dy: -10 }`. Text alignment follows `labelAt`:
// `'end'` → left-aligned, `'start'` → right-aligned, numeric → centered.
//
// Reveal/hide on the connector still apply to the label (it lives inside the
// connector's `<g>`, so it inherits the directive).
function labelInfo(c) {
  if (c.label == null || c.label === '') return null
  // Labels rely on resolvable `from`/`to` endpoints. Connectors using a raw
  // `d:` path string don't expose terminal coords, so labels are unsupported
  // there — the author can fall back to a no-border text box if needed.
  if (c.from == null || c.to == null) return null
  const at = c.labelAt ?? 'end'
  const start = resolvePoint(c.from)
  const end = resolvePoint(c.to)
  let x, y, anchor
  if (at === 'start') {
    x = start[0]; y = start[1]; anchor = 'end'
  } else if (at === 'end') {
    x = end[0]; y = end[1]; anchor = 'start'
  } else if (typeof at === 'number') {
    const t = Math.max(0, Math.min(1, at))
    x = (1 - t) * start[0] + t * end[0]
    y = (1 - t) * start[1] + t * end[1]
    anchor = 'middle'
  } else {
    throw new Error(`Diagram: unknown labelAt "${at}" (use "start", "end", or number in [0, 1])`)
  }
  const defaultDx = at === 'start' ? -8 : at === 'end' ? 8 : 0
  const defaultDy = typeof at === 'number' ? -10 : 0
  const dx = c.labelOffset?.dx ?? defaultDx
  const dy = c.labelOffset?.dy ?? defaultDy
  return { x: x + dx, y: y + dy, anchor, text: c.label }
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
<template v-for="(bg, bi) in backgrounds" :key="`bg-${bi}`">
<g v-if="isHideMode(bg)" v-click-hide="hideDirective(bg)" class="background">
<image :href="bg.src" :x="bg.x" :y="bg.y" :width="bg.w" :height="bg.h" :opacity="bg.opacity ?? 1" preserveAspectRatio="none" />
</g>
<g v-else v-click="clickDirective(bg)" class="background">
<image :href="bg.src" :x="bg.x" :y="bg.y" :width="bg.w" :height="bg.h" :opacity="bg.opacity ?? 1" preserveAspectRatio="none" />
</g>
</template>
<template v-for="(a, ai) in axes" :key="`ax-${ai}`">
<g v-if="isHideMode(a)" v-click-hide="hideDirective(a)" :class="['axis', a.style ? `axis-${a.style}` : null]">
<line :x1="axisGeometry(a).x1" :y1="axisGeometry(a).y1" :x2="axisGeometry(a).x2" :y2="axisGeometry(a).y2" />
<text v-if="axisLabelInfo(a)" class="axis-label" :x="axisLabelInfo(a).x" :y="axisLabelInfo(a).y" :style="{ textAnchor: axisLabelInfo(a).anchor, dominantBaseline: axisLabelInfo(a).baseline }">{{ axisLabelInfo(a).text }}</text>
</g>
<g v-else v-click="clickDirective(a)" :class="['axis', a.style ? `axis-${a.style}` : null]">
<line :x1="axisGeometry(a).x1" :y1="axisGeometry(a).y1" :x2="axisGeometry(a).x2" :y2="axisGeometry(a).y2" />
<text v-if="axisLabelInfo(a)" class="axis-label" :x="axisLabelInfo(a).x" :y="axisLabelInfo(a).y" :style="{ textAnchor: axisLabelInfo(a).anchor, dominantBaseline: axisLabelInfo(a).baseline }">{{ axisLabelInfo(a).text }}</text>
</g>
</template>
<template v-for="g in groups" :key="`g-${g.id}`">
<g v-if="isHideMode(g)" v-click-hide="hideDirective(g)" :class="['group', g.style ? `group-${g.style}` : null]">
<ellipse v-if="g.shape === 'ellipse'" :cx="g.x + g.w / 2" :cy="g.y + g.h / 2" :rx="g.w / 2" :ry="g.h / 2" />
<polygon v-else-if="isArrowShape(g)" :points="arrowPoints(g)" />
<rect v-else :x="g.x" :y="g.y" :width="g.w" :height="g.h" :rx="rectRx(g, 4)" />
<template v-if="textByClickStates(g).length">
<template v-for="(state, si) in textByClickStates(g)" :key="`s-${si}`">
<g v-if="state.mode === 'hide-at'" v-click-hide="state.value">
<foreignObject v-if="isWrapped(g)" :x="wrapBounds(g).fx" :y="wrapBounds(g).fy" :width="wrapBounds(g).fw" :height="wrapBounds(g).fh" :transform="textRotation(g, textCenter(g).cx, textCenter(g).cy)">
<div xmlns="http://www.w3.org/1999/xhtml" class="diagram-wrap-text"><template v-for="(line, li) in state.lines" :key="li"><br v-if="li > 0" />{{ line }}</template></div>
</foreignObject>
<text v-else :x="textCenter(g).cx" :y="textCenter(g).cy" :transform="textRotation(g, textCenter(g).cx, textCenter(g).cy)">
<tspan v-for="(line, li) in state.lines" :key="li" :x="textCenter(g).cx" :dy="li === 0 ? firstDy(state.lines.length) : '1.2em'">{{ line }}</tspan>
</text>
</g>
<g v-else-if="state.mode === 'none'">
<foreignObject v-if="isWrapped(g)" :x="wrapBounds(g).fx" :y="wrapBounds(g).fy" :width="wrapBounds(g).fw" :height="wrapBounds(g).fh" :transform="textRotation(g, textCenter(g).cx, textCenter(g).cy)">
<div xmlns="http://www.w3.org/1999/xhtml" class="diagram-wrap-text"><template v-for="(line, li) in state.lines" :key="li"><br v-if="li > 0" />{{ line }}</template></div>
</foreignObject>
<text v-else :x="textCenter(g).cx" :y="textCenter(g).cy" :transform="textRotation(g, textCenter(g).cx, textCenter(g).cy)">
<tspan v-for="(line, li) in state.lines" :key="li" :x="textCenter(g).cx" :dy="li === 0 ? firstDy(state.lines.length) : '1.2em'">{{ line }}</tspan>
</text>
</g>
<g v-else v-click="state.value">
<foreignObject v-if="isWrapped(g)" :x="wrapBounds(g).fx" :y="wrapBounds(g).fy" :width="wrapBounds(g).fw" :height="wrapBounds(g).fh" :transform="textRotation(g, textCenter(g).cx, textCenter(g).cy)">
<div xmlns="http://www.w3.org/1999/xhtml" class="diagram-wrap-text"><template v-for="(line, li) in state.lines" :key="li"><br v-if="li > 0" />{{ line }}</template></div>
</foreignObject>
<text v-else :x="textCenter(g).cx" :y="textCenter(g).cy" :transform="textRotation(g, textCenter(g).cx, textCenter(g).cy)">
<tspan v-for="(line, li) in state.lines" :key="li" :x="textCenter(g).cx" :dy="li === 0 ? firstDy(state.lines.length) : '1.2em'">{{ line }}</tspan>
</text>
</g>
</template>
</template>
<template v-else-if="textLines(g).length">
<foreignObject v-if="isWrapped(g)" :x="wrapBounds(g).fx" :y="wrapBounds(g).fy" :width="wrapBounds(g).fw" :height="wrapBounds(g).fh" :transform="textRotation(g, textCenter(g).cx, textCenter(g).cy)">
<div xmlns="http://www.w3.org/1999/xhtml" class="diagram-wrap-text"><template v-for="(line, i) in wrapText(g)" :key="i"><br v-if="i > 0" />{{ line }}</template></div>
</foreignObject>
<text v-else :x="textCenter(g).cx" :y="textCenter(g).cy" :transform="textRotation(g, textCenter(g).cx, textCenter(g).cy)">
<tspan v-for="(line, i) in textLines(g)" :key="i" :x="textCenter(g).cx" :dy="i === 0 ? firstDy(textLines(g).length) : '1.2em'">{{ line }}</tspan>
</text>
</template>
</g>
<g v-else v-click="clickDirective(g)" :class="['group', g.style ? `group-${g.style}` : null]">
<ellipse v-if="g.shape === 'ellipse'" :cx="g.x + g.w / 2" :cy="g.y + g.h / 2" :rx="g.w / 2" :ry="g.h / 2" />
<polygon v-else-if="isArrowShape(g)" :points="arrowPoints(g)" />
<rect v-else :x="g.x" :y="g.y" :width="g.w" :height="g.h" :rx="rectRx(g, 4)" />
<template v-if="textByClickStates(g).length">
<template v-for="(state, si) in textByClickStates(g)" :key="`s-${si}`">
<g v-if="state.mode === 'hide-at'" v-click-hide="state.value">
<foreignObject v-if="isWrapped(g)" :x="wrapBounds(g).fx" :y="wrapBounds(g).fy" :width="wrapBounds(g).fw" :height="wrapBounds(g).fh" :transform="textRotation(g, textCenter(g).cx, textCenter(g).cy)">
<div xmlns="http://www.w3.org/1999/xhtml" class="diagram-wrap-text"><template v-for="(line, li) in state.lines" :key="li"><br v-if="li > 0" />{{ line }}</template></div>
</foreignObject>
<text v-else :x="textCenter(g).cx" :y="textCenter(g).cy" :transform="textRotation(g, textCenter(g).cx, textCenter(g).cy)">
<tspan v-for="(line, li) in state.lines" :key="li" :x="textCenter(g).cx" :dy="li === 0 ? firstDy(state.lines.length) : '1.2em'">{{ line }}</tspan>
</text>
</g>
<g v-else-if="state.mode === 'none'">
<foreignObject v-if="isWrapped(g)" :x="wrapBounds(g).fx" :y="wrapBounds(g).fy" :width="wrapBounds(g).fw" :height="wrapBounds(g).fh" :transform="textRotation(g, textCenter(g).cx, textCenter(g).cy)">
<div xmlns="http://www.w3.org/1999/xhtml" class="diagram-wrap-text"><template v-for="(line, li) in state.lines" :key="li"><br v-if="li > 0" />{{ line }}</template></div>
</foreignObject>
<text v-else :x="textCenter(g).cx" :y="textCenter(g).cy" :transform="textRotation(g, textCenter(g).cx, textCenter(g).cy)">
<tspan v-for="(line, li) in state.lines" :key="li" :x="textCenter(g).cx" :dy="li === 0 ? firstDy(state.lines.length) : '1.2em'">{{ line }}</tspan>
</text>
</g>
<g v-else v-click="state.value">
<foreignObject v-if="isWrapped(g)" :x="wrapBounds(g).fx" :y="wrapBounds(g).fy" :width="wrapBounds(g).fw" :height="wrapBounds(g).fh" :transform="textRotation(g, textCenter(g).cx, textCenter(g).cy)">
<div xmlns="http://www.w3.org/1999/xhtml" class="diagram-wrap-text"><template v-for="(line, li) in state.lines" :key="li"><br v-if="li > 0" />{{ line }}</template></div>
</foreignObject>
<text v-else :x="textCenter(g).cx" :y="textCenter(g).cy" :transform="textRotation(g, textCenter(g).cx, textCenter(g).cy)">
<tspan v-for="(line, li) in state.lines" :key="li" :x="textCenter(g).cx" :dy="li === 0 ? firstDy(state.lines.length) : '1.2em'">{{ line }}</tspan>
</text>
</g>
</template>
</template>
<template v-else-if="textLines(g).length">
<foreignObject v-if="isWrapped(g)" :x="wrapBounds(g).fx" :y="wrapBounds(g).fy" :width="wrapBounds(g).fw" :height="wrapBounds(g).fh" :transform="textRotation(g, textCenter(g).cx, textCenter(g).cy)">
<div xmlns="http://www.w3.org/1999/xhtml" class="diagram-wrap-text"><template v-for="(line, i) in wrapText(g)" :key="i"><br v-if="i > 0" />{{ line }}</template></div>
</foreignObject>
<text v-else :x="textCenter(g).cx" :y="textCenter(g).cy" :transform="textRotation(g, textCenter(g).cx, textCenter(g).cy)">
<tspan v-for="(line, i) in textLines(g)" :key="i" :x="textCenter(g).cx" :dy="i === 0 ? firstDy(textLines(g).length) : '1.2em'">{{ line }}</tspan>
</text>
</template>
</g>
</template>
<template v-for="(c, i) in connectors" :key="`c-${i}`">
<g v-if="isHideMode(c)" v-click-hide="hideDirective(c)" :class="['connector', c.style ? `connector-${c.style}` : null]">
<path :d="pathFor(c)" :marker-start="arrowMarkers(c).start" :marker-end="arrowMarkers(c).end" />
<text v-if="labelInfo(c)" class="connector-label" :x="labelInfo(c).x" :y="labelInfo(c).y" :style="{ textAnchor: labelInfo(c).anchor }">{{ labelInfo(c).text }}</text>
</g>
<g v-else v-click="clickDirective(c)" :class="['connector', c.style ? `connector-${c.style}` : null]">
<path :d="pathFor(c)" :marker-start="arrowMarkers(c).start" :marker-end="arrowMarkers(c).end" />
<text v-if="labelInfo(c)" class="connector-label" :x="labelInfo(c).x" :y="labelInfo(c).y" :style="{ textAnchor: labelInfo(c).anchor }">{{ labelInfo(c).text }}</text>
</g>
</template>
<template v-for="b in boxes" :key="`b-${b.id}`">
<g v-if="isHideMode(b)" v-click-hide="hideDirective(b)" :class="['box', b.style ? `box-${b.style}` : null]">
<ellipse v-if="b.shape === 'ellipse'" :cx="b.x + b.w / 2" :cy="b.y + b.h / 2" :rx="b.w / 2" :ry="b.h / 2" :style="b.fill ? { fill: b.fill } : null" />
<polygon v-else-if="isArrowShape(b)" :points="arrowPoints(b)" :style="b.fill ? { fill: b.fill } : null" />
<rect v-else :x="b.x" :y="b.y" :width="b.w" :height="b.h" :rx="rectRx(b, 3)" :style="b.fill ? { fill: b.fill } : null" />
<template v-if="textByClickStates(b).length">
<template v-for="(state, si) in textByClickStates(b)" :key="`s-${si}`">
<g v-if="state.mode === 'hide-at'" v-click-hide="state.value">
<foreignObject v-if="isWrapped(b)" :x="wrapBounds(b).fx" :y="wrapBounds(b).fy" :width="wrapBounds(b).fw" :height="wrapBounds(b).fh" :transform="textRotation(b, textCenter(b).cx, textCenter(b).cy)">
<div xmlns="http://www.w3.org/1999/xhtml" class="diagram-wrap-text"><template v-for="(line, li) in state.lines" :key="li"><br v-if="li > 0" />{{ line }}</template></div>
</foreignObject>
<text v-else :x="textCenter(b).cx" :y="textCenter(b).cy" :transform="textRotation(b, textCenter(b).cx, textCenter(b).cy)">
<tspan v-for="(line, li) in state.lines" :key="li" :x="textCenter(b).cx" :dy="li === 0 ? firstDy(state.lines.length) : '1.2em'">{{ line }}</tspan>
</text>
</g>
<g v-else-if="state.mode === 'none'">
<foreignObject v-if="isWrapped(b)" :x="wrapBounds(b).fx" :y="wrapBounds(b).fy" :width="wrapBounds(b).fw" :height="wrapBounds(b).fh" :transform="textRotation(b, textCenter(b).cx, textCenter(b).cy)">
<div xmlns="http://www.w3.org/1999/xhtml" class="diagram-wrap-text"><template v-for="(line, li) in state.lines" :key="li"><br v-if="li > 0" />{{ line }}</template></div>
</foreignObject>
<text v-else :x="textCenter(b).cx" :y="textCenter(b).cy" :transform="textRotation(b, textCenter(b).cx, textCenter(b).cy)">
<tspan v-for="(line, li) in state.lines" :key="li" :x="textCenter(b).cx" :dy="li === 0 ? firstDy(state.lines.length) : '1.2em'">{{ line }}</tspan>
</text>
</g>
<g v-else v-click="state.value">
<foreignObject v-if="isWrapped(b)" :x="wrapBounds(b).fx" :y="wrapBounds(b).fy" :width="wrapBounds(b).fw" :height="wrapBounds(b).fh" :transform="textRotation(b, textCenter(b).cx, textCenter(b).cy)">
<div xmlns="http://www.w3.org/1999/xhtml" class="diagram-wrap-text"><template v-for="(line, li) in state.lines" :key="li"><br v-if="li > 0" />{{ line }}</template></div>
</foreignObject>
<text v-else :x="textCenter(b).cx" :y="textCenter(b).cy" :transform="textRotation(b, textCenter(b).cx, textCenter(b).cy)">
<tspan v-for="(line, li) in state.lines" :key="li" :x="textCenter(b).cx" :dy="li === 0 ? firstDy(state.lines.length) : '1.2em'">{{ line }}</tspan>
</text>
</g>
</template>
</template>
<template v-else-if="textLines(b).length">
<foreignObject v-if="isWrapped(b)" :x="wrapBounds(b).fx" :y="wrapBounds(b).fy" :width="wrapBounds(b).fw" :height="wrapBounds(b).fh" :transform="textRotation(b, textCenter(b).cx, textCenter(b).cy)">
<div xmlns="http://www.w3.org/1999/xhtml" class="diagram-wrap-text"><template v-for="(line, i) in wrapText(b)" :key="i"><br v-if="i > 0" />{{ line }}</template></div>
</foreignObject>
<text v-else :x="textCenter(b).cx" :y="textCenter(b).cy" :transform="textRotation(b, textCenter(b).cx, textCenter(b).cy)">
<tspan v-for="(line, i) in textLines(b)" :key="i" :x="textCenter(b).cx" :dy="i === 0 ? firstDy(textLines(b).length) : '1.2em'">{{ line }}</tspan>
</text>
</template>
</g>
<g v-else v-click="clickDirective(b)" :class="['box', b.style ? `box-${b.style}` : null]">
<ellipse v-if="b.shape === 'ellipse'" :cx="b.x + b.w / 2" :cy="b.y + b.h / 2" :rx="b.w / 2" :ry="b.h / 2" :style="b.fill ? { fill: b.fill } : null" />
<polygon v-else-if="isArrowShape(b)" :points="arrowPoints(b)" :style="b.fill ? { fill: b.fill } : null" />
<rect v-else :x="b.x" :y="b.y" :width="b.w" :height="b.h" :rx="rectRx(b, 3)" :style="b.fill ? { fill: b.fill } : null" />
<template v-if="textByClickStates(b).length">
<template v-for="(state, si) in textByClickStates(b)" :key="`s-${si}`">
<g v-if="state.mode === 'hide-at'" v-click-hide="state.value">
<foreignObject v-if="isWrapped(b)" :x="wrapBounds(b).fx" :y="wrapBounds(b).fy" :width="wrapBounds(b).fw" :height="wrapBounds(b).fh" :transform="textRotation(b, textCenter(b).cx, textCenter(b).cy)">
<div xmlns="http://www.w3.org/1999/xhtml" class="diagram-wrap-text"><template v-for="(line, li) in state.lines" :key="li"><br v-if="li > 0" />{{ line }}</template></div>
</foreignObject>
<text v-else :x="textCenter(b).cx" :y="textCenter(b).cy" :transform="textRotation(b, textCenter(b).cx, textCenter(b).cy)">
<tspan v-for="(line, li) in state.lines" :key="li" :x="textCenter(b).cx" :dy="li === 0 ? firstDy(state.lines.length) : '1.2em'">{{ line }}</tspan>
</text>
</g>
<g v-else-if="state.mode === 'none'">
<foreignObject v-if="isWrapped(b)" :x="wrapBounds(b).fx" :y="wrapBounds(b).fy" :width="wrapBounds(b).fw" :height="wrapBounds(b).fh" :transform="textRotation(b, textCenter(b).cx, textCenter(b).cy)">
<div xmlns="http://www.w3.org/1999/xhtml" class="diagram-wrap-text"><template v-for="(line, li) in state.lines" :key="li"><br v-if="li > 0" />{{ line }}</template></div>
</foreignObject>
<text v-else :x="textCenter(b).cx" :y="textCenter(b).cy" :transform="textRotation(b, textCenter(b).cx, textCenter(b).cy)">
<tspan v-for="(line, li) in state.lines" :key="li" :x="textCenter(b).cx" :dy="li === 0 ? firstDy(state.lines.length) : '1.2em'">{{ line }}</tspan>
</text>
</g>
<g v-else v-click="state.value">
<foreignObject v-if="isWrapped(b)" :x="wrapBounds(b).fx" :y="wrapBounds(b).fy" :width="wrapBounds(b).fw" :height="wrapBounds(b).fh" :transform="textRotation(b, textCenter(b).cx, textCenter(b).cy)">
<div xmlns="http://www.w3.org/1999/xhtml" class="diagram-wrap-text"><template v-for="(line, li) in state.lines" :key="li"><br v-if="li > 0" />{{ line }}</template></div>
</foreignObject>
<text v-else :x="textCenter(b).cx" :y="textCenter(b).cy" :transform="textRotation(b, textCenter(b).cx, textCenter(b).cy)">
<tspan v-for="(line, li) in state.lines" :key="li" :x="textCenter(b).cx" :dy="li === 0 ? firstDy(state.lines.length) : '1.2em'">{{ line }}</tspan>
</text>
</g>
</template>
</template>
<template v-else-if="textLines(b).length">
<foreignObject v-if="isWrapped(b)" :x="wrapBounds(b).fx" :y="wrapBounds(b).fy" :width="wrapBounds(b).fw" :height="wrapBounds(b).fh" :transform="textRotation(b, textCenter(b).cx, textCenter(b).cy)">
<div xmlns="http://www.w3.org/1999/xhtml" class="diagram-wrap-text"><template v-for="(line, i) in wrapText(b)" :key="i"><br v-if="i > 0" />{{ line }}</template></div>
</foreignObject>
<text v-else :x="textCenter(b).cx" :y="textCenter(b).cy" :transform="textRotation(b, textCenter(b).cx, textCenter(b).cy)">
<tspan v-for="(line, i) in textLines(b)" :key="i" :x="textCenter(b).cx" :dy="i === 0 ? firstDy(textLines(b).length) : '1.2em'">{{ line }}</tspan>
</text>
</template>
</g>
</template>
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
.diagram .box polygon,
.diagram .group rect,
.diagram .group ellipse,
.diagram .group polygon {
  fill: var(--slidev-theme-bg, transparent);
  stroke: currentColor;
  stroke-width: 1.5;
}
.diagram .group rect,
.diagram .group ellipse,
.diagram .group polygon {
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
.diagram .axis line {
  stroke: currentColor;
  stroke-width: 1.5;
  opacity: 0.7;
}
.diagram .axis text {
  font-size: 14px;
  opacity: 0.75;
}
/* Wrapped text via <foreignObject>: center the div inside the bbox, match
   the inherited <text> styling so author can opt into wrap without restyling. */
.diagram-wrap-text {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  text-align: center;
  color: currentColor;
  font-family: inherit;
  font-size: 18px;
  line-height: 1.2;
  word-break: break-word;
  overflow-wrap: break-word;
  box-sizing: border-box;
}
.diagram .group .diagram-wrap-text {
  font-size: 14px;
  letter-spacing: 0.15em;
  opacity: 0.6;
}
</style>
