<template>
  <div>
    <LoadingBlock v-if="!d" />
    <template v-else>
      <div class="d-flex justify-content-between align-items-center mb-3 no-print flex-wrap gap-2">
        <router-link to="/student/results" class="btn btn-light"><i class="bi bi-arrow-left me-1"></i>All results</router-link>
        <div class="d-flex gap-2">
          <button class="btn btn-soft" @click="download"><i class="bi bi-download me-1"></i>Download (HTML)</button>
          <button class="btn btn-gradient" @click="print"><i class="bi bi-printer me-1"></i>Print / Save PDF</button>
        </div>
      </div>
      <div class="card-emp scorecard mx-auto" ref="card">
        <div class="sc-head">
          <div class="d-flex justify-content-between align-items-start flex-wrap gap-3">
            <div><div class="small text-white-50 text-uppercase" style="letter-spacing:.15em">Examination Management Portal</div><h3 class="fw-bold text-white mb-0">Examination Scorecard</h3></div>
            <div class="text-end text-white"><div class="small text-white-50">Scorecard #</div><b>EMP-{{ d.booking.id.toString().padStart(6, '0') }}</b></div>
          </div>
        </div>
        <div class="card-body p-4">
          <div class="row g-3 mb-4">
            <div class="col-md-6">
              <div class="info-block"><div class="lbl">Student</div><b>{{ d.student.name }}</b><div class="small">Roll no {{ d.student.profile.roll_no }} · {{ d.student.profile.program }}</div></div>
            </div>
            <div class="col-md-6">
              <div class="info-block"><div class="lbl">Examination</div><b>{{ d.exam.name }}</b><div class="small">{{ d.exam.course_code }} – {{ d.exam.course_name }} · {{ d.exam.exam_type }}</div></div>
            </div>
            <div class="col-md-4"><div class="info-block"><div class="lbl">Date</div><b>{{ $f.fmtDate(d.booking.date) }}</b></div></div>
            <div class="col-md-4"><div class="info-block"><div class="lbl">Examiner</div><b>{{ d.evaluation.examiner_name }}</b></div></div>
            <div class="col-md-4"><div class="info-block"><div class="lbl">Result released</div><b>{{ $f.fmtDate(d.exam.published_at || d.evaluation.evaluated_at) }}</b></div></div>
          </div>
          <table class="table table-bordered align-middle mb-4">
            <thead class="table-light"><tr><th>Criterion</th><th class="text-center">Weightage</th><th class="text-center">Marks</th><th>Comment</th></tr></thead>
            <tbody>
              <tr v-for="s in d.evaluation.scores" :key="s.rubric_id">
                <td class="fw-semibold">{{ s.criterion }}</td><td class="text-center">{{ s.weightage }}%</td>
                <td class="text-center"><b>{{ s.marks }}</b> / {{ s.max_marks }}
                  <div class="progress mt-1" style="height:5px"><div class="progress-bar" :style="{ width: (s.marks / s.max_marks * 100) + '%' }"></div></div></td>
                <td class="small text-muted">{{ s.comment || '—' }}</td>
              </tr>
            </tbody>
          </table>
          <div class="row g-3 align-items-stretch mb-4">
            <div class="col-md-4"><div class="big-stat"><div class="lbl">Total</div><div class="val">{{ d.evaluation.total_marks }}<small>/{{ d.evaluation.max_marks }}</small></div></div></div>
            <div class="col-md-4"><div class="big-stat"><div class="lbl">Percentage</div><div class="val">{{ d.evaluation.percentage }}%</div></div></div>
            <div class="col-md-4"><div class="big-stat" :style="{ borderColor: $f.gradeColor(d.evaluation.grade) }"><div class="lbl">Grade · Result</div><div class="val" :style="{ color: $f.gradeColor(d.evaluation.grade) }">{{ d.evaluation.grade }} · {{ d.evaluation.passed ? 'PASS' : 'FAIL' }}</div></div></div>
          </div>
          <div class="feedback">
            <div class="lbl mb-1">Examiner remarks</div><p class="mb-3">{{ d.evaluation.remarks }}</p>
            <div class="row g-3">
              <div class="col-md-6" v-if="d.evaluation.strengths"><div class="lbl mb-1 text-success">Strengths</div><p class="mb-0 small">{{ d.evaluation.strengths }}</p></div>
              <div class="col-md-6" v-if="d.evaluation.improvements"><div class="lbl mb-1 text-warning">Areas to improve</div><p class="mb-0 small">{{ d.evaluation.improvements }}</p></div>
            </div>
          </div>
          <div class="small text-muted mt-4 d-flex justify-content-between flex-wrap"><span>Pass marks: {{ d.evaluation.pass_marks }} · Grades S ≥90, A ≥80, B ≥70, C ≥60, D ≥50, E ≥40</span><span>Generated {{ new Date().toLocaleString('en-IN') }}</span></div>
        </div>
      </div>
    </template>
  </div>
</template>
<script>
import api from '@/services/api'
import { downloadBlob } from '@/utils/format'
import LoadingBlock from '@/components/common/LoadingBlock.vue'
export default {
  name: 'StudentScorecard',
  components: { LoadingBlock },
  props: { id: String },
  data: () => ({ d: null }),
  async mounted () { try { this.d = (await api.get(`/student/results/${this.id}`)).data.data } catch (e) { this.$error(e); this.$router.push('/student/results') } },
  methods: {
    print () { window.print() },
    download () {
      const css = [...document.querySelectorAll('style, link[rel=stylesheet]')].map(n => n.outerHTML).join('')
      const html = `<!DOCTYPE html><html><head><meta charset="utf-8"><title>Scorecard</title>${css}</head><body style="padding:24px;background:#fff">${this.$refs.card.outerHTML}</body></html>`
      downloadBlob(new Blob([html], { type: 'text/html' }), `scorecard_${this.d.exam.name.replace(/\W+/g, '_')}.html`)
    }
  }
}
</script>
<style scoped>
.scorecard { max-width: 900px; overflow: hidden; }
.sc-head { background: var(--emp-gradient); padding: 1.75rem 2rem; }
.info-block { border: 1px solid var(--emp-border); border-radius: 12px; padding: .75rem 1rem; height: 100%; }
.lbl { font-size: .7rem; text-transform: uppercase; letter-spacing: .1em; color: var(--emp-muted); font-weight: 700; }
.big-stat { border: 2px solid var(--emp-border); border-radius: 14px; padding: 1rem; text-align: center; height: 100%; }
.big-stat .val { font-size: 1.8rem; font-weight: 800; }
.big-stat .val small { font-size: 1rem; color: var(--emp-muted); }
.feedback { background: rgba(79,70,229,.05); border-radius: 14px; padding: 1.25rem; }
</style>
