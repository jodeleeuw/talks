# slidev-addon-cogsci-demos

Interactive teaching demos shared by the talks in this repo. It's a local
Slidev addon: a talk turns it on with a path in its headmatter, and the
components are then available on every slide with no imports.

```yaml
addons:
  - '@/../../../../addons/cogsci-demos'   # path from the talk's folder to this one
```

`@/` means "relative to the talk's folder", so count one `../` per level
between the talk and the repo root (`talks/classes/cogs319/04-…` is four).
Edits here show up live in `pnpm dev`; there's nothing to install.

## `<TuringMachine>`

```md
<TuringMachine tape="__yxxyx__" :head="3" start="0"
  :rules="[['0', 'x', 'x', 'R', '0'], ['0', 'y', 'x', 'R', 'HALT']]" />
```

- `rules`: `[state, read, write, move, next]` (or objects with those keys);
  move is `L`, `R` or `N`. `_` is blank. It halts on entering a `halt` state
  (default `['HALT']`) or when no rule matches.
- With no `step` prop it has Reset / Back / Step / Run buttons.
  `:step="$clicks"` steps it on slide clicks instead (set `clicks:` on the slide).
- `:reveal="$clicks"` with `:step="Math.max(0, $clicks - 4)"` builds it up
  first: empty tape, symbols, head, state, rules.
- `view`: `diagram` (default), `table`, `both`, `none`.
  `labels`: `short` (`x → x, R`, default) or `long` (`Read x; Write x; Move R;`).
- `editable` adds a box for typing a new starting tape. `cells` sets how many
  cells show (default 9); the window scrolls with the head.

## `<HodgkinHuxley>`

A live Hodgkin–Huxley neuron (1952 squid-axon parameters, rest at −65 mV).
"Stimulate" sends a 1 ms pulse whose size the slider sets (threshold is about
7 µA/cm²); "steady current" fires repeatedly above about 6.3 µA/cm². "Show
gates" adds m, h and n. Props: `window` (ms shown, 100), `speed` (simulated
ms per second, 25), `current`, `pulse`, `gates`. It only runs while on screen.

## `<PerceptronPlayground>`

One perceptron unit with sliders for w₁, w₂ and b over the four binary input
patterns. `problem`: `and`, `or` or `xor` (default); `problems` lists the
buttons shown. "Try every setting" sweeps about 15,000 weight settings and
reports the best score (3 of 4 for XOR); "Train" runs the perceptron learning
rule, which converges on AND and OR and cycles on XOR.
