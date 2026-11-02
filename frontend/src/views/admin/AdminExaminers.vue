<template>
  <div>
    <PageHeader title="Examiners" subtitle="Examiners cannot self-register – create their accounts here. Credentials are e-mailed automatically." :crumbs="[{ label: 'Admin', to: '/admin' }, { label: 'Examiners' }]">
      <button class="btn btn-gradient" @click="open"><i class="bi bi-person-plus me-1"></i>Add examiner</button>
    </PageHeader>
    <UserList role="examiner" ref="list" />

    <BaseModal :show="show" title="Add examiner" subtitle="A welcome e-mail with the login details will be sent" icon="person-plus" size="lg" @close="show = false">
      <div v-if="created" class="text-center py-3">
        <span class="icon-box bg-success bg-opacity-10 text-success mb-3" style="width:64px;height:64px;font-size:1.8rem"><i class="bi bi-check2-circle"></i></span>
        <h5 class="fw-bold">Examiner account created</h5>
        <p class="text-muted small">Share these credentials if the e-mail does not arrive.</p>
        <div class="cred mx-auto">
          <div><span class="text-muted">E-mail</span><b>{{ created.email }}</b></div>
          <div><span class="text-muted">Password</span><b>{{ created.initial_password }}</b></div>
        </div>
      </div>
      <form v-else id="exForm" class="row g-3" @submit.prevent="save" novalidate>
        <div class="col-md-6"><label class="form-label">Full name *</label><input v-model.trim="f.name" class="form-control" :class="{ 'is-invalid': e.name }" placeholder="Dr. Jane Doe"><div class="invalid-feedback">{{ e.name }}</div></div>
        <div class="col-md-6"><label class="form-label">E-mail *</label><input v-model.trim="f.email" type="email" class="form-control" :class="{ 'is-invalid': e.email }"><div class="invalid-feedback">{{ e.email }}</div></div>
        <div class="col-md-6"><label class="form-label">Phone</label><input v-model.trim="f.phone" class="form-control" :class="{ 'is-invalid': e.phone }"><div class="invalid-feedback">{{ e.phone }}</div></div>
        <div class="col-md-6"><label class="form-label">Employee ID</label><input v-model.trim="f.employee_id" class="form-control text-uppercase" :class="{ 'is-invalid': e.employee_id }" placeholder="Auto-generated if empty"><div class="invalid-feedback">{{ e.employee_id }}</div></div>
        <div class="col-md-6"><label class="form-label">Department *</label><input v-model.trim="f.department" class="form-control" :class="{ 'is-invalid': e.department }" placeholder="CSE"><div class="invalid-feedback">{{ e.department }}</div></div>
        <div class="col-md-6"><label class="form-label">Designation</label><select v-model="f.designation" class="form-select"><option>Professor</option><option>Associate Professor</option><option>Assistant Professor</option><option>Teaching Fellow</option><option>Guest Faculty</option></select></div>
        <div class="col-md-6"><label class="form-label">Specialization</label><input v-model.trim="f.specialization" class="form-control"></div>
        <div class="col-md-6"><label class="form-label">Office</label><input v-model.trim="f.office" class="form-control"></div>
        <div class="col-12">
          <label class="form-label">Initial password</label>
          <div class="input-group">
            <input v-model="f.password" class="form-control" :class="{ 'is-invalid': e.password }" placeholder="Leave empty to generate one">
            <button type="button" class="btn btn-light" @click="f.password = gen()">Generate</button>
            <div class="invalid-feedback">{{ e.password }}</div>
          </div>
        </div>
      </form>
      <template #footer>
        <template v-if="created"><button class="btn btn-light" @click="open">Add another</button><button class="btn btn-gradient" @click="show = false">Done</button></template>
        <template v-else><button class="btn btn-light" @click="show = false">Cancel</button><button class="btn btn-gradient" form="exForm" :disabled="busy">Create examiner</button></template>
      </template>
    </BaseModal>
  </div>
</template>
<script>
import api from '@/services/api'
import PageHeader from '@/components/common/PageHeader.vue'
import UserList from '@/components/admin/UserList.vue'
import BaseModal from '@/components/common/BaseModal.vue'
const blank = () => ({ name: '', email: '', phone: '', employee_id: '', department: '', designation: 'Assistant Professor', specialization: '', office: '', password: '' })
export default {
  name: 'AdminExaminers',
  components: { PageHeader, UserList, BaseModal },
  data () { return { show: this.$route.query.new === '1', f: blank(), e: {}, busy: false, created: null } },
  methods: {
    open () { this.f = blank(); this.e = {}; this.created = null; this.show = true },
    gen () { return 'Exam@' + Math.random().toString(36).slice(2, 8) },
    async save () {
      const e = {}
      if (!this.f.name) e.name = 'Required'
      if (!/^[^@\s]+@[^@\s]+\.[a-zA-Z]{2,}$/.test(this.f.email)) e.email = 'Valid e-mail required'
      if (!this.f.department) e.department = 'Required'
      if (this.f.password && this.f.password.length < 6) e.password = 'Min 6 characters'
      this.e = e
      if (Object.keys(e).length) return
      this.busy = true
      try {
        const r = await api.post('/admin/examiners', this.f)
        this.created = r.data.data; this.$toast(r.data.message); this.$refs.list.load()
      } catch (err) { this.e = err.fieldErrors || {}; this.$error(err) }
      this.busy = false
    }
  }
}
</script>
<style scoped>
.cred { max-width: 340px; border: 1px dashed var(--emp-border); border-radius: 14px; padding: 1rem; text-align: left; }
.cred div { display: flex; justify-content: space-between; padding: .25rem 0; }
</style>
