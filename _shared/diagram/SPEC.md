# `<Diagram>` spec reference

The `<Diagram>` component renders a declarative SVG scene from a single `spec` object: boxes, optional groups (dashed containers), connectors, axes, and background images, all in a shared viewBox. Each shape and connector can be gated by Slidev clicks for build-up animations.

This file is the authoritative API reference. Implementation lives in [`Diagram.vue`](./Diagram.vue).

## Component props

| Prop | Type | Default | Notes |
|---|---|---|---|
| `spec` | `Object` | — | Required. The diagram specification (see below). |
| `fit` | `'aspect' \| 'container'` | `'aspect'` | `'aspect'` locks the wrapper to the spec's `w / h` ratio (parent gives width, height computed). `'container'` makes the wrapper fill its parent — the parent must constrain both axes. |
| `startAt` | `Number` | `0` | Treat the first `N` clicks as already-happened. All `revealAt` / `reveal` / `hideAt` / `textByClick` thresholds are shifted by `-N`. Lets one spec be reused across consecutive slides without duplicating it (slide A drives state 0→5, slide B opens at `:start-at="5"` with the build-up frozen and clicks `6+` still firing). Setting `startAt >= max(revealAt)` freezes at the final state. |

## Spec object

```ts
{
  w: Number,                  // viewBox width  (default 960)
  h: Number,                  // viewBox height (default 540)
  backgrounds: Background[],  // image layers, rendered first
  background:  Background,    // sugar: single background, prepended to backgrounds[]
  axes:        Axis[],
  groups:      Group[],       // dashed containers — visual variant of boxes
  boxes:       Box[],
  connectors:  Connector[],   // rendered last (on top)
}
```

Render order is: backgrounds → groups → connectors → axes → boxes. Z-order within an array follows array order (later = on top).

## Box

A rectangle, ellipse, arrow, or rounded-rect with optional text.

| Field | Type | Notes |
|---|---|---|
| `id` | `String` | Optional. Used by other items' `parent` and by connector snap anchors. |
| `x`, `y` | `Number` | Required. Position in viewBox units. |
| `w`, `h` | `Number` | Required. Size in viewBox units. |
| `anchor` | `'top-left' \| 'top' \| 'top-right' \| 'left' \| 'center' \| 'right' \| 'bottom-left' \| 'bottom' \| 'bottom-right'` | Default `'top-left'`. Which corner/edge `(x, y)` refers to. `'center'` positions the box so its center is at `(x, y)`. |
| `parent` | `String` | If set, `x` / `y` are interpreted relative to the parent box / group's resolved position. |
| `shape` | `'rect' \| 'roundRect' \| 'ellipse' \| 'arrow' \| 'rightArrow' \| 'leftArrow' \| 'upArrow' \| 'downArrow'` | Default `'rect'`. Arrows are PPTX-style chunky shapes. `'roundRect'` auto-computes `rx` from min dimension (capped at 30px) unless `rx` is set. |
| `rx` | `Number` | Corner radius for `'rect'` / `'roundRect'`. |
| `fill` | `String` | CSS color, applied inline. Otherwise styled via class hooks (see below). |
| `style` | `String` | Adds `box-${style}` class for `:deep()` targeting. |
| `text` | `String \| String[] \| Number` | Static text. A string is split on `\n`. |
| `lines` | `String[]` | Explicit per-line array — alternative to `text`. |
| `wrap` | `Boolean` | Render text via `<foreignObject>` with CSS word-wrapping. Text auto-centers. |
| `maxWidth` | `Number` | Max wrapped-text width in px. Implies `wrap`. Defaults to `w - 16` when wrapping. |
| `textRotate` | `Number \| 'vertical-up' \| 'vertical-down'` | Rotation in CSS degrees (positive = clockwise) or named verticals. |
| `revealAt` | `Number` | Appear on click N. |
| `reveal` | `{ from, to? \| until? }` | Range visibility. `to` is **inclusive**, `until` is **exclusive**. |
| `hideAt` | `Number` | Visible initially, hidden from click N. |
| `textByClick` | `Object` | Per-click text swap (see below). |

## Group

Structurally identical to a box (all the same fields). Rendered with a dashed stroke and 60% opacity; default text is smaller (14px vs. 18px). Use for containers that visually enclose nested boxes — set children's `parent` to the group's `id` so they position relative to it.

## Connector

A line between two endpoints, with optional waypoints, arrows, and label.

| Field | Type | Notes |
|---|---|---|
| `from` | `Point` | Required. See "Point syntax" below. |
| `to` | `Point` | Required. |
| `d` | `String` | Optional raw SVG path. If present, overrides all routing (`from` / `to` / `via` / `route`). |
| `route` | `'VH' \| 'vertical-horizontal' \| 'HV' \| 'horizontal-vertical'` | Orthogonal routing between endpoints. Without `route` or `via`, the connector is a straight line. |
| `via` | `Array<{ x?: Axis, y?: Axis }>` | Waypoints. Each entry inherits the previous point's coord for unspecified axes (so `[{ x: 200 }, { y: 100 }]` produces an L-bend through `(200, prev.y)` then `(200, 100)`). |
| `outset` | `Number \| { from?: Number, to?: Number }` | Perpendicular offset from snapped endpoints before routing. Matches PowerPoint's bent-connector behavior. |
| `arrow` | `Boolean \| 'forward' \| 'reverse' \| 'both' \| 'none' \| { start?, end? }` | Default `true` = forward (end) arrow only. |
| `label` | `String` | Text along the path. |
| `labelAt` | `'start' \| 'end' \| Number` | Default `'end'`. Number in `[0, 1]` places the label that fraction of the straight-line distance from `from` to `to`. |
| `labelOffset` | `{ dx?, dy? }` | Pixel adjustment to label position. |
| `style` | `String` | Adds `connector-${style}` class. |
| `revealAt` / `reveal` / `hideAt` | | Same semantics as Box. |

### Point syntax (`from` / `to`)

- `[x, y]` — literal viewBox coordinates.
- `'boxId.side'` — snap to a named anchor on a box/group. Sides: `'top' | 'bottom' | 'left' | 'right' | 'center'` (defaults to `'center'` if just `'boxId'`).
- `{ snap: 'boxId.side', dx?, dy? }` — snap + pixel offset.

Snap points resolve from the bounding box (not the polygon silhouette — arrows snap to their bbox edges).

### Axis syntax (`via[*].x`, `via[*].y`)

Each axis in a `via` entry accepts:

- `Number` — literal coordinate.
- `'boxId.side'` — extract the relevant axis from the snap point (e.g. `via: [{ x: 'data.center' }]` is the x of `data`'s center).
- `{ snap: 'boxId.side', offset?: Number }` — snap + offset.

## Axis (chart axis)

| Field | Type | Notes |
|---|---|---|
| `kind` | `'vertical' \| 'horizontal'` | Required. |
| `x` | `Number` | Required when `kind === 'vertical'`. |
| `y` | `Number` | Required when `kind === 'horizontal'`. |
| `from`, `to` | `Number` | Required. Start/end along the axis direction. |
| `label` | `String` | Optional label text. |
| `labelAt` | `'from' \| 'to' \| Number` | Default `'from'` for vertical, `'to'` for horizontal. Number in `[0, 1]` is a fractional position. |
| `labelOffset` | `{ dx?, dy? }` | Pixel adjustment. |
| `style` | `String` | Adds `axis-${style}` class. |
| `revealAt` / `reveal` / `hideAt` | | Same semantics as Box. |

## Background

| Field | Type | Notes |
|---|---|---|
| `src` | `String` | Required. Image URL or data URI. |
| `x`, `y`, `w`, `h` | `Number` | Required. Position and size in viewBox units. |
| `opacity` | `Number` | Default `1`. |
| `revealAt` / `reveal` / `hideAt` | | Same semantics as Box. |

The sugar form `spec.background = { ... }` prepends a single background to `spec.backgrounds[]`.

## Reveal semantics

The full reveal API on every shape, connector, axis, group, and background:

| Form | Behavior |
|---|---|
| (none) | Always visible. |
| `revealAt: N` | Hidden until click N, visible from click N onward. |
| `reveal: { from: A, to: B }` | Visible on clicks A through **B inclusive**. |
| `reveal: { from: A, until: B }` | Visible on clicks A through **B − 1** (half-open). |
| `hideAt: N` | Visible until click N − 1, hidden from click N onward. |
| `reveal: { until: B }` | Equivalent to `hideAt: B`. |

Translates internally to Slidev's `v-click` / `v-click-hide`:

- `revealAt: N` → `v-click="N"`
- `reveal: { from: A, to: B }` → `v-click="[A, B + 1]"` (Slidev uses half-open ranges; we translate inclusive `to` for you)
- `hideAt: N` → `v-click-hide="N"`

**Don't pass `0`** as `revealAt` / `from` / `to`. Slidev clamps `v-click="0"` to `1` with a console warning. The component already handles the "always visible" case as the absence of any reveal directive, so just omit the field.

**`startAt` interaction:** every threshold is shifted by `-startAt`. Items whose reveals fall entirely in the past get rewritten as "always visible" or dropped. `textByClick` keys shift the same way — the most-recent past entry becomes the new click-0 state (and overwrites the static `text` / `lines` if present).

## `textByClick`

Swap a box's text content at successive click states without repositioning.

```js
{
  text: 'initial',           // optional static text (used through first key - 1)
  textByClick: {
    '0': 'first state',      // overrides `text` from click 0
    '2': 'after click 2',
    '4': ['line one', 'line two'],
  },
}
```

- Keys are stringified non-negative integers.
- Last-key-wins: the largest key `<= current click` decides what renders.
- Values are `String`, `String[]`, or falsy (hides text in that range).
- If you don't include `'0'`, the box's static `text` / `lines` fills the click-0 state through the first key − 1.

## CSS class hooks

Style from a parent component's scoped CSS via `:deep()`. The default theme is monochrome (uses `currentColor`); attach a class to `<Diagram>` and target your own class hooks:

```vue
<Diagram class="my-theme" :spec="spec" />

<style scoped>
.my-theme :deep(.box-main rect) { stroke-width: 2; }
.my-theme :deep(.box-main text) { font-weight: 600; }
.my-theme :deep(.connector path) { stroke-width: 2; opacity: 0.75; }
.my-theme :deep(.connector-arc path) { stroke-dasharray: 4 4; }
.my-theme :deep(.axis-callout text) { font-style: italic; }
</style>
```

Generated classes on each `<g>`:

| Element | Class | Plus, if `style` set |
|---|---|---|
| Box | `box` | `box-${style}` |
| Group | `group` | `group-${style}` |
| Connector | `connector` | `connector-${style}` |
| Axis | `axis` | `axis-${style}` |
| Background | `background` | — |

Plus on individual text nodes:

- Connector label: `<text class="connector-label">`
- Axis label: `<text class="axis-label">`
- Wrapped text (via `<foreignObject>`): inner `<div class="diagram-wrap-text">`

## Minimal example

```js
{
  w: 960, h: 360,
  boxes: [
    { id: 'in',  x:  80, y: 130, w: 180, h: 100, text: 'Input',   style: 'main', rx: 10 },
    { id: 'mid', x: 390, y: 130, w: 180, h: 100, text: 'Process', style: 'main', rx: 10 },
    { id: 'out', x: 700, y: 130, w: 180, h: 100, text: 'Output',  style: 'main', rx: 10, revealAt: 1 },
  ],
  connectors: [
    { from: 'in.right',  to: 'mid.left' },
    { from: 'mid.right', to: 'out.left', revealAt: 1 },
  ],
}
```
