<template>
  <div>
    <PageHeader title="My profile" subtitle="Keep your details up to date and manage your password." />
    <div class="row g-4">
      <div class="col-xl-4">
        <div class="card-emp overflow-hidden">
          <div class="profile-cover"></div>
          <div class="card-body text-center" style="margin-top:-52px">
            <span class="avatar avatar-lg border border-4 border-white shadow">{{ $f.initials(user.name) }}</span>
            <h5 class="fw-bold mt-3 mb-0">{{ user.name }}</h5>
            <div class="text-muted small">{{ user.email }}</div>
            <div class="d-flex justify-content-center gap-2 mt-2">
              <span class="badge-soft bs-primary text-capitalize"><i class="bi bi-shield-check me-1"></i>{{ user.role }}</span>
              <StatusBadge :status="user.active ? 'active' : 'blocked'" />
            </div>
            <div class="divider my-3"></div>
            <div class="text-start small d-grid gap-2">
              <div v-if="p.roll_no"><i class="bi bi-person-vcard me-2 text-muted"></i>Roll no: <b>{{ p.roll_no }}</b></div>
              <div v-if="p.employee_id"><i class="bi bi-person-vcard me-2 text-muted"></i>Employee ID: <b>{{ p.employee_id }}</b></div>
              <div v-if="p.department"><i class="bi bi-building me-2 text-muted"></i>{{ p.department }}</div>
              <div v-if="user.phone"><i class="bi bi-telephone me-2 text-muted"></i>{{ user.phone }}</div>
              <div><i class="bi bi-calendar3 me-2 text-muted"></i>Member since {{ $f.fmtDate(user.created_at) }}</div>
              <div><i class="bi bi-clock-history me-2 text-muted"></i>Last login {{ $f.fmtDateTime(user.last_login_at) }}</div>
            </div>
          </div>
        </div>
        <div class="card-emp mt-4 p-3 d-flex gap-3 align-items-center">
          <span class="icon-box bg-primary bg-opacity-10 text-primary"><i class="bi bi-cloud-arrow-down"></i></span>
          <div class="flex-grow-1"><div class="fw-bold">Your data</div><small class="text-muted">Export your activity & statistics as CSV</small></div>
          <router-link to="/export" class="btn btn-sm btn-soft">Export</router-link>
        </div>
        <div class="card-emp mt-4">
          <div class="card-header"><i class="bi bi-activity me-2 text-primary"></i>Recent activity</div>
          <div class="card-body">
            <div v-if="!activity.length" class="small text-muted">No activity yet.</div>
            <div class="timeline">
              <div v-for="a in activity.slice(0, 8)" :key="a.id" class="timeline-item done">
                <div class="small fw-semibold text-capitalize">{{ a.action.replace(/_/g, ' ') }}</div>
                <div class="small text-muted">{{ a.details }} · {{ $f.timeAgo(a.created_at) }}</div>
              </div>
            </div>
          </div>
        </div>
      </div>
      <div class="col-xl-8">
        <div class="card-emp">
          <div class="card-header"><i class="bi bi-person-lines-fill me-2 text-primary"></i>Personal details</div>
          <div class="card-body">
            <form @submit.prevent="save" novalidate>
              <div class="row g-3">
                <div class="col-md-6"><label class="form-label">Full name *</label><input v-model.trim="f.name" class="form-control" :class="{ 'is-invalid': e.name }" required><div class="invalid-feedback">{{ e.name }}</div></div>
                <div class="col-md-6"><label class="form-label">Phone</label><input v-model.trim="f.phone" class="form-control" :class="{ 'is-invalid': e.phone }"><div class="invalid-feedback">{{ e.phone }}</div></div>
                <div class="col-md-6"><label class="form-label">E-mail</label><input :value="user.email" class="form-control" disabled><div class="form-text">Contact admin to change e-mail.</div></div>
                <template v-if="user.role === 'student'">
                  <div class="col-md-6"><label class="form-label">Roll number</label><input :value="p.roll_no" class="form-control" disabled></div>
                  <div class="col-md-6"><label class="form-label">Program</label><input v-model="f.program" class="form-control"></div>
                  <div class="col-md-3"><label class="form-label">Year</label><input v-model.number="f.year" type="number" min="1" max="6" class="form-control"></div>
                  <div class="col-md-3"><label class="form-label">Gender</label><select v-model="f.gender" class="form-select"><option value="">—</option><option>Male</option><option>Female</option><option>Other</option></select></div>
                  <div class="col-md-6"><label class="form-label">Department</label><input v-model="f.department" class="form-control"></div>
                  <div class="col-md-6"><label class="form-label">Date of birth</label><input v-model="f.dob" type="date" class="form-control" :max="$f.todayISO()"></div>
                  <div class="col-12"><label class="form-label">Address</label><input v-model="f.address" class="form-control"></div>
                </template>
                <template v-if="user.role === 'examiner'">
                  <div class="col-md-6"><label class="form-label">Department</label><input v-model="f.department" class="form-control"></div>
                  <div class="col-md-6"><label class="form-label">Designation</label><input v-model="f.designation" class="form-control"></div>
                  <div class="col-md-6"><label class="form-label">Specialization</label><input v-model="f.specialization" class="form-control"></div>
                  <div class="col-md-6"><label class="form-label">Office</label><input v-model="f.office" class="form-control"></div>
                </template>
                <div class="col-12" v-if="user.role !== 'admin'"><label class="form-label">Short bio</label><textarea v-model="f.bio" class="form-control" rows="3" maxlength="500"></textarea></div>
                <div class="col-12"><button class="btn btn-gradient" :disabled="busy"><span v-if="busy" class="spinner-border spinner-border-sm me-2"></span>Save changes</button></div>
              </div>
            </form>
          </div>
        </div>
        <div class="card-emp mt-4">
          <div class="card-header"><i class="bi bi-key me-2 text-primary"></i>Security · change password</div>
          <div class="card-body">
            <form @submit.prevent="changePw" novalidate class="row g-3">
              <div class="col-md-4"><label class="form-label">Current password</label><input v-model="pw.current_password" type="password" class="form-control" :class="{ 'is-invalid': pe.current_password }" autocomplete="current-password"><div class="invalid-feedback">{{ pe.current_password }}</div></div>
              <div class="col-md-4"><label class="form-label">New password</label><input v-model="pw.new_password" type="password" class="form-control" :class="{ 'is-invalid': pe.new_password }" autocomplete="new-password"><div class="invalid-feedback">{{ pe.new_password }}</div></div>
              <div class="col-md-4"><label class="form-label">Confirm new password</label><input v-model="pw.confirm" type="password" class="form-control" :class="{ 'is-invalid': pe.confirm }" autocomplete="new-password"><div class="invalid-feedback">{{ pe.confirm }}</div></div>
              <div class="col-12"><button class="btn btn-outline-primary" :disabled="pwBusy">Update password</button></div>
            </form>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import api from '@/services/api'
import PageHeader from '@/components/common/PageHeader.vue'
import StatusBadge from '@/components/common/StatusBadge.vue'
export default {
  name: 'ProfileView',
  components: { PageHeader, StatusBadge },
  data: () => ({ f: {}, e: {}, busy: false, pw: { current_password: '', new_password: '', confirm: '' }, pe: {}, pwBusy: false, activity: [] }),
  computed: {
    user () { return this.$store.state.auth.user || {} },
    p () { return this.user.profile || {} }
  },
  async mounted () {
    const u = await this.$store.dispatch('auth/fetchMe')
    this.f = { name: u.name, phone: u.phone || '', ...u.profile }
    try { this.activity = (await api.get('/profile/activity')).data.data } catch (e) { /* ignore */ }
  },
  methods: {
    async save () {
      this.e = {}
      if (!this.f.name || this.f.name.length < 2) { this.e.name = 'Name is required'; return }
      this.busy = true
      try {
        const { data } = await api.put('/profile', this.f)
        this.$store.commit('auth/setUser', data.data)
        this.$toast('Profile updated')
      } catch (err) { this.e = err.fieldErrors || {}; this.$error(err) }
      this.busy = false
    },
    async changePw () {
      this.pe = {}
      if (!this.pw.current_password) this.pe.current_password = 'Required'
      if (this.pw.new_password.length < 6) this.pe.new_password = 'At least 6 characters'
      if (this.pw.new_password !== this.pw.confirm) this.pe.confirm = 'Does not match'
      if (Object.keys(this.pe).length) return
      this.pwBusy = true
      try {
        await api.post('/profile/change-password', this.pw)
        this.$toast('Password changed')
        this.pw = { current_password: '', new_password: '', confirm: '' }
      } catch (err) { this.pe = err.fieldErrors || {}; this.$error(err) }
      this.pwBusy = false
    }
  }
}
</script>
<style scoped>.profile-cover { height: 90px; background: var(--emp-gradient); }</style>
