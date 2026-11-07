---
theme: fenbrook
title: Training, Overfitting, Regularization
info: |
  ## Training, Overfitting, Regularization
  COGS 319: the training loop, epochs and batches, overfitting, and the
  bias–variance tradeoff.
transition: fade
addons:
  - '@/../../../../addons/cogsci-demos'
themeConfig:
  course: COGS 319
  event: Training, Overfitting, Regularization
layout: cover
---

# Training, Overfitting, Regularization

::speaker::
Josh de Leeuw

::event::
COGS 319 · Spring 2027

---
layout: panel
clicks: 1
---

## Backpropagation

<BackpropChain :i0="-1" :w="[-2, 0.5, 1]" :y="-1" blanks :step="$clicks >= 1 ? 6 : 0" :controls="false" />

<p v-if="$clicks === 0" class="m">L = (−1 − y′)² = 1 + 2y′ + y′² &nbsp;→&nbsp; dL/dy′ = ?</p>

<style scoped>
.m { margin: 0; font-family: 'JetBrains Mono', monospace; }
</style>

<!--
Solve this one. Click for the answers: dL/dy′ = 4, dL/dw2 = 4, dy′/db = 1, dL/dw1 = 8, db/da = 0.5, dL/dw0 = −2.
-->

---
layout: center
---

# Reviewing the standard workflow:

---
layout: two-cols-header
cols: right-wide
clicks: 1
---

::left::

<div v-click="1">

```python
model = keras.Model(
  inputs = ...,
  outputs = ...
)
```

</div>

::right::

<figure class="chollet">
  <BaseImg src="images/chollet-weights.png" alt="Diagram from Chollet: input X passes through layers whose weights are the parameters; the network produces predictions Y prime. Goal: finding the right values for these weights." />
  <figcaption>Chollet, F. Deep Learning with Python, 2nd ed.</figcaption>
</figure>

<style scoped>
.chollet { margin: 0; display: flex; flex-direction: column; align-items: center; gap: 0.6rem; }
.chollet img { background: #fff; max-height: 380px; max-width: 100%; }
.chollet figcaption { font-size: 0.85rem; color: var(--fenbrook-muted); }
</style>

---
layout: two-cols-header
cols: right-wide
clicks: 1
---

::left::

```python
model = keras.Model(
  inputs = ...,
  outputs = ...
)
```

<div v-click="1">

```python
model.compile(
  loss = keras.losses.MeanSquaredError(),
  optimizer = keras.optimizers.SGD()
)
```

</div>

::right::

<figure class="chollet">
  <BaseImg src="images/chollet-loss.png" alt="Diagram from Chollet: the predictions Y prime and the true targets Y feed a loss function, which produces a loss score." />
  <figcaption>Chollet, F. Deep Learning with Python, 2nd ed.</figcaption>
</figure>

<style scoped>
.chollet { margin: 0; display: flex; flex-direction: column; align-items: center; gap: 0.6rem; }
.chollet img { background: #fff; max-height: 380px; max-width: 100%; }
.chollet figcaption { font-size: 0.85rem; color: var(--fenbrook-muted); }
</style>

---
layout: two-cols-header
cols: right-wide
clicks: 1
---

::left::

```python
model = keras.Model(
  inputs = ...,
  outputs = ...
)
```

```python
model.compile(
  loss = keras.losses.MeanSquaredError(),
  optimizer = keras.optimizers.SGD()
)
```

<div v-click="1">

```python
model.fit(
  x = ...,
  y = ...
)
```

</div>

::right::

<figure class="chollet">
  <BaseImg src="images/chollet-optimizer.png" alt="Diagram from Chollet: the loss score is used as a feedback signal by an optimizer, which makes weight updates to the layers." />
  <figcaption>Chollet, F. Deep Learning with Python, 2nd ed.</figcaption>
</figure>

<style scoped>
.chollet { margin: 0; display: flex; flex-direction: column; align-items: center; gap: 0.6rem; }
.chollet img { background: #fff; max-height: 380px; max-width: 100%; }
.chollet figcaption { font-size: 0.85rem; color: var(--fenbrook-muted); }
</style>

---
layout: panel
clicks: 4
---

## What does the training step entail?

<p class="cap">{{ $clicks === 0 ? 'training data' : 'x = input (e.g., image) · y = target output (e.g., label)' }}</p>

<TrainingBatches :step="$clicks" :batch-size="1" phases :controls="false" />

<style scoped>
.cap { margin: 0; color: var(--fenbrook-fg-soft); }
</style>

<!--
Each box is one training example. Click 1 takes the first example through the network and compares the prediction with the target; click 2 runs backprop. Clicks 3 and 4 do the same for the next example.
-->

---
layout: panel
---

## What does the training step entail?

<p class="cap">Each time through the entire training set is one <b>epoch</b>.</p>

<TrainingBatches :batch-size="1" />

<style scoped>
.cap { margin: 0; }
.cap b { color: var(--fenbrook-accent); }
</style>

<!--
Press Run and let it go past the last example: the epoch counter ticks over and the strip starts again from the left.
-->

---
layout: panel
clicks: 4
---

## What does the training step entail?

<p class="cap">We usually train in batches. There is one execution of backprop per batch.</p>

<TrainingBatches :step="$clicks" :batch-size="3" phases :controls="false" />

<style scoped>
.cap { margin: 0; }
</style>

<!--
Batches of three: the whole batch goes forward, the losses are combined, and backprop runs once for the batch. The batch-size buttons on the previous slide switch between 1, 3 and the whole set.
-->

---
layout: center
---

## We typically train for many epochs.

<p v-click class="big">How do we know when to stop?</p>

<style scoped>
.big { font-size: 1.5rem; color: var(--fenbrook-accent); }
</style>

---
layout: panel
clicks: 1
---

## Overfitting

<LossCurves>
  <span v-if="$clicks >= 1">But what is actually happening?</span>
</LossCurves>

---
layout: panel
clicks: 2
---

## Overfitting

<OverfitPlayground :show-new="$clicks >= 1" />

<p class="cap">{{ ['But what is actually happening?', 'Now what if we get new data?', 'We do a better job on the novel data with less training'][$clicks] }}</p>

<style scoped>
.cap { margin: 0; text-align: center; color: var(--fenbrook-accent); }
</style>

<!--
Replaces the 30-slide green/pink sequence with a live network (2 inputs, 30 hidden units, trained on 20 points, a few of them mislabelled). Press Train and watch the dotted boundary bend around individual points as training loss keeps falling.

Click 1 draws new points from the same source. Validation loss bottoms out early (the circle marks where early stopping would have stopped) and then climbs: we do a better job on the novel data with less training.

The sliders preview the remedies on the "How do we avoid overfitting?" slide: more training points, fewer hidden units, weight decay. Reset after changing them.
-->

---
layout: panel
---

## Overfitting

<LossCurves>
  at some point we start to learn features that are specific to the training data
</LossCurves>

---
layout: center
---

## Stepping outside our neural network bubble for a few minutes…

---
layout: panel
clicks: 5
---

## The bias-variance tradeoff

<PolynomialFit
  :degree="1"
  :equation="$clicks >= 1"
  :show-fit="$clicks >= 2"
  :samples="$clicks >= 4 ? 8 : 1"
  :show-points="$clicks < 4"
  :controls="false"
/>

<p class="verdict">
  <span v-if="$clicks === 3"><b>High bias.</b> (systematic misprediction)</span>
  <span v-if="$clicks >= 5"><b>Low variance.</b> (Difference in models with different samples)</span>
</p>

<style scoped>
.verdict { margin: 0; min-height: 1.6em; text-align: center; }
.verdict b { color: var(--fenbrook-accent); }
</style>

<!--
Points come from a wavy curve plus noise. A straight line (click 2) misses the wiggles the same way every time: high bias. Click 4 fits lines to eight fresh samples; they barely differ: low variance.
-->

---
layout: panel
clicks: 4
---

## The bias-variance tradeoff

<PolynomialFit
  :degree="7"
  :show-fit="$clicks >= 1"
  :samples="$clicks >= 3 ? 8 : 1"
  :show-points="$clicks < 3"
  :controls="false"
/>

<p class="verdict">
  <span v-if="$clicks === 2"><b>Low bias.</b></span>
  <span v-if="$clicks >= 4"><b>High variance.</b> (Difference in models with different samples)</span>
</p>

<style scoped>
.verdict { margin: 0; min-height: 1.6em; text-align: center; }
.verdict b { color: var(--fenbrook-accent); }
</style>

<!--
A degree-7 polynomial follows each sample closely (low bias), but fits to eight fresh samples (click 3) disagree wildly: high variance.

The original slide's "Low bias." label carried "(systematic misprediction)" copied from the high-bias slide; it's left off here.
-->

---
layout: center
clicks: 2
---

<svg viewBox="0 0 760 330" class="bv" role="img" aria-label="As model complexity goes from low to high, bias falls and variance rises">
  <defs>
    <marker id="bv-a" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="#e8e3d8" /></marker>
  </defs>
  <path v-if="$clicks >= 1" d="M40,20 C170,140 260,190 380,200 S640,212 720,214" class="bias" />
  <text v-if="$clicks >= 1" x="80" y="40" class="lb bias-l">bias</text>
  <path v-if="$clicks >= 2" d="M40,222 C200,218 330,214 420,196 S640,100 720,24" class="var" />
  <text v-if="$clicks >= 2" x="690" y="60" class="lb var-l" text-anchor="end">variance</text>
  <line x1="30" y1="250" x2="730" y2="250" class="ax" marker-start="url(#bv-a)" marker-end="url(#bv-a)" />
  <text x="30" y="290" class="lb">Low model complexity</text>
  <text x="730" y="290" class="lb" text-anchor="end">High model complexity</text>
</svg>

<style scoped>
.bv { width: 100%; max-width: 820px; }
.ax { stroke: #e8e3d8; stroke-width: 2.5; }
.lb { fill: #e8e3d8; font-size: 16px; }
.bias { fill: none; stroke: #5b8fd6; stroke-width: 3; }
.var { fill: none; stroke: #e8a33a; stroke-width: 3; }
.bias-l { fill: #5b8fd6; }
.var-l { fill: #e8a33a; }
</style>

---
layout: panel
---

## Try it

<PolynomialFit :degree="3" />

<!--
Drag the degree and press "Overlay samples" to see variance grow. "Error by degree" averages training error and error on new data over 30 samples for every degree: training error keeps falling while error on new data is U-shaped. Ridge λ is L2 regularization; a small amount tames the high-degree fits without lowering the degree.
-->

---

## How do we avoid overfitting?

1. Increase size of training dataset
2. Prevent the model from adapting too much to the training data.
3. Reduce model complexity.

<p v-click class="why">Why do each of these work?</p>

<style scoped>
.why { margin-top: 1.5rem; color: var(--fenbrook-accent); }
</style>

<!--
Each one is a slider on the overfitting demo: training points (1), weight decay (2; early stopping is the other common version), hidden units (3).
-->

---
layout: center
---

## Why is evaluating on validation data not enough?

<p v-click class="q">What do you think a best case evaluation plan would be?</p>

<style scoped>
.q { font-size: 1.3rem; margin-top: 1.5rem; }
</style>
