<template>
  <div>
    <div class="table-responsive">
      <table class="table table-emp">
        <thead><tr><th>#</th><th>Student</th><th v-if="showExam">Examination</th><th>Slot</th><th>Examiner</th><th>Status</th><th>Evaluation</th><th class="text-end">Actions</th></tr></thead>
        <tbody>
          <tr v-if="!bookings.length"><td :colspan="showExam ? 8 : 7" class="text-center text-muted py-4">No bookings</td></tr>
          <tr v-for="b in bookings" :key="b.id">
            <td class="text-muted small">{{ b.id }}</td>
            <td>
              <router-link :to="'/admin/users/' + b.student_id" class="fw-semibold text-decoration-none">{{ b.student_name }}</router-link>
              <div class="small text-muted">{{ b.roll_no }}</div>
            </td>
            <td v-if="showExam"><div class="fw-semibold">{{ b.exam_name }}</div><small class="text-muted">{{ b.course_code }}</small></td>
            <td><div>{{ $f.fmtDay(b.date) }}</div><small class="text-muted">{{ $f.fmtTime(b.start_time) }}<span v-if="b.reschedule_count" class="badge-soft bs-warning ms-1">rescheduled</span></small></td>
            <td>{{ b.examiner_name || '—' }}</td>
            <td><StatusBadge :status="b.status" /><div v-if="b.cancel_reason" class="small text-muted mt-1" :title="b.cancel_reason">by {{ b.cancelled_by }}</div></td>
            <td>
              <span v-if="b.evaluation_status === 'submitted'" class="fw-semibold">{{ b.total_marks }}<small class="text-muted">/{{ b.max_marks }}</small></span>
              <StatusBadge v-else-if="b.evaluation_status" status="draft" label="Draft" />
              <span v-else class="small text-muted">—</span>
            </td>
            <td class="text-end text-nowrap">
              <template v-if="b.status === 'booked' && b.evaluation_status !== 'submitted'">
                <button class="btn btn-sm btn-icon btn-soft me-1" title="Reschedule / reassign" @click="openMove(b)"><i class="bi bi-arrow-repeat"></i></button>
                <button class="btn btn-sm btn-icon btn-soft-danger" title="Cancel booking" @click="cancel(b)"><i class="bi bi-x-lg"></i></button>
              </template>
              <a v-if="b.submission_link" :href="b.submission_link" target="_blank" rel="noopener" class="btn btn-sm btn-icon btn-light ms-1" title="Submission"><i class="bi bi-link-45deg"></i></a>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <BaseModal :show="mv.show" title="Reschedule booking" subtitle="Move the student to another slot (possibly with another examiner)" icon="arrow-repeat" @close="mv.show = false">
      <div v-if="mv.b" class="small mb-3"><b>{{ mv.b.student_name }}</b> · {{ mv.b.exam_name }}<br><span class="text-muted">Current: {{ $f.fmtDay(mv.b.date) }} {{ $f.fmtTime(mv.b.start_time) }} with {{ mv.b.examiner_name }}</span></div>
      <div v-if="!mv.options.length" class="text-muted small">No other slot with free seats. Increase a slot's capacity or ask an examiner to add slots.</div>
      <div class="d-grid gap-2">
        <label v-for="s in mv.options" :key="s.id" class="pick" :class="{ on: mv.id === s.id }">
          <input type="radio" class="d-none" :value="s.id" v-model="mv.id">
          <i class="bi bi-calendar-event text-primary"></i>
          <div class="flex-grow-1"><div class="fw-semibold small">{{ $f.fmtDay(s.date) }} · {{ $f.fmtTime(s.start_time) }}–{{ $f.fmtTime(s.end_time) }}</div><small class="text-muted">{{ s.examiner_name }}</small></div>
          <span class="badge-soft bs-success">{{ s.available_seats }} free</span>
        </label>
      </div>
      <label class="form-label mt-3">Note (optional)</label>
      <input v-model="mv.note" class="form-control" placeholder="e.g. Examiner on leave">
      <template #footer><button class="btn btn-light" @click="mv.show = false">Cancel</button><button class="btn btn-gradient" :disabled="!mv.id" @click="move">Move booking</button></template>
    </BaseModal>
  </div>
</template>

<script>
import api from '@/services/api'
import BaseModal from '@/components/common/BaseModal.vue'
import StatusBadge from '@/components/common/StatusBadge.vue'
export default {
  name: 'BookingTable',
  components: { BaseModal, StatusBadge },
  props: { bookings: Array, showExam: Boolean },
  emits: ['changed'],
  data: () => ({ mv: { show: false, b: null, options: [], id: null, note: '' } }),
  methods: {
    async openMove (b) {
      const slots = (await api.get('/admin/slots', { params: { exam_id: b.exam_id } })).data.data
      const today = this.$f.todayISO()
      this.mv = { show: true, b, id: null, note: '', options: slots.filter(s => s.id !== b.slot_id && s.status === 'available' && s.available_seats > 0 && s.date >= today) }
    },
    async move () {
      try { const r = await api.post(`/admin/bookings/${this.mv.b.id}/reschedule`, { slot_id: this.mv.id, note: this.mv.note }); this.$toast(r.data.message); this.mv.show = false; this.$emit('changed') } catch (e) { this.$error(e) }
    },
    async cancel (b) {
      const reason = await this.$confirm({ title: 'Cancel booking?', message: `Cancel ${b.student_name}'s booking for ${b.exam_name}? The seat will be released.`, input: 'Reason', variant: 'danger', confirmText: 'Cancel booking', icon: 'x-octagon' })
      if (!reason) return
      try { const r = await api.post(`/admin/bookings/${b.id}/cancel`, { reason: reason.trim() }); this.$toast(r.data.message); this.$emit('changed') } catch (e) { this.$error(e) }
    }
  }
}
</script>
<style scoped>
.pick { display: flex; gap: .75rem; align-items: center; padding: .6rem .8rem; border: 1.5px solid var(--emp-border); border-radius: 12px; cursor: pointer; }
.pick.on { border-color: var(--emp-primary); background: rgba(79,70,229,.07); }
</style>
