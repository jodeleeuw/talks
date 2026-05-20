<script setup lang="ts">
withDefaults(defineProps<{
  headers: string[]
  rows: (string | number)[][]
  highlightRow?: number
  highlightCol?: number
  mono?: boolean
  // Rotate column header text. 'vertical-up' = -90° / reads bottom-to-top
  // (matches PPTX `vert=270` rotation); 'vertical-down' = 90° / reads top-to-
  // bottom. Headers stay aligned to their columns; the header row's height
  // grows to fit the rotated text.
  headerRotate?: 'vertical-up' | 'vertical-down'
}>(), {
  mono: true,
})
</script>

<template>
  <table class="josh-data" :class="[{ mono }, headerRotate ? `header-${headerRotate}` : null]">
    <thead>
      <tr>
        <th
          v-for="(h, ci) in headers"
          :key="ci"
          :class="{ 'col-highlight': highlightCol === ci }"
        ><span class="th-text">{{ h }}</span></th>
      </tr>
    </thead>
    <tbody>
      <tr
        v-for="(row, ri) in rows"
        :key="ri"
        :class="{ 'row-highlight': highlightRow === ri }"
      >
        <td
          v-for="(cell, ci) in row"
          :key="ci"
          :class="{ 'col-highlight': highlightCol === ci }"
        >{{ cell }}</td>
      </tr>
    </tbody>
  </table>
</template>

<style scoped>
.josh-data {
  margin: 1.5rem auto 0;
  font-size: 1.4rem;
  border-collapse: collapse;
}

.josh-data.mono {
  font-family: 'JetBrains Mono', ui-monospace, monospace;
}

.josh-data th,
.josh-data td {
  padding: 0.7rem 2rem;
  border: 1px solid var(--josh-rule);
  text-align: center;
}

.josh-data th {
  color: var(--josh-fg-soft);
  text-transform: uppercase;
  font-size: 0.85rem;
  letter-spacing: 0.08em;
  font-weight: 500;
}

/* Rotated header text: the <th> gets a fixed height (enough for the rotated
   string), tighter horizontal padding, and the inner <span> rotates around its
   own center. */
.josh-data.header-vertical-up th,
.josh-data.header-vertical-down th {
  padding: 0.4rem 0.5rem;
  vertical-align: bottom;
  height: 7rem;
}

.josh-data.header-vertical-up .th-text,
.josh-data.header-vertical-down .th-text {
  display: inline-block;
  white-space: nowrap;
  transform-origin: center center;
}

.josh-data.header-vertical-up .th-text {
  transform: rotate(-90deg);
}

.josh-data.header-vertical-down .th-text {
  transform: rotate(90deg);
}

.josh-data tbody tr.row-highlight td {
  color: var(--josh-accent);
  font-weight: 600;
}

.josh-data th.col-highlight,
.josh-data td.col-highlight {
  color: var(--josh-accent);
  font-weight: 600;
}

/* When a row is fully highlighted, keep its cells consistently accented even
   if a column highlight intersects (both selectors apply the same color). */
.josh-data tbody tr.row-highlight td.col-highlight {
  color: var(--josh-accent);
}
</style>
