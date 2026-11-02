<template>
  <nav class="navbar navbar-expand-lg emp-navbar sticky-top" :class="{ scrolled }">
    <div class="container">
      <AppLogo />
      <button class="navbar-toggler border-0" type="button" data-bs-toggle="collapse" data-bs-target="#pubNav" aria-label="Toggle navigation">
        <i class="bi bi-list fs-2"></i>
      </button>
      <div class="collapse navbar-collapse" id="pubNav">
        <ul class="navbar-nav mx-auto gap-lg-1">
          <li class="nav-item"><router-link class="nav-link" to="/" exact-active-class="active">Home</router-link></li>
          <li class="nav-item"><a class="nav-link" href="/#features" @click.prevent="go('features')">Features</a></li>
          <li class="nav-item"><a class="nav-link" href="/#how" @click.prevent="go('how')">How it works</a></li>
          <li class="nav-item"><router-link class="nav-link" to="/about">About</router-link></li>
          <li class="nav-item"><router-link class="nav-link" to="/contact">Contact</router-link></li>
        </ul>
        <div class="d-flex align-items-center gap-2 py-2 py-lg-0">
          <ThemeToggle />
          <template v-if="loggedIn">
            <router-link :to="$store.getters['auth/home']" class="btn btn-gradient">
              <i class="bi bi-grid-1x2 me-1"></i> Dashboard
            </router-link>
            <div class="dropdown">
              <button class="btn p-0 border-0" data-bs-toggle="dropdown" aria-label="Account menu">
                <span class="avatar">{{ $f.initials(user.name) }}</span>
              </button>
              <ul class="dropdown-menu dropdown-menu-end">
                <li class="px-3 py-2"><div class="fw-bold">{{ user.name }}</div><small class="text-muted text-capitalize">{{ user.role }}</small></li>
                <li><hr class="dropdown-divider"></li>
                <li><router-link class="dropdown-item" to="/profile"><i class="bi bi-person me-2"></i>Profile</router-link></li>
                <li><button class="dropdown-item text-danger" @click="logout"><i class="bi bi-box-arrow-right me-2"></i>Logout</button></li>
              </ul>
            </div>
          </template>
          <template v-else>
            <router-link to="/login" class="btn btn-soft">Log in</router-link>
            <router-link to="/register" class="btn btn-gradient">Get started</router-link>
          </template>
        </div>
      </div>
    </div>
  </nav>
</template>

<script>
import AppLogo from './AppLogo.vue'
import ThemeToggle from '@/components/common/ThemeToggle.vue'
export default {
  name: 'PublicNavbar',
  components: { AppLogo, ThemeToggle },
  data: () => ({ scrolled: false }),
  computed: {
    loggedIn () { return this.$store.getters['auth/isLoggedIn'] },
    user () { return this.$store.state.auth.user }
  },
  mounted () { window.addEventListener('scroll', this.onScroll); this.onScroll() },
  beforeUnmount () { window.removeEventListener('scroll', this.onScroll) },
  methods: {
    onScroll () { this.scrolled = window.scrollY > 10 },
    go (id) {
      if (this.$route.path !== '/') this.$router.push({ path: '/', hash: '#' + id })
      else document.getElementById(id)?.scrollIntoView({ behavior: 'smooth' })
    },
    async logout () {
      await this.$store.dispatch('auth/logout')
      this.$toast('You have been logged out')
      this.$router.push('/')
    }
  }
}
</script>

<style>
.emp-navbar { background: rgba(255,255,255,.72); backdrop-filter: saturate(180%) blur(14px); transition: box-shadow .2s, background .2s; padding: .75rem 0; }
[data-bs-theme="dark"] .emp-navbar { background: rgba(11,17,32,.72); }
.emp-navbar.scrolled { box-shadow: 0 6px 24px rgba(15,23,42,.08); }
.emp-navbar .nav-link { font-weight: 600; color: var(--emp-muted); padding: .5rem .9rem !important; border-radius: .6rem; }
.emp-navbar .nav-link:hover, .emp-navbar .nav-link.active { color: var(--emp-primary); background: rgba(79,70,229,.07); }
</style>
