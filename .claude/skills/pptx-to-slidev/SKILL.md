---
name: pptx-to-slidev
description: Convert a PPTX file (typically a Google Slides export) into a Slidev presentation in this repo. Use this whenever the user wants to turn a `.pptx`, a PowerPoint deck, or an exported Google Slides deck into a Slidev / sli.dev talk — including phrases like "port to slidev", "make a slidev version of these slides", "rewrite this deck in slidev", or just dropping a `.pptx` path into the conversation. Scaffolds the talk dir from the repo's `template/`, extracts images, and writes a structured analysis (text, shape geometry, connectors, notes) that you read to design `slides.md` with sensible layouts and click-driven build-ups.
---

# PPTX → Slidev

Convert a PowerPoint / Google-Slides-exported `.pptx` deck into a Slidev presentation that lives alongside other talks in this repo. The goal is to capture the **structure** of the original deck — content, sectioning, build-up intent, diagram geometry — rather than its exact visual fidelity. The result should be a `slides.md` that is easy to theme and easy to edit.

## When to use

Invoke whenever the user has a `.pptx` and wants a Slidev version of it. If they only have a Google Slides URL, run `/google-slides-export` first to produce the `.pptx`, then run this skill.

## How to invoke

Run the prep script. It deterministically scaffolds the talk dir and produces an analysis file — then you (Claude) read the analysis and write `slides.md` with judgment.

```
python3 .claude/skills/pptx-to-slidev/prep.py <PATH_TO_PPTX> [--output <talk-dir-name>] [--repo <repo-root>] [--template <path>]
```

- `<PATH_TO_PPTX>` — required.
- `--output` / `-o` — destination dir name, relative to `--repo` (default: slugified PPTX filename).
- `--repo` — repo root (default: cwd). Must contain a `template/` dir.
- `--template` — override the template path.

The script will:

1. Copy `template/` to `<repo>/<output>/` (slides.md, package.json, `vite.config.ts`, `components/Diagram.vue`, an empty `diagrams/` dir). `node_modules/`, `dist/`, and `package-lock.json` are deliberately excluded — copying `node_modules` is slow *and* corrupts symlinks. **Run `npm install` once in the new dir before `npx slidev build`.** Fails if the dir already exists — ask the user before clobbering.
2. Extract every image from `ppt/media/` into the new dir (co-located with `slides.md`, **not** in `public/`).
3. Copy any `<pptx-stem>.thumbnails/slide-N.png` files (produced by `google-slides-export`) into `<dest>/_thumbnails/` and reference them in the analysis.
4. Parse each slide and write `_analysis.json` + `_analysis.md` into the new dir.

After the script runs, **read `_analysis.md`** end-to-end **and read the per-slide `_thumbnails/slide-N.png` for any slide that's non-trivial** — the PNG shows you what raw coordinates can't. Delete `_analysis.json`, `_analysis.md`, and `_thumbnails/` once you're done with them.

The `vite.config.ts` extends Vite's `server.fs.allow` to include the repo root so the deck can import the shared `_shared/diagram/Diagram.vue`. The `components/Diagram.vue` wrapper auto-registers `<Diagram>` globally for every slide via Slidev's `components/` auto-import.

### Source thumbnails

`google-slides-export` (run *before* this skill when the source is a Slides URL) calls the Slides API's `presentations.pages.getThumbnail` once per slide and saves PNGs to `<pptx-stem>.thumbnails/slide-N.png`. `prep.py` then copies them into the new talk's `_thumbnails/` directory and adds a `**Source:**` line under every slide in `_analysis.md`.

**Always open the thumbnail before writing a non-trivial slide.** The geometry/text dump tells you what's on the slide; the PNG tells you what it *looks like* (color groupings, visual hierarchy, whether two boxes form a pair, whether an arrow is decorative or load-bearing). For pure-text slides you can usually skip the PNG.

If thumbnails aren't present (local PPTX with no Slides URL, or `--no-thumbnails` was passed), you're flying blind — flag that to the user before guessing at complex layouts.

## Writing slides.md from the analysis

### Workflow

1. Read `_analysis.md` end to end. Note the deck size — it's the SVG `viewBox` you'll use for any diagram slides.
2. Scan for **adjacent slides with overlapping content** — these are nearly always build-up animations (progressive bullets, diagram states, highlight passes). Plan to collapse them into a single Slidev slide with click reveals.
3. Decide each slide's Slidev layout (see table below).
4. Replace the template's placeholder `slides.md` with your converted deck.
5. Verify the build: `cd <talk-dir> && npm install && npx slidev build`. If it succeeds, `rm -rf dist/`. If it fails, read the error, fix, rebuild.
6. Delete `_analysis.json` and `_analysis.md`.

### Mapping slide kinds to Slidev layouts

| Source slide | Slidev layout |
| --- | --- |
| Title with subtitle / framing bullets | `cover` (or default with `class: text-center`) |
| Pull-quote with attribution | `quote` |
| Blank slide acting as a divider | `section` |
| Single centered headline / call-to-action | `center` |
| Image + text side-by-side | `media` (theme-josh) — `side: left|right`, optional `caption` |
| 2–6 images in a grid / mosaic | `gallery` (theme-josh) — named slots `::a::`–`::f::`, optional `::overlay::` for a centered card |
| Full-bleed background image with overlaid text | `image-bg` (theme-josh) — props `image`, `align`, `darken`, `position`, `tint`. **For photographs only** — never for data viz / charts (the overlay text lands on top of the chart). |
| Title pinned at top + tall content (table, chart, big diagram) | `panel` (theme-josh) — props `align: 'left' \| 'center'`, `gap`. Use whenever `default`'s vertical-centering would push the H1 off-screen. |
| Naked source thumbnail (hand-drawn figure, freeform diagram) | `image` (theme-josh) — props `image`, optional `caption`, `captionPosition: 'top' \| 'bottom'`. The caption gets a scrim background so it stays readable over any image edge. |
| Truth table / small data grid | `panel` + `<DataTable :headers :rows :highlight-row :highlight-col />` (so the H1 stays anchored above the table) |
| Closing slide ("thanks", "questions") | `end` or `outro` (theme-josh) |
| Ordinary content slide | (no layout — use the default) |

These are starting points, not rules. Pick whatever reads best. The `gallery`, `image-bg`, `media`, and `outro` layouts auto-hide the footer (see `global-top.vue`'s `HIDE_ON` set), so don't pile `footer: false` on top.

### Collapsing build-up slides

Google Slides and PowerPoint don't have native click reveals, so authors duplicate a slide multiple times with one extra element each — a stack of slides 3, 4, 5, 6 with identical text but different highlights, or slides 8, 9, 10, 11 that build a diagram one piece at a time. The analysis output makes these obvious because the text/shape lists overlap heavily across consecutive slides — and the `**Diff from slide N**` block under each slide makes the per-transition delta explicit.

#### The core rule: one source-slide transition = one click

A single transition from slide N to slide N+1 maps to **one** `revealAt` value, even when it introduces multiple new shapes/connectors/text changes. The author chose to reveal those elements together for a reason — a node and the label that names it, a binary op and both its inputs, a structure and the annotation that describes it. Splitting them across separate clicks loses that grouping and produces a fussier build-up than the source.

Concretely:

- If the diff block lists three added shapes, all three share the same `revealAt`.
- If the diff block lists `added shapes (2)` **and** `text changes on existing shapes (1)`, all three of those entries share the same `revealAt`.
- Number clicks by transition index (1, 2, 3, …), not by element count.

Watch especially for these transition shapes that are easy to miss:

- **Multi-element additions** — slide N→N+1 reveals two things simultaneously (a new input box *and* the arrow that connects it; the data line *and* the multiplier sitting on it). The diff block lists them together; keep them together.
- **Text swaps on a stable shape** — the diff shows `text/content changes on existing shapes`. That's a transition (one click), not a no-op.
- **Structural duplication** — the same set of shapes appears a second time at the same coordinates (signalling unrolling or recurrence). The diff shows N shapes added; treat it as one click.
- **Annotation swaps over a static diagram** — slide N and N+1 share the diagram but swap an explanatory text box. Use `reveal: { from: N, to: N }` on each annotation so only the active one shows.

#### Four patterns to watch for in `_analysis.md`

1. **Progressive bullets / shapes** — adjacent slides where each transition adds one or more elements. Each diff block = one click. Collapse with `<v-clicks>` (when the order matches DOM order) or `v-click="N"` (when it doesn't).
2. **Diagram build-ups** — adjacent slides where new shapes appear over a constant base. Inside the `<Diagram>` spec, set `revealAt: N` on every element introduced by transition N — boxes, connectors, and groups all share the same N.
3. **Image-swap reveals** — adjacent slides with **identical text** but **different pictures** (a single heading like "Is this multiple realizability?" with the photo pair swapping each click). The script flags these as `🔄 IMAGE-SWAP-REVEAL`. Collapse with a stack of positioned `<div>`s, one per state, gated by `v-click.hide="N"` / `v-click="[N, N+1]"` / `v-click="N"`. See the converted deck `tmp_talks/05-do-all-minds-work-the-same-way/` for a worked example.
4. **Highlight reveals** — adjacent slides with **identical plain text** but **different per-run formatting** (a sentence is black on one slide and gray on the next; or numbers gain a strikethrough). The script flags these as `⚠ HIGHLIGHT-REVEAL` in the analysis and prints a per-run `[default] / [#XXXXXX] / [b] / [s] / [u]` breakdown under each formatted paragraph (`[s]` = strikethrough, `[u]` = underline; combined like `[bs]`, `[s+#FF0000]`). **Do not collapse these by stripping formatting** — that loses the speaker's emphasis cue. Instead, split the text into segments and bind a class to `$clicks`:

   ```md
   ---
   layout: quote
   clicks: 3
   ---

   <p>
     <span :class="{ on: $clicks === 0 }">First segment…</span>
     <span :class="{ on: $clicks === 1 }">Second segment…</span>
   </p>

   <style scoped>
   span { opacity: 0.3; transition: opacity .3s; }
   span.on { opacity: 1; }
   </style>
   ```

Collapse them into **one** Slidev slide and use clicks:

- For sequential text reveals, wrap children in `<v-clicks>...</v-clicks>`.
- For explicit indexing across heterogeneous elements (mix of divs, SVG groups, etc.), use the `v-click="N"` directive on each element. This works inside SVG `<g>` too, which is essential for staged diagrams.
- For highlight reveals, bind a CSS class to `$clicks` (as shown above) so the active segment is emphasized and the others fade.

The resulting slide preserves the original click count, but the markdown stays compact.

#### Direct `v-click` syntax gotchas (Vue elements, not Diagram specs)

When you write `v-click` straight on a `<p>` / `<span>` / `<div>`, you're hitting Slidev's raw directive — *not* the `<Diagram>` component's `reveal` API. The two have different conventions:

| Want | Direct `v-click` on a Vue element | Diagram spec |
| --- | --- | --- |
| Appear at click N, stay forever | `v-click="N"` | `revealAt: N` (or `reveal: { from: N }`) |
| Visible during clicks A through B *inclusive* | `v-click="[A, B+1]"` (Slidev range is **half-open**) | `reveal: { from: A, to: B }` (component translates internally) |
| Visible at click N only | `v-click="[N, N+1]"` | `reveal: { from: N, to: N }` |
| Visible at start (click 0), hidden from click N onward | `v-click.hide="N"` | (use markdown `v-click.hide` outside the diagram — the spec has no dedicated form for this) |
| Never visible (don't ever do this) | `v-click="[N, N]"` ← **bug**: half-open `start <= current < end` means never active | n/a |

Two specific cases the LSTM-style annotation swap hits:

```md
<!-- Wrong — [0,0] is never visible (half-open), and [1,1]/[2,2] are too -->
<p v-click="[0, 0]"><b>Forget gate.</b> …</p>
<p v-click="[1, 1]"><b>Input gate.</b>  …</p>
<p v-click="[2, 2]"><b>Output gate.</b> …</p>

<!-- Right -->
<p v-click.hide="1"><b>Forget gate.</b> …</p>
<p v-click="[1, 2]"><b>Input gate.</b>  …</p>
<p v-click="[2, 3]"><b>Output gate.</b> …</p>
```

Don't pass `0` to Slidev's `v-click` value (Slidev normalizes 0 to 1 with a warning) — use `.hide` instead when you need an element visible at the initial state.

#### Worked example: multiple elements on one click

Source deck has slide 2 (a network diagram with three boxes) and slide 3 (the same diagram plus a labeled input text *and* an output node). The diff block under slide 3 looks like:

```
**Diff from slide 2** (if this is a build-up, treat the whole block as one click — every entry below shares the same revealAt):
- added shapes (1):
  - `ellipse` at (466.1, 98.0) size 42.6×42.6  text=''
- text/content changes on existing shapes (1):
  - `rect` at (298.4, 388.2): '' → 'Once'
```

Both entries belong to the same click. Correct:

```jsonc
// in diagrams/<name>.json — both share revealAt: 1
{ "id": "out",          "x": 466.1, "y": 98.0, ..., "revealAt": 1 },
{ "id": "input-label",  "x": 298.4, "y": 388.2, ..., "text": "Once", "revealAt": 1 }
```

Wrong (one click per element — invents structure that wasn't in the source):

```jsonc
{ "id": "out",         "revealAt": 1 },
{ "id": "input-label", "revealAt": 2 }   // BAD: the author revealed these together
```

### Recreating diagrams (shapes + connectors)

When the analysis lists multiple shapes and connectors with positions, the slide is a diagram. **Default to the `<Diagram>` component** (auto-imported via `components/Diagram.vue`, backed by `_shared/diagram/Diagram.vue`). Write the geometry as a JSON spec file in the deck's `diagrams/` directory and reference it.

#### Workflow per diagram slide

1. Create `diagrams/<descriptive-name>.json` in the deck dir.
2. In the slide section of `slides.md`, add a `<script setup>` block importing just that spec (Slidev scopes `<script setup>` per slide — every diagram slide needs its own import).
3. Render with `<Diagram :spec="..." />`, optionally passing `class="..."` so the slide's scoped CSS can theme it via `:deep()`.

```md
<script setup>
import spec from './diagrams/my-diagram.json'
</script>

# Slide title

<Diagram class="my-theme" :spec="spec" />

<style scoped>
.my-theme :deep(.box-emphasis rect) { fill: rgba(255, 153, 0, 0.18); }
</style>
```

#### Spec schema

```jsonc
{
  "w": 960, "h": 540,             // deck size from the analysis header (SVG viewBox)
  "groups": [                     // optional, rendered behind boxes (encoder/decoder containers, etc.)
    { "id": "g1", "x": 100, "y": 380, "w": 200, "h": 80, "text": "ENCODER", "style": "..." }
  ],
  "boxes": [
    {
      "id": "input1",             // referenced by connectors as "input1.top|right|bottom|left|center"
      "x": 200, "y": 270, "w": 100, "h": 44,  // pixel coords in the viewBox space — copy straight from the analysis
      "shape": "ellipse",         // optional — "ellipse" or one of the arrow shapes; default is a rectangle. See "Shapes" below
      "anchor": "top-left",       // optional, where (x, y) sits on the box — see below (default: top-left)
      "parent": "frame",          // optional, treat (x, y) as offsets from another box's top-left — see below
      "text": "Input",            // single line — or use `lines` / `"a\nb"` for multi-line, see "Text" below
      "lines": ["Input", "(US)"], // optional — array form for multi-line; takes precedence over `text`
      "wrap": true,               // optional — auto-wrap text to the box width via <foreignObject>. See "Text" below
      "maxWidth": 180,            // optional — px cap on wrap width (implies wrap)
      "textRotate": "vertical-up", // optional — degrees number or "vertical-up"/"vertical-down". See "Rotated text"
      "style": "rnn",             // optional, becomes CSS class `box-rnn` on the <g> element
      "fill": "#999999",          // optional explicit fill (overrides theme CSS) — see Fills below
      "rx": 3,                    // optional corner radius (default 3 for boxes, 4 for groups)
      "revealAt": 2,              // optional, appear at click N and stay (shorthand for `reveal: { from: N }`)
      "reveal": { "from": 1, "to": 2 },   // optional, visible from click 1 through click 2 — see Reveals below
      "hideAt": 1,                // optional, visible at start, hidden from click N onward — see Reveals below
      "textByClick": { "3": "f(X)", "4": ["1 if X ≥ T", "0 if X < T"] }   // optional — swap text content per click, see Per-click text swaps below
    }
  ],
  "connectors": [
    { "from": "input1.top", "to": "emb1.bottom" },                              // straight, both ends snapped, default arrow at end
    { "from": "rnn1.top", "to": "attn.left", "route": "VH" },                   // V then H — sharp elbow at (rnn1.x, attn.y)
    { "from": "rnn1.top", "to": "attn.left", "via": [{ "y": "attn.center" }] }, // same elbow via an explicit waypoint
    { "from": "a.right", "to": "b.top", "outset": 20 },                         // perpendicular leave + perpendicular arrive (PPTX bent4-style)
    { "from": "node.right", "to": "node.top", "outset": 30 },                   // self-loop on adjacent sides — auto-wraps around the corner
    { "from": [330, 168.1], "to": "rnn1.bottom" },                              // free endpoint as a literal tuple
    { "from": { "snap": "rnn1.top", "dy": 50 }, "to": "data.top" },             // free endpoint as a snap+offset
    { "from": "a.right", "to": "b.left", "style": "highlight", "arrow": false },
    { "from": "out.top", "to": "in.bottom", "arrow": "reverse" },               // arrow at the start instead — see Arrows below
    { "from": "a.right", "to": "b.left", "arrow": "both" },                     // arrows at both ends
    { "from": "act.right", "to": "out.left", "label": "signal" },               // text along the path — see Connector labels below
    { "d": "M 776 168 Q 700 100 600 180", "style": "curve" }                    // raw SVG path — fallback for curves
  ]
}
```

**Box positions:** raw pixel coords in the `viewBox` coordinate system — the analysis already gives them in this form, so copy directly.

**Shapes:** boxes default to a rectangle (`<rect>`). Set `shape:` to switch the geometry:

| value | renders | notes |
| --- | --- | --- |
| omitted | rectangle | default — uses `rx` for corner radius (default 3) |
| `"ellipse"` | ellipse / circle | radius is half the bbox in each axis |
| `"arrow"` / `"rightArrow"` | chunky horizontal arrow → | stem 65% of width × 50% of height; head fills the remaining width and full height |
| `"leftArrow"` | chunky horizontal arrow ← | mirror of rightArrow |
| `"upArrow"` | chunky vertical arrow ↑ | stem at bottom, head at top |
| `"downArrow"` | chunky vertical arrow ↓ | stem at top, head at bottom |

PPTX exports the four arrow variants as native shapes (`<a:prstGeom prst="downArrow">` etc.); the analysis surfaces them on the shape line so you can copy `shape: "downArrow"` directly. Snap references (`box.top` / `bottom` / `left` / `right` / `center`) resolve to the bbox edges, not the arrow's silhouette — connectors anchored to an arrow box land at the bbox edge, just like any rect.

Text inside an arrow centers within the stem portion (not the head triangle), so labels read cleanly along the shaft.

**Anchor:** by default `(x, y)` is the box's **top-left corner** (matching the analysis output). Set `anchor` to reposition where `(x, y)` lands on the box — handy when you want to center a box on a known point or align it to a corner. Supported values: `top-left` (default), `top`, `top-right`, `left`, `center`, `right`, `bottom-left`, `bottom`, `bottom-right`. The 9-position grid corresponds to the same edge/corner names used by snap references on the other side. Example:

```jsonc
// place a callout label centered on (500, 100)
{ "id": "note", "x": 500, "y": 100, "w": 200, "h": 40, "anchor": "center", "text": "see above" }
```

**Parent:** set `parent: "<otherBoxId>"` to make `(x, y)` an offset from the parent's top-left instead of an absolute viewBox position. Useful when a diagram has a repeated module (e.g. an LSTM gate) whose internals are easier to express relative to the module's frame — once the frame is placed, every child reuses the same locals. Parents resolve recursively; the parent itself can have a parent. Anchor offsets are applied in the box's local frame before the parent translation.

```jsonc
// two modules with identical internal structure — only the parent changes
{ "id": "m1", "x": 95.7, "y": 125.0, "w": 148, "h": 306, "style": "module" },
{ "id": "m1-w", "parent": "m1", "x": 17.4, "y": 220.4, "w": 50, "h": 30, "text": "W0" },
{ "id": "m2", "x": 270.9, "y": 125.6, "w": 148, "h": 306, "style": "module" },
{ "id": "m2-w", "parent": "m2", "x": 17.4, "y": 220.4, "w": 50, "h": 30, "text": "W2" }  // same locals
```

Snap references (`"m1-w.top"`) always resolve to slide-absolute coords, so connectors don't need to know whether a target is parented.

#### Point and axis resolution

Connector endpoints (`from`, `to`) accept three forms:

```jsonc
"attention.left"                                  // snap reference — center of named edge
[330, 168.1]                                      // literal [x, y] tuple
{ "snap": "enc1-rnn.top", "dy": 50, "dx": 0 }     // offset relative to a snap point
```

`via` items pin one or both axes. `x` and `y` accept three forms:

```jsonc
{ "y": 102.8 }                                    // literal value
{ "y": "attention.center" }                       // snap reference — pulls the y of attention.center
{ "y": { "snap": "attention.top", "offset": -20 } }  // offset relative to a snap's axis value
```

When a via specifies only `x` (or only `y`), the other axis is inherited from the previous waypoint. This is what makes V-then-H routing work without spelling out both coordinates:

```jsonc
// "from enc1-rnn.top, up to attention's vertical center, then across to attention.left"
{ "from": "enc1-rnn.top", "to": "attention.left", "via": [{ "y": "attention.center" }] }
```

Snap references are `"<boxId>.<side>"` where side is `top | right | bottom | left | center`. The `id` matches a box or group `id` from the spec.

#### Orthogonal-routing shorthand

For the common case of a single 90° elbow, `route` skips the explicit waypoint:

```jsonc
{ "from": "w0.top", "to": "plus.bottom", "route": "VH" }   // up first, then over
{ "from": "a.right", "to": "b.top", "route": "HV" }        // across first, then down
```

Accepted aliases (case-insensitive): `VH` / `vh` / `vertical-horizontal`, `HV` / `hv` / `horizontal-vertical`. `VH` means "leave the start vertically, then turn 90° horizontally to reach the end"; `HV` is the opposite. If both `route` and `via` are set, the route elbow is inserted first, then the via waypoints. Prefer `route` for single-bend connectors and `via` for anything more elaborate.

#### `outset`: perpendicular leave / arrive (and self-loops)

`outset: N` pushes each snapped endpoint **perpendicular to its face** by `N` px before routing kicks in. This matches PowerPoint's bent-connector behavior (every bent4/bent5 in a PPTX leaves and arrives perpendicular to the connected face) and is what makes self-loops on the same shape route cleanly around it.

```jsonc
// PPTX bentConnector4 ("leave perpendicular, wrap around, arrive perpendicular")
{ "from": "a.right", "to": "b.top", "outset": 20 }                              // L-bend between the two stubs
{ "from": "a.right", "to": "b.left", "outset": 20, "via": [{ "x": 500 }] }      // Z-bend, midpoint at x=500

// Asymmetric outsets
{ "from": "a.right", "to": "b.top", "outset": { "from": 30, "to": 10 } }

// Self-loop on adjacent sides — outset alone, auto-corner around the shape
{ "from": "node.right", "to": "node.top", "outset": 30 }

// Self-loop on the same side — use snap+dx/dy to spread the endpoints, then outset closes the loop
{ "from": { "snap": "node.top", "dx": -10 }, "to": { "snap": "node.top", "dx": 10 }, "outset": 30 }
```

How it works internally:

1. Each snapped endpoint gets a "stub" point pushed perpendicular by its outset value (the side encoded in the snap reference — `top`/`right`/`bottom`/`left` — determines the direction).
2. `route` / `via` operate **between the stubs**, so any explicit mid-routing sits between the perpendicular approach segments and doesn't disturb them.
3. **Self-loop auto-corner.** When `from` and `to` snap to the **same shape id** on **perpendicular sides** (e.g. `right` → `top`) and you give no `route`/`via`, the component inserts a single L-corner between the two stubs. The corner lands outside the shape, so the path naturally wraps around it.
4. Same-side self-loops (e.g. `top` → `top`) need offset endpoints (`{ snap, dx, dy }`) so the start and end aren't the same point. Once the endpoints are spread, the symmetric outset values produce a clean three-segment loop with no extra `via` needed.

When prep.py flags a connector as `**[SELF-LOOP]**` or `**[MULTI-BEND]**` in the analysis, it also suggests the `outset` spec form on the next line — prefer that form over pasting the raw `d="…"` it generated, because snap refs stay coherent when box positions move.

#### When to use raw `d` (escape hatch)

The `d` field is the SVG path `d` attribute — the same `M`/`L`/`H`/`V`/`Q`/`C` mini-language the analysis emits for every connector. Prefer `from`/`to`/`via` for everything orthogonal; reach for `d` only when:
- the source has a freeform curve (Bézier) the waypoint model can't express,
- you want to preserve the analysis's suggested `d` verbatim and don't care about anchoring it semantically.

The analysis prints a ready-to-paste `d="…"` for every source connector. Snap when you can (more readable, edits stay coherent if box positions shift), use `d` when you must.

#### Text (single line, multi-line, line-wrapping)

`text` defaults to a single line. For multi-line text in a box or group:

```jsonc
{ "text": "Line 1\nLine 2" }                   // newlines inside a single string
{ "text": ["Line 1", "Line 2"] }               // array form
{ "lines": ["Line 1", "Line 2"], "text": "" }  // explicit `lines` (takes precedence)
```

All three render as multiple `<tspan>`s vertically centered around the box's center, with 1.2em line height. Pick line breaks deliberately. Don't paste the analysis's ` | `-joined string as-is into `text:` (that renders the `|` literally) — split into `lines`. The analysis prints multi-paragraph shape text either as a fenced block (multi-paragraph case) or ` | `-joined (legacy / diff-blocks); either way, one paragraph → one `lines[]` entry.

**Auto-wrap.** For one-off long labels that should wrap to the box, set `wrap: true` (or `maxWidth: <px>`) instead of pre-splitting:

```jsonc
{ "id": "note", "x": 600, "y": 230, "w": 280, "h": 90,
  "text": "What do these different circuits have in common?", "wrap": true }
```

Wrapped text renders via `<foreignObject>` + a centered `<div>` so the browser handles word-break and line-height. `maxWidth` (px) clamps the inner width below the box width — useful when you want narrower text inside a wider box. Without `wrap`/`maxWidth`, the component falls through to the existing `<text>`/`<tspan>` path — existing decks render byte-identically.

#### Rotated text (`textRotate`)

For labels that should run vertically (PPTX `<a:bodyPr vert="vert270">`, or any custom rotation), set `textRotate` on the box:

```jsonc
{ "text": "REDUCTIONISM", "textRotate": "vertical-up" }    // -90° / CCW (reads bottom-up)
{ "text": "EMERGENCE",    "textRotate": "vertical-down" }  // 90° / CW  (reads top-down)
{ "text": "10°",          "textRotate": 10 }               // arbitrary degrees, CSS convention (positive = CW)
```

The whole `<text>` (multi-line `<tspan>`s included) and any `<foreignObject>` wrap rotate together as a block, centered on the box's geometric center. The analysis emits `vert=270` / `vert=90` on shapes whose text is rotated — feed that straight into `textRotate`.

#### Fit modes (`fit` prop)

By default the `<Diagram>` wrapper locks itself to the spec's `w / h` aspect ratio. Width comes from the parent; height is computed. That works when the diagram is the only content on the slide, but on a slide with a title / paragraph / footer above and below, a 16:9 spec is taller than the available area and the bottom rows get clipped.

Pass `fit="container"` to switch the wrapper to `width: 100% / height: 100%` and let the SVG's `preserveAspectRatio="xMidYMid meet"` scale the drawing inside the available bounds. The parent must constrain height — put the `<Diagram>` inside a flex-1 wrapper:

```md
<div class="diagram-wrap">
  <Diagram class="my-diagram" fit="container" :spec="spec" />
</div>

<style scoped>
.diagram-wrap { flex: 1 1 0; min-height: 0; display: flex; justify-content: center; }
</style>
```

Default (`fit="aspect"`) is fine when the diagram *is* the slide — no title above. Use `fit="container"` whenever you wrap the diagram with a heading or trailing caption.

#### Fills

By default a box's fill comes from the theme CSS — usually `var(--slidev-theme-bg, transparent)` so the box reads through the slide background. Set `fill: "#RRGGBB"` on a box to override that with an explicit color. The prep script extracts every `<a:solidFill><a:srgbClr>` from the source PPTX and surfaces it as `fill=#RRGGBB` on the per-shape line in the analysis — copy those values straight into the spec.

```jsonc
{ "id": "h1", "x": 339, "y": 249, "w": 43, "h": 43, "shape": "ellipse", "fill": "#999999" }
```

When to use `fill` vs CSS theming:

- **Explicit `fill`** — when the source uses color to encode information that varies per-shape (grayscale activity in neurons, traffic-light status, per-cell highlights). The color belongs to *this shape on this slide*, not to a class of shapes. The fill survives slide-to-slide build-ups: a `text/fill changes on existing shapes` entry in a diff block usually means the author is animating a recolor across clicks (e.g. activations propagating through a network).
- **CSS class `style:` + `:deep()` rule** — when an entire category of shapes shares a theme color (every `box-rnn` is faint orange). Set `style: "rnn"` on the boxes and theme it once in `<style scoped>`.

Use both together when most shapes follow a category color but a few need to break out: set both `style: "neuron"` (for the stroke/baseline look) and `fill: "#434343"` (for this specific neuron's activity level). The inline `fill` style wins because it's bound as an element style attribute, not a CSS rule.

Schemes / theme color references (`<a:schemeClr>` in PPTX) are deliberately skipped by the extractor — those default to white/dark and would clobber the theme.

#### Arrows

Each connector has an `arrow` field. Accepted values:

| value | renders | notes |
| --- | --- | --- |
| omitted / `true` / `"forward"` | arrowhead at the `to` end | default |
| `false` / `"none"` | no arrowheads | for label ties, brackets, decorative lines |
| `"reverse"` | arrowhead at the `from` end | flip without rewriting `from`/`to` |
| `"both"` | arrowheads at both ends | bidirectional / double-headed |
| `{ start: bool, end: bool }` | explicit booleans | rarely needed |

The prep script reads PowerPoint's `<a:headEnd>` / `<a:tailEnd>` and computes `arrow=forward|reverse|both|none` for every source connector — copy that value straight into the spec when it isn't `forward`.

#### Reveals

Four forms, all work on boxes, groups, and connectors:

- `revealAt: N` — appear at click `N` and stay forever. Shorthand for `reveal: { from: N }`.
- `reveal: { from: A, to: B }` — visible from click `A` through click `B`, **inclusive on both ends**, then hidden. Useful when an explanatory label needs to swap each step of a build-up. The component handles the translation to Slidev's half-open internal range — you write inclusive coordinates and they work as written.
- `hideAt: N` — **visible at start, hidden from click `N` onward**. The complement of `revealAt`. Routed through Slidev's `v-click-hide` directive internally, which sidesteps the `0 → 1` normalization trap, so `hideAt: 1` does what you'd expect (visible at click 0, hidden from click 1).
- `reveal: { from: A, until: B }` — visible from `A` through `B-1` (half-open, parallel to Slidev's `v-click="[A, B]"`). Use `from`+`until` when the upper bound is "hide at click N onward"; use `from`+`to` when it's "still visible at click N."

```jsonc
{ "id": "explain-forget", "text": "The forget gate…", "reveal": { "from": 1, "to": 1 } },  // visible at click 1 only
{ "id": "explain-input",  "text": "The input gate…",  "reveal": { "from": 2, "to": 2 } }   // visible at click 2 only
```

Slidev derives the slide's total click count from the highest value seen in any `v-click` directive on the slide. Use the bare `revealAt: N` form (or `reveal: { from: N }`) for "appear and stay" — **never** put an artificially large sentinel like `99` in the upper bound, because Slidev will then require 99 clicks before advancing.

Don't pass `0` as `from`/`to`/`revealAt` — Slidev normalizes 0 to 1 with a console warning, so the result won't be what you wrote. If you need an element visible at the initial state and hidden after click 1, put it outside the Diagram spec and use `v-click.hide="1"` directly on the Vue element (see the direct `v-click` gotchas section above).

If a build-up needs the same element to *move* between clicks (e.g. an Output box at one y-coord for clicks 0–1, then a different y-coord from click 2 onward), declare two boxes with overlapping coords and complementary `reveal` ranges. There's no built-in tween.

#### Per-click text swaps (`textByClick`)

When the *same* box gains or swaps text as clicks advance, use `textByClick` instead of declaring ghost-overlay boxes at the same coords. The mapping is `{ "<click>": <string | string[]> }` and is **last-key-wins**: the largest key `≤ current click` decides what to render. Strings are single-line; arrays render as multi-line `lines`.

```jsonc
{
  "id": "act", "x": 620, "y": 355, "w": 140, "h": 60, "style": "act",
  "textByClick": {
    "3": "f(X)",
    "4": ["1 if X ≥ T", "0 if X < T"]
  }
}
```

- Click 0–2: no text (the box is empty).
- Click 3: `"f(X)"`.
- Click 4 onward: the two-line threshold rule.

If you also set the static `text`/`lines` and omit a `"0"` key, the static content fills click 0 until the smallest `textByClick` key fires. An explicit `"0"` key replaces the static content as the initial state.

Geometry never changes — only the rendered text. Total click count is derived automatically (every state's `v-click`/`v-click-hide` bound participates in Slidev's `maxMap`), so adding `textByClick: { "4": ... }` correctly extends the slide's click total.

Prefer `textByClick` over the ghost-overlay-box pattern whenever the only thing changing is the text content of a stable shape — it's one box instead of three, and the JSON stays readable.

#### Connector labels (`label`, `labelAt`, `labelOffset`)

Render a text label along a connector path. The label inherits the connector's reveal/hide directive (so hiding the connector hides the label), and it sits at the post-`outset` tip — not the snap point.

```jsonc
{ "from": "act.right", "to": "out.left", "label": "signal" }                 // text right of the end tip (default)
{ "from": "a.right", "to": "b.left", "label": "X = 5", "labelAt": 0.5 }      // midpoint, centered above the line
{ "from": "in.bottom", "to": "out.top", "label": "h", "labelAt": "start" }   // at the start tip, left-aligned
```

- `labelAt: 'end'` (default) — label anchored at the `to` tip, left-aligned (text reads right of the tip). Default offset `{ dx: 8, dy: 0 }`.
- `labelAt: 'start'` — anchored at the `from` tip, right-aligned. Default offset `{ dx: -8, dy: 0 }`.
- `labelAt: <number>` — fraction `t ∈ [0, 1]` along the straight line between the two terminal coords. Centered above the line. Default offset `{ dx: 0, dy: -10 }`. Best for straight/orthogonal connectors; the numeric form doesn't follow curved paths.
- `labelOffset: { dx?, dy? }` — fine-tune offset from the computed anchor point.

`labelInfo` returns `null` (no label rendered) when the connector uses a raw `d:` path — labels need resolvable `from`/`to` endpoints. Fall back to a no-border text box at that location if you need a label on a curve.

Style the label via the connector's `style`: a connector `{ style: "callout", label: "…" }` renders `<text class="connector-callout">`, themable in scoped CSS as `.diagram-name :deep(.connector-callout text) { ... }`.

#### Theming

The component bakes in: `currentColor` strokes, transparent fill defaulting to `var(--slidev-theme-bg)`, group rects dashed at 0.6 opacity, text using inherited font. Per-deck theming goes in the slide's `<style scoped>` block:

```css
.my-theme :deep(.box-rnn rect)    { fill: rgba(255, 153, 0, 0.12); }
.my-theme :deep(.box-label rect)  { stroke: none; fill: transparent; }
.my-theme :deep(.box-label text)  { font-style: italic; }
.my-theme :deep(.connector-skip path) { stroke: #d33; stroke-width: 2.5; }
```

`:deep()` is required because the slide's scoped CSS can't reach inside the Diagram component otherwise. The class on each generated element is `box-<style>`, `group-<style>`, or `connector-<style>` — pick semantic `style` values in the spec (`rnn`, `attention`, `label`, `callout`, `arc`, `highlight`, …) so the CSS reads.

#### When to give up on `<Diagram>` (and just use the source PNG)

The component is great for **graph-shaped** diagrams: 5–15 labeled boxes connected by snap-routed arrows, where the spatial arrangement matters but the visual style doesn't. It's *not* the right tool for everything in the deck. Bail and use the source PNG as an `<img>` when:

- The slide is flagged with the `🪄 Freeform/dense figure` annotation — prep.py already decided this isn't graph-shaped, take the hint.
- The diagram has **more than ~15 shapes** and you're scaffolding from scratch — the JSON authoring cost dominates.
- The source uses **decorative imagery as load-bearing content** (the reduction ladder has hand-drawn animal silhouettes next to each "scale" label; the cognitive-mapping deck has a brain with arrows pointing into specific regions). Recreating those in SVG loses the point.
- The source is **rasterized SmartArt / Visio / clipart** that came across as one `image*.png`. Don't try to reverse-engineer it; just place the image.
- The diagram has **mixed-formatting or rich text inside boxes** (bold + color within one label, equations, code) that won't survive the `<text>` element.
- The shapes are **non-rectangular** (organic curves, polygons, freeform) and `shape: "ellipse"` isn't enough.

**Preferred fallback: use the source thumbnail.** Every slide has a PNG in `_thumbnails/slide-N.png` (when `google-slides-export` produced them). For a "just show the diagram" slide:

```md
---
layout: image
image: ./_thumbnails/slide-11.png
caption: "Tic-tac-toe as a symbol system: board state plus a set of legal actions."
---
```

(`caption` and `captionPosition: 'top' | 'bottom'` are optional; the caption gets a scrim background so it stays readable over any image edge.)

Caveat: thumbnails are 1600×900 PNGs that bake in the source theme — fine for content slides but won't match your Slidev theme. So use the thumbnail when fidelity matters more than theming. For diagrams you *want* themed, do the `<Diagram>` work.

**Secondary fallback: inline SVG / HTML.** Drop into raw markup when you need partial-Diagram + something exotic (tweened motion, gradients, multi-line foreignObject text). Most cases get covered by Diagram + thumbnails + image layouts; inline SVG is rare.

#### Known `<Diagram>` limitations

Things the component does not (yet) do — work around with the strategies above:

- **No obstacle avoidance.** A connector from A.right to C.left will draw straight through anything in between (e.g. a box B sitting on that line). Either route around with `via`/`route`, or move B, or accept the crossing.
- **No animations between two states of the same element.** Text content can swap across clicks via `textByClick`, but if a box needs to *move* or *resize*, declare two boxes with complementary `reveal` / `hideAt` ranges (no built-in tween).
- **Labels on raw `d:` paths.** Connector `label` requires resolvable `from`/`to` endpoints. For curved connectors written as raw SVG `d:` paths, add a no-border text box at the label location instead.

### Analysis annotations reference

Beyond the geometry/text dump and diff blocks, `_analysis.md` emits a few semantic hints. Recognize them on a quick scan:

- `**Tables:**` (per slide) — PPTX tables (`<a:tbl>`) extracted with cell contents. Convert with the theme's `<DataTable :headers="..." :rows="...">` component (or a raw markdown table). The script prints rows as JSON arrays so they're paste-ready. Header detection prefers PPTX's `<a:tblPr firstRow="1">`, then `<a:tr h="1">`, then "all-bold first row"; when nothing matches it emits `Headers: null` and puts every row in `Rows`.
- ` vert=270` / `vert=90` / `vert=stacked` on a shape line — the shape's text is rotated. Map directly to `textRotate: "vertical-up"` (270) / `"vertical-down"` (90) on a `<Diagram>` box, or wrap with `transform: rotate(...)` in raw HTML. Picked up from `<a:bodyPr vert="...">` *or* `<a:xfrm rot="...">` (PPTX uses both).
- ` 🎨 full-slide overlay (likely a darken scrim over a background picture)` — a slide-sized opaque rect at (0,0), low luminance. **Don't render this as a content shape.** It's a darkening scrim over a background photo; treat the picture beneath as a background and put the overlay in CSS (a `linear-gradient` over the image, or `theme-josh`'s `image-bg` layout with `darken: 0.6`).
- ` ✂ crop l=…% t=…% r=…% b=…%` on a picture — the source image is wider/taller than the bbox; only the visible portion shows. See "Cropped pictures" below for the wrapper recipe.
- ` ⚠ video placeholder` on a picture — the source had an embedded video; Google's PPTX export replaced it with a thumbnail. The `<deck>.videos.json` sidecar has the original URL/embed metadata. See "Videos" below.
- `🔄 IMAGE-SWAP-REVEAL` (slide annotation) — same heading as previous slide but pictures changed. Collapse into one Slidev slide with click-gated image stacks.
- `⚠ HIGHLIGHT-REVEAL` (slide annotation) — same text as previous slide but per-run formatting (strike, color, bold) changed. Collapse with `$clicks`-bound CSS classes.
- `💡 Mermaid candidate (LR|TB)` (slide annotation) — see "When to use Mermaid instead" below.
- `🪄 Freeform/dense figure (N shapes, M with no text)` (slide annotation, near the top) — the slide is a hand-drawn drawing, freeform diagram, or decorative mesh (X/O on a board, network spaghetti). Trying to recreate this in `<Diagram>` is wasted effort — use `layout: image` with the source thumbnail. The accompanying suggestion in the annotation gives you the exact `<img>` path. Triggers when there are ≥ 12 positioned shapes, ≥ 55% have no text, AND there are ≥ 12 empty shapes in absolute terms (gates out perceptron-style schematics that hit the ratio early in their build).
- `⛔ scene change` (diff-block header swap) — replaces the usual "treat the whole block as one click" hint. Fires when ≥ 70% of the prior slide's shapes are removed and at least one is added — i.e., slide N+1 is a fresh slide, not a build-up of slide N. **Do not** wrap the affected slides as `v-click` reveals; just author them as separate Slidev slides. Triggers when prior slide had ≥ 5 shapes.
- `decorative slivers (cropped views of the same image, likely a parallax/stripe overlay; not load-bearing)` — surfaced both in the per-slide `**Pictures:**` block and inside `added pictures` / `removed pictures` diff entries. Means the source author tiled many thin cropped strips of a single image as background decor. Skip them entirely — render the un-cropped image as the slide background (e.g. via `layout: image-bg`) and ignore the slivers. The diff block's count in the `(N)` header stays accurate (semantic content unchanged); only the per-entry rendering collapses.

**Multi-paragraph shape text.** When a shape has more than one paragraph, the per-slide listing emits a fenced block under the geometry line (not the inline `text='...'` form). Diff blocks still join with ` | ` because they need to be compact. Either way: one paragraph = one `<p>` (or one `lines[]` entry) when you author the slide.

**Run-format tags.** Inside the per-paragraph breakdown, runs are tagged like `` [default] `` / `` [b+#FF0000] `` / `` [is] `` / `` [u] `` where letters mean: `b` bold, `i` italic, `s` strikethrough, `u` underline. They collapse into one token (`[bs]` = bold + strike) and a `+#RRGGBB` color suffix follows when present. Strike and underline pass through to your slide via GFM (`~~text~~` for strike) or inline CSS — no special component needed.

### When to use Mermaid instead

If a slide is flagged `💡 Mermaid candidate (LR|TB)` in the analysis, every shape is a basic node and every connector snaps cleanly between two shapes — the diagram is graph-shaped, not spatially meaningful. Prefer a Slidev ```` ```mermaid ```` block in those cases: less code, automatic layout, and `v-click` still works via CSS class toggles.

Skip the Mermaid suggestion (and use `<Diagram>`) when the spatial arrangement itself carries meaning: a "World ↔ Mind" pair with curved arrows above and below, three connectors that share a horizontal segment to signal "all encoder states feed attention", a skip-connection arrow that visibly bypasses an intermediate node. Mermaid would flatten these into auto-routed flows and lose the metaphor.

See `.agents/skills/slidev/references/diagram-mermaid.md` (installed via `npx skills add slidevjs/slidev`) for Mermaid-in-Slidev specifics.

### Gotcha: blank lines + indentation inside raw HTML/SVG blocks

If you find yourself hand-writing a raw `<svg>` block in slides.md (rather than using `<Diagram :spec="…" />`), watch out for this: Slidev's markdown parser treats a blank line inside an HTML block as a paragraph break and re-enters markdown mode for what follows. If the next line is indented **4+ spaces** (the natural indent for nested SVG children), markdown wraps it in `<pre><code>`, and Vue then fails the build with "Element is missing end tag" or "`<pre>` cannot be child of `<svg>`".

Two fixes (either works): strip the indentation so no child line starts with 4+ spaces, or keep the indent but remove every blank line inside the block — the blank line is what re-arms the markdown code-block rule.

Default to `<Diagram :spec="…" />` and you'll never hit this.

### Gotcha: YAML reserved characters in frontmatter values

Slide frontmatter is YAML, so layout props that look like single punctuation marks need quoting or they get reinterpreted. The one that bites in this repo is the `outro` layout's `mark` prop: `mark: ?` parses as a complex-mapping-key indicator and arrives at the component as `undefined` (the layout silently falls back to its default `?`). Write `mark: '?'` instead.

Same applies to any value that starts with one of YAML's flow indicators: `?`, `:`, `,`, `[`, `]`, `{`, `}`, `&`, `*`, `!`, `|`, `>`, `%`, `@`, `` ` ``, or a leading `-`. When in doubt, quote.

### Images

Images live alongside `slides.md` after the prep script runs. Reference them with a **relative** path: `<img src="./image1.png" />` or `![](./image1.png)`.

Slidev's build will fail with `Import "/foo.png" from slide Markdown resolves outside of Vite server.fs.allow` if you use an absolute `/foo.png` path. **Do not** move images into `public/` — that's the path that triggers the error.

#### Cropped pictures

PPTX stores image crops as four edge insets (`<a:srcRect l="..." t="..." r="..." b="...">`, in 1/1000ths of a percent) — the source image is the full `image*.png` extracted from the deck, but only a subset is visible inside the picture's bbox. **The prep script extracts the full image; the crop is applied only at render time.** If you drop the raw `<img src="./image*.png" />` onto the slide, you'll show the whole thing instead of the framed portion the author chose.

When a picture is cropped, the analysis flags it with `✂ crop l=…% t=…% r=…% b=…%` and prints four ready-to-paste CSS percentages — `width`, `height`, `left`, `top` — already computed against the wrapper. Plug them into a wrapper that's sized to the bbox and clips overflow:

```md
<div class="cropped">
  <img src="./image3.png" alt="…" />
</div>

<style scoped>
.cropped {
  position: relative;
  overflow: hidden;
  /* size to the picture's bbox; aspect-ratio + flex works too */
  width: 100%;
  aspect-ratio: 406 / 300;   /* bbox w/h from the analysis */
}
.cropped img {
  position: absolute;
  /* paste the four values from the analysis directly */
  width: 123.1%;
  height: 100%;
  left: -11.53%;
  top: 0%;
}
</style>
```

The math: width = `100 / (100 - l - r)` × 100%, height = `100 / (100 - t - b)` × 100%, left = `-l / (100 - l - r)` × 100%, top = `-t / (100 - t - b)` × 100%. The script prints these directly so you don't have to compute them — just paste.

For the common case of "use the cropped image inside the `media` layout's `::media::` slot", wrap the `<img>` in the cropping div and place that div in the slot. The layout's media container becomes the bbox; the wrapper clips to it.

### Videos

Google's PPTX export silently flattens every embedded video into a static thumbnail picture — the URL, source, and playback settings are gone. To preserve them, the `google-slides-export` skill writes a `<deck>.videos.json` sidecar alongside the PPTX whenever it sees video elements; `prep.py` reads it automatically and surfaces a `**Videos:**` block on every affected slide, plus a `⚠ video placeholder` tag on the picture that should be replaced.

In `slides.md`, embed the video in place of the placeholder picture:

```md
<!-- YouTube -->
<Youtube id="dQw4w9WgXcQ" width="480" height="270" />

<!-- or plain iframe (works on both Slidev and a static SPA build) -->
<iframe
  src="https://www.youtube.com/embed/dQw4w9WgXcQ"
  width="480" height="270"
  frameborder="0"
  allow="autoplay; encrypted-media; picture-in-picture"
  allowfullscreen
></iframe>

<!-- Drive videos -->
<iframe
  src="https://drive.google.com/file/d/<FILE_ID>/preview"
  width="480" height="270"
  allow="autoplay"
  allowfullscreen
></iframe>
```

Position the embed using the sidecar's bbox (in deck px) — typically inside a positioned container so it lands where the thumbnail used to. The placeholder picture itself should be left out of the converted slide entirely; the analysis's `⚠ video placeholder` tag tells you which `image*.png` to skip.

If the user only has a PPTX (no Slides URL / no sidecar), the original video is unrecoverable from the file alone — ask them for the URL.

## Notes for the assistant

- The prep script is stdlib-only — no install step needed.
- The analysis is intentionally low-level (raw px positions, raw text). Use judgment when translating: don't try to mechanically reproduce every element's position, and don't preserve decorative shapes the original used as background filler.
- **Visual fidelity is not the goal.** Structural clarity and themeability are. If the source uses six fonts and four highlight colors, your conversion uses one font and `currentColor`.
- The script does **not** overwrite existing dirs. If a previous conversion lives there, ask the user before removing it.
- Speaker notes in Google-Slides-exported PPTX are usually empty placeholders. The script filters out the slide-number marker, so anything that shows up in the "Notes" section of the analysis is real content worth keeping (translate to Slidev's `<!-- ... -->` comment block under the slide, which becomes presenter notes).
- After verifying the build, delete `dist/` and the `_analysis.*` files so the talk dir stays clean.
- If the source deck used SmartArt or other Google-rendered shapes, Google often rasterizes them to images on PPTX export. You'll see them as picture elements rather than shape lists — that's expected; just place the image.
