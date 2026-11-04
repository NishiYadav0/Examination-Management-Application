<template>
  <div>
    <LoadingBlock v-if="!d" cards />
    <template v-else>
      <div class="row g-4 mb-4">
        <div class="col-xl-8">
          <div class="hero-card card-emp p-4 h-100 fade-in">
            <h1 class="h3 fw-bold text-white mb-1">Hi {{ firstName }}, ready for your next exam? 🎯</h1>
            <p class="text-white-50">{{ d.counts.available_exams }} examination(s) are open for booking with {{ d.counts.available_slots }} free seat(s).</p>
            <div class="d-flex flex-wrap gap-2">
              <router-link to="/student/exams?availability=bookable" class="btn btn-light fw-bold"><i class="bi bi-calendar-plus me-1"></i>Book a slot</router-link>
              <button class="btn btn-outline-light" :disabled="exporting" @click="exportCsv('exam_history')"><span v-if="exporting" class="spinner-border spinner-border-sm me-1"></span><i v-else class="bi bi-file-earmark-arrow-down me-1"></i>Export history (CSV)</button>
            </div>
          </div>
        </div>
        <div class="col-xl-4">
          <div class="card-emp h-100 next-exam">
            <div class="card-body">
              <div class="small-caps text-muted mb-2">Next examination</div>
              <template v-if="d.next_exam">
                <h5 class="fw-bold mb-1">{{ d.next_exam.exam_name }}</h5>
                <div class="small text-muted mb-3">{{ d.next_exam.course_code }} · {{ d.next_exam.exam_type }}</div>
                <div class="countdown mb-3"><span class="fs-2 fw-800 text-primary">{{ countdown }}</span></div>
                <div class="small d-grid gap-1">
                  <div><i class="bi bi-calendar-event me-2"></i>{{ $f.fmtDay(d.next_exam.date) }} · {{ $f.fmtTime(d.next_exam.start_time) }}</div>
                  <div><i class="bi bi-person me-2"></i>{{ d.next_exam.examiner_name }}</div>
                </div>
                <a v-if="d.next_exam.meeting_link" :href="d.next_exam.meeting_link" target="_blank" rel="noopener" class="btn btn-sm btn-gradient mt-3 w-100"><i class="bi bi-camera-video me-1"></i>Join meeting</a>
              </template>
              <EmptyState v-else icon="calendar2-x" title="No upcoming exams" text="Book a slot to see it here." />
            </div>
          </div>
        </div>
      </div>

      <div class="row g-3 mb-4">
        <div class="col-6 col-xl-3"><StatCard label="Available examinations" :value="d.counts.available_exams" icon="clipboard2-check" color="#4f46e5" to="/student/exams?availability=bookable" /></div>
        <div class="col-6 col-xl-3"><StatCard label="Available seats" :value="d.counts.available_slots" icon="door-open" color="#10b981" to="/student/exams?availability=bookable" /></div>
        <div class="col-6 col-xl-3"><StatCard label="Upcoming booked" :value="d.counts.upcoming" icon="calendar-check" color="#06b6d4" to="/student/bookings" /></div>
        <div class="col-6 col-xl-3"><StatCard label="Published results" :value="d.counts.results" icon="trophy" color="#f59e0b" to="/student/results" /></div>
      </div>

      <div class="row g-4 mb-4">
        <div class="col-xl-7">
          <div class="card-emp h-100">
            <div class="card-header d-flex justify-content-between"><span><i class="bi bi-door-open me-2 text-success"></i>Open for booking</span><router-link to="/student/exams" class="small">Browse all</router-link></div>
            <div class="list-group list-group-flush">
              <div v-if="!d.available_exams.length" class="p-4 text-center text-muted small">No examination is open for booking right now.</div>
              <router-link v-for="e in d.available_exams" :key="e.id" :to="'/student/exams/' + e.id" class="list-group-item list-group-item-action bg-transparent py-3 d-flex align-items-center gap-3">
                <span class="icon-box" :style="{ background: typeMeta(e.exam_type).color + '1a', color: typeMeta(e.exam_type).color }"><i :class="'bi bi-' + typeMeta(e.exam_type).icon"></i></span>
                <div class="flex-grow-1 min-w-0"><div class="fw-semibold">{{ e.name }}</div><small class="text-muted">{{ e.course_code }} · book by {{ $f.fmtDate(e.booking_end) }} · {{ e.available_seats }} seats</small></div>
                <span class="btn btn-sm btn-soft">Book</span>
              </router-link>
            </div>
          </div>
        </div>
        <div class="col-xl-5">
          <div class="card-emp h-100">
            <div class="card-header"><i class="bi bi-graph-up-arrow me-2 text-primary"></i>My performance</div>
            <div class="card-body"><ChartBox type="bar" :labels="d.performance.map(p => p.exam.length > 18 ? p.exam.slice(0, 16) + '…' : p.exam)" :datasets="[{ label: 'Score %', data: d.performance.map(p => p.pct), colors: d.performance.map(p => p.pct >= 40 ? '#4f46e5' : '#ef4444') }]" :height="240" /></div>
          </div>
        </div>
      </div>

      <div class="row g-4">
        <div class="col-xl-6">
          <div class="card-emp h-100">
            <div class="card-header d-flex justify-content-between"><span><i class="bi bi-calendar-check me-2 text-primary"></i>Upcoming examinations</span><router-link to="/student/bookings" class="small">My bookings</router-link></div>
            <div class="list-group list-group-flush">
              <div v-if="!d.upcoming.length" class="p-4 text-center text-muted small">No upcoming examinations.</div>
              <div v-for="b in d.upcoming" :key="b.id" class="list-group-item bg-transparent d-flex gap-3 align-items-center">
                <div class="date-box"><div>{{ new Date(b.date).getDate() }}</div><small>{{ new Date(b.date).toLocaleString('en', { month: 'short' }) }}</small></div>
                <div class="flex-grow-1 min-w-0"><div class="fw-semibold text-truncate">{{ b.exam_name }}</div><small class="text-muted">{{ $f.fmtTime(b.start_time) }} · {{ b.examiner_name }}</small></div>
                <StatusBadge :status="b.status" />
              </div>
            </div>
          </div>
        </div>
        <div class="col-xl-6">
          <div class="card-emp h-100">
            <div class="card-header d-flex justify-content-between"><span><i class="bi bi-trophy me-2 text-warning"></i>Latest results</span><router-link to="/student/results" class="small">All results</router-link></div>
            <div class="list-group list-group-flush">
              <div v-if="!d.results.length" class="p-4 text-center text-muted small">No published results yet.</div>
              <router-link v-for="r in d.results" :key="r.id" :to="'/student/results/' + r.id" class="list-group-item list-group-item-action bg-transparent d-flex gap-3 align-items-center">
                <span class="grade" :style="{ background: $f.gradeColor(r.grade) }">{{ r.grade }}</span>
                <div class="flex-grow-1 min-w-0"><div class="fw-semibold text-truncate">{{ r.exam_name }}</div><small class="text-muted">{{ r.total_marks }}/{{ r.max_marks }} · {{ r.percentage }}%</small></div>
                <i class="bi bi-chevron-right text-muted"></i>
              </router-link>
            </div>
          </div>
        </div>
      </div>
    </template>
  </div>
</template>
<script>
import api from '@/services/api'
import { TYPE_META } from '@/utils/format'
import exportMixin from '@/utils/exportMixin'
import LoadingBlock from '@/components/common/LoadingBlock.vue'
import StatCard from '@/components/common/StatCard.vue'
import StatusBadge from '@/components/common/StatusBadge.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import ChartBox from '@/components/charts/ChartBox.vue'
export default {
  name: 'StudentDashboard',
  mixins: [exportMixin],
  components: { LoadingBlock, StatCard, StatusBadge, EmptyState, ChartBox },
  data: () => ({ d: null, now: Date.now(), tick: null }),
  computed: {
    firstName () { return this.$store.state.auth.user.name.split(' ')[0] },
    countdown () {
      const n = this.d.next_exam
      const t = new Date(`${n.date}T${n.start_time}:00`).getTime() - this.now
      if (t <= 0) return 'Starting now'
      const dd = Math.floor(t / 86400000); const h = Math.floor(t % 86400000 / 3600000); const m = Math.floor(t % 3600000 / 60000)
      return dd ? `${dd}d ${h}h ${m}m` : `${h}h ${m}m`
    }
  },
  async mounted () {
    try { this.d = (await api.get('/student/dashboard')).data.data } catch (e) { this.$error(e) }
    this.tick = setInterval(() => { this.now = Date.now() }, 30000)
  },
  beforeUnmount () { clearInterval(this.tick) },
  methods: { typeMeta (t) { return TYPE_META[t] || { icon: 'tag', color: '#4f46e5' } } }
}
</script>
<style scoped>
.hero-card { background: linear-gradient(135deg, #4f46e5, #7c3aed 60%, #db2777); border: 0; }
.date-box { width: 50px; text-align: center; border-radius: 12px; background: rgba(79,70,229,.08); color: var(--emp-primary); padding: .35rem 0; font-weight: 800; line-height: 1.1; flex-shrink: 0; }
.date-box small { font-size: .65rem; text-transform: uppercase; }
.grade { width: 40px; height: 40px; border-radius: 12px; color: #fff; display: inline-flex; align-items: center; justify-content: center; font-weight: 800; flex-shrink: 0; }
</style>
