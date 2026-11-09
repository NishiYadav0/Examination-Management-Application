<template>
  <div>
    <PageHeader title="Notifications" :subtitle="unread + ' unread'">
      <button class="btn btn-soft" :disabled="!unread" @click="$store.dispatch('notif/readAll')"><i class="bi bi-check2-all me-1"></i>Mark all as read</button>
    </PageHeader>
    <ul class="nav nav-pills nav-pills-emp mb-3 gap-2">
      <li v-for="t in tabs" :key="t"><button class="nav-link text-capitalize" :class="{ active: tab === t }" @click="tab = t">{{ t }}</button></li>
    </ul>
    <div class="card-emp">
      <EmptyState v-if="!list.length" icon="bell-slash" title="You're all caught up" text="New alerts about bookings, results and schedules will appear here." />
      <div v-for="n in list" :key="n.id" class="n-row" :class="{ unread: !n.is_read }">
        <span class="icon-box" :class="'bg-' + color(n.type) + ' bg-opacity-10 text-' + color(n.type)"><i :class="'bi bi-' + icon(n.type)"></i></span>
        <div class="flex-grow-1 min-w-0 cursor-pointer" @click="open(n)">
          <div class="fw-semibold">{{ n.title }} <span v-if="!n.is_read" class="badge bg-primary ms-1">New</span></div>
          <div class="small text-muted">{{ n.message }}</div>
          <div class="small text-muted mt-1"><i class="bi bi-clock me-1"></i>{{ $f.fmtDateTime(n.created_at) }}</div>
        </div>
        <button class="btn btn-icon btn-soft-danger" @click="remove(n)" title="Delete"><i class="bi bi-trash"></i></button>
      </div>
    </div>
  </div>
</template>
<script>
import api from '@/services/api'
import PageHeader from '@/components/common/PageHeader.vue'
import EmptyState from '@/components/common/EmptyState.vue'
export default {
  name: 'NotificationsView',
  components: { PageHeader, EmptyState },
  data: () => ({ tab: 'all', tabs: ['all', 'unread', 'read'] }),
  computed: {
    items () { return this.$store.state.notif.items },
    unread () { return this.$store.state.notif.unread },
    list () { return this.items.filter(n => this.tab === 'all' || (this.tab === 'unread' ? !n.is_read : n.is_read)) }
  },
  mounted () { this.$store.dispatch('notif/load') },
  methods: {
    color (t) { return { success: 'success', warning: 'warning', danger: 'danger' }[t] || 'primary' },
    icon (t) { return { success: 'check-circle', warning: 'exclamation-triangle', danger: 'x-octagon' }[t] || 'info-circle' },
    async open (n) { if (!n.is_read) await this.$store.dispatch('notif/read', n.id); if (n.link) this.$router.push(n.link) },
    async remove (n) { await api.delete(`/notifications/${n.id}`); this.$store.dispatch('notif/load') }
  }
}
</script>
<style scoped>
.n-row { display: flex; gap: 1rem; align-items: center; padding: 1rem 1.25rem; border-bottom: 1px solid var(--emp-border); }
.n-row:last-child { border-bottom: 0; }
.n-row.unread { background: rgba(79,70,229,.04); }
</style>
