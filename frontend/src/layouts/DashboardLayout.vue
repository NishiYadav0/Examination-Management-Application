<template>
  <div class="emp-shell">
    <AppSidebar />
    <div class="emp-backdrop d-lg-none" v-if="$store.state.ui.sidebarOpen" @click="$store.commit('ui/setSidebar', false)"></div>
    <div class="emp-main">
      <AppTopbar />
      <div class="emp-content container-fluid">
        <slot />
      </div>
      <footer class="emp-dash-footer no-print">
        © {{ year }} Examination Management Portal · <router-link to="/">Home</router-link> ·
        <router-link to="/about">About</router-link> · <router-link to="/contact">Contact</router-link>
      </footer>
    </div>
  </div>
</template>

<script>
import AppSidebar from '@/components/layout/AppSidebar.vue'
import AppTopbar from '@/components/layout/AppTopbar.vue'
export default {
  name: 'DashboardLayout',
  components: { AppSidebar, AppTopbar },
  data: () => ({ year: new Date().getFullYear(), timer: null }),
  mounted () {
    // poll notifications every 30 s
    this.timer = setInterval(() => this.$store.dispatch('notif/load'), 30000)
  },
  beforeUnmount () { clearInterval(this.timer) }
}
</script>

<style>
.emp-shell { min-height: 100vh; }
.emp-main { margin-left: var(--emp-sidebar-w); min-height: 100vh; display: flex; flex-direction: column; transition: margin .25s ease; }
.emp-content { padding: 1.5rem 1.75rem 2rem; flex: 1; max-width: 1500px; }
.emp-dash-footer { padding: 1rem 1.75rem; font-size: .8rem; color: var(--emp-muted); border-top: 1px solid var(--emp-border); }
.emp-dash-footer a { color: var(--emp-muted); text-decoration: none; }
.emp-dash-footer a:hover { color: var(--emp-primary); }
.emp-backdrop { position: fixed; inset: 0; background: rgba(15,23,42,.45); z-index: 1035; backdrop-filter: blur(2px); }
@media (max-width: 991.98px) {
  .emp-main { margin-left: 0; }
  .emp-content { padding: 1rem; }
}
</style>
