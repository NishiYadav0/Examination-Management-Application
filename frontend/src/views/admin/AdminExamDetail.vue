<template>
  <div>
    <LoadingBlock v-if="!exam" cards />
    <template v-else>
      <PageHeader :title="exam.name" :subtitle="exam.course_code + ' · ' + exam.course_name" :crumbs="[{ label: 'Admin', to: '/admin' }, { label: 'Examinations', to: '/admin/exams' }, { label: exam.name }]">
        <button class="btn btn-light" @click="editShow = true" :disabled="exam.results_published"><i class="bi bi-pencil me-1"></i>Edit</button>
        <button class="btn btn-soft-danger" @click="remove"><i class="bi bi-trash"></i></button>
      </PageHeader>

      <!-- lifecycle stepper -->
      <div class="card-emp p-3 p-md-4 mb-4">
        <div class="stepper">
          <div v-for="(s, i) in steps" :key="s.k" class="st" :class="{ done: i < stepIndex, current: i === stepIndex }">
            <span class="dot"><i :class="'bi bi-' + (i < stepIndex ? 'check-lg' : s.i)"></i></span>
            <div class="small fw-semibold mt-2">{{ s.label }}</div>
          </div>
        </div>
        <div class="divider my-3"></div>
        <div class="d-flex flex-wrap gap-2 align-items-center">
          <span class="small text-muted me-2"><i class="bi bi-lightning-charge me-1"></i>Actions:</span>
          <button v-for="a in actions" :key="a.action" class="btn btn-sm" :class="a.cls" @click="changeStatus(a)"><i :class="'bi bi-' + a.icon + ' me-1'"></i>{{ a.label }}</button>
          <button v-if="!exam.results_published && ['closed', 'completed'].includes(exam.status)" class="btn btn-sm btn-success" @click="publish()"><i class="bi bi-megaphone me-1"></i>Publish results</button>
          <button v-if="exam.results_published" class="btn btn-sm btn-soft-warning" @click="unpublish"><i class="bi bi-eye-slash me-1"></i>Withdraw results</button>
          <span v-if="!actions.length && !['closed', 'completed'].includes(exam.status)" class="small text-muted">No actions available</span>
        </div>
        <div v-if="warnings.length" class="mt-3">
          <div v-for="w in warnings" :key="w" class="small text-warning-emphasis"><i class="bi bi-exclamation-triangle me-1"></i>{{ w }}</div>
        </div>
      </div>

      <div class="row g-3 mb-4">
        <div class="col-6 col-lg-2" v-for="s in summaryCards" :key="s.label"><StatCard v-bind="s" /></div>
      </div>

      <ul class="nav nav-pills nav-pills-emp mb-3 gap-2 flex-nowrap overflow-auto">
        <li v-for="t in tabs" :key="t.k"><button class="nav-link text-nowrap" :class="{ active: tab === t.k }" @click="tab = t.k"><i :class="'bi bi-' + t.i + ' me-1'"></i>{{ t.label }}</button></li>
      </ul>

      <!-- OVERVIEW -->
      <div v-if="tab === 'overview'" class="row g-4">
        <div class="col-lg-7">
          <div class="card-emp h-100">
            <div class="card-header"><i class="bi bi-calendar-range me-2 text-primary"></i>Timeline</div>
            <div class="card-body">
              <div v-for="w in windowsView" :key="w.label" class="win mb-3">
                <div class="d-flex justify-content-between small mb-1">
                  <span class="fw-semibold"><i :class="'bi bi-' + w.icon + ' me-1'" :style="{ color: w.color }"></i>{{ w.label }}</span>
                  <span class="text-muted">{{ $f.fmtDate(w.start) }} → {{ $f.fmtDate(w.end) }}</span>
                </div>
                <div class="progress" style="height:10px"><div class="progress-bar" :style="{ width: w.pct + '%', background: w.color }"></div></div>
                <div class="small mt-1" :class="w.active ? 'text-success' : 'text-muted'">{{ w.note }}</div>
              </div>
            </div>
          </div>
        </div>
        <div class="col-lg-5">
          <div class="card-emp h-100">
            <div class="card-header"><i class="bi bi-info-circle me-2 text-primary"></i>Details</div>
            <div class="card-body small">
              <dl class="row mb-0">
                <dt class="col-5 text-muted fw-normal">Type</dt><dd class="col-7">{{ exam.exam_type }}</dd>
                <dt class="col-5 text-muted fw-normal">Duration</dt><dd class="col-7">{{ exam.duration_minutes }} minutes</dd>
                <dt class="col-5 text-muted fw-normal">Max / pass marks</dt><dd class="col-7">{{ exam.max_marks }} / {{ exam.pass_marks }}</dd>
                <dt class="col-5 text-muted fw-normal">Submission link</dt><dd class="col-7">{{ exam.requires_submission ? 'Required' : 'Not required' }}</dd>
                <dt class="col-5 text-muted fw-normal">Result release</dt><dd class="col-7">{{ exam.auto_publish ? '⚡ Instantly after each evaluation' : 'After admin publishes' }}</dd>
                <dt class="col-5 text-muted fw-normal">Results</dt><dd class="col-7">{{ exam.results_published ? 'Published ' + $f.fmtDateTime(exam.published_at) : 'Not published' }}</dd>
                <dt class="col-5 text-muted fw-normal">Created</dt><dd class="col-7">{{ $f.fmtDateTime(exam.created_at) }}</dd>
              </dl>
              <div class="divider my-3"></div>
              <div class="fw-semibold mb-1">Description</div><p class="text-muted">{{ exam.description || '—' }}</p>
              <div class="fw-semibold mb-1">Instructions</div><p class="text-muted mb-0">{{ exam.instructions || '—' }}</p>
            </div>
          </div>
        </div>
      </div>

      <!-- RUBRIC -->
      <div v-if="tab === 'rubric'" class="card-emp">
        <div class="card-header d-flex flex-wrap justify-content-between align-items-center gap-2">
          <span><i class="bi bi-grid-3x3-gap me-2 text-primary"></i>Rubric builder</span>
          <span class="badge-soft" :class="Math.abs(weightTotal - 100) < 0.01 ? 'bs-success' : 'bs-danger'">Weightage total: {{ weightTotal }}%</span>
        </div>
        <div class="card-body">
          <div v-if="rubricLocked" class="alert alert-warning small"><i class="bi bi-lock me-1"></i>Evaluations have started – the rubric is locked to keep marks consistent.</div>
          <p class="small text-muted">Each criterion is scored out of its own maximum. The final mark = Σ (marks ÷ criterion max × weightage%) × {{ exam.max_marks }}.</p>
          <div class="table-responsive">
            <table class="table table-emp align-middle">
              <thead><tr><th style="width:26%">Criterion *</th><th style="width:12%">Max marks *</th><th style="width:12%">Weightage % *</th><th>Description</th><th style="width:10%">Worth</th><th></th></tr></thead>
              <tbody>
                <tr v-for="(r, i) in rubric" :key="i">
                  <td><input v-model.trim="r.criterion" class="form-control form-control-sm" :disabled="rubricLocked" placeholder="e.g. Code quality"></td>
                  <td><input v-model.number="r.max_marks" type="number" min="0.5" step="0.5" class="form-control form-control-sm" :disabled="rubricLocked"></td>
                  <td><input v-model.number="r.weightage" type="number" min="0.5" max="100" step="0.5" class="form-control form-control-sm" :disabled="rubricLocked"></td>
                  <td><input v-model="r.description" class="form-control form-control-sm" :disabled="rubricLocked" placeholder="What to look for"></td>
                  <td class="small text-muted">{{ ((r.weightage || 0) / 100 * exam.max_marks).toFixed(1) }} marks</td>
                  <td><button class="btn btn-sm btn-icon btn-soft-danger" :disabled="rubricLocked" @click="rubric.splice(i, 1)"><i class="bi bi-trash"></i></button></td>
                </tr>
              </tbody>
            </table>
          </div>
          <div class="d-flex flex-wrap gap-2 mt-2">
            <button class="btn btn-soft" :disabled="rubricLocked" @click="rubric.push({ criterion: '', max_marks: 10, weightage: 0, description: '' })"><i class="bi bi-plus-lg me-1"></i>Add criterion</button>
            <button class="btn btn-light" :disabled="rubricLocked" @click="autoWeights">Auto-distribute weightage</button>
            <button class="btn btn-light" :disabled="rubricLocked" @click="openCopy"><i class="bi bi-copy me-1"></i>Copy rubric from another exam</button>
            <button class="btn btn-gradient ms-auto" :disabled="rubricLocked || !rubric.length" @click="saveRubric"><i class="bi bi-save me-1"></i>Save rubric</button>
          </div>
        </div>
      </div>

      <!-- EXAMINERS -->
      <div v-if="tab === 'examiners'" class="card-emp">
        <div class="card-header d-flex justify-content-between align-items-center">
          <span><i class="bi bi-person-badge me-2 text-primary"></i>Assigned examiners <small class="text-muted fw-normal ms-1">· assigned examiners are e-mailed automatically</small></span>
          <button class="btn btn-sm btn-gradient" @click="saveExaminers"><i class="bi bi-save me-1"></i>Save assignment</button>
        </div>
        <div class="card-body">
          <div class="row g-3">
            <div class="col-md-6 col-xl-4" v-for="x in allExaminers" :key="x.id">
              <label class="ex-card" :class="{ on: assigned.includes(x.id), off: !x.active }">
                <input type="checkbox" class="form-check-input me-1" :value="x.id" v-model="assigned" :disabled="!x.active">
                <span class="avatar">{{ $f.initials(x.name) }}</span>
                <div class="min-w-0"><div class="fw-semibold">{{ x.name }}</div>
                  <small class="text-muted">{{ x.profile.designation }} · {{ x.profile.department }}</small>
                  <div class="small text-muted">{{ slotsOf(x.id) }} slot(s) in this exam <span v-if="!x.active" class="text-danger">· blocked</span></div></div>
              </label>
            </div>
          </div>
        </div>
      </div>

      <!-- SLOTS -->
      <div v-if="tab === 'slots'" class="card-emp">
        <div class="card-header"><i class="bi bi-calendar3-week me-2 text-primary"></i>All examiner slots ({{ slots.length }})</div>
        <SlotTable :slots="slots" @changed="load" />
      </div>

      <!-- BOOKINGS -->
      <div v-if="tab === 'bookings'" class="card-emp">
        <div class="card-header d-flex justify-content-between align-items-center flex-wrap gap-2">
          <span><i class="bi bi-bookmark-star me-2 text-primary"></i>Bookings</span>
          <select v-model="bStatus" class="form-select form-select-sm" style="width:auto"><option value="">All</option><option v-for="s in ['booked','completed','absent','cancelled']" :key="s" :value="s">{{ $f.statusMeta(s).label }}</option></select>
        </div>
        <BookingTable :bookings="bookings.filter(b => !bStatus || b.status === bStatus)" @changed="load" />
      </div>

      <!-- RESULTS -->
      <div v-if="tab === 'results'" class="card-emp">
        <div class="card-header d-flex justify-content-between align-items-center flex-wrap gap-2">
          <span><i class="bi bi-trophy me-2 text-primary"></i>Results</span>
          <div class="d-flex gap-2">
            <button class="btn btn-sm btn-light" @click="exportCsv"><i class="bi bi-filetype-csv me-1"></i>Download CSV</button>
            <button v-if="!exam.results_published" class="btn btn-sm btn-success" :disabled="!['closed', 'completed'].includes(exam.status)" @click="publish()"><i class="bi bi-megaphone me-1"></i>Publish</button>
          </div>
        </div>
        <div class="table-responsive">
          <table class="table table-emp">
            <thead><tr><th>Student</th><th>Examiner</th><th v-for="r in exam.rubrics" :key="r.id" class="text-center">{{ r.criterion }}<div class="fw-normal">/{{ r.max_marks }}</div></th><th>Total</th><th>Grade</th><th>Status</th></tr></thead>
            <tbody>
              <tr v-if="!results.length"><td :colspan="5 + exam.rubrics.length" class="text-center text-muted py-4">No bookings yet</td></tr>
              <tr v-for="r in results" :key="r.id">
                <td><div class="fw-semibold">{{ r.student_name }}</div><small class="text-muted">{{ r.roll_no }}</small></td>
                <td class="small">{{ r.examiner_name }}</td>
                <td v-for="c in exam.rubrics" :key="c.id" class="text-center">{{ score(r, c.id) }}</td>
                <td class="fw-bold">{{ r.evaluation && r.evaluation.status === 'submitted' ? r.evaluation.total_marks : '—' }}</td>
                <td><span v-if="r.evaluation && r.evaluation.status === 'submitted'" class="fw-bold" :style="{ color: $f.gradeColor(r.evaluation.grade) }">{{ r.evaluation.grade }}</span></td>
                <td><StatusBadge :status="r.status === 'absent' ? 'absent' : (r.evaluation ? (r.evaluation.status === 'submitted' ? 'submitted' : 'draft') : 'pending')" /></td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <BaseModal :show="copy.show" title="Copy rubric from another exam" subtitle="Pick an examination – its criteria are loaded into the builder so you can review, edit and then save" icon="copy" size="lg" @close="copy.show = false">
        <div class="input-group mb-3">
          <span class="input-group-text"><i class="bi bi-search"></i></span>
          <input v-model="copy.q" class="form-control" placeholder="Search exam, course or type">
        </div>
        <div v-if="copy.loading" class="text-center py-3"><span class="spinner-border spinner-border-sm"></span></div>
        <div v-else-if="!copySources.length" class="text-center text-muted small py-3">No other examination has a rubric yet.</div>
        <div class="row g-3">
          <div class="col-md-5">
            <div class="d-grid gap-2 copy-list">
              <label v-for="e in copySources" :key="e.id" class="pick" :class="{ on: copy.id === e.id }">
                <input type="radio" class="d-none" :value="e.id" v-model="copy.id" @change="previewCopy">
                <div class="min-w-0 flex-grow-1">
                  <div class="fw-semibold small">{{ e.name }}</div>
                  <small class="text-muted">{{ e.course_code }} · {{ e.exam_type }} · {{ e.rubric_count }} criteria</small>
                </div>
                <span v-if="e.exam_type === exam.exam_type" class="badge-soft bs-success flex-shrink-0" title="Same examination type">same type</span>
              </label>
            </div>
          </div>
          <div class="col-md-7">
            <div v-if="!copy.id" class="text-muted small text-center py-5 border rounded-4"><i class="bi bi-arrow-left me-1"></i>Select an examination to preview its rubric</div>
            <div v-else class="border rounded-4 p-3">
              <div class="small-caps text-muted mb-2">Preview</div>
              <div v-for="r in copy.preview" :key="r.id" class="mb-2">
                <div class="d-flex justify-content-between small"><b>{{ r.criterion }}</b><span>{{ r.weightage }}% · /{{ r.max_marks }}</span></div>
                <div class="progress" style="height:6px"><div class="progress-bar" :style="{ width: r.weightage + '%' }"></div></div>
                <small class="text-muted">{{ r.description }}</small>
              </div>
              <div class="divider my-3"></div>
              <div class="small fw-semibold mb-1">How to apply</div>
              <div class="form-check"><input id="cpR" v-model="copy.mode" class="form-check-input" type="radio" value="replace"><label for="cpR" class="form-check-label small">Replace the current criteria</label></div>
              <div class="form-check"><input id="cpA" v-model="copy.mode" class="form-check-input" type="radio" value="append" :disabled="!rubric.length"><label for="cpA" class="form-check-label small">Add to the current criteria (re-balance weightage after)</label></div>
            </div>
          </div>
        </div>
        <template #footer>
          <button class="btn btn-light" @click="copy.show = false">Cancel</button>
          <button class="btn btn-gradient" :disabled="!copy.preview.length" @click="applyCopy"><i class="bi bi-box-arrow-in-down me-1"></i>Load into builder</button>
        </template>
      </BaseModal>

      <BaseModal :show="editShow" title="Edit examination" icon="pencil-square" size="lg" @close="editShow = false">
        <ExamForm v-if="editShow" :exam="exam" form-id="examEdit" @saved="editShow = false; load()" />
        <template #footer><button class="btn btn-light" @click="editShow = false">Cancel</button><button class="btn btn-gradient" form="examEdit">Save changes</button></template>
      </BaseModal>
    </template>
  </div>
</template>

<script>
import api from '@/services/api'
import { downloadBlob } from '@/utils/format'
import PageHeader from '@/components/common/PageHeader.vue'
import LoadingBlock from '@/components/common/LoadingBlock.vue'
import StatCard from '@/components/common/StatCard.vue'
import StatusBadge from '@/components/common/StatusBadge.vue'
import BaseModal from '@/components/common/BaseModal.vue'
import ExamForm from '@/components/admin/ExamForm.vue'
import SlotTable from '@/components/admin/SlotTable.vue'
import BookingTable from '@/components/admin/BookingTable.vue'

const ACTIONS = {
  draft: [{ action: 'open_slot_creation', label: 'Open slot creation', icon: 'unlock', cls: 'btn-primary' }],
  slot_creation: [{ action: 'open_booking', label: 'Open student booking', icon: 'door-open', cls: 'btn-primary' }, { action: 'close_slot_creation', label: 'Close slot creation', icon: 'lock', cls: 'btn-soft-warning' }],
  booking_open: [{ action: 'close_booking', label: 'Close booking', icon: 'lock', cls: 'btn-warning' }, { action: 'open_slot_creation', label: 'Re-open slot creation', icon: 'unlock', cls: 'btn-soft' }],
  closed: [{ action: 'open_booking', label: 'Re-open booking', icon: 'door-open', cls: 'btn-soft' }, { action: 'complete', label: 'Mark completed', icon: 'check2-circle', cls: 'btn-primary' }],
  completed: []
}

export default {
  name: 'AdminExamDetail',
  components: { PageHeader, LoadingBlock, StatCard, StatusBadge, BaseModal, ExamForm, SlotTable, BookingTable },
  props: { id: String },
  data: () => ({
    exam: null, tab: 'overview', rubric: [], allExaminers: [], assigned: [], bookings: [], results: [], bStatus: '', editShow: false,
    copy: { show: false, loading: false, exams: [], q: '', id: null, preview: [], mode: 'replace' },
    steps: [{ k: 'draft', label: 'Draft', i: 'pencil' }, { k: 'slot_creation', label: 'Slot creation', i: 'calendar-plus' },
      { k: 'booking_open', label: 'Booking open', i: 'door-open' }, { k: 'closed', label: 'Closed', i: 'lock' }, { k: 'completed', label: 'Completed', i: 'trophy' }],
    tabs: [{ k: 'overview', label: 'Overview', i: 'info-circle' }, { k: 'rubric', label: 'Rubric', i: 'grid-3x3-gap' }, { k: 'examiners', label: 'Examiners', i: 'person-badge' },
      { k: 'slots', label: 'Slots', i: 'calendar3-week' }, { k: 'bookings', label: 'Bookings', i: 'bookmark-star' }, { k: 'results', label: 'Results', i: 'trophy' }]
  }),
  computed: {
    stepIndex () { return this.steps.findIndex(s => s.k === this.exam.status) },
    actions () { return ACTIONS[this.exam.status] || [] },
    slots () { return this.exam.slots || [] },
    copySources () {
      const q = this.copy.q.toLowerCase()
      return this.copy.exams
        .filter(e => e.id !== this.exam.id && e.rubric_count > 0 && (!q || [e.name, e.course_code, e.exam_type].join(' ').toLowerCase().includes(q)))
        .sort((a, b) => (b.exam_type === this.exam.exam_type) - (a.exam_type === this.exam.exam_type))
    },
    rubricLocked () { return this.results.some(r => r.evaluation) },
    weightTotal () { return Math.round(this.rubric.reduce((a, r) => a + (Number(r.weightage) || 0), 0) * 100) / 100 },
    warnings () {
      const w = []
      if (!this.exam.examiners.length) w.push('No examiners assigned yet.')
      if (Math.abs(this.exam.rubric_weightage - 100) > 0.01) w.push(`Rubric weightage is ${this.exam.rubric_weightage}% – it must total 100% before slot creation.`)
      if (this.exam.status === 'slot_creation' && !this.exam.timeline_checks.slot_creation_today) w.push('Today is outside the slot creation period – examiners cannot create slots.')
      if (this.exam.status === 'booking_open' && !this.exam.timeline_checks.booking_today) w.push('Today is outside the booking period – students cannot book.')
      return w
    },
    summaryCards () {
      const s = this.exam.summary
      return [
        { label: 'Slots', value: this.exam.slot_count, icon: 'calendar3-week', color: '#4f46e5' },
        { label: 'Seats free', value: this.exam.available_seats, icon: 'door-open', color: '#10b981' },
        { label: 'Bookings', value: s.bookings, icon: 'bookmark-star', color: '#06b6d4' },
        { label: 'Evaluated', value: s.evaluated, icon: 'clipboard-check', color: '#7c3aed' },
        { label: 'Pending', value: s.pending_evaluation, icon: 'hourglass-split', color: '#f59e0b' },
        { label: 'Avg marks', value: s.avg_marks ?? '—', icon: 'graph-up', color: '#ec4899' }
      ]
    },
    windowsView () {
      const today = this.$f.todayISO()
      const e = this.exam
      return [
        { label: 'Slot creation', start: e.slot_creation_start, end: e.slot_creation_end, icon: 'calendar-plus', color: '#06b6d4' },
        { label: 'Booking', start: e.booking_start, end: e.booking_end, icon: 'door-open', color: '#10b981' },
        { label: 'Examinations', start: e.exam_start, end: e.exam_end, icon: 'mic', color: '#7c3aed' }
      ].map(w => {
        const s = new Date(w.start); const en = new Date(w.end); const t = new Date(today)
        const pct = t < s ? 0 : t > en ? 100 : Math.round((t - s) / Math.max(en - s, 86400000) * 100)
        const active = today >= w.start && today <= w.end
        const note = today < w.start ? `Starts in ${this.$f.daysUntil(w.start)} day(s)` : today > w.end ? 'Period over' : `In progress · ${this.$f.daysUntil(w.end)} day(s) left`
        return { ...w, pct, active, note }
      })
    }
  },
  mounted () { this.load() },
  methods: {
    async load () {
      try {
        const [d, r, x] = await Promise.all([api.get(`/admin/exams/${this.id}`), api.get(`/admin/exams/${this.id}/results`), api.get('/admin/examiners')])
        this.exam = d.data.data
        this.rubric = this.exam.rubrics.map(r => ({ ...r }))
        this.results = r.data.data.results
        this.allExaminers = x.data.data
        this.assigned = this.exam.examiners.map(e => e.id)
        this.bookings = (await api.get('/admin/bookings', { params: { exam_id: this.id } })).data.data
      } catch (e) { this.$error(e); if (e.response && e.response.status === 404) this.$router.push('/admin/exams') }
    },
    slotsOf (id) { return this.slots.filter(s => s.examiner_id === id && s.status !== 'cancelled').length },
    score (r, rid) {
      if (!r.evaluation) return '—'
      const s = r.evaluation.scores.find(x => x.rubric_id === rid)
      return s ? s.marks : '—'
    },
    async changeStatus (a) {
      if (!await this.$confirm({ title: a.label + '?', message: `The examination status will change. Affected users are notified.`, confirmText: a.label, icon: a.icon })) return
      try { const r = await api.post(`/admin/exams/${this.id}/status`, { action: a.action }); this.$toast(r.data.message); this.load() } catch (e) { this.$error(e) }
    },
    async publish (force = false) {
      if (!force && !await this.$confirm({ title: 'Publish results?', message: 'Students will be able to see marks and feedback and will receive an e-mail.', confirmText: 'Publish', variant: 'success', icon: 'megaphone' })) return
      try {
        const r = await api.post(`/admin/exams/${this.id}/publish`, { force }); this.$toast(r.data.message); this.load()
      } catch (e) {
        if (e.response && e.response.status === 409 && e.fieldErrors && e.fieldErrors.pending) {
          if (await this.$confirm({ title: 'Some evaluations are pending', message: e.userMessage, confirmText: 'Publish anyway', variant: 'warning', icon: 'exclamation-triangle' })) this.publish(true)
        } else this.$error(e)
      }
    },
    async unpublish () {
      if (!await this.$confirm({ title: 'Withdraw results?', message: 'Students will no longer see marks until you publish again.', variant: 'warning', confirmText: 'Withdraw', icon: 'eye-slash' })) return
      try { const r = await api.post(`/admin/exams/${this.id}/unpublish`); this.$toast(r.data.message); this.load() } catch (e) { this.$error(e) }
    },
    async openCopy () {
      this.copy = { show: true, loading: true, exams: [], q: '', id: null, preview: [], mode: this.rubric.length ? 'replace' : 'replace' }
      try { this.copy.exams = (await api.get('/admin/exams')).data.data } catch (e) { this.$error(e) }
      this.copy.loading = false
    },
    async previewCopy () {
      try { this.copy.preview = (await api.get(`/admin/exams/${this.copy.id}/rubrics`)).data.data } catch (e) { this.$error(e) }
    },
    applyCopy () {
      const items = this.copy.preview.map(r => ({ criterion: r.criterion, max_marks: r.max_marks, weightage: r.weightage, description: r.description || '' }))
      this.rubric = this.copy.mode === 'append' ? [...this.rubric, ...items] : items
      const src = this.copy.exams.find(e => e.id === this.copy.id)
      this.copy.show = false
      this.$toast(`Loaded ${items.length} criteria from "${src ? src.name : 'exam'}". Review and click Save rubric.`, Math.abs(this.weightTotal - 100) < 0.01 ? 'success' : 'warning')
    },
    autoWeights () {
      const total = this.rubric.reduce((a, r) => a + (Number(r.max_marks) || 0), 0)
      if (!total) return
      let acc = 0
      this.rubric.forEach((r, i) => {
        if (i === this.rubric.length - 1) r.weightage = Math.round((100 - acc) * 100) / 100
        else { r.weightage = Math.round(r.max_marks / total * 10000) / 100; acc += r.weightage }
      })
    },
    async saveRubric () {
      if (this.rubric.some(r => !r.criterion || !(r.max_marks > 0) || !(r.weightage > 0))) return this.$toast('Every criterion needs a name, max marks and weightage', 'warning')
      if (Math.abs(this.weightTotal - 100) > 0.01) return this.$toast(`Weightages must add up to 100% (now ${this.weightTotal}%)`, 'warning')
      try { const r = await api.put(`/admin/exams/${this.id}/rubrics`, { rubrics: this.rubric }); this.$toast(r.data.message); this.load() } catch (e) { this.$error(e) }
    },
    async saveExaminers () {
      try { const r = await api.put(`/admin/exams/${this.id}/examiners`, { examiner_ids: this.assigned }); this.$toast(r.data.message); this.load() } catch (e) { this.$error(e) }
    },
    async remove () {
      if (!await this.$confirm({ title: 'Delete examination?', message: 'Only examinations without bookings can be deleted.', variant: 'danger', confirmText: 'Delete', icon: 'trash' })) return
      try { await api.delete(`/admin/exams/${this.id}`); this.$toast('Examination deleted'); this.$router.push('/admin/exams') } catch (e) { this.$error(e) }
    },
    exportCsv () {
      const head = ['Roll No', 'Student', 'Examiner', ...this.exam.rubrics.map(r => r.criterion), 'Total', 'Grade', 'Status']
      const rows = this.results.map(r => [r.roll_no, r.student_name, r.examiner_name, ...this.exam.rubrics.map(c => this.score(r, c.id)),
        r.evaluation ? r.evaluation.total_marks : '', r.evaluation ? r.evaluation.grade : '', r.status])
      const csv = [head, ...rows].map(row => row.map(v => `"${String(v ?? '').replace(/"/g, '""')}"`).join(',')).join('\n')
      downloadBlob(new Blob([csv], { type: 'text/csv' }), `${this.exam.name.replace(/\W+/g, '_')}_results.csv`)
    }
  }
}
</script>

<style scoped>
.stepper { display: flex; justify-content: space-between; position: relative; }
.stepper::before { content: ""; position: absolute; top: 20px; left: 8%; right: 8%; height: 3px; background: var(--emp-border); }
.st { flex: 1; text-align: center; position: relative; color: var(--emp-muted); }
.st .dot { width: 42px; height: 42px; border-radius: 50%; display: inline-flex; align-items: center; justify-content: center; background: var(--emp-card-bg); border: 3px solid var(--emp-border); position: relative; z-index: 1; }
.st.done .dot { background: var(--emp-primary); border-color: var(--emp-primary); color: #fff; }
.st.current .dot { border-color: var(--emp-primary); color: var(--emp-primary); box-shadow: 0 0 0 6px rgba(79,70,229,.15); }
.st.current { color: var(--emp-primary); }
.ex-card { display: flex; gap: .75rem; align-items: center; padding: .9rem; border: 1.5px solid var(--emp-border); border-radius: 14px; cursor: pointer; height: 100%; }
.ex-card.on { border-color: var(--emp-primary); background: rgba(79,70,229,.06); }
.ex-card.off { opacity: .5; }
.copy-list { max-height: 380px; overflow-y: auto; overflow-x: hidden; padding-right: 4px; }
.pick { display: flex; gap: .75rem; align-items: center; padding: .6rem .8rem; border: 1.5px solid var(--emp-border); border-radius: 12px; cursor: pointer; }
.pick.on { border-color: var(--emp-primary); background: rgba(79,70,229,.07); }
@media (max-width: 576px) { .st .small { font-size: .65rem; } .st .dot { width: 34px; height: 34px; } .stepper::before { top: 16px; } }
</style>
