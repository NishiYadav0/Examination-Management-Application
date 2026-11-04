<template>
  <div>
    <PageHeader title="Evaluations" subtitle="History of all evaluations you have saved or submitted." :crumbs="[{ label: 'Examiner', to: '/examiner' }, { label: 'Evaluations' }]" />
    <div class="card-emp">
      <div class="p-3 border-bottom d-flex gap-2 flex-wrap">
        <div class="input-group" style="max-width:300px"><span class="input-group-text"><i class="bi bi-search"></i></span><input v-model="q" class="form-control" placeholder="Student or exam"></div>
        <select v-model="status" class="form-select" style="max-width:180px"><option value="">All</option><option value="submitted">Submitted</option><option value="draft">Draft</option></select>
      </div>
      <LoadingBlock v-if="loading" class="p-3" />
      <EmptyState v-else-if="!list.length" icon="award" title="No evaluations yet" />
      <div v-else class="table-responsive">
        <table class="table table-emp">
          <thead><tr><th>Student</th><th>Examination</th><th>Marks</th><th>Grade</th><th>Status</th><th>Published</th><th>Date</th><th></th></tr></thead>
          <tbody>
            <tr v-for="e in list" :key="e.id">
              <td><div class="fw-semibold">{{ e.student_name }}</div><small class="text-muted">{{ e.roll_no }}</small></td>
              <td><div class="small fw-semibold">{{ e.exam_name }}</div><small class="text-muted">{{ e.course_code }}</small></td>
              <td class="fw-bold">{{ e.total_marks }} <small class="text-muted fw-normal">/ {{ e.max_marks }}</small></td>
              <td><b :style="{ color: $f.gradeColor(e.grade) }">{{ e.grade }}</b></td>
              <td><StatusBadge :status="e.status === 'submitted' ? 'submitted' : 'draft'" /></td>
              <td><i :class="e.results_published ? 'bi bi-check-circle-fill text-success' : 'bi bi-dash-circle text-muted'"></i></td>
              <td class="small">{{ $f.fmtDate(e.evaluated_at) }}</td>
              <td class="text-end"><router-link :to="'/examiner/evaluate/' + e.booking_id" class="btn btn-sm btn-soft">Open</router-link></td>
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
  name: 'ExaminerEvaluations',
  components: { PageHeader, LoadingBlock, EmptyState, StatusBadge },
  data: () => ({ rows: [], loading: true, q: '', status: '' }),
  computed: { list () { const q = this.q.toLowerCase(); return this.rows.filter(e => (!this.status || e.status === this.status) && (!q || (e.student_name + e.exam_name + e.roll_no).toLowerCase().includes(q))) } },
  async mounted () { try { this.rows = (await api.get('/examiner/evaluations')).data.data } catch (e) { this.$error(e) } this.loading = false }
}
</script>
