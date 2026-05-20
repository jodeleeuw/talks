# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repo shape

This repo is a collection of [Slidev](https://sli.dev) talks. Each talk is a self-contained sibling directory at the repo root, scaffolded from `template/`. Talks have no shared `package.json` at the root — every talk has its own dependencies and is installed/built independently:

```bash
cd <talk-dir>
npm install
npm run dev       # dev server at :3030
npm run build     # static SPA into dist/
npm run export    # PDF (requires playwright-chromium)
```

`README.md` documents the manual flow (copy `template/`, rename). The more common path right now is the `pptx-to-slidev` skill — see below.

## The tooling, not the talks

Right now the project is focused on building the PPTX → Slidev pipeline, not on producing keepable decks. Generated talks land in `tmp_talks/` (gitignored), and `*.pptx` source files are gitignored too. Don't be surprised that the repo looks "empty" of talks — that's deliberate. Long-term-usable talks would live at the repo root; throwaway generations live in `tmp_talks/`.

## Skills

Three skills under `.claude/skills/` drive the workflow:

- **`google-slides-export`** — pulls a Google Slides deck (or a whole Drive folder) down to `.pptx` via browser OAuth. Run this first when the user only has a Slides URL.
- **`pptx-to-slidev`** — the main one. `prep.py` scaffolds a new talk dir from `template/`, extracts images, and emits `_analysis.json` + `_analysis.md`. Claude then reads the analysis and hand-writes `slides.md`. Read `.claude/skills/pptx-to-slidev/SKILL.md` end to end before invoking — it documents the click-mapping rules, the `<Diagram>` spec, and several non-obvious gotchas.
- **`slidev`** — general Slidev reference (layouts, components, Vue/Markdown interop).

## The shared `<Diagram>` component

`_shared/diagram/Diagram.vue` is a single SVG-rendering component that every generated talk consumes. The plumbing:

1. Each talk's `template/vite.config.ts` extends `server.fs.allow` to include the **repo root**, so Vite is willing to serve files from `../_shared/`.
2. Each talk's `template/components/Diagram.vue` is a thin wrapper that imports `../../_shared/diagram/Diagram.vue` and re-exports it. Slidev auto-registers anything in `components/`, so `<Diagram>` is available globally on every slide.

This is why all three pieces (`vite.config.ts`, `components/Diagram.vue`, `_shared/diagram/Diagram.vue`) must stay in sync — breaking one breaks diagram rendering across every talk. If you change the shared component's API, update [`_shared/diagram/SPEC.md`](_shared/diagram/SPEC.md) (the authoritative reference) and re-check the PPTX→spec mapping table in `.claude/skills/pptx-to-slidev/SKILL.md`.

The Diagram spec uses `revealAt: N` / `reveal: { from, to }` for click-driven build-ups; these translate internally to Slidev's `v-click`. Outside `<Diagram>`, you write raw `v-click` directives directly on Vue elements — the two have different conventions, including the half-open range trap noted in user memory. The SKILL.md "Direct `v-click` syntax gotchas" table is the authoritative reference.

`<Diagram>` also has a `startAt: Number` prop. The component rewrites every reveal directive on every spec item as if the first `startAt` clicks already happened — `revealAt: 5` with `startAt: 3` becomes effective `revealAt: 2`; `revealAt: 3` becomes always-visible. `textByClick` keys shift too; the most-recent past entry overwrites the click-0 state. Lets one spec be reused across multiple slides without duplicating it — e.g. slide A drives a build-up through state 5, slide B opens at `:start-at="5"` with the build "frozen" and a `revealAt: 6` element appearing on the first click.

The spec also supports an `axes: [...]` field — declarative `{ kind: 'vertical' | 'horizontal', x | y, from, to, label }` chart axes. Renders as a path + a positioned text label, themed via `.axis` / `.axis-<style>` CSS hooks. Skips the fiddle of declaring axes as free-endpoint connectors with `arrow: "none"`.

## The shared `theme-josh` Slidev theme

`_shared/theme-josh/` is a custom Slidev theme consumed by talks via a relative path: `theme: ../_shared/theme-josh` in `slides.md` headmatter. It works because the talk's `vite.config.ts` extends `server.fs.allow` to the repo root (same plumbing as `<Diagram>`).

Structure:
- `package.json` — `slidev-theme` keywords, `colorSchema: 'dark'`, font + `themeConfig` defaults.
- `layouts/` — `default` (vertically centered), `cover`, `section`, `center`, `cover-day` (course-lecture opener: course/event mark, big question in the H1 slot, discussion prompt in the `::discussion::` named slot), `media` (text + dominant media — `::media::` slot accepts `<img>`, `<Youtube>`, `<iframe>`, `<video>`, etc.; props: `side`, `bleed`, `caption`, `captionSide: 'bottom' | 'right' | 'left'`), `aside` (main + sidebar definition; props: `side`, `asideStyle: 'rail' | 'card'` — `'card'` for rounded-border callouts), `quote` (decorative bigmark + ::attribution::), `outro` (closer with optional ::next:: housekeeping), `gallery` (2-6-image grid via named slots `::a::`–`::f::` plus optional `::overlay::` for a centered card; props: `cols`, `fit`, `gap`, `radius`, `bleed`), `image-bg` (full-bleed background image with overlaid text; props: `image`, `align`, `darken`, `position`, `tint`), `image` (full image with optional `caption` and `captionPosition: 'top' | 'bottom'`; use for naked thumbnails or oversized figures), `panel` (top-anchored title + flex body — use whenever a slide has a tall `<DataTable>`, `<Diagram>`, or chart that would push the H1 off-screen under `default`'s vertical-centering; props: `align: 'left' | 'center'`, `gap`), `fact` (impact-stat layout — big serif-italic number/phrase in the H1 slot, supporting caption as h2 or p; props: `source` for a small citation, `align: 'center' | 'left'`), `two-cols-header` (header in the default slot, two columns in `::left::` / `::right::` named slots; props: `cols: 'equal' | 'left-wide' | 'right-wide'`, `gap`).
- `styles/layout.css` + `code.css` — design tokens (`--josh-bg`, `--josh-fg`, `--josh-accent`, etc.), type scale, base layout. `.slidev-layout` sets `display: flex; flex-direction: column; justify-content: center; height: 100%` so content centers vertically by default.
- `components/Hi.vue` — inline keyword highlight: `<Hi>word</Hi>` (or `variant="solid|box"`).
- `components/Quiet.vue` — companion to `<Hi>`. Mutes color + drops opacity so the surrounding sentence fades behind the highlighted keyword: `<Quiet>Environmental</Quiet> <Hi>science</Hi>`. `variant="strike"` adds a line-through.
- `components/DataTable.vue` — styled table for truth tables and small data grids: `<DataTable :headers="['A','B']" :rows="[[0,1],[1,0]]" :highlight-row="1" :highlight-col="0" />`. Monospace by default (`mono="false"` to switch off). `header-rotate="vertical-up" | "vertical-down"` rotates column headers 90° (matches PPTX `vert=270` on co-occurrence-matrix headers).
- `components/Cropped.vue` — wrapper for PPTX cropped pictures. `<Cropped src :crop="{ l, t, r, b }" :aspect="[w, h]" />` fills its parent (gallery cell, media slot) and applies the scale + offset math the analysis prints under `✂ crop l=…% t=…% r=…% b=…%`.
- `components/Sticker.vue` — drag-positioned floating image. `<Sticker id="…" src="./image.png" />` paired with a `dragPos:` block in slide frontmatter (`dragPos: { <id>: "x,y,w,h" }` or `"x,y,w,h,rotation"`). Wraps Slidev's built-in `<v-drag>` in frontmatter-id mode so the markdown body stays clean even when a slide has 10+ images. Double-click any sticker in `npm run dev` to drag/resize/rotate; the editor writes the new pos back to `dragPos[id]`. Props: `frame: 'none' | 'polaroid' | 'shadow'`, `rotate` (fixed decorative tilt). Use for slides with many irregularly-placed images where `gallery`/`media`/`image-bg` don't fit; `prep.py` emits a ready-to-paste `dragPos:` block + `<Sticker>` lines under a `🪧 Sticker candidate` annotation when it spots ≥ 3 free-floating pictures.
- `components/AnnotatedImage.vue` + `Box.vue` / `Label.vue` / `Layer.vue` / `Mask.vue` — overlay primitives for image-substrate slides. `<AnnotatedImage src :viewbox="[w, h]">` provides a source-pixel coord system via Vue provide/inject; the children position absolutely in that space. Sizes itself like an `<img object-fit:contain>` — fills the available parent space without overflowing on either axis; pass `width` / `max-width` / `max-height` (CSS length or px number) for explicit caps. `layout="container"` switches to "fill an externally-sized parent" mode. Each child takes the same reveal API as a Diagram item (`reveal-at`, `reveal: { from, to | until }`, `hide-at`). `<Mask>` is shown by default and primarily uses `hide-at` to lift on click (variants: `'solid'` opaque, `'dim'` translucent darken, `'blur'` frosted glass). Replaces the older `.stage`-div + Diagram-with-overlay recipe for annotated-photo / image-swap slides.
- `global-top.vue` — the persistent footer (course/event left, page number + signature mark right).

Talks configure the footer via headmatter:

```yaml
themeConfig:
  initials: jdl
  course: PSYC 101
  event: Lecture 1
  date: Spring 2026
```

Per-slide `footer: false` (or `footer: "custom text"`) overrides; `cover`, `section`, `end`, `cover-day`, `outro`, `image-bg`, and `gallery` layouts auto-hide it (see the `HIDE_ON` set in `global-top.vue`). `panel` keeps the footer (it's a content layout).

Non-obvious gotchas:

- **The footer lives in `global-top.vue`, not `global-bottom.vue`.** Slidev's `<GlobalBottom />` renders *before* `<SlidesShow>` in the DOM (stacking behind slides), so anything in `global-bottom.vue` gets covered when slides have an opaque background — you see it flash through during fade transitions, then disappear. `global-top.vue` renders after slides so it stacks on top. The name describes z-order, not screen position.
- **Always set `layout: cover` explicitly on slide 1.** Slidev's `currentLayout` composable falls back to `'cover'` for slide 1 when `meta.layout` is missing, but that fallback depends on `currentSlideNo` which races with `currentSlideRoute` during navigation. Explicit layout eliminates the race and the resulting footer flicker.
- **UnoCSS preflight strips `ol`/`ul` markers globally.** The `default`, `panel`, and `center` layouts each re-assert `list-style: decimal | disc; padding-left: 1.5rem` via scoped `:deep(ol)` / `:deep(ul)` rules so plain markdown numbered/bulleted lists render with visible markers. The `aside` and `outro` layouts deliberately use `list-style: none` with their own `::before` arrow markers and win at equal specificity inside their own components. If you add a new layout, copy the list-fix block from `default.vue`.
- **Don't read layout via `nav.currentLayout`** in components — use `nav.currentSlideRoute.value?.meta?.layout` directly, for the same race reason.

## prep.py architecture

`prep.py` is stdlib-only and parses PPTX XML directly (no `python-pptx` dependency). Two things worth knowing before editing:

- **Group transforms**: shapes nested in `p:grpSp` need transform composition (`_group_transform` + `_compose_transform` + `_walk_shapes`) to map local coords to slide-absolute coords. All shape/connector geometry in the analysis is slide-absolute — never raw local.
- **Diff blocks**: each slide's `_analysis.md` entry ends with a `**Diff from slide N**` block listing what changed since the previous slide. The skill's click-collapsing logic depends on these diffs being accurate, so changes to shape comparison need to preserve diff fidelity.

## Commit style

Look at `git log --oneline` before writing a message. Recent commits use short imperative subjects (`Ignore __pycache__/`, `Snap PPTX connectors to shape edges and match source routing`) with optional one-paragraph bodies explaining *why*, not what. Add the `Co-Authored-By` trailer for Claude commits.
