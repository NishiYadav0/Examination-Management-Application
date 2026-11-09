<template>
  <div>
    <PageHeader title="Reports & background jobs" subtitle="Monthly HTML reports, scheduled job triggers and the full activity log." :crumbs="[{ label: 'Admin', to: '/admin' }, { label: 'Reports & Jobs' }]" />
    <div class="row g-4 mb-4">
      <div class="col-md-6">
        <div class="card-emp h-100 p-4">
          <div class="d-flex gap-3">
            <span class="icon-box bg-primary bg-opacity-10 text-primary"><i class="bi bi-bell"></i></span>
            <div class="flex-grow-1">
              <h6 class="fw-bold mb-1">Daily examination reminder</h6>
              <p class="small text-muted">Runs every day via Celery Beat. E-mails students with examinations in the next 48 h (exam, date & time, examiner, instructions) and nudges students who haven't booked open exams.</p>
              <button class="btn btn-soft" :disabled="busy.daily" @click="run('daily-reminder')"><span v-if="busy.daily" class="spinner-border spinner-border-sm me-1"></span><i v-else class="bi bi-play-fill me-1"></i>Run now</button>
            </div>
          </div>
        </div>
      </div>
      <div class="col-md-6">
        <div class="card-emp h-100 p-4">
          <div class="d-flex gap-3">
            <span class="icon-box bg-success bg-opacity-10 text-success"><i class="bi bi-file-earmark-bar-graph"></i></span>
            <div class="flex-grow-1">
              <h6 class="fw-bold mb-1">Monthly examination report</h6>
              <p class="small text-muted">Generated on the 1st of every month and e-mailed to the admin as HTML. Generate any month on demand:</p>
              <div class="d-flex gap-2 flex-wrap">
                <input v-model="month" type="month" class="form-control" style="max-width:190px" aria-label="Month">
                <button class="btn btn-soft-success" :disabled="busy.monthly" @click="run('monthly-report')"><span v-if="busy.monthly" class="spinner-border spinner-border-sm me-1"></span><i v-else class="bi bi-play-fill me-1"></i>Generate</button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <div class="card-emp mb-4">
      <div class="card-header d-flex justify-content-between align-items-center"><span><i class="bi bi-archive me-2 text-primary"></i>Generated monthly reports</span><button class="btn btn-sm btn-light" @click="load"><i class="bi bi-arrow-clockwise"></i></button></div>
      <div class="table-responsive">
        <table class="table table-emp">
          <thead><tr><th>Month</th><th>Exams</th><th>Evaluated</th><th>Completed</th><th>Pending</th><th>E-mailed</th><th>Generated</th><th></th></tr></thead>
          <tbody>
            <tr v-if="!reports.length"><td colspan="8" class="text-center text-muted py-4">No reports yet – click Generate above.</td></tr>
            <tr v-for="r in reports" :key="r.id">
              <td class="fw-semibold">{{ monthLabel(r.month) }}</td><td>{{ r.stats.exams_conducted }}</td><td>{{ r.stats.students_evaluated }}</td>
              <td>{{ r.stats.completed_bookings }}</td><td>{{ r.stats.pending_evaluations }}</td>
              <td><StatusBadge :status="r.emailed ? 'done' : 'failed'" :label="r.emailed ? 'Sent' : 'Not sent'" /></td>
              <td class="small">{{ $f.fmtDateTime(r.created_at) }}</td>
              <td class="text-end"><button class="btn btn-sm btn-soft" @click="view(r)"><i class="bi bi-eye me-1"></i>View</button></td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <div class="card-emp" id="activity">
      <div class="card-header d-flex justify-content-between align-items-center flex-wrap gap-2">
        <span><i class="bi bi-activity me-2 text-primary"></i>Activity log (latest 200)</span>
        <input v-model="aq" class="form-control form-control-sm" style="max-width:240px" placeholder="Filter user / action">
      </div>
      <div class="table-responsive" style="max-height:520px">
        <table class="table table-emp">
          <thead><tr><th>When</th><th>User</th><th>Role</th><th>Action</th><th>Details</th></tr></thead>
          <tbody><tr v-for="a in activityF" :key="a.id"><td class="small text-nowrap">{{ $f.fmtDateTime(a.created_at) }}</td><td>{{ a.user_name || 'System' }}</td>
            <td><span class="badge-soft bs-secondary text-capitalize">{{ a.role || '-' }}</span></td><td class="text-capitalize small fw-semibold">{{ a.action.replace(/_/g, ' ') }}</td><td class="small text-muted">{{ a.details }}</td></tr></tbody>
        </table>
      </div>
    </div>

    <BaseModal :show="!!preview" :title="preview ? 'Report · ' + monthLabel(preview.month) : ''" icon="file-earmark-richtext" size="xl" @close="preview = null">
      <iframe v-if="preview" :srcdoc="preview.html" class="w-100 border-0 rounded" style="height:70vh" title="Monthly report"></iframe>
      <template #footer><button class="btn btn-light" @click="printReport"><i class="bi bi-printer me-1"></i>Print / Save as PDF</button><button class="btn btn-gradient" @click="preview = null">Close</button></template>
    </BaseModal>
  </div>
</template>
<script>
import api from '@/services/api'
import PageHeader from '@/components/common/PageHeader.vue'
import StatusBadge from '@/components/common/StatusBadge.vue'
import BaseModal from '@/components/common/BaseModal.vue'
export default {
  name: 'AdminReports',
  components: { PageHeader, StatusBadge, BaseModal },
  data: () => ({ reports: [], activity: [], aq: '', month: new Date().toISOString().slice(0, 7), busy: { daily: false, monthly: false }, preview: null }),
  computed: {
    activityF () { const q = this.aq.toLowerCase(); return this.activity.filter(a => !q || [a.user_name, a.action, a.details].join(' ').toLowerCase().includes(q)) }
  },
  mounted () { this.load() },
  methods: {
    async load () {
      try {
        const [r, a] = await Promise.all([api.get('/admin/reports'), api.get('/admin/activity')])
        this.reports = r.data.data; this.activity = a.data.data
      } catch (e) { this.$error(e) }
    },
    monthLabel (m) { const [y, mo] = m.split('-'); return new Date(y, mo - 1).toLocaleString('en', { month: 'long', year: 'numeric' }) },
    async run (job) {
      const key = job === 'daily-reminder' ? 'daily' : 'monthly'
      this.busy[key] = true
      try {
        const r = await api.post(`/admin/jobs/${job}`, job === 'monthly-report' ? { month: this.month } : {})
        this.$toast(r.data.message, 'info')
        const id = r.data.data.task_id
        for (let i = 0; i < 20; i++) {
          await new Promise(res => setTimeout(res, 1000))
          const st = (await api.get(`/admin/jobs/status/${id}`)).data.data
          if (st.state === 'SUCCESS') { this.$toast(`Job finished: ${JSON.stringify(st.result)}`); break }
          if (st.state === 'FAILURE') { this.$toast('Job failed – check the Celery worker terminal', 'danger'); break }
        }
        this.load()
      } catch (e) { this.$error(e) }
      this.busy[key] = false
    },
    async view (r) {
      try { this.preview = (await api.get(`/admin/reports/${r.id}/html`)).data.data } catch (e) { this.$error(e) }
    },
    printReport () {
      const w = window.open('', '_blank'); w.document.write(this.preview.html); w.document.close(); w.focus(); setTimeout(() => w.print(), 300)
    }
  }
}
</script>
