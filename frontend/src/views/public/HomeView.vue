<template>
  <div class="home">
    <!-- ================= HERO ================= -->
    <section class="hero">
      <div class="blob b1"></div><div class="blob b2"></div><div class="grid-bg"></div>
      <div class="container position-relative">
        <div class="row align-items-center g-5">
          <div class="col-lg-6 fade-in">
            <span class="hero-pill"><span class="dot"></span> Examination season, simplified</span>
            <h1 class="hero-title mt-3">
              Vivas, practicals & project demos — <span class="gradient-text">scheduled, booked and graded</span> in one place.
            </h1>
            <p class="hero-sub">EMP replaces spreadsheets and e-mail threads with a single portal where admins plan examinations,
              examiners publish slots and grade with rubrics, and students book, attend and track results.</p>
            <div class="d-flex flex-wrap gap-3 mt-4">
              <router-link v-if="!loggedIn" to="/register" class="btn btn-gradient btn-lg px-4">
                Create student account <i class="bi bi-arrow-right ms-1"></i>
              </router-link>
              <router-link v-else :to="$store.getters['auth/home']" class="btn btn-gradient btn-lg px-4">
                Go to my dashboard <i class="bi bi-arrow-right ms-1"></i>
              </router-link>
              <a href="#how" class="btn btn-lg btn-outline-secondary px-4" @click.prevent="scroll('how')"><i class="bi bi-play-circle me-1"></i> How it works</a>
            </div>
            <div class="d-flex flex-wrap gap-4 mt-4 small text-muted">
              <span><i class="bi bi-shield-check text-success me-1"></i>Role-based access</span>
              <span><i class="bi bi-lightning-charge text-warning me-1"></i>Redis-fast</span>
              <span><i class="bi bi-envelope-check text-primary me-1"></i>Automatic reminders</span>
            </div>
          </div>
          <div class="col-lg-6">
            <div class="mock position-relative">
              <div class="card-emp mock-main p-4">
                <div class="d-flex justify-content-between align-items-center mb-3">
                  <div>
                    <div class="small-caps text-muted">Next examination</div>
                    <div class="fw-bold fs-5">MAD-II Project Viva</div>
                  </div>
                  <span class="badge-soft bs-success"><i class="bi bi-door-open me-1"></i>Booking open</span>
                </div>
                <div class="row g-2 mb-3">
                  <div class="col-4" v-for="s in mockSlots" :key="s.t">
                    <div class="mock-slot" :class="{ picked: s.picked, full: s.full }">
                      <div class="fw-bold">{{ s.t }}</div><small>{{ s.full ? 'Full' : s.seats + ' seats' }}</small>
                    </div>
                  </div>
                </div>
                <div class="small-caps text-muted mb-2">Evaluation rubric</div>
                <div v-for="r in mockRubric" :key="r.n" class="mb-2">
                  <div class="d-flex justify-content-between small"><span>{{ r.n }}</span><b>{{ r.v }}/{{ r.m }}</b></div>
                  <div class="progress" style="height:7px"><div class="progress-bar" :style="{ width: (r.v / r.m * 100) + '%', background: r.c }"></div></div>
                </div>
              </div>
              <div class="float-card fc1 card-emp"><span class="icon-box bg-success bg-opacity-10 text-success" style="width:38px;height:38px"><i class="bi bi-check2-circle"></i></span>
                <div><div class="fw-bold small">Slot booked</div><small class="text-muted">Fri · 10:00 AM</small></div></div>
              <div class="float-card fc2 card-emp"><span class="icon-box bg-primary bg-opacity-10 text-primary" style="width:38px;height:38px"><i class="bi bi-trophy"></i></span>
                <div><div class="fw-bold small">Grade A · 86%</div><small class="text-muted">Result published</small></div></div>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- ================= STATS ================= -->
    <section class="container stats-strip">
      <div class="card-emp p-3 p-md-4">
        <div class="row text-center g-3">
          <div class="col-6 col-md-2" v-for="s in statItems" :key="s.label">
            <div class="fs-2 fw-800 gradient-text">{{ s.value }}</div>
            <div class="small text-muted fw-semibold">{{ s.label }}</div>
          </div>
        </div>
      </div>
    </section>

    <!-- ================= FEATURES ================= -->
    <section id="features" class="section container">
      <div class="text-center mb-5">
        <span class="small-caps text-primary">Features</span>
        <h2 class="display-6 fw-bold mt-2">Everything an examination cell needs</h2>
        <p class="text-muted mx-auto" style="max-width:640px">From timelines and rubrics to slot booking, evaluation and published scorecards —
          every step is tracked, validated and auditable.</p>
      </div>
      <div class="row g-4">
        <div class="col-sm-6 col-lg-3" v-for="f in features" :key="f.t">
          <div class="card-emp h-100 p-4 hover-lift feature">
            <span class="icon-box mb-3" :style="{ background: f.c + '1a', color: f.c }"><i :class="'bi bi-' + f.i"></i></span>
            <h6 class="fw-bold">{{ f.t }}</h6>
            <p class="small text-muted mb-0">{{ f.d }}</p>
          </div>
        </div>
      </div>
    </section>

    <!-- ================= HOW IT WORKS ================= -->
    <section id="how" class="section how-bg">
      <div class="container">
        <div class="text-center mb-4">
          <span class="small-caps text-primary">How it works</span>
          <h2 class="display-6 fw-bold mt-2">Built around three roles</h2>
        </div>
        <ul class="nav nav-pills nav-pills-emp justify-content-center mb-4 gap-2">
          <li class="nav-item" v-for="r in roles" :key="r.key">
            <button class="nav-link" :class="{ active: role === r.key }" @click="role = r.key"><i :class="'bi bi-' + r.icon + ' me-1'"></i>{{ r.label }}</button>
          </li>
        </ul>
        <div class="row g-4 justify-content-center">
          <div class="col-md-6 col-lg-3" v-for="(s, i) in currentRole.steps" :key="role + i">
            <div class="card-emp h-100 p-4 fade-in step">
              <span class="step-no">{{ i + 1 }}</span>
              <i :class="'bi bi-' + s.i + ' fs-3 text-primary'"></i>
              <h6 class="fw-bold mt-3">{{ s.t }}</h6>
              <p class="small text-muted mb-0">{{ s.d }}</p>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- ================= LIFECYCLE ================= -->
    <section class="section container">
      <div class="row g-5 align-items-center">
        <div class="col-lg-5">
          <span class="small-caps text-primary">Examination lifecycle</span>
          <h2 class="fw-bold mt-2">Every exam follows a clear, enforced timeline</h2>
          <p class="text-muted">Admins control each window. The portal blocks slot creation, booking or evaluation outside the allowed
            period — so nobody books twice, no slot is overbooked and every mark is traceable.</p>
          <ul class="list-unstyled small">
            <li class="mb-2"><i class="bi bi-check2-circle text-success me-2"></i>One booking per student per examination</li>
            <li class="mb-2"><i class="bi bi-check2-circle text-success me-2"></i>Slots auto-marked <b>Full</b> at capacity</li>
            <li class="mb-2"><i class="bi bi-check2-circle text-success me-2"></i>Examiners grade only their own students</li>
            <li><i class="bi bi-check2-circle text-success me-2"></i>Results visible only after admin publishes</li>
          </ul>
        </div>
        <div class="col-lg-7">
          <div class="lifecycle">
            <div class="lc-step" v-for="(s, i) in lifecycle" :key="s.t">
              <span class="lc-icon" :style="{ background: s.c }"><i :class="'bi bi-' + s.i"></i></span>
              <div><div class="fw-bold">{{ i + 1 }}. {{ s.t }}</div><small class="text-muted">{{ s.d }}</small></div>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- ================= EXAM TYPES ================= -->
    <section class="section container pt-0">
      <div class="text-center mb-5">
        <span class="small-caps text-primary">Examination types</span>
        <h2 class="display-6 fw-bold mt-2">Designed for live evaluations</h2>
      </div>
      <div class="row g-4">
        <div class="col-sm-6 col-lg-3" v-for="t in types" :key="t.n">
          <div class="type-card h-100 hover-lift" :style="{ '--c': t.c }">
            <i :class="'bi bi-' + t.i"></i>
            <h5 class="fw-bold mt-3">{{ t.n }}</h5>
            <p class="small mb-0 opacity-75">{{ t.d }}</p>
          </div>
        </div>
      </div>
    </section>

    <!-- ================= OPEN EXAMS ================= -->
    <section class="section container pt-0" v-if="upcoming.length">
      <div class="d-flex justify-content-between align-items-end mb-4 flex-wrap gap-2">
        <div>
          <span class="small-caps text-primary">Live now</span>
          <h2 class="fw-bold mt-2 mb-0">Examinations open on the portal</h2>
        </div>
        <router-link :to="loggedIn ? '/student/exams' : '/register'" class="btn btn-soft">View all <i class="bi bi-arrow-right"></i></router-link>
      </div>
      <div class="row g-4">
        <div class="col-md-6 col-lg-4" v-for="e in upcoming" :key="e.id">
          <div class="card-emp p-4 h-100 hover-lift">
            <div class="d-flex justify-content-between mb-2">
              <span class="badge-soft bs-primary">{{ e.course_code }}</span>
              <StatusBadge :status="e.status" />
            </div>
            <h6 class="fw-bold mb-1">{{ e.name }}</h6>
            <p class="small text-muted mb-3">{{ e.course_name }}</p>
            <div class="d-flex gap-3 small text-muted">
              <span><i class="bi bi-tag me-1"></i>{{ e.exam_type }}</span>
              <span><i class="bi bi-clock me-1"></i>{{ e.duration_minutes }} min</span>
              <span><i class="bi bi-calendar-event me-1"></i>till {{ $f.fmtDate(e.booking_end) }}</span>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- ================= FAQ ================= -->
    <section class="section container pt-0">
      <div class="row g-5">
        <div class="col-lg-4">
          <span class="small-caps text-primary">FAQ</span>
          <h2 class="fw-bold mt-2">Questions, answered</h2>
          <p class="text-muted">Can't find what you're looking for? <router-link to="/contact">Contact our support team</router-link>.</p>
        </div>
        <div class="col-lg-8">
          <div class="accordion" id="faq">
            <div class="accordion-item card-emp mb-3 overflow-hidden" v-for="(q, i) in faqs" :key="i">
              <h2 class="accordion-header">
                <button class="accordion-button fw-semibold" :class="{ collapsed: i !== 0 }" type="button" data-bs-toggle="collapse" :data-bs-target="'#fq' + i">{{ q.q }}</button>
              </h2>
              <div :id="'fq' + i" class="accordion-collapse collapse" :class="{ show: i === 0 }" data-bs-parent="#faq">
                <div class="accordion-body text-muted">{{ q.a }}</div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- ================= CTA ================= -->
    <section class="container">
      <div class="cta p-5 text-center text-white">
        <h2 class="fw-bold">Ready for your next examination?</h2>
        <p class="opacity-75 mb-4">Register as a student in less than a minute and book your slot as soon as booking opens.</p>
        <div class="d-flex justify-content-center gap-3 flex-wrap">
          <router-link to="/register" class="btn btn-light btn-lg px-4 fw-bold">Register now</router-link>
          <router-link to="/login" class="btn btn-outline-light btn-lg px-4">I already have an account</router-link>
        </div>
      </div>
    </section>
  </div>
</template>

<script>
import api from '@/services/api'
import StatusBadge from '@/components/common/StatusBadge.vue'

export default {
  name: 'HomeView',
  components: { StatusBadge },
  data: () => ({
    stats: {},
    upcoming: [],
    role: 'student',
    mockSlots: [{ t: '09:30', seats: 2 }, { t: '10:00', seats: 1, picked: true }, { t: '10:30', full: true }],
    mockRubric: [{ n: 'Concept clarity', v: 26, m: 30, c: '#4f46e5' }, { n: 'Code walkthrough', v: 33, m: 40, c: '#06b6d4' }, { n: 'Q&A', v: 27, m: 30, c: '#10b981' }],
    features: [
      { i: 'calendar2-range', t: 'Timeline control', d: 'Configure slot-creation, booking and examination windows; open or close each with one click.', c: '#4f46e5' },
      { i: 'grid-3x3-gap', t: 'Rubric builder', d: 'Define weighted criteria per examination; totals are computed automatically on the server.', c: '#7c3aed' },
      { i: 'calendar-plus', t: 'Examiner slots', d: 'Examiners publish online or offline slots, even auto-split a whole morning into back-to-back sessions.', c: '#06b6d4' },
      { i: 'bookmark-check', t: 'Smart booking', d: 'One booking per exam, clash detection, live seat counts and automatic Full status.', c: '#10b981' },
      { i: 'arrow-left-right', t: 'Reschedule & reassign', d: 'Admins move students between slots or change the examiner in exceptional situations.', c: '#f59e0b' },
      { i: 'award', t: 'Scorecards', d: 'Published results with criterion-wise marks, grade, feedback and a printable scorecard.', c: '#ec4899' },
      { i: 'bell', t: 'Reminders & alerts', d: 'Daily e-mail reminders, booking confirmations, result mails and in-app notifications.', c: '#ef4444' },
      { i: 'bar-chart-line', t: 'Analytics', d: 'Dashboards for every role, monthly HTML reports and CSV export of examination history.', c: '#14b8a6' }
    ],
    roles: [
      { key: 'admin', label: 'Admin', icon: 'shield-lock', steps: [
        { i: 'journal-plus', t: 'Create courses & exams', d: 'Set type, duration, marks and the complete timeline.' },
        { i: 'list-check', t: 'Build rubric & assign', d: 'Weighted criteria totalling 100% and the examiners who will conduct it.' },
        { i: 'toggles', t: 'Open windows', d: 'Open slot creation, then booking — close them when done.' },
        { i: 'megaphone', t: 'Publish results', d: 'Review evaluations and publish; students are notified instantly.' }] },
      { key: 'examiner', label: 'Examiner', icon: 'person-badge', steps: [
        { i: 'box-arrow-in-right', t: 'Log in', d: 'Accounts are created by the admin – credentials arrive by e-mail.' },
        { i: 'calendar-plus', t: 'Publish slots', d: 'Add slots with capacity and meeting link during the creation window.' },
        { i: 'people', t: 'Meet students', d: 'See who booked each slot, mark attendance and join the session.' },
        { i: 'clipboard-check', t: 'Grade with rubric', d: 'Enter criterion marks and remarks; the total is calculated for you.' }] },
      { key: 'student', label: 'Student', icon: 'mortarboard', steps: [
        { i: 'person-plus', t: 'Register', d: 'Create your account with your roll number in seconds.' },
        { i: 'search', t: 'Find examinations', d: 'Search and filter open examinations by course and type.' },
        { i: 'calendar-check', t: 'Book a slot', d: 'Choose a convenient slot; cancel before the deadline if plans change.' },
        { i: 'trophy', t: 'Get results', d: 'View marks, feedback and download your scorecard once published.' }] }
    ],
    lifecycle: [
      { i: 'pencil-square', t: 'Draft', d: 'Admin sets up the exam, timeline and rubric', c: '#64748b' },
      { i: 'calendar-plus', t: 'Slot creation', d: 'Examiners publish their available slots', c: '#06b6d4' },
      { i: 'door-open', t: 'Booking open', d: 'Students book one slot each', c: '#10b981' },
      { i: 'lock', t: 'Closed', d: 'Examinations are conducted and evaluated', c: '#f59e0b' },
      { i: 'check2-circle', t: 'Completed', d: 'Results published with feedback', c: '#4f46e5' }
    ],
    types: [
      { n: 'Viva', i: 'mic', d: 'Oral examinations with concept & Q&A based rubrics.', c: '#4f46e5' },
      { n: 'Practical', i: 'terminal', d: 'Live lab or programming evaluation, graded on correctness.', c: '#0891b2' },
      { n: 'Project Demo', i: 'rocket-takeoff', d: 'Students run and present their project live with a submission link.', c: '#7c3aed' },
      { n: 'Assessment', i: 'journal-check', d: 'General scheduled evaluation sessions of any format.', c: '#059669' }
    ],
    faqs: [
      { q: 'Who can register on the portal?', a: 'Only students can self-register. Examiner accounts are created by the admin, and the single admin account is created automatically when the system is installed.' },
      { q: 'Can I book more than one slot for the same examination?', a: 'No. Each student can hold only one active booking per examination. You can cancel before the booking deadline and book another slot.' },
      { q: 'What happens if a slot fills up?', a: 'Slots are marked Full automatically when all seats are taken and re-open if someone cancels.' },
      { q: 'When will I see my marks?', a: 'After your examiner submits the evaluation and the admin publishes results. You will get an e-mail and an in-app notification.' },
      { q: 'Can I install EMP like an app?', a: 'Yes! Use the “Install app” button in the dashboard (or your browser menu → Install / Add to Home screen).' }
    ]
  }),
  computed: {
    loggedIn () { return this.$store.getters['auth/isLoggedIn'] },
    currentRole () { return this.roles.find(r => r.key === this.role) },
    statItems () {
      const s = this.stats
      return [
        { label: 'Courses', value: s.courses ?? '—' }, { label: 'Examinations', value: s.examinations ?? '—' },
        { label: 'Students', value: s.students ?? '—' }, { label: 'Examiners', value: s.examiners ?? '—' },
        { label: 'Bookings', value: s.bookings ?? '—' }, { label: 'Evaluations', value: s.evaluations ?? '—' }
      ]
    }
  },
  async mounted () {
    try {
      const [a, b] = await Promise.all([api.get('/public/stats'), api.get('/public/upcoming')])
      this.stats = a.data.data
      this.upcoming = b.data.data
    } catch (e) { /* API down – landing page still renders */ }
    if (this.$route.hash) setTimeout(() => this.scroll(this.$route.hash.slice(1)), 150)
  },
  methods: {
    scroll (id) { document.getElementById(id)?.scrollIntoView({ behavior: 'smooth' }) }
  }
}
</script>

<style scoped>
.hero { position: relative; overflow: hidden; padding: 5rem 0 7rem; }
.blob { position: absolute; border-radius: 50%; filter: blur(80px); opacity: .45; }
.b1 { width: 480px; height: 480px; background: #a5b4fc; top: -160px; right: -80px; }
.b2 { width: 380px; height: 380px; background: #f0abfc; bottom: -180px; left: -120px; opacity: .35; }
[data-bs-theme="dark"] .blob { opacity: .18; }
.grid-bg { position: absolute; inset: 0; background-image: linear-gradient(rgba(79,70,229,.06) 1px, transparent 1px),
  linear-gradient(90deg, rgba(79,70,229,.06) 1px, transparent 1px); background-size: 42px 42px;
  mask-image: radial-gradient(circle at 50% 30%, #000 20%, transparent 70%); }
.hero-pill { display: inline-flex; align-items: center; gap: .5rem; background: rgba(79,70,229,.08); color: var(--emp-primary);
  padding: .4rem .9rem; border-radius: 999px; font-weight: 600; font-size: .85rem; }
.hero-pill .dot { width: 8px; height: 8px; border-radius: 50%; background: #10b981; box-shadow: 0 0 0 4px rgba(16,185,129,.2); }
.hero-title { font-size: clamp(2rem, 4.2vw, 3.3rem); font-weight: 800; line-height: 1.12; letter-spacing: -.035em; }
.hero-sub { font-size: 1.1rem; color: var(--emp-muted); margin-top: 1.25rem; max-width: 560px; }
.mock { padding: 2rem 1rem; }
.mock-main { transform: rotate(-1.5deg); box-shadow: var(--emp-shadow-lg); }
.mock-slot { border: 1.5px solid var(--emp-border); border-radius: 12px; padding: .6rem; text-align: center; font-size: .85rem; }
.mock-slot small { color: var(--emp-muted); }
.mock-slot.picked { border-color: var(--emp-primary); background: rgba(79,70,229,.08); color: var(--emp-primary); }
.mock-slot.full { opacity: .5; text-decoration: line-through; }
.float-card { position: absolute; display: flex; gap: .7rem; align-items: center; padding: .75rem 1rem; animation: float 5s ease-in-out infinite; }
.fc1 { top: 0; right: 0; }
.fc2 { bottom: 0; left: -10px; animation-delay: 1.5s; }
@keyframes float { 0%, 100% { transform: translateY(0); } 50% { transform: translateY(-10px); } }
.stats-strip { margin-top: -3.5rem; position: relative; z-index: 2; }
.section { padding: 5rem 0; }
.how-bg { background: var(--emp-gradient-soft); }
.step { position: relative; }
.step-no { position: absolute; top: 1rem; right: 1.2rem; font-size: 2.2rem; font-weight: 800; color: rgba(79,70,229,.12); }
.lifecycle { display: grid; gap: 1rem; }
.lc-step { display: flex; gap: 1rem; align-items: center; background: var(--emp-card-bg); border: 1px solid var(--emp-border);
  padding: 1rem 1.25rem; border-radius: 16px; box-shadow: var(--emp-shadow); }
.lc-step:nth-child(even) { margin-left: 2rem; }
.lc-icon { width: 44px; height: 44px; border-radius: 12px; color: #fff; display: inline-flex; align-items: center; justify-content: center; font-size: 1.2rem; flex-shrink: 0; }
.type-card { border-radius: 20px; padding: 1.75rem; color: #fff; background: linear-gradient(145deg, var(--c), #0f172a 160%); }
.type-card i { font-size: 2rem; }
.cta { border-radius: 28px; background: var(--emp-gradient); box-shadow: var(--emp-shadow-lg); position: relative; overflow: hidden; }
.accordion-item { border: 1px solid var(--emp-border) !important; }
@media (max-width: 767px) { .lc-step:nth-child(even) { margin-left: 0; } .hero { padding: 3rem 0 6rem; } .section { padding: 3.5rem 0; } }
</style>
