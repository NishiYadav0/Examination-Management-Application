<template>
  <form :id="formId" class="row g-3" @submit.prevent="submit" novalidate>
    <div class="col-md-4">
      <label class="form-label">Date *</label>
      <input v-model="f.date" type="date" class="form-control" :class="{ 'is-invalid': e.date }" :min="minDate" :max="exam.exam_end">
      <div class="invalid-feedback">{{ e.date }}</div>
    </div>
    <div class="col-6 col-md-4">
      <label class="form-label">Start time *</label>
      <input v-model="f.start_time" type="time" class="form-control" :class="{ 'is-invalid': e.start_time }" @change="autoEnd">
      <div class="invalid-feedback">{{ e.start_time }}</div>
    </div>
    <div class="col-6 col-md-4">
      <label class="form-label">End time *</label>
      <input v-model="f.end_time" type="time" class="form-control" :class="{ 'is-invalid': e.end_time }">
      <div class="invalid-feedback">{{ e.end_time }}</div>
    </div>
    <div class="col-md-4">
      <label class="form-label">Capacity (students) *</label>
      <input v-model.number="f.capacity" type="number" min="1" max="200" class="form-control" :class="{ 'is-invalid': e.capacity }">
      <div class="invalid-feedback">{{ e.capacity }}</div>
    </div>
    <div class="col-md-4">
      <label class="form-label">Mode</label>
      <select v-model="f.mode" class="form-select"><option value="online">Online</option><option value="offline">Offline (in person)</option></select>
    </div>
    <div class="col-md-4" v-if="f.mode === 'offline'">
      <label class="form-label">Venue *</label>
      <input v-model.trim="f.venue" class="form-control" :class="{ 'is-invalid': e.venue }" placeholder="Lab 2, Block A">
      <div class="invalid-feedback">{{ e.venue }}</div>
    </div>
    <div :class="f.mode === 'offline' ? 'col-12' : 'col-md-4'">
      <label class="form-label">Meeting link</label>
      <input v-model.trim="f.meeting_link" type="url" class="form-control" :class="{ 'is-invalid': e.meeting_link }" placeholder="https://meet.google.com/…">
      <div class="invalid-feedback">{{ e.meeting_link }}</div>
    </div>
    <div class="col-12"><label class="form-label">Notes for students</label><input v-model.trim="f.notes" class="form-control" maxlength="300" placeholder="Optional"></div>
    <div class="col-12" v-if="!slot">
      <div class="split p-3">
        <div class="form-check form-switch">
          <input id="split" v-model="f.auto_split" class="form-check-input" type="checkbox">
          <label for="split" class="form-check-label fw-semibold">Auto-split into back-to-back {{ exam.duration_minutes }}-minute slots</label>
        </div>
        <div class="small text-muted mt-1">
          <template v-if="f.auto_split">This will create <b>{{ splitCount }}</b> slot(s) between {{ f.start_time || '--' }} and {{ f.end_time || '--' }}.</template>
          <template v-else>Handy for vivas: choose 10:00–12:00 to publish several short slots at once.</template>
        </div>
      </div>
    </div>
  </form>
</template>
<script>
import api from '@/services/api'
export default {
  name: 'SlotForm',
  props: { exam: Object, slot: Object, formId: { type: String, default: 'slotForm' } },
  emits: ['saved'],
  data () {
    const s = this.slot
    const today = this.$f.todayISO()
    const minDate = this.exam.exam_start > today ? this.exam.exam_start : today
    return {
      e: {}, minDate,
      f: s ? { ...s } : { date: minDate, start_time: '10:00', end_time: '', capacity: 1, mode: 'online', meeting_link: '', venue: '', notes: '', auto_split: false }
    }
  },
  created () { if (!this.slot) this.autoEnd() },
  computed: {
    splitCount () {
      if (!this.f.start_time || !this.f.end_time) return 0
      const m = (t) => { const [h, mm] = t.split(':').map(Number); return h * 60 + mm }
      return Math.max(0, Math.floor((m(this.f.end_time) - m(this.f.start_time)) / this.exam.duration_minutes))
    }
  },
  methods: {
    autoEnd () {
      if (!this.f.start_time) return
      const [h, m] = this.f.start_time.split(':').map(Number)
      const t = h * 60 + m + this.exam.duration_minutes * (this.f.auto_split ? 4 : 1)
      if (!this.f.end_time || this.f.end_time <= this.f.start_time) this.f.end_time = `${String(Math.floor(t / 60) % 24).padStart(2, '0')}:${String(t % 60).padStart(2, '0')}`
    },
    validate () {
      const e = {}; const f = this.f
      if (!f.date) e.date = 'Required'
      else if (f.date < this.minDate) e.date = 'Date cannot be in the past or before the exam period'
      else if (this.exam.exam_end && f.date > this.exam.exam_end) e.date = 'After the exam period'
      if (!f.start_time) e.start_time = 'Required'
      if (!f.end_time) e.end_time = 'Required'
      else if (f.end_time <= f.start_time) e.end_time = 'Must be after start'
      if (!(f.capacity >= 1)) e.capacity = 'At least 1'
      if (f.mode === 'offline' && !f.venue) e.venue = 'Venue required'
      if (f.meeting_link && !/^https?:\/\//.test(f.meeting_link)) e.meeting_link = 'Must start with http(s)://'
      if (f.auto_split && this.splitCount < 1) e.end_time = 'Window too short for one slot'
      this.e = e
      return !Object.keys(e).length
    },
    async submit () {
      if (!this.validate()) return
      try {
        const r = this.slot ? await api.put(`/examiner/slots/${this.slot.id}`, this.f) : await api.post('/examiner/slots', { ...this.f, exam_id: this.exam.id })
        this.$toast(r.data.message)
        this.$emit('saved')
      } catch (err) { this.e = err.fieldErrors || {}; this.$error(err) }
    }
  }
}
</script>
<style scoped>.split { border: 1px dashed var(--emp-border); border-radius: 12px; background: rgba(79,70,229,.03); }</style>
