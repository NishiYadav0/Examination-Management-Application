<template>
  <div>
    <PageHeader title="My progress" subtitle="Track your performance across examinations." :crumbs="[{ label: 'Student', to: '/student' }, { label: 'Progress' }]" />
    <LoadingBlock v-if="!s" cards />
    <template v-else>
      <div class="row g-3 mb-4">
        <div class="col-6 col-md-3"><StatCard label="Average score" :value="s.avg_pct + '%'" icon="graph-up" color="#4f46e5" /></div>
        <div class="col-6 col-md-3"><StatCard label="Best score" :value="s.best + '%'" icon="star" color="#10b981" /></div>
        <div class="col-6 col-md-3"><StatCard label="Passed" :value="s.passed + '/' + s.total_results" icon="patch-check" color="#06b6d4" /></div>
        <div class="col-6 col-md-3"><StatCard label="Bookings" :value="Object.values(s.status).reduce((a, b) => a + b, 0)" icon="bookmark" color="#f59e0b" /></div>
      </div>
      <div class="row g-4">
        <div class="col-lg-8"><div class="card-emp h-100"><div class="card-header">Score trend (%)</div><div class="card-body">
          <ChartBox type="line" :labels="s.performance.map(p => p.exam)" :datasets="[{ label: 'Score %', data: s.performance.map(p => p.pct) }]" /></div></div></div>
        <div class="col-lg-4"><div class="card-emp h-100"><div class="card-header">Booking status</div><div class="card-body">
          <ChartBox type="doughnut" :labels="Object.keys(s.status).map(k => $f.statusMeta(k).label)" :datasets="[{ data: Object.values(s.status) }]" /></div></div></div>
        <div class="col-lg-6"><div class="card-emp h-100"><div class="card-header">Examinations by type</div><div class="card-body">
          <ChartBox type="bar" :labels="Object.keys(s.by_type)" :datasets="[{ label: 'Exams', data: Object.values(s.by_type), color: '#7c3aed' }]" :height="240" /></div></div></div>
        <div class="col-lg-6"><div class="card-emp h-100"><div class="card-header">Grades</div><div class="card-body">
          <ChartBox type="bar" :labels="Object.keys(s.grades)" :datasets="[{ label: 'Count', data: Object.values(s.grades), colors: Object.keys(s.grades).map(g => $f.gradeColor(g)) }]" :height="240" /></div></div></div>
      </div>
    </template>
  </div>
</template>
<script>
import api from '@/services/api'
import PageHeader from '@/components/common/PageHeader.vue'
import LoadingBlock from '@/components/common/LoadingBlock.vue'
import StatCard from '@/components/common/StatCard.vue'
import ChartBox from '@/components/charts/ChartBox.vue'
export default {
  name: 'StudentStatistics',
  components: { PageHeader, LoadingBlock, StatCard, ChartBox },
  data: () => ({ s: null }),
  async mounted () { try { this.s = (await api.get('/student/statistics')).data.data } catch (e) { this.$error(e) } }
}
</script>
