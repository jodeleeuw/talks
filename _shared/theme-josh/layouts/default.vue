<template>
  <div class="slidev-layout josh-default">
    <slot />
  </div>
</template>

<style scoped>
/* UnoCSS / Tailwind preflight resets `ol` to `list-style: none; padding: 0`,
   which hides the "1." / "2." numerals on plain markdown ordered lists.
   Re-assert decimal markers for the default layout only — layouts like
   `aside` and `outro` deliberately use `list-style: none` with their own
   ::before markers, and they win via their own scoped :deep rules. */
.josh-default :deep(ol) {
  list-style: decimal;
  padding-left: 1.5rem;
}

.josh-default :deep(ul) {
  list-style: disc;
  padding-left: 1.5rem;
}

.josh-default :deep(ol li),
.josh-default :deep(ul li) {
  margin: 0.6rem 0;
  line-height: 1.5;
  font-size: 1.35rem;
  color: var(--josh-fg);
}

.josh-default :deep(ol li::marker),
.josh-default :deep(ul li::marker) {
  color: var(--josh-fg-soft);
}
</style>
