<template>
  <div>
    <LoadingBlock v-if="!d" cards />
    <template v-else>
      <div class="hero-card card-emp p-4 mb-4 fade-in">
        <div class="row align-items-center g-3">
          <div class="col-lg-7">
            <h1 class="h3 fw-bold text-white mb-1">Hello, {{ name }}!</h1>
            <p class="text-white-50 mb-0">You have <b class="text-white">{{ d.counts.today }}</b> student(s) today and <b class="text-white">{{ d.counts.pending_evaluations }}</b> evaluation(s) pending.</p>
          </div>
          <div class="col-lg-5 d-flex gap-2 justify-content-lg-end flex-wrap">
            <router-link to="/examiner/students?evaluation=pending" class="btn btn-light fw-bold"><i class="bi bi-clipboard-check me-1"></i>Evaluate now</router-link>
            <router-link to="/examiner/exams" class="btn btn-outline-light"><i class="bi bi-calendar-plus me-1"></i>Create slots</router-link>
          </div>
        </div>
      </div>

      <div class="row g-3 mb-4">
        <div class="col-6 col-xl-3"><StatCard label="Assigned examinations" :value="d.counts.assigned_exams" icon="clipboard2-check" color="#4f46e5" to="/examiner/exams" /></div>
        <div class="col-6 col-xl-3"><StatCard label="Created slots" :value="d.counts.slots" icon="calendar3-week" color="#06b6d4" to="/examiner/slots" /></div>
        <div class="col-6 col-xl-3"><StatCard label="Booked students" :value="d.counts.booked_students" icon="people" color="#10b981" to="/examiner/students" /></div>
        <div class="col-6 col-xl-3"><StatCard label="Pending evaluations" :value="d.counts.pending_evaluations" icon="hourglass-split" color="#f59e0b" to="/examiner/students?evaluation=pending" /></div>
      </div>

      <div class="row g-4 mb-4">
        <div class="col-xl-7">
          <div class="card-emp h-100">
            <div class="card-header d-flex justify-content-between"><span><i class="bi bi-clipboard2-check me-2 text-primary"></i>Assigned examinations</span><router-link to="/examiner/exams" class="small">All</router-link></div>
            <div class="list-group list-group-flush">
              <div v-if="!d.exams.length" class="p-4 text-center text-muted small">No examinations assigned yet.</div>
              <router-link v-for="e in d.exams" :key="e.id" :to="'/examiner/exams/' + e.id" class="list-group-item list-group-item-action bg-transparent py-3">
                <div class="d-flex justify-content-between align-items-center gap-2">
                  <div class="min-w-0"><div class="fw-semibold">{{ e.name }}</div><small class="text-muted">{{ e.course_code }} · {{ e.exam_type }} · {{ e.my_slots }} my slot(s)</small></div>
                  <div class="text-end"><StatusBadge :status="e.status" /><div v-if="e.can_create_slots" class="small text-success mt-1"><i class="bi bi-unlock"></i> Slot creation open</div></div>
                </div>
              </router-link>
            </div>
          </div>
        </div>
        <div class="col-xl-5">
          <div class="card-emp h-100">
            <div class="card-header"><i class="bi bi-calendar-week me-2 text-primary"></i>Students in the next 7 days</div>
            <div class="card-body"><ChartBox type="bar" :labels="d.week_load.map(w => $f.fmtDay(w.date))" :datasets="[{ label: 'Students', data: d.week_load.map(w => w.count), color: '#06b6d4' }]" :height="240" /></div>
          </div>
        </div>
      </div>

      <div class="row g-4">
        <div class="col-xl-6">
          <div class="card-emp h-100">
            <div class="card-header"><i class="bi bi-hourglass-split me-2 text-warning"></i>Pending evaluations</div>
            <div class="list-group list-group-flush">
              <div v-if="!d.pending.length" class="p-4 text-center text-muted small"><i class="bi bi-emoji-smile d-block fs-3"></i>All caught up!</div>
              <div v-for="b in d.pending" :key="b.id" class="list-group-item bg-transparent d-flex align-items-center gap-2">
                <span class="avatar avatar-sm">{{ $f.initials(b.student_name) }}</span>
                <div class="flex-grow-1 min-w-0"><div class="fw-semibold">{{ b.student_name }}</div><small class="text-muted">{{ b.exam_name }} · {{ $f.fmtDay(b.date) }}</small></div>
                <router-link :to="'/examiner/evaluate/' + b.id" class="btn btn-sm btn-gradient">Evaluate</router-link>
              </div>
            </div>
          </div>
        </div>
        <div class="col-xl-6">
          <div class="card-emp h-100">
            <div class="card-header"><i class="bi bi-calendar-event me-2 text-primary"></i>Upcoming slots</div>
            <div class="list-group list-group-flush">
              <div v-if="!d.upcoming_slots.length" class="p-4 text-center text-muted small">No upcoming slots</div>
              <div v-for="s in d.upcoming_slots" :key="s.id" class="list-group-item bg-transparent d-flex align-items-center gap-3">
                <div class="date-box"><div>{{ new Date(s.date).getDate() }}</div><small>{{ new Date(s.date).toLocaleString('en', { month: 'short' }) }}</small></div>
                <div class="flex-grow-1 min-w-0"><div class="fw-semibold text-truncate">{{ s.exam_name }}</div><small class="text-muted">{{ $f.fmtTime(s.start_time) }}–{{ $f.fmtTime(s.end_time) }} · {{ s.booked_count }}/{{ s.capacity }} booked</small></div>
                <StatusBadge :status="s.status" />
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
import LoadingBlock from '@/components/common/LoadingBlock.vue'
import StatCard from '@/components/common/StatCard.vue'
import StatusBadge from '@/components/common/StatusBadge.vue'
import ChartBox from '@/components/charts/ChartBox.vue'
export default {
  name: 'ExaminerDashboard',
  components: { LoadingBlock, StatCard, StatusBadge, ChartBox },
  data: () => ({ d: null }),
  computed: { name () { return this.$store.state.auth.user.name } },
  async mounted () { try { this.d = (await api.get('/examiner/dashboard')).data.data } catch (e) { this.$error(e) } }
}
</script>
<style scoped>
.hero-card { background: linear-gradient(135deg, #0891b2, #4f46e5); border: 0; }
.date-box { width: 50px; text-align: center; border-radius: 12px; background: rgba(79,70,229,.08); color: var(--emp-primary); padding: .35rem 0; font-weight: 800; line-height: 1.1; }
.date-box small { font-size: .65rem; text-transform: uppercase; font-weight: 700; }
</style>
