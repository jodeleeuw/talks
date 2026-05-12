# talks
Talks, lecture slides, etc.

## Creating a new talk

Each talk lives in its own directory. To start a new one, copy the `template/` directory and rename it:

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
