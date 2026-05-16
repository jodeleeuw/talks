<template>
  <div class="slidev-layout josh-center">
    <div class="center-body">
      <slot />
    </div>
  </div>
</template>

<style scoped>
.josh-center {
  display: flex;
  align-items: center;
  justify-content: center;
  text-align: center;
  padding: 4rem 5rem;
}

.center-body {
  max-width: 28ch;
}

.center-body :slotted(h1) {
  font-size: 3.5rem !important;
  font-weight: 500;
  line-height: 1.15;
  letter-spacing: -0.02em;
}

.center-body :slotted(h2) {
  font-size: 2rem !important;
  color: var(--josh-fg-soft);
  font-weight: 400;
}

.center-body :slotted(p) {
  font-size: 1.6rem;
  line-height: 1.5;
}
</style>
