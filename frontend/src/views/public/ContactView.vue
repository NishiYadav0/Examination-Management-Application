<template>
  <div>
    <section class="page-hero">
      <div class="container text-center">
        <span class="small-caps text-primary">Contact</span>
        <h1 class="display-6 fw-bold mt-2">We're here to help</h1>
        <p class="text-muted mx-auto" style="max-width:560px">Questions about registration, bookings or results? Send us a message and the examination cell will get back to you.</p>
      </div>
    </section>
    <div class="container" style="margin-top:-2rem">
      <div class="row g-4">
        <div class="col-lg-4">
          <div class="d-grid gap-3">
            <div class="card-emp p-4 d-flex gap-3" v-for="c in cards" :key="c.t">
              <span class="icon-box" :style="{ background: c.c + '1a', color: c.c }"><i :class="'bi bi-' + c.i"></i></span>
              <div><div class="fw-bold">{{ c.t }}</div><div class="small text-muted">{{ c.d }}</div></div>
            </div>
          </div>
        </div>
        <div class="col-lg-8">
          <div class="card-emp">
            <div class="card-header"><i class="bi bi-envelope-paper me-2 text-primary"></i>Send us a message</div>
            <div class="card-body"><ContactForm @sent="sent" /></div>
          </div>
          <div v-if="loggedIn" class="card-emp mt-4">
            <div class="card-header d-flex justify-content-between align-items-center">
              <span><i class="bi bi-chat-square-text me-2 text-primary"></i>My previous messages</span>
              <router-link to="/support" class="small">Open in dashboard</router-link>
            </div>
            <div class="card-body"><TicketList ref="tickets" /></div>
          </div>
          <div v-else class="card-emp mt-4 p-4 d-flex flex-wrap align-items-center justify-content-between gap-3">
            <div><b>Have an account?</b><div class="small text-muted">Log in to track your messages and see replies from support.</div></div>
            <router-link to="/login?redirect=/contact" class="btn btn-soft">Log in</router-link>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
<script>
import ContactForm from '@/components/common/ContactForm.vue'
import TicketList from '@/components/common/TicketList.vue'
export default {
  name: 'ContactView',
  components: { ContactForm, TicketList },
  data: () => ({
    cards: [
      { i: 'envelope', t: 'E-mail', d: 'support@emp.local', c: '#4f46e5' },
      { i: 'telephone', t: 'Phone', d: '+91 44 2257 0000 (Mon–Fri, 9–6)', c: '#10b981' },
      { i: 'geo-alt', t: 'Office', d: 'Examination Cell, IIT Madras, Chennai 600036', c: '#f59e0b' },
      { i: 'lightning-charge', t: 'Response time', d: 'Usually within one working day', c: '#ec4899' }
    ]
  }),
  computed: { loggedIn () { return this.$store.getters['auth/isLoggedIn'] } },
  methods: { sent () { if (this.$refs.tickets) this.$refs.tickets.load() } }
}
</script>
<style scoped>
.page-hero { padding: 4rem 0 4.5rem; background: var(--emp-gradient-soft); }
</style>
