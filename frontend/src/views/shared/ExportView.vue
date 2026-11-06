<template>
  <div>
    <PageHeader title="Export my data" :subtitle="subtitle" :crumbs="[{ label: 'Dashboard', to: $store.getters['auth/home'] }, { label: 'Export my data' }]" />

    <!-- hero: one-click complete export -->
    <div class="export-hero card-emp p-4 mb-4">
      <div class="row align-items-center g-3">
        <div class="col-lg-8 d-flex gap-3 align-items-center">
          <span class="hero-icon"><i class="bi bi-cloud-arrow-down"></i></span>
          <div>
            <h5 class="fw-bold text-white mb-1">Download everything in one click</h5>
            <p class="text-white-50 mb-0 small">Your profile, statistics, activity log{{ role === 'student' ? ', examination history' : role === 'examiner' ? ', slots and evaluations' : ', platform statistics and audit log' }} and notifications – as a single CSV file.
              It runs in the background (Celery); you'll get a notification and an e-mail with the file attached.</p>
          </div>
        </div>
        <div class="col-lg-4 text-lg-end">
          <button class="btn btn-light btn-lg fw-bold" :disabled="exporting" @click="exportCsv('full')">
            <span v-if="exporting && exportingKind === 'full'" class="spinner-border spinner-border-sm me-2"></span><i v-else class="bi bi-archive me-2"></i>Export everything
          </button>
        </div>
      </div>
    </div>

    <h6 class="small-caps text-muted mb-3">Or pick exactly what you need</h6>
    <LoadingBlock v-if="!kinds.length" :rows="2" />
    <div class="row g-3 mb-4">
      <div class="col-sm-6 col-xl-4" v-for="k in singleKinds" :key="k.key">
        <div class="card-emp h-100 p-3 kind-card hover-lift d-flex gap-3">
          <span class="icon-box" :style="{ background: color(k.key) + '1a', color: color(k.key) }"><i :class="'bi bi-' + k.icon"></i></span>
          <div class="flex-grow-1 min-w-0 d-flex flex-column">
            <div class="fw-bold">{{ k.label }}</div>
            <div class="small text-muted mb-2">{{ k.description }}</div>
            <div class="mt-auto d-flex align-items-center gap-2">
              <button class="btn btn-sm btn-soft" :disabled="exporting" @click="exportCsv(k.key)">
                <span v-if="exporting && exportingKind === k.key" class="spinner-border spinner-border-sm me-1"></span><i v-else class="bi bi-filetype-csv me-1"></i>Export CSV
              </button>
              <small v-if="lastOf(k.key)" class="text-muted">last: {{ $f.timeAgo(lastOf(k.key).created_at) }}</small>
            </div>
          </div>
        </div>
      </div>
    </div>

    <div class="card-emp">
      <div class="card-header d-flex justify-content-between align-items-center">
        <span><i class="bi bi-clock-history me-2 text-primary"></i>My export history</span>
        <button class="btn btn-sm btn-light" @click="load" title="Refresh"><i class="bi bi-arrow-clockwise"></i></button>
      </div>
      <div class="table-responsive">
        <table class="table table-emp">
          <thead><tr><th>Requested</th><th>Export</th><th>Status</th><th>Rows</th><th>File</th><th></th></tr></thead>
          <tbody>
            <tr v-if="!jobs.length"><td colspan="6" class="text-center text-muted py-4">No exports yet – choose one above.</td></tr>
            <tr v-for="j in jobs" :key="j.id">
              <td class="small text-nowrap">{{ $f.fmtDateTime(j.created_at) }}</td>
              <td class="fw-semibold">{{ j.kind_label }}</td>
              <td><StatusBadge :status="j.status" /><div v-if="j.error" class="small text-danger">{{ j.error }}</div></td>
              <td>{{ j.status === 'done' ? j.row_count : '—' }}</td>
              <td class="small text-muted text-truncate" style="max-width:260px">{{ j.filename || '—' }}</td>
              <td class="text-end"><button v-if="j.status === 'done'" class="btn btn-sm btn-soft" @click="downloadExport(j)"><i class="bi bi-download me-1"></i>Download</button></td>
            </tr>
          </tbody>
        </table>
      </div>
      <div class="p-3 border-top small text-muted"><i class="bi bi-shield-lock me-1"></i>Privacy: every export only contains <b>your own</b> data{{ role === 'admin' ? ' and the platform data you administer' : '' }}. Needs Redis + the Celery worker to be running.</div>
    </div>
  </div>
</template>

<script>
import api from '@/services/api'
import exportMixin from '@/utils/exportMixin'
import PageHeader from '@/components/common/PageHeader.vue'
import LoadingBlock from '@/components/common/LoadingBlock.vue'
import StatusBadge from '@/components/common/StatusBadge.vue'

const COLORS = { profile: '#4f46e5', activity: '#06b6d4', notifications: '#f59e0b', tickets: '#ec4899', exam_history: '#10b981',
  assigned_exams: '#7c3aed', slots: '#0891b2', evaluations: '#10b981', platform_stats: '#7c3aed', exams_overview: '#10b981', audit_log: '#ef4444' }

export default {
  name: 'ExportView',
  mixins: [exportMixin],
  components: { PageHeader, LoadingBlock, StatusBadge },
  data: () => ({ kinds: [], jobs: [] }),
  computed: {
    role () { return this.$store.getters['auth/role'] },
    singleKinds () { return this.kinds.filter(k => k.key !== 'full') },
    subtitle () { return 'Download your own activity, statistics and details from the portal as CSV files.' }
  },
  async mounted () {
    try { this.kinds = (await api.get('/exports/kinds')).data.data } catch (e) { this.$error(e) }
    this.load()
  },
  methods: {
    async load () { try { this.jobs = (await api.get('/exports')).data.data } catch (e) { this.$error(e) } },
    color (k) { return COLORS[k] || '#4f46e5' },
    lastOf (k) { return this.jobs.find(j => j.kind === k && j.status === 'done') },
    onExportStarted () { this.load() },
    onExportDone () { this.load() }
  }
}
</script>

<style scoped>
.export-hero { background: linear-gradient(135deg, #0f766e, #4f46e5 70%); border: 0; }
.hero-icon { width: 60px; height: 60px; border-radius: 18px; background: rgba(255,255,255,.15); color: #fff; display: inline-flex; align-items: center; justify-content: center; font-size: 1.8rem; flex-shrink: 0; }
</style>
