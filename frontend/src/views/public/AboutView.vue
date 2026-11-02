<template>
  <div>
    <section class="page-hero">
      <div class="container">
        <div class="row align-items-center g-5">
          <div class="col-lg-7">
            <span class="small-caps text-primary">About EMP</span>
            <h1 class="display-5 fw-bold mt-2">Bringing order to examination season</h1>
            <p class="lead text-muted">Institutions still juggle spreadsheets, e-mails and phone calls to plan vivas and practicals.
              The Examination Management Portal gives administrators, examiners and students one shared, reliable workflow.</p>
          </div>
          <div class="col-lg-5">
            <div class="row g-3">
              <div class="col-6" v-for="v in values" :key="v.t">
                <div class="card-emp p-3 h-100 text-center">
                  <i :class="'bi bi-' + v.i + ' fs-3'" :style="{ color: v.c }"></i>
                  <div class="fw-bold mt-2">{{ v.t }}</div><small class="text-muted">{{ v.d }}</small>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>

    <section class="container py-5">
      <div class="row g-4">
        <div class="col-md-4" v-for="r in roles" :key="r.t">
          <div class="card-emp p-4 h-100">
            <span class="icon-box mb-3" :style="{ background: r.c + '1a', color: r.c }"><i :class="'bi bi-' + r.i"></i></span>
            <h5 class="fw-bold">{{ r.t }}</h5>
            <ul class="small text-muted ps-3 mb-0"><li v-for="p in r.p" :key="p" class="mb-1">{{ p }}</li></ul>
          </div>
        </div>
      </div>
    </section>

    <section class="container pb-5">
      <div class="card-emp p-4 p-lg-5">
        <div class="row g-4 align-items-center">
          <div class="col-lg-5">
            <span class="small-caps text-primary">Technology</span>
            <h3 class="fw-bold mt-2">Built on a lightweight, reliable stack</h3>
            <p class="text-muted mb-0">A Flask REST API with token based role security, a Vue 3 single page application styled with Bootstrap,
              SQLite storage, Redis caching and Celery background jobs for reminders, reports and exports.</p>
          </div>
          <div class="col-lg-7">
            <div class="row g-3">
              <div class="col-6 col-md-4" v-for="t in tech" :key="t.n">
                <div class="tech p-3 text-center"><i :class="'bi bi-' + t.i + ' fs-4 text-primary'"></i><div class="fw-semibold small mt-1">{{ t.n }}</div><small class="text-muted">{{ t.d }}</small></div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  </div>
</template>
<script>
export default {
  name: 'AboutView',
  data: () => ({
    values: [
      { i: 'shield-check', t: 'Fair', d: 'Same rules for everyone', c: '#10b981' },
      { i: 'eye', t: 'Transparent', d: 'Rubric-wise marks', c: '#4f46e5' },
      { i: 'lightning', t: 'Fast', d: 'Cached & async', c: '#f59e0b' },
      { i: 'phone', t: 'Anywhere', d: 'Responsive & installable', c: '#ec4899' }
    ],
    roles: [
      { t: 'Admin', i: 'shield-lock', c: '#4f46e5', p: ['Courses, examinations & rubrics', 'Opens/closes slot creation and booking', 'Reschedules bookings & reassigns examiners', 'Blocks/unblocks & edits any user', 'Publishes results and views analytics'] },
      { t: 'Examiner', i: 'person-badge', c: '#06b6d4', p: ['Created by admin – no self sign-up', 'Publishes slots during the creation window', 'Sees booked students & marks attendance', 'Evaluates with the predefined rubric', 'Marks slots / exams as completed'] },
      { t: 'Student', i: 'mortarboard', c: '#10b981', p: ['Registers and edits profile', 'Searches & filters examinations', 'Books one slot per exam, cancels before deadline', 'Tracks booking status & history', 'Views results, feedback & scorecards'] }
    ],
    tech: [
      { n: 'Flask', d: 'REST API', i: 'server' }, { n: 'Vue 3', d: 'SPA + Router + Vuex', i: 'window-stack' },
      { n: 'Bootstrap 5', d: 'Responsive UI', i: 'bootstrap' }, { n: 'SQLite', d: 'Database', i: 'database' },
      { n: 'Redis', d: 'Caching', i: 'lightning-charge' }, { n: 'Celery', d: 'Batch jobs', i: 'gear-wide-connected' }
    ]
  })
}
</script>
<style scoped>
.page-hero { padding: 4.5rem 0; background: var(--emp-gradient-soft); }
.tech { border: 1px solid var(--emp-border); border-radius: 14px; }
</style>
