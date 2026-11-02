<template>
  <div>
    <PageHeader title="Support tickets" subtitle="Messages from the contact page (guests) and from logged-in users." :crumbs="[{ label: 'Admin', to: '/admin' }, { label: 'Support' }]" />
    <div class="row g-4">
      <div class="col-lg-5">
        <div class="card-emp">
          <div class="p-3 border-bottom d-flex gap-2 flex-wrap">
            <button v-for="s in ['', 'open', 'replied', 'closed']" :key="s" class="btn btn-sm" :class="status === s ? 'btn-primary' : 'btn-light'" @click="status = s">{{ s ? $f.statusMeta(s).label : 'All' }} <span class="opacity-75">({{ count(s) }})</span></button>
          </div>
          <LoadingBlock v-if="loading" class="p-3" />
          <EmptyState v-else-if="!list.length" icon="inbox" title="No tickets" />
          <div class="ticket-list">
            <div v-for="t in list" :key="t.id" class="t-item" :class="{ sel: sel && sel.id === t.id }" @click="select(t)">
              <div class="d-flex justify-content-between gap-2">
                <div class="fw-semibold text-truncate">{{ t.subject }}</div><StatusBadge :status="t.status" />
              </div>
              <div class="small text-muted">{{ t.name }} · <span class="text-capitalize">{{ t.role }}</span> · {{ $f.timeAgo(t.created_at) }}</div>
            </div>
          </div>
        </div>
      </div>
      <div class="col-lg-7">
        <div class="card-emp" v-if="sel">
          <div class="card-header d-flex justify-content-between align-items-center">
            <span>#{{ sel.id }} · {{ sel.subject }}</span><span class="badge-soft bs-secondary">{{ sel.category }}</span>
          </div>
          <div class="card-body">
            <div class="d-flex gap-2 align-items-center mb-3">
              <span class="avatar">{{ $f.initials(sel.name) }}</span>
              <div><div class="fw-semibold">{{ sel.name }} <span class="badge-soft bs-primary text-capitalize ms-1">{{ sel.role }}</span></div><small class="text-muted">{{ sel.email }} · {{ $f.fmtDateTime(sel.created_at) }}</small></div>
              <router-link v-if="sel.user_id" :to="'/admin/users/' + sel.user_id" class="btn btn-sm btn-soft ms-auto">Profile</router-link>
            </div>
            <div class="msg">{{ sel.message }}</div>
            <div v-if="sel.admin_reply" class="reply mt-3"><div class="small fw-bold text-primary mb-1">Your reply · {{ $f.fmtDateTime(sel.replied_at) }}</div>{{ sel.admin_reply }}</div>
            <form class="mt-4" @submit.prevent="reply">
              <label class="form-label">{{ sel.admin_reply ? 'Send another reply' : 'Reply' }}</label>
              <textarea v-model.trim="text" rows="4" class="form-control" placeholder="Write your reply – it is e-mailed to the sender" required></textarea>
              <div class="d-flex flex-wrap gap-2 mt-3">
                <div class="form-check me-auto"><input id="cl" v-model="close" class="form-check-input" type="checkbox"><label for="cl" class="form-check-label small">Close ticket after replying</label></div>
                <button type="button" v-if="sel.status !== 'closed'" class="btn btn-light" @click="setStatus('closed')">Close without reply</button>
                <button type="button" v-else class="btn btn-light" @click="setStatus('open')">Re-open</button>
                <button class="btn btn-gradient"><i class="bi bi-send me-1"></i>Send reply</button>
              </div>
            </form>
          </div>
        </div>
        <div v-else class="card-emp"><EmptyState icon="chat-left-text" title="Select a ticket" text="Choose a ticket from the list to read and reply." /></div>
      </div>
    </div>
  </div>
</template>
<script>
import api from '@/services/api'
import PageHeader from '@/components/common/PageHeader.vue'
import LoadingBlock from '@/components/common/LoadingBlock.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import StatusBadge from '@/components/common/StatusBadge.vue'
export default {
  name: 'AdminSupport',
  components: { PageHeader, LoadingBlock, EmptyState, StatusBadge },
  data: () => ({ tickets: [], loading: true, status: '', sel: null, text: '', close: false }),
  computed: { list () { return this.tickets.filter(t => !this.status || t.status === this.status) } },
  mounted () { this.load() },
  methods: {
    count (s) { return this.tickets.filter(t => !s || t.status === s).length },
    async load () {
      this.loading = true
      try { this.tickets = (await api.get('/admin/tickets')).data.data; if (this.sel) this.sel = this.tickets.find(t => t.id === this.sel.id) } catch (e) { this.$error(e) }
      this.loading = false
    },
    select (t) { this.sel = t; this.text = ''; this.close = false },
    async reply () {
      try { const r = await api.post(`/admin/tickets/${this.sel.id}/reply`, { reply: this.text, close: this.close }); this.$toast(r.data.message); this.text = ''; this.load() } catch (e) { this.$error(e) }
    },
    async setStatus (s) {
      try { await api.post(`/admin/tickets/${this.sel.id}/status`, { status: s }); this.$toast('Ticket updated'); this.load() } catch (e) { this.$error(e) }
    }
  }
}
</script>
<style scoped>
.ticket-list { max-height: 620px; overflow-y: auto; }
.t-item { padding: .9rem 1rem; border-bottom: 1px solid var(--emp-border); cursor: pointer; }
.t-item:hover { background: rgba(79,70,229,.04); }
.t-item.sel { background: rgba(79,70,229,.08); border-left: 3px solid var(--emp-primary); }
.msg { background: var(--bs-tertiary-bg); border-radius: 12px; padding: 1rem; white-space: pre-wrap; }
.reply { background: rgba(79,70,229,.06); border-left: 3px solid var(--emp-primary); border-radius: 10px; padding: .75rem 1rem; white-space: pre-wrap; }
</style>
