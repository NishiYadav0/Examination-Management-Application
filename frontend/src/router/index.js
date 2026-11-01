import { createRouter, createWebHistory } from 'vue-router'
import store from '@/store'

const P = (c) => () => import(`@/views/public/${c}.vue`)
const A = (c) => () => import(`@/views/admin/${c}.vue`)
const E = (c) => () => import(`@/views/examiner/${c}.vue`)
const S = (c) => () => import(`@/views/student/${c}.vue`)
const SH = (c) => () => import(`@/views/shared/${c}.vue`)

const dash = (role, extra = {}) => ({ layout: 'dashboard', requiresAuth: true, role, ...extra })

const routes = [
  // ---------- public ----------
  { path: '/', name: 'home', component: P('HomeView'), meta: { title: 'Home' } },
  { path: '/about', name: 'about', component: P('AboutView'), meta: { title: 'About' } },
  { path: '/contact', name: 'contact', component: P('ContactView'), meta: { title: 'Contact' } },
  { path: '/login', name: 'login', component: () => import('@/views/auth/LoginView.vue'), meta: { title: 'Login', guestOnly: true, layout: 'blank' } },
  { path: '/register', name: 'register', component: () => import('@/views/auth/RegisterView.vue'), meta: { title: 'Register', guestOnly: true, layout: 'blank' } },

  // ---------- shared (all roles) ----------
  { path: '/profile', component: SH('ProfileView'), meta: dash(null, { title: 'My Profile' }) },
  { path: '/notifications', component: SH('NotificationsView'), meta: dash(null, { title: 'Notifications' }) },
  { path: '/support', component: SH('SupportView'), meta: dash(null, { title: 'Help & Support' }) },
  { path: '/export', component: SH('ExportView'), meta: dash(null, { title: 'Export my data' }) },

  // ---------- admin ----------
  { path: '/admin', component: A('AdminDashboard'), meta: dash('admin', { title: 'Admin Dashboard' }) },
  { path: '/admin/statistics', component: A('AdminStatistics'), meta: dash('admin', { title: 'Statistics' }) },
  { path: '/admin/courses', component: A('AdminCourses'), meta: dash('admin', { title: 'Courses' }) },
  { path: '/admin/exams', component: A('AdminExams'), meta: dash('admin', { title: 'Examinations' }) },
  { path: '/admin/exams/:id', component: A('AdminExamDetail'), meta: dash('admin', { title: 'Examination' }), props: true },
  { path: '/admin/slots', component: A('AdminSlots'), meta: dash('admin', { title: 'Examiner Slots' }) },
  { path: '/admin/bookings', component: A('AdminBookings'), meta: dash('admin', { title: 'Bookings' }) },
  { path: '/admin/examiners', component: A('AdminExaminers'), meta: dash('admin', { title: 'Examiners' }) },
  { path: '/admin/students', component: A('AdminStudents'), meta: dash('admin', { title: 'Students' }) },
  { path: '/admin/users/:id', component: A('AdminUserDetail'), meta: dash('admin', { title: 'User Profile' }), props: true },
  { path: '/admin/search', component: A('AdminSearch'), meta: dash('admin', { title: 'Search' }) },
  { path: '/admin/support', component: A('AdminSupport'), meta: dash('admin', { title: 'Support Tickets' }) },
  { path: '/admin/reports', component: A('AdminReports'), meta: dash('admin', { title: 'Reports & Jobs' }) },

  // ---------- examiner ----------
  { path: '/examiner', component: E('ExaminerDashboard'), meta: dash('examiner', { title: 'Examiner Dashboard' }) },
  { path: '/examiner/statistics', component: E('ExaminerStatistics'), meta: dash('examiner', { title: 'My Statistics' }) },
  { path: '/examiner/exams', component: E('ExaminerExams'), meta: dash('examiner', { title: 'Assigned Exams' }) },
  { path: '/examiner/exams/:id', component: E('ExaminerExamDetail'), meta: dash('examiner', { title: 'Examination' }), props: true },
  { path: '/examiner/slots', component: E('ExaminerSlots'), meta: dash('examiner', { title: 'My Slots' }) },
  { path: '/examiner/students', component: E('ExaminerStudents'), meta: dash('examiner', { title: 'Booked Students' }) },
  { path: '/examiner/evaluate/:id', component: E('ExaminerEvaluate'), meta: dash('examiner', { title: 'Evaluate' }), props: true },
  { path: '/examiner/evaluations', component: E('ExaminerEvaluations'), meta: dash('examiner', { title: 'Evaluations' }) },

  // ---------- student ----------
  { path: '/student', component: S('StudentDashboard'), meta: dash('student', { title: 'Student Dashboard' }) },
  { path: '/student/statistics', component: S('StudentStatistics'), meta: dash('student', { title: 'My Progress' }) },
  { path: '/student/exams', component: S('StudentExams'), meta: dash('student', { title: 'Browse Exams' }) },
  { path: '/student/exams/:id', component: S('StudentExamDetail'), meta: dash('student', { title: 'Examination' }), props: true },
  { path: '/student/bookings', component: S('StudentBookings'), meta: dash('student', { title: 'My Bookings' }) },
  { path: '/student/results', component: S('StudentResults'), meta: dash('student', { title: 'Results' }) },
  { path: '/student/results/:id', component: S('StudentScorecard'), meta: dash('student', { title: 'Scorecard' }), props: true },
  { path: '/student/export', redirect: '/export' },

  { path: '/:pathMatch(.*)*', name: 'notfound', component: P('NotFound'), meta: { title: 'Not found' } }
]

const router = createRouter({
  history: createWebHistory(process.env.BASE_URL),
  routes,
  scrollBehavior: (to, from, saved) => saved || (to.hash ? { el: to.hash, behavior: 'smooth' } : { top: 0 })
})

// Role based navigation guard
router.beforeEach((to) => {
  const loggedIn = store.getters['auth/isLoggedIn']
  const role = store.getters['auth/role']
  if (to.meta.requiresAuth && !loggedIn) return { path: '/login', query: { redirect: to.fullPath } }
  if (to.meta.guestOnly && loggedIn) return store.getters['auth/home']
  if (to.meta.role && to.meta.role !== role) {
    store.dispatch('ui/toast', { message: 'You do not have access to that page', type: 'warning' })
    return store.getters['auth/home']
  }
  return true
})
router.afterEach((to) => {
  document.title = `${to.meta.title || 'EMP'} · Examination Management Portal`
  store.commit('ui/setSidebar', false)
})

export default router
