<template>
  <div>
    <PageHeader title="Statistics & analytics" subtitle="Institution-wide examination insights." :crumbs="[{ label: 'Admin', to: '/admin' }, { label: 'Statistics' }]">
      <button class="btn btn-light no-print" @click="print"><i class="bi bi-printer me-1"></i>Print</button>
    </PageHeader>
    <LoadingBlock v-if="!s" cards />
    <template v-else>
      <div class="row g-3 mb-4">
        <div class="col-6 col-lg-3"><StatCard label="Evaluations submitted" :value="s.total_evaluated" icon="clipboard-check" color="#4f46e5" /></div>
        <div class="col-6 col-lg-3"><StatCard label="Average score" :value="s.avg_percentage + '%'" icon="graph-up" color="#10b981" /></div>
        <div class="col-6 col-lg-3"><StatCard label="Active bookings" :value="s.booking_status.booked || 0" icon="bookmark-check" color="#06b6d4" /></div>
        <div class="col-6 col-lg-3"><StatCard label="Cancellations" :value="s.booking_status.cancelled || 0" icon="x-circle" color="#ef4444" /></div>
      </div>
      <div class="row g-4">
        <div class="col-lg-8"><div class="card-emp h-100"><div class="card-header">Registrations & bookings · last 6 months</div><div class="card-body">
          <ChartBox type="line" :labels="s.months.map(m => monthLabel(m))" :datasets="[{ label: 'New students', data: s.registrations }, { label: 'Bookings', data: s.monthly_bookings, color: '#10b981' }]" /></div></div></div>
        <div class="col-lg-4"><div class="card-emp h-100"><div class="card-header">Grade distribution</div><div class="card-body">
          <ChartBox type="doughnut" :labels="Object.keys(s.grades)" :datasets="[{ data: Object.values(s.grades) }]" /></div></div></div>
        <div class="col-lg-6"><div class="card-emp h-100"><div class="card-header">Average score & pass rate by examination</div><div class="card-body">
          <ChartBox type="bar" :labels="s.exam_performance.map(e => short(e.name))" :datasets="[{ label: 'Avg %', data: s.exam_performance.map(e => e.avg_pct) }, { label: 'Pass rate %', data: s.exam_performance.map(e => e.pass_rate), color: '#10b981' }]" /></div></div></div>
        <div class="col-lg-6"><div class="card-emp h-100"><div class="card-header">Slot utilisation</div><div class="card-body">
          <ChartBox type="bar" :labels="s.slot_utilisation.map(e => short(e.name))" :datasets="[{ label: 'Booked', data: s.slot_utilisation.map(e => e.booked), color: '#7c3aed' }, { label: 'Capacity', data: s.slot_utilisation.map(e => e.capacity), color: '#cbd5e1' }]" /></div></div></div>
        <div class="col-lg-4"><div class="card-emp h-100"><div class="card-header">Bookings by examination type</div><div class="card-body">
          <ChartBox type="polarArea" :labels="Object.keys(s.bookings_by_type)" :datasets="[{ data: Object.values(s.bookings_by_type) }]" /></div></div></div>
        <div class="col-lg-4"><div class="card-emp h-100"><div class="card-header">Booking status</div><div class="card-body">
          <ChartBox type="pie" :labels="Object.keys(s.booking_status).map(k => $f.statusMeta(k).label)" :datasets="[{ data: Object.values(s.booking_status) }]" /></div></div></div>
        <div class="col-lg-4"><div class="card-emp h-100"><div class="card-header">Bookings per course</div><div class="card-body">
          <ChartBox type="bar" :labels="s.course_bookings.map(c => c.code)" :datasets="[{ label: 'Bookings', data: s.course_bookings.map(c => c.count), color: '#f59e0b' }]" /></div></div></div>
        <div class="col-12"><div class="card-emp"><div class="card-header">Examination performance table</div>
          <div class="table-responsive"><table class="table table-emp"><thead><tr><th>Examination</th><th>Evaluated</th><th>Average</th><th>Average %</th><th>Pass rate</th></tr></thead>
            <tbody><tr v-for="e in s.exam_performance" :key="e.name"><td class="fw-semibold">{{ e.name }}</td><td>{{ e.count }}</td><td>{{ e.avg }} / {{ e.max }}</td>
              <td style="min-width:160px"><div class="progress" style="height:8px"><div class="progress-bar" :style="{ width: e.avg_pct + '%' }"></div></div><small>{{ e.avg_pct }}%</small></td>
              <td><span class="badge-soft" :class="e.pass_rate >= 75 ? 'bs-success' : e.pass_rate >= 50 ? 'bs-warning' : 'bs-danger'">{{ e.pass_rate }}%</span></td></tr></tbody></table></div></div></div>
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
  name: 'AdminStatistics',
  components: { PageHeader, LoadingBlock, StatCard, ChartBox },
  data: () => ({ s: null }),
  async mounted () { try { this.s = (await api.get('/admin/statistics')).data.data } catch (e) { this.$error(e) } },
  methods: {
    short (n) { return n.length > 22 ? n.slice(0, 20) + '…' : n },
    monthLabel (m) { const [y, mo] = m.split('-'); return new Date(y, mo - 1).toLocaleString('en', { month: 'short', year: '2-digit' }) },
    print () { window.print() }
  }
}
</script>
