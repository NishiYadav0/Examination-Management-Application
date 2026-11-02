<template>
  <div>
    <LoadingBlock v-if="!u" cards />
    <template v-else>
      <PageHeader :title="u.name" :subtitle="u.email" :crumbs="[{ label: 'Admin', to: '/admin' }, { label: isStudent ? 'Students' : 'Examiners', to: isStudent ? '/admin/students' : '/admin/examiners' }, { label: u.name }]">
        <button class="btn" :class="u.active ? 'btn-soft-danger' : 'btn-soft-success'" @click="toggleBlock"><i :class="u.active ? 'bi bi-slash-circle me-1' : 'bi bi-check-circle me-1'"></i>{{ u.active ? 'Block' : 'Unblock' }}</button>
        <button class="btn btn-light" @click="resetPw"><i class="bi bi-key me-1"></i>Reset password</button>
        <button class="btn btn-soft-danger" @click="remove" title="Delete account"><i class="bi bi-trash"></i></button>
      </PageHeader>

      <div v-if="!u.active" class="alert alert-danger d-flex gap-2 align-items-center"><i class="bi bi-slash-circle fs-5"></i><div><b>This account is blocked.</b> {{ u.blocked_reason }}</div></div>

      <div class="row g-3 mb-4">
        <div class="col-6 col-lg-2" v-for="s in statCards" :key="s.label"><StatCard v-bind="s" /></div>
      </div>

      <div class="row g-4">
        <div class="col-xl-4">
          <div class="card-emp">
            <div class="card-body text-center">
              <span class="avatar avatar-lg" :class="{ 'opacity-50': !u.active }">{{ $f.initials(u.name) }}</span>
              <h5 class="fw-bold mt-3 mb-0">{{ u.name }}</h5>
              <div class="small text-muted">{{ isStudent ? u.profile.roll_no : u.profile.employee_id }}</div>
              <div class="d-flex justify-content-center gap-2 mt-2"><span class="badge-soft bs-primary text-capitalize">{{ u.role }}</span><StatusBadge :status="u.active ? 'active' : 'blocked'" /></div>
              <div class="small text-muted mt-3">Joined {{ $f.fmtDate(u.created_at) }} · Last login {{ u.last_login_at ? $f.timeAgo(u.last_login_at) : 'never' }}</div>
            </div>
            <div class="divider"></div>
            <div class="card-body">
              <div class="d-flex justify-content-between align-items-center mb-3"><b>Edit profile</b><small class="text-muted">Admin override</small></div>
              <form @submit.prevent="save" class="row g-2 small">
                <div class="col-12"><label class="form-label">Name</label><input v-model.trim="f.name" class="form-control form-control-sm" required></div>
                <div class="col-12"><label class="form-label">E-mail</label><input v-model.trim="f.email" type="email" class="form-control form-control-sm" required></div>
                <div class="col-6"><label class="form-label">Phone</label><input v-model.trim="f.phone" class="form-control form-control-sm"></div>
                <template v-if="isStudent">
                  <div class="col-6"><label class="form-label">Roll no</label><input v-model.trim="f.roll_no" class="form-control form-control-sm"></div>
                  <div class="col-12"><label class="form-label">Program</label><input v-model="f.program" class="form-control form-control-sm"></div>
                  <div class="col-6"><label class="form-label">Department</label><input v-model="f.department" class="form-control form-control-sm"></div>
                  <div class="col-6"><label class="form-label">Year</label><input v-model.number="f.year" type="number" min="1" max="6" class="form-control form-control-sm"></div>
                </template>
                <template v-else>
                  <div class="col-6"><label class="form-label">Employee ID</label><input v-model.trim="f.employee_id" class="form-control form-control-sm"></div>
                  <div class="col-6"><label class="form-label">Department</label><input v-model="f.department" class="form-control form-control-sm"></div>
                  <div class="col-6"><label class="form-label">Designation</label><input v-model="f.designation" class="form-control form-control-sm"></div>
                  <div class="col-12"><label class="form-label">Specialization</label><input v-model="f.specialization" class="form-control form-control-sm"></div>
                </template>
                <div class="col-12 mt-3"><button class="btn btn-gradient btn-sm w-100">Save profile</button></div>
              </form>
            </div>
          </div>
        </div>

        <div class="col-xl-8">
          <div class="card-emp mb-4">
            <div class="card-header"><i class="bi bi-bar-chart me-2 text-primary"></i>{{ isStudent ? 'Performance per examination (%)' : 'Evaluations per examination' }}</div>
            <div class="card-body">
              <ChartBox v-if="isStudent" type="bar" :labels="u.chart.map(c => c.exam)" :datasets="[{ label: 'Score %', data: u.chart.map(c => c.pct), colors: u.chart.map(c => c.pct >= 40 ? '#4f46e5' : '#ef4444') }]" :height="240" />
              <ChartBox v-else type="doughnut" :labels="u.chart.map(c => c.exam)" :datasets="[{ data: u.chart.map(c => c.count) }]" :height="240" />
            </div>
          </div>

          <ul class="nav nav-pills nav-pills-emp mb-3 gap-2">
            <li v-for="t in tabs" :key="t.k"><button class="nav-link" :class="{ active: tab === t.k }" @click="tab = t.k">{{ t.label }}</button></li>
          </ul>

          <div class="card-emp" v-if="tab === 'bookings'"><BookingTable :bookings="u.bookings" show-exam @changed="load" /></div>
          <div class="card-emp" v-if="tab === 'slots'"><SlotTable :slots="u.slots" show-exam @changed="load" /></div>
          <div class="card-emp" v-if="tab === 'exams'">
            <div class="list-group list-group-flush">
              <router-link v-for="e in u.assigned_exams" :key="e.id" :to="'/admin/exams/' + e.id" class="list-group-item list-group-item-action d-flex justify-content-between align-items-center py-3 bg-transparent">
                <div><div class="fw-semibold">{{ e.name }}</div><small class="text-muted">{{ e.course_code }} · {{ e.exam_type }}</small></div><StatusBadge :status="e.status" />
              </router-link>
              <div v-if="!u.assigned_exams.length" class="p-4 text-center text-muted small">No examinations assigned</div>
            </div>
          </div>
          <div class="card-emp" v-if="tab === 'activity'">
            <div class="card-body">
              <div v-if="!u.activity.length" class="text-muted small">No activity recorded.</div>
              <div class="timeline">
                <div v-for="a in u.activity" :key="a.id" class="timeline-item done">
                  <div class="small fw-semibold text-capitalize">{{ a.action.replace(/_/g, ' ') }}</div>
                  <div class="small text-muted">{{ a.details }} · {{ $f.fmtDateTime(a.created_at) }}</div>
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
import PageHeader from '@/components/common/PageHeader.vue'
import LoadingBlock from '@/components/common/LoadingBlock.vue'
import StatCard from '@/components/common/StatCard.vue'
import StatusBadge from '@/components/common/StatusBadge.vue'
import ChartBox from '@/components/charts/ChartBox.vue'
import BookingTable from '@/components/admin/BookingTable.vue'
import SlotTable from '@/components/admin/SlotTable.vue'

export default {
  name: 'AdminUserDetail',
  components: { PageHeader, LoadingBlock, StatCard, StatusBadge, ChartBox, BookingTable, SlotTable },
  props: { id: String },
  data: () => ({ u: null, f: {}, tab: '' }),
  computed: {
    isStudent () { return this.u.role === 'student' },
    tabs () {
      return this.isStudent ? [{ k: 'bookings', label: 'Examination history' }, { k: 'activity', label: 'Activity log' }]
        : [{ k: 'exams', label: 'Assigned exams' }, { k: 'slots', label: 'Slots' }, { k: 'activity', label: 'Activity log' }]
    },
    statCards () {
      const s = this.u.stats
      if (this.isStudent) {
        return [
          { label: 'Bookings', value: s.total_bookings, icon: 'bookmark', color: '#4f46e5' }, { label: 'Active', value: s.active, icon: 'calendar-check', color: '#06b6d4' },
          { label: 'Completed', value: s.completed, icon: 'check2-circle', color: '#10b981' }, { label: 'Cancelled', value: s.cancelled, icon: 'x-circle', color: '#64748b' },
          { label: 'Absent', value: s.absent, icon: 'person-x', color: '#ef4444' }, { label: 'Avg score', value: s.avg_pct != null ? s.avg_pct + '%' : '—', icon: 'graph-up', color: '#7c3aed' }
        ]
      }
      return [
        { label: 'Assigned exams', value: s.assigned_exams, icon: 'clipboard2-check', color: '#4f46e5' }, { label: 'Slots', value: s.slots, icon: 'calendar3-week', color: '#06b6d4' },
        { label: 'Students booked', value: s.students_booked, icon: 'people', color: '#10b981' }, { label: 'Evaluated', value: s.evaluations, icon: 'award', color: '#7c3aed' },
        { label: 'Pending', value: s.pending, icon: 'hourglass-split', color: '#f59e0b' }, { label: 'Avg given', value: s.avg_given_pct != null ? s.avg_given_pct + '%' : '—', icon: 'graph-up', color: '#ec4899' }
      ]
    }
  },
  mounted () { this.load() },
  methods: {
    async load () {
      try {
        this.u = (await api.get(`/admin/users/${this.id}`)).data.data
        this.f = { name: this.u.name, email: this.u.email, phone: this.u.phone, ...this.u.profile }
        if (!this.tab) this.tab = this.tabs[0].k
      } catch (e) { this.$error(e); this.$router.push('/admin') }
    },
    async save () {
      try { const r = await api.put(`/admin/users/${this.id}`, this.f); this.$toast(r.data.message); this.load() } catch (e) { this.$error(e) }
    },
    async toggleBlock () {
      let reason = null
      if (this.u.active) {
        reason = await this.$confirm({ title: `Block ${this.u.name}?`, message: 'The user is logged out immediately and cannot sign in.', input: 'Reason', variant: 'danger', confirmText: 'Block', icon: 'slash-circle' })
        if (!reason) return
      }
      try { const r = await api.post(`/admin/users/${this.id}/block`, { block: this.u.active, reason: reason && reason.trim() }); this.$toast(r.data.message); this.load() } catch (e) { this.$error(e) }
    },
    async resetPw () {
      if (!await this.$confirm({ title: 'Reset password?', message: 'A new random password will be generated and e-mailed to the user. Existing sessions are signed out.', confirmText: 'Reset', icon: 'key' })) return
      try {
        const r = await api.post(`/admin/users/${this.id}/reset-password`)
        this.$confirm({ title: 'New password', message: `New password: ${r.data.data.password}`, confirmText: 'OK', cancelText: 'Close', icon: 'key' })
      } catch (e) { this.$error(e) }
    },
    async remove () {
      if (!await this.$confirm({ title: 'Delete account?', message: 'Accounts with examination history cannot be deleted – block them instead.', variant: 'danger', confirmText: 'Delete', icon: 'trash' })) return
      try { await api.delete(`/admin/users/${this.id}`); this.$toast('Account deleted'); this.$router.push(this.isStudent ? '/admin/students' : '/admin/examiners') } catch (e) { this.$error(e) }
    }
  }
}
</script>
