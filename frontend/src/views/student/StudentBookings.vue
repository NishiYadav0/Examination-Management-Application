<template>
  <div>
    <PageHeader title="My bookings" subtitle="Your booking status and complete examination history." :crumbs="[{ label: 'Student', to: '/student' }, { label: 'Bookings' }]">
      <router-link to="/student/exams?availability=bookable" class="btn btn-gradient"><i class="bi bi-plus-lg me-1"></i>Book a slot</router-link>
    </PageHeader>
    <ul class="nav nav-pills nav-pills-emp mb-3 gap-2 flex-nowrap overflow-auto">
      <li v-for="t in tabs" :key="t.k"><button class="nav-link text-nowrap" :class="{ active: tab === t.k }" @click="tab = t.k">{{ t.label }} <span class="opacity-75">({{ count(t.k) }})</span></button></li>
    </ul>
    <LoadingBlock v-if="loading" />
    <EmptyState v-else-if="!list.length" icon="calendar-x" title="No bookings here" text="Book a slot from Browse Exams." />
    <div class="d-grid gap-3">
      <div v-for="b in list" :key="b.id" class="card-emp booking fade-in" :class="'b-' + b.status">
        <div class="card-body d-flex flex-wrap gap-3 align-items-center">
          <div class="date-box"><div>{{ new Date(b.date).getDate() }}</div><small>{{ new Date(b.date).toLocaleString('en', { month: 'short' }) }}</small></div>
          <div class="flex-grow-1 min-w-0">
            <div class="d-flex flex-wrap gap-2 align-items-center"><b>{{ b.exam_name }}</b><span class="badge-soft bs-secondary">{{ b.course_code }}</span><span class="badge-soft bs-info">{{ b.exam_type }}</span></div>
            <div class="small text-muted mt-1">
              <i class="bi bi-clock me-1"></i>{{ $f.fmtTime(b.start_time) }}–{{ $f.fmtTime(b.end_time) }}
              <i class="bi bi-person ms-3 me-1"></i>{{ b.examiner_name }}
              <span v-if="b.mode === 'offline'"><i class="bi bi-geo-alt ms-3 me-1"></i>{{ b.venue }}</span>
            </div>
            <div class="small text-muted"><i class="bi bi-bookmark me-1"></i>Booked {{ $f.fmtDateTime(b.booked_at) }} · #{{ b.id }}
              <span v-if="b.reschedule_count" class="text-warning ms-2"><i class="bi bi-arrow-repeat"></i> Rescheduled by admin{{ b.admin_note ? ': ' + b.admin_note : '' }}</span></div>
            <div v-if="b.status === 'cancelled'" class="small text-danger mt-1">Cancelled by {{ b.cancelled_by }} {{ b.cancel_reason ? '· ' + b.cancel_reason : '' }}</div>
          </div>
          <div class="text-end">
            <StatusBadge :status="b.status" />
            <div v-if="b.status === 'completed'" class="small mt-1">
              <router-link v-if="b.results_published" :to="'/student/results/' + b.id" class="fw-semibold">{{ b.total_marks }}/{{ b.max_marks }} · View</router-link>
              <span v-else class="text-muted">Result pending</span>
            </div>
          </div>
          <div class="d-flex gap-2 w-100 w-md-auto justify-content-end" v-if="b.status === 'booked'">
            <a v-if="b.meeting_link" :href="b.meeting_link" target="_blank" rel="noopener" class="btn btn-sm btn-soft"><i class="bi bi-camera-video me-1"></i>Join</a>
            <router-link :to="'/student/exams/' + b.exam_id" class="btn btn-sm btn-light">Details</router-link>
            <button class="btn btn-sm btn-soft-danger" :disabled="!b.can_cancel" :title="b.can_cancel ? 'Cancel booking' : 'Cancellation deadline passed'" @click="cancel(b)"><i class="bi bi-x-lg me-1"></i>Cancel</button>
          </div>
        </div>
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
  name: 'StudentBookings',
  components: { PageHeader, LoadingBlock, EmptyState, StatusBadge },
  data: () => ({ rows: [], loading: true, tab: 'upcoming', tabs: [{ k: 'upcoming', label: 'Upcoming' }, { k: 'completed', label: 'Completed' }, { k: 'cancelled', label: 'Cancelled' }, { k: 'absent', label: 'Absent' }, { k: 'all', label: 'All history' }] }),
  computed: {
    list () { return this.rows.filter(b => this.match(b, this.tab)) }
  },
  mounted () { this.load() },
  methods: {
    match (b, t) { return t === 'all' || (t === 'upcoming' ? b.status === 'booked' : b.status === t) },
    count (t) { return this.rows.filter(b => this.match(b, t)).length },
    async load () { this.loading = true; try { this.rows = (await api.get('/student/bookings')).data.data } catch (e) { this.$error(e) } this.loading = false },
    async cancel (b) {
      const reason = await this.$confirm({ title: 'Cancel this booking?', message: `${b.exam_name} on ${this.$f.fmtDay(b.date)} at ${this.$f.fmtTime(b.start_time)}. The seat will be released for others.`, input: 'Reason (optional)', variant: 'danger', confirmText: 'Yes, cancel', cancelText: 'Keep booking', icon: 'calendar-x' })
      if (!reason) return
      try { const r = await api.post(`/student/bookings/${b.id}/cancel`, { reason: reason.trim() }); this.$toast(r.data.message, 'warning'); this.$store.dispatch('notif/load'); this.load() } catch (e) { this.$error(e) }
    }
  }
}
</script>
<style scoped>
.booking { border-left: 4px solid var(--emp-primary); }
.b-completed { border-left-color: #10b981; } .b-cancelled { border-left-color: #94a3b8; } .b-absent { border-left-color: #ef4444; }
.date-box { width: 56px; text-align: center; border-radius: 14px; background: rgba(79,70,229,.08); color: var(--emp-primary); padding: .45rem 0; font-weight: 800; font-size: 1.2rem; line-height: 1.1; }
.date-box small { font-size: .68rem; text-transform: uppercase; display: block; }
@media (min-width: 768px) { .w-md-auto { width: auto !important; } }
</style>
