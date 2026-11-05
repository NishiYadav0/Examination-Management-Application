<template>
  <div>
    <div class="table-responsive">
      <table class="table table-emp">
        <thead><tr><th>#</th><th v-if="showExam">Examination</th><th>Examiner</th><th>Date & time</th><th>Mode</th><th>Seats</th><th>Status</th><th class="text-end">Actions</th></tr></thead>
        <tbody>
          <tr v-if="!slots.length"><td :colspan="showExam ? 8 : 7" class="text-center text-muted py-4">No slots</td></tr>
          <tr v-for="s in slots" :key="s.id">
            <td class="text-muted small">{{ s.id }}</td>
            <td v-if="showExam"><div class="fw-semibold">{{ s.exam_name }}</div><small class="text-muted">{{ s.course_code }} · {{ s.exam_type }}</small></td>
            <td><div class="d-flex align-items-center gap-2"><span class="avatar avatar-sm">{{ $f.initials(s.examiner_name || '?') }}</span><span>{{ s.examiner_name || '—' }}</span></div></td>
            <td><div>{{ $f.fmtDay(s.date) }}</div><small class="text-muted">{{ $f.fmtTime(s.start_time) }} – {{ $f.fmtTime(s.end_time) }}</small></td>
            <td><span class="badge-soft" :class="s.mode === 'online' ? 'bs-info' : 'bs-warning'"><i :class="s.mode === 'online' ? 'bi bi-camera-video' : 'bi bi-geo-alt'"></i> {{ s.mode }}</span></td>
            <td style="min-width:110px">
              <div class="small">{{ s.booked_count }}/{{ s.capacity }} booked</div>
              <div class="progress" style="height:5px"><div class="progress-bar" :class="s.booked_count >= s.capacity ? 'bg-danger' : 'bg-primary'" :style="{ width: (s.booked_count / s.capacity * 100) + '%' }"></div></div>
            </td>
            <td><StatusBadge :status="s.status" /></td>
            <td class="text-end text-nowrap">
              <template v-if="!['cancelled', 'completed'].includes(s.status)">
                <button class="btn btn-sm btn-icon btn-soft me-1" title="Reschedule" @click="openEdit(s)"><i class="bi bi-calendar2-week"></i></button>
                <button class="btn btn-sm btn-icon btn-soft-warning me-1" title="Change examiner" @click="openReassign(s)"><i class="bi bi-arrow-left-right"></i></button>
                <button class="btn btn-sm btn-icon btn-soft-danger" title="Cancel slot" @click="cancel(s)"><i class="bi bi-x-lg"></i></button>
              </template>
              <span v-else class="small text-muted">—</span>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <BaseModal :show="edit.show" title="Reschedule slot" subtitle="Booked students and the examiner are notified automatically" icon="calendar2-week" @close="edit.show = false">
      <form id="slotEdit" class="row g-3" @submit.prevent="saveEdit">
        <div class="col-12"><label class="form-label">Date</label><input v-model="edit.f.date" type="date" class="form-control" required></div>
        <div class="col-6"><label class="form-label">Start</label><input v-model="edit.f.start_time" type="time" class="form-control" required></div>
        <div class="col-6"><label class="form-label">End</label><input v-model="edit.f.end_time" type="time" class="form-control" required></div>
        <div class="col-6"><label class="form-label">Capacity</label><input v-model.number="edit.f.capacity" type="number" min="1" class="form-control" required></div>
        <div class="col-6"><label class="form-label">Venue</label><input v-model="edit.f.venue" class="form-control"></div>
        <div class="col-12"><label class="form-label">Meeting link</label><input v-model="edit.f.meeting_link" type="url" class="form-control" placeholder="https://"></div>
      </form>
      <template #footer><button class="btn btn-light" @click="edit.show = false">Cancel</button><button class="btn btn-gradient" form="slotEdit">Save</button></template>
    </BaseModal>

    <BaseModal :show="re.show" title="Change examiner" subtitle="Use only in exceptional situations" icon="arrow-left-right" @close="re.show = false">
      <p class="small text-muted" v-if="re.slot">Slot #{{ re.slot.id }} · {{ $f.fmtDay(re.slot.date) }} {{ $f.fmtTime(re.slot.start_time) }} — currently <b>{{ re.slot.examiner_name }}</b></p>
      <div class="d-grid gap-2">
        <label v-for="x in examiners" :key="x.id" class="pick" :class="{ on: re.id === x.id, off: !x.active || (re.slot && x.id === re.slot.examiner_id) }">
          <input type="radio" class="d-none" :value="x.id" v-model="re.id" :disabled="!x.active || (re.slot && x.id === re.slot.examiner_id)">
          <span class="avatar avatar-sm">{{ $f.initials(x.name) }}</span>
          <div><div class="fw-semibold small">{{ x.name }}</div><small class="text-muted">{{ x.profile.department }} · {{ x.slots }} slots</small></div>
        </label>
      </div>
      <template #footer><button class="btn btn-light" @click="re.show = false">Cancel</button><button class="btn btn-gradient" :disabled="!re.id" @click="saveReassign">Reassign</button></template>
    </BaseModal>
  </div>
</template>

<script>
import api from '@/services/api'
import BaseModal from '@/components/common/BaseModal.vue'
import StatusBadge from '@/components/common/StatusBadge.vue'
export default {
  name: 'SlotTable',
  components: { BaseModal, StatusBadge },
  props: { slots: Array, showExam: Boolean },
  emits: ['changed'],
  data: () => ({ edit: { show: false, f: {} }, re: { show: false, slot: null, id: null }, examiners: [] }),
  methods: {
    openEdit (s) { this.edit = { show: true, f: { ...s } } },
    async saveEdit () {
      try { const r = await api.put(`/admin/slots/${this.edit.f.id}`, this.edit.f); this.$toast(r.data.message); this.edit.show = false; this.$emit('changed') } catch (e) { this.$error(e) }
    },
    async openReassign (s) {
      if (!this.examiners.length) this.examiners = (await api.get('/admin/examiners')).data.data
      this.re = { show: true, slot: s, id: null }
    },
    async saveReassign () {
      try { const r = await api.post(`/admin/slots/${this.re.slot.id}/reassign`, { examiner_id: this.re.id }); this.$toast(r.data.message); this.re.show = false; this.$emit('changed') } catch (e) { this.$error(e) }
    },
    async cancel (s) {
      const reason = await this.$confirm({ title: 'Cancel this slot?', message: `${s.booked_count} booked student(s) will be cancelled and notified.`, input: 'Reason (shown to students)', variant: 'danger', confirmText: 'Cancel slot', icon: 'calendar-x' })
      if (!reason) return
      try { const r = await api.post(`/admin/slots/${s.id}/cancel`, { reason: reason.trim() }); this.$toast(r.data.message); this.$emit('changed') } catch (e) { this.$error(e) }
    }
  }
}
</script>
<style scoped>
.pick { display: flex; gap: .75rem; align-items: center; padding: .6rem .8rem; border: 1.5px solid var(--emp-border); border-radius: 12px; cursor: pointer; }
.pick.on { border-color: var(--emp-primary); background: rgba(79,70,229,.07); }
.pick.off { opacity: .45; cursor: not-allowed; }
</style>
