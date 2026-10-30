# 🎓 EMP – Examination Management Portal (V2)

Modern Application Development II · IIT Madras BS · Sep 2026 term

A multi-role web application where the **Admin** plans examinations (vivas, practicals, project demos, assessments),
**Examiners** publish slots and grade students with rubrics, and **Students** book slots, attend and view results.

👉 **How to run:** see [`RUN_GUIDE.md`](RUN_GUIDE.md) · **Design plan:** [`PLAN.md`](PLAN.md) · **Status:** [`PROGRESS.md`](PROGRESS.md)

## Tech stack
| Layer | Used |
|---|---|
| Backend API | Flask 3 (Blueprints), Flask-Security-Too (token auth + RBAC), Flask-SQLAlchemy |
| Database | SQLite – created programmatically with `db.create_all()` |
| Cache | Redis via Flask-Caching (TTL + version-key invalidation, `X-Cache` header) |
| Batch jobs | Celery + Redis (worker + beat) · e-mails through SMTP → MailHog |
| Frontend | Vue 3 (Vue CLI), Vue Router, Vuex, Bootstrap 5 + Bootstrap Icons, Chart.js, Axios |
| Templates | Jinja2 only for e-mail / report HTML (not for UI) |

## Features
**Admin** – dashboard (courses, exams, students, examiners, slots, bookings + charts) · CRUD courses & exams ·
timeline configuration · rubric builder (weightage must total 100 %) · assign examiners · open/close slot creation
and booking · view all slots (reschedule, change examiner, cancel) · view all bookings (reschedule to another
slot/examiner, cancel) · add examiners (credentials e-mailed) · view/edit/block/unblock/reset password of any
student or examiner with per-user statistics & activity log · global search · publish/withdraw results ·
statistics page · support tickets · monthly reports & manual job triggers · activity log.

**Examiner** – dashboard (assigned exams, slots, booked students, pending evaluations) · create slots only in the
creation window (auto-split into back-to-back slots, clash detection) · edit/remove before booking begins ·
booked students & attendance · rubric evaluation with live weighted total, draft/submit · mark slot / exam completed ·
statistics.

**Student** – register/login/profile · dashboard (available exams & seats, upcoming, booked, results, next-exam
countdown) · search & filter exams · book (one per exam, no overbooking, time-clash check, optional submission
link) · cancel before deadline · booking history · results + printable scorecard · CSV export (Celery) · progress charts.

**Results & notifications** – per examination the admin chooses the *result release* mode:
*After admin publishes* (default) or *Instantly after evaluation*. When an examiner submits an evaluation the student
always gets an in-app notification **and an e-mail** – with the criterion-wise marks if results are released instantly,
otherwise a "your exam was evaluated" mail followed by the result mail when the admin publishes (never duplicated).
Examiners are e-mailed (and notified in-app) when the admin assigns or removes them from an examination, or moves a slot to them.

**Export my data (all roles)** – one page (`/export`) where every user downloads *their own* data as CSV via a Celery
job: profile & statistics, activity log, notifications, support requests, plus role data (student: examination history ·
examiner: assigned exams, slots, evaluations · admin: platform statistics, examinations overview, audit log) or
**everything in one file**. Finished exports are notified in-app, e-mailed as attachment and kept in an export history.

**Everyone** – modern responsive UI (desktop + mobile), dark mode, in-app notifications, contact/support page for
guests and logged-in users, installable PWA ("Add to desktop").

**Background jobs** – daily examination reminder (e-mail), monthly HTML examination report to admin,
user-triggered CSV export with alert, booking/cancellation/result/credential e-mails.

## Folder structure
```
project_2xfXXXXXX/
├── backend/
│   ├── app.py              # app factory, Celery, DB bootstrap
│   ├── config.py  celery_config.py  requirements.txt
│   ├── models/models.py    # all tables
│   ├── routes/             # auth, public, common, admin, examiner, student
│   ├── tasks/jobs.py       # Celery tasks
│   ├── utils/              # cache, mailer, rules, helpers, seed
│   └── templates/emails/   # Jinja2 e-mail & report templates
└── frontend/
    ├── public/             # index.html, manifest.json, sw.js, icons
    └── src/
        ├── components/     # layout, common, admin, examiner, charts
        ├── views/          # public, auth, shared, admin, examiner, student
        ├── router/  store/  services/  utils/  config/  assets/
        └── App.vue  main.js
```

## Database tables
`user`, `role`, `roles_users`, `student_profile`, `examiner_profile`, `course`, `examination`, `exam_examiner`,
`rubric`, `slot`, `booking`, `evaluation`, `evaluation_score`, `support_ticket`, `notification`, `activity_log`,
`export_job`, `monthly_report`.

## API endpoints
All endpoints return JSON. Protected ones need header `Authentication-Token: <token>` (returned by login/register).

| Method | Endpoint |
|---|---|
| `GET` | `/api/admin/activity` |
| `GET` | `/api/admin/bookings` |
| `POST` | `/api/admin/bookings/<int:bid>/cancel` |
| `POST` | `/api/admin/bookings/<int:bid>/reschedule` |
| `GET` | `/api/admin/courses` |
| `POST` | `/api/admin/courses` |
| `DELETE` | `/api/admin/courses/<int:cid>` |
| `GET` | `/api/admin/courses/<int:cid>` |
| `PUT` | `/api/admin/courses/<int:cid>` |
| `GET` | `/api/admin/dashboard` |
| `GET` | `/api/admin/examiners` |
| `POST` | `/api/admin/examiners` |
| `GET` | `/api/admin/exams` |
| `POST` | `/api/admin/exams` |
| `DELETE` | `/api/admin/exams/<int:eid>` |
| `GET` | `/api/admin/exams/<int:eid>` |
| `PUT` | `/api/admin/exams/<int:eid>` |
| `PUT` | `/api/admin/exams/<int:eid>/examiners` |
| `POST` | `/api/admin/exams/<int:eid>/publish` |
| `GET` | `/api/admin/exams/<int:eid>/results` |
| `GET` | `/api/admin/exams/<int:eid>/rubrics` |
| `POST` | `/api/admin/exams/<int:eid>/rubrics` |
| `PUT` | `/api/admin/exams/<int:eid>/rubrics` |
| `POST` | `/api/admin/exams/<int:eid>/status` |
| `POST` | `/api/admin/exams/<int:eid>/unpublish` |
| `POST` | `/api/admin/jobs/<string:job>` |
| `GET` | `/api/admin/jobs/status/<string:task_id>` |
| `GET` | `/api/admin/reports` |
| `GET` | `/api/admin/reports/<int:rid>/html` |
| `DELETE` | `/api/admin/rubrics/<int:rid>` |
| `PUT` | `/api/admin/rubrics/<int:rid>` |
| `GET` | `/api/admin/search` |
| `GET` | `/api/admin/slots` |
| `PUT` | `/api/admin/slots/<int:sid>` |
| `POST` | `/api/admin/slots/<int:sid>/cancel` |
| `POST` | `/api/admin/slots/<int:sid>/reassign` |
| `GET` | `/api/admin/statistics` |
| `GET` | `/api/admin/students` |
| `GET` | `/api/admin/tickets` |
| `POST` | `/api/admin/tickets/<int:tid>/reply` |
| `POST` | `/api/admin/tickets/<int:tid>/status` |
| `DELETE` | `/api/admin/users/<int:uid>` |
| `GET` | `/api/admin/users/<int:uid>` |
| `PUT` | `/api/admin/users/<int:uid>` |
| `POST` | `/api/admin/users/<int:uid>/block` |
| `POST` | `/api/admin/users/<int:uid>/reset-password` |
| `POST` | `/api/auth/login` |
| `POST` | `/api/auth/logout` |
| `GET` | `/api/auth/me` |
| `POST` | `/api/auth/register` |
| `POST` | `/api/examiner/bookings/<int:bid>/attendance` |
| `GET` | `/api/examiner/bookings/<int:bid>/evaluation` |
| `POST` | `/api/examiner/bookings/<int:bid>/evaluation` |
| `GET` | `/api/examiner/dashboard` |
| `GET` | `/api/examiner/evaluations` |
| `GET` | `/api/examiner/exams` |
| `GET` | `/api/examiner/exams/<int:eid>` |
| `POST` | `/api/examiner/exams/<int:eid>/complete` |
| `GET` | `/api/examiner/slots` |
| `POST` | `/api/examiner/slots` |
| `DELETE` | `/api/examiner/slots/<int:sid>` |
| `PUT` | `/api/examiner/slots/<int:sid>` |
| `GET` | `/api/examiner/slots/<int:sid>/bookings` |
| `POST` | `/api/examiner/slots/<int:sid>/complete` |
| `GET` | `/api/examiner/statistics` |
| `GET` | `/api/examiner/students` |
| `GET` | `/api/exports` |
| `POST` | `/api/exports` |
| `GET` | `/api/exports/<int:jid>` |
| `GET` | `/api/exports/<int:jid>/download` |
| `GET` | `/api/exports/kinds` |
| `GET` | `/api/my/tickets` |
| `GET` | `/api/notifications` |
| `DELETE` | `/api/notifications/<int:nid>` |
| `POST` | `/api/notifications/<int:nid>/read` |
| `POST` | `/api/notifications/read-all` |
| `GET` | `/api/profile` |
| `PUT` | `/api/profile` |
| `GET` | `/api/profile/activity` |
| `POST` | `/api/profile/change-password` |
| `POST` | `/api/public/contact` |
| `GET` | `/api/public/courses` |
| `GET` | `/api/public/stats` |
| `GET` | `/api/public/upcoming` |
| `GET` | `/api/student/bookings` |
| `POST` | `/api/student/bookings` |
| `POST` | `/api/student/bookings/<int:bid>/cancel` |
| `PUT` | `/api/student/bookings/<int:bid>/submission` |
| `GET` | `/api/student/dashboard` |
| `GET` | `/api/student/exams` |
| `GET` | `/api/student/exams/<int:eid>` |
| `GET` | `/api/student/exports` |
| `POST` | `/api/student/exports` |
| `GET` | `/api/student/exports/<int:jid>` |
| `GET` | `/api/student/exports/<int:jid>/download` |
| `GET` | `/api/student/results` |
| `GET` | `/api/student/results/<int:bid>` |
| `GET` | `/api/student/statistics` |
