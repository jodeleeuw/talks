<script setup>
// RLHF demo: the room votes between two replies, round by round. At the end
// it shows what the reward model learned, i.e. what this audience rewards.
import { computed, ref } from 'vue'

const props = defineProps({
  rounds: {
    type: Array,
    default: () => [
      {
        prompt: 'I wrote a poem. Is it good?',
        a: "It's wonderful! You're a natural poet.",
        b: 'The opening image is striking. The middle loses its rhythm. Try reading it aloud.',
        learnA: 'reward flattery', learnB: 'reward candor',
      },
      {
        prompt: 'How long should I boil an egg?',
        a: 'About 6–7 minutes for jammy, 10–12 for hard-boiled.',
        b: "Great question! Eggs have been a staple of human diets for millennia, and the art of boiling them is surprisingly rich. Before we begin, let's consider…",
        learnA: 'reward getting to the point', learnB: 'reward elaborate preambles',
      },
      {
        prompt: 'Will it rain in Poughkeepsie next Saturday?',
        a: 'Yes, it will rain on Saturday.',
        b: "I can't know that yet. A forecast will be reliable a few days out.",
        learnA: 'reward confident guesses', learnB: 'reward admitting uncertainty',
      },
    ],
  },
})

const i = ref(0)
const votes = ref([])
const done = computed(() => i.value >= props.rounds.length)
const round = computed(() => props.rounds[i.value])

function vote(which, e) {
  const r = round.value
  votes.value.push({ which, learned: which === 'a' ? r.learnA : r.learnB })
  i.value++
  e?.currentTarget?.blur?.()
}
function reset(e) {
  i.value = 0
  votes.value = []
  e?.currentTarget?.blur?.()
}
</script>

<template>
  <div class="pv">
    <template v-if="!done">
      <span class="tag">round {{ i + 1 }} / {{ rounds.length }}</span>
      <div class="chat"><p class="bubble">{{ round.prompt }}</p></div>
      <div class="pair">
        <button class="reply" @click="vote('a', $event)"><span class="ab">A</span>{{ round.a }}</button>
        <button class="reply" @click="vote('b', $event)"><span class="ab">B</span>{{ round.b }}</button>
      </div>
    </template>
    <div v-else class="end">
      <p>You just trained a <b>reward model</b>. It learned to:</p>
      <ul class="learned">
        <li v-for="(v, k) in votes" :key="k">{{ v.learned }}</li>
      </ul>
      <p class="sub">The chatbot is then optimized to produce whatever this room rewarded.</p>
      <button class="ghost" @click="reset">Run again</button>
    </div>
  </div>
</template>

<style scoped>
.pv { font-size: 0.95rem; max-width: 46rem; margin: 0 auto; text-align: left; }
/* The user's prompt as a right-aligned chat bubble. */
.chat { display: flex; justify-content: flex-end; margin: 0 0 0.9rem; }
.bubble {
  margin: 0; max-width: 75%; font-size: 1.15rem; line-height: 1.35; padding: 0.6rem 1rem;
  border-radius: 18px 18px 4px 18px; color: var(--fenbrook-fg);
  background: color-mix(in srgb, var(--fenbrook-accent) 22%, var(--fenbrook-bg-elev));
}
.tag { display: block; font-family: 'JetBrains Mono', monospace; font-size: 0.65rem; letter-spacing: 0.04em; text-transform: uppercase; color: var(--fenbrook-muted); margin-bottom: 0.3rem; }
.pair { display: grid; grid-template-columns: 1fr 1fr; gap: 0.8rem; }
.reply {
  font: inherit; font-size: 0.9rem; text-align: left; line-height: 1.4; cursor: pointer;
  padding: 0.8rem 1rem; border-radius: 10px; min-height: 7rem;
  border: 1px solid var(--fenbrook-rule); background: var(--fenbrook-bg-elev); color: var(--fenbrook-fg-soft);
  transition: border-color 0.2s;
}
.reply:hover { border-color: var(--fenbrook-accent); color: var(--fenbrook-fg); }
.ab { display: block; font-family: 'JetBrains Mono', monospace; font-weight: 700; color: var(--fenbrook-accent); margin-bottom: 0.3rem; }
.end { text-align: center; }
.end p { margin: 0 0 0.4rem; font-size: 1.3rem; color: var(--fenbrook-fg); }
.end b { color: var(--fenbrook-accent); }
.end .sub { font-size: 0.95rem; color: var(--fenbrook-fg-soft); margin: 1rem 0; }
.learned { list-style: none !important; padding: 0 !important; margin: 0.8rem 0 0; display: grid; gap: 0.5rem; justify-items: center; }
/* !important: the panel layout's list rules otherwise win on margin and color. */
.learned li { font-size: 1.3rem; color: var(--fenbrook-accent) !important; margin: 0 !important; }
button.ghost {
  font: inherit; font-size: 0.85rem; cursor: pointer; padding: 0.35rem 0.9rem; border-radius: 6px;
  background: transparent; color: var(--fenbrook-fg-soft); border: 1px solid var(--fenbrook-rule);
}
</style>
