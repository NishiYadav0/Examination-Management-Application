<template>
  <form :id="formId" @submit.prevent="submit" novalidate class="row g-3">
    <div class="col-md-6">
      <label class="form-label">Course *</label>
      <select v-model="f.course_id" class="form-select" :class="{ 'is-invalid': e.course_id }">
        <option value="">Select course</option>
        <option v-for="c in courses" :key="c.id" :value="c.id">{{ c.code }} – {{ c.name }}</option>
      </select>
      <div class="invalid-feedback">{{ e.course_id }}</div>
    </div>
    <div class="col-md-6">
      <label class="form-label">Examination type *</label>
      <select v-model="f.exam_type" class="form-select"><option v-for="t in types" :key="t">{{ t }}</option></select>
    </div>
    <div class="col-12">
      <label class="form-label">Examination name *</label>
      <input v-model.trim="f.name" class="form-control" :class="{ 'is-invalid': e.name }" maxlength="150" placeholder="e.g. MAD-II Project Viva">
      <div class="invalid-feedback">{{ e.name }}</div>
    </div>
    <div class="col-md-4">
      <label class="form-label">Duration (min) *</label>
      <input v-model.number="f.duration_minutes" type="number" min="5" max="600" class="form-control" :class="{ 'is-invalid': e.duration_minutes }">
      <div class="invalid-feedback">{{ e.duration_minutes }}</div>
    </div>
    <div class="col-md-4">
      <label class="form-label">Maximum marks *</label>
      <input v-model.number="f.max_marks" type="number" min="1" max="1000" step="0.5" class="form-control" :class="{ 'is-invalid': e.max_marks }">
      <div class="invalid-feedback">{{ e.max_marks }}</div>
    </div>
    <div class="col-md-4">
      <label class="form-label">Pass marks</label>
      <input v-model.number="f.pass_marks" type="number" min="0" :max="f.max_marks" step="0.5" class="form-control" :class="{ 'is-invalid': e.pass_marks }">
      <div class="invalid-feedback">{{ e.pass_marks }}</div>
    </div>
    <div class="col-12"><div class="small-caps text-primary mt-2"><i class="bi bi-calendar-range me-1"></i>Timeline</div></div>
    <div class="col-md-6" v-for="w in windows" :key="w.k">
      <label class="form-label">{{ w.label }} *</label>
      <div class="input-group">
        <input v-model="f[w.k + '_start']" type="date" class="form-control" :class="{ 'is-invalid': e[w.k + '_start'] }" aria-label="start">
        <span class="input-group-text">→</span>
        <input v-model="f[w.k + '_end']" type="date" class="form-control" :class="{ 'is-invalid': e[w.k + '_end'] }" :min="f[w.k + '_start']" aria-label="end">
      </div>
      <div class="small text-danger mt-1" v-if="e[w.k + '_start'] || e[w.k + '_end']">{{ e[w.k + '_start'] || e[w.k + '_end'] }}</div>
      <div class="form-text">{{ w.help }}</div>
    </div>
    <div class="col-12"><label class="form-label">Description</label><textarea v-model="f.description" class="form-control" rows="2"></textarea></div>
    <div class="col-12"><label class="form-label">Instructions for students</label><textarea v-model="f.instructions" class="form-control" rows="2" placeholder="Shown on booking and in reminder e-mails"></textarea></div>
    <div class="col-md-6">
      <div class="form-check form-switch">
        <input id="reqsub" v-model="f.requires_submission" class="form-check-input" type="checkbox">
        <label for="reqsub" class="form-check-label">Require project / submission link while booking</label>
      </div>
    </div>
    <div class="col-12">
      <label class="form-label">Result release to students</label>
      <div class="d-flex flex-wrap gap-2">
        <label class="rel" :class="{ on: !f.auto_publish }"><input type="radio" class="d-none" :value="false" v-model="f.auto_publish">
          <i class="bi bi-megaphone"></i><div><b>After admin publishes</b><small class="d-block text-muted">Students get marks + e-mail when you click Publish</small></div></label>
        <label class="rel" :class="{ on: f.auto_publish }"><input type="radio" class="d-none" :value="true" v-model="f.auto_publish">
          <i class="bi bi-lightning-charge"></i><div><b>Instantly after evaluation</b><small class="d-block text-muted">Each student gets marks + e-mail as soon as the examiner submits</small></div></label>
      </div>
    </div>
    <div class="col-12" v-if="examiners.length">
      <label class="form-label">Assign examiners</label>
      <div class="d-flex flex-wrap gap-2">
        <label v-for="x in examiners" :key="x.id" class="ex-chip" :class="{ on: f.examiner_ids.includes(x.id), off: !x.active }">
          <input type="checkbox" class="d-none" :value="x.id" v-model="f.examiner_ids" :disabled="!x.active">
          <span class="avatar avatar-sm">{{ $f.initials(x.name) }}</span>{{ x.name }}
        </label>
      </div>
      <div class="form-text"><i class="bi bi-envelope me-1"></i>Newly assigned (or removed) examiners are notified by e-mail and in-app.</div>
    </div>
  </form>
</template>

<script>
import api from '@/services/api'
import { EXAM_TYPES } from '@/utils/format'

function addDays (n) { const d = new Date(); d.setDate(d.getDate() + n); d.setMinutes(d.getMinutes() - d.getTimezoneOffset()); return d.toISOString().slice(0, 10) }

export default {
  name: 'ExamForm',
  props: { exam: Object, formId: { type: String, default: 'examForm' } },
  emits: ['saved', 'busy'],
  data () {
    const x = this.exam
    return {
      types: EXAM_TYPES, courses: [], examiners: [], e: {},
      windows: [
        { k: 'slot_creation', label: 'Slot creation period', help: 'Examiners publish slots in this period' },
        { k: 'booking', label: 'Booking period', help: 'Students book / cancel slots in this period' },
        { k: 'exam', label: 'Examination period', help: 'Dates on which slots can be scheduled' }
      ],
      f: x ? { ...x, examiner_ids: (x.examiners || []).map(e => e.id) } : {
        course_id: this.$route.query.course_id ? Number(this.$route.query.course_id) : '', exam_type: 'Viva', name: '', duration_minutes: 20, max_marks: 100, pass_marks: 40,
        slot_creation_start: addDays(0), slot_creation_end: addDays(5), booking_start: addDays(6), booking_end: addDays(12),
        exam_start: addDays(8), exam_end: addDays(20), description: '', instructions: '', requires_submission: false, auto_publish: false, examiner_ids: []
      }
    }
  },
  async mounted () {
    const [c, x] = await Promise.all([api.get('/admin/courses'), api.get('/admin/examiners')])
    this.courses = c.data.data
    this.examiners = x.data.data
  },
  methods: {
    validate () {
      const e = {}; const f = this.f
      if (!f.course_id) e.course_id = 'Select a course'
      if (!f.name) e.name = 'Name is required'
      if (!(f.duration_minutes >= 5)) e.duration_minutes = 'Min 5 minutes'
      if (!(f.max_marks > 0)) e.max_marks = 'Must be positive'
      if (f.pass_marks > f.max_marks) e.pass_marks = 'Cannot exceed max marks'
      for (const w of this.windows) {
        if (!f[w.k + '_start']) e[w.k + '_start'] = 'Start date required'
        if (!f[w.k + '_end']) e[w.k + '_end'] = 'End date required'
        else if (f[w.k + '_start'] > f[w.k + '_end']) e[w.k + '_end'] = 'End must be on/after start'
      }
      if (f.booking_start && f.slot_creation_start && f.booking_start < f.slot_creation_start) e.booking_start = 'Booking cannot start before slot creation'
      this.e = e
      return !Object.keys(e).length
    },
    async submit () {
      if (!this.validate()) return
      this.$emit('busy', true)
      try {
        const res = this.f.id ? await api.put(`/admin/exams/${this.f.id}`, this.f) : await api.post('/admin/exams', this.f)
        this.$toast(res.data.message)
        this.$emit('saved', res.data.data)
      } catch (err) { this.e = err.fieldErrors || {}; this.$error(err) }
      this.$emit('busy', false)
    }
  }
}
</script>
<style scoped>
.ex-chip { display: inline-flex; align-items: center; gap: .5rem; padding: .3rem .8rem .3rem .3rem; border: 1.5px solid var(--emp-border); border-radius: 999px; cursor: pointer; font-size: .85rem; font-weight: 500; }
.ex-chip.on { border-color: var(--emp-primary); background: rgba(79,70,229,.08); color: var(--emp-primary); }
.ex-chip.off { opacity: .45; cursor: not-allowed; }
.rel { display: flex; gap: .7rem; align-items: flex-start; flex: 1 1 240px; padding: .75rem .9rem; border: 1.5px solid var(--emp-border); border-radius: 12px; cursor: pointer; font-size: .88rem; }
.rel i { font-size: 1.2rem; color: var(--emp-muted); }
.rel.on { border-color: var(--emp-primary); background: rgba(79,70,229,.06); }
.rel.on i { color: var(--emp-primary); }
</style>
