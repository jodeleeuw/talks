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

## Shared pieces

`lib/` holds plain JavaScript the components share: `iam.js` (the
interactive activation model, its 14-segment font and its lexicon in
`iam-lexicon.js`), `mlp.js` (a tiny two-layer network trained with Adam),
and `plot.js` (scales, paths, a seeded random generator). `styles/index.css`
styles the buttons, sliders and axes every demo uses (`.cd-*` classes) and
loads on every slide of a talk that turns the addon on.

Most demos take `:step="$clicks"` to drive a build from slide clicks and
`:controls="false"` to hide their buttons; without `step` they run from their
own buttons.

## `<FlashTrial>`

A tachistoscope: fixation, a stimulus for a few tens of ms, then a mask and a
question. `trials`: `[{ stimulus, mask, cue, question }]` (`cue` boxes a
position in the mask). `duration` (ms, 60), `fixation` (ms, 700). With `step`,
click n plays trial n; otherwise a Next trial button steps through.

## `<InteractiveActivation>`

A running McClelland & Rumelhart (1981) interactive activation model: 14
line-segment features per position, 26 letters per position and 1,179
four-letter words, with the paper's parameters. Click segments to hide them,
type any four letters, and run it; two plots show letter activations in a
chosen position and the most active words. Presets cover the word
superiority effect (WORK, VRMK, K alone, each flashed then masked), the
"K or R?" ambiguous letter and the pseudoword MAVE. Props: `word`, `hide`
(`{ position: [segments] }`), `probe`, `mask` (cycles before the #### mask,
0 = none), `cycles`, `presets`.

## `<ActivationUnit>`

One interactive-activation unit's activation over time under steady
excitation and inhibition, with sliders for both inputs, decay and resting
level, the equilibrium line, and an option to switch the input off halfway.
Props: `excitation`, `inhibition`, `decay`, `rest`.

## `<DeltaRule>`

A one-layer pattern associator drawn as in the COGS 319 slides, trained with
Δw = learningRate × (desired − output) × input. `inputs`, `desired` (`null`
hides that row), `weights` (`[output][input]`, default zeros), `lr`,
`showOutputs`, `showLr`. `:step="n"` shows the weights after n updates and
highlights the cells that changed. Clicking an input or desired value flips
its sign.

## `<BackpropChain>`

Backprop through a three-weight chain, `a = i0·w0, b = a·w1, y′ = b·w2,
L = (y − y′)²`. `step` reveals the gradients in the order the slides derive
them (dL/dy′, dL/dw2, dy′/db, dL/dw1, db/da, dL/dw0). `values` (false shows
names only), `blanks` (shows `= ?` for unrevealed gradients), `wiggle` (nudges
w0 to show the finite-difference loss). Controls compare finite differences
with backprop for several h, and take gradient steps with a loss sparkline.
Props `i0`, `w`, `y` set the problem.

## `<GradientDescent>`

Gradient descent on a one-weight loss curve with a shallow local minimum and a
deeper global one. `start`, `lr`, `step` (hops), `curve` (false hides the
curve, showing only what the learner knows), `tangent`, `hint`. Clicking the
plot sets the starting weight.

## `<TrainingBatches>`

The training loop: a strip of training examples, the current batch lit, and
x → network → y′ → loss ← y with a backprop arrow. `n` (examples, 13),
`batchSize`, `step`, `phases` (two steps per batch: forward, then backprop),
`loop` (diagram), `controls` (batch size 1 / 3 / all, Step, Run). Shows the
epoch, batch and backprop count.

## `<OverfitPlayground>`

A 2–H–1 network learning a curved boundary from a few noisy points, with the
decision field, its boundary, and training and validation loss curves (a
circle marks where early stopping would stop). Sliders for hidden units,
weight decay and training points; `showNew` draws validation points. Props:
`hidden`, `points`, `decay`, `epochs`, `lr`, `seed`, `autoplay`.

## `<PolynomialFit>`

The bias–variance tradeoff with polynomial regression on noisy samples of a
wavy curve. `degree`, `samples` (how many fresh samples to fit and overlay),
`ridge` (L2 penalty), `showPoints`, `showFit`, `equation`. Controls add New
sample, Overlay samples, and Error by degree (training vs new-data error
averaged over 30 samples).
