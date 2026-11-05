// Formatting helpers shared by all pages
export function fmtDate (v, opts = { day: '2-digit', month: 'short', year: 'numeric' }) {
  if (!v) return '—'
  const d = new Date(v.length === 10 ? v + 'T00:00:00' : v)
  return isNaN(d) ? v : d.toLocaleDateString('en-IN', opts)
}
export function fmtDay (v) { return fmtDate(v, { weekday: 'short', day: '2-digit', month: 'short' }) }
export function fmtDateTime (v) {
  if (!v) return '—'
  const d = new Date(v)
  return d.toLocaleString('en-IN', { day: '2-digit', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit' })
}
export function fmtTime (t) {
  if (!t) return '—'
  const [h, m] = t.split(':').map(Number)
  const ap = h >= 12 ? 'PM' : 'AM'
  return `${((h + 11) % 12) + 1}:${String(m).padStart(2, '0')} ${ap}`
}
export function timeAgo (v) {
  if (!v) return ''
  const s = Math.floor((Date.now() - new Date(v).getTime()) / 1000)
  if (s < 60) return 'just now'
  if (s < 3600) return `${Math.floor(s / 60)} min ago`
  if (s < 86400) return `${Math.floor(s / 3600)} h ago`
  if (s < 604800) return `${Math.floor(s / 86400)} d ago`
  return fmtDate(v)
}
export function daysUntil (v) {
  if (!v) return null
  const today = new Date(); today.setHours(0, 0, 0, 0)
  return Math.round((new Date(v + 'T00:00:00') - today) / 86400000)
}
export function initials (name = '') {
  return name.replace(/^(Dr\.|Prof\.|Mr\.|Ms\.|Mrs\.)\s*/i, '').split(' ').filter(Boolean).slice(0, 2).map(p => p[0]).join('').toUpperCase()
}
export function todayISO () {
  const d = new Date(); d.setMinutes(d.getMinutes() - d.getTimezoneOffset())
  return d.toISOString().slice(0, 10)
}

const STATUS = {
  draft: ['Draft', 'secondary', 'pencil-square'],
  slot_creation: ['Slot Creation', 'info', 'calendar-plus'],
  booking_open: ['Booking Open', 'success', 'door-open'],
  closed: ['Closed', 'warning', 'lock'],
  completed: ['Completed', 'primary', 'check2-circle'],
  available: ['Available', 'success', 'circle'],
  full: ['Full', 'danger', 'people-fill'],
  cancelled: ['Cancelled', 'secondary', 'x-circle'],
  booked: ['Booked', 'primary', 'bookmark-check'],
  absent: ['Absent', 'danger', 'person-x'],
  submitted: ['Evaluated', 'success', 'clipboard-check'],
  pending: ['Pending', 'warning', 'hourglass-split'],
  open: ['Open', 'warning', 'envelope-open'],
  replied: ['Replied', 'info', 'reply'],
  done: ['Ready', 'success', 'check-circle'],
  failed: ['Failed', 'danger', 'exclamation-circle'],
  active: ['Active', 'success', 'check-circle'],
  inactive: ['Inactive', 'secondary', 'pause-circle'],
  blocked: ['Blocked', 'danger', 'slash-circle']
}
export function statusMeta (s) {
  const m = STATUS[s] || [s ? s.replace(/_/g, ' ') : '—', 'secondary', 'dot']
  return { label: m[0], color: m[1], icon: m[2] }
}
export const EXAM_TYPES = ['Viva', 'Practical', 'Project Demo', 'Assessment']
export const TYPE_META = {
  Viva: { icon: 'mic', color: '#4f46e5' },
  Practical: { icon: 'terminal', color: '#0891b2' },
  'Project Demo': { icon: 'rocket-takeoff', color: '#7c3aed' },
  Assessment: { icon: 'journal-check', color: '#059669' }
}
export function gradeColor (g) {
  return { S: '#7c3aed', A: '#4f46e5', B: '#0891b2', C: '#059669', D: '#d97706', E: '#ea580c', U: '#dc2626' }[g] || '#64748b'
}
export function downloadBlob (blob, filename) {
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url; a.download = filename; document.body.appendChild(a); a.click(); a.remove()
  setTimeout(() => URL.revokeObjectURL(url), 1000)
}
