<template>
  <AuthShell heading="Welcome back!" text="Log in to manage examinations, publish slots, evaluate students or book your next viva.">
    <h2 class="fw-bold mb-1">Sign in</h2>
    <p class="text-muted mb-4">Admins, examiners and students all sign in here.</p>

    <div v-if="blocked" class="alert alert-danger d-flex gap-2"><i class="bi bi-slash-circle"></i><div>{{ blocked }}</div></div>

    <form @submit.prevent="submit" novalidate>
      <div class="mb-3">
        <label class="form-label">E-mail address</label>
        <div class="input-group">
          <span class="input-group-text"><i class="bi bi-envelope"></i></span>
          <input v-model.trim="email" type="email" class="form-control" :class="{ 'is-invalid': errors.email }" placeholder="you@example.com" autocomplete="username" required>
          <div class="invalid-feedback">{{ errors.email }}</div>
        </div>
      </div>
      <div class="mb-2">
        <label class="form-label">Password</label>
        <div class="input-group">
          <span class="input-group-text"><i class="bi bi-lock"></i></span>
          <input v-model="password" :type="show ? 'text' : 'password'" class="form-control" :class="{ 'is-invalid': errors.password }" placeholder="••••••••" autocomplete="current-password" required>
          <button type="button" class="btn btn-outline-secondary" @click="show = !show" :aria-label="show ? 'Hide password' : 'Show password'"><i :class="show ? 'bi bi-eye-slash' : 'bi bi-eye'"></i></button>
          <div class="invalid-feedback">{{ errors.password }}</div>
        </div>
      </div>
      <div class="d-flex justify-content-between align-items-center mb-4 small">
        <div class="form-check"><input id="rem" class="form-check-input" type="checkbox" checked><label for="rem" class="form-check-label">Remember me</label></div>
        <router-link to="/contact">Forgot password?</router-link>
      </div>
      <button class="btn btn-gradient w-100 py-2" :disabled="busy">
        <span v-if="busy" class="spinner-border spinner-border-sm me-2"></span>Sign in
      </button>
    </form>

    <div class="demo mt-4">
      <div class="small-caps text-muted mb-2">Quick demo login</div>
      <div class="d-flex flex-wrap gap-2">
        <button v-for="d in demos" :key="d.role" type="button" class="btn btn-sm btn-soft" @click="fill(d)"><i :class="'bi bi-' + d.icon + ' me-1'"></i>{{ d.role }}</button>
      </div>
    </div>
    <p class="text-center mt-4 mb-0 text-muted">New student? <router-link to="/register" class="fw-semibold">Create an account</router-link></p>
  </AuthShell>
</template>

<script>
import AuthShell from '@/components/layout/AuthShell.vue'
export default {
  name: 'LoginView',
  components: { AuthShell },
  data: () => ({
    email: '', password: '', show: false, busy: false, errors: {}, blocked: '',
    demos: [
      { role: 'Admin', icon: 'shield-lock', email: 'admin@emp.com', password: 'admin123' },
      { role: 'Examiner', icon: 'person-badge', email: 'examiner1@emp.com', password: 'examiner123' },
      { role: 'Student', icon: 'mortarboard', email: 'student1@emp.com', password: 'student123' }
    ]
  }),
  methods: {
    fill (d) { this.email = d.email; this.password = d.password },
    async submit () {
      this.errors = {}; this.blocked = ''
      if (!/^[^@\s]+@[^@\s]+\.[a-zA-Z]{2,}$/.test(this.email)) this.errors.email = 'Enter a valid e-mail'
      if (!this.password) this.errors.password = 'Password is required'
      if (Object.keys(this.errors).length) return
      this.busy = true
      try {
        const user = await this.$store.dispatch('auth/login', { email: this.email, password: this.password })
        this.$store.dispatch('notif/load')
        this.$toast(`Welcome back, ${user.name}!`)
        const redirect = this.$route.query.redirect
        this.$router.push(redirect && !redirect.startsWith('/login') ? redirect : `/${user.role}`)
      } catch (e) {
        if (e.response && e.response.status === 403) this.blocked = e.userMessage
        else this.$error(e)
      } finally { this.busy = false }
    }
  }
}
</script>
