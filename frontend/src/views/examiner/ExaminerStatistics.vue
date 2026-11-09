<template>
  <div>
    <PageHeader title="My statistics" subtitle="Your evaluation workload and grading patterns." :crumbs="[{ label: 'Examiner', to: '/examiner' }, { label: 'Statistics' }]" />
    <LoadingBlock v-if="!s" cards />
    <template v-else>
      <div class="row g-3 mb-4">
        <div class="col-6 col-md-4"><StatCard label="Students evaluated" :value="s.total_evaluated" icon="award" color="#4f46e5" /></div>
        <div class="col-6 col-md-4"><StatCard label="Average score given" :value="s.avg_pct + '%'" icon="graph-up" color="#10b981" /></div>
        <div class="col-12 col-md-4"><StatCard label="Slots created" :value="Object.values(s.slot_status).reduce((a, b) => a + b, 0)" icon="calendar3-week" color="#06b6d4" /></div>
      </div>
      <div class="row g-4">
        <div class="col-lg-7"><div class="card-emp h-100"><div class="card-header">Average score by examination</div><div class="card-body">
          <ChartBox type="bar" :labels="s.avg_by_exam.map(a => a.exam)" :datasets="[{ label: 'Avg %', data: s.avg_by_exam.map(a => a.avg_pct) }, { label: 'Students', data: s.avg_by_exam.map(a => a.count), color: '#f59e0b' }]" /></div></div></div>
        <div class="col-lg-5"><div class="card-emp h-100"><div class="card-header">Grades awarded</div><div class="card-body">
          <ChartBox type="doughnut" :labels="Object.keys(s.grades)" :datasets="[{ data: Object.values(s.grades) }]" /></div></div></div>
        <div class="col-lg-5"><div class="card-emp h-100"><div class="card-header">Slot status</div><div class="card-body">
          <ChartBox type="pie" :labels="Object.keys(s.slot_status).map(k => $f.statusMeta(k).label)" :datasets="[{ data: Object.values(s.slot_status) }]" :height="240" /></div></div></div>
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
  name: 'ExaminerStatistics',
  components: { PageHeader, LoadingBlock, StatCard, ChartBox },
  data: () => ({ s: null }),
  async mounted () { try { this.s = (await api.get('/examiner/statistics')).data.data } catch (e) { this.$error(e) } }
}
</script>
