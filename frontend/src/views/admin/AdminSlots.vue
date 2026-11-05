<template>
  <div>
    <PageHeader title="Examiner slots" subtitle="Every slot created by examiners – reschedule, reassign or cancel in exceptional situations." :crumbs="[{ label: 'Admin', to: '/admin' }, { label: 'Slots' }]" />
    <div class="row g-3 mb-3">
      <div class="col-6 col-md-3" v-for="s in counters" :key="s.k">
        <div class="mini card-emp p-3 cursor-pointer" :class="{ sel: status === s.k }" @click="status = status === s.k ? '' : s.k">
          <div class="small text-muted">{{ s.label }}</div><div class="fs-4 fw-800" :style="{ color: s.c }">{{ count(s.k) }}</div>
        </div>
      </div>
    </div>
    <div class="card-emp">
      <div class="p-3 d-flex flex-wrap gap-2 border-bottom">
        <div class="input-group" style="max-width:300px"><span class="input-group-text"><i class="bi bi-search"></i></span><input v-model="q" class="form-control" placeholder="Exam or examiner"></div>
        <select v-model="examId" class="form-select" style="max-width:240px"><option value="">All examinations</option><option v-for="e in exams" :key="e.id" :value="e.id">{{ e.name }}</option></select>
        <select v-model="examinerId" class="form-select" style="max-width:200px"><option value="">All examiners</option><option v-for="x in examiners" :key="x.id" :value="x.id">{{ x.name }}</option></select>
        <input v-model="date" type="date" class="form-control" style="max-width:170px" aria-label="Date">
        <button v-if="q || examId || examinerId || date || status" class="btn btn-light" @click="q = examId = examinerId = date = status = ''">Clear</button>
      </div>
      <LoadingBlock v-if="loading" class="p-3" />
      <template v-else>
        <SlotTable :slots="paged" show-exam @changed="load" />
        <Paginator v-model="page" :total="filtered.length" :per-page="12" />
      </template>
    </div>
  </div>
</template>
<script>
import api from '@/services/api'
import PageHeader from '@/components/common/PageHeader.vue'
import LoadingBlock from '@/components/common/LoadingBlock.vue'
import Paginator from '@/components/common/Paginator.vue'
import SlotTable from '@/components/admin/SlotTable.vue'
export default {
  name: 'AdminSlots',
  components: { PageHeader, LoadingBlock, Paginator, SlotTable },
  data: () => ({ slots: [], exams: [], examiners: [], loading: true, q: '', examId: '', examinerId: '', date: '', status: '', page: 1,
    counters: [{ k: 'available', label: 'Available', c: '#10b981' }, { k: 'full', label: 'Full', c: '#ef4444' }, { k: 'completed', label: 'Completed', c: '#4f46e5' }, { k: 'cancelled', label: 'Cancelled', c: '#64748b' }] }),
  computed: {
    filtered () {
      const q = this.q.toLowerCase()
      return this.slots.filter(s => (!this.status || s.status === this.status) && (!this.examId || s.exam_id === this.examId) &&
        (!this.examinerId || s.examiner_id === this.examinerId) && (!this.date || s.date === this.date) &&
        (!q || [s.exam_name, s.examiner_name, s.course_code].join(' ').toLowerCase().includes(q)))
    },
    paged () { return this.filtered.slice((this.page - 1) * 12, this.page * 12) }
  },
  watch: { filtered () { this.page = 1 } },
  async mounted () {
    this.load()
    const [e, x] = await Promise.all([api.get('/admin/exams'), api.get('/admin/examiners')])
    this.exams = e.data.data; this.examiners = x.data.data
  },
  methods: {
    async load () { this.loading = true; try { this.slots = (await api.get('/admin/slots')).data.data } catch (e) { this.$error(e) } this.loading = false },
    count (k) { return this.slots.filter(s => s.status === k).length }
  }
}
</script>
<style scoped>.mini.sel { outline: 2px solid var(--emp-primary); }</style>
