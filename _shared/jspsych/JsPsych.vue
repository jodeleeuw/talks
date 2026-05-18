<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount, watch } from 'vue'

const props = withDefaults(defineProps<{
  timeline: any[]
  // The jsPsych runtime is injected so this component stays dependency-free.
  // The talk-local wrapper imports `initJsPsych` from `jspsych` and passes it here.
  initJsPsych: (opts: Record<string, any>) => any
  autostart?: boolean
}>(), {
  autostart: true,
})

const root = ref<HTMLDivElement | null>(null)
let jsPsych: any = null

async function run() {
  if (!root.value) return
  if (jsPsych) {
    try { jsPsych.abortExperiment() } catch {}
    jsPsych = null
  }
  root.value.innerHTML = ''
  jsPsych = props.initJsPsych({
    display_element: root.value,
  })
  try {
    await jsPsych.run(props.timeline)
  } catch (e) {
    console.error('jsPsych timeline error:', e)
  }
}

onMounted(() => {
  if (props.autostart) run()
})

onBeforeUnmount(() => {
  try { jsPsych?.abortExperiment() } catch {}
  jsPsych = null
})

watch(() => props.timeline, () => {
  if (props.autostart) run()
})

defineExpose({ run })
</script>

<template>
  <div ref="root" class="jspsych-host"></div>
</template>

<style scoped>
.jspsych-host {
  width: 100%;
  height: 100%;
  position: relative;
}

.jspsych-host :deep(.jspsych-display-element) {
  width: 100%;
  height: 100%;
  background: transparent;
  color: inherit;
  font-family: inherit;
}
.jspsych-host :deep(.jspsych-content-wrapper) {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
}
.jspsych-host :deep(.jspsych-content) {
  max-width: 100%;
  max-height: 100%;
  margin: 0;
  text-align: center;
  color: inherit;
}
.jspsych-host :deep(img) {
  max-width: 100%;
  max-height: 100%;
}
</style>
