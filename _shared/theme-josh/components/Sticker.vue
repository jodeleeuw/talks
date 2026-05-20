<script setup lang="ts">
import { computed } from 'vue'

const props = withDefaults(defineProps<{
  // Required. Unique within the slide. The Slidev drag editor writes
  // updated positions to slide frontmatter under `dragPos[id]`, so the
  // markdown body stays clean even when a slide has many stickers.
  id: string
  src: string
  alt?: string
  // Optional decorative rotation (deg). The drag editor's own rotation
  // (5th element of the `pos` string, set with shift-drag on a handle)
  // composes on top. Use this for a fixed "stuck-on-the-board" tilt.
  rotate?: number | string
  // Optional decorative frame: 'polaroid' adds a white border + shadow.
  frame?: 'none' | 'polaroid' | 'shadow'
  // Explicit size in slide-canvas px. Overrides whatever <v-drag> derives
  // from the `dragPos[id]` w/h. Useful when the dragPos block is missing
  // size (e.g. only "x,y"), and as a safety net so stickers never balloon
  // to the image's natural pixel dimensions.
  w?: number | string
  h?: number | string
}>(), {
  alt: '',
  rotate: 0,
  frame: 'none',
})

const stickerStyle = computed(() => {
  const deg = typeof props.rotate === 'string' ? parseFloat(props.rotate) : props.rotate
  const out: Record<string, string> = {}
  if (deg) out.transform = `rotate(${deg}deg)`
  if (props.w != null) out.width = typeof props.w === 'number' ? `${props.w}px` : props.w
  if (props.h != null) out.height = typeof props.h === 'number' ? `${props.h}px` : props.h
  return Object.keys(out).length ? out : null
})
</script>

<template>
  <v-drag :pos="id">
    <div class="josh-sticker" :class="`josh-sticker--${frame}`" :style="stickerStyle">
      <img :src="src" :alt="alt" />
    </div>
  </v-drag>
</template>

<style scoped>
.josh-sticker {
  width: 100%;
  height: 100%;
  display: block;
  user-select: none;
}

.josh-sticker img {
  width: 100%;
  height: 100%;
  object-fit: contain;
  display: block;
  pointer-events: none;
  -webkit-user-drag: none;
}

.josh-sticker--polaroid {
  background: #fafafa;
  padding: 6% 6% 14% 6%;
  box-shadow: 0 8px 22px rgba(0, 0, 0, 0.35);
}

.josh-sticker--shadow {
  filter: drop-shadow(0 6px 14px rgba(0, 0, 0, 0.35));
}
</style>
