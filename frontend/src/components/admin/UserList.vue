<template>
  <div class="card-emp">
    <div class="p-3 d-flex flex-wrap gap-2 border-bottom align-items-center">
      <div class="input-group" style="max-width:340px">
        <span class="input-group-text"><i class="bi bi-search"></i></span>
        <input v-model="q" class="form-control" :placeholder="role === 'student' ? 'Name, e-mail, roll no, program' : 'Name, e-mail, employee id, department'">
      </div>
      <div class="btn-group">
        <button v-for="s in ['', 'active', 'blocked']" :key="s" class="btn btn-sm" :class="status === s ? 'btn-primary' : 'btn-light'" @click="status = s">{{ s ? $f.statusMeta(s).label : 'All' }}</button>
      </div>
      <span class="ms-auto small text-muted">{{ filtered.length }} {{ role }}(s)</span>
    </div>
    <LoadingBlock v-if="loading" class="p-3" />
    <EmptyState v-else-if="!filtered.length" icon="people" :title="'No ' + role + 's found'" text="Try another search." />
    <div v-else class="table-responsive">
      <table class="table table-emp">
        <thead>
          <tr>
            <th>{{ role === 'student' ? 'Student' : 'Examiner' }}</th>
            <th v-if="role === 'student'">Roll no</th><th v-else>Employee ID</th>
            <th>{{ role === 'student' ? 'Program' : 'Department' }}</th>
            <th v-if="role === 'student'">Bookings</th>
            <template v-else><th>Exams</th><th>Slots</th><th>Evaluated</th></template>
            <th>Joined</th><th>Status</th><th class="text-end">Actions</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="u in paged" :key="u.id">
            <td>
              <router-link :to="'/admin/users/' + u.id" class="d-flex align-items-center gap-2 text-decoration-none text-body">
                <span class="avatar avatar-sm" :class="{ 'opacity-50': !u.active }">{{ $f.initials(u.name) }}</span>
                <div><div class="fw-semibold">{{ u.name }}</div><small class="text-muted">{{ u.email }}</small></div>
              </router-link>
            </td>
            <td class="small fw-semibold">{{ u.profile.roll_no || u.profile.employee_id }}</td>
            <td class="small">{{ role === 'student' ? u.profile.program : u.profile.department }}<div class="text-muted" v-if="role !== 'student'">{{ u.profile.designation }}</div></td>
            <td v-if="role === 'student'">{{ u.bookings }}</td>
            <template v-else><td>{{ u.assigned_exams }}</td><td>{{ u.slots }}</td><td>{{ u.evaluations }}</td></template>
            <td class="small">{{ $f.fmtDate(u.created_at) }}</td>
            <td><StatusBadge :status="u.active ? 'active' : 'blocked'" /><div v-if="!u.active && u.blocked_reason" class="small text-muted text-truncate" style="max-width:140px" :title="u.blocked_reason">{{ u.blocked_reason }}</div></td>
            <td class="text-end text-nowrap">
              <router-link :to="'/admin/users/' + u.id" class="btn btn-sm btn-icon btn-soft me-1" title="View / edit"><i class="bi bi-eye"></i></router-link>
              <button class="btn btn-sm btn-icon me-1" :class="u.active ? 'btn-soft-danger' : 'btn-soft-success'" :title="u.active ? 'Block' : 'Unblock'" @click="toggle(u)"><i :class="u.active ? 'bi bi-slash-circle' : 'bi bi-check-circle'"></i></button>
            </td>
          </tr>
        </tbody>
      </table>
      <Paginator v-model="page" :total="filtered.length" :per-page="10" />
    </div>
  </div>
</template>

<script>
import api from '@/services/api'
import LoadingBlock from '@/components/common/LoadingBlock.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import StatusBadge from '@/components/common/StatusBadge.vue'
import Paginator from '@/components/common/Paginator.vue'
export default {
  name: 'UserList',
  components: { LoadingBlock, EmptyState, StatusBadge, Paginator },
  props: { role: String },
  data () { return { users: [], loading: true, q: this.$route.query.q || '', status: this.$route.query.status || '', page: 1 } },
  computed: {
    filtered () {
      const q = this.q.toLowerCase()
      return this.users.filter(u => (!this.status || (this.status === 'active') === u.active) &&
        (!q || [u.name, u.email, u.phone, ...Object.values(u.profile || {})].join(' ').toLowerCase().includes(q)))
    },
    paged () { return this.filtered.slice((this.page - 1) * 10, this.page * 10) }
  },
  watch: { filtered () { this.page = 1 } },
  mounted () { this.load() },
  methods: {
    async load () {
      this.loading = true
      try { this.users = (await api.get(`/admin/${this.role}s`)).data.data } catch (e) { this.$error(e) }
      this.loading = false
    },
    async toggle (u) {
      let reason = null
      if (u.active) {
        reason = await this.$confirm({ title: `Block ${u.name}?`, message: 'The user will be logged out immediately and cannot sign in until unblocked.', input: 'Reason (shown to the user)', variant: 'danger', confirmText: 'Block', icon: 'slash-circle' })
        if (!reason) return
      } else if (!await this.$confirm({ title: `Unblock ${u.name}?`, message: 'The user will be able to log in again.', variant: 'success', confirmText: 'Unblock', icon: 'check-circle' })) return
      try {
        const r = await api.post(`/admin/users/${u.id}/block`, { block: u.active, reason: reason && reason.trim() })
        this.$toast(r.data.message); this.load()
      } catch (e) { this.$error(e) }
    }
  }
}
</script>
