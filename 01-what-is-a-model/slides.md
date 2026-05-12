---
theme: default
title: What is a model?
info: |
  ## What is a model?
  An introduction to computational cognitive modeling.
class: text-center
transition: slide-left
---

# What is a model?

<div class="mt-8 text-left max-w-xl mx-auto">

- What purposes does a model serve?
- What qualities does a model have?
- What properties are desirable for models?

</div>

---
layout: section
---

# Why model?

---
layout: quote
---

> The essential purpose of cognitive modeling is to allow investigation of the implications of ideas, beyond the limits of human thinking. Models allow the exploration of the implications of ideas that cannot be fully explored by thought alone. As such, they are vehicles for scientific discovery, in much the same way as experiments on human (or other) participants. But the discoveries take a particular form: A system with a particular set of specified properties has another set of properties that arise from those in the specified set as consequences. From observations of this type, we then attempt to draw implications for the nature of human cognition. Alas, such inferences are under-constrained, and there is often room for differences of opinion concerning the meaning of the outcome of a given investigation. The implication of this is not that models are useless, but that care in interpreting their successes and failures, as well as further investigation, is usually required. This makes modeling an ongoing process, just like other aspects of science.

— Jay McClelland

---
layout: section
---

# Theory and data

---

# Theory and data

<div class="theory-data-diagram">

  <svg class="diagram-arrows" viewBox="0 0 960 540" preserveAspectRatio="xMidYMid meet">
    <defs>
      <marker id="arrowhead" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">
        <path d="M 0 0 L 10 5 L 0 10 Z" fill="currentColor" />
      </marker>
    </defs>
    <!-- bidirectional arcs between data and theory boxes (always visible) -->
    <path class="arc arc-top" d="M 620 248 Q 482 130 345 248" />
    <path class="arc arc-bottom" d="M 345 292 Q 482 410 620 292" />

    <!-- prediction-flow arrows: theory → predicted data → data (visible on click 1) -->
    <g v-click="1" class="flow flow-predict">
      <path d="M 700 215 C 700 150 620 100 542 100" />
      <path d="M 416 100 C 340 100 240 150 240 212" />
    </g>

    <!-- observation-flow arrows: observations → data → theory (visible on click 2) -->
    <g v-click="2" class="flow flow-observe">
      <path d="M 416 440 C 340 440 240 380 240 328" />
      <path d="M 345 292 Q 482 410 620 292" />
    </g>
  </svg>

  <div class="diagram-box box-data">data &amp; experiments</div>
  <div class="diagram-box box-theory">theory &amp; models</div>

  <div v-click="1" class="datapoints datapoints-top">
    <div class="datapoint">a</div>
    <div class="datapoint">b</div>
    <div class="datapoint">c</div>
    <div class="datapoint">d</div>
  </div>
  <div v-click="1" class="diagram-label label-top">
    What would happen if…?
  </div>

  <div v-click="2" class="datapoints datapoints-bottom">
    <div class="datapoint">a</div>
    <div class="datapoint">b</div>
    <div class="datapoint">c</div>
    <div class="datapoint">d</div>
  </div>
  <div v-click="2" class="diagram-label label-bottom">
    Which model best explains…?
  </div>

</div>

<style scoped>
.theory-data-diagram {
  position: relative;
  width: 100%;
  aspect-ratio: 960 / 540;
  margin-top: 1rem;
}
.diagram-arrows {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  pointer-events: none;
  color: currentColor;
  opacity: 0.7;
}
.diagram-arrows path {
  fill: none;
  stroke: currentColor;
  stroke-width: 2;
  marker-end: url(#arrowhead);
}
.diagram-box {
  position: absolute;
  top: 39.3%;
  width: 25.8%;
  padding: 0.5rem 0.75rem;
  border: 2px solid currentColor;
  border-radius: 0.6rem;
  background: var(--slidev-theme-bg, transparent);
  text-align: center;
  font-weight: 600;
}
.box-data   { left: 10.1%; }
.box-theory { left: 64.6%; }
.datapoints {
  position: absolute;
  left: 43.3%;
  width: 13.1%;
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
  font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
}
.datapoints-top    { top: 3.3%; }
.datapoints-bottom { top: 62.9%; }
.datapoint {
  border: 1px solid currentColor;
  border-radius: 0.3rem;
  padding: 0.15rem 0.4rem;
  text-align: center;
  background: var(--slidev-theme-bg, transparent);
}
.diagram-label {
  position: absolute;
  font-style: italic;
}
.label-top    { top: 13.7%; right: 4%; }
.label-bottom { top: 73.5%; right: 4%; }
</style>

---
layout: section
---

# What are computational cognitive models?

---
layout: cover
---

# What kind of thing is a mind?

<div class="mt-8">
  <img src="./brain.png" class="mx-auto max-h-80" alt="Brain" />
</div>

---
layout: two-cols-header
---

# A scene

::left::

<img src="./scene.png" class="max-h-96" alt="Scene with people" />

<div class="text-sm opacity-60 mt-2">Adapted from Shimon Edelman</div>

::right::

<v-clicks>

- **kid**
- **ball**
- **adult**
- **adult**
- **dog**

</v-clicks>

---

# What kind of thing is a mind?

<v-clicks>

- It's not what it is made of.
- It's what it does, and how it relates to the world.
- How do we describe these functions and relationships?

</v-clicks>

---

# The language of computation

<v-clicks>

- We can use the language of **computation**.
- Theory of computation gives us a rich set of formal tools to think about **processes** (aka algorithms!) and how they work.

</v-clicks>

---

# Levels of analysis

<div class="grid grid-cols-3 gap-8 mt-8">

<div class="p-6 rounded border">

### Computational

What computational problem is being solved?

</div>

<div class="p-6 rounded border">

### Algorithmic

What computational processes are used?

</div>

<div class="p-6 rounded border">

### Implementational

How is the process implemented?

</div>

</div>

---
layout: section
---

# This semester

---

# This semester

<div class="text-2xl mt-8">

Neural networks from **1943 → 2025**.

</div>

<div class="mt-12 max-w-3xl">

How has the development of neural network models over the past 80 years influenced how we think about the mind?

</div>

---

# Course structure

- **Tuesdays** — a new technique or model type.
- **Thursdays** — discuss a paper that uses that technique.
- **Fridays** — lab for hands-on work, typically building the model from Thursday's paper.

---

# Assignments

- **Weekly labs** — 55% of grade. Skill-building activities, not evaluations of your ability to code.
- **Course project** — 30% of grade.
- **Participation** — 15% of grade.

---
layout: center
---

# Before next class

- Fill out the **pre-course survey** on Moodle.
- Sign up for a free **Google Colab Pro** account. Link on Moodle.

---
layout: end
---

# Thank you
