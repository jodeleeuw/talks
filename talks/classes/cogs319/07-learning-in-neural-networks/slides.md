---
theme: fenbrook
title: Learning in Neural Networks
info: |
  ## Learning in Neural Networks
  COGS 319: the delta rule, backpropagation and gradient descent.
transition: fade
addons:
  - '@/../../../../addons/cogsci-demos'
themeConfig:
  course: COGS 319
  event: Learning in Neural Networks
layout: cover
---

# Learning in Neural Networks

::speaker::
Josh de Leeuw

::event::
COGS 319 · Spring 2027

---
layout: panel
---

## A model neuron for deep learning

<NeuronDiagram :activation="['f(X)']" output="f(X)" />

---

```python
# python implementation of one neuron
inputs = np.array([5, 3, -1])
weights = np.array([-1, -2, -2])
bias = 4
sum = np.dot(inputs, weights) + bias
output = activation_function(sum)
```

<style scoped>
.slidev-code { font-size: 1.25rem !important; line-height: 2 !important; }
</style>

---
layout: panel
clicks: 1
---

## What are the outputs?

<DeltaRule
  :weights="[[1, .5, 1, 1], [-1, -1, .5, .5], [1, 0, 1, -1], [.5, .5, 1, -1]]"
  :desired="null"
  :show-outputs="$clicks >= 1"
  :controls="false"
  :show-lr="false"
/>

<!--
Each output is the weighted sum of the four inputs. Click to reveal: −.5, −3, 1, 1.
-->

---
layout: panel
clicks: 1
---

## The Delta Rule

<p class="rule">Δw<sub>ij</sub> = learningRate × (desired<sub>j</sub> − output<sub>j</sub>) × input<sub>i</sub></p>

<DeltaRule :desired="[1, -1, -1, 1]" :step="$clicks" :controls="false" />

<p class="ask" v-if="$clicks === 0">Calculate these new weights</p>

<style scoped>
.rule { font-size: 1.25rem; margin: 0; }
.ask { margin: 0; color: var(--fenbrook-accent); }
</style>

<!--
All the weights start at 0, so every output is 0. Have the class compute the new weights before clicking. The original slide filled in only the first output's weights (.25, .25, −.25, −.25); the click here updates all four outputs, and the highlighted cells show what moved.
-->

---
layout: panel
---

## Try it

<DeltaRule :desired="[1, -1, -1, 1]" />

<!--
"Update" applies the delta rule once to every weight; the highlighted cells are the ones that just changed. Click an input or a desired value to flip its sign and start over. With these inputs the network learns the pattern in a couple of updates; slide the learning rate up past 0.5 and it overshoots.
-->

---

## Where does the delta rule come from?

<p class="rule">Δw<sub>ij</sub> = learningRate × (desired<sub>j</sub> − output<sub>j</sub>) × input<sub>i</sub></p>

<div class="steps">
  <p v-click>Error, difference between what you want and what you got: <b>(desired<sub>j</sub> − output<sub>j</sub>)</b></p>
  <p v-click>But, errors matter less when the input is small, and more when the input is large: <b>(desired<sub>j</sub> − output<sub>j</sub>) × input<sub>i</sub></b></p>
  <p v-click>Many contributions to the final activation, so we don't want to change too fast in response to any one input: <b>learningRate × (desired<sub>j</sub> − output<sub>j</sub>) × input<sub>i</sub></b></p>
</div>

<style scoped>
.rule { font-size: 1.25rem; }
.steps { display: flex; flex-direction: column; gap: 1rem; margin-top: 1rem; }
.steps p { margin: 0; }
.steps b { color: var(--fenbrook-accent); font-weight: 600; white-space: nowrap; }
</style>

---
layout: two-cols-header
cols: left-wide
clicks: 4
---

## The Delta Rule. An alternative interpretation.

::left::

<DeltaRule
  :inputs="[1, 1, -1, -1]"
  :desired="[1]"
  :weights="[[$clicks >= 4 ? 0.1 : 0, 0, 0, 0]]"
  :controls="false"
/>

::right::

<div class="side">
  <p>If we wiggle a weight a little bit, how does the error change?</p>
  <div v-if="[1, 2].includes($clicks)" class="frac">
    <span>{{ $clicks === 1 ? 'Value after wiggle − value before wiggle' : 'f(x + h) − f(x)' }}</span>
    <span class="bar" />
    <span>{{ $clicks === 1 ? 'Amount of wiggle' : 'h' }}</span>
  </div>
  <template v-if="$clicks === 3">
    <p>Find the derivative of the error with respect to a weight.</p>
    <p>Move the weight by some small amount to reduce the error.</p>
  </template>
  <div v-if="$clicks >= 4" class="calc">
    <p>h = 0.1</p>
    <p>f(x+h) = 0.9</p>
    <p>f(x) = 1</p>
    <p class="hit">[f(x+h) − f(x)] / h = −1</p>
  </div>
</div>

<style scoped>
.side { display: flex; flex-direction: column; gap: 1rem; font-size: 1.05rem; }
.side p { margin: 0; }
.frac { display: inline-flex; flex-direction: column; align-items: center; gap: 0.35rem; align-self: flex-start; }
.frac .bar { width: 100%; border-top: 2px solid var(--fenbrook-fg); }
.calc { display: flex; flex-direction: column; gap: 0.35rem; font-family: 'JetBrains Mono', monospace; }
.hit { color: var(--fenbrook-accent); }
</style>

<!--
Here f is the error, desired − output. With every weight at 0 the output is 0 and the error is 1. Wiggling the first weight up by h = 0.1 makes the output 0.1 and the error 0.9, so the error changes by −1 per unit of weight.
-->

---
layout: two-cols-header
cols: left-wide
clicks: 3
---

## The Delta Rule. An alternative interpretation.

::left::

<DeltaRule
  :inputs="[1, 1, -1, -1]"
  :desired="[1]"
  :weights="[[$clicks >= 3 ? -0.5 : 0, 0, 0, 0]]"
  :controls="false"
/>

::right::

<div class="side">
  <p>Error = Desired − y′</p>
  <p>y′ = Input1 × Weight1 + …</p>
  <p class="hit">dError / dWeight1 = {{ ['?', '−Input1', '−1', '−1'][$clicks] }}</p>
</div>

<style scoped>
.side { display: flex; flex-direction: column; gap: 0.8rem; font-size: 1.15rem; font-family: 'JetBrains Mono', monospace; }
.side p { margin: 0; }
.hit { color: var(--fenbrook-accent); }
</style>

<!--
The last click shows Weight1 at −0.5, as in the original slides. Note for Josh: with the delta rule's sign (Δw = lr × (desired − output) × input = 0.25 × 1 × 1) this weight would move to +0.25, not −0.5.
-->

---
layout: panel
clicks: 2
---

## Backpropagation

<p class="lead">{{ ['How does the error change when we adjust any particular weight?', 'We could just wiggle each weight individually.', 'Or we can work backwards from the output.'][$clicks] }}</p>

<BackpropNet :step="$clicks" />

<style scoped>
.lead { margin: 0; font-size: 1.15rem; }
</style>

<!--
Wiggling each weight one at a time is the method of finite differences: it works, but it takes one extra pass through the network per weight. Backprop gets every gradient in one backward pass.
-->

---
layout: panel
clicks: 3
---

## Backpropagation

<p class="lead">How does the loss change when we adjust w0?</p>

<BackpropChain
  :values="$clicks >= 1"
  :wiggle="$clicks >= 2 ? 0.1 : 0"
  :step="0"
  :controls="false"
/>

<p v-if="$clicks >= 3" class="fd">( f(x+h) − f(x) ) / h = (11.56 − 9) / 0.1 = 25.6</p>

<style scoped>
.lead { margin: 0; font-size: 1.15rem; }
.fd { margin: 0; font-family: 'JetBrains Mono', monospace; color: var(--fenbrook-accent); }
</style>

<!--
Click 1 fills in the numbers (i0 = 2, w0 = .5, w1 = −1, w2 = 2, target y = 1, so y′ = −2 and L = 9). Click 2 wiggles w0 up by 0.1: the loss goes to 11.56. Click 3 is the finite-difference slope.
-->

---
layout: panel
clicks: 7
---

## Backpropagation

<BackpropChain :step="Math.min($clicks, 6)" :controls="false" />

<div class="deriv">
  <template v-if="$clicks <= 1">
    <p>Let's start with how the loss changes as y′ changes:</p>
    <p v-if="$clicks === 1" class="m">L = (1 − y′)² = 1 − 2y′ + y′² &nbsp;→&nbsp; dL/dy′ = 2y′ − 2 = −4 − 2 = −6</p>
    <p v-else class="m">L = (1 − y′)²</p>
  </template>
  <template v-else-if="$clicks === 2">
    <p>dL/dw2 = (dL/dy′)(dy′/dw2). <b>This is the chain rule.</b></p>
    <p class="m">dy′/dw2 = −1 &nbsp;→&nbsp; dL/dw2 = −6 × −1 = 6</p>
  </template>
  <template v-else-if="$clicks <= 4">
    <p>Now, what about w1? &nbsp;dL/dw1 = (dL/dy′)(dy′/db)(db/dw1)</p>
    <p class="m">{{ $clicks === 3 ? 'dy′/db = 2' : 'dL/dw1 = −6 × 2 × 1 = −12' }}</p>
  </template>
  <template v-else-if="$clicks <= 6">
    <p>Finally, what about w0? &nbsp;dL/dw0 = (dL/dy′)(dy′/db)(db/da)(da/dw0)</p>
    <p class="m">{{ $clicks === 5 ? 'db/da = −1' : 'dL/dw0 = −6 × 2 × −1 × 2 = 24' }}</p>
  </template>
  <template v-else>
    <p>Great! So we know the gradients for all the weights.</p>
    <p><b>How much should we change each weight?</b></p>
  </template>
</div>

<style scoped>
.deriv { display: flex; flex-direction: column; gap: 0.4rem; min-height: 4.5rem; }
.deriv p { margin: 0; }
.m { font-family: 'JetBrains Mono', monospace; color: var(--fenbrook-accent); }
</style>

<!--
Each click reveals the next gradient on the network and its step of the chain rule.

dL/dw0 = 24 doesn't match what we got with finite differences (25.6), but we chose a relatively big h. If h = 0.01, then we get 24.16 with finite differences.
-->

---
layout: panel
---

## Check it yourself

<BackpropChain :step="6" />

<!--
"Wiggle w0" compares the finite-difference slope with the backprop answer for h = 0.1, 0.01 and 0.001; it closes in on 24 as h shrinks. "Gradient step" moves every weight downhill by learning rate × gradient and plots the loss, which previews the next slides.
-->

---
layout: panel
clicks: 3
---

<GradientDescent
  :curve="$clicks >= 3"
  :tangent="$clicks >= 1"
  :step="$clicks >= 2 ? 1 : 0"
  :hint="$clicks === 2 ? 'In most backprop variants the learning rate controls how big the hop is.' : ''"
  :controls="false"
/>

<!--
All the network knows is where it is (the dot) and the slope there (the tangent, click 1). It hops downhill (click 2); the learning rate sets how big the hop is. Click 3 reveals the whole loss curve, which the network never gets to see.
-->

---
layout: panel
---

## Learning rate

<GradientDescent />

<!--
Drag the learning rate and press Run. Small rates settle into the shallow dip on the left; big ones hop over the hump into the deeper valley, and very big ones bounce around. Click on the plot to start from a different weight.
-->

---
layout: center
---

<figure class="chollet">
  <BaseImg src="images/chollet-weights.png" alt="Diagram from Chollet: input X passes through layers whose weights are the parameters; the network produces predictions Y prime. Goal: finding the right values for these weights." />
  <figcaption>Chollet, F. Deep Learning with Python, 2nd ed.</figcaption>
</figure>

<style scoped>
.chollet { margin: 0 auto; display: flex; flex-direction: column; align-items: center; gap: 0.8rem; }
.chollet img { background: #fff; max-height: 400px; max-width: 100%; }
.chollet figcaption { font-size: 0.85rem; color: var(--fenbrook-muted); }
</style>

---
layout: center
---

<figure class="chollet">
  <BaseImg src="images/chollet-loss.png" alt="Diagram from Chollet: the predictions Y prime and the true targets Y feed a loss function, which produces a loss score." />
  <figcaption>Chollet, F. Deep Learning with Python, 2nd ed.</figcaption>
</figure>

<style scoped>
.chollet { margin: 0 auto; display: flex; flex-direction: column; align-items: center; gap: 0.8rem; }
.chollet img { background: #fff; max-height: 400px; max-width: 100%; }
.chollet figcaption { font-size: 0.85rem; color: var(--fenbrook-muted); }
</style>

---
layout: center
---

<figure class="chollet">
  <BaseImg src="images/chollet-optimizer.png" alt="Diagram from Chollet: the loss score is used as a feedback signal by an optimizer, which makes weight updates to the layers." />
  <figcaption>Chollet, F. Deep Learning with Python, 2nd ed.</figcaption>
</figure>

<style scoped>
.chollet { margin: 0 auto; display: flex; flex-direction: column; align-items: center; gap: 0.8rem; }
.chollet img { background: #fff; max-height: 400px; max-width: 100%; }
.chollet figcaption { font-size: 0.85rem; color: var(--fenbrook-muted); }
</style>

---
layout: panel
---

## Backpropagation

<BackpropChain :step="6" :controls="false" />

<div class="q">
  <p>Why is training a neural network harder than this?</p>
  <p>What have we left out?</p>
</div>

<style scoped>
.q p { margin: 0.2rem 0; font-size: 1.15rem; }
</style>

<!--
- No nonlinearities here, derivatives are simple.
- Input / output changes, so constantly shifting target. Have to figure out how to get a solution that works across input/output targets.
- As networks get deeper and there's more non-linearity, vanishing gradients.
- Optimizing parameters can be challenging. Picking/adjusting a learning rate.
-->

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
