# talks
Talks, lecture slides, etc.

## Prerequisites

This repo uses [**pnpm**](https://pnpm.io) so that every talk shares one global, content-addressable
package store instead of each carrying its own ~450 MB copy of Slidev's dependencies. Talks stay
self-contained — each has its own `node_modules` — but identical packages are hard-linked from the
store, so dozens of talks cost roughly one talk's worth of disk.

pnpm is managed via [Corepack](https://nodejs.org/api/corepack.html), which ships with Node. The
pinned version lives in each `package.json`'s `packageManager` field, so a one-time enable is all
you need:

```bash
corepack enable pnpm   # run once per machine / Node version
```

Requires Node 20+ (Node 24 recommended; older Node trips the Corepack/pnpm 11 loader).

## Creating a new talk

Each talk lives in its own directory. Run the scaffolder from the repo root:

```bash
pnpm new
```

It prompts for a parent folder (repo root, `workshops/`, `tmp_talks/`, or a new one), then a name. It copies `template/`, runs `pnpm install`, opens the folder in VS Code (if `code` is on `PATH`), and starts the dev server.

To do it by hand instead:

```bash
cp -r template/ my-talk-name
cd my-talk-name
pnpm install
pnpm dev
```

This project uses [Slidev](https://sli.dev) — a Markdown-based presentation tool for developers.

## Commands

| Command | Description |
| ------- | ----------- |
| `pnpm dev` | Start the development server |
| `pnpm build` | Build the slides as a static site |
| `pnpm export` | Export the slides to PDF |
