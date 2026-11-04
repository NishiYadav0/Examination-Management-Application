<template>
  <div>
    <PageHeader title="Assigned examinations" subtitle="Examinations you conduct. Create slots while slot creation is open." :crumbs="[{ label: 'Examiner', to: '/examiner' }, { label: 'Exams' }]" />
    <div class="d-flex flex-wrap gap-2 mb-3">
      <div class="input-group" style="max-width:320px"><span class="input-group-text"><i class="bi bi-search"></i></span><input v-model="q" class="form-control" placeholder="Search"></div>
      <select v-model="status" class="form-select" style="max-width:200px"><option value="">All status</option><option v-for="s in ['slot_creation','booking_open','closed','completed','draft']" :key="s" :value="s">{{ $f.statusMeta(s).label }}</option></select>
    </div>
    <LoadingBlock v-if="loading" />
    <EmptyState v-else-if="!list.length" icon="clipboard-x" title="No examinations" text="The admin has not assigned you any examination yet." />
    <div class="row g-4">
      <div class="col-md-6 col-xl-4" v-for="e in list" :key="e.id">
        <div class="card-emp h-100 hover-lift d-flex flex-column">
          <div class="type-strip" :style="{ background: typeColor(e.exam_type) }"></div>
          <div class="card-body d-flex flex-column">
            <div class="d-flex justify-content-between mb-2"><span class="badge-soft bs-primary">{{ e.course_code }}</span><StatusBadge :status="e.status" /></div>
            <h6 class="fw-bold">{{ e.name }}</h6>
            <div class="small text-muted mb-3">{{ e.exam_type }} · {{ e.duration_minutes }} min · {{ e.max_marks }} marks</div>
            <div class="row text-center g-2 mb-3">
              <div class="col-4"><div class="mini-stat"><b>{{ e.my_slots }}</b><small>My slots</small></div></div>
              <div class="col-4"><div class="mini-stat"><b>{{ e.my_bookings }}</b><small>Booked</small></div></div>
              <div class="col-4"><div class="mini-stat"><b>{{ e.rubric_count }}</b><small>Criteria</small></div></div>
            </div>
            <div class="small mb-3" :class="e.can_create_slots ? 'text-success' : 'text-muted'">
              <i :class="e.can_create_slots ? 'bi bi-unlock' : 'bi bi-lock'"></i>
              {{ e.can_create_slots ? `Slot creation open till ${$f.fmtDate(e.slot_creation_end)}` : `Slot creation: ${$f.fmtDate(e.slot_creation_start)} – ${$f.fmtDate(e.slot_creation_end)}` }}
            </div>
            <router-link :to="'/examiner/exams/' + e.id" class="btn btn-soft mt-auto">{{ e.can_create_slots ? 'Manage slots' : 'Open examination' }} <i class="bi bi-arrow-right"></i></router-link>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
<script>
import api from '@/services/api'
import { TYPE_META } from '@/utils/format'
import PageHeader from '@/components/common/PageHeader.vue'
import LoadingBlock from '@/components/common/LoadingBlock.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import StatusBadge from '@/components/common/StatusBadge.vue'
export default {
  name: 'ExaminerExams',
  components: { PageHeader, LoadingBlock, EmptyState, StatusBadge },
  data: () => ({ exams: [], loading: true, q: '', status: '' }),
  computed: {
    list () { const q = this.q.toLowerCase(); return this.exams.filter(e => (!this.status || e.status === this.status) && (!q || (e.name + e.course_code).toLowerCase().includes(q))) }
  },
  async mounted () { try { this.exams = (await api.get('/examiner/exams')).data.data } catch (e) { this.$error(e) } this.loading = false },
  methods: { typeColor (t) { return (TYPE_META[t] || {}).color || '#4f46e5' } }
}
</script>
<style scoped>
.type-strip { height: 5px; border-radius: 16px 16px 0 0; }
.mini-stat { background: var(--bs-tertiary-bg); border-radius: 10px; padding: .45rem; }
.mini-stat b { display: block; font-size: 1.1rem; }
.mini-stat small { color: var(--emp-muted); font-size: .7rem; }
</style>
