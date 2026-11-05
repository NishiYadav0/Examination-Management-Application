<template>
  <div>
    <PageHeader title="Results" subtitle="Published results with examiner feedback." :crumbs="[{ label: 'Student', to: '/student' }, { label: 'Results' }]" />
    <LoadingBlock v-if="loading" cards />
    <template v-else>
      <div class="row g-3 mb-4" v-if="rows.length">
        <div class="col-6 col-md-3"><StatCard label="Results published" :value="rows.length" icon="trophy" color="#f59e0b" /></div>
        <div class="col-6 col-md-3"><StatCard label="Average" :value="avg + '%'" icon="graph-up" color="#4f46e5" /></div>
        <div class="col-6 col-md-3"><StatCard label="Best" :value="best + '%'" icon="star" color="#10b981" /></div>
        <div class="col-6 col-md-3"><StatCard label="Passed" :value="rows.filter(r => r.passed).length + '/' + rows.length" icon="patch-check" color="#06b6d4" /></div>
      </div>
      <EmptyState v-if="!rows.length" icon="hourglass" title="No published results yet" text="Results appear here once the admin publishes them." />
      <div class="row g-4">
        <div class="col-md-6 col-xl-4" v-for="r in rows" :key="r.id">
          <div class="card-emp h-100 result hover-lift">
            <div class="card-body">
              <div class="d-flex justify-content-between align-items-start mb-3">
                <div><span class="badge-soft bs-secondary">{{ r.course_code }}</span><h6 class="fw-bold mt-2 mb-0">{{ r.exam_name }}</h6><small class="text-muted">{{ r.exam_type }} · {{ $f.fmtDate(r.date) }}</small></div>
                <span class="grade" :style="{ background: $f.gradeColor(r.grade) }">{{ r.grade }}</span>
              </div>
              <div class="ring-wrap">
                <svg viewBox="0 0 36 36" class="ring"><path class="bg" d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"/>
                  <path class="fg" :stroke="$f.gradeColor(r.grade)" :stroke-dasharray="r.percentage + ', 100'" d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"/></svg>
                <div class="ring-txt"><b>{{ r.total_marks }}</b><small>/ {{ r.max_marks }}</small></div>
              </div>
              <div class="text-center mb-3"><span class="badge" :class="r.passed ? 'bg-success' : 'bg-danger'">{{ r.passed ? 'PASS' : 'FAIL' }}</span> <span class="small text-muted ms-1">{{ r.percentage }}%</span></div>
              <p class="small text-muted text-truncate-2 mb-3"><i class="bi bi-chat-quote me-1"></i>{{ r.evaluation.remarks }}</p>
              <router-link :to="'/student/results/' + r.id" class="btn btn-soft w-100">View scorecard</router-link>
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
import EmptyState from '@/components/common/EmptyState.vue'
import StatCard from '@/components/common/StatCard.vue'
export default {
  name: 'StudentResults',
  components: { PageHeader, LoadingBlock, EmptyState, StatCard },
  data: () => ({ rows: [], loading: true }),
  computed: {
    avg () { return this.rows.length ? (this.rows.reduce((a, r) => a + r.percentage, 0) / this.rows.length).toFixed(1) : 0 },
    best () { return this.rows.length ? Math.max(...this.rows.map(r => r.percentage)) : 0 }
  },
  async mounted () { try { this.rows = (await api.get('/student/results')).data.data } catch (e) { this.$error(e) } this.loading = false }
}
</script>
<style scoped>
.grade { width: 46px; height: 46px; border-radius: 14px; color: #fff; display: inline-flex; align-items: center; justify-content: center; font-weight: 800; font-size: 1.3rem; }
.ring-wrap { position: relative; width: 130px; margin: 0 auto .75rem; }
.ring { display: block; }
.ring .bg { fill: none; stroke: rgba(148,163,184,.2); stroke-width: 3.2; }
.ring .fg { fill: none; stroke-width: 3.2; stroke-linecap: round; transition: stroke-dasharray .6s; }
.ring-txt { position: absolute; inset: 0; display: flex; flex-direction: column; align-items: center; justify-content: center; }
.ring-txt b { font-size: 1.6rem; line-height: 1; }
.ring-txt small { color: var(--emp-muted); }
</style>
