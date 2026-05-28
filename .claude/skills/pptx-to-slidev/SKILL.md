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

The file opens with a `## Contents` table-of-contents — one line per slide with the slide's title (or first paragraph) and any annotation icons it has (`🪄`, `🎬×N`, `🔄`, `🔁`, `⚠`, `⛔`, `⛔text-swap`, `💡<dir>`, `🪧`). Scan the TOC first to spot the high-signal slides; then read those slides' detail blocks. Also: when a slide's shape geometry is identical to the previous slide's, the `**Shapes (px in deck coords):**` block elides with `_(identical to slide N)_` rather than repeating — the diff block above carries the per-transition signal.

The deck's `package.json` pins `slidev-theme-fenbrook` from GitHub, and `slides.md` headmatter selects it via `theme: fenbrook`. The theme provides `<Diagram>` and all the other components (`<Hi>`, `<DataTable>`, `<Cropped>`, `<Sticker>`, `<AnnotatedImage>`, …) as globally-registered components — no wrapper file, no `vite.config.ts`, no relative paths.

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
5. **Verify the build + render in one call:** `.claude/scripts/verify-talk.sh <talk-dir>`. The script runs `npm install` (if needed), `npx slidev build`, starts `npm run dev`, headless-screenshots every slide into `<talk-dir>/_shots/slide-N.png`, and stops the dev server. If build fails, it prints the tail of the build log and exits non-zero. Read the resulting PNGs with the `Read` tool to catch layout regressions that `npx slidev build` won't surface (Vite import-analysis differences, layouts that overflow the 16:9 box and trigger slidev's auto-scale-down, scoped-CSS clashes, missing fonts, etc.). The common offender is relative JSON imports from `<script setup>` — see "Recreating diagrams" for the `import.meta.glob` workaround.

   Useful flags: `--shots 1,3,5-7` for a subset, `--shots none` to skip screenshots (build-only), `--port N` if 3030 is taken (auto-fallback to next free port if not specified).

6. **Clean up:** `.claude/scripts/cleanup-talk.sh <talk-dir>`. Removes `_analysis.json`, `_analysis.md`, `_thumbnails/`, `_shots/`, and `dist/` in one shot.

### Mapping slide kinds to Slidev layouts

| Source slide | Slidev layout |
| --- | --- |
| Title with subtitle / framing bullets | `cover` (or default with `class: text-center`) |
| Pull-quote with attribution | `quote` |
| Blank slide acting as a divider | `section` |
| Single centered headline / call-to-action | `center` |
| Image + text side-by-side | `media` (fenbrook) — `side: left|right`, optional `caption` |
| 2–6 images in a grid / mosaic | `gallery` (fenbrook) — named slots `::a::`–`::f::`, optional `::overlay::` for a centered card |
| Full-bleed background image with overlaid text | `image-bg` (fenbrook) — props `image`, `align`, `darken`, `position`, `tint`. **For photographs only** — never for data viz / charts (the overlay text lands on top of the chart). |
| Title pinned at top + tall content (table, chart, big diagram) | `panel` (fenbrook) — props `align: 'left' \| 'center'`, `gap`. Use whenever `default`'s vertical-centering would push the H1 off-screen. |
| Naked source thumbnail (hand-drawn figure, freeform diagram) | `image` (fenbrook) — props `image`, optional `caption`, `captionPosition: 'top' \| 'bottom'`. The caption gets a scrim background so it stays readable over any image edge. |
| Truth table / small data grid | `panel` + `<DataTable :headers :rows :highlight-row :highlight-col />` (so the H1 stays anchored above the table) |
| Closing slide ("thanks", "questions") | `end` or `outro` (fenbrook) |
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
3. **Image-swap reveals** — adjacent slides with **identical text** but **different pictures** (a single heading like "Is this multiple realizability?" with the photo pair swapping each click), or layered photos where one image gets revealed regions on click. The script flags these as `🔄 IMAGE-SWAP-REVEAL` *only when one of three collapse signals is present*: shared heading/text, overlapping picture bboxes (layered), or constant non-picture overlay shapes (callouts annotating the swap). The recommended primitive is `<AnnotatedImage>` with N `<Layer src :at :reveal-at>` children — see "Annotated images" below. The older `<div class="stage">` + manual `v-click.hide` recipe still works but is more verbose.

   **The complement: `🔁 ADJACENT-PICTURE-SLIDES`.** When adjacent picture slides have NO shared heading, NO overlapping bboxes, and NO constant overlay — they're disconnected illustrative examples. The script recommends **N separate `layout: image` slides with captions** in that case. Don't collapse; let the viewer page back and forth between examples instead of hiding them behind clicks.
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
| Visible at start (click 0), hidden from click N onward | `v-click.hide="N"` | `hideAt: N` |
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

When the analysis lists multiple shapes and connectors with positions, the slide is a diagram. **Default to the `<Diagram>` component** (auto-registered globally by `slidev-theme-fenbrook`). Write the geometry as a JSON spec file in the deck's `diagrams/` directory and reference it.

#### Workflow per diagram slide

1. Create `diagrams/<descriptive-name>.json` in the deck dir.
2. In the slide section of `slides.md`, add a `<script setup>` block that loads the spec via `import.meta.glob` (see "Why `import.meta.glob`" below).

> **`<script setup>` is per-slide.** Slidev compiles each slide as its own Vue component, so `<script setup>` blocks are scoped to the slide they appear in. Variables imported on slide 7 are *not* visible on slide 8 — every diagram slide needs its own `<script setup>` block (even when loading the same spec twice). A `slides.md` with N diagram slides has N `<script setup>` blocks, each loading what *that* slide uses. This is fine and expected; don't try to hoist them.
3. Render with `<Diagram :spec="..." />`, optionally passing `class="..."` so the slide's scoped CSS can theme it via `:deep()`.

```md
<script setup>
const _specs = import.meta.glob('./diagrams/*.json', { eager: true, import: 'default' })
const spec = _specs['./diagrams/my-diagram.json']
</script>

# Slide title

<Diagram class="my-theme" :spec="spec" />

<style scoped>
.my-theme :deep(.box rect) { fill: none; stroke: none; }            /* zero out default box borders */
.my-theme :deep(.box-emphasis rect) { fill: rgba(255, 153, 0, 0.18); }
</style>
```

> **Why `import.meta.glob` instead of a plain `import`?** Vite's dev-mode import-analysis can't resolve relative paths from Slidev's virtual `slides.md__slidev_N.md` files, so `import spec from './diagrams/foo.json'` works in `npx slidev build` but silently breaks in `npm run dev` — Vite throws a "Failed to resolve import" error and the slide renders without the diagram. `import.meta.glob` is processed by Vite specially and resolves correctly in both modes. The pattern is a one-line cost; use it for every diagram slide. (The trailing `[N]` indexing into `_specs` is paste-friendly: change the filename in one place when you rename a spec.)

> **Zero out default box borders.** Every `<Diagram>` `<g class="box">` renders its `<rect>` with the default `stroke: currentColor`, so any `style:` you add to a spec ships with a visible border by default. The `.box rect { fill: none; stroke: none; }` rule above is a safe starting point — then opt boxes back in via per-style `box-<style>` rules (`.box-neuron rect { fill: #333399; }`, etc.). Skipping this is how you end up with mysterious empty rectangles around your text labels.

#### Full spec reference

The `<Diagram>` API — every prop, every spec field, snap/route/outset syntax, reveal semantics, theming hooks — lives in [`docs/DIAGRAM.md` in the theme repo](https://github.com/jodeleeuw/slidev-theme-fenbrook/blob/main/docs/DIAGRAM.md). **Read it once before writing your first spec.** This skill only covers the PPTX → spec translation; everything else is in that doc.

#### Mapping prep.py annotations to spec fields

What the analysis surfaces and where it lands in the spec:

| Analysis annotation | Spec field | Notes |
|---|---|---|
| Position `(x, y, w, h)` on a shape | `x`, `y`, `w`, `h` | Already in viewBox coords — copy directly. |
| `shape=ellipse` / `roundRect` / `rightArrow` / `leftArrow` / `upArrow` / `downArrow` | `shape` | PPTX `<a:prstGeom>` shapes. Default is rectangle when omitted. |
| `fill=#RRGGBB` | `fill` | Inline color override. PPTX scheme colors are deliberately skipped (they default to white/dark and would clobber the theme). |
| `vert=270` | `textRotate: "vertical-up"` | CCW, reads bottom-up. |
| `vert=90` | `textRotate: "vertical-down"` | CW, reads top-down. |
| Connector arrow modifier (`arrow=reverse`/`both`/`none`) | `arrow` | From `<a:headEnd>` / `<a:tailEnd>`. Default (`forward`) means omit the field. |
| `**[SELF-LOOP]**` or `**[MULTI-BEND]**` flags | `outset` + optional `via` | The analysis prints a suggested spec snippet on the next line — paste that rather than the raw `d=`, because snap refs stay coherent if positions shift. |
| Background photo per slide | `background:` or `backgrounds[]` | But see PDF-export caveat below. |

**PDF-export caveat for `background` / `backgrounds`:** the SVG `<image>` element these generate can render dim or be omitted entirely by Playwright + Chromium under some PDF export configurations.

- **Photographs and gradient-heavy rasters** → prefer the `<AnnotatedImage>` recipe (HTML `<img>` for the base) rather than the SVG `<image>` element. This is the case the PDF-export pipeline gets wrong.
- **Line-art figures / chart screenshots / clean-edged diagrams** → `backgrounds:` (or `background:`) is fine. These render reliably in PDF export and let you use the diagram coord system for overlay annotations without extra wrapping markup.

The `background` field is also fine for programmatic patterns, `data:` URIs, or live-only viewing.

#### When to give up on `<Diagram>` (and reach for stickers, inline SVG, or — last resort — the thumbnail)

The component is great for **graph-shaped** diagrams: 5–15 labeled boxes connected by snap-routed arrows, where the spatial arrangement matters but the visual style doesn't. It's *not* the right tool for everything in the deck. Bail when:

- The slide is flagged with the `🪄 Freeform/dense figure` annotation — prep.py already decided this isn't graph-shaped, take the hint.
- The diagram has **more than ~15 shapes** and you're scaffolding from scratch — the JSON authoring cost dominates.
- The source uses **decorative imagery as load-bearing content** (the reduction ladder has hand-drawn animal silhouettes next to each "scale" label; the cognitive-mapping deck has a brain with arrows pointing into specific regions). Recreating those in SVG loses the point.
- The source is **rasterized SmartArt / Visio / clipart** that came across as one `image*.png`. Don't try to reverse-engineer it; just place the image.
- The diagram has **mixed-formatting or rich text inside boxes** (bold + color within one label, equations, code) that won't survive the `<text>` element.
- The shapes are **non-rectangular** (organic curves, polygons, freeform) and `shape: "ellipse"` isn't enough.
- The slide has **non-graph PPTX shapes** (`cloudCallout`, `wedgeRectCallout`, freeform `<a:custGeom>`, hearts, suns, banners) — `<Diagram>` only supports rect / roundRect / ellipse / arrow.

**Preferred fallback: `<Sticker>` + inline SVG for any decorative chrome.** Most "unusual layout" slides are some combination of:

1. A few free-floating images at specific positions (sticker territory)
2. One or two decorative PPTX shapes you can't recreate in `<Diagram>` (cloud bubble, custom callout) — draw these inline with a small `<svg>` block
3. A text overlay or caption (positioned via `<v-drag>` or absolute CSS)

This composes cleanly and keeps theme typography. The two-facing-heads-with-a-thought-bubble pattern is the canonical case: two `<Sticker>`s (one with `flipH`), an inline `<svg>` cloud, and the question text — all positioned via a single `dragPos:` frontmatter block. Drag-edit in `npm run dev` to fine-tune. See "Free-floating images / `<Sticker>`" below.

```md
---
footer: false
dragPos:
  head-left:  "16,16,374,518"
  head-right: "597,16,374,518"
  bubble:     "353,0,311,245"
  question:   "300,330,400,160"
---

<Sticker id="head-left"  src="./image10.png" />
<Sticker id="head-right" src="./image10.png" flipH />

<v-drag pos="bubble">
  <svg viewBox="0 0 311 245" preserveAspectRatio="none">
    <path d="M 70 165 Q 30 165 30 125 …" fill="#fff" stroke="#222" stroke-width="2" />
  </svg>
</v-drag>

<v-drag pos="question">
  <p>Or do we use concepts like <em>belief</em> and <em>desire</em> to make sense of behavior?</p>
</v-drag>
```

**Fallback of last resort: the source thumbnail.** Every slide has a PNG in `_thumbnails/slide-N.png` (when `google-slides-export` produced them). Use it only when:

- The slide is flagged `🪄 Freeform/dense figure` (a hand-drawn figure that's not worth reconstructing), or
- The composition is genuinely too fiddly to recreate (dozens of stickers, complex custom paths, baked-in shading).

```md
---
layout: image
image: ./_thumbnails/slide-11.png
caption: "Tic-tac-toe as a symbol system: board state plus a set of legal actions."
---
```

Thumbnails are 1600×900 PNGs that bake in the source theme — typography won't match Slidev, you can't reposition pieces, and the file has to be moved out of `_thumbnails/` before cleanup (since the cleanup script wipes that directory). Default to stickers + inline SVG; reach for thumbnails only after that's been ruled out.

#### Known `<Diagram>` limitations

Things the component does not (yet) do — work around with the strategies above:

- **No obstacle avoidance.** A connector from A.right to C.left will draw straight through anything in between (e.g. a box B sitting on that line). Either route around with `via`/`route`, or move B, or accept the crossing.
- **No animations between two states of the same element.** Text content can swap across clicks via `textByClick`, but if a box needs to *move* or *resize*, declare two boxes with complementary `reveal` / `hideAt` ranges (no built-in tween).
- **Labels on raw `d:` paths.** Connector `label` requires resolvable `from`/`to` endpoints. For curved connectors written as raw SVG `d:` paths, add a no-border text box at the label location instead.

### Analysis annotations reference

Beyond the geometry/text dump and diff blocks, `_analysis.md` emits a few semantic hints. Recognize them on a quick scan:

- `**Tables:**` (per slide) — PPTX tables (`<a:tbl>`) extracted with cell contents. Convert with the theme's `<DataTable :headers="..." :rows="...">` component (or a raw markdown table). The script prints rows as JSON arrays so they're paste-ready. Header detection prefers PPTX's `<a:tblPr firstRow="1">`, then `<a:tr h="1">`, then "all-bold first row"; when nothing matches it emits `Headers: null` and puts every row in `Rows`.
- ` vert=270` / `vert=90` / `vert=stacked` on a shape line — the shape's text is rotated. Map directly to `textRotate: "vertical-up"` (270) / `"vertical-down"` (90) on a `<Diagram>` box, or wrap with `transform: rotate(...)` in raw HTML. Picked up from `<a:bodyPr vert="...">` *or* `<a:xfrm rot="...">` (PPTX uses both).
- ` 🎨 full-slide overlay (likely a darken scrim over a background picture)` — a slide-sized opaque rect at (0,0), low luminance. **Don't render this as a content shape.** It's a darkening scrim over a background photo; treat the picture beneath as a background and put the overlay in CSS (a `linear-gradient` over the image, or `fenbrook`'s `image-bg` layout with `darken: 0.6`).
- ` ✂ crop l=…% t=…% r=…% b=…%` on a picture — the source image is wider/taller than the bbox; only the visible portion shows. See "Cropped pictures" below for the wrapper recipe.
- ` ⚠ video placeholder` on a picture — the source had an embedded video; Google's PPTX export replaced it with a thumbnail. The `<deck>.videos.json` sidecar has the original URL/embed metadata. See "Videos" below.
- `🔄 IMAGE-SWAP-REVEAL` (slide annotation) — adjacent slides where the pictures change AND at least one collapse signal is present: a shared heading/text, overlapping picture bboxes (layered swap, not alternatives), or constant non-picture overlay shapes (callouts annotating a changing photo). The annotation lists which signals fired. Collapse into one Slidev slide — `<AnnotatedImage>` is the recommended primitive (see "Annotated images" below).
- `🔁 ADJACENT-PICTURE-SLIDES` (slide annotation) — adjacent slides with different pictures but **none** of the IMAGE-SWAP-REVEAL collapse signals (no shared heading, no overlapping bboxes, no constant overlay). These are disconnected illustrative examples that happen to sit next to each other. **Recommend N separate `layout: image` slides with captions** rather than a click-collapsed swap stack. The N-separate-slides form lets the viewer page back and forth between examples instead of hiding them behind clicks.
- `⚠ HIGHLIGHT-REVEAL` (slide annotation) — same text as previous slide but per-run formatting (strike, color, bold) changed. Collapse with `$clicks`-bound CSS classes.
- `💡 Mermaid candidate (LR|TB)` (slide annotation) — see "When to use Mermaid instead" below.
- `🎬 PPTX animation — N clicks built into this slide` (slide annotation, between the diff block and per-element listings) — the source slide has in-PPTX animations on its shapes (entrance, exit, emphasis, motion). The annotation lists each user-click group with its target spids and effect kind. **This is the highest-signal cue in the whole analysis**: you're not collapsing duplicate source slides into clicks; you're literally reading the click reveals the original author embedded into a single slide. Map every group to a `revealAt: N` on the corresponding shape/picture/connector. Note that animation targets can be pictures too (PPTX `<p:pic>` elements), which appear in the slide's `**Pictures:**` block — match the spid in the annotation against the shape's `#NNN` id or by position. See "Annotated images" below for the canonical recipe when overlay boxes/labels animate over a photograph.

  **Click-run collapse.** When N (≥ 3) consecutive clicks all target the same shape with the same effect, the listing collapses to one line like `clicks 1–11: shape #237 (entrance × 11 consecutive — likely a paragraph or bullet build on a single text shape)`. When PPTX has an explicit `<p:bldP build="p">` marker on that shape (paragraph-by-paragraph build), the line names it directly. If the paragraph count from the shape's text doesn't match the click count (PPTX sometimes emits one extra click per nested bullet build), the line flags the mismatch.
- `🪄 Freeform/dense figure (N shapes, M with no text)` (slide annotation, near the top) — the slide is a hand-drawn drawing, freeform diagram, or decorative mesh (X/O on a board, network spaghetti). Trying to recreate this in `<Diagram>` is wasted effort — use `layout: image` with the source thumbnail. The accompanying suggestion in the annotation gives you the exact `<img>` path. Triggers when there are ≥ 12 positioned shapes, ≥ 55% have no text, AND there are ≥ 12 empty shapes in absolute terms (gates out perceptron-style schematics that hit the ratio early in their build). A second-stage check disables the flag when the empty shapes look like the unlabeled member of a labeled-grid pair (≥ 80% share an X coordinate, or each has a non-empty sibling within `2 × shape_width` horizontally) — those are tractable in `<Diagram>` as two-column layouts.
- `⛔ scene change` (diff-block header swap) — replaces the usual "treat the whole block as one click" hint. Fires on either of: (a) ≥ 70% of a 5+ shape prior is wiped + at least one new shape added, or (b) 100% of the prior's shapes are removed regardless of count (catches title → body transitions that path (a)'s 5-shape gate misses). **Do not** wrap the affected slides as `v-click` reveals; author them as separate Slidev slides.
- `⛔ text-swap scene change` (diff-block header swap) — every shape stayed put but the *only* change is a text replacement on a single shape, and the new text shares no word tokens with the old (Jaccard ≤ 0.15). The "stable banner with rotating content" pattern, where the source author rotated unrelated content through one persistent text frame. Treat as a fresh slide, not a click-driven swap.
- `🪧 Sticker candidate (N free-floating pictures)` (slide annotation, under the `**Pictures:**` block) — the slide has **2+** free-floating images and no grid/swap signal. The block prints (a) a `dragPos:` YAML snippet to paste into the slide's frontmatter and (b) one `<Sticker>` or `<v-drag>+<Cropped>` line per picture, with `flipH` / `flipV` / `:rotate` props pre-filled from any PPTX transforms. Initial positions are computed from PPTX coordinates (Slidev's default 980-wide 16:9 canvas). After pasting, `npm run dev` and **double-click any sticker** to drag / resize / rotate in place — the editor writes new positions back to the `dragPos:` block. See "Free-floating images / `<Sticker>`" below. The annotation fires at the lower 2-picture threshold deliberately — meme-style "article + reaction photo + caption" slides and "two facing heads + thought bubble" slides both compose better with stickers + inline SVG than with `layout: image` + a baked thumbnail. **Skip the Sticker block** if the picture set is actually a grid (use `gallery`), a single dominant figure (`media` / `image`), or an annotation overlay on one base image (`<AnnotatedImage>`).
- ` ⤿ flipH` / ` ⤿ flipV` / ` ⤿ rot=N°` on a picture line — the source PPTX has `<a:xfrm flipH="1">`, `flipV="1"`, or `rot="…"` on this picture. These don't show up in the coords, so they used to silently get lost. Map straight to `<Sticker flipH>`, `<Sticker flipV>`, or `<Sticker :rotate="N">`. The Sticker block in a `🪧 Sticker candidate` annotation already inlines these props for you.
- `decorative slivers (cropped views of the same image, likely a parallax/stripe overlay; not load-bearing)` — surfaced both in the per-slide `**Pictures:**` block and inside `added pictures` / `removed pictures` diff entries. Means the source author tiled many thin cropped strips of a single image as background decor. Skip them entirely — render the un-cropped image as the slide background (e.g. via `layout: image-bg`) and ignore the slivers. The diff block's count in the `(N)` header stays accurate (semantic content unchanged); only the per-entry rendering collapses.

**Multi-paragraph shape text.** When a shape has more than one paragraph, the per-slide listing emits a fenced block under the geometry line (not the inline `text='...'` form). Diff blocks still join with ` | ` because they need to be compact. Either way: one paragraph = one `<p>` (or one `lines[]` entry) when you author the slide.

**When the paragraphs in shape A visually align with separate items in shape B, split A into separate boxes.** PPTX authors will sometimes put 6 lines of text (e.g. "Sociology / Psychology / Biology / Biochemistry / Classical physics / Quantum mechanics") in a single tall text shape, with line spacing chosen so each line sits at the same y as one of 6 separately-positioned items elsewhere on the slide (e.g. a "metaphysical reduction ladder" with 6 scale-label boxes). The PPTX listing shows shape A as one box; the diff makes it look like a single element. **Don't model it as one `<Diagram>` box with a `lines: [...]` array** — that stacks all 6 lines tightly at the top and breaks the horizontal alignment with shape B. Instead, split A into 6 separate boxes at the matching y-coords (copy the y/h from B's rows, offset only the x), so each line stays aligned with its counterpart. The thumbnail makes this pattern obvious; the geometry dump alone doesn't.

**Run-format tags.** Inside the per-paragraph breakdown, runs are tagged like `` [default] `` / `` [b+#FF0000] `` / `` [is] `` / `` [u] `` where letters mean: `b` bold, `i` italic, `s` strikethrough, `u` underline. They collapse into one token (`[bs]` = bold + strike) and a `+#RRGGBB` color suffix follows when present. Strike and underline pass through to your slide via GFM (`~~text~~` for strike) or inline CSS — no special component needed.

### Inline fenbrook components

Beyond `<Diagram>`, the `fenbrook` theme ships a handful of inline components that auto-register on every slide.

- `<Hi>text</Hi>` — keyword highlight. Variants: `marker` (default; underlay), `solid` (color only), `box` (border).
- `<Quiet>text</Quiet>` — paired companion to `<Hi>`. Mutes color and drops opacity so a `<Hi>keyword</Hi>` pops while the surrounding sentence fades. Variants: `muted` (default), `strike` (adds a line-through, for negation context).

  ```md
  <p><Quiet>Environmental</Quiet> <Hi>science</Hi> <Quiet>examines…</Quiet></p>
  ```

  **Markdown emphasis still applies inside.** The markdown parser runs before Vue, so `_` and `*` inside `<Hi>` / `<Quiet>` are still interpreted as emphasis markers. Multi-underscore PPTX-style fill-in-the-blank placeholders are the common failure: `<Hi>____________</Hi>` parses as a chain of `<em>` open/close tags and Vue then dies with "Element is missing end tag." Escape with `\_` (or `\*`), or replace the placeholder with non-conflicting characters (`—`, `…`, `▮▮▮▮`).

- `<DataTable :headers :rows :highlight-row :highlight-col :header-rotate />` — styled table for truth tables and small data grids. The analysis's `**Tables:**` block emits rows as JSON arrays, paste-ready. `header-rotate: 'vertical-up' | 'vertical-down'` rotates the header text 90° — match PPTX `vert=270` / `vert=90` on a co-occurrence matrix's column headers.

  ```md
  <DataTable :headers="['ice', 'steam', 'water']" :rows="[[1, 0, 1], [0, 1, 1]]" header-rotate="vertical-up" />
  ```

- `<Cropped src :crop :aspect alt />` — wrapper for PPTX cropped pictures (`✂ crop l=…% t=…% r=…% b=…%`). Pass the four edge insets straight from the analysis; the component handles the scale + offset math, sized to fill its parent (or to the supplied `aspect` if the parent doesn't constrain it). Use this inside `gallery` slots or anywhere a one-line wrapper beats a hand-rolled `.cropped` div + scoped style block.

  ```md
  <Cropped src="./image6.png" :crop="{ l: 0, t: 22.8, r: 0, b: 25.3 }" :aspect="[224, 175]" alt="Lab thumbnail" />
  ```

  See the "Cropped pictures" section below for the manual recipe — `<Cropped>` is the wrapper-shorthand for the same math.

- `<AnnotatedImage>` + `<Box>` / `<Label>` / `<Layer>` — overlay primitives for image-substrate slides. See "Annotated images" below.

- `<Sticker id src :frame :rotate flipH flipV :w :h alt />` — drag-positioned floating image. Pair with a `dragPos:` block in slide frontmatter (the prep script emits a ready-to-paste one when it sees the `🪧 Sticker candidate` pattern). `npm run dev` → double-click to drag/resize/rotate; positions write back to `dragPos[id]`. `frame: 'polaroid' | 'shadow'` for decorative chrome. `flipH` / `flipV` mirror the image (use when porting PPTX `flipH="1"` / `flipV="1"`). `:rotate="N"` is a fixed decorative tilt in degrees (composes with `rotate` from the drag editor). `:w`/`:h` are an escape-hatch size cap for when `dragPos:` is missing or you specifically want to lock the size (they block drag-resize). See "Free-floating images / `<Sticker>`" below.

#### Layout prop reference

A few non-obvious props worth knowing about on the theme layouts:

- `layout: aside`, `asideStyle: 'card'` — wraps the sidebar in a rounded-border container with a subtle tint, matching PPTX-style roundRect callouts. The default `'rail'` is a flush stripe with an accent border.
- `layout: media`, `captionSide: 'right' | 'left' | 'bottom'` — defaults to `'bottom'` (caption under the frame). Side captions render as a narrow rail beside the frame — match PPTX patterns where a small citation rect sits to the right of the figure rather than beneath it.
- `layout: outro`, `mark: '?'` — single-character mark behind the closing slide. **Quote the YAML value** when the mark is a YAML reserved indicator (`?`, `:`, `[`, `]`, `{`, `}`, `&`, `*`, `!`, `|`, `>`, `%`, `@`, `` ` ``, `,`, leading `-`). See "Gotcha: YAML reserved characters" below for the full list.

### Annotated images

When a slide has the `🎬 PPTX animation` annotation **and** the underlying content is a photograph (or other raster image) with overlay annotations — bounding-box callouts, stat readouts, labels — the canonical pattern is the `<AnnotatedImage>` component (fenbrook) with image-space child elements: `<Box>`, `<Label>`, `<Layer>`. All positions are in source-pixel space (the deck `w × h` from the analysis header), so values paste straight from `_analysis.md`. HTML `<img>` for every raster layer (PDF-export safe), absolutely-positioned `<div>`s for boxes/labels.

The same component subsumes the layered-image-swap pattern (where one image is the base and others reveal regions on click). When a `🔄 IMAGE-SWAP-REVEAL` annotation lists overlapping picture bboxes, reach for `<AnnotatedImage>` rather than the older `<div class="stage">` recipe — fewer moving parts.

```md
<AnnotatedImage src="./image26.png" :viewbox="[960, 540]" fit="cover">
  <!-- Layered raster, click-revealed. Coords are source pixels. -->
  <Layer src="./image9.png" :at="[155, 77.5, 650, 385]" :reveal-at="2" />

  <!-- Callout boxes — outline rectangles in source-pixel coords. -->
  <Box :at="[135.9, 7.4, 127.3, 385.5]" :reveal-at="1" variant="callout" />
  <Box :at="[410.8, 454.7, 84, 81.5]"   :reveal-at="1" variant="callout" />

  <!-- Labels — text positioned by [x, y] point or sized [x, y, w, h] box. -->
  <Label :at="[263, 94, 336, 98]" :reveal-at="1" variant="stats">
    <strong>player</strong><br />number: 3
  </Label>
  <Label :at="[499, 439, 336, 98]" :reveal-at="1" variant="stats">
    <strong>ball</strong><br />…
  </Label>
</AnnotatedImage>

<style scoped>
/* Escape the default layout's padding so the photo is full-bleed. */
:deep(.slidev-layout.josh-default) { padding: 0; }

/* Variant theming. Variant name X becomes class `.annotated-box-X`
   (on Box) or `.annotated-label-X` (on Label). */
:deep(.annotated-box-callout) { border-color: #fff; border-width: 3px; }
:deep(.annotated-label-stats) {
  font-family: 'JetBrains Mono', ui-monospace, monospace;
  color: #fff;
  background: rgba(0, 0, 0, 0.55);
  padding: 0.4rem 0.6rem;
  border-radius: 4px;
}
</style>
```

Props:

- `<AnnotatedImage>`: `src` (base image — full-bleed `<img>` inside the wrapper), `viewbox: [w, h]` (source-pixel coord system; defaults to `[960, 540]`), `fit: 'cover' | 'contain'` (base-image fit; default `'cover'`), `layout: 'aspect' | 'container'` (defaults to `'aspect'` — wrapper locks to the viewbox aspect ratio; use `'container'` only when the parent constrains the wrapper to a matching aspect).
- `<Box>`: `at: [x, y, w, h]` (required, viewbox coords), `revealAt` / `reveal: { from, to, until }` / `hideAt` (same reveal API as `<Diagram>`), `variant: <string>` (becomes `.annotated-box-<variant>`).
- `<Label>`: `at: [x, y]` (point) or `[x, y, w, h]` (sized), reveal props, `variant`, `align: 'left' | 'center' | 'right'`. Slot accepts any markdown/HTML.
- `<Layer>`: `src` (image path), `at: [x, y, w, h]` (omit for full-bleed), reveal props, `fit: 'cover' | 'contain'`.

**Why `<AnnotatedImage>` over the old `<Diagram>`-with-`stage`-div recipe:**

- Inline in markdown — no separate JSON spec file for a one-off overlay.
- Coords stay in source-pixel space — no `100 / (100 - l - r)` percent conversions to fish for the right number.
- PDF-safe by default — HTML `<img>` for all rasters; the SVG `<image>` element issue doesn't apply.
- Subsumes the swap-stack: `<AnnotatedImage>` with N `<Layer :reveal-at>` children IS the swap-stack pattern, expressed declaratively.

`<Diagram>` stays the right tool for graph-shaped diagrams with snap-routed connectors; `<AnnotatedImage>` handles "image is the substrate, shapes sit on top."

**Click ordering:** the `🎬` annotation lists user-clicks in source order. PPTX `clickEffect` starts a new user click; `afterEffect`/`withEffect` join the previous click (no extra user input). The annotation already shows them as `click 1:`, `click 2:` — copy those indices straight into `reveal-at` / `v-click`.

### When to use Mermaid instead

If a slide is flagged `💡 Mermaid candidate (LR|TB)` in the analysis, every shape is a basic node and every connector snaps cleanly between two shapes — the diagram is graph-shaped, not spatially meaningful. Prefer a Slidev ```` ```mermaid ```` block in those cases: less code, automatic layout, and `v-click` still works via CSS class toggles.

Skip the Mermaid suggestion (and use `<Diagram>`) when the spatial arrangement itself carries meaning: a "World ↔ Mind" pair with curved arrows above and below, three connectors that share a horizontal segment to signal "all encoder states feed attention", a skip-connection arrow that visibly bypasses an intermediate node. Mermaid would flatten these into auto-routed flows and lose the metaphor.

See `.agents/skills/slidev/references/diagram-mermaid.md` (installed via `npx skills add slidevjs/slidev`) for Mermaid-in-Slidev specifics.

### Gotcha: named slots + default-slot content on `media` / `aside` / `gallery`

Layouts that mix a default `<slot />` with named `<slot name="X" />` slots — `media`, `aside`, `gallery`, `two-cols-header`, `outro`, etc. — follow one markdown rule: content *outside* any `::name::` directive goes into the default slot. **Don't** also write an explicit `::default::` block; Vue errors with "Extraneous children found when component already has explicitly named default slot."

The pattern that works: put all default-slot content (including the `# Title`) *before* the named slot directives, no `::default::` keyword.

```md
---
layout: media
side: left
---

# Why Hermissenda?                              <!-- default slot -->

Some prose about Hermissenda.                   <!-- default slot -->

::media::

<img src="./hermissenda.png" />                 <!-- media slot -->
```

If you find yourself writing `# Title` → `::media::` → content → `::default::` → more content, swap the order: put the default-slot content first and the named slot last.

### Gotcha: blank lines + indentation inside raw HTML/SVG blocks

If you find yourself hand-writing a raw `<svg>` block in slides.md (rather than using `<Diagram :spec="…" />`), watch out for this: Slidev's markdown parser treats a blank line inside an HTML block as a paragraph break and re-enters markdown mode for what follows. If the next line is indented **4+ spaces** (the natural indent for nested SVG children), markdown wraps it in `<pre><code>`, and Vue then fails the build with "Element is missing end tag" or "`<pre>` cannot be child of `<svg>`".

Two fixes (either works): strip the indentation so no child line starts with 4+ spaces, or keep the indent but remove every blank line inside the block — the blank line is what re-arms the markdown code-block rule.

Default to `<Diagram :spec="…" />` and you'll never hit this.

### Gotcha: SVG `<text>` typography attributes get overridden

Inside an inline `<svg>` in slides.md, **put typography in inline `style`**, not in presentation attributes. The attributes survive into the DOM but lose the CSS cascade to UnoCSS/theme rules, so `<text font-size="16">` ends up rendering at the slide's inherited body font size — labels come out 3–4× the intended size and overflow whatever box they were sized to fit.

```html
<!-- Wrong — font-size attribute gets out-specificity'd; renders huge -->
<text x="121" y="94" font-size="16" text-anchor="middle" fill="#111">belief</text>

<!-- Right — inline style wins the cascade -->
<text x="121" y="94" style="font-size:16px;text-anchor:middle;dominant-baseline:middle" fill="#111">belief</text>
```

`fill`, `stroke`, `x`, `y`, `width`, `height`, `viewBox`, `preserveAspectRatio`, `href` (on `<image>`) all work fine as attributes. The issue is specific to typography on `<text>` — `font-size`, `font-weight`, `font-family`, `text-anchor`, `dominant-baseline`. Easiest rule: pile all `<text>` typography into one `style="…"` and stop reaching for the per-attribute form.

This does **not** apply inside `<Diagram>` spec JSON — the component renders the SVG itself with its own scoped CSS, so spec fields work as documented. The gotcha is only for raw inline SVG authored in markdown.

### Gotcha: `<Youtube>` width/height props in flex containers

`<Youtube id="…" width="800" height="450" />` ignores `width` / `height` when nested in a flex container — the iframe ends up tall-and-narrow because the flex parent sizes it. Use a plain `<iframe>` inside a wrapper that has an explicit `aspect-ratio: 16 / 9` and let CSS handle the size:

```html
<div class="video-wrap">
  <iframe src="https://www.youtube.com/embed/<ID>"
          allow="autoplay; encrypted-media; picture-in-picture"
          allowfullscreen></iframe>
</div>

<style scoped>
.video-wrap { width: min(80%, 1024px); aspect-ratio: 16 / 9; overflow: hidden; border-radius: 6px; }
.video-wrap iframe { width: 100%; height: 100%; border: 0; display: block; }
</style>
```

This is also what the `**Videos:**` block in the analysis recommends — when porting a `⚠ video placeholder`, default to the iframe form.

### Gotcha: YAML reserved characters in frontmatter values

Slide frontmatter is YAML, so layout props that look like single punctuation marks need quoting or they get reinterpreted. The one that bites in this repo is the `outro` layout's `mark` prop: `mark: ?` parses as a complex-mapping-key indicator and arrives at the component as `undefined` (the layout silently falls back to its default `?`).

Always quote the mark:

```yaml
---
layout: outro
mark: '?'      # ← quoted. Plain `mark: ?` is a YAML parse-error / undefined.
---
```

Same applies to any value that starts with one of YAML's flow indicators: `?`, `:`, `,`, `[`, `]`, `{`, `}`, `&`, `*`, `!`, `|`, `>`, `%`, `@`, `` ` ``, or a leading `-`. When in doubt, quote.

### Images

Images live alongside `slides.md` after the prep script runs. Reference them with a **relative** path: `<img src="./image1.png" />` or `![](./image1.png)`.

Slidev's build will fail with `Import "/foo.png" from slide Markdown resolves outside of Vite server.fs.allow` if you use an absolute `/foo.png` path. **Do not** move images into `public/` — that's the path that triggers the error.

#### Cropped pictures

PPTX stores image crops as four edge insets (`<a:srcRect l="..." t="..." r="..." b="...">`, in 1/1000ths of a percent) — the source image is the full `image*.png` extracted from the deck, but only a subset is visible inside the picture's bbox. **The prep script extracts the full image; the crop is applied only at render time.** If you drop the raw `<img src="./image*.png" />` onto the slide, you'll show the whole thing instead of the framed portion the author chose.

When a picture is cropped, the analysis flags it with `✂ crop l=…% t=…% r=…% b=…%` and prints four ready-to-paste CSS percentages — `width`, `height`, `left`, `top` — already computed against the wrapper.

**Shorthand:** the fenbrook `<Cropped>` component encapsulates the wrapper + scale math. Pass the four edge insets straight from the analysis, optionally with the bbox aspect:

```md
<Cropped src="./image3.png" :crop="{ l: 0, t: 22.8, r: 0, b: 25.3 }" :aspect="[224, 175]" alt="…" />
```

`<Cropped>` fills its parent — handy in gallery cells (no extra plumbing) and in `media`'s `::media::` slot. Pass `:aspect="[w, h]"` when the parent doesn't constrain height.

**Manual recipe** (when you need to customize the wrapper further):

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

#### Free-floating images / `<Sticker>`

Some source slides have small images placed at specific, irregular positions — illustrations scattered around a central diagram, polaroid-style reference photos, a "wall" of cover art, or just an article + a reaction photo + a caption (meme territory). None of the standard layouts fit: `gallery` forces a grid, `media` assumes one dominant image, `image-bg` is a single background.

The pattern is `<Sticker id src />` paired with a `dragPos:` block in slide frontmatter. Slidev's `<v-drag>` powers the drag-edit: double-click any sticker in `npm run dev` and you get drag/resize/rotate handles. Releasing the handle writes the new pos back to `dragPos[id]` in the markdown source.

```yaml
---
dragPos:
  pic-0: "814,58,117,143"
  pic-1: "757,115,143,172"
  pic-2: "84,64,130,130"
  # ...
---

# A scattering of icons

<Sticker id="pic-0" src="./image15.png" />
<Sticker id="pic-1" src="./image2.png" />
<Sticker id="pic-2" src="./image9.png" />
```

The `pos` string is `"x,y,w,h"` or `"x,y,w,h,rotation"` in **Slidev canvas coords** (default 980 × 551, 16:9). The prep script does this conversion for you — every picture line in `**Pictures:**` ends with `→ slidev pos \`x,y,w,h\``, and when a slide has 2+ free-floating pictures the script also emits a ready-to-paste `dragPos:` YAML block and matching `<Sticker>` / `<v-drag>+<Cropped>` lines under a `🪧 Sticker candidate` annotation. Just copy both blocks into the slide and run the dev server to nudge.

**Props:**

- `id` (required) — must be unique across the slide. Keys in `dragPos:` are scoped to the slide.
- `src` (required) — relative image path.
- `alt` — alt text. Defaults to empty.
- `rotate` — fixed decorative tilt in deg. Composes with the editor's rotation handle (which writes a 5th value to the `pos` string) and with `flipH` / `flipV`. Set this when the PPTX picture line shows `⤿ rot=N°` — that's the source's intentional tilt.
- `flipH` / `flipV` — boolean. Mirror the image horizontally / vertically. Set when the picture line shows `⤿ flipH` / `⤿ flipV`. Common case: two facing heads ported from a single source image, where one of them has `flipH="1"` in PPTX.
- `frame` — `'none'` (default), `'polaroid'` (white border + drop shadow), or `'shadow'` (drop shadow only).
- `w` / `h` — optional hard size cap in slide-canvas px. Applied as inline CSS on the inner sticker box. Use when there's no `dragPos:` entry for this id (so v-drag would otherwise let the image render at its natural pixel size). **Setting `:w` / `:h` also blocks the drag editor's resize handle** — the inline style overrides whatever `<v-drag>` would apply, so the sticker freezes visually at the prop size even though dragPos is updating. Omit these props on stickers you want to fine-tune via dblclick-drag; the `dragPos:` `w,h` values handle sizing in the normal flow.

**Cropped stickers.** `<Sticker>` doesn't crop — its `<img>` always uses `object-fit: contain`. When the PPTX picture has a `✂ crop` annotation, wrap a `<Cropped>` inside a raw `<v-drag>` instead:

```md
<v-drag pos="screaming-woman">
  <Cropped src="./image3.png" :crop="{ l: 18.469, t: 0, r: 6.848, b: 0 }" :aspect="[267, 242]" />
</v-drag>
```

prep.py already emits this form in the sticker-candidate block when a picture has a crop, so you usually paste it verbatim.

**Combining with inline SVG / text overlays.** Stickers don't have to be alone. The richest unusual-layout slides combine:

- 2+ `<Sticker>` for the photographic / illustrative pieces.
- An inline `<svg>` inside a `<v-drag pos="…">` for any decorative chrome you can't recreate with `<Diagram>` (cloud bubble, custom callout, hand-drawn frame).
- A `<v-drag pos="caption">` wrapping a styled `<p>` for any meme caption or pull quote (use a dark `background` pill so white text stays readable when it overlaps a light photo).

Each gets its own entry in the `dragPos:` block. Drag-edit in dev to fine-tune.

**When NOT to use Sticker.** If the pictures form a clean grid, use `gallery`. If one picture is dominant and the rest are decorative, use `media` or `image`. If multiple pictures are layered and reveal regions on click, use `<AnnotatedImage>`. `<Sticker>` is for the *no-clean-layout* case where positions are part of the slide's meaning (illustrations next to a diagram, a board of polaroids, two facing heads with a thought bubble, etc.).

**Build vs dev.** Drag-editing only works in `npm run dev`. In `npm run build` (static SPA), stickers render exactly where the `dragPos:` block says. So: position in dev, ship from build. If `dragPos[id]` is missing for a sticker, the sticker mounts at its natural document-flow position and the editor captures whatever it lands at on the first drag — usually you want positions seeded by the prep script's `dragPos:` block.

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
- After verifying the build, run `.claude/scripts/cleanup-talk.sh <talk-dir>` to remove `_analysis.*`, `_thumbnails/`, `_shots/`, and `dist/` in one shot — keeps the talk dir clean.
- If the source deck used SmartArt or other Google-rendered shapes, Google often rasterizes them to images on PPTX export. You'll see them as picture elements rather than shape lists — that's expected; just place the image.
