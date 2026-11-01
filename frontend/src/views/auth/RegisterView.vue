<template>
  <AuthShell heading="Join the portal" text="Create your student account to browse examinations, book slots and track your results.">
    <h2 class="fw-bold mb-1">Create student account</h2>
    <p class="text-muted mb-4">Examiner accounts are created by the admin.</p>
    <form @submit.prevent="submit" novalidate>
      <div class="row g-3">
        <div class="col-12">
          <label class="form-label">Full name *</label>
          <input v-model.trim="f.name" class="form-control" :class="{ 'is-invalid': e.name }" placeholder="e.g. Aarav Sharma" maxlength="120">
          <div class="invalid-feedback">{{ e.name }}</div>
        </div>
        <div class="col-md-6">
          <label class="form-label">Roll number *</label>
          <input v-model.trim="f.roll_no" class="form-control text-uppercase" :class="{ 'is-invalid': e.roll_no }" placeholder="23F1000123" maxlength="30">
          <div class="invalid-feedback">{{ e.roll_no }}</div>
        </div>
        <div class="col-md-6">
          <label class="form-label">Phone</label>
          <input v-model.trim="f.phone" class="form-control" :class="{ 'is-invalid': e.phone }" placeholder="9876543210" maxlength="15">
          <div class="invalid-feedback">{{ e.phone }}</div>
        </div>
        <div class="col-12">
          <label class="form-label">E-mail *</label>
          <input v-model.trim="f.email" type="email" class="form-control" :class="{ 'is-invalid': e.email }" placeholder="you@example.com" autocomplete="username">
          <div class="invalid-feedback">{{ e.email }}</div>
        </div>
        <div class="col-md-7">
          <label class="form-label">Program</label>
          <select v-model="f.program" class="form-select">
            <option>BS in Data Science & Applications</option><option>BS in Electronic Systems</option><option>B.Tech</option><option>M.Tech</option><option>Other</option>
          </select>
        </div>
        <div class="col-md-5">
          <label class="form-label">Year</label>
          <select v-model="f.year" class="form-select"><option v-for="y in 5" :key="y" :value="y">Year {{ y }}</option></select>
        </div>
        <div class="col-md-6">
          <label class="form-label">Password *</label>
          <input v-model="f.password" type="password" class="form-control" :class="{ 'is-invalid': e.password }" autocomplete="new-password" placeholder="Min 6 characters">
          <div class="invalid-feedback">{{ e.password }}</div>
          <div class="progress mt-2" style="height:5px"><div class="progress-bar" :class="strength.cls" :style="{ width: strength.pct + '%' }"></div></div>
          <small class="text-muted">{{ strength.label }}</small>
        </div>
        <div class="col-md-6">
          <label class="form-label">Confirm password *</label>
          <input v-model="f.confirm_password" type="password" class="form-control" :class="{ 'is-invalid': e.confirm_password }" autocomplete="new-password">
          <div class="invalid-feedback">{{ e.confirm_password }}</div>
        </div>
        <div class="col-12">
          <div class="form-check">
            <input id="terms" v-model="terms" type="checkbox" class="form-check-input" :class="{ 'is-invalid': e.terms }">
            <label for="terms" class="form-check-label small">I agree to follow the examination code of conduct.</label>
            <div class="invalid-feedback">{{ e.terms }}</div>
          </div>
        </div>
        <div class="col-12">
          <button class="btn btn-gradient w-100 py-2" :disabled="busy"><span v-if="busy" class="spinner-border spinner-border-sm me-2"></span>Create account</button>
        </div>
      </div>
    </form>
    <p class="text-center mt-4 mb-0 text-muted">Already registered? <router-link to="/login" class="fw-semibold">Sign in</router-link></p>
  </AuthShell>
</template>

<script>
import AuthShell from '@/components/layout/AuthShell.vue'
export default {
  name: 'RegisterView',
  components: { AuthShell },
  data: () => ({
    busy: false, terms: false, e: {},
    f: { name: '', roll_no: '', phone: '', email: '', program: 'BS in Data Science & Applications', year: 1, password: '', confirm_password: '' }
  }),
  computed: {
    strength () {
      const p = this.f.password
      let s = 0
      if (p.length >= 6) s++
      if (p.length >= 10) s++
      if (/[A-Z]/.test(p) && /[a-z]/.test(p)) s++
      if (/\d/.test(p)) s++
      if (/[^A-Za-z0-9]/.test(p)) s++
      const map = [['Too short', 'bg-danger'], ['Weak', 'bg-danger'], ['Fair', 'bg-warning'], ['Good', 'bg-info'], ['Strong', 'bg-success'], ['Very strong', 'bg-success']]
      return { pct: (s / 5) * 100, label: p ? map[s][0] : ' ', cls: map[s][1] }
    }
  },
  methods: {
    validate () {
      const e = {}; const f = this.f
      if (f.name.length < 2) e.name = 'Please enter your full name'
      if (!/^[A-Za-z0-9]{4,30}$/.test(f.roll_no)) e.roll_no = 'Roll number: 4–30 letters/digits'
      if (f.phone && !/^[0-9+\-\s]{7,15}$/.test(f.phone)) e.phone = 'Invalid phone number'
      if (!/^[^@\s]+@[^@\s]+\.[a-zA-Z]{2,}$/.test(f.email)) e.email = 'Enter a valid e-mail'
      if (f.password.length < 6) e.password = 'At least 6 characters'
      if (f.password !== f.confirm_password) e.confirm_password = 'Passwords do not match'
      if (!this.terms) e.terms = 'Please accept to continue'
      this.e = e
      return !Object.keys(e).length
    },
    async submit () {
      if (!this.validate()) return
      this.busy = true
      try {
        await this.$store.dispatch('auth/register', this.f)
        this.$store.dispatch('notif/load')
        this.$toast('Account created – welcome to EMP!')
        this.$router.push('/student')
      } catch (err) {
        this.e = err.fieldErrors || {}
        this.$error(err)
      } finally { this.busy = false }
    }
  }
}
</script>
