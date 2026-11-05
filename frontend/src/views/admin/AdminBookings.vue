<template>
  <div>
    <PageHeader title="Bookings" subtitle="All student bookings – search, reschedule to another slot/examiner or cancel." :crumbs="[{ label: 'Admin', to: '/admin' }, { label: 'Bookings' }]">
      <button class="btn btn-light" @click="exportCsv"><i class="bi bi-filetype-csv me-1"></i>Export view</button>
    </PageHeader>
    <div class="card-emp">
      <div class="p-3 d-flex flex-wrap gap-2 border-bottom">
        <div class="input-group" style="max-width:320px"><span class="input-group-text"><i class="bi bi-search"></i></span><input v-model="q" class="form-control" placeholder="Student, roll no, exam, booking #"></div>
        <select v-model="examId" class="form-select" style="max-width:240px"><option value="">All examinations</option><option v-for="e in exams" :key="e.id" :value="e.id">{{ e.name }}</option></select>
        <select v-model="status" class="form-select" style="max-width:170px"><option value="">All status</option><option v-for="s in ['booked','completed','absent','cancelled']" :key="s" :value="s">{{ $f.statusMeta(s).label }}</option></select>
        <span class="ms-auto small text-muted align-self-center">{{ filtered.length }} booking(s)</span>
      </div>
      <LoadingBlock v-if="loading" class="p-3" />
      <template v-else>
        <BookingTable :bookings="paged" show-exam @changed="load" />
        <Paginator v-model="page" :total="filtered.length" :per-page="12" />
      </template>
    </div>
  </div>
</template>
<script>
import api from '@/services/api'
import { downloadBlob } from '@/utils/format'
import PageHeader from '@/components/common/PageHeader.vue'
import LoadingBlock from '@/components/common/LoadingBlock.vue'
import Paginator from '@/components/common/Paginator.vue'
import BookingTable from '@/components/admin/BookingTable.vue'
export default {
  name: 'AdminBookings',
  components: { PageHeader, LoadingBlock, Paginator, BookingTable },
  data () { return { bookings: [], exams: [], loading: true, q: this.$route.query.q || '', examId: '', status: this.$route.query.status || '', page: 1 } },
  computed: {
    filtered () {
      const q = this.q.toLowerCase()
      return this.bookings.filter(b => (!this.status || b.status === this.status) && (!this.examId || b.exam_id === this.examId) &&
        (!q || String(b.id) === q || [b.student_name, b.roll_no, b.exam_name, b.student_email, b.examiner_name].join(' ').toLowerCase().includes(q)))
    },
    paged () { return this.filtered.slice((this.page - 1) * 12, this.page * 12) }
  },
  watch: { filtered () { this.page = 1 } },
  async mounted () { this.load(); this.exams = (await api.get('/admin/exams')).data.data },
  methods: {
    async load () { this.loading = true; try { this.bookings = (await api.get('/admin/bookings')).data.data } catch (e) { this.$error(e) } this.loading = false },
    exportCsv () {
      const head = ['Booking', 'Roll No', 'Student', 'Examination', 'Course', 'Date', 'Time', 'Examiner', 'Status', 'Marks']
      const rows = this.filtered.map(b => [b.id, b.roll_no, b.student_name, b.exam_name, b.course_code, b.date, b.start_time, b.examiner_name, b.status, b.total_marks ?? ''])
      const csv = [head, ...rows].map(r => r.map(v => `"${String(v ?? '').replace(/"/g, '""')}"`).join(',')).join('\n')
      downloadBlob(new Blob([csv], { type: 'text/csv' }), 'bookings.csv')
    }
  }
}
</script>
