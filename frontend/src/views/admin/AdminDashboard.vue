<template>
  <div>
    <div class="welcome card-emp p-4 mb-4 fade-in">
      <div class="row align-items-center g-3">
        <div class="col-md-8">
          <h1 class="h3 fw-bold text-white mb-1">Admin control centre</h1>
          <p class="text-white-50 mb-0">Monitor examinations, slots, bookings and evaluations across the institution.</p>
        </div>
        <div class="col-md-4 text-md-end d-flex gap-2 justify-content-md-end flex-wrap">
          <router-link to="/admin/exams?new=1" class="btn btn-light fw-bold"><i class="bi bi-plus-lg me-1"></i>New examination</router-link>
          <router-link to="/admin/examiners?new=1" class="btn btn-outline-light"><i class="bi bi-person-plus me-1"></i>Add examiner</router-link>
        </div>
      </div>
    </div>

    <LoadingBlock v-if="!d" cards :rows="4" />
    <template v-else>
      <div class="row g-3 mb-4">
        <div class="col-6 col-md-4 col-xxl-2" v-for="s in stats" :key="s.label">
          <StatCard v-bind="s" />
        </div>
      </div>

      <div class="row g-3 mb-4">
        <div class="col-md-4" v-for="a in alerts" :key="a.label">
          <router-link :to="a.to" class="alert-tile text-decoration-none" :style="{ '--c': a.color }">
            <i :class="'bi bi-' + a.icon"></i>
            <div><div class="fs-4 fw-800">{{ a.value }}</div><div class="small">{{ a.label }}</div></div>
            <i class="bi bi-arrow-right ms-auto"></i>
          </router-link>
        </div>
      </div>

      <div class="row g-4 mb-4">
        <div class="col-xl-8">
          <div class="card-emp h-100">
            <div class="card-header d-flex justify-content-between"><span><i class="bi bi-graph-up me-2 text-primary"></i>Booking trend · last 14 days</span></div>
            <div class="card-body"><ChartBox type="line" :labels="d.booking_trend.map(t => $f.fmtDate(t.date, { day: '2-digit', month: 'short' }))" :datasets="[{ label: 'Bookings', data: d.booking_trend.map(t => t.count) }]" /></div>
          </div>
        </div>
        <div class="col-xl-4">
          <div class="card-emp h-100">
            <div class="card-header"><i class="bi bi-pie-chart me-2 text-primary"></i>Examinations by status</div>
            <div class="card-body"><ChartBox type="doughnut" :labels="Object.keys(d.exam_status).map(k => $f.statusMeta(k).label)" :datasets="[{ data: Object.values(d.exam_status) }]" /></div>
          </div>
        </div>
      </div>

      <div class="row g-4 mb-4">
        <div class="col-lg-6">
          <div class="card-emp h-100">
            <div class="card-header"><i class="bi bi-fire me-2 text-danger"></i>Popular examinations</div>
            <div class="card-body"><ChartBox type="bar" :labels="d.popular_exams.map(p => shorten(p.name))" :datasets="[{ label: 'Bookings', data: d.popular_exams.map(p => p.bookings), color: '#7c3aed' }]" :options="{ indexAxis: 'y' }" /></div>
          </div>
        </div>
        <div class="col-lg-6">
          <div class="card-emp h-100">
            <div class="card-header"><i class="bi bi-person-workspace me-2 text-info"></i>Examiner workload</div>
            <div class="card-body"><ChartBox type="bar" :labels="d.examiner_workload.map(w => w.name)" :datasets="[{ label: 'Slots', data: d.examiner_workload.map(w => w.slots) }, { label: 'Evaluations', data: d.examiner_workload.map(w => w.evaluations), color: '#10b981' }]" /></div>
          </div>
        </div>
      </div>

      <div class="row g-4">
        <div class="col-xl-7">
          <div class="card-emp h-100">
            <div class="card-header d-flex justify-content-between align-items-center">
              <span><i class="bi bi-calendar-event me-2 text-primary"></i>Upcoming slots</span>
              <router-link to="/admin/slots" class="small">View all</router-link>
            </div>
            <div class="table-responsive">
              <table class="table table-emp">
                <thead><tr><th>Examination</th><th>Examiner</th><th>When</th><th>Seats</th><th>Status</th></tr></thead>
                <tbody>
                  <tr v-if="!d.upcoming_slots.length"><td colspan="5" class="text-center text-muted py-4">No upcoming slots</td></tr>
                  <tr v-for="s in d.upcoming_slots" :key="s.id">
                    <td><div class="fw-semibold">{{ s.exam_name }}</div><small class="text-muted">{{ s.course_code }}</small></td>
                    <td>{{ s.examiner_name }}</td>
                    <td><div>{{ $f.fmtDay(s.date) }}</div><small class="text-muted">{{ $f.fmtTime(s.start_time) }}</small></td>
                    <td>{{ s.booked_count }}/{{ s.capacity }}</td>
                    <td><StatusBadge :status="s.status" /></td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </div>
        <div class="col-xl-5">
          <div class="card-emp h-100">
            <div class="card-header d-flex justify-content-between align-items-center">
              <span><i class="bi bi-activity me-2 text-primary"></i>Recent activity</span>
              <router-link to="/admin/reports#activity" class="small">Full log</router-link>
            </div>
            <div class="card-body">
              <div class="timeline">
                <div v-for="a in d.recent_activity" :key="a.id" class="timeline-item done">
                  <div class="small"><b>{{ a.user_name || 'System' }}</b> <span class="text-muted">· {{ a.action.replace(/_/g, ' ') }}</span></div>
                  <div class="small text-muted">{{ a.details }} · {{ $f.timeAgo(a.created_at) }}</div>
                </div>
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
import StatCard from '@/components/common/StatCard.vue'
import StatusBadge from '@/components/common/StatusBadge.vue'
import LoadingBlock from '@/components/common/LoadingBlock.vue'
import ChartBox from '@/components/charts/ChartBox.vue'

export default {
  name: 'AdminDashboard',
  components: { StatCard, StatusBadge, LoadingBlock, ChartBox },
  data: () => ({ d: null }),
  computed: {
    stats () {
      const c = this.d.counts
      return [
        { label: 'Courses', value: c.courses, icon: 'journal-bookmark', color: '#4f46e5', to: '/admin/courses' },
        { label: 'Examinations', value: c.examinations, icon: 'clipboard2-check', color: '#7c3aed', to: '/admin/exams' },
        { label: 'Students', value: c.students, icon: 'mortarboard', color: '#06b6d4', to: '/admin/students' },
        { label: 'Examiners', value: c.examiners, icon: 'person-badge', color: '#10b981', to: '/admin/examiners' },
        { label: 'Exam slots', value: c.slots, icon: 'calendar3-week', color: '#f59e0b', to: '/admin/slots' },
        { label: 'Bookings', value: c.bookings, icon: 'bookmark-star', color: '#ec4899', to: '/admin/bookings' }
      ]
    },
    alerts () {
      const c = this.d.counts
      return [
        { label: 'Pending evaluations', value: c.pending_evaluations, icon: 'hourglass-split', color: '#f59e0b', to: '/admin/bookings?status=booked' },
        { label: 'Open support tickets', value: c.open_tickets, icon: 'chat-square-dots', color: '#4f46e5', to: '/admin/support' },
        { label: 'Blocked accounts', value: c.blocked_users, icon: 'slash-circle', color: '#ef4444', to: '/admin/students?status=blocked' }
      ]
    }
  },
  async mounted () {
    try { this.d = (await api.get('/admin/dashboard')).data.data } catch (e) { this.$error(e) }
  },
  methods: { shorten (s) { return s.length > 26 ? s.slice(0, 24) + '…' : s } }
}
</script>

<style scoped>
.welcome { background: var(--emp-gradient); border: 0; }
.alert-tile { display: flex; align-items: center; gap: 1rem; padding: 1rem 1.25rem; border-radius: 16px; color: var(--c);
  background: color-mix(in srgb, var(--c) 10%, transparent); border: 1px solid color-mix(in srgb, var(--c) 25%, transparent); transition: transform .15s; }
.alert-tile:hover { transform: translateY(-2px); }
.alert-tile > i:first-child { font-size: 1.6rem; }
</style>
