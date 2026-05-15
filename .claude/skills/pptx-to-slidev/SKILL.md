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

1. Copy `template/` to `<repo>/<output>/` (slides.md, package.json, `vite.config.ts`, `components/Diagram.vue`, an empty `diagrams/` dir). **Fails if the dir already exists** — ask the user before clobbering.
2. Extract every image from `ppt/media/` into the new dir (co-located with `slides.md`, **not** in `public/`).
3. Parse each slide and write `_analysis.json` + `_analysis.md` into the new dir.

After the script runs, **read `_analysis.md`** end-to-end, then design and write `slides.md`. Delete `_analysis.json` and `_analysis.md` once you're done with them.

The `vite.config.ts` extends Vite's `server.fs.allow` to include the repo root so the deck can import the shared `_shared/diagram/Diagram.vue`. The `components/Diagram.vue` wrapper auto-registers `<Diagram>` globally for every slide via Slidev's `components/` auto-import.

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
| Image + text side-by-side | `two-cols-header` or `two-cols` |
| Closing slide ("thanks", "questions") | `end` |
| Ordinary content slide | (no layout — use the default) |

These are starting points, not rules. Pick whatever reads best.

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

#### Three patterns to watch for in `_analysis.md`

1. **Progressive bullets / shapes** — adjacent slides where each transition adds one or more elements. Each diff block = one click. Collapse with `<v-clicks>` (when the order matches DOM order) or `v-click="N"` (when it doesn't).
2. **Diagram build-ups** — adjacent slides where new shapes appear over a constant base. Inside the `<Diagram>` spec, set `revealAt: N` on every element introduced by transition N — boxes, connectors, and groups all share the same N.
3. **Highlight reveals** — adjacent slides with **identical plain text** but **different per-run formatting** (a sentence is black on one slide and gray on the next). The script flags these as `⚠ HIGHLIGHT-REVEAL` in the analysis and prints a per-run `[default] / [#XXXXXX] / [b]` breakdown under each formatted paragraph. **Do not collapse these by stripping formatting** — that loses the speaker's emphasis cue. Instead, split the text into segments and bind a class to `$clicks`:

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
      "anchor": "top-left",       // optional, where (x, y) sits on the box — see below (default: top-left)
      "parent": "frame",          // optional, treat (x, y) as offsets from another box's top-left — see below
      "text": "Input",
      "style": "rnn",             // optional, becomes CSS class `box-rnn` on the <g> element
      "rx": 3,                    // optional corner radius (default 3 for boxes, 4 for groups)
      "revealAt": 2,              // optional, appear at click N and stay (shorthand for `reveal: { from: N }`)
      "reveal": { "from": 1, "to": 2 }  // optional, visible from click 1 through click 2 — see Reveals below
    }
  ],
  "connectors": [
    { "from": "input1.top", "to": "emb1.bottom" },                              // straight, both ends snapped
    { "from": "rnn1.top", "to": "attn.left", "route": "VH" },                   // V then H — sharp elbow at (rnn1.x, attn.y)
    { "from": "rnn1.top", "to": "attn.left", "via": [{ "y": "attn.center" }] }, // same elbow via an explicit waypoint
    { "from": [330, 168.1], "to": "rnn1.bottom" },                              // free endpoint as a literal tuple
    { "from": { "snap": "rnn1.top", "dy": 50 }, "to": "data.top" },             // free endpoint as a snap+offset
    { "from": "a.right", "to": "b.left", "style": "highlight", "arrow": false },
    { "d": "M 776 168 Q 700 100 600 180", "style": "curve" }                    // raw SVG path — fallback for curves
  ]
}
```

**Box positions:** raw pixel coords in the `viewBox` coordinate system — the analysis already gives them in this form, so copy directly.

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

#### When to use raw `d` (escape hatch)

The `d` field is the SVG path `d` attribute — the same `M`/`L`/`H`/`V`/`Q`/`C` mini-language the analysis emits for every connector. Prefer `from`/`to`/`via` for everything orthogonal; reach for `d` only when:
- the source has a freeform curve (Bézier) the waypoint model can't express,
- you want to preserve the analysis's suggested `d` verbatim and don't care about anchoring it semantically.

The analysis prints a ready-to-paste `d="…"` for every source connector. Snap when you can (more readable, edits stay coherent if box positions shift), use `d` when you must.

#### Reveals

Two forms, both work on boxes, groups, and connectors:

- `revealAt: N` — appear at click `N` and stay forever. Shorthand for `reveal: { from: N }`.
- `reveal: { from: A, to: B }` — visible from click `A` through click `B`, **inclusive on both ends**, then hidden. Useful when an explanatory label needs to swap each step of a build-up. The component handles the translation to Slidev's half-open internal range — you write inclusive coordinates and they work as written.

```jsonc
{ "id": "explain-forget", "text": "The forget gate…", "reveal": { "from": 1, "to": 1 } },  // visible at click 1 only
{ "id": "explain-input",  "text": "The input gate…",  "reveal": { "from": 2, "to": 2 } }   // visible at click 2 only
```

Slidev derives the slide's total click count from the highest value seen in any `v-click` directive on the slide. Use the bare `revealAt: N` form (or `reveal: { from: N }`) for "appear and stay" — **never** put an artificially large sentinel like `99` in the upper bound, because Slidev will then require 99 clicks before advancing.

Don't pass `0` as `from`/`to`/`revealAt` — Slidev normalizes 0 to 1 with a console warning, so the result won't be what you wrote. If you need an element visible at the initial state and hidden after click 1, put it outside the Diagram spec and use `v-click.hide="1"` directly on the Vue element (see the direct `v-click` gotchas section above).

If a build-up needs the same element to *move* between clicks (e.g. an Output box at one y-coord for clicks 0–1, then a different y-coord from click 2 onward), declare two boxes with overlapping coords and complementary `reveal` ranges. There's no built-in tween.

#### Theming

The component bakes in: `currentColor` strokes, transparent fill defaulting to `var(--slidev-theme-bg)`, group rects dashed at 0.6 opacity, text using inherited font. Per-deck theming goes in the slide's `<style scoped>` block:

```css
.my-theme :deep(.box-rnn rect)    { fill: rgba(255, 153, 0, 0.12); }
.my-theme :deep(.box-label rect)  { stroke: none; fill: transparent; }
.my-theme :deep(.box-label text)  { font-style: italic; }
.my-theme :deep(.connector-skip path) { stroke: #d33; stroke-width: 2.5; }
```

`:deep()` is required because the slide's scoped CSS can't reach inside the Diagram component otherwise. The class on each generated element is `box-<style>`, `group-<style>`, or `connector-<style>` — pick semantic `style` values in the spec (`rnn`, `attention`, `label`, `callout`, `arc`, `highlight`, …) so the CSS reads.

#### When to fall back to inline SVG

The Diagram component covers boxes-and-connectors with single-line text. Fall back to inline SVG / HTML when a slide needs:
- multi-line or mixed-formatting text inside boxes (the component renders text as `<text>`, not foreignObject),
- non-rectangular shapes (circles, polygons, freeform),
- per-element text alignment that isn't centered,
- tweened motion between clicks.

These cases are rare. Try the component first.

### When to use Mermaid instead

If a slide is flagged `💡 Mermaid candidate (LR|TB)` in the analysis, every shape is a basic node and every connector snaps cleanly between two shapes — the diagram is graph-shaped, not spatially meaningful. Prefer a Slidev ```` ```mermaid ```` block in those cases: less code, automatic layout, and `v-click` still works via CSS class toggles.

Skip the Mermaid suggestion (and use `<Diagram>`) when the spatial arrangement itself carries meaning: a "World ↔ Mind" pair with curved arrows above and below, three connectors that share a horizontal segment to signal "all encoder states feed attention", a skip-connection arrow that visibly bypasses an intermediate node. Mermaid would flatten these into auto-routed flows and lose the metaphor.

See `.agents/skills/slidev/references/diagram-mermaid.md` (installed via `npx skills add slidevjs/slidev`) for Mermaid-in-Slidev specifics.

### Gotcha: blank lines + indentation inside raw HTML/SVG blocks

If you find yourself hand-writing a raw `<svg>` block in slides.md (rather than using `<Diagram :spec="…" />`), watch out for this: Slidev's markdown parser treats a blank line inside an HTML block as a paragraph break and re-enters markdown mode for what follows. If the next line is indented **4+ spaces** (the natural indent for nested SVG children), markdown wraps it in `<pre><code>`, and Vue then fails the build with "Element is missing end tag" or "`<pre>` cannot be child of `<svg>`".

Two fixes (either works): strip the indentation so no child line starts with 4+ spaces, or keep the indent but remove every blank line inside the block — the blank line is what re-arms the markdown code-block rule.

Default to `<Diagram :spec="…" />` and you'll never hit this.

### Images

Images live alongside `slides.md` after the prep script runs. Reference them with a **relative** path: `<img src="./image1.png" />` or `![](./image1.png)`.

Slidev's build will fail with `Import "/foo.png" from slide Markdown resolves outside of Vite server.fs.allow` if you use an absolute `/foo.png` path. **Do not** move images into `public/` — that's the path that triggers the error.

## Notes for the assistant

- The prep script is stdlib-only — no install step needed.
- The analysis is intentionally low-level (raw px positions, raw text). Use judgment when translating: don't try to mechanically reproduce every element's position, and don't preserve decorative shapes the original used as background filler.
- **Visual fidelity is not the goal.** Structural clarity and themeability are. If the source uses six fonts and four highlight colors, your conversion uses one font and `currentColor`.
- The script does **not** overwrite existing dirs. If a previous conversion lives there, ask the user before removing it.
- Speaker notes in Google-Slides-exported PPTX are usually empty placeholders. The script filters out the slide-number marker, so anything that shows up in the "Notes" section of the analysis is real content worth keeping (translate to Slidev's `<!-- ... -->` comment block under the slide, which becomes presenter notes).
- After verifying the build, delete `dist/` and the `_analysis.*` files so the talk dir stays clean.
- If the source deck used SmartArt or other Google-rendered shapes, Google often rasterizes them to images on PPTX export. You'll see them as picture elements rather than shape lists — that's expected; just place the image.
