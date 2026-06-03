---
theme: fenbrook
title: Agentic AI for Science
info: A why-to & how-to guide for researchers
transition: fade
themeConfig:
  event: URSI 2026
  accentIcons:
    - mingcute:chat-4-ai-line
    - material-symbols:science-outline
    - uil:science
layout: cover
---

# Agentic AI for Science

A why-to & how-to guide for researchers

::speaker::

Josh de Leeuw - Cognitive Science

::event::

URSI Workshop 2026

---
layout: image-right
image: images/chatgpt.png
---

# Our <Hi>introduction</Hi> to AI shaped our expectations of AI.

---
layout: center
width: 30vw
---

# Agentic systems unlock a whole set of capabilities. 

You can <Hi>talk</Hi> to your computer. You can <Hi>teach</Hi> your computer.


---

# Goals for today: 

<v-clicks>

1. Gain a high-level understanding of how these tools work.
2. Explore potential applications.
3. Learn how to manage these tools to maximize their benefit.
4. Worry a bit about how this impacts scientific research.

</v-clicks>

---
clicks: 8
---

# How Large Language Models (LLMs) learn

<script setup>
const sentence = ['The', 'quick', 'brown', 'fox', 'jumps', 'over', 'the', 'lazy', 'dog']
const rest = sentence.slice(1)
</script>

<div class="next-token">
  <span class="token">The</span>
  <template v-for="(word, i) in rest" :key="i">
    <span class="slot" :style="{ minWidth: word.length * 0.62 + 'em' }">
      <span class="word" v-click>{{ word }}</span>
    </span>
  </template>
  <span class="token">.</span>
</div>

<style scoped>
.next-token {
  display: flex;
  flex-wrap: wrap;
  align-items: flex-end;
  gap: 0.5em;
  font-size: 2rem;
}
.token { line-height: 1.6; }
.slot {
  display: inline-block;
  border-bottom: 3px solid var(--fenbrook-accent);
  line-height: 1.6;
  text-align: center;
}
</style>

---
layout: panel
clicks: 2
---

# How an LLM is built

<script setup>
const llmSpec = {
  w: 960, h: 470,
  boxes: [
    { id: 'pre',  shape: 'roundRect', x: 25,  y: 40, w: 270, h: 92, text: 'Pre-training' },
    { id: 'post', shape: 'roundRect', x: 345, y: 40, w: 270, h: 92, text: 'Supervised fine-tuning', wrap: true },
    { id: 'rlhf', shape: 'roundRect', x: 665, y: 40, w: 270, h: 92, text: 'Preference tuning' },

    { shape: 'roundRect', x: 25,  y: 142, w: 270, h: 4, fill: 'var(--fenbrook-accent)', strokeWidth: 0, reveal: { from: 0, to: 0 } },
    { shape: 'roundRect', x: 345, y: 142, w: 270, h: 4, fill: 'var(--fenbrook-accent)', strokeWidth: 0, reveal: { from: 1, to: 1 } },
    { shape: 'roundRect', x: 665, y: 142, w: 270, h: 4, fill: 'var(--fenbrook-accent)', strokeWidth: 0, reveal: { from: 2, to: 2 } },

    { id: 'aside', shape: 'roundRect', x: 25, y: 185, w: 910, h: 250,
      fill: 'var(--fenbrook-bg-elev)', wrap: true, maxWidth: 820, fontSize: 28,
      strokeWidth: 0,
      textByClick: {
        '0': ['Predict the next token across trillions of words of text.'],
        '1': ['Train on curated examples. Often this includes many examples of instructions paired with good answers. This teaches the model to follow a request and respond in a helpful, consistent format.'],
        '2': ['Humans rank competing responses; a reward model learns their taste. The model is then optimized to produce responses people prefer.']
      }
    }
  ],
  connectors: [
    { from: 'pre.right',  to: 'post.left' },
    { from: 'post.right', to: 'rlhf.left' }
  ]
}
</script>

<Diagram :spec="llmSpec" />

---
layout: center
---

# Is it all next token prediction?

Yes, <Hi>but...</Hi>

---
layout: aside
sidebarScale: 0.6
---

# In-context learning

You can teach the LLM by giving it more information about your task. The ecosystem is settling on the format of <Hi>skill files</Hi>.

::sidebar::

## Example skill - Download Google Slides

<RawText src="text/sample-skill.md" />

---
layout: media
side: left
bleed: true
---

<script setup>
const base = import.meta.env.BASE_URL
</script>

<p style="font-size: 2rem">Access to a terminal + coding skills =</p>

<h1 style="font-size: 2.8rem">a <Hi>general-purpose</Hi> computer user</h1>

::media::

<img :src="base + 'images/terminal.svg'" alt="An agent session driven by plain-English prompts" />

---
layout: quote
---

Pretty much 100% of our code is written by Claude [...] For me personally it has been 100% for two+ months now, I don’t even make small edits by hand. I shipped 22 [pull requests] yesterday and 27 the day before, each one 100% written by Claude. 

::attribution::

Boris Cherney, *Anthropic* (Jan 2026)

---
layout: two-cols-header
clicks: 6
---

# Agentic AI = Model + Harness

::left::

## The model

<p v-click="1">The trained LLM that predicts the next token.</p>

<p v-click="2">Examples include Claude Opus 4.8 · GPT 5 · Gemini 3.5 Flash · Llama 70B</p>

<p v-click="3">Varies in capability, speed, and cost.</p>

::right::

## The harness

<p v-click="4">The software wrapped around the model: it runs the agent loop, hands the model tools, manages its context, and connects it to your files and terminal.</p>

<p v-click="5">Examples include Claude Code · Antigravity · OpenClaw · OpenCode</p>

<p v-click="6">Varies in user interface, memory capabilities, level of autonomy, etc.</p>

---
layout: media
side: right
clicks: 3
---

# Models can be trained to generate tool calls

::media::

<div class="lane">
  <div class="turn">
    <div class="role">User</div>
    <p class="msg">How many data files are there from session 3?</p>
  </div>
  <div class="turn" v-click="1">
    <div class="role">Model <span class="note">— doesn't answer; requests an action</span></div>
    <pre class="toolcall">{
  <span class="k">"tool"</span>: <span class="s">"bash"</span>,
  <span class="k">"command"</span>: <span class="s">"ls data/session-3/*.csv | wc -l"</span>
}</pre>
  </div>
  <div class="turn" v-click="2">
    <div class="role">Harness <span class="note">— runs it; hands back the result</span></div>
    <pre class="result" style>12</pre>
  </div>
  <div class="turn" v-click="3">
    <div class="role">Model <span class="note">— reads result; generates response</span></div>
    <p class="msg">There are 12 data files from session 3.</p>
  </div>
</div>

<style scoped>
.lane {
  display: flex;
  flex-direction: column;
  gap: 1.3rem;
  width: 100%;
  padding: 1.6rem 1.8rem;
}
.role {
  font-family: 'JetBrains Mono', ui-monospace, monospace;
  font-size: 0.72rem;
  text-transform: uppercase;
  letter-spacing: 0.12em;
  color: var(--fenbrook-accent);
  margin-bottom: 0.35rem;
}
.role .note {
  color: var(--fenbrook-fg-soft);
  text-transform: none;
  letter-spacing: 0;
}
.msg {
  font-size: 1.1rem;
  line-height: 1.5;
  color: var(--fenbrook-fg);
  margin: 0;
}
.toolcall, .result {
  margin: 0;
  padding: 0.7rem 1rem;
  background: var(--fenbrook-bg-elev);
  border-left: 3px solid var(--fenbrook-accent);
  border-radius: 4px;
  font-family: 'JetBrains Mono', ui-monospace, monospace;
  font-size: 0.6rem;
  line-height: 1.45;
  white-space: pre;
}
.toolcall .k { color: var(--fenbrook-accent); }
.toolcall .s { color: var(--fenbrook-fg-soft); }
.result { display: inline-block; }
</style>

---
layout: aside
sidebarScale: 0.8
---

# What stops the agent from taking unwanted actions?

Almost all tool calls are opt-in. Most harnesses are adopting a <Hi>sandbox mode</Hi>.

::sidebar::

## /sandbox mode

The agent's commands run in a locked-down environment:

- Only files in the sandbox can be read and modified.
- Network access is blocked by default.
- Anything that goes outside the sandbox has to ask first.

This gives the agent broad permissions in a narrow environment.


---

# What leaves your computer?

<p>Only what the <Hi>model sees</Hi>: your *prompts*, the *files it opens*, and the *output of commands it runs*. Everything else stays untouched.</p>

<p v-click>A <Hi>local model</Hi> keeps all of it on your disk.</p>

---
layout: center
footer: false
---

<script setup>
const base = import.meta.env.BASE_URL
</script>

<div class="ag">
  <img :src="base + 'images/Google-Antigravity-Icon-Full-Color.png'" alt="Antigravity" class="ag-icon" />
  <h1 class="ag-word">Antigravity</h1>
  <a class="ag-link" href="https://antigravity.google" target="_blank" rel="noopener">↓ antigravity.google</a>
</div>

<style scoped>
.ag {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 1rem;
}
.ag-icon {
  width: 200px;
  height: auto;
}
.ag-word {
  margin: 0;
  font-size: 3.4rem;
  font-weight: 600;
  letter-spacing: -0.02em;
  color: var(--fenbrook-fg);
}
.ag-tag {
  margin: 0;
  font-size: 1.3rem;
  color: var(--fenbrook-fg-soft);
}
.ag-link {
  font-family: 'JetBrains Mono', ui-monospace, monospace;
  font-size: 1.3rem;
  color: var(--fenbrook-bg);
  background: var(--fenbrook-accent);
  padding: 0.6rem 1.5rem;
  border-radius: 999px;
  text-decoration: none;
}
</style>

---

<p style="font-family:'JetBrains Mono',ui-monospace,monospace;font-size:0.75rem;text-transform:uppercase;letter-spacing:0.14em;color:var(--fenbrook-accent);margin:0 0 0.6rem">Tips for new users · 1 / 4</p>

# Treat it like a skilled collaborator who doesn't know your project.

Give it the goal and enough context, and it fills in the rest. Hand it <Hi>"here's the problem"</Hi> and it goes looking for a solution.

---

<p style="font-family:'JetBrains Mono',ui-monospace,monospace;font-size:0.75rem;text-transform:uppercase;letter-spacing:0.14em;color:var(--fenbrook-accent);margin:0 0 0.6rem">Tips for new users · 2 / 4</p>

# Sessions end. Files are forever.

Use files for long-term memory in a project. New sessions reset the context.


---

<p style="font-family:'JetBrains Mono',ui-monospace,monospace;font-size:0.75rem;text-transform:uppercase;letter-spacing:0.14em;color:var(--fenbrook-accent);margin:0 0 0.6rem">Tips for new users · 3 / 4</p>

# Manage the context

The context can enhance the agent's capabilities, but it can also add unnecessary resource usage. Use tools like `/clear` and `/compact` to control the context.

---

<p style="font-family:'JetBrains Mono',ui-monospace,monospace;font-size:0.75rem;text-transform:uppercase;letter-spacing:0.14em;color:var(--fenbrook-accent);margin:0 0 0.6rem">Tips for new users · 4 / 4</p>

# Shape overall behavior with clear instructions.

Most harnesses have a place where you can add instructions that are read at the start of each session, e.g., <Hi>CLAUDE.md</Hi> or <Hi>AGENTS.md</Hi>.

---
layout: aside
side: right
asideStyle: card
sidebarScale: 0.8
clicks: 5
---

# Come up with a plan for <Hi>verification</Hi>.

One advantage of agents is that they can autonomously check their own work, but they need to know how to do that.

::sidebar::

## Ways to verify

<v-clicks>

- **Define tests** that the agent can run. The agent can help build these.
- **Ask for sources** to verify information.
- **Ask for a written log** for reviewing behavior.
- **Clear context** and ask for a review of the work.

</v-clicks>

---
layout: panel
---

<h1 style="font-size:1.7rem;margin:0 0 0.5rem">Just because we can...</h1>

<div class="count">What parts of the research process should agents help with?</div>

<div class="cats">
<div class="cat"><div class="dom">Research methodology</div><div class="ex">Hypothesis Generation · What-If Oracle · Research Planning</div></div>
<div class="cat"><div class="dom">Scientific communication</div><div class="ex">Paper Writing · Scientific Slides</div></div>
<div class="cat"><div class="dom">Databases &amp; data access</div><div class="ex">Specialized DB Search · Paper Discovery</div></div>
  <div class="cat"><div class="dom">Genomics &amp; RNA-seq</div><div class="ex">Scanpy · PyDESeq2 · BioPython · scVelo</div></div>
  <div class="cat"><div class="dom">Cheminformatics</div><div class="ex">RDKit · DeepChem · DiffDock · OpenMM</div></div>
  <div class="cat"><div class="dom">Proteomics / mass spec</div><div class="ex">pyOpenMS · matchms</div></div>
  <div class="cat"><div class="dom">Clinical &amp; precision medicine</div><div class="ex">ClinVar · DepMap · PyHealth</div></div>
  <div class="cat"><div class="dom">Medical imaging &amp; pathology</div><div class="ex">pydicom · PathML · histolab</div></div>
  <div class="cat"><div class="dom">Neuroscience</div><div class="ex">BIDS · Neuropixels</div></div>
  <div class="cat"><div class="dom">Machine learning</div><div class="ex">PyTorch Lightning · scikit-learn · PyMC · UMAP</div></div>
  <div class="cat"><div class="dom">Materials, chem &amp; physics</div><div class="ex">Pymatgen · Astropy · Qiskit</div></div>
  <div class="cat"><div class="dom">Engineering &amp; simulation</div><div class="ex">SimPy · FluidSim · SymPy</div></div>
  <div class="cat"><div class="dom">Data &amp; visualization</div><div class="ex">Matplotlib · Polars · GeoPandas · NetworkX</div></div>
  <div class="cat"><div class="dom">Lab automation</div><div class="ex">PyLabRobot · Opentrons · Benchling</div></div>
  <div class="cat"><div class="dom">Protein engineering</div><div class="ex">ESM · Adaptyv</div></div>
  <div class="cat"><div class="dom">Infrastructure</div><div class="ex">Modal · DNAnexus · GPU acceleration</div></div>
  <div class="cat"><div class="dom">Compliance</div><div class="ex">ISO 13485 Certification</div></div>
</div>

<div class="links">
  <div class="ref-label">Sources</div>
  <a href="https://github.com/Imbad0202/academic-research-skills" target="_blank" rel="noopener">github.com/Imbad0202/academic-research-skills</a>
  <a href="https://github.com/K-Dense-AI/scientific-agent-skills/tree/main/skills" target="_blank" rel="noopener">github.com/K-Dense-AI/scientific-agent-skills</a>
</div>

<style scoped>
.count { font-size: 0.95rem; color: var(--fenbrook-fg-soft); margin: 0 0 0.7rem; }
.count strong { color: var(--fenbrook-accent); font-weight: 600; }
.cats {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 0.6rem 1.3rem;
}
.cat .dom {
  font-family: 'JetBrains Mono', ui-monospace, monospace;
  font-size: 0.58rem;
  text-transform: uppercase;
  letter-spacing: 0.1em;
  color: var(--fenbrook-accent);
  margin-bottom: 0.12rem;
}
.cat .ex { font-size: 0.72rem; color: var(--fenbrook-fg-soft); line-height: 1.3; }
.links {
  display: flex;
  flex-direction: column;
  gap: 0.05rem;
  margin-top: 0.7rem;
  font-family: 'JetBrains Mono', ui-monospace, monospace;
  font-size: 0.6rem;
  color: var(--fenbrook-fg-soft);
}
.links .ref-label {
  font-size: 0.52rem;
  text-transform: uppercase;
  letter-spacing: 0.14em;
  color: var(--fenbrook-accent);
  margin-bottom: 0.1rem;
}
.links a {
  color: var(--fenbrook-fg-soft);
  text-decoration: none !important;
  border-bottom: none !important;
  width: fit-content;
}
</style>

---

# What does it cost?

Subscriptions (e.g., Claude Pro, Google AI Pro, ChatGPT Pro) are currently $20/mo for the entry tier. 

Pay-as-you-go (per token) is likely more expensive if you use a few times per week.

Local models are free.

---
layout: media
side: right
---

# Agentic AI for Science

A why-to & how-to guide for researchers.

::media::

<QRCode href="https://jodeleeuw.github.io/talks/workshops/ursi-agentic-ai/" caption="Scan for slides"/>
