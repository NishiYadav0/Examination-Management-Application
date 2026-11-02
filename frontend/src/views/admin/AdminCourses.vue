<template>
  <div>
    <PageHeader title="Courses" subtitle="Create, update and retire the courses under which examinations are conducted." :crumbs="[{ label: 'Admin', to: '/admin' }, { label: 'Courses' }]">
      <button class="btn btn-gradient" @click="openForm()"><i class="bi bi-plus-lg me-1"></i>New course</button>
    </PageHeader>

    <div class="card-emp">
      <div class="p-3 d-flex flex-wrap gap-2 border-bottom">
        <div class="input-group" style="max-width:320px">
          <span class="input-group-text"><i class="bi bi-search"></i></span>
          <input v-model="q" class="form-control" placeholder="Search code, name, department">
        </div>
        <select v-model="status" class="form-select" style="max-width:160px"><option value="">All status</option><option value="active">Active</option><option value="inactive">Inactive</option></select>
        <div class="ms-auto btn-group">
          <button class="btn btn-sm" :class="view === 'grid' ? 'btn-primary' : 'btn-light'" @click="view = 'grid'" title="Card view"><i class="bi bi-grid"></i></button>
          <button class="btn btn-sm" :class="view === 'table' ? 'btn-primary' : 'btn-light'" @click="view = 'table'" title="Table view"><i class="bi bi-list-ul"></i></button>
        </div>
      </div>
      <LoadingBlock v-if="loading" class="p-3" />
      <EmptyState v-else-if="!filtered.length" icon="journal-x" title="No courses found" text="Try a different search or create a new course." />
      <div v-else-if="view === 'grid'" class="row g-3 p-3">
        <div class="col-md-6 col-xl-4" v-for="c in filtered" :key="c.id">
          <div class="course-card h-100 hover-lift">
            <div class="d-flex justify-content-between align-items-start">
              <span class="badge-soft bs-primary fs-6">{{ c.code }}</span>
              <StatusBadge :status="c.status" />
            </div>
            <h6 class="fw-bold mt-3 mb-1">{{ c.name }}</h6>
            <p class="small text-muted text-truncate-2 mb-3">{{ c.description || 'No description' }}</p>
            <div class="d-flex flex-wrap gap-3 small text-muted mb-3">
              <span><i class="bi bi-building me-1"></i>{{ c.department || '—' }}</span>
              <span><i class="bi bi-layers me-1"></i>{{ c.level || '—' }}</span>
              <span><i class="bi bi-award me-1"></i>{{ c.credits }} credits</span>
              <span><i class="bi bi-clipboard2-check me-1"></i>{{ c.exam_count }} exams</span>
            </div>
            <div class="d-flex gap-2">
              <router-link :to="'/admin/exams?course_id=' + c.id" class="btn btn-sm btn-soft flex-grow-1">Examinations</router-link>
              <button class="btn btn-sm btn-icon btn-light" @click="openForm(c)" title="Edit"><i class="bi bi-pencil"></i></button>
              <button class="btn btn-sm btn-icon btn-soft-danger" @click="remove(c)" title="Delete"><i class="bi bi-trash"></i></button>
            </div>
          </div>
        </div>
      </div>
      <div v-else class="table-responsive">
        <table class="table table-emp">
          <thead><tr><th>Code</th><th>Name</th><th>Department</th><th>Level</th><th>Credits</th><th>Exams</th><th>Status</th><th class="text-end">Actions</th></tr></thead>
          <tbody>
            <tr v-for="c in filtered" :key="c.id">
              <td class="fw-bold text-primary">{{ c.code }}</td><td>{{ c.name }}</td><td>{{ c.department || '—' }}</td><td>{{ c.level || '—' }}</td>
              <td>{{ c.credits }}</td><td>{{ c.exam_count }}</td><td><StatusBadge :status="c.status" /></td>
              <td class="text-end text-nowrap">
                <button class="btn btn-sm btn-icon btn-light me-1" @click="openForm(c)"><i class="bi bi-pencil"></i></button>
                <button class="btn btn-sm btn-icon btn-soft-danger" @click="remove(c)"><i class="bi bi-trash"></i></button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <BaseModal :show="show" :title="form.id ? 'Edit course' : 'New course'" icon="journal-plus" @close="show = false">
      <form id="courseForm" @submit.prevent="save" novalidate class="row g-3">
        <div class="col-md-4"><label class="form-label">Code *</label><input v-model.trim="form.code" class="form-control text-uppercase" :class="{ 'is-invalid': e.code }" maxlength="20" required><div class="invalid-feedback">{{ e.code }}</div></div>
        <div class="col-md-8"><label class="form-label">Name *</label><input v-model.trim="form.name" class="form-control" :class="{ 'is-invalid': e.name }" maxlength="150" required><div class="invalid-feedback">{{ e.name }}</div></div>
        <div class="col-md-6"><label class="form-label">Department</label><input v-model.trim="form.department" class="form-control"></div>
        <div class="col-md-6"><label class="form-label">Level</label><select v-model="form.level" class="form-select"><option value="">—</option><option>Foundation</option><option>Diploma</option><option>Degree</option><option>PG</option></select></div>
        <div class="col-md-6"><label class="form-label">Credits</label><input v-model.number="form.credits" type="number" min="0" max="20" class="form-control" :class="{ 'is-invalid': e.credits }"><div class="invalid-feedback">{{ e.credits }}</div></div>
        <div class="col-md-6"><label class="form-label">Status</label><select v-model="form.status" class="form-select"><option value="active">Active</option><option value="inactive">Inactive</option></select></div>
        <div class="col-12"><label class="form-label">Description</label><textarea v-model="form.description" rows="3" class="form-control"></textarea></div>
      </form>
      <template #footer>
        <button class="btn btn-light" @click="show = false">Cancel</button>
        <button class="btn btn-gradient" form="courseForm" :disabled="busy">{{ form.id ? 'Save changes' : 'Create course' }}</button>
      </template>
    </BaseModal>
  </div>
</template>

<script>
import api from '@/services/api'
import PageHeader from '@/components/common/PageHeader.vue'
import StatusBadge from '@/components/common/StatusBadge.vue'
import LoadingBlock from '@/components/common/LoadingBlock.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import BaseModal from '@/components/common/BaseModal.vue'

const blank = () => ({ id: null, code: '', name: '', department: '', level: '', credits: 4, status: 'active', description: '' })
export default {
  name: 'AdminCourses',
  components: { PageHeader, StatusBadge, LoadingBlock, EmptyState, BaseModal },
  data: () => ({ courses: [], loading: true, q: '', status: '', view: 'grid', show: false, form: blank(), e: {}, busy: false }),
  computed: {
    filtered () {
      const q = this.q.toLowerCase()
      return this.courses.filter(c => (!this.status || c.status === this.status) &&
        (!q || [c.code, c.name, c.department].join(' ').toLowerCase().includes(q)))
    }
  },
  mounted () { this.load() },
  methods: {
    async load () {
      this.loading = true
      try { this.courses = (await api.get('/admin/courses')).data.data } catch (e) { this.$error(e) }
      this.loading = false
    },
    openForm (c) { this.form = c ? { ...blank(), ...c } : blank(); this.e = {}; this.show = true },
    async save () {
      this.e = {}
      if (!this.form.code) this.e.code = 'Required'
      if (!this.form.name) this.e.name = 'Required'
      if (Object.keys(this.e).length) return
      this.busy = true
      try {
        const res = this.form.id ? await api.put(`/admin/courses/${this.form.id}`, this.form) : await api.post('/admin/courses', this.form)
        this.$toast(res.data.message); this.show = false; this.load()
      } catch (err) { this.e = err.fieldErrors || {}; this.$error(err) }
      this.busy = false
    },
    async remove (c) {
      if (!await this.$confirm({ title: 'Delete course?', message: `Delete ${c.code} – ${c.name}? Courses with booking history cannot be deleted.`, variant: 'danger', confirmText: 'Delete', icon: 'trash' })) return
      try { const r = await api.delete(`/admin/courses/${c.id}`); this.$toast(r.data.message); this.load() } catch (e) { this.$error(e) }
    }
  }
}
</script>
<style scoped>
.course-card { border: 1px solid var(--emp-border); border-radius: 16px; padding: 1.25rem; background: var(--emp-card-bg); }
</style>
