<template>
  <div>
    <PageHeader title="Examinations" subtitle="Plan examinations, control their windows and follow them to result publication." :crumbs="[{ label: 'Admin', to: '/admin' }, { label: 'Examinations' }]">
      <button class="btn btn-gradient" @click="show = true"><i class="bi bi-plus-lg me-1"></i>New examination</button>
    </PageHeader>

    <div class="status-tabs mb-3">
      <button v-for="s in statusTabs" :key="s.k" class="st" :class="{ active: status === s.k }" @click="status = s.k">
        {{ s.label }} <span class="cnt">{{ count(s.k) }}</span>
      </button>
    </div>

    <div class="card-emp">
      <div class="p-3 d-flex flex-wrap gap-2 border-bottom">
        <div class="input-group" style="max-width:320px">
          <span class="input-group-text"><i class="bi bi-search"></i></span>
          <input v-model="q" class="form-control" placeholder="Search exam or course">
        </div>
        <select v-model="courseId" class="form-select" style="max-width:220px"><option value="">All courses</option><option v-for="c in courses" :key="c.id" :value="String(c.id)">{{ c.code }}</option></select>
        <select v-model="type" class="form-select" style="max-width:180px"><option value="">All types</option><option v-for="t in types" :key="t">{{ t }}</option></select>
      </div>
      <LoadingBlock v-if="loading" class="p-3" />
      <EmptyState v-else-if="!filtered.length" icon="clipboard-x" title="No examinations" text="Adjust the filters or create a new examination." />
      <div v-else class="table-responsive">
        <table class="table table-emp">
          <thead><tr><th>Examination</th><th>Type</th><th>Booking window</th><th>Examiners</th><th>Slots</th><th>Bookings</th><th>Status</th><th></th></tr></thead>
          <tbody>
            <tr v-for="e in paged" :key="e.id" class="cursor-pointer" @click="$router.push('/admin/exams/' + e.id)">
              <td>
                <div class="fw-semibold">{{ e.name }}</div>
                <small class="text-muted">{{ e.course_code }} · {{ e.duration_minutes }} min · {{ e.max_marks }} marks</small>
              </td>
              <td><span class="badge-soft bs-info"><i :class="'bi bi-' + typeIcon(e.exam_type) + ' me-1'"></i>{{ e.exam_type }}</span></td>
              <td class="small">{{ $f.fmtDate(e.booking_start) }} – {{ $f.fmtDate(e.booking_end) }}</td>
              <td>
                <div class="d-flex">
                  <span v-for="x in e.examiners.slice(0, 3)" :key="x.id" class="avatar avatar-sm border border-2 border-white" style="margin-right:-8px" :title="x.name">{{ $f.initials(x.name) }}</span>
                  <span v-if="!e.examiners.length" class="text-muted small">None</span>
                </div>
              </td>
              <td>{{ e.slot_count }}</td>
              <td>{{ e.booking_count }}</td>
              <td><StatusBadge :status="e.status" /><div v-if="e.results_published" class="small text-success mt-1"><i class="bi bi-megaphone"></i> Published</div></td>
              <td class="text-end"><i class="bi bi-chevron-right text-muted"></i></td>
            </tr>
          </tbody>
        </table>
        <Paginator v-model="page" :total="filtered.length" :per-page="10" />
      </div>
    </div>

    <BaseModal :show="show" title="New examination" subtitle="Created as Draft – open windows from the exam page" icon="clipboard-plus" size="lg" @close="show = false">
      <ExamForm v-if="show" @saved="saved" @busy="busy = $event" />
      <template #footer>
        <button class="btn btn-light" @click="show = false">Cancel</button>
        <button class="btn btn-gradient" form="examForm" :disabled="busy">Create examination</button>
      </template>
    </BaseModal>
  </div>
</template>

<script>
import api from '@/services/api'
import { EXAM_TYPES, TYPE_META } from '@/utils/format'
import PageHeader from '@/components/common/PageHeader.vue'
import StatusBadge from '@/components/common/StatusBadge.vue'
import LoadingBlock from '@/components/common/LoadingBlock.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import BaseModal from '@/components/common/BaseModal.vue'
import Paginator from '@/components/common/Paginator.vue'
import ExamForm from '@/components/admin/ExamForm.vue'

export default {
  name: 'AdminExams',
  components: { PageHeader, StatusBadge, LoadingBlock, EmptyState, BaseModal, Paginator, ExamForm },
  data () {
    return {
      exams: [], courses: [], loading: true, show: this.$route.query.new === '1', busy: false, page: 1,
      q: '', status: '', type: '', courseId: this.$route.query.course_id || '', types: EXAM_TYPES,
      statusTabs: [{ k: '', label: 'All' }, { k: 'draft', label: 'Draft' }, { k: 'slot_creation', label: 'Slot creation' },
        { k: 'booking_open', label: 'Booking open' }, { k: 'closed', label: 'Closed' }, { k: 'completed', label: 'Completed' }]
    }
  },
  computed: {
    base () {
      const q = this.q.toLowerCase()
      return this.exams.filter(e => (!this.type || e.exam_type === this.type) && (!this.courseId || String(e.course_id) === this.courseId) &&
        (!q || [e.name, e.course_code, e.course_name].join(' ').toLowerCase().includes(q)))
    },
    filtered () { return this.base.filter(e => !this.status || e.status === this.status) },
    paged () { return this.filtered.slice((this.page - 1) * 10, this.page * 10) }
  },
  watch: { filtered () { this.page = 1 } },
  async mounted () {
    this.load()
    this.courses = (await api.get('/admin/courses')).data.data
  },
  methods: {
    async load () {
      this.loading = true
      try { this.exams = (await api.get('/admin/exams')).data.data } catch (e) { this.$error(e) }
      this.loading = false
    },
    count (k) { return this.base.filter(e => !k || e.status === k).length },
    typeIcon (t) { return (TYPE_META[t] || {}).icon || 'tag' },
    saved (exam) { this.show = false; this.$router.push('/admin/exams/' + exam.id) }
  }
}
</script>
<style scoped>
.status-tabs { display: flex; gap: .5rem; overflow-x: auto; padding-bottom: 2px; }
.st { border: 1px solid var(--emp-border); background: var(--emp-card-bg); border-radius: 999px; padding: .45rem 1rem; font-weight: 600; font-size: .85rem; color: var(--emp-muted); white-space: nowrap; }
.st.active { background: var(--emp-primary); color: #fff; border-color: var(--emp-primary); }
.st .cnt { background: rgba(148,163,184,.2); border-radius: 999px; padding: 0 .5rem; margin-left: .3rem; font-size: .75rem; }
.st.active .cnt { background: rgba(255,255,255,.25); }
</style>
