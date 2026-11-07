---
theme: fenbrook
title: Creating a model
info: |
  ## Creating a model
  COGS 319, day 2: generalization data from McGuire (1961) and Shepard's
  universal law of generalization (1987).
transition: fade
themeConfig:
  course: COGS 319
  event: Creating a model
layout: cover
---

# Creating a model

::speaker::
Josh de Leeuw

::event::
COGS 319 · Spring 2027

---
layout: center
width: 100%
---

<div class="qr-slide">
  <QRCode href="https://cogsciresearch.vassar.edu/319/categorization/" :size="300" />
  <p><a href="https://cogsciresearch.vassar.edu/319/categorization/">https://cogsciresearch.vassar.edu/319/categorization/</a></p>
</div>

<style scoped>
.qr-slide { display: flex; flex-direction: column; align-items: center; gap: 1.5rem; }
.qr-slide p { font-size: 1.4rem; margin: 0; white-space: nowrap; }
</style>

---
layout: center
width: 100%
---

<script setup>
const base = import.meta.env.BASE_URL
</script>

<div class="cat-figure">
  <img :src="base + 'images/categorization-results.png'" alt="Scatter plot of class categorization responses: a cloud of red points on the left and a cloud of teal points on the right, each with a black center point. In each corner is an example stimulus, a circle with a line through it: small circles on the left, large circles on the right, with the line tilted one way at the top and the other way at the bottom." />
  <svg viewBox="265.2 55.6 429.6 428.9" aria-hidden="true">
    <g fill="none" stroke="#1a1a1a">
      <circle cx="296.1" cy="121.9" r="21.7" stroke-width="1" />
      <line x1="284.9" y1="103.4" x2="307.4" y2="140.6" stroke-width="1" />
      <circle cx="296.1" cy="392.2" r="21.7" stroke-width="1" />
      <line x1="307.7" y1="373.7" x2="284.6" y2="410.6" stroke-width="1" />
      <circle cx="642.8" cy="122.0" r="31.5" stroke-width="1.45" />
      <line x1="626.5" y1="94.9" x2="659.0" y2="148.8" stroke-width="1.45" />
      <circle cx="642.7" cy="392.1" r="31.3" stroke-width="1.45" />
      <line x1="659.4" y1="365.6" x2="626.1" y2="418.7" stroke-width="1.45" />
    </g>
  </svg>
</div>

<style scoped>
.cat-figure {
  position: relative;
  height: 400px;
  aspect-ratio: 429.6 / 428.9;
  margin: 0 auto;
}
.cat-figure img,
.cat-figure svg {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
}
</style>

---
clicks: 5
---

<script setup>
const _specs = import.meta.glob('./diagrams/*.json', { eager: true, import: 'default' })
const spec = _specs['./diagrams/mcguire-1961.json']
</script>

<Diagram class="mcguire mcguire-theme" :spec="spec" />

<p class="cite">McGuire (1961)</p>

<style scoped>
.mcguire.mcguire-theme { width: 100%; }
.mcguire.mcguire-theme :deep(.box-screen rect) { fill: #f4f1ea; stroke: none; }
.mcguire.mcguire-theme :deep(.box-dot ellipse) { fill: #1f1d1b; stroke: none; }
.mcguire.mcguire-theme :deep(.box-num rect) { fill: none; stroke: none; }
.mcguire.mcguire-theme :deep(.box-num text) { fill: #1f1d1b; }
.cite { text-align: right; color: var(--fenbrook-fg-soft); margin-top: 0.75rem; }
</style>

<!--
Experiment was an association learning experiment, focused on other questions, but Shepard used it to get generalization errors.

Participants saw circle 2s, then three digit number 2s. Had to guess the number.
-->

---
layout: media
side: left
---

<script setup>
const base = import.meta.env.BASE_URL
</script>

# Shepard's Universal Law of Generalization

Shepard (1987)

::media::

<img :src="base + 'images/shepard-1987-generalization.png'" alt="Twelve panels (A to L) from Shepard (1987), each plotting the empirical measure of generalization against distance in psychological space. Every panel follows the same exponential decay. Panels: sizes of circles; lightnesses and saturations; positions in a linear array; sizes and lightnesses of squares; spectral hues (pigeon data); consonant phonemes; sizes and shapes of triangles; spectral hues (pigeon data); vowel phonemes; free-form shapes; spectral hues (human data); Morse code signals." />
