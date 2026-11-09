<template>
  <div>
    <PageHeader title="Help & Support" subtitle="Raise a query with the examination cell and follow the replies here." />
    <div class="row g-4">
      <div class="col-xl-7">
        <div class="card-emp"><div class="card-header"><i class="bi bi-send me-2 text-primary"></i>New request</div>
          <div class="card-body"><ContactForm @sent="$refs.list.load()" /></div></div>
        <div class="card-emp mt-4"><div class="card-header"><i class="bi bi-question-circle me-2 text-primary"></i>Quick answers</div>
          <div class="card-body small">
            <p v-for="q in faqs" :key="q.q" class="mb-3"><b>{{ q.q }}</b><br><span class="text-muted">{{ q.a }}</span></p>
          </div></div>
      </div>
      <div class="col-xl-5">
        <div class="card-emp"><div class="card-header"><i class="bi bi-chat-square-text me-2 text-primary"></i>My requests</div>
          <div class="card-body"><TicketList ref="list" /></div></div>
      </div>
    </div>
  </div>
</template>
<script>
import PageHeader from '@/components/common/PageHeader.vue'
import ContactForm from '@/components/common/ContactForm.vue'
import TicketList from '@/components/common/TicketList.vue'
export default {
  name: 'SupportView',
  components: { PageHeader, ContactForm, TicketList },
  data: () => ({
    faqs: [
      { q: 'I need to change my booked slot.', a: 'Cancel it before the booking deadline and book another one. After the deadline, ask the admin to reschedule it for you.' },
      { q: 'My slot creation button is disabled.', a: 'Examiners can create slots only while the admin keeps slot creation open and today is within the configured period.' },
      { q: 'When will results appear?', a: 'Once your examiner submits the evaluation and the admin publishes results for that examination.' }
    ]
  })
}
</script>
