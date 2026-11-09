<template>
  <div class="toast-container position-fixed top-0 end-0 p-3" style="z-index: 2000">
    <transition-group name="toast">
      <div v-for="t in toasts" :key="t.id" class="emp-toast" :class="'t-' + t.type" role="alert">
        <i :class="'bi bi-' + icon(t.type)"></i>
        <div class="flex-grow-1">
          <div v-if="t.title" class="fw-bold">{{ t.title }}</div>
          <div>{{ t.message }}</div>
        </div>
        <button class="btn-close btn-sm" @click="$store.commit('ui/removeToast', t.id)" aria-label="Close"></button>
      </div>
    </transition-group>
  </div>
</template>
<script>
export default {
  name: 'ToastContainer',
  computed: { toasts () { return this.$store.state.ui.toasts } },
  methods: {
    icon (t) { return { success: 'check-circle-fill', danger: 'x-octagon-fill', warning: 'exclamation-triangle-fill', info: 'info-circle-fill' }[t] || 'info-circle-fill' }
  }
}
</script>
<style>
.emp-toast { display: flex; gap: .75rem; align-items: flex-start; min-width: 300px; max-width: 400px; background: var(--emp-card-bg);
  border: 1px solid var(--emp-border); border-left: 4px solid; border-radius: 14px; padding: .9rem 1rem; margin-bottom: .6rem;
  box-shadow: 0 16px 40px rgba(15,23,42,.16); font-size: .9rem; }
.emp-toast > i { font-size: 1.2rem; }
.t-success { border-left-color: #10b981; } .t-success > i { color: #10b981; }
.t-danger { border-left-color: #ef4444; } .t-danger > i { color: #ef4444; }
.t-warning { border-left-color: #f59e0b; } .t-warning > i { color: #f59e0b; }
.t-info { border-left-color: #06b6d4; } .t-info > i { color: #06b6d4; }
.toast-enter-active, .toast-leave-active { transition: all .25s ease; }
.toast-enter-from, .toast-leave-to { opacity: 0; transform: translateX(40px); }
</style>
