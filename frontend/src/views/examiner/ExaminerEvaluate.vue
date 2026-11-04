<template>
  <div>
    <LoadingBlock v-if="!d" cards />
    <template v-else>
      <PageHeader :title="'Evaluate · ' + d.student.name" :subtitle="d.exam.name + ' · ' + d.exam.exam_type" :crumbs="[{ label: 'Examiner', to: '/examiner' }, { label: 'Students', to: '/examiner/students' }, { label: 'Evaluate' }]" />
      <div v-if="!d.locked" class="alert small d-flex gap-2 align-items-center" :class="d.instant_release ? 'alert-success' : 'alert-secondary'">
        <i :class="d.instant_release ? 'bi bi-lightning-charge-fill' : 'bi bi-megaphone'"></i>
        <div v-if="d.instant_release"><b>Instant result release:</b> when you submit, the student immediately sees the marks and receives an e-mail with the criterion-wise result.</div>
        <div v-else><b>Results are released by the admin:</b> on submit the student is told (in-app + e-mail) that the exam is evaluated; marks become visible after the admin publishes.</div>
      </div>
      <div v-if="d.locked" class="alert alert-info"><i class="bi bi-lock me-1"></i>Results are published – this evaluation is read-only.</div>
      <div v-else-if="!d.can_evaluate" class="alert alert-warning"><i class="bi bi-clock me-1"></i>This slot is on {{ $f.fmtDate(d.booking.date) }}. You can evaluate after the examination takes place.</div>
      <div v-else-if="d.booking.status === 'absent'" class="alert alert-danger"><i class="bi bi-person-x me-1"></i>The student is marked absent. Mark them present from the students list to evaluate.</div>

      <div class="row g-4">
        <div class="col-xl-4 order-xl-2">
          <div class="card-emp mb-4 sticky-xl">
            <div class="card-body text-center">
              <span class="avatar avatar-lg">{{ $f.initials(d.student.name) }}</span>
              <h5 class="fw-bold mt-3 mb-0">{{ d.student.name }}</h5>
              <div class="small text-muted">{{ d.student.profile.roll_no }} · {{ d.student.profile.program }}</div>
              <div class="divider my-3"></div>
              <div class="small text-start d-grid gap-2">
                <div><i class="bi bi-calendar-event me-2 text-muted"></i>{{ $f.fmtDay(d.booking.date) }} · {{ $f.fmtTime(d.booking.start_time) }}–{{ $f.fmtTime(d.booking.end_time) }}</div>
                <div v-if="d.booking.submission_link"><i class="bi bi-link-45deg me-2 text-muted"></i><a :href="d.booking.submission_link" target="_blank" rel="noopener">Submission link</a></div>
                <div v-if="d.booking.meeting_link"><i class="bi bi-camera-video me-2 text-muted"></i><a :href="d.booking.meeting_link" target="_blank" rel="noopener">Meeting link</a></div>
                <div v-if="d.booking.student_note"><i class="bi bi-chat-left-quote me-2 text-muted"></i>{{ d.booking.student_note }}</div>
              </div>
            </div>
            <div class="total-box">
              <div class="small text-white-50">Weighted total</div>
              <div class="display-5 fw-800">{{ total.toFixed(2) }}<span class="fs-5 opacity-75"> / {{ d.exam.max_marks }}</span></div>
              <div class="d-flex justify-content-center gap-2 mt-1">
                <span class="badge bg-light text-dark">{{ pct.toFixed(1) }}%</span>
                <span class="badge bg-light text-dark">Grade {{ grade }}</span>
                <span class="badge" :class="total >= d.exam.pass_marks ? 'bg-success' : 'bg-danger'">{{ total >= d.exam.pass_marks ? 'Pass' : 'Below pass' }}</span>
              </div>
            </div>
          </div>
        </div>

        <div class="col-xl-8 order-xl-1">
          <div class="card-emp mb-4">
            <div class="card-header d-flex justify-content-between"><span><i class="bi bi-grid-3x3-gap me-2 text-primary"></i>Rubric</span><small class="text-muted">{{ filled }}/{{ d.exam.rubrics.length }} criteria scored</small></div>
            <div class="card-body">
              <div v-for="r in d.exam.rubrics" :key="r.id" class="crit" :class="{ err: errors[r.id] }">
                <div class="d-flex justify-content-between flex-wrap gap-2">
                  <div><div class="fw-bold">{{ r.criterion }} <span class="badge-soft bs-primary ms-1">{{ r.weightage }}%</span></div><small class="text-muted">{{ r.description }}</small></div>
                  <div class="d-flex align-items-center gap-2">
                    <input v-model.number="scores[r.id].marks" type="number" :min="0" :max="r.max_marks" step="0.5" class="form-control form-control-sm text-center fw-bold" style="width:90px" :disabled="readonly" :aria-label="r.criterion">
                    <span class="text-muted small">/ {{ r.max_marks }}</span>
                  </div>
                </div>
                <input v-model.number="scores[r.id].marks" type="range" class="form-range mt-2" :min="0" :max="r.max_marks" step="0.5" :disabled="readonly">
                <div class="d-flex gap-1 flex-wrap mb-2">
                  <button v-for="p in [0, 25, 50, 75, 100]" :key="p" type="button" class="btn btn-sm btn-light py-0 px-2" :disabled="readonly" @click="scores[r.id].marks = Math.round(r.max_marks * p / 100 * 2) / 2">{{ p }}%</button>
                </div>
                <input v-model="scores[r.id].comment" class="form-control form-control-sm" placeholder="Comment for this criterion (optional)" maxlength="300" :disabled="readonly">
                <div v-if="errors[r.id]" class="small text-danger mt-1">{{ errors[r.id] }}</div>
              </div>
            </div>
          </div>

          <div class="card-emp">
            <div class="card-header"><i class="bi bi-chat-square-text me-2 text-primary"></i>Feedback</div>
            <div class="card-body row g-3">
              <div class="col-12"><label class="form-label">Overall remarks *</label><textarea v-model="remarks" rows="3" class="form-control" :class="{ 'is-invalid': errors.remarks }" :disabled="readonly" placeholder="Summary visible to the student"></textarea><div class="invalid-feedback">{{ errors.remarks }}</div></div>
              <div class="col-md-6"><label class="form-label">Strengths</label><textarea v-model="strengths" rows="2" class="form-control" :disabled="readonly"></textarea></div>
              <div class="col-md-6"><label class="form-label">Areas to improve</label><textarea v-model="improvements" rows="2" class="form-control" :disabled="readonly"></textarea></div>
              <div class="col-12 d-flex flex-wrap gap-2" v-if="!readonly">
                <router-link to="/examiner/students" class="btn btn-light">Back</router-link>
                <button class="btn btn-outline-primary ms-auto" :disabled="busy" @click="save(false)"><i class="bi bi-save me-1"></i>Save draft</button>
                <button class="btn btn-gradient" :disabled="busy" @click="save(true)"><i class="bi bi-send-check me-1"></i>{{ d.evaluation && d.evaluation.status === 'submitted' ? 'Update evaluation' : 'Submit evaluation' }}</button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </template>
  </div>
</template>
<script>
import api from '@/services/api'
import PageHeader from '@/components/common/PageHeader.vue'
import LoadingBlock from '@/components/common/LoadingBlock.vue'
function gradeFor (p) { return p >= 90 ? 'S' : p >= 80 ? 'A' : p >= 70 ? 'B' : p >= 60 ? 'C' : p >= 50 ? 'D' : p >= 40 ? 'E' : 'U' }
export default {
  name: 'ExaminerEvaluate',
  components: { PageHeader, LoadingBlock },
  props: { id: String },
  data: () => ({ d: null, scores: {}, remarks: '', strengths: '', improvements: '', errors: {}, busy: false }),
  computed: {
    readonly () { return this.d.locked || !this.d.can_evaluate || this.d.booking.status === 'absent' },
    total () {
      return this.d.exam.rubrics.reduce((a, r) => {
        const m = Number(this.scores[r.id].marks)
        return a + (isNaN(m) || this.scores[r.id].marks === '' ? 0 : Math.min(m, r.max_marks) / r.max_marks * r.weightage / 100 * this.d.exam.max_marks)
      }, 0)
    },
    pct () { return this.total / this.d.exam.max_marks * 100 },
    grade () { return gradeFor(this.pct) },
    filled () { return this.d.exam.rubrics.filter(r => this.scores[r.id].marks !== '' && this.scores[r.id].marks != null).length }
  },
  async mounted () {
    try {
      const d = (await api.get(`/examiner/bookings/${this.id}/evaluation`)).data.data
      const sc = {}
      d.exam.rubrics.forEach(r => {
        const ex = d.evaluation && d.evaluation.scores.find(s => s.rubric_id === r.id)
        sc[r.id] = { marks: ex ? ex.marks : '', comment: ex ? ex.comment || '' : '' }
      })
      this.scores = sc
      if (d.evaluation) { this.remarks = d.evaluation.remarks || ''; this.strengths = d.evaluation.strengths || ''; this.improvements = d.evaluation.improvements || '' }
      this.d = d
    } catch (e) { this.$error(e); this.$router.push('/examiner/students') }
  },
  methods: {
    validate (submit) {
      const e = {}
      this.d.exam.rubrics.forEach(r => {
        const m = this.scores[r.id].marks
        if (m === '' || m == null) { if (submit) e[r.id] = 'Marks required' } else if (m < 0 || m > r.max_marks) e[r.id] = `Enter 0 – ${r.max_marks}`
      })
      if (submit && !this.remarks.trim()) e.remarks = 'Remarks are required to submit'
      this.errors = e
      return !Object.keys(e).length
    },
    async save (submit) {
      if (!this.validate(submit)) return this.$toast('Please correct the highlighted fields', 'warning')
      if (submit && !await this.$confirm({ title: 'Submit evaluation?', message: `Total ${this.total.toFixed(2)} / ${this.d.exam.max_marks} (${this.grade}). ` + (this.d.instant_release ? 'The student will see these marks immediately and get an e-mail.' : 'The student is notified; marks appear after the admin publishes.'), confirmText: 'Submit', icon: 'send-check' })) return
      this.busy = true
      try {
        const payload = { scores: Object.entries(this.scores).map(([rid, s]) => ({ rubric_id: Number(rid), marks: s.marks, comment: s.comment })), remarks: this.remarks, strengths: this.strengths, improvements: this.improvements, submit }
        const r = await api.post(`/examiner/bookings/${this.id}/evaluation`, payload)
        this.$toast(r.data.message)
        if (submit) this.$router.push('/examiner/students?evaluation=pending')
      } catch (err) { this.errors = err.fieldErrors || {}; this.$error(err) }
      this.busy = false
    }
  }
}
</script>
<style scoped>
.crit { border: 1px solid var(--emp-border); border-radius: 14px; padding: 1rem; margin-bottom: 1rem; }
.crit.err { border-color: #ef4444; }
.total-box { background: var(--emp-gradient); color: #fff; text-align: center; padding: 1.5rem; border-radius: 0 0 16px 16px; }
@media (min-width: 1200px) { .sticky-xl { position: sticky; top: 90px; } }
</style>
