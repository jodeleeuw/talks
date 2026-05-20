<script setup lang="ts">
import { useSlots } from 'vue'
import FitContent from '../components/FitContent.vue'

withDefaults(defineProps<{
  side?: 'left' | 'right'
  bleed?: boolean
  caption?: string
  // Where the caption sits relative to the media frame. 'bottom' (default)
  // stacks it below; 'right' / 'left' place it beside the frame as a slim
  // sidebar (matches PPTX patterns where a small citation rect sits next to
  // the figure rather than beneath it).
  captionSide?: 'bottom' | 'right' | 'left'
}>(), {
  side: 'right',
  bleed: false,
  captionSide: 'bottom',
})

const slots = useSlots()
</script>

<template>
  <div
    class="slidev-layout josh-media"
    :class="[
      `side-${side}`,
      bleed ? 'bleed' : 'padded',
      `caption-${captionSide}`,
    ]"
  >
    <div class="media-text">
      <FitContent align="center" origin="left center">
        <div class="text-inner">
          <slot />
        </div>
      </FitContent>
    </div>

    <div class="media-column">
      <div class="media-frame">
        <slot v-if="slots.media" name="media" />
      </div>
      <div v-if="caption" class="media-caption">{{ caption }}</div>
    </div>
  </div>
</template>

<style scoped>
.josh-media {
  display: grid;
  grid-template-columns: 1fr 1.15fr;
  gap: 3rem;
  height: 100%;
  overflow: hidden;
}

.josh-media.padded {
  padding: 3rem 4rem 3.5rem;
}

.josh-media.bleed {
  padding: 3rem 0 3.5rem 4rem;
  gap: 3.5rem;
}

.josh-media.side-left {
  grid-template-columns: 1.15fr 1fr;
}
.josh-media.side-left .media-text { order: 2; }
.josh-media.side-left .media-column { order: 1; }
.josh-media.side-left.bleed {
  padding: 3rem 4rem 3.5rem 0;
}

.media-text {
  min-height: 0;
  min-width: 0;
}

.text-inner :deep(h1) {
  font-size: 3.2rem;
  font-weight: 500;
  line-height: 1.12;
  letter-spacing: -0.02em;
  color: var(--josh-fg);
  margin: 0 0 1.5rem;
  max-width: 18ch;
}

.text-inner :deep(h1 em),
.text-inner :deep(h1 strong) {
  color: var(--josh-accent);
}

.text-inner :deep(p) {
  font-size: 1.3rem;
  line-height: 1.5;
  color: var(--josh-fg-soft);
  margin: 0 0 0.9rem;
  max-width: 34ch;
}

.text-inner :deep(p:last-child) {
  margin-bottom: 0;
}

.text-inner :deep(em) {
  color: var(--josh-fg);
  font-style: italic;
}

.text-inner :deep(strong) {
  color: var(--josh-accent);
  font-weight: 600;
}

/* The media column wraps the frame + caption. captionSide='bottom' stacks
   them vertically; 'right'/'left' put the caption beside the frame. */
.media-column {
  position: relative;
  min-height: 0;
  min-width: 0;
  display: flex;
  flex-direction: column;
  justify-content: center;
}

.josh-media.caption-right .media-column {
  flex-direction: row;
  align-items: stretch;
  gap: 0.9rem;
}

.josh-media.caption-left .media-column {
  flex-direction: row-reverse;
  align-items: stretch;
  gap: 0.9rem;
}

/* The frame is the sized box the slot's content fills. `overflow: hidden`
   + `border-radius` round whatever's inside (img, iframe, video, <Youtube>),
   so callers don't need to style their embed for corners. */
.media-frame {
  flex: 1 1 0;
  min-height: 0;
  min-width: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
  border-radius: 6px;
  background: color-mix(in oklab, var(--josh-fg) 4%, transparent);
}

/* Make common embed elements fill the frame by default. Slidev's <Youtube>
   renders as <iframe>, so styling iframe covers it too. <img> defaults to
   `contain` (no cropping) — override per-slide with scoped CSS for `cover`. */
.media-frame :deep(img) {
  width: 100%;
  height: 100%;
  object-fit: contain;
}
.media-frame :deep(iframe),
.media-frame :deep(video) {
  width: 100%;
  height: 100%;
  border: 0;
}

.josh-media.bleed .media-frame {
  border-radius: 0;
  background: transparent;
}

.media-caption {
  flex: 0 0 auto;
  margin-top: 0.6rem;
  font-family: 'JetBrains Mono', ui-monospace, monospace;
  font-size: 0.7rem;
  color: var(--josh-muted);
  letter-spacing: 0.02em;
  text-align: right;
}

/* Side captions: narrow rail beside the frame. No top margin (the row gap
   handles spacing); align to top so a multi-line caption reads as a column
   of metadata rather than a footnote. */
.josh-media.caption-right .media-caption,
.josh-media.caption-left .media-caption {
  margin-top: 0;
  align-self: flex-end;
  max-width: 12rem;
  text-align: left;
  writing-mode: horizontal-tb;
  padding-bottom: 0.4rem;
}
</style>
