# talks
Talks, lecture slides, etc.

## Creating a new talk

Each talk lives in its own directory. Run the scaffolder from the repo root:

```bash
npm run new
```

It prompts for a parent folder (repo root, `workshops/`, `tmp_talks/`, or a new one), then a name. It copies `template/`, runs `npm install`, opens the folder in VS Code (if `code` is on `PATH`), and starts the dev server.

To do it by hand instead:

```bash
cp -r template/ my-talk-name
cd my-talk-name
npm install
npm run dev
```

This project uses [Slidev](https://sli.dev) — a Markdown-based presentation tool for developers.

## Commands

| Command | Description |
| ------- | ----------- |
| `npm run dev` | Start the development server |
| `npm run build` | Build the slides as a static site |
| `npm run export` | Export the slides to PDF |
