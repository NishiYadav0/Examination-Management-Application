<template>
  <div>
    <PageHeader title="Booked students" subtitle="Students booked into your slots – mark attendance and evaluate." :crumbs="[{ label: 'Examiner', to: '/examiner' }, { label: 'Students' }]" />
    <div class="card-emp">
      <div class="p-3 d-flex flex-wrap gap-2 border-bottom">
        <div class="input-group" style="max-width:300px"><span class="input-group-text"><i class="bi bi-search"></i></span><input v-model="q" class="form-control" placeholder="Name, roll no, exam"></div>
        <select v-model="examId" class="form-select" style="max-width:240px"><option value="">All examinations</option><option v-for="e in exams" :key="e.id" :value="e.id">{{ e.name }}</option></select>
        <div class="btn-group">
          <button v-for="t in evTabs" :key="t.k" class="btn btn-sm" :class="evaluation === t.k ? 'btn-primary' : 'btn-light'" @click="evaluation = t.k">{{ t.label }}</button>
        </div>
        <button v-if="slotId" class="btn btn-sm btn-soft" @click="slotId = null">Slot #{{ slotId }} <i class="bi bi-x"></i></button>
      </div>
      <LoadingBlock v-if="loading" class="p-3" />
      <EmptyState v-else-if="!list.length" icon="people" title="No students" text="Nothing matches the current filters." />
      <div v-else class="table-responsive">
        <table class="table table-emp">
          <thead><tr><th>Student</th><th>Examination</th><th>Slot</th><th>Submission</th><th>Status</th><th>Marks</th><th class="text-end">Actions</th></tr></thead>
          <tbody>
            <tr v-for="b in list" :key="b.id">
              <td><div class="d-flex gap-2 align-items-center"><span class="avatar avatar-sm">{{ $f.initials(b.student_name) }}</span><div><div class="fw-semibold">{{ b.student_name }}</div><small class="text-muted">{{ b.roll_no }}</small></div></div></td>
              <td><div class="small fw-semibold">{{ b.exam_name }}</div><small class="text-muted">{{ b.course_code }}</small></td>
              <td><div>{{ $f.fmtDay(b.date) }}</div><small class="text-muted">{{ $f.fmtTime(b.start_time) }}</small></td>
              <td><a v-if="b.submission_link" :href="b.submission_link" target="_blank" rel="noopener" class="small"><i class="bi bi-link-45deg"></i> Open</a><span v-else class="text-muted small">—</span></td>
              <td><StatusBadge :status="b.status" /><div v-if="b.evaluation_status === 'draft'" class="small text-warning mt-1">Draft saved</div></td>
              <td><b v-if="b.evaluation_status === 'submitted'">{{ b.total_marks }}</b><span v-else class="text-muted">—</span></td>
              <td class="text-end text-nowrap">
                <template v-if="b.date <= today">
                  <router-link v-if="['booked','completed'].includes(b.status)" :to="'/examiner/evaluate/' + b.id" class="btn btn-sm me-1" :class="b.evaluation_status === 'submitted' ? 'btn-light' : 'btn-gradient'">{{ b.evaluation_status === 'submitted' ? 'View / edit' : 'Evaluate' }}</router-link>
                  <button v-if="b.status === 'booked' && b.evaluation_status !== 'submitted'" class="btn btn-sm btn-icon btn-soft-danger" title="Mark absent" @click="attendance(b, false)"><i class="bi bi-person-x"></i></button>
                  <button v-if="b.status === 'absent'" class="btn btn-sm btn-soft-success" @click="attendance(b, true)">Mark present</button>
                </template>
                <span v-else class="small text-muted"><i class="bi bi-clock"></i> in {{ $f.daysUntil(b.date) }} day(s)</span>
                <a v-if="b.meeting_link && b.status === 'booked'" :href="b.meeting_link" target="_blank" rel="noopener" class="btn btn-sm btn-icon btn-light ms-1" title="Join meeting"><i class="bi bi-camera-video"></i></a>
              </td>
            </tr>
          </tbody>
        </table>
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
  name: 'ExaminerStudents',
  components: { PageHeader, LoadingBlock, EmptyState, StatusBadge },
  data () {
    return { rows: [], exams: [], loading: true, q: this.$route.query.q || '', examId: '', evaluation: this.$route.query.evaluation || '', slotId: this.$route.query.slot ? Number(this.$route.query.slot) : null,
      evTabs: [{ k: '', label: 'All' }, { k: 'pending', label: 'Pending' }, { k: 'done', label: 'Evaluated' }] }
  },
  computed: {
    today () { return this.$f.todayISO() },
    list () {
      const q = this.q.toLowerCase()
      return this.rows.filter(b => (!this.examId || b.exam_id === this.examId) && (!this.slotId || b.slot_id === this.slotId) &&
        (!this.evaluation || (this.evaluation === 'pending' ? b.status === 'booked' && b.evaluation_status !== 'submitted' : b.evaluation_status === 'submitted')) &&
        (!q || [b.student_name, b.roll_no, b.exam_name].join(' ').toLowerCase().includes(q)))
    }
  },
  async mounted () { this.load(); this.exams = (await api.get('/examiner/exams')).data.data },
  methods: {
    async load () { this.loading = true; try { this.rows = (await api.get('/examiner/students')).data.data } catch (e) { this.$error(e) } this.loading = false },
    async attendance (b, present) {
      if (!present && !await this.$confirm({ title: 'Mark absent?', message: `${b.student_name} will be marked absent for ${b.exam_name}.`, variant: 'danger', confirmText: 'Mark absent', icon: 'person-x' })) return
      try { const r = await api.post(`/examiner/bookings/${b.id}/attendance`, { present }); this.$toast(r.data.message); this.load() } catch (e) { this.$error(e) }
    }
  }
}
</script>
