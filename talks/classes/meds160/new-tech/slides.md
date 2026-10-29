---
theme: fenbrook
title: New Tech
info: |
  ## New Tech
  Is AI the most human oriented technology we've ever made?
transition: fade
themeConfig:
  accentIcons: hugeicons:artificial-intelligence-03
  course: MEDS 160
  event: Guest Lecture
layout: cover
---

# New Tech

artificial intelligence, human thinking, and our extended future

::speaker::
Josh de Leeuw

::event::
MEDS 160 Guest Lecture · Fall 2026

---
layout: center
width: 75%
---

# A provocative claim:

## Artificial Intelligence is the most <Hi>human oriented technology</Hi> we've ever created.

---
layout: section
number: 1
---

# How are AI systems trained?

---
layout: panel
align: center
clicks: 1
---

# Step 1: <Hi>predict</Hi> the next word

<NextToken :revealed="$clicks > 0" />

<!--
Predict the next token.
-->

---
layout: panel
align: center
---

# Step 2: when it's wrong, <Hi>nudge</Hi> it

<TrainStep />

<!--
When a mistake is made, adjust the machine so that the correct word is more likely next time.
-->

---
layout: quote
---

Think of ChatGPT as a blurry jpeg of all the text on the Web.

::attribution::
Ted Chiang, *The New Yorker*, February 2023

---
layout: panel
align: center
---

# A <Hi>completer</Hi>, not an assistant

<div class="completer">
  <div class="col">
    <div class="tag">prompt</div>
    <div class="card prompt">Serendipity means the occurrence and development of events by chance in a happy or beneficial way. Use the word in a sentence.</div>
    <div v-click class="tag">GPT-3, pretrained only</div>
    <div v-after class="card">Serendipity is the ability to see something good in something bad. Use the word in a sentence.<br><br>Serendipity means to be happy with what you have. Use the word in a sentence.<br><br>Serendipity means finding something good in something that is bad. Use the word in a sentence.</div>
  </div>
  <div class="col">
    <div class="tag">prompt</div>
    <div class="card prompt">Create a shopping list from this recipe:<br>Trim the ends off zucchini. Cut zucchini in half lengthwise; scoop out pulp, leaving 1/2-in. shells. Finely chop pulp. In a skillet, cook beef, zucchini pulp, onion, mushrooms and peppers over medium heat until meat is no longer pink; drain. […] Sprinkle with remaining cheese.</div>
    <div v-click class="tag">GPT-3, pretrained only</div>
    <div v-after class="card">Bake, uncovered, at 350° for 20-25 minutes or until zucchini is tender and cheese is melted.</div>
  </div>
</div>

<style>
.completer { display: grid; grid-template-columns: 1fr 1fr; gap: 1.2rem; align-items: start; text-align: left; font-size: 0.85rem; line-height: 1.4; }
.completer .col { display: grid; gap: 0.4rem; }
.completer .tag { font-family: 'JetBrains Mono', monospace; font-size: 0.65rem; letter-spacing: 0.04em; text-transform: uppercase; color: var(--fenbrook-muted); margin-top: 0.3rem; }
.completer .card { border: 1px solid var(--fenbrook-rule); border-radius: 10px; padding: 0.55rem 0.9rem; color: var(--fenbrook-fg); }
.completer .prompt { background: var(--fenbrook-bg-elev); }
</style>

<!--
This led to LLMs that generated plausible completions. But not the "chatgpt moment."

Needed to learn how to interact in this new setting that was not well represented in the corpus of the internet.
-->

---
layout: panel
---

# Step 3: show it <Hi>good answers</Hi>

<p class="sources">Train on example answers: <Hi>written</Hi> by hired people, <Hi>curated</Hi> from existing text, or <Hi>generated</Hi> by another model and checked by people.</p>

<div class="demos">
  <div class="tag">prompt</div><div class="tag">example answer</div>

  <div class="card prompt">List five ideas for how to regain enthusiasm for my career</div>
  <div v-click class="card">1. Take on a project that stretches you.<br>2. Find a mentor, or become one.<br>3. Learn one new skill.<br>4. Remember why you started.<br>5. Take real time off.</div>

  <div class="card prompt mono">Extract all course titles from the table below:<br>| Title | Lecturer | Room |<br>| Calculus 101 | Smith | Hall B |<br>| Art History | Paz | Hall A |</div>
  <div v-click class="card">Calculus 101, Art History</div>
</div>

<style>
.sources { margin: 0; font-size: 1rem; color: var(--fenbrook-fg-soft); max-width: 60rem; }
.demos { display: grid; grid-template-columns: 1fr 1fr; gap: 0.55rem 1rem; align-content: start; font-size: 0.9rem; line-height: 1.4; }
.demos .tag { font-family: 'JetBrains Mono', monospace; font-size: 0.65rem; letter-spacing: 0.04em; text-transform: uppercase; color: var(--fenbrook-muted); }
.demos .card { border: 1px solid var(--fenbrook-rule); border-radius: 10px; padding: 0.45rem 0.9rem; color: var(--fenbrook-fg); }
.demos .prompt { background: var(--fenbrook-bg-elev); }
.demos .mono { font-family: 'JetBrains Mono', monospace; font-size: 0.75rem; }
</style>

<!--
Fine-tuning.
-->

---
layout: panel
align: center
---

# Step 4: people <Hi>pick a winner</Hi>

<PreferenceVote />

<!--
RL-HF (and other reinforcement learning systems)
-->

---
layout: panel
---

# Step 5: same model, <Hi>different jobs</Hi>

<div class="jobs">
  <div class="chat"><p class="bubble">Can you help me with my essay?</p></div>

  <div class="cols">
    <div class="col">
      <div class="tag">system prompt</div>
      <div class="card sys">You are a writing tutor. Never write the essay for the student. Ask questions.</div>
      <div v-click class="card reply">Sure! What's your argument, in one sentence?</div>
    </div>
    <div class="col">
      <div class="tag">system prompt</div>
      <div class="card sys">You are a helpful assistant.</div>
      <div v-click class="card reply">Of course! Paste it in and tell me what kind of feedback you want.</div>
    </div>
    <div class="col">
      <div class="tag">system prompt</div>
      <div class="card sys">You are the support agent for an airline. Only discuss bookings.</div>
      <div v-click class="card reply">Sorry, I can only help with bookings. Do you have a reservation question?</div>
    </div>
  </div>

  <p v-click class="harness">Plus a <Hi>harness</Hi> around it: web search, running code, memory, your files, safety filters.</p>
</div>

<style>
.jobs { display: grid; gap: 0.8rem; align-content: start; font-size: 0.9rem; line-height: 1.4; }
.jobs .chat { display: flex; justify-content: flex-end; }
.jobs .bubble {
  margin: 0; font-size: 1.15rem; padding: 0.6rem 1rem; border-radius: 18px 18px 4px 18px; color: var(--fenbrook-fg);
  background: color-mix(in srgb, var(--fenbrook-accent) 22%, var(--fenbrook-bg-elev));
}
.jobs .cols { display: grid; grid-template-columns: repeat(3, 1fr); gap: 0.8rem; }
.jobs .col { display: grid; gap: 0.4rem; align-content: start; }
.jobs .tag { font-family: 'JetBrains Mono', monospace; font-size: 0.65rem; letter-spacing: 0.04em; text-transform: uppercase; color: var(--fenbrook-muted); }
.jobs .card { border: 1px solid var(--fenbrook-rule); border-radius: 10px; padding: 0.55rem 0.9rem; color: var(--fenbrook-fg); }
.jobs .sys { font-family: 'JetBrains Mono', monospace; font-size: 0.75rem; background: var(--fenbrook-bg-elev); color: var(--fenbrook-fg-soft); min-height: 4.6rem; }
.jobs .harness { margin: 0.4rem 0 0; font-size: 1.05rem; color: var(--fenbrook-fg-soft); }
</style>

---
layout: center
width: 80%
---

# <Quiet>The most human oriented technology?</Quiet>

## It's trained on <Hi>our language and our preferences</Hi>.

---
layout: section
number: 2
---

# How do LLMs work?

---
layout: media
side: right
caption: "Santiago Ramón y Cajal, Purkinje cells (A) and granule cells (B), pigeon cerebellum, 1899. Instituto Cajal, Madrid. Public domain."
---

<script setup>
const base = import.meta.env.BASE_URL
</script>

# A <Hi>real</Hi> neuron

- **Dendrites**: branches that collect signals from other neurons
- **Cell body**: adds those signals up
- **Axon**: carries a spike onward when the total is high enough

::media::
<img :src="base + 'images/cajal-purkinje.jpg'" alt="Ramón y Cajal's ink drawing of Purkinje cells, with a densely branching dendritic tree above each cell body and a thin axon running down" class="cajal" />

<style scoped>
.cajal { max-height: 100%; max-width: 100%; object-fit: contain; border-radius: 6px; }
</style>

---
layout: panel
---

# Real neurons → <Hi>artificial neurons</Hi>

<p class="sub43">McCulloch &amp; Pitts (1943): a neuron is “all-or-none.” It fires if at least <b>θ</b> excitatory inputs are on, and <b>any</b> active inhibitory input stops it.</p>

<McCullochPitts />

<style>
.sub43 { margin: 0; font-size: 1.05rem; color: var(--fenbrook-fg-soft); }
.sub43 b { color: var(--fenbrook-fg); }
</style>

<!--
History is traceable to the earliest attempts at building computational systems inspired by the brain.
-->

---
layout: panel
clicks: 4
---

<script setup>
const _specs = import.meta.glob('./diagrams/*.json', { eager: true, import: 'default' })
const neuron = _specs['./diagrams/neuron.json']
</script>

# Real neurons → <Hi>artificial neurons</Hi>

<Diagram class="nn" :spec="neuron" />

<style scoped>
.nn :deep(.box-bio rect) { fill: none; stroke: none; }
.nn :deep(.box-bio .diagram-wrap-text) { color: var(--fenbrook-accent); font-style: italic; }
.nn :deep(.connector-label) { fill: var(--fenbrook-muted); }
</style>

<!--
Real neurons -> Artificial neurons
-->

---
layout: panel
clicks: 4
---

<script setup>
const base = import.meta.env.BASE_URL
</script>

# Neural <Hi>networks</Hi>

<div class="catdog">
  <img :src="base + 'images/puppy.jpg'" alt="golden retriever puppy" class="pup" />
  <span class="arrow">→</span>
  <CatDogNet class="net" />
</div>

<style scoped>
.catdog { display: flex; align-items: center; gap: 1rem; }
.pup { width: 9rem; aspect-ratio: 1; object-fit: cover; border-radius: 10px; flex: none; }
.arrow { font-size: 1.6rem; color: var(--fenbrook-muted); flex: none; }
.net { flex: 1; min-width: 0; }
</style>

---

# These are <Hi>not</Hi> brains.

They were a theoretical framework to think about what brains *do*.

<div v-click>

<Quiet>…then people figured out they could do real stuff.</Quiet>

</div>

<!--
... these are not brains. They were a theoretical framework to think about what brains *do*.

Then people started to figure out that they can do real stuff.
-->

---
layout: media
side: right
caption: "Mark I Perceptron, c. 1960. Left: its wiring and motor-driven weights (Cornell University Library). Right: its operator's manual (public domain)."
---

<script setup>
const base = import.meta.env.BASE_URL
</script>

# The perceptron <Hi>learns</Hi>

- **Rosenblatt, 1958**: a psychologist, funded by the Navy
- Eye: 20 × 20 light sensors (<Hi>400 pixels</Hi>)
- Weights: knobs, turned by motors when it was wrong

<p v-click class="nyt">The <i>New York Times</i>: the Navy expects it to “walk, talk, see, write, reproduce itself and be conscious of its existence.”</p>

::media::
<div class="mark1">
  <img :src="base + 'images/mark1-perceptron-photo.jpeg'" alt="Close-up of the Mark I Perceptron: a dense tangle of patch wires on the left and columns of motor-driven potentiometers on the right" class="wires" />
  <img :src="base + 'images/mark1-perceptron.png'" alt="Black-and-white photo of the Mark I Perceptron: tall cabinets of wiring and plugboards with a camera on a tripod in front, labeled S-unit monitor, association units, response panel" class="whole" />
</div>

<style scoped>
.mark1 { display: flex; gap: 0.6rem; align-items: center; height: 100%; width: 100%; min-height: 0; }
.mark1 img { min-width: 0; max-height: 100%; object-fit: contain; border-radius: 6px; }
.mark1 .wires { flex: 0.81; }
.mark1 .whole { flex: 1.23; }
.nyt { font-size: 0.8rem !important; line-height: 1.4 !important; color: var(--fenbrook-muted) !important; margin-top: 1.5rem !important; }
</style>

---
layout: panel
---

# Before 2012: <Hi>hand-built</Hi> vision

<div class="vocs">
  <div class="voctask">
    <p>PASCAL VOC: is there a … in this photo?</p>
    <div class="chips">
      <span v-for="c in ['aeroplane','bicycle','bird','boat','bottle','bus','car','cat','chair','cow','dining table','dog','horse','motorbike','person','potted plant','sheep','sofa','train','tv']" :key="c">{{ c }}</span>
    </div>
    <p class="how">20 categories. Engineers designed the features (edges, gradients, “visual words”) by hand; a classifier learned only the last step.</p>
  </div>
  <VocChart />
</div>

<p class="cite">Best entry each year, PASCAL VOC classification (Everingham et al.). The test set changed each year.</p>

<style scoped>
.vocs { display: grid; grid-template-columns: 17rem 1fr; gap: 2.5rem; align-items: center; width: 100%; }
.voctask p { margin: 0 0 0.6rem !important; font-size: 0.95rem !important; color: var(--fenbrook-fg) !important; }
.chips { display: flex; flex-wrap: wrap; gap: 0.3rem; }
.chips span { font-size: 0.72rem; padding: 0.1rem 0.45rem; border-radius: 999px; border: 1px solid var(--fenbrook-rule); color: var(--fenbrook-fg-soft); }
.voctask p.how { margin: 0.8rem 0 0 !important; font-size: 0.8rem !important; line-height: 1.4; color: var(--fenbrook-muted) !important; }
.cite { margin: 0.3rem 0 0 !important; font-size: 0.7rem !important; color: var(--fenbrook-muted) !important; }
</style>

---
layout: panel
clicks: 2
---

<script setup>
const base = import.meta.env.BASE_URL
</script>

# 2012: networks <Hi>learn to see</Hi>

<div class="inet">
  <div class="task">
    <img :src="base + 'images/puppy.jpg'" alt="golden retriever puppy" />
    <ol>
      <li class="hit">golden retriever</li>
      <li>Labrador retriever</li>
      <li>cocker spaniel</li>
      <li>tennis ball</li>
      <li>teddy bear</li>
    </ol>
    <p>ImageNet: 1.2 million photos, 1,000 categories (120 are dog breeds). Five guesses; it counts if one is right.</p>
  </div>
  <ImageNetChart />
</div>

<style scoped>
.inet { display: grid; grid-template-columns: 17rem 1fr; gap: 2.5rem; align-items: center; width: 100%; }
.task { display: grid; grid-template-columns: 6.5rem auto; gap: 0.4rem 0.9rem; align-items: center; }
.task img { width: 6.5rem; aspect-ratio: 1; object-fit: cover; border-radius: 8px; }
.task ol { margin: 0 !important; padding-left: 1.2rem !important; }
.task li { margin: 0 !important; font-size: 0.8rem !important; line-height: 1.45 !important; color: var(--fenbrook-fg-soft) !important; white-space: nowrap; }
.task li.hit { color: var(--fenbrook-accent) !important; font-weight: 600; }
.task p { grid-column: 1 / -1; margin: 0.4rem 0 0 !important; font-size: 0.8rem !important; line-height: 1.4; color: var(--fenbrook-muted) !important; }
</style>

---

# Inspired by brains, but <Hi>very different</Hi> constraints

<!--
Share a similar set of underlying commitments, but LLMs are very different from humans too.

Constraints are way different. Power consumption, storage, time, etc.
-->

---
layout: fact
source: "Balasubramanian (2021), PNAS 118(32) · Meta, Llama 3.1 model card (2024)"
---

# 20 watts

<style scoped>
:deep(.fact-inner) { max-width: 46ch !important; }
.step { margin-top: 0.8rem; }
</style>

The power budget of a human brain. About one bright LED bulb.

<div v-click class="step">

One GPU: <Hi>700 watts</Hi>. That's 35 brains.

</div>

<div v-click class="step">

Training Llama 3: 16,000 GPUs for months, about 21,600 megawatt-hours.<br>
A brain's first 20 years: 3.5.<br>
That's <Hi>6,000 people</Hi> growing up.

</div>

---
layout: panel
align: center
clicks: 2
---

# Thousands of times <Hi>more words</Hi>

<DataCircles />

<p class="cite">Area ∝ amount of text. Human estimate: Frank (2023), <i>Trends in Cognitive Sciences</i>. Llama 3 team (2024).</p>

<style scoped>
.cite { margin: 0.3rem 0 0 !important; font-size: 0.7rem !important; color: var(--fenbrook-muted) !important; }
</style>

---
layout: center
width: 80%
---

# <Quiet>The most human oriented technology?</Quiet>

## It's built on a <Hi>theory of us</Hi>.

---
layout: section
number: 3
---

# How do we interact with LLMs?

---
layout: panel
clicks: 3
---

# Who learns <Hi>whose</Hi> language?

<div class="al">

<ol class="steps">
  <li :class="{ on: $clicks === 0, past: $clicks > 0 }">machine code</li>
  <li :class="{ on: $clicks === 1, past: $clicks > 1 }">assembly</li>
  <li :class="{ on: $clicks === 2, past: $clicks > 2 }">Python</li>
  <li :class="{ on: $clicks === 3 }">plain English</li>
</ol>

<div class="rung">

<div class="code" v-if="$clicks === 0">

```text
01001000 10001101 00111101 00011001
00000000 00000000 00000000 10111110
00000101 00000000 00000000 00000000
00110001 11000000 10001011 00001111
11110110 11000001 00000001 01110101
00000010 00000001 11001000 01001000
10000011 11000111 00000100 11111111
11001110 01110101 11101111 11000011
00000011 00000000 00000000 00000000
00001000 00000000 00000000 00000000
00000101 00000000 00000000 00000000
00001100 00000000 00000000 00000000
00000111 00000000 00000000 00000000
```

</div>
<div class="code" v-if="$clicks === 1">

```asm
    lea  rdi, [rip + numbers]
    mov  esi, 5
    xor  eax, eax
next:
    mov  ecx, [rdi]
    test cl, 1
    jnz  skip
    add  eax, ecx
skip:
    add  rdi, 4
    dec  esi
    jnz  next
    ret
numbers:
    .long 3, 8, 5, 12, 7
```

</div>
<div class="code" v-if="$clicks === 2">

```python
numbers = [3, 8, 5, 12, 7]
total = 0
for n in numbers:
    if n % 2 == 0:
        total += n
```

</div>
<div class="code prose" v-if="$clicks === 3">

What do the even numbers in this list add up to?

3, 8, 5, 12, 7

</div>

</div>
</div>

<style scoped>
.al { display: grid; grid-template-columns: 11rem 1fr; gap: 1.5rem; align-items: stretch; }
.al .steps { list-style: none; padding: 0; margin: 0 !important; display: grid; gap: 0.5rem; }
.steps li {
  margin: 0 !important; display: flex; align-items: center; font-size: 0.95rem; padding: 0.5rem 0.8rem; border-radius: 8px;
  border: 1px solid var(--fenbrook-rule); color: var(--fenbrook-fg-soft);
}
.steps li.past { color: var(--fenbrook-muted); }
.steps li.on { background: var(--fenbrook-accent); border-color: var(--fenbrook-accent); color: var(--fenbrook-bg); }
.rung { display: grid; }
.code {
  height: 100%; border-radius: 10px; overflow: hidden;
  background: var(--fenbrook-bg-elev); border: 1px solid var(--fenbrook-rule);
}
.code :deep(.slidev-code-wrapper) { margin: 0; }
.code :deep(.slidev-code) { border: none !important; border-radius: 0 !important; box-shadow: none !important; }
.code :deep(pre) { margin: 0; padding: 0.9rem 1.1rem !important; background: transparent !important; font-size: 0.85rem; line-height: 1.55; }
.code.prose { display: flex; flex-direction: column; justify-content: center; align-items: flex-start; gap: 1rem; padding: 0 1.1rem; }
.code.prose p { margin: 0; font-size: 2rem; color: var(--fenbrook-fg); }
</style>

---
layout: panel
---

# It does what you <Hi>mean</Hi>

<div class="prag">
  <div class="row head">
    <span>You say</span>
    <span>A literal machine</span>
    <span>An LLM</span>
  </div>
  <div class="row" v-click>
    <span class="say">“Can you make this shorter?”</span>
    <span class="lit">Yes.</span>
    <span class="llm">Shortens it.</span>
  </div>
  <div class="row" v-click>
    <span class="say">“My boss is going to read this.”</span>
    <span class="lit">OK.</span>
    <span class="llm">Makes it formal, cuts the joke.</span>
  </div>
  <div class="row" v-click>
    <span class="say">“No, the other one.”</span>
    <span class="lit"><code>Error: 'one' is undefined</code></span>
    <span class="llm">Switches to the other option.</span>
  </div>
</div>

<style scoped>
.prag { display: grid; gap: 0.6rem; margin-top: 1rem; }
.row { display: grid; grid-template-columns: 1.4fr 1.1fr 1.2fr; gap: 1.5rem; align-items: center; padding: 0.7rem 1.1rem; border-radius: 10px; background: var(--fenbrook-bg-elev); border: 1px solid var(--fenbrook-rule); }
.row.head { background: transparent; border-color: transparent; padding-top: 0; padding-bottom: 0; font-size: 0.75rem; text-transform: uppercase; letter-spacing: 0.08em; color: var(--fenbrook-muted); }
.say { font-size: 1.15rem; color: var(--fenbrook-fg); }
.lit { font-size: 1.05rem; color: var(--fenbrook-muted); }
.lit code { font-size: 0.85rem; white-space: nowrap; }
.llm { font-size: 1.05rem; color: var(--fenbrook-accent); }
</style>

---
layout: center
width: 70%
---

# We can talk to it like a person. Do we <Hi>think</Hi> of it like one?

---

# The heat just kicked on. <Hi>Why?</Hi>

<div class="stances">
<div v-click="1">

### Physical stance
“A metal strip cooled, bent, and closed a circuit.”

<Quiet>Predict it from what it's made of and the laws of physics.</Quiet>

</div>
<div v-click="2">

### Design stance
“It's set to keep the room at 68°.”

<Quiet>Predict it from what it was built to do.</Quiet>

</div>
<div v-click="3">

### Intentional stance
“It thinks it's cold in here.”

<Quiet>Predict it from beliefs and desires.</Quiet>

</div>
</div>

<style scoped>
.stances { display: grid; grid-template-columns: repeat(3, 1fr); gap: 2rem; margin-top: 1.5rem; }
.stances h3 { color: var(--fenbrook-accent); margin-bottom: 0.4rem; }
.stances p { font-size: 1rem; }
</style>

<!--
Three different interactions. Describe them. One physical stance, one design stance, one intentional stance.
-->

---
layout: panel
---

# People use the <Hi>intentional</Hi> stance to talk about AI

<div class="xq">
  <div v-click class="row"><p class="q">“Predicting the next token well means that you <Hi>understand</Hi> the underlying reality…”</p><p class="who">Ilya Sutskever, OpenAI chief scientist · 2023</p></div>
  <div v-click class="row"><p class="q">“These things do <Hi>understand</Hi>.”</p><p class="who">Geoffrey Hinton, on <i>60 Minutes</i> · 2023</p></div>
  <div v-click class="row"><p class="q">“Alignment <Hi>faking</Hi> in large language models”</p><p class="who">Anthropic &amp; Redwood Research, paper title · 2024</p></div>
  <div v-click class="row"><p class="q">Models “<Hi>hide their intent</Hi> while continuing to misbehave.”</p><p class="who">OpenAI researchers · 2025</p></div>
  <div v-click class="row"><p class="q">“Claude will <Hi>plan</Hi> what it will say many words ahead.”</p><p class="who">Anthropic researchers · 2025</p></div>
</div>

<style scoped>
.xq { display: grid; gap: 0.85rem; max-width: 50rem; }
.row p { margin: 0 !important; }
.q { font-size: 1.25rem !important; line-height: 1.3; color: var(--fenbrook-fg) !important; }
.who { font-family: 'JetBrains Mono', monospace; font-size: 0.7rem !important; letter-spacing: 0.03em; color: var(--fenbrook-muted) !important; margin-top: 0.15rem !important; }
</style>

---

# The stance works because it was <Hi>built</Hi> to

<v-clicks>

- **Step 1:** trained to continue text written by people with beliefs and goals. <Quiet>Predicting us means modeling minds.</Quiet>
- **Step 3:** shown thousands of examples of a helpful assistant. <Quiet>It's handed a character to play.</Quiet>
- **Step 4:** rewarded when people liked its answer. <Quiet>"It wants to help" is the goal we trained in.</Quiet>

</v-clicks>

---
layout: panel
---

# When the stance <Hi>breaks</Hi>

<Tokenizer />

---
layout: center
width: 80%
---

# <Quiet>The most human oriented technology?</Quiet>

## It's shaped to <Hi>fit us</Hi>.

---
layout: center
width: 44ch
clicks: 1
---

<div :class="['q1', { dim: $clicks > 0 }]">

## When we use these systems, are we still <Hi>thinking</Hi>?

</div>

<div v-click class="q2">

# Is human thinking always in the <Hi>brain</Hi>?

</div>

<style scoped>
.q1 { transition: opacity 0.4s; }
.q1.dim { opacity: 0.35; }
.q2 { margin-top: 2.5rem; }
</style>

---
layout: quote
---

We humans are and always have been … ‘extended minds’ – hybrid thinking systems defined (and constantly re-defined) across a rich mosaic of resources only some of which are housed in the biological brain.

::attribution::
Andy Clark, “Extending Minds with Generative AI,” *Nature Communications* (2025)

---
layout: panel
align: center
---

# Thinking with your <Hi>hands</Hi>

<p class="sub">Find a seven-letter word. Move the tiles if it helps.</p>

<ScrabbleRack />

<style scoped>
.sub { margin: 0 0 1.5rem !important; color: var(--fenbrook-fg-soft) !important; }
</style>

---

# Otto and Inga both go to <Hi>MoMA</Hi>

<div class="pair">
<div>

<v-clicks>

**Inga** hears about an exhibition at the Museum of Modern Art.

She remembers it's on 53rd Street.

She walks there.

</v-clicks>

</div>
<div>

<v-clicks at="4">

**Otto** has Alzheimer's. He writes everything in a notebook.

He looks it up: 53rd Street.

He walks there.

</v-clicks>

</div>
</div>

<div v-click="7" class="punch">

If the notebook does the job memory does, Clark & Chalmers argue, it's <Hi>part of Otto's mind</Hi>.

</div>

<style scoped>
.pair { display: grid; grid-template-columns: 1fr 1fr; gap: 3rem; margin-top: 1rem; }
.pair p { margin: 0 0 0.6rem; }
.punch { margin-top: 1.5rem; font-size: 1.25rem; }
</style>

---
layout: panel
---

# What makes something <Hi>part of your mind</Hi>?

<div v-click="1" class="cc">

<p class="lead">Clark &amp; Chalmers: what makes Otto's notebook count</p>

<v-clicks at="2">

- It's a **constant** in his life: he rarely acts without consulting it.
- It's **directly available**, without difficulty.
- He trusts it **the way he'd trust a memory**.
- He **endorsed** the information when he wrote it down. <Quiet>(They hedge on this one.)</Quiet>

</v-clicks>

</div>

<style scoped>
.cc { margin-top: 1rem; }
.lead { margin: 0 0 0.8rem !important; font-family: 'JetBrains Mono', monospace; font-size: 0.8rem !important; letter-spacing: 0.04em; text-transform: uppercase; color: var(--fenbrook-muted) !important; }
.cc li { margin-bottom: 0.5rem; }
</style>

---
layout: center
width: 60ch
---

# How is an AI <Hi>different</Hi> from Otto's notebook?

---
layout: center
width: 60ch
---

<p class="tag">Clark: “extended cognitive hygiene”</p>

# What do we <Hi>want</Hi> to extend?

<div v-click>

# What do we <Hi>not</Hi> want to extend?

</div>

<style scoped>
.tag { margin: 0 0 1.5rem !important; font-family: 'JetBrains Mono', monospace; font-size: 0.8rem !important; letter-spacing: 0.04em; text-transform: uppercase; color: var(--fenbrook-muted) !important; }
</style>

---
layout: quote
---

This discovery of yours will create forgetfulness in the learners' souls, because they will not use their memories.

::attribution::
Thamus, on the invention of writing, in Plato's *Phaedrus* (trans. Benjamin Jowett)

---
layout: outro
mark: ""
notesLabel: "This spring"
---

**Josh de Leeuw**

jdeleeuw@vassar.edu

::next::

**COGS 100: Introduction to Cognitive Science**

Spring 2027. More on minds, brains, and machines.

<style scoped>
/* the outro's big background mark only takes text; draw the deck's accent icon (themeConfig.accentIcons) there instead */
:deep(.bigmark) {
  width: 26rem; height: 26rem; bottom: 1.5rem; left: 1rem;
  -webkit-text-stroke: 0; background: var(--fenbrook-accent); opacity: 0.24;
  -webkit-mask: url('https://api.iconify.design/hugeicons/artificial-intelligence-03.svg') center / contain no-repeat;
  mask: url('https://api.iconify.design/hugeicons/artificial-intelligence-03.svg') center / contain no-repeat;
}
</style>
