<template>
  <div class="auth-wrap">
    <div class="auth-side d-none d-lg-flex">
      <AppLogo light />
      <div class="my-auto">
        <h2 class="fw-bold text-white display-6">{{ heading }}</h2>
        <p class="text-white-50 fs-6 mb-4">{{ text }}</p>
        <div class="d-grid gap-3">
          <div class="side-pt" v-for="p in points" :key="p.t"><i :class="'bi bi-' + p.i"></i><div><b>{{ p.t }}</b><div class="small opacity-75">{{ p.d }}</div></div></div>
        </div>
      </div>
      <small class="text-white-50">© {{ new Date().getFullYear() }} Examination Management Portal</small>
    </div>
    <div class="auth-main">
      <div class="d-flex justify-content-between align-items-center mb-4">
        <div class="d-lg-none"><AppLogo /></div>
        <router-link to="/" class="small ms-auto text-decoration-none"><i class="bi bi-arrow-left me-1"></i>Back to home</router-link>
      </div>
      <div class="auth-card fade-in"><slot /></div>
    </div>
  </div>
</template>
<script>
import AppLogo from './AppLogo.vue'
export default {
  name: 'AuthShell',
  components: { AppLogo },
  props: { heading: String, text: String },
  data: () => ({
    points: [
      { i: 'calendar2-check', t: 'Book in seconds', d: 'Live seat availability for every slot' },
      { i: 'clipboard2-data', t: 'Rubric based grading', d: 'Transparent criterion-wise marks' },
      { i: 'bell', t: 'Never miss an exam', d: 'Daily reminders and instant alerts' }
    ]
  })
}
</script>
<style>
.auth-wrap { min-height: 100vh; display: flex; }
.auth-side { width: 44%; background: var(--emp-gradient); padding: 2.5rem 3rem; flex-direction: column; position: relative; overflow: hidden; }
.auth-side::after { content: ""; position: absolute; width: 420px; height: 420px; border-radius: 50%; background: rgba(255,255,255,.08); right: -140px; bottom: -120px; }
.side-pt { display: flex; gap: 1rem; align-items: flex-start; color: #fff; background: rgba(255,255,255,.1); padding: 1rem 1.2rem; border-radius: 16px; backdrop-filter: blur(6px); }
.side-pt i { font-size: 1.4rem; }
.auth-main { flex: 1; padding: 2rem; display: flex; flex-direction: column; }
.auth-card { width: 100%; max-width: 480px; margin: auto; }
</style>
