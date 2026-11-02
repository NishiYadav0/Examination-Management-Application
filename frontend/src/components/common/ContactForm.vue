<template>
  <form @submit.prevent="submit" novalidate>
    <div class="row g-3">
      <template v-if="!user">
        <div class="col-md-6">
          <label class="form-label">Full name *</label>
          <input v-model.trim="form.name" class="form-control" :class="{ 'is-invalid': errors.name }" required maxlength="120" placeholder="Your name">
          <div class="invalid-feedback">{{ errors.name }}</div>
        </div>
        <div class="col-md-6">
          <label class="form-label">E-mail *</label>
          <input v-model.trim="form.email" type="email" class="form-control" :class="{ 'is-invalid': errors.email }" required placeholder="you@example.com">
          <div class="invalid-feedback">{{ errors.email }}</div>
        </div>
      </template>
      <div v-else class="col-12">
        <div class="alert alert-primary bg-primary bg-opacity-10 border-0 small mb-0">
          <i class="bi bi-person-check me-1"></i> Sending as <b>{{ user.name }}</b> ({{ user.email }}). Replies appear below and in your notifications.
        </div>
      </div>
      <div class="col-md-4">
        <label class="form-label">Category</label>
        <select v-model="form.category" class="form-select">
          <option v-for="c in categories" :key="c">{{ c }}</option>
        </select>
      </div>
      <div class="col-md-8">
        <label class="form-label">Subject *</label>
        <input v-model.trim="form.subject" class="form-control" :class="{ 'is-invalid': errors.subject }" required maxlength="200" placeholder="How can we help?">
        <div class="invalid-feedback">{{ errors.subject }}</div>
      </div>
      <div class="col-12">
        <label class="form-label">Message *</label>
        <textarea v-model.trim="form.message" rows="5" class="form-control" :class="{ 'is-invalid': errors.message }" required minlength="10" maxlength="5000" placeholder="Describe your question or issue…"></textarea>
        <div class="invalid-feedback">{{ errors.message }}</div>
        <div class="form-text text-end">{{ form.message.length }}/5000</div>
      </div>
      <div class="col-12">
        <button class="btn btn-gradient px-4" :disabled="busy">
          <span v-if="busy" class="spinner-border spinner-border-sm me-2"></span><i v-else class="bi bi-send me-2"></i>Send message
        </button>
      </div>
    </div>
  </form>
</template>

<script>
import api from '@/services/api'
const EMAIL = /^[^@\s]+@[^@\s]+\.[a-zA-Z]{2,}$/
export default {
  name: 'ContactForm',
  emits: ['sent'],
  data: () => ({
    busy: false, errors: {},
    categories: ['General', 'Account', 'Booking', 'Examination', 'Results', 'Technical issue', 'Feedback'],
    form: { name: '', email: '', category: 'General', subject: '', message: '' }
  }),
  computed: { user () { return this.$store.getters['auth/isLoggedIn'] ? this.$store.state.auth.user : null } },
  methods: {
    validate () {
      const e = {}
      if (!this.user) {
        if (!this.form.name) e.name = 'Please enter your name'
        if (!EMAIL.test(this.form.email)) e.email = 'Please enter a valid e-mail'
      }
      if (!this.form.subject) e.subject = 'Subject is required'
      if (this.form.message.length < 10) e.message = 'Message must be at least 10 characters'
      this.errors = e
      return !Object.keys(e).length
    },
    async submit () {
      if (!this.validate()) return
      this.busy = true
      try {
        const { data } = await api.post('/public/contact', this.form)
        this.$toast(data.message)
        this.form = { name: '', email: '', category: 'General', subject: '', message: '' }
        this.$emit('sent', data.data)
      } catch (e) {
        this.errors = e.fieldErrors || {}
        this.$error(e)
      } finally { this.busy = false }
    }
  }
}
</script>
