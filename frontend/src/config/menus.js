// Sidebar navigation per role
export default {
  admin: [
    { section: 'Overview' },
    { to: '/admin', icon: 'grid-1x2', label: 'Dashboard', exact: true },
    { to: '/admin/statistics', icon: 'bar-chart-line', label: 'Statistics' },
    { section: 'Academics' },
    { to: '/admin/courses', icon: 'journal-bookmark', label: 'Courses' },
    { to: '/admin/exams', icon: 'clipboard2-check', label: 'Examinations' },
    { to: '/admin/slots', icon: 'calendar3-week', label: 'Examiner Slots' },
    { to: '/admin/bookings', icon: 'bookmark-star', label: 'Bookings' },
    { section: 'People' },
    { to: '/admin/examiners', icon: 'person-badge', label: 'Examiners' },
    { to: '/admin/students', icon: 'mortarboard', label: 'Students' },
    { section: 'System' },
    { to: '/admin/search', icon: 'search', label: 'Global Search' },
    { to: '/admin/support', icon: 'chat-square-text', label: 'Support Tickets', badge: 'tickets' },
    { to: '/admin/reports', icon: 'file-earmark-bar-graph', label: 'Reports & Jobs' },
    { to: '/export', icon: 'cloud-arrow-down', label: 'Export My Data' }
  ],
  examiner: [
    { section: 'Overview' },
    { to: '/examiner', icon: 'grid-1x2', label: 'Dashboard', exact: true },
    { to: '/examiner/statistics', icon: 'bar-chart-line', label: 'My Statistics' },
    { section: 'Examinations' },
    { to: '/examiner/exams', icon: 'clipboard2-check', label: 'Assigned Exams' },
    { to: '/examiner/slots', icon: 'calendar3-week', label: 'My Slots' },
    { to: '/examiner/students', icon: 'people', label: 'Booked Students' },
    { to: '/examiner/evaluations', icon: 'award', label: 'Evaluations' },
    { section: 'Account' },
    { to: '/export', icon: 'cloud-arrow-down', label: 'Export My Data' },
    { to: '/support', icon: 'life-preserver', label: 'Help & Support' }
  ],
  student: [
    { section: 'Overview' },
    { to: '/student', icon: 'grid-1x2', label: 'Dashboard', exact: true },
    { to: '/student/statistics', icon: 'graph-up-arrow', label: 'My Progress' },
    { section: 'Examinations' },
    { to: '/student/exams', icon: 'search', label: 'Browse Exams' },
    { to: '/student/bookings', icon: 'calendar-check', label: 'My Bookings' },
    { to: '/student/results', icon: 'trophy', label: 'Results' },
    { section: 'Account' },
    { to: '/export', icon: 'cloud-arrow-down', label: 'Export My Data' },
    { to: '/support', icon: 'life-preserver', label: 'Help & Support' }
  ]
}
