<template>
  <router-link to="/" class="emp-logo d-inline-flex align-items-center gap-2 text-decoration-none" :class="{ light }" title="Go to home page">
    <span class="emp-logo-mark"><i class="bi bi-mortarboard-fill"></i></span>
    <span v-if="!compact" class="emp-logo-text">
      <span class="fw-800">EMP</span><small class="d-block">Exam Portal</small>
    </span>
  </router-link>
</template>
<script>
export default { name: 'AppLogo', props: { light: Boolean, compact: Boolean } }
</script>
<style>
.emp-logo-mark { width: 40px; height: 40px; border-radius: 12px; background: var(--emp-gradient); color: #fff; display: inline-flex;
  align-items: center; justify-content: center; font-size: 1.25rem; box-shadow: 0 6px 16px rgba(79,70,229,.35); }
.emp-logo-text { line-height: 1; color: var(--bs-body-color); font-size: 1.2rem; letter-spacing: -.02em; }
.emp-logo-text small { font-size: .62rem; text-transform: uppercase; letter-spacing: .16em; color: var(--emp-muted); font-weight: 700; margin-top: 3px; }
.emp-logo.light .emp-logo-text { color: #fff; }
.emp-logo.light .emp-logo-text small { color: rgba(255,255,255,.6); }
</style>
