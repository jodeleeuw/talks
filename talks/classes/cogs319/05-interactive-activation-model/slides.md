---
theme: fenbrook
title: The Interactive Activation Model
info: |
  ## The Interactive Activation Model
  COGS 319: the word superiority effect and McClelland & Rumelhart's (1981)
  interactive activation model of letter perception.
transition: fade
addons:
  - '@/../../../../addons/cogsci-demos'
themeConfig:
  course: COGS 319
  event: The Interactive Activation Model
layout: cover
---

# The Interactive Activation Model

::speaker::
Josh de Leeuw

::event::
COGS 319 · Spring 2027

---
layout: media
---

# The Interactive Activation Model

What can we learn from a neural network that doesn't learn?

::media::

<BaseImg class="paper" src="images/mcclelland-rumelhart-1981.png" alt="First page of McClelland and Rumelhart (1981), An Interactive Activation Model of Context Effects in Letter Perception: Part 1. An Account of Basic Findings, Psychological Review." />

<style scoped>
.paper { max-height: 440px; background: #fff; }
</style>

---
clicks: 3
---

<FlashTrial :step="$clicks" :trials="[
  { stimulus: 'WORK', mask: '####', cue: 3, question: 'M or K?' },
  { stimulus: 'VRMK', mask: '####', cue: 3, question: 'M or K?' },
  { stimulus: '___K', mask: '####', cue: 3, question: 'M or K?' },
]" />

<!--
Each click runs one trial: a fixation cross, the letters for about 60 ms, then a #### mask with the probed position boxed. Ask the class "M or K?" before moving on. "Again" replays a trial; the exposure slider (bottom) sets the flash duration. Shorter is harder; on most projectors 50–80 ms works.
-->

---

<div class="results">
  <div class="group">
    <span class="hand">This is most accurate!</span>
    <span class="row hit">W O R K</span>
    <span class="row">V R M K</span>
    <span class="row">&nbsp; &nbsp; &nbsp; K</span>
  </div>
  <div v-click class="group">
    <span class="hand">This is most accurate!</span>
    <span class="row hit">M A V E</span>
    <span class="row">V R M E</span>
    <span class="row">&nbsp; &nbsp; &nbsp; E</span>
  </div>
  <div v-click class="group">
    <span class="row"><span class="box">S</span> H I P</span>
    <span class="row"><span class="box">S</span> I N K</span>
    <span class="hand">No difference in first letter accuracy</span>
  </div>
</div>

<style scoped>
.results { display: grid; grid-template-columns: repeat(3, 1fr); gap: 2.5rem; align-items: start; width: 100%; }
.group { display: flex; flex-direction: column; align-items: center; gap: 1rem; }
.row { font-family: 'JetBrains Mono', monospace; font-weight: 700; font-size: 2rem; letter-spacing: 0.05em; white-space: pre; }
.row.hit { color: var(--fenbrook-accent); }
.box { border: 2px solid currentColor; padding: 0 0.1em; }
.hand { font-family: 'Caveat', 'Comic Sans MS', cursive; font-size: 1.3rem; color: var(--fenbrook-fg-soft); }
</style>

<!--
Letters are reported more accurately in a word than in a random string, or even alone. Pseudowords (MAVE) get the same advantage.

SHIP vs. SINK: Surprising, perhaps, because there are only three words _HIP but 12-14 for _INK
-->

---
layout: media
---

## How can we explain these findings?

::media::

<BaseImg class="levels" src="images/iam-levels.png" alt="Sketch of three levels of processing: feature level at the bottom with input arrows, letter level in the middle, and word level at the top, with arrows running up and down between neighbouring levels and loops within each level." />

<style scoped>
.levels { max-height: 420px; background: #fff; }
</style>

---
layout: media
---

Describe what's going on here.

- What do the circles/ovals represent?
- What do the lines represent?
- (Are they all the same?)
- How does the process unfold as the model sees a letter/word?
- Where are the points of confusion?

::media::

<BaseImg class="net" src="images/iam-network.png" alt="Figure 3 from McClelland and Rumelhart (1981): a fragment of the network, with word units (ABLE, TRAP, TRIP, TAKE, TIME, CART) at the top, letter units in the middle, and feature units at the bottom, densely interconnected; arrowheads mark excitatory connections and dots mark inhibitory ones." />

<style scoped>
.net { max-height: 400px; background: #fff; }
</style>

---
layout: two-cols-header
cols: equal
clicks: 6
---

::left::

<UnitDiagram :step="Math.min($clicks, 3)" />

::right::

<div class="eqs">
  <p v-if="$clicks === 0">Activation value is <i>a<sub>i</sub>(t)</i></p>
  <p v-else-if="$clicks <= 3"><i>n<sub>i</sub>(t)</i> = excitatory_sum − inhibitory_sum</p>
  <p v-else-if="$clicks === 4"><i>e<sub>i</sub>(t)</i> = <i>n<sub>i</sub>(t)</i>(Max activation − <i>a<sub>i</sub>(t)</i>) &nbsp;[if <i>n<sub>i</sub>(t)</i> &gt; 0]</p>
  <p v-else-if="$clicks === 5"><i>e<sub>i</sub>(t)</i> = <i>n<sub>i</sub>(t)</i>(<i>a<sub>i</sub>(t)</i> − minimum activation) &nbsp;[if <i>n<sub>i</sub>(t)</i> &lt; 0]</p>
  <template v-else>
    <p><i>a<sub>i</sub>(t)</i> = current activation</p>
    <p><i>n<sub>i</sub>(t)</i> = net input</p>
    <p><i>e<sub>i</sub>(t)</i> = effect of input</p>
  </template>
</div>

<style scoped>
.eqs { font-size: 1.15rem; display: flex; flex-direction: column; gap: 0.3rem; }
.eqs p { margin: 0; }
</style>

<!--
Clicks 1–3 add the feature units (/ excites A, | inhibits it), the rival letter B, and the word units ABLE (excites) and BALL (inhibits). White arrows are excitatory, red inhibitory. Clicks 4–6 step through the equations.
-->

---
clicks: 2
---

<div class="update">
  <div class="unit">A</div>
  <div class="eq">
    <p class="formula">
      <i>a<sub>i</sub>(t + 1)</i> = <i>a<sub>i</sub>(t)</i>
      <span :class="{ mark: $clicks >= 1 }">− decayrate*(<i>a<sub>i</sub>(t)</i> − restingstate)</span>
      + <span :class="{ mark: $clicks >= 2 }"><i>e<sub>i</sub>(t)</i></span>
    </p>
    <p v-click="1" class="note">The decay is a proportion of how active we are.<br>More active = more decay.</p>
    <p v-click="2" class="note right">Effect of input</p>
  </div>
</div>

<style scoped>
.update { display: flex; align-items: center; gap: 2.5rem; }
.unit { width: 84px; height: 84px; flex: none; border: 2.4px solid var(--fenbrook-fg); border-radius: 50%; display: grid; place-items: center; font-family: 'JetBrains Mono', monospace; font-weight: 700; font-size: 1.6rem; }
.eq { display: flex; flex-direction: column; gap: 0.8rem; }
.eq p { margin: 0; }
.formula { font-size: 1.3rem; }
.mark { border-bottom: 2px solid #e0453a; border-radius: 0 0 40% 40%; padding-bottom: 2px; }
.note { font-size: 0.95rem; color: var(--fenbrook-fg-soft); }
.note.right { text-align: right; }
</style>

---
layout: panel
---

## One unit over time

<ActivationUnit />

<!--
The same update rule, run on one unit with steady input. Push excitation up and the unit climbs but slows as it nears the maximum (the n(max − a) term); add inhibition and it sinks toward the minimum. Decay pulls it back toward rest, so with input on it settles where decay balances input. "Turn input off halfway" shows it relax back to its resting level.
-->

---
layout: center
---

## Why does the model produce these patterns?

<div class="figs">
  <figure>
    <figcaption class="head">R E A D &nbsp;or&nbsp; E</figcaption>
    <BaseImg src="images/iam-read-e.png" alt="Figure from McClelland and Rumelhart: letter-level activation of E over time when presented in READ versus alone; E in READ rises higher than E alone." />
  </figure>
  <figure>
    <figcaption class="head">M A V E</figcaption>
    <BaseImg src="images/iam-rich-get-richer.png" alt="Figure 10 from McClelland and Rumelhart, the rich-get-richer effect: activation curves over time for the words have, gave, save and move when the model sees MAVE." />
  </figure>
  <figure>
    <figcaption class="head">M A V E</figcaption>
    <BaseImg src="images/iam-gang.png" alt="Figure 11 from McClelland and Rumelhart, the gang effect: activation curves over time for male, move and more when the model sees MAVE under different assumptions." />
  </figure>
</div>

<style scoped>
.figs { display: grid; grid-template-columns: 1.25fr 1fr 1fr; gap: 1rem; align-items: end; margin-top: 1rem; }
figure { margin: 0; display: flex; flex-direction: column; align-items: center; gap: 0.5rem; }
figure img { background: #fff; max-height: 270px; width: 100%; object-fit: contain; }
.head { font-family: 'JetBrains Mono', monospace; font-weight: 700; letter-spacing: 0.1em; }
</style>

---
layout: panel
---

## Run the model

<InteractiveActivation />

<!--
A working version of the model: 1,179 four-letter words, 26 letter units per position, and 14 line-segment features per position, with the parameters from the 1981 paper.

- "WOR? (K or R?)" covers the parts of the last letter that tell K from R. Both letters get the same bottom-up support, but WORK feeds activation back down to K, so K wins.
- "WORK", "VRMK" and "K alone" flash the display for 12 cycles and then mask it. Run all three and compare how high K peaks (listed under the buttons): word > letter alone > nonword in this run.
- "MAVE" is not a word, but HAVE, GAVE, SAVE and friends all support the E (rich get richer / gang effects).

Click a segment to cover or uncover it; type any four letters ("_" leaves a position blank).
-->

---
layout: media
---

# The Interactive Activation Model

What can we learn from a neural network that doesn't learn?

What's the benefit of this kind of model?

What do we get out of this scientifically?

::media::

<BaseImg class="paper" src="images/mcclelland-rumelhart-1981.png" alt="First page of McClelland and Rumelhart (1981), An Interactive Activation Model of Context Effects in Letter Perception: Part 1. An Account of Basic Findings, Psychological Review." />

<style scoped>
.paper { max-height: 440px; background: #fff; }
</style>
