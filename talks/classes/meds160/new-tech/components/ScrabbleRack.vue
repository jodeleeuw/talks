<script setup>
// A Scrabble rack: drag tiles to reorder them, or shuffle. Rearranging the
// tiles is part of how players search for words (Clark & Chalmers 1998).
import { ref } from 'vue'

const props = defineProps({
  letters: { type: String, default: 'SIPATRE' }, // → PIRATES, PARTIES, TRAIPSE
})

const SCORE = { A: 1, B: 3, C: 3, D: 2, E: 1, F: 4, G: 2, H: 4, I: 1, J: 8, K: 5, L: 1, M: 3, N: 1, O: 1, P: 3, Q: 10, R: 1, S: 1, T: 1, U: 1, V: 4, W: 4, X: 8, Y: 4, Z: 10 }
let uid = 0
const tiles = ref([...props.letters.toUpperCase()].map(ch => ({ id: uid++, ch })))
const dragging = ref(null)
const rack = ref(null)

function down(e, t) {
  dragging.value = t.id
  e.currentTarget.setPointerCapture(e.pointerId)
}
function move(e) {
  if (dragging.value == null) return
  // find the slot under the pointer from the tiles' on-screen positions
  const root = rack.value?.$el ?? rack.value // TransitionGroup ref is a component
  const els = [...root.querySelectorAll('.tile')]
  const from = tiles.value.findIndex(t => t.id === dragging.value)
  let to = els.findIndex((el) => {
    const r = el.getBoundingClientRect()
    return e.clientX < r.left + r.width / 2
  })
  if (to === -1) to = els.length - 1
  else if (to > from) to -= 1
  if (to !== from) {
    const next = [...tiles.value]
    const [t] = next.splice(from, 1)
    next.splice(to, 0, t)
    tiles.value = next
  }
}
function up() { dragging.value = null }

function shuffle(e) {
  const next = [...tiles.value]
  for (let i = next.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [next[i], next[j]] = [next[j], next[i]]
  }
  tiles.value = next
  e.currentTarget.blur()
}
</script>

<template>
  <div class="sr">
    <TransitionGroup ref="rack" tag="div" name="slide" class="rack" @pointermove="move" @pointerup="up" @pointercancel="up">
      <div
        v-for="t in tiles" :key="t.id"
        :class="['tile', { lift: dragging === t.id }]"
        @pointerdown="down($event, t)"
      >
        {{ t.ch }}<sub>{{ SCORE[t.ch] }}</sub>
      </div>
    </TransitionGroup>
    <div class="shelf" />
    <button @click="shuffle">shuffle</button>
  </div>
</template>

<style scoped>
.sr { display: flex; flex-direction: column; align-items: center; gap: 0 !important; }
.sr > * { margin: 0 !important; }
.rack { display: flex; gap: 0.5rem; padding: 0 1rem; touch-action: none; user-select: none; }
.tile {
  position: relative; width: 4.2rem; height: 4.2rem; display: grid; place-items: center;
  font-family: Georgia, 'Times New Roman', serif; font-weight: 700; font-size: 2.4rem; color: #2b2116;
  background: linear-gradient(160deg, #f4e2bd, #e2c48d); border-radius: 6px;
  box-shadow: 0 2px 0 #b8955a, 0 4px 8px rgba(0, 0, 0, 0.35);
  cursor: grab; transition: transform 0.15s, box-shadow 0.15s;
}
.tile sub { position: absolute; right: 0.35rem; bottom: 0.2rem; font-size: 0.8rem; font-family: inherit; }
.tile.lift { cursor: grabbing; transform: translateY(-10px) rotate(-3deg); box-shadow: 0 2px 0 #b8955a, 0 14px 18px rgba(0, 0, 0, 0.45); z-index: 2; }
.slide-move { transition: transform 0.2s ease; }
.sr .shelf { width: calc(7 * 4.7rem + 2rem); height: 0.9rem; margin-top: 0.25rem !important; border-radius: 3px; background: linear-gradient(#6b4a2b, #4a3220); box-shadow: 0 4px 8px rgba(0, 0, 0, 0.4); }
.sr button {
  margin-top: 1.4rem !important; font: inherit; font-size: 0.85rem; line-height: 1.2; height: auto; min-height: 0; cursor: pointer; padding: 0.35rem 1rem !important; border-radius: 6px;
  border: 1px solid var(--fenbrook-rule); background: transparent; color: var(--fenbrook-fg-soft);
}
.sr button:hover { border-color: var(--fenbrook-accent); color: var(--fenbrook-fg); }
</style>
