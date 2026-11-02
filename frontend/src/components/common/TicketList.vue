<template>
  <div>
    <LoadingBlock v-if="loading" :rows="3" />
    <EmptyState v-else-if="!tickets.length" icon="chat-square-dots" title="No messages yet" text="Messages you send to support will appear here with replies." />
    <div v-else class="d-grid gap-3">
      <div v-for="t in tickets" :key="t.id" class="border rounded-4 p-3">
        <div class="d-flex justify-content-between flex-wrap gap-2">
          <div><span class="badge-soft bs-secondary me-2">#{{ t.id }} · {{ t.category }}</span><b>{{ t.subject }}</b></div>
          <StatusBadge :status="t.status" />
        </div>
        <p class="small text-muted mt-2 mb-2">{{ t.message }}</p>
        <div class="small text-muted"><i class="bi bi-clock me-1"></i>{{ $f.fmtDateTime(t.created_at) }}</div>
        <div v-if="t.admin_reply" class="reply mt-3">
          <div class="small fw-bold text-primary mb-1"><i class="bi bi-reply me-1"></i>Support replied · {{ $f.timeAgo(t.replied_at) }}</div>
          <div class="small">{{ t.admin_reply }}</div>
        </div>
      </div>
    </div>
  </div>
</template>
<script>
import api from '@/services/api'
import LoadingBlock from './LoadingBlock.vue'
import EmptyState from './EmptyState.vue'
import StatusBadge from './StatusBadge.vue'
export default {
  name: 'TicketList',
  components: { LoadingBlock, EmptyState, StatusBadge },
  data: () => ({ tickets: [], loading: true }),
  mounted () { this.load() },
  methods: {
    async load () {
      this.loading = true
      try { this.tickets = (await api.get('/my/tickets')).data.data } catch (e) { this.$error(e) }
      this.loading = false
    }
  }
}
</script>
<style scoped>.reply { background: rgba(79,70,229,.06); border-left: 3px solid var(--emp-primary); border-radius: 10px; padding: .75rem 1rem; }</style>
