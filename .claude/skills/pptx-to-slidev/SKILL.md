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

1. Copy `template/` to `<repo>/<output>/`. **Fails if the dir already exists** — ask the user before clobbering.
2. Extract every image from `ppt/media/` into the new dir (co-located with `slides.md`, **not** in `public/`).
3. Parse each slide and write `_analysis.json` + `_analysis.md` into the new dir.

After the script runs, **read `_analysis.md`** end-to-end, then design and write `slides.md`. Delete `_analysis.json` and `_analysis.md` once you're done with them.

## Writing slides.md from the analysis

### Workflow

1. Read `_analysis.md` end to end. Note the deck size — it's the SVG `viewBox` you'll use for any diagram slides.
2. Scan for **adjacent slides with overlapping content** — these are nearly always build-up animations (progressive bullets, diagram states, highlight passes). Plan to collapse them into a single Slidev slide with click reveals.
3. Decide each slide's Slidev layout (see table below).
4. Replace the template's placeholder `slides.md` with your converted deck.
5. Verify the build: `cd <talk-dir> && npm install && npx slidev build`. If it succeeds, `rm -rf dist/`. If it fails, read the error, fix, rebuild. Note that `build` can pass while the dev server still warns on diagram slides — see the indent/blank-line gotcha below.
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

Google Slides and PowerPoint don't have native click reveals, so authors duplicate a slide multiple times with one extra element each — a stack of slides 3, 4, 5, 6 with identical text but different highlights, or slides 8, 9, 10, 11 that build a diagram one piece at a time. The analysis output makes these obvious because the text/shape lists overlap heavily across consecutive slides.

Three patterns to watch for in `_analysis.md`:

1. **Progressive bullets / shapes** — adjacent slides where each one adds elements. Collapse with `<v-clicks>` or `v-click="N"`.
2. **Diagram build-ups** — adjacent slides where new shapes appear over a constant base. Collapse using `<g v-click="N">` groups inside one SVG.
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

### Recreating diagrams (shapes + connectors)

When the analysis lists multiple shapes and connectors with positions, the slide is a diagram. To preserve geometry without sacrificing themeability:

1. Use the deck size from the analysis header as the SVG `viewBox`: `viewBox="0 0 <w> <h>"`. This makes the shape positions in the analysis usable directly.
2. Position outer boxes as absolutely-placed `<div>`s using **percentages** of that coordinate system (e.g. an x of 620 px on a 960-wide deck → `left: 64.6%`). Percentages mean the diagram scales with the slide and the source coords stay readable.
3. Draw connectors as SVG `<path>` elements inside a single `<svg>` overlay layered over the boxes. The connector positions in the analysis are approximate end-points — you'll usually need to nudge them, and a curved `Q`/`C` path looks better than a straight line.
4. Use **`stroke="currentColor"`** on SVG strokes and **`background: var(--slidev-theme-bg, transparent)`** on box fills. A theme can then recolor the whole diagram by changing the text color and one CSS variable.
5. Put structural CSS in a `<style scoped>` block in the slide. Use **semantic class names** the theme can target — `diagram-box`, `box-data`, `box-theory`, `datapoint`, `diagram-label`, etc. — not utility-name-only classes like `red-box`.
6. Wrap each progressive-reveal group in `<g v-click="N">` (or a div, for non-SVG elements). The `v-click` directive works inside SVG without ceremony.

### Gotcha: blank lines + indentation inside HTML/SVG blocks

Slidev passes slide content through a markdown parser before Vue compiles the result. Inside an HTML block (`<div>`, `<svg>`, `<g>`, …) the parser treats a blank line as a paragraph break and will then re-enter markdown mode for what follows. If the next line is indented **4+ spaces** (the natural indent for a nested SVG child), markdown wraps it in `<pre><code>` — which Vue then emits as an "Element is missing end tag" build error or a `<pre> cannot be child of <svg>` dev-server warning.

The warning is visible only when running the dev server (`npm run dev`); `npx slidev build` can succeed in spite of it. Always do a quick dev-server pass on diagram-heavy slides before declaring victory.

Two fixes (either works):

- **Flatten:** strip the leading indentation on SVG/HTML children so no line starts with 4+ spaces, and remove blank lines between siblings inside the block.
- **Keep readable indent, lose the blank lines:** indented children are fine *as long as no blank line precedes them*. The blank line is what re-arms the markdown code-block rule.

Prefer flattening for big diagrams — it's robust and the geometry doesn't get less readable since the coordinates are right there in the attributes.

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
