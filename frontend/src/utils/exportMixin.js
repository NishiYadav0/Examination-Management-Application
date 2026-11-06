// "Export my data" – starts a Celery CSV export job, polls it and downloads the file.
// Works for every role: this.exportCsv('activity'), this.exportCsv('full'), …
import api from '@/services/api'
import { downloadBlob } from '@/utils/format'

export default {
  data: () => ({ exporting: false, exportingKind: null }),
  methods: {
    async exportCsv (kind = 'exam_history') {
      if (this.exporting) return
      this.exporting = true
      this.exportingKind = kind
      try {
        const r = await api.post('/exports', { kind })
        this.$toast(r.data.message, 'info')
        const id = r.data.data.id
        if (this.onExportStarted) this.onExportStarted(r.data.data)
        for (let i = 0; i < 40; i++) {
          await new Promise(res => setTimeout(res, 1000))
          const j = (await api.get(`/exports/${id}`)).data.data
          if (j.status === 'done') {
            this.$toast(`${j.kind_label}: ${j.row_count} row(s). A copy was also e-mailed to you.`, 'success', 'CSV ready')
            this.$store.dispatch('notif/load')
            await this.downloadExport(j)
            break
          }
          if (j.status === 'failed') { this.$toast(j.error || 'Export failed', 'danger'); break }
          if (i === 39) this.$toast('Still working… check "Export my data" in a moment.', 'warning')
        }
        if (this.onExportDone) this.onExportDone()
      } catch (e) { this.$error(e) }
      this.exporting = false
      this.exportingKind = null
    },
    async downloadExport (j) {
      try {
        const res = await api.get(`/exports/${j.id}/download`, { responseType: 'blob' })
        downloadBlob(res.data, j.filename)
      } catch (e) { this.$error(e) }
    }
  }
}
