<template>
  <div>
    <PageHeader title="Browse examinations" subtitle="Search and filter examinations, then book a slot while booking is open." :crumbs="[{ label: 'Student', to: '/student' }, { label: 'Exams' }]" />
    <div class="card-emp p-3 mb-4">
      <div class="row g-2">
        <div class="col-lg-4"><div class="input-group"><span class="input-group-text"><i class="bi bi-search"></i></span><input v-model="q" class="form-control" placeholder="Search by exam, course or type"></div></div>
        <div class="col-6 col-lg-2"><select v-model="type" class="form-select"><option value="">All types</option><option v-for="t in types" :key="t">{{ t }}</option></select></div>
        <div class="col-6 col-lg-2"><select v-model="course" class="form-select"><option value="">All courses</option><option v-for="c in courses" :key="c.id" :value="String(c.id)">{{ c.code }}</option></select></div>
        <div class="col-6 col-lg-2"><select v-model="status" class="form-select"><option value="">Any status</option><option v-for="s in ['slot_creation','booking_open','closed','completed']" :key="s" :value="s">{{ $f.statusMeta(s).label }}</option></select></div>
        <div class="col-6 col-lg-2"><select v-model="availability" class="form-select"><option value="">All</option><option value="bookable">Bookable now</option><option value="booked">Booked by me</option></select></div>
      </div>
    </div>
    <LoadingBlock v-if="loading" />
    <EmptyState v-else-if="!list.length" icon="search" title="No examinations match" text="Try clearing some filters." ><button class="btn btn-soft" @click="clear">Clear filters</button></EmptyState>
    <div class="row g-4">
      <div class="col-md-6 col-xl-4" v-for="e in list" :key="e.id">
        <div class="exam-card card-emp h-100 hover-lift">
          <div class="head" :style="{ background: `linear-gradient(135deg, ${meta(e).color}, #0f172a 180%)` }">
            <div class="d-flex justify-content-between align-items-start">
              <span class="badge bg-white bg-opacity-25">{{ e.course_code }}</span>
              <StatusBadge :status="e.status" class="bg-white" />
            </div>
            <i :class="'bi bi-' + meta(e).icon + ' big'"></i>
            <div class="small opacity-75">{{ e.exam_type }}</div>
          </div>
          <div class="card-body d-flex flex-column">
            <h6 class="fw-bold mb-1">{{ e.name }}</h6>
            <div class="small text-muted mb-3">{{ e.course_name }}</div>
            <div class="d-flex flex-wrap gap-3 small text-muted mb-3">
              <span><i class="bi bi-clock me-1"></i>{{ e.duration_minutes }} min</span>
              <span><i class="bi bi-award me-1"></i>{{ e.max_marks }} marks</span>
              <span><i class="bi bi-people me-1"></i>{{ e.examiners.length }} examiner(s)</span>
            </div>
            <div class="small mb-3">
              <i class="bi bi-calendar-range me-1 text-primary"></i>Booking {{ $f.fmtDate(e.booking_start) }} – {{ $f.fmtDate(e.booking_end) }}
              <div v-if="e.status === 'booking_open'" class="mt-1" :class="e.available_seats ? 'text-success' : 'text-danger'"><i class="bi bi-circle-fill" style="font-size:.5rem"></i> {{ e.available_seats }} seat(s) left</div>
            </div>
            <div v-if="e.my_booking" class="booked small mb-3"><i class="bi bi-bookmark-check-fill me-1"></i>Booked · {{ $f.fmtDay(e.my_booking.date) }} {{ $f.fmtTime(e.my_booking.start_time) }}</div>
            <router-link :to="'/student/exams/' + e.id" class="btn mt-auto" :class="e.can_book ? 'btn-gradient' : 'btn-soft'">{{ e.can_book ? 'Choose a slot' : 'View details' }}</router-link>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
<script>
import api from '@/services/api'
import { EXAM_TYPES, TYPE_META } from '@/utils/format'
import PageHeader from '@/components/common/PageHeader.vue'
import LoadingBlock from '@/components/common/LoadingBlock.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import StatusBadge from '@/components/common/StatusBadge.vue'
export default {
  name: 'StudentExams',
  components: { PageHeader, LoadingBlock, EmptyState, StatusBadge },
  data () {
    return { exams: [], courses: [], loading: true, types: EXAM_TYPES, q: this.$route.query.q || '', type: '', course: '', status: '', availability: this.$route.query.availability || '' }
  },
  computed: {
    list () {
      const q = this.q.toLowerCase()
      return this.exams.filter(e => (!this.type || e.exam_type === this.type) && (!this.course || String(e.course_id) === this.course) &&
        (!this.status || e.status === this.status) && (!this.availability || (this.availability === 'bookable' ? e.can_book : !!e.my_booking)) &&
        (!q || [e.name, e.course_code, e.course_name, e.exam_type].join(' ').toLowerCase().includes(q)))
    }
  },
  async mounted () {
    try {
      const [e, c] = await Promise.all([api.get('/student/exams'), api.get('/public/courses')])
      this.exams = e.data.data; this.courses = c.data.data
    } catch (err) { this.$error(err) }
    this.loading = false
  },
  methods: {
    meta (e) { return TYPE_META[e.exam_type] || { icon: 'tag', color: '#4f46e5' } },
    clear () { this.q = this.type = this.course = this.status = this.availability = '' }
  }
}
</script>
<style scoped>
.exam-card { overflow: hidden; }
.exam-card .head { color: #fff; padding: 1.1rem 1.25rem 1rem; position: relative; min-height: 118px; }
.exam-card .big { position: absolute; right: 18px; bottom: 6px; font-size: 3rem; opacity: .25; }
.booked { background: rgba(16,185,129,.1); color: #047857; padding: .45rem .7rem; border-radius: 10px; font-weight: 600; }
[data-bs-theme="dark"] .booked { color: #6ee7b7; }
</style>
