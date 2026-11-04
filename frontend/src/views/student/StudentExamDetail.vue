<template>
  <div>
    <LoadingBlock v-if="!e" cards />
    <template v-else>
      <PageHeader :title="e.name" :subtitle="e.course_code + ' · ' + e.course_name" :crumbs="[{ label: 'Student', to: '/student' }, { label: 'Exams', to: '/student/exams' }, { label: e.name }]" />
      <div class="row g-4">
        <div class="col-xl-8">
          <!-- my booking -->
          <div v-if="e.my_booking" class="card-emp booked-card mb-4">
            <div class="card-body d-flex flex-wrap gap-3 align-items-center">
              <span class="icon-box bg-success text-white"><i class="bi bi-bookmark-check-fill"></i></span>
              <div class="flex-grow-1">
                <div class="fw-bold">{{ e.my_booking.status === 'booked' ? "You're booked!" : e.my_booking.status === 'completed' ? 'Examination attended' : 'Marked absent' }}</div>
                <div class="small text-muted">{{ $f.fmtDay(e.my_booking.date) }} · {{ $f.fmtTime(e.my_booking.start_time) }}–{{ $f.fmtTime(e.my_booking.end_time) }} with {{ e.my_booking.examiner_name }}</div>
              </div>
              <StatusBadge :status="e.my_booking.status" />
              <a v-if="e.my_booking.meeting_link" :href="e.my_booking.meeting_link" target="_blank" rel="noopener" class="btn btn-sm btn-soft"><i class="bi bi-camera-video me-1"></i>Meeting</a>
              <router-link to="/student/bookings" class="btn btn-sm btn-light">Manage</router-link>
            </div>
          </div>

          <!-- slots -->
          <div class="card-emp mb-4">
            <div class="card-header d-flex justify-content-between align-items-center flex-wrap gap-2">
              <span><i class="bi bi-calendar3-week me-2 text-primary"></i>Available slots</span>
              <div class="small text-muted"><span class="legend l-av"></span>Available <span class="legend l-full ms-2"></span>Full</div>
            </div>
            <div class="card-body">
              <div v-if="!e.booking_allowed" class="alert alert-secondary small d-flex gap-2"><i class="bi bi-info-circle"></i><div>{{ e.booking_message }}</div></div>
              <EmptyState v-if="!e.slots.length" icon="calendar-x" title="No slots published yet" text="Examiners haven't published slots for this examination yet." />
              <div v-for="(slots, day) in grouped" :key="day" class="mb-4">
                <div class="fw-bold small text-muted mb-2"><i class="bi bi-calendar-event me-1"></i>{{ $f.fmtDate(day, { weekday: 'long', day: 'numeric', month: 'long' }) }}</div>
                <div class="row g-2">
                  <div class="col-sm-6 col-lg-4" v-for="s in slots" :key="s.id">
                    <button class="slot-tile w-100" :class="{ full: s.status !== 'available', sel: sel && sel.id === s.id }" :disabled="!canBook || s.status !== 'available'" @click="choose(s)">
                      <div class="d-flex justify-content-between"><b>{{ $f.fmtTime(s.start_time) }}</b><small>{{ s.status === 'available' ? s.available_seats + ' left' : 'Full' }}</small></div>
                      <div class="small text-muted text-start"><i class="bi bi-person me-1"></i>{{ s.examiner_name }}</div>
                      <div class="small text-muted text-start"><i :class="s.mode === 'online' ? 'bi bi-camera-video me-1' : 'bi bi-geo-alt me-1'"></i>{{ s.mode === 'online' ? 'Online' : s.venue }}</div>
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <div class="card-emp">
            <div class="card-header"><i class="bi bi-grid-3x3-gap me-2 text-primary"></i>How you'll be evaluated</div>
            <div class="card-body">
              <div v-for="r in e.rubrics" :key="r.id" class="mb-3">
                <div class="d-flex justify-content-between small"><b>{{ r.criterion }}</b><span>{{ r.weightage }}%</span></div>
                <div class="progress" style="height:8px"><div class="progress-bar" :style="{ width: r.weightage + '%' }"></div></div>
                <small class="text-muted">{{ r.description }}</small>
              </div>
            </div>
          </div>
        </div>

        <div class="col-xl-4">
          <div class="card-emp mb-4">
            <div class="card-body">
              <div class="d-flex justify-content-between mb-3"><span class="badge-soft bs-info">{{ e.exam_type }}</span><StatusBadge :status="e.status" /></div>
              <div class="d-grid gap-2 small">
                <div class="d-flex justify-content-between"><span class="text-muted">Duration</span><b>{{ e.duration_minutes }} min</b></div>
                <div class="d-flex justify-content-between"><span class="text-muted">Maximum marks</span><b>{{ e.max_marks }}</b></div>
                <div class="d-flex justify-content-between"><span class="text-muted">Pass marks</span><b>{{ e.pass_marks }}</b></div>
                <div class="d-flex justify-content-between"><span class="text-muted">Booking</span><b>{{ $f.fmtDate(e.booking_start) }} – {{ $f.fmtDate(e.booking_end) }}</b></div>
                <div class="d-flex justify-content-between"><span class="text-muted">Exam period</span><b>{{ $f.fmtDate(e.exam_start) }} – {{ $f.fmtDate(e.exam_end) }}</b></div>
                <div class="d-flex justify-content-between"><span class="text-muted">Examiners</span><b class="text-end">{{ e.examiners.map(x => x.name).join(', ') }}</b></div>
              </div>
              <div v-if="e.requires_submission" class="alert alert-warning small mt-3 mb-0"><i class="bi bi-link-45deg me-1"></i>A project / submission link is required when booking.</div>
            </div>
          </div>
          <div class="card-emp">
            <div class="card-header"><i class="bi bi-info-square me-2 text-primary"></i>Instructions</div>
            <div class="card-body small"><p class="text-muted">{{ e.description }}</p><p class="mb-0">{{ e.instructions || 'No special instructions.' }}</p></div>
          </div>
        </div>
      </div>

      <BaseModal :show="!!sel" title="Confirm booking" :subtitle="e.name" icon="calendar-check" @close="sel = null">
        <div v-if="sel">
          <div class="confirm-box mb-3">
            <div><i class="bi bi-calendar-event me-2"></i><b>{{ $f.fmtDate(sel.date, { weekday: 'long', day: 'numeric', month: 'long', year: 'numeric' }) }}</b></div>
            <div><i class="bi bi-clock me-2"></i>{{ $f.fmtTime(sel.start_time) }} – {{ $f.fmtTime(sel.end_time) }}</div>
            <div><i class="bi bi-person me-2"></i>{{ sel.examiner_name }}</div>
            <div><i :class="sel.mode === 'online' ? 'bi bi-camera-video me-2' : 'bi bi-geo-alt me-2'"></i>{{ sel.mode === 'online' ? 'Online meeting' : sel.venue }}</div>
          </div>
          <div class="mb-3">
            <label class="form-label">Project / submission link <span v-if="e.requires_submission" class="text-danger">*</span></label>
            <input v-model.trim="link" type="url" class="form-control" :class="{ 'is-invalid': err.submission_link }" placeholder="https://github.com/you/project">
            <div class="invalid-feedback">{{ err.submission_link }}</div>
          </div>
          <div><label class="form-label">Note for the examiner</label><input v-model.trim="note" class="form-control" maxlength="300" placeholder="Optional"></div>
          <p class="small text-muted mt-3 mb-0"><i class="bi bi-info-circle me-1"></i>One booking per examination. You can cancel until {{ $f.fmtDate(e.booking_end) }}.</p>
        </div>
        <template #footer><button class="btn btn-light" @click="sel = null">Cancel</button><button class="btn btn-gradient" :disabled="busy" @click="book"><span v-if="busy" class="spinner-border spinner-border-sm me-1"></span>Confirm booking</button></template>
      </BaseModal>
    </template>
  </div>
</template>
<script>
import api from '@/services/api'
import PageHeader from '@/components/common/PageHeader.vue'
import LoadingBlock from '@/components/common/LoadingBlock.vue'
import StatusBadge from '@/components/common/StatusBadge.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import BaseModal from '@/components/common/BaseModal.vue'
export default {
  name: 'StudentExamDetail',
  components: { PageHeader, LoadingBlock, StatusBadge, EmptyState, BaseModal },
  props: { id: String },
  data: () => ({ e: null, sel: null, link: '', note: '', err: {}, busy: false }),
  computed: {
    canBook () { return this.e.booking_allowed && !this.e.my_booking },
    grouped () { const g = {}; this.e.slots.forEach(s => { (g[s.date] = g[s.date] || []).push(s) }); return g }
  },
  mounted () { this.load() },
  methods: {
    async load () { try { this.e = (await api.get(`/student/exams/${this.id}`)).data.data } catch (err) { this.$error(err); this.$router.push('/student/exams') } },
    choose (s) { this.sel = s; this.err = {} },
    async book () {
      this.err = {}
      if (this.e.requires_submission && !this.link) this.err.submission_link = 'Required for this examination'
      else if (this.link && !/^https?:\/\//.test(this.link)) this.err.submission_link = 'Must start with http(s)://'
      if (Object.keys(this.err).length) return
      this.busy = true
      try {
        const r = await api.post('/student/bookings', { slot_id: this.sel.id, submission_link: this.link, note: this.note })
        this.$toast(r.data.message, 'success', 'Booked!')
        this.sel = null
        this.$store.dispatch('notif/load')
        this.load()
      } catch (err) { this.err = err.fieldErrors || {}; this.$error(err); this.load() }
      this.busy = false
    }
  }
}
</script>
<style scoped>
.slot-tile { border: 1.5px solid var(--emp-border); border-radius: 14px; background: var(--emp-card-bg); padding: .75rem .9rem; transition: all .15s; color: inherit; }
.slot-tile:not(:disabled):hover { border-color: var(--emp-primary); transform: translateY(-2px); box-shadow: var(--emp-shadow); }
.slot-tile.sel { border-color: var(--emp-primary); background: rgba(79,70,229,.08); }
.slot-tile.full { opacity: .5; background: repeating-linear-gradient(45deg, transparent, transparent 6px, rgba(148,163,184,.12) 6px, rgba(148,163,184,.12) 12px); }
.slot-tile:disabled { cursor: not-allowed; }
.legend { display: inline-block; width: 10px; height: 10px; border-radius: 3px; margin-right: 4px; }
.l-av { border: 2px solid var(--emp-primary); } .l-full { background: #cbd5e1; }
.booked-card { border-left: 4px solid #10b981; }
.confirm-box { background: rgba(79,70,229,.06); border-radius: 14px; padding: 1rem 1.2rem; display: grid; gap: .4rem; }
</style>
