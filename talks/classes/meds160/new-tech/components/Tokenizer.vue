<script setup>
// Live tokenizer: GPT-4o's real o200k_base vocabulary (via js-tiktoken),
// loaded lazily so the ~2 MB rank table doesn't slow down the rest of the deck.
import { computed, onMounted, ref, shallowRef } from 'vue'

const props = defineProps({
  initial: { type: String, default: "How many r's are in strawberry?" },
  presets: {
    type: Array,
    default: () => ["How many r's are in strawberry?", 'strawberry', 'Poughkeepsie', 'antidisestablishmentarianism'],
  },
})

const text = ref(props.initial)
const enc = shallowRef(null)
const showIds = ref(false)

onMounted(async () => {
  const [{ Tiktoken }, { default: ranks }] = await Promise.all([
    import('js-tiktoken/lite'),
    import('js-tiktoken/ranks/o200k_base'),
  ])
  enc.value = new Tiktoken(ranks)
})

const tokens = computed(() => {
  if (!enc.value) return []
  return enc.value.encode(text.value).map(id => ({ id, text: enc.value.decode([id]) }))
})
const blur = e => e.currentTarget.blur()
</script>

<template>
  <div class="tk">
    <input v-model="text" class="field" spellcheck="false" placeholder="Type anything…">
    <div class="presets">
      <button v-for="p in presets" :key="p" @click="text = p; blur($event)">{{ p }}</button>
      <button class="ghost" @click="showIds = !showIds; blur($event)">{{ showIds ? 'show text' : 'show what the model sees' }}</button>
    </div>

    <div class="chips">
      <span v-if="!enc" class="loading">loading tokenizer…</span>
      <span v-for="(t, i) in tokens" :key="i" class="chip" :class="`c${i % 5}`">
        {{ showIds ? t.id : t.text.replace(/ /g, '·') }}
      </span>
    </div>

    <p class="stat">
      <b>{{ text.length }}</b> characters → <b>{{ tokens.length }}</b> tokens
      <span class="fine">· GPT-4o's tokenizer (o200k_base), running live</span>
    </p>
  </div>
</template>

<style scoped>
.tk { display: grid; gap: 0.8rem; max-width: 46rem; }
.field {
  font: inherit; font-size: 1.3rem; padding: 0.5rem 0.8rem; border-radius: 8px;
  background: var(--fenbrook-bg-elev); color: var(--fenbrook-fg); border: 1px solid var(--fenbrook-rule);
}
.field:focus { outline: none; border-color: var(--fenbrook-accent); }
.presets { display: flex; flex-wrap: wrap; gap: 0.4rem; }
.chips { display: flex; flex-wrap: wrap; gap: 0.3rem; min-height: 2.6rem; align-items: center; }
.chip {
  font-family: 'JetBrains Mono', monospace; font-size: 1.05rem; white-space: pre;
  padding: 0.25rem 0.5rem; border-radius: 5px; color: var(--fenbrook-bg);
}
.c0 { background: #e0a87c; } .c1 { background: #9fc4b0; } .c2 { background: #c7a9d9; }
.c3 { background: #e6cf8a; } .c4 { background: #9cb8db; }
.loading { color: var(--fenbrook-muted); font-style: italic; }
.stat { margin: 0; font-family: 'JetBrains Mono', monospace; font-size: 0.85rem; color: var(--fenbrook-fg-soft); }
.stat b { color: var(--fenbrook-accent); }
.fine { color: var(--fenbrook-muted); font-size: 0.7rem; }
button {
  font: inherit; font-size: 0.75rem; cursor: pointer; padding: 0.25rem 0.6rem; border-radius: 6px;
  border: 1px solid var(--fenbrook-rule); background: transparent; color: var(--fenbrook-fg-soft);
}
button:hover { border-color: var(--fenbrook-accent); color: var(--fenbrook-fg); }
button.ghost { border-style: dashed; }
</style>
