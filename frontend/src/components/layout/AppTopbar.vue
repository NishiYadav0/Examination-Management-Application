<template>
  <header class="emp-topbar no-print">
    <button class="btn btn-icon btn-soft d-lg-none" @click="$store.commit('ui/setSidebar', true)" aria-label="Open menu">
      <i class="bi bi-list fs-5"></i>
    </button>
    <div class="d-none d-md-block">
      <div class="small text-muted">{{ greeting }}, {{ firstName }} 👋</div>
      <div class="fw-bold">{{ $route.meta.title }}</div>
    </div>
    <form class="emp-search ms-md-4 flex-grow-1" @submit.prevent="search">
      <i class="bi bi-search"></i>
      <input v-model="q" class="form-control" :placeholder="searchPlaceholder" aria-label="Search">
    </form>
    <div class="d-flex align-items-center gap-2 ms-auto">
      <InstallButton />
      <router-link to="/" class="btn btn-icon btn-soft d-none d-sm-inline-flex" title="Website home"><i class="bi bi-house"></i></router-link>
      <ThemeToggle />
      <!-- notifications -->
      <div class="dropdown">
        <button class="btn btn-icon btn-soft position-relative" data-bs-toggle="dropdown" data-bs-auto-close="outside" aria-label="Notifications">
          <i class="bi bi-bell"></i>
          <span v-if="unread" class="position-absolute top-0 start-100 translate-middle badge rounded-pill bg-danger">{{ unread > 9 ? '9+' : unread }}</span>
        </button>
        <div class="dropdown-menu dropdown-menu-end notif-menu p-0">
          <div class="d-flex justify-content-between align-items-center p-3 border-bottom">
            <strong>Notifications</strong>
            <button v-if="unread" class="btn btn-sm btn-link p-0" @click="$store.dispatch('notif/readAll')">Mark all read</button>
          </div>
          <div class="notif-list">
            <div v-if="!items.length" class="text-center text-muted small p-4"><i class="bi bi-bell-slash d-block fs-3 mb-1"></i>No notifications yet</div>
            <a v-for="n in items.slice(0, 6)" :key="n.id" href="#" class="notif-item" :class="{ unread: !n.is_read }" @click.prevent="open(n)">
              <span class="notif-dot" :class="'bg-' + (n.type === 'danger' ? 'danger' : n.type)"></span>
              <div class="min-w-0">
                <div class="fw-semibold small">{{ n.title }}</div>
                <div class="small text-muted text-truncate-2">{{ n.message }}</div>
                <div class="text-muted" style="font-size:.7rem">{{ $f.timeAgo(n.created_at) }}</div>
              </div>
            </a>
          </div>
          <router-link to="/notifications" class="d-block text-center p-2 border-top small fw-semibold">View all</router-link>
        </div>
      </div>
      <!-- profile -->
      <div class="dropdown">
        <button class="btn p-0 border-0 d-flex align-items-center gap-2" data-bs-toggle="dropdown" aria-label="Account">
          <span class="avatar">{{ $f.initials(user.name) }}</span>
          <i class="bi bi-chevron-down small text-muted d-none d-sm-inline"></i>
        </button>
        <ul class="dropdown-menu dropdown-menu-end" style="min-width: 230px">
          <li class="px-3 py-2">
            <div class="fw-bold">{{ user.name }}</div>
            <small class="text-muted">{{ user.email }}</small>
          </li>
          <li><hr class="dropdown-divider"></li>
          <li><router-link class="dropdown-item" :to="$store.getters['auth/home']"><i class="bi bi-grid-1x2 me-2"></i>Dashboard</router-link></li>
          <li><router-link class="dropdown-item" to="/profile"><i class="bi bi-person me-2"></i>My profile</router-link></li>
          <li><router-link class="dropdown-item" to="/notifications"><i class="bi bi-bell me-2"></i>Notifications</router-link></li>
          <li><router-link class="dropdown-item" to="/export"><i class="bi bi-cloud-arrow-down me-2"></i>Export my data</router-link></li>
          <li v-if="user.role !== 'admin'"><router-link class="dropdown-item" to="/support"><i class="bi bi-life-preserver me-2"></i>Help & Support</router-link></li>
          <li><router-link class="dropdown-item" to="/"><i class="bi bi-house me-2"></i>Website home</router-link></li>
          <li><hr class="dropdown-divider"></li>
          <li><button class="dropdown-item text-danger" @click="logout"><i class="bi bi-box-arrow-right me-2"></i>Logout</button></li>
        </ul>
      </div>
    </div>
  </header>
</template>

<script>
import ThemeToggle from '@/components/common/ThemeToggle.vue'
import InstallButton from '@/components/common/InstallButton.vue'
export default {
  name: 'AppTopbar',
  components: { ThemeToggle, InstallButton },
  data: () => ({ q: '' }),
  computed: {
    user () { return this.$store.state.auth.user || { name: '' } },
    firstName () { return (this.user.name || '').replace(/^(Dr\.|Prof\.|Mr\.|Ms\.)\s*/, '').split(' ')[0] },
    items () { return this.$store.state.notif.items },
    unread () { return this.$store.state.notif.unread },
    greeting () { const h = new Date().getHours(); return h < 12 ? 'Good morning' : h < 17 ? 'Good afternoon' : 'Good evening' },
    searchPlaceholder () {
      return { admin: 'Search students, examiners, exams, bookings…', examiner: 'Search booked students…', student: 'Search examinations…' }[this.user.role]
    }
  },
  methods: {
    search () {
      const q = this.q.trim()
      if (!q) return
      const target = { admin: '/admin/search', examiner: '/examiner/students', student: '/student/exams' }[this.user.role]
      this.$router.push({ path: target, query: { q } })
      this.q = ''
    },
    async open (n) {
      if (!n.is_read) await this.$store.dispatch('notif/read', n.id)
      if (n.link) this.$router.push(n.link)
    },
    async logout () {
      await this.$store.dispatch('auth/logout')
      this.$toast('Logged out successfully')
      this.$router.push('/login')
    }
  }
}
</script>

<style>
.emp-topbar { position: sticky; top: 0; z-index: 1020; display: flex; align-items: center; gap: .75rem; padding: .8rem 1.75rem;
  background: rgba(245,247,251,.8); backdrop-filter: blur(14px); border-bottom: 1px solid var(--emp-border); }
[data-bs-theme="dark"] .emp-topbar { background: rgba(11,17,32,.8); }
.emp-search { position: relative; max-width: 460px; }
.emp-search i { position: absolute; left: 14px; top: 50%; transform: translateY(-50%); color: var(--emp-muted); }
.emp-search .form-control { padding-left: 2.4rem; background: var(--emp-card-bg); border-radius: 12px; }
.notif-menu { width: 340px; max-width: 92vw; overflow: hidden; }
.notif-list { max-height: 360px; overflow-y: auto; }
.notif-item { display: flex; gap: .75rem; padding: .8rem 1rem; text-decoration: none; color: inherit; border-bottom: 1px solid var(--emp-border); }
.notif-item:hover { background: rgba(79,70,229,.05); }
.notif-item.unread { background: rgba(79,70,229,.06); }
.notif-dot { width: 9px; height: 9px; border-radius: 50%; margin-top: 6px; flex-shrink: 0; }
@media (max-width: 991.98px) { .emp-topbar { padding: .7rem 1rem; } }
</style>
