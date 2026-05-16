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

This is why all three pieces (`vite.config.ts`, `components/Diagram.vue`, `_shared/diagram/Diagram.vue`) must stay in sync — breaking one breaks diagram rendering across every talk. If you change the shared component's API, update the SKILL.md docs that describe the spec.

The Diagram spec uses `revealAt: N` / `reveal: { from, to }` for click-driven build-ups; these translate internally to Slidev's `v-click`. Outside `<Diagram>`, you write raw `v-click` directives directly on Vue elements — the two have different conventions, including the half-open range trap noted in user memory. The SKILL.md "Direct `v-click` syntax gotchas" table is the authoritative reference.

## The shared `theme-josh` Slidev theme

`_shared/theme-josh/` is a custom Slidev theme consumed by talks via a relative path: `theme: ../_shared/theme-josh` in `slides.md` headmatter. It works because the talk's `vite.config.ts` extends `server.fs.allow` to the repo root (same plumbing as `<Diagram>`).

Structure:
- `package.json` — `slidev-theme` keywords, `colorSchema: 'dark'`, font + `themeConfig` defaults.
- `layouts/` — `default` (vertically centered), `cover`, `section`, `center`, `day` (course-lecture opener: course/event mark, big question in the H1 slot, discussion prompt in the `::discussion::` named slot).
- `styles/layout.css` + `code.css` — design tokens (`--josh-bg`, `--josh-fg`, `--josh-accent`, etc.), type scale, base layout. `.slidev-layout` sets `display: flex; flex-direction: column; justify-content: center; height: 100%` so content centers vertically by default.
- `components/Hi.vue` — inline keyword highlight: `<Hi>word</Hi>` (or `variant="solid|box"`).
- `global-top.vue` — the persistent footer (course/event left, page number + signature mark right).

Talks configure the footer via headmatter:

```yaml
themeConfig:
  initials: jdl
  course: PSYC 101
  event: Lecture 1
  date: Spring 2026
```

Per-slide `footer: false` (or `footer: "custom text"`) overrides; cover/section/end layouts auto-hide it.

Non-obvious gotchas:

- **The footer lives in `global-top.vue`, not `global-bottom.vue`.** Slidev's `<GlobalBottom />` renders *before* `<SlidesShow>` in the DOM (stacking behind slides), so anything in `global-bottom.vue` gets covered when slides have an opaque background — you see it flash through during fade transitions, then disappear. `global-top.vue` renders after slides so it stacks on top. The name describes z-order, not screen position.
- **Always set `layout: cover` explicitly on slide 1.** Slidev's `currentLayout` composable falls back to `'cover'` for slide 1 when `meta.layout` is missing, but that fallback depends on `currentSlideNo` which races with `currentSlideRoute` during navigation. Explicit layout eliminates the race and the resulting footer flicker.
- **Don't read layout via `nav.currentLayout`** in components — use `nav.currentSlideRoute.value?.meta?.layout` directly, for the same race reason.

## prep.py architecture

`prep.py` is stdlib-only and parses PPTX XML directly (no `python-pptx` dependency). Two things worth knowing before editing:

- **Group transforms**: shapes nested in `p:grpSp` need transform composition (`_group_transform` + `_compose_transform` + `_walk_shapes`) to map local coords to slide-absolute coords. All shape/connector geometry in the analysis is slide-absolute — never raw local.
- **Diff blocks**: each slide's `_analysis.md` entry ends with a `**Diff from slide N**` block listing what changed since the previous slide. The skill's click-collapsing logic depends on these diffs being accurate, so changes to shape comparison need to preserve diff fidelity.

## Commit style

Look at `git log --oneline` before writing a message. Recent commits use short imperative subjects (`Ignore __pycache__/`, `Snap PPTX connectors to shape edges and match source routing`) with optional one-paragraph bodies explaining *why*, not what. Add the `Co-Authored-By` trailer for Claude commits.
