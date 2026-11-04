<template>
  <div>
    <PageHeader title="My slots" subtitle="All slots you created across examinations." :crumbs="[{ label: 'Examiner', to: '/examiner' }, { label: 'Slots' }]" />
    <ul class="nav nav-pills nav-pills-emp mb-3 gap-2">
      <li v-for="t in tabs" :key="t.k"><button class="nav-link" :class="{ active: when === t.k }" @click="when = t.k; load()">{{ t.label }}</button></li>
    </ul>
    <LoadingBlock v-if="loading" />
    <EmptyState v-else-if="!slots.length" icon="calendar-x" title="No slots" text="Open an assigned examination to create slots." ><router-link to="/examiner/exams" class="btn btn-soft">Assigned exams</router-link></EmptyState>
    <div v-else>
      <div v-for="(group, day) in grouped" :key="day" class="mb-4">
        <div class="day-head"><i class="bi bi-calendar-event me-2"></i>{{ $f.fmtDate(day, { weekday: 'long', day: 'numeric', month: 'long', year: 'numeric' }) }} <span v-if="day === today" class="badge bg-danger ms-2">Today</span></div>
        <div class="row g-3">
          <div class="col-md-6 col-xl-4" v-for="s in group" :key="s.id">
            <div class="card-emp h-100 p-3 slot-card" :class="'st-' + s.status">
              <div class="d-flex justify-content-between align-items-start">
                <div><div class="fw-bold">{{ $f.fmtTime(s.start_time) }} – {{ $f.fmtTime(s.end_time) }}</div><small class="text-muted">{{ s.exam_name }}</small></div>
                <StatusBadge :status="s.status" />
              </div>
              <div class="small text-muted my-2"><i :class="s.mode === 'online' ? 'bi bi-camera-video' : 'bi bi-geo-alt'"></i> {{ s.mode === 'online' ? (s.meeting_link || 'Online') : s.venue }}</div>
              <div class="progress mb-1" style="height:6px"><div class="progress-bar" :style="{ width: (s.booked_count / s.capacity * 100) + '%' }"></div></div>
              <div class="small">{{ s.booked_count }}/{{ s.capacity }} booked</div>
              <div class="d-flex gap-2 mt-3">
                <router-link :to="'/examiner/students?slot=' + s.id" class="btn btn-sm btn-soft flex-grow-1"><i class="bi bi-people me-1"></i>Students</router-link>
                <a v-if="s.meeting_link" :href="s.meeting_link" target="_blank" rel="noopener" class="btn btn-sm btn-light" title="Join"><i class="bi bi-camera-video"></i></a>
                <button v-if="['available','full'].includes(s.status) && s.date <= today" class="btn btn-sm btn-soft-success" @click="complete(s)" title="Mark completed"><i class="bi bi-check2-all"></i></button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
<script>
import api from '@/services/api'
import PageHeader from '@/components/common/PageHeader.vue'
import LoadingBlock from '@/components/common/LoadingBlock.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import StatusBadge from '@/components/common/StatusBadge.vue'
export default {
  name: 'ExaminerSlots',
  components: { PageHeader, LoadingBlock, EmptyState, StatusBadge },
  data: () => ({ slots: [], loading: true, when: 'upcoming', tabs: [{ k: 'upcoming', label: 'Upcoming' }, { k: 'past', label: 'Past' }, { k: '', label: 'All' }] }),
  computed: {
    today () { return this.$f.todayISO() },
    grouped () {
      const g = {}
      const list = this.when === 'past' ? [...this.slots].reverse() : this.slots
      list.forEach(s => { (g[s.date] = g[s.date] || []).push(s) })
      return g
    }
  },
  mounted () { this.load() },
  methods: {
    async load () { this.loading = true; try { this.slots = (await api.get('/examiner/slots', { params: { when: this.when || undefined } })).data.data } catch (e) { this.$error(e) } this.loading = false },
    async complete (s) {
      try { const r = await api.post(`/examiner/slots/${s.id}/complete`); this.$toast(r.data.message); this.load() } catch (e) { this.$error(e) }
    }
  }
}
</script>
<style scoped>
.day-head { font-weight: 700; margin-bottom: .75rem; color: var(--emp-muted); font-size: .9rem; }
.slot-card { border-left: 4px solid var(--emp-primary); }
.slot-card.st-full { border-left-color: #ef4444; }
.slot-card.st-completed { border-left-color: #10b981; }
.slot-card.st-cancelled { border-left-color: #94a3b8; opacity: .7; }
</style>
