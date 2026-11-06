"""'Export my data' – CSV builders for every role.

Every user can export ONLY their own data (profile, statistics, activity, …).
The admin additionally owns the platform, so the admin's exports cover the
examinations / audit data they manage.

Each builder returns a list of *sections*: (title, headers, rows).
A single-kind export writes one section; the "full" export writes all of them
into one CSV separated by section titles.
"""
from collections import Counter
from datetime import date

from models import (db, User, Role, Course, Examination, Slot, Booking, Evaluation, ActivityLog,
                    Notification, SupportTicket, grade_for, fmt_dt)

# key -> (label, description, icon, roles)
KINDS = {
    "profile": ("Profile & statistics", "Your account details and key statistics", "person-vcard", ("student", "examiner", "admin")),
    "activity": ("Activity log", "Everything you did on the portal (logins, bookings, changes…)", "activity", ("student", "examiner", "admin")),
    "notifications": ("Notifications", "All alerts you received", "bell", ("student", "examiner", "admin")),
    "tickets": ("Support requests", "Messages you sent to support and the replies", "chat-square-text", ("student", "examiner")),
    "exam_history": ("Examination history", "Every booking with date, examiner, marks and status", "journal-check", ("student",)),
    "assigned_exams": ("Assigned examinations", "Exams you conduct with slot and evaluation counts", "clipboard2-check", ("examiner",)),
    "slots": ("My slots", "All slots you created with seats and status", "calendar3-week", ("examiner",)),
    "evaluations": ("My evaluations", "Criterion-wise marks and remarks you gave", "award", ("examiner",)),
    "platform_stats": ("Platform statistics", "Institution-wide counts and per-examination results", "bar-chart-line", ("admin",)),
    "exams_overview": ("Examinations overview", "All examinations with timelines, bookings and averages", "clipboard-data", ("admin",)),
    "audit_log": ("Platform audit log", "Activity of every user (admin only)", "shield-check", ("admin",)),
    "full": ("Everything (complete report)", "All of the above in one CSV file", "archive", ("student", "examiner", "admin")),
}


def kind_label(kind):
    return KINDS.get(kind, (kind or "Export",))[0]


def kinds_for(role):
    return [{"key": k, "label": v[0], "description": v[1], "icon": v[2]}
            for k, v in KINDS.items() if role in v[3]]


def allowed(kind, role):
    return kind in KINDS and role in KINDS[kind][3]


def _dt(v):
    return fmt_dt(v).replace("T", " ")[:16] if v else ""


def _d(v):
    return v.isoformat() if isinstance(v, date) else (v or "")


def _t(t):
    return t.strftime("%H:%M") if t else ""


def _pct(ev):
    return round(ev.total_marks / ev.exam.max_marks * 100, 1) if ev and ev.exam and ev.exam.max_marks else 0


# ------------------------------------------------------------------ common sections
def profile_section(user):
    rows = [("User ID", user.id), ("Name", user.name), ("E-mail", user.email), ("Phone", user.phone or ""),
            ("Role", user.role), ("Status", "Active" if user.active else "Blocked"),
            ("Member since", _dt(user.created_at)), ("Last login", _dt(user.last_login_at))]
    for k, v in (user.to_dict().get("profile") or {}).items():
        rows.append((k.replace("_", " ").title(), v if v is not None else ""))
    rows.append(("", ""))
    rows.append(("— Statistics —", ""))
    rows += stats_rows(user)
    rows.append(("Actions recorded", ActivityLog.query.filter_by(user_id=user.id).count()))
    return ("Profile & statistics", ["Field", "Value"], rows)


def stats_rows(user):
    if user.role == "student":
        bookings = Booking.query.filter_by(student_id=user.id).all()
        res = [b for b in bookings if b.exam.results_visible and b.evaluation and b.evaluation.status == "submitted"]
        pcts = [_pct(b.evaluation) for b in res]
        st = Counter(b.status for b in bookings)
        return [("Total bookings", len(bookings)), ("Active bookings", st.get("booked", 0)),
                ("Completed", st.get("completed", 0)), ("Cancelled", st.get("cancelled", 0)),
                ("Absent", st.get("absent", 0)), ("Results available", len(res)),
                ("Average score %", round(sum(pcts) / len(pcts), 1) if pcts else "-"),
                ("Best score %", max(pcts) if pcts else "-"),
                ("Passed", sum(1 for b in res if b.evaluation.total_marks >= (b.exam.pass_marks or 0)))]
    if user.role == "examiner":
        slots = Slot.query.filter_by(examiner_id=user.id).all()
        evals = Evaluation.query.filter_by(examiner_id=user.id, status="submitted").all()
        pending = sum(1 for s in slots for b in s.active_bookings
                      if b.status == "booked" and not (b.evaluation and b.evaluation.status == "submitted"))
        return [("Assigned examinations", user.assigned_exams.count()),
                ("Slots created", len([s for s in slots if s.status != "cancelled"])),
                ("Students booked", sum(len(s.active_bookings) for s in slots)),
                ("Evaluations submitted", len(evals)), ("Pending evaluations", pending),
                ("Average score given %", round(sum(_pct(e) for e in evals) / len(evals), 1) if evals else "-")]
    # admin
    return [("Courses", Course.query.count()), ("Examinations", Examination.query.count()),
            ("Students", User.query.join(User.roles).filter(Role.name == "student").count()),
            ("Examiners", User.query.join(User.roles).filter(Role.name == "examiner").count()),
            ("Slots", Slot.query.filter(Slot.status != "cancelled").count()), ("Bookings", Booking.query.count()),
            ("Evaluations submitted", Evaluation.query.filter_by(status="submitted").count()),
            ("Open support tickets", SupportTicket.query.filter_by(status="open").count())]


def activity_section(user):
    logs = ActivityLog.query.filter_by(user_id=user.id).order_by(ActivityLog.created_at.desc()).all()
    return ("Activity log", ["Date & time", "Action", "Details"],
            [(_dt(a.created_at), a.action.replace("_", " "), a.details or "") for a in logs])


def notifications_section(user):
    items = Notification.query.filter_by(user_id=user.id).order_by(Notification.created_at.desc()).all()
    return ("Notifications", ["Date & time", "Title", "Message", "Type", "Read"],
            [(_dt(n.created_at), n.title, n.message or "", n.type, "Yes" if n.is_read else "No") for n in items])


def tickets_section(user):
    items = (SupportTicket.query.filter((SupportTicket.user_id == user.id) | (SupportTicket.email == user.email))
             .order_by(SupportTicket.created_at.desc()).all())
    return ("Support requests", ["Ticket", "Date", "Category", "Subject", "Message", "Status", "Reply", "Replied at"],
            [(t.id, _dt(t.created_at), t.category, t.subject, t.message, t.status, t.admin_reply or "",
              _dt(t.replied_at)) for t in items])


# ------------------------------------------------------------------ student
def exam_history_section(user):
    roll = user.student_profile.roll_no if user.student_profile else user.id
    rows = []
    for b in Booking.query.filter_by(student_id=user.id).order_by(Booking.booked_at.desc()).all():
        ev = b.evaluation
        visible = b.exam.results_visible and ev and ev.status == "submitted"
        rows.append((user.id, roll, user.name, b.exam.name, b.exam.exam_type,
                     f"{b.exam.course.code} - {b.exam.course.name}", _d(b.slot.date),
                     f"{_t(b.slot.start_time)}-{_t(b.slot.end_time)}",
                     b.slot.examiner.name if b.slot.examiner else "TBA",
                     ev.total_marks if visible else ("Pending" if b.status in ("booked", "completed") else "-"),
                     b.exam.max_marks, grade_for(_pct(ev)) if visible else "-",
                     (ev.remarks or "") if visible else "", b.status.capitalize(), _dt(b.booked_at)))
    return ("Examination history",
            ["Student ID", "Roll No", "Student Name", "Examination Name", "Examination Type", "Course",
             "Examination Date", "Time", "Examiner", "Marks Obtained", "Maximum Marks", "Grade",
             "Examiner Remarks", "Booking Status", "Booked On"], rows)


# ------------------------------------------------------------------ examiner
def assigned_exams_section(user):
    rows = []
    for e in user.assigned_exams.all():
        mine = [s for s in e.slots if s.examiner_id == user.id and s.status != "cancelled"]
        bks = [b for s in mine for b in s.active_bookings]
        done = [b for b in bks if b.evaluation and b.evaluation.status == "submitted"]
        rows.append((e.name, e.course.code, e.exam_type, e.status, _d(e.exam_start), _d(e.exam_end), len(mine),
                     len(bks), len(done), len([b for b in bks if b.status == "booked" and b not in done]),
                     "Yes" if e.results_visible else "No"))
    return ("Assigned examinations", ["Examination", "Course", "Type", "Status", "Exam from", "Exam to",
                                      "My slots", "My students", "Evaluated", "Pending", "Results visible"], rows)


def slots_section(user):
    slots = Slot.query.filter_by(examiner_id=user.id).order_by(Slot.date, Slot.start_time).all()
    return ("My slots", ["Slot ID", "Examination", "Course", "Date", "Start", "End", "Mode", "Venue / Link",
                         "Capacity", "Booked", "Available", "Status"],
            [(s.id, s.exam.name, s.exam.course.code, _d(s.date), _t(s.start_time), _t(s.end_time), s.mode,
              s.venue or s.meeting_link or "", s.capacity, len(s.active_bookings), s.available_seats, s.status)
             for s in slots])


def evaluations_section(user):
    rows = []
    for e in Evaluation.query.filter_by(examiner_id=user.id).order_by(Evaluation.evaluated_at.desc()).all():
        crit = "; ".join(f"{sc.rubric.criterion}: {sc.marks}/{sc.rubric.max_marks}" for sc in e.scores if sc.rubric)
        rows.append((_dt(e.evaluated_at), e.student.name,
                     e.student.student_profile.roll_no if e.student.student_profile else "", e.exam.name,
                     _d(e.booking.slot.date) if e.booking and e.booking.slot else "", crit, e.total_marks,
                     e.exam.max_marks, grade_for(_pct(e)), e.status, e.remarks or "",
                     "Yes" if e.exam.results_visible else "No"))
    return ("My evaluations", ["Evaluated at", "Student", "Roll No", "Examination", "Exam date",
                               "Criterion marks", "Total", "Max", "Grade", "Status", "Remarks",
                               "Visible to student"], rows)


# ------------------------------------------------------------------ admin
def platform_stats_section(user):
    rows = [(k, v) for k, v in stats_rows(user)]
    rows.append(("", ""))
    rows.append(("— Per examination —", ""))
    for e in Examination.query.all():
        evs = Evaluation.query.filter_by(exam_id=e.id, status="submitted").all()
        avg = round(sum(x.total_marks for x in evs) / len(evs), 1) if evs else "-"
        rows.append((e.name, f"{len(evs)} evaluated · avg {avg}/{e.max_marks} · status {e.status}"))
    return ("Platform statistics", ["Metric", "Value"], rows)


def exams_overview_section(user):
    rows = []
    for e in Examination.query.order_by(Examination.created_at).all():
        bks = Booking.query.filter(Booking.exam_id == e.id, Booking.status != "cancelled").all()
        evs = [b.evaluation for b in bks if b.evaluation and b.evaluation.status == "submitted"]
        rows.append((e.id, e.name, e.course.code, e.exam_type, e.status, _d(e.slot_creation_start),
                     _d(e.slot_creation_end), _d(e.booking_start), _d(e.booking_end), _d(e.exam_start),
                     _d(e.exam_end), ", ".join(x.name for x in e.examiners),
                     len([s for s in e.slots if s.status != "cancelled"]), len(bks), len(evs),
                     round(sum(x.total_marks for x in evs) / len(evs), 1) if evs else "-", e.max_marks,
                     "Instant" if e.auto_publish else "After publish", "Yes" if e.results_published else "No"))
    return ("Examinations overview",
            ["ID", "Examination", "Course", "Type", "Status", "Slot creation from", "Slot creation to",
             "Booking from", "Booking to", "Exam from", "Exam to", "Examiners", "Slots", "Bookings",
             "Evaluated", "Average", "Max marks", "Result release", "Published"], rows)


def audit_log_section(user):
    logs = ActivityLog.query.order_by(ActivityLog.created_at.desc()).all()
    return ("Platform audit log", ["Date & time", "User", "Role", "Action", "Details"],
            [(_dt(a.created_at), a.user.name if a.user else "System", a.user.role if a.user else "",
              a.action.replace("_", " "), a.details or "") for a in logs])


BUILDERS = {
    "profile": profile_section, "activity": activity_section, "notifications": notifications_section,
    "tickets": tickets_section, "exam_history": exam_history_section,
    "assigned_exams": assigned_exams_section, "slots": slots_section, "evaluations": evaluations_section,
    "platform_stats": platform_stats_section, "exams_overview": exams_overview_section,
    "audit_log": audit_log_section,
}


def build_sections(user, kind):
    if kind == "full":
        return [BUILDERS[k](user) for k in KINDS if k != "full" and allowed(k, user.role)]
    return [BUILDERS[kind](user)]
