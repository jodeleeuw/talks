---
theme: fenbrook
title: Origins of Neural Networks
info: |
  ## Origins of Neural Networks
  COGS 319: from Turing machines and McCulloch & Pitts neurons to
  perceptrons, multi-layer networks, and the past-tense debate.
transition: fade
addons:
  - '@/../../../../addons/cogsci-demos'
themeConfig:
  course: COGS 319
  event: Origins of Neural Networks
layout: cover
---

# Origins of Neural Networks

::speaker::
Josh de Leeuw

::event::
COGS 319 · Spring 2027

---
layout: center
width: 100%
---

<BaseImg class="hero" src="images/neuron.png" alt="Fluorescence micrograph of a single neuron: a bright green cell body with branching dendrites dotted in magenta, on a black background." />

<style scoped>
.hero { height: 430px; margin: 0 auto; }
</style>

---
layout: center
---

# Is it possible to compute like a neuron?

---

## Problem: What is computable?

What kinds of problems can be computed and what kinds cannot?

What kinds of problems could we *never* hope to solve by building a machine (or writing down a finite set of steps)?

---

## An uncomputable procedure.

1. Start with a number X.
2. Divide it by 2.
3. Repeat step 2 until the number is equal to 0.
4. Report how many repetitions of Step 2 were needed.

---
layout: center
width: 24ch
---

## How can we take any possible procedure and check whether it is computable?

---
layout: media
---

## Alan Turing's insight

Turing creates a formal mathematical tool to investigate this problem.

It became known as a Turing Machine.

::media::

<BaseImg class="portrait" src="images/turing.png" alt="Black-and-white portrait photograph of Alan Turing in a suit and tie." />

<style scoped>
.portrait { max-height: 300px; }
</style>

---
clicks: 7
---

<TuringMachine tape="__yxxyx__" :head="3" start="0" labels="long"
  :rules="[['0', 'x', 'x', 'R', '0'], ['0', 'y', 'x', 'R', 'HALT']]"
  :reveal="$clicks"
  :step="Math.max(0, $clicks - 4)" />

<!--
What is a Turing Machine?

A TM has an infinitely long tape, organized into boxes.

A TM has a head that is positioned over one box at any time. The head can move left or right.

At each step, the head must read the symbol, write a new symbol, and move either left or right.

The head has internal state, which governs the rules for reading, writing, and moving.

A table of rules defines what the machine will do in any given state/symbol combination.
-->

---
clicks: 3
---

<TuringMachine tape="__yxxyx__" :head="3" start="0" view="table"
  :rules="[['0', 'x', 'x', 'R', '0'], ['0', 'y', 'x', 'R', 'HALT']]"
  :step="$clicks" />

<!--
What is a Turing Machine?

A TM has an infinitely long tape, organized into boxes.

A TM has a head that is positioned over one box at any time. The head can move left or right.

At each step, the head must read the symbol, write a new symbol, and move either left or right.

The head has internal state, which governs the rules for reading, writing, and moving.

A table of rules defines what the machine will do in any given state/symbol combination.
-->

---
layout: panel
---

## Try it

<TuringMachine tape="__yxxyx__" :head="3" start="0" view="both" editable
  :rules="[['0', 'x', 'x', 'R', '0'], ['0', 'y', 'x', 'R', 'HALT']]" />

<style scoped>
:deep(.tm) { max-height: 370px; }
</style>

<!--
Interactive: Step, Back, Run. Type a new tape in the box (use _ for blanks) to try other inputs, e.g. one with no y, which runs off forever to the right.
-->

---

## You can create a Turing Machine for any algorithm

Turing proved that any algorithm can be broken down into the kinds of operations that a Turing Machine can do.

… but it would take a semester to show you why this is the case.

---
layout: media
---

## McCulloch & Pitts (1943)

The first(?) attempt to mathematically model simple kinds of neural networks.

::media::

<BaseImg class="paper" src="images/mcculloch-pitts-1943.png" alt="Excerpt from McCulloch and Pitts (1943), section 2, The Theory: Nets Without Circles. It lists five physical assumptions: the activity of the neuron is all-or-none; a fixed number of synapses must be excited within the period of latent addition to excite a neuron; the only significant delay is synaptic delay; any inhibitory synapse absolutely prevents excitation; the structure of the net does not change with time." />

<style scoped>
.paper { background: #fff; padding: 0.4rem; }
</style>

---
layout: two-cols-header
cols: right-wide
---

::left::

## Logical Operations with Neurons

These operations are Turing Complete (with some assumptions about the tape)

::right::

<div class="mp-logic">
  <BaseImg src="images/mcculloch-pitts-logic.png" alt="McCulloch and Pitts' figure of small nets of neurons, panels a to i, drawn as triangles with axons ending on other neurons." />
  <span style="left: 40.4%; top: 4.3%">1 at t-1</span>
  <span style="left: 82.6%; top: 3.4%">1 OR 2</span>
  <span style="left: 35.6%; top: 18%">1 AND 2</span>
  <span style="left: 80%; top: 21.6%">1 AND NOT 2</span>
  <span style="left: 41.4%; top: 83.6%">1 at t-1<br>AND<br>1 at t-2</span>
</div>

<style scoped>
.mp-logic {
  position: relative;
  height: 470px;
  aspect-ratio: 1306 / 1248;
  margin-left: auto;
  background: #fff;
}
.mp-logic img { width: 100%; height: 100%; display: block; }
.mp-logic span {
  position: absolute;
  width: 22.5%;
  height: 11.5%;
  display: flex;
  align-items: center;
  font-size: 13px;
  line-height: 1.15;
  color: #000;
}
</style>

---
layout: panel
gap: 0.75rem
---

<p class="hh-lead">One direction we could go from here: More biological realism.</p>

## Hodgkin & Huxley model

<HodgkinHuxley />

<p class="hh-src"><a href="https://www.andrewkrause.org/tools-code/hodgkin-huxley-simulation-with-javascript">Original web demo</a></p>

<style scoped>
.hh-lead { margin: 0; color: var(--fenbrook-fg-soft); font-size: 1.1rem; }
h2 { margin: 0; font-size: 1.8rem; }
.hh-src { margin: 0; text-align: right; font-size: 0.8rem; }
</style>

<!--
Live simulation. Stimulate with a small pulse (under about 7) and nothing happens; a bigger one fires a spike. Raise the steady current past about 6.3 and it fires repeatedly, faster as the current grows. "Show gates" plots m, h and n.
-->

---
layout: center
---

# Does this level matter for explaining cognition?

---
layout: center
width: 30ch
---

# Connectionism

Cognition is best described by the distributed computation that occurs in networks of neurons.

<!--
One theory about the key functional properties of a mind is known as connectionism. Connectionism focuses on the functional properties of neurons, and proposes that the important part of biological minds is the distributed computation that occurs in neurons. If we can recreate the right kinds of distributed computation, then we can recreate cognition.

Like other approaches aimed at describing the functional characteristics of a mind, connectionism works through mathematical abstraction. These abstractions, or models, are meant to capture the important bits of the system while ignoring the details. Or, another way of thinking about this is that we're trying to identify something like the algorithm from Marr's levels, without worrying about the details of how the algorithm is implemented. This will necessarily involve ignoring some parts of the implementation, and instead focusing on what we believe to be the key functional properties of the system.
-->

---
clicks: 4
---

<NeuronDiagram build />

<!--
Finally, we have some kind of activation function, which describes how the aggregate activity of the neuron is transformed into the output. There are lots of possible activation functions that can be used. In this case, I'm imagining that there is a threshold, which I'm representing with the letter T, and if the aggregate activity is at or above the threshold, the neuron's output is 1. If it is below the threshold, then the output is 0.
-->

---
layout: panel
---

## What's the output?

<NeuronDiagram :inputs="['10', '4', '-3']" :weights="['0.8', '0.5', '2']" :activation="['1 if X ≥ 3', '0 if X < 3']" output="?" />

---
layout: panel
---

## What's the output?

<NeuronDiagram :inputs="['5', '-3', '1']" :weights="['-1', '-2', '-2']" :activation="['max(0, X)']" output="?" />

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

Compare this kind of model neural network with the function of a real neuron and the real neural networks of the brain.

What's left out?

---
layout: panel
---

## Early connectionism (c. 1957): **Perceptrons.**

<div class="perceptron">
  <Network view-box="40 60 540 350" :r="49.45" :arrow="101.3"
    :layers="[{ x: 200.2, ys: [122.4, 234.2, 346] }, { x: 408.3, ys: [179.1, 289.3] }]" />
  <BaseImg src="images/mark-i-perceptron.png" alt="Black-and-white photograph of the Mark I Perceptron: a tall cabinet packed with a dense tangle of wires, with banks of connectors at the sides." />
</div>

<blockquote class="nyt">
"... the embryo of an electronic computer that [the Navy] expects will be able to walk, talk, see, write, reproduce itself and be conscious of its existence."
<span>New York Times article on Perceptrons</span>
</blockquote>

<style scoped>
.perceptron { display: grid; grid-template-columns: 1fr auto; gap: 2rem; align-items: center; min-height: 0; }
.perceptron img { height: 250px; }
.nyt { font-size: 1rem; margin: 0; }
.nyt span { display: block; text-align: right; font-style: normal; margin-top: 0.3rem; }
.nyt span::before { content: '– '; }
</style>

---
layout: center
width: 100%
---

<figure class="rosenblatt">
  <BaseImg src="images/rosenblatt-1958-perceptron.png" alt="Two diagrams from Rosenblatt. Fig. 1, organization of a biological brain: red areas indicate active cells responding to the letter X. Fig. 2, organization of a perceptron: a retina of sensory points feeds a projection area by topographic connections, then association units by random connections, then response units that send an output signal, with feedback circuits." />
  <figcaption>An image of the perceptron from Rosenblatt's “The Design of an Intelligent Automaton,” Summer 1958.</figcaption>
</figure>

<style scoped>
.rosenblatt { margin: 0; }
.rosenblatt img { height: 400px; margin: 0 auto; }
.rosenblatt figcaption { font-size: 0.9rem; color: var(--fenbrook-fg-soft); margin-top: 0.6rem; }
</style>

---
layout: media
---

## What can Perceptrons do?

Think of each input node as a dimension, and each output as a category.

Perceptrons can find the linear separation between categories.

Two-dimensional example to the right, but most perceptrons have many more dimensions.

::media::

<BaseImg class="sep-img" src="images/perceptron-linear-separation.png" alt="Four panels plotting animals by size (vertical) against domestication (horizontal): large red dogs and small blue cats. Over the four panels a straight line shifts until it separates the dogs from the cats." />

<style scoped>
.sep-img { background: #fff; }
</style>

---
layout: panel
---

<div class="cant">
  <BaseImg src="images/perceptrons-book.png" alt="Green cover of Perceptrons by Marvin L. Minsky and Seymour A. Papert, expanded edition, with an orange spiral maze pattern." />
  <div>
    <h2>What can't Perceptrons do?</h2>
    <p>Non-linear boundaries.</p>
    <p>This makes most complex pattern recognition tasks impossible for Perceptrons</p>
  </div>
</div>

<SeparabilityPlots />

<style scoped>
.cant { display: flex; gap: 1.5rem; align-items: center; }
.cant img { height: 130px; transform: rotate(2.88deg); }
.cant h2 { font-size: 1.6rem; margin: 0 0 0.4rem; }
.cant p { margin: 0.2rem 0; font-size: 1.15rem; }
</style>

---
layout: panel
---

## Can any weights separate XOR?

<PerceptronPlayground problem="xor" />

<!--
Drag w1, w2 and b. The shaded side outputs 1. Nothing gets all four right; "Try every setting" checks about 15,000 and the best is 3 of 4. AND and OR (buttons at the top) are easy. "Train" runs the perceptron learning rule: it settles on AND and OR and cycles forever on XOR.
-->

---
layout: panel
---

## The solution? Multi-layer networks (c. 1986)

<div class="mlp">
  <Network view-box="40 130 580 320" :r="38.5" :arrow="78.8" :layers="[
    { x: 166.8, ys: [186.4, 273.4, 360.4], label: 'Input Nodes', labelY: 424 },
    { x: 328.8, ys: [230.5, 316.2], label: 'Hidden Nodes', labelY: 387 },
    { x: 484.6, ys: [183.8, 270.8, 357.8], label: 'Output Nodes', labelY: 425 },
  ]" />
  <BaseImg src="images/rumelhart-hinton-williams-1986.png" alt="First page of Rumelhart, Hinton and Williams, Learning representations by back-propagating errors, showing the title, authors and opening abstract." />
</div>

<style scoped>
.mlp { display: grid; grid-template-columns: 1fr auto; gap: 2rem; align-items: center; }
.mlp img { height: 300px; transform: rotate(3.89deg); background: #fff; }
</style>

---
layout: center
---

# But why did these become a popular model of the mind?

---
layout: media
---

## Past-tense acquisition

This man is *ricking*

Yesterday, he \_\_\_\_\_\_.

::media::

<BaseImg class="ricking" src="images/ricking.png" alt="A person doing a handstand on a moving skateboard down a sunlit, tree-lined street." />

<style scoped>
.ricking { max-height: 340px; }
</style>

---

Children show an overgeneralization pattern. When they start to learn lots of *regular -ed* verbs, they generalize to other verbs, both new and some old.

*The dog is going outside.*

*The dog goed outside.*

This leads to a slightly odd pattern where they show a decrease in accuracy for irregular verbs for a while.

---

Models of language learning posited a two-part process: one that allowed the children to learn the rule for making past tense verbs, and another to memorize exceptions to the rule.

This was a symbolic / rule-based model.

---
layout: panel
---

## Could a non-symbolic, non-rule based mechanism show the same kinds of patterns?

<figure class="rm">
  <BaseImg src="images/rumelhart-mcclelland-network.png" alt="Rumelhart and McClelland's past-tense network: a phonological representation of the root form is encoded into Wickelfeatures, a pattern associator with modifiable connections maps them to Wickelfeatures of the past tense, and a decoding network turns those into the phonological past tense." />
  <figcaption>Rumelhart &amp; McClelland, 1985</figcaption>
</figure>

<style scoped>
.rm { margin: 0; align-self: center; }
.rm img { height: 330px; background: #fff; }
.rm figcaption { text-align: right; color: var(--fenbrook-fg-soft); margin-top: 0.4rem; }
</style>

---
layout: center
width: 100%
---

<figure class="rm">
  <BaseImg src="images/rumelhart-mcclelland-learning-curve.png" alt="Learning curves from Rumelhart and McClelland: percent features correct over 200 trials. Regular verbs climb quickly toward 1.0; irregular verbs dip early, then rise more slowly." />
  <figcaption>Rumelhart &amp; McClelland, 1985</figcaption>
</figure>

<style scoped>
.rm { margin: 0 auto; width: fit-content; }
.rm img { height: 330px; background: #fff; }
.rm figcaption { text-align: right; color: var(--fenbrook-fg-soft); margin-top: 0.4rem; }
</style>

---

Connectionist models starts to show generative power for explaining cognitive phenomena.

Though there are lots of skeptics at this stage, too.
