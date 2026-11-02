<template>
  <aside class="emp-sidebar" :class="{ open: $store.state.ui.sidebarOpen }">
    <div class="emp-sidebar-head">
      <AppLogo light />
      <button class="btn btn-icon text-white d-lg-none" @click="$store.commit('ui/setSidebar', false)" aria-label="Close menu">
        <i class="bi bi-x-lg"></i>
      </button>
    </div>
    <div class="emp-role-chip">
      <span class="avatar avatar-sm">{{ $f.initials(user.name) }}</span>
      <div class="min-w-0">
        <div class="fw-semibold text-truncate text-white small">{{ user.name }}</div>
        <div class="role text-capitalize"><i class="bi bi-shield-check me-1"></i>{{ user.role }}</div>
      </div>
    </div>
    <nav class="emp-nav">
      <template v-for="(item, i) in menu" :key="i">
        <div v-if="item.section" class="emp-nav-section">{{ item.section }}</div>
        <router-link v-else :to="item.to" class="emp-nav-link" :class="{ active: isActive(item) }">
          <i :class="'bi bi-' + item.icon"></i>
          <span>{{ item.label }}</span>
          <span v-if="item.badge && badge(item.badge)" class="badge rounded-pill bg-danger ms-auto">{{ badge(item.badge) }}</span>
        </router-link>
      </template>
      <div class="emp-nav-section">Quick links</div>
      <router-link to="/" class="emp-nav-link"><i class="bi bi-house"></i><span>Website home</span></router-link>
      <router-link to="/profile" class="emp-nav-link" :class="{ active: $route.path === '/profile' }"><i class="bi bi-person-gear"></i><span>My profile</span></router-link>
    </nav>
    <div class="emp-sidebar-foot">
      <button class="emp-nav-link w-100 border-0 bg-transparent text-start" @click="logout">
        <i class="bi bi-box-arrow-left"></i><span>Logout</span>
      </button>
    </div>
  </aside>
</template>

<script>
import AppLogo from './AppLogo.vue'
import menus from '@/config/menus'
export default {
  name: 'AppSidebar',
  components: { AppLogo },
  computed: {
    user () { return this.$store.state.auth.user || { name: '' } },
    menu () { return menus[this.user.role] || [] }
  },
  methods: {
    isActive (item) {
      const p = this.$route.path
      return item.exact ? p === item.to : p === item.to || p.startsWith(item.to + '/')
    },
    badge (key) {
      if (key === 'tickets') return this.$store.state.notif.items.filter(n => !n.is_read && n.title.includes('support')).length || null
      return null
    },
    async logout () {
      const ok = await this.$confirm({ title: 'Log out?', message: 'You will need to sign in again to access your dashboard.', confirmText: 'Logout', variant: 'danger', icon: 'box-arrow-left' })
      if (!ok) return
      await this.$store.dispatch('auth/logout')
      this.$toast('Logged out successfully')
      this.$router.push('/login')
    }
  }
}
</script>

<style>
.emp-sidebar { position: fixed; top: 0; bottom: 0; left: 0; width: var(--emp-sidebar-w); background: var(--emp-sidebar-bg);
  display: flex; flex-direction: column; z-index: 1040; transition: transform .25s ease; color: #cbd5e1;
  background-image: radial-gradient(circle at 0 0, rgba(124,58,237,.25), transparent 45%); }
.emp-sidebar-head { display: flex; align-items: center; justify-content: space-between; padding: 1.25rem 1.25rem .75rem; }
.emp-role-chip { margin: .5rem 1rem 1rem; padding: .7rem .8rem; border-radius: 14px; background: rgba(255,255,255,.06);
  display: flex; gap: .7rem; align-items: center; }
.emp-role-chip .role { font-size: .72rem; color: #a5b4fc; font-weight: 600; }
.min-w-0 { min-width: 0; }
.emp-nav { flex: 1; overflow-y: auto; padding: 0 .75rem 1rem; scrollbar-width: thin; }
.emp-nav-section { font-size: .66rem; text-transform: uppercase; letter-spacing: .14em; color: #64748b; font-weight: 700; padding: 1rem .75rem .4rem; }
.emp-nav-link { display: flex; align-items: center; gap: .75rem; padding: .62rem .8rem; border-radius: 11px; color: #cbd5e1;
  text-decoration: none; font-weight: 500; font-size: .9rem; margin-bottom: 2px; transition: background .15s, color .15s; }
.emp-nav-link i { font-size: 1.05rem; width: 20px; text-align: center; opacity: .85; }
.emp-nav-link:hover { background: rgba(255,255,255,.06); color: #fff; }
.emp-nav-link.active { background: var(--emp-gradient); color: #fff; box-shadow: 0 8px 20px rgba(79,70,229,.35); }
.emp-sidebar-foot { padding: .75rem; border-top: 1px solid rgba(255,255,255,.06); }
@media (max-width: 991.98px) {
  .emp-sidebar { transform: translateX(-100%); }
  .emp-sidebar.open { transform: none; box-shadow: 0 0 40px rgba(0,0,0,.4); }
}
</style>
