"""Admin API – full control over courses, exams, rubrics, users, slots, bookings, results."""
import os
import secrets
from collections import Counter, defaultdict
from datetime import date, datetime, timedelta

from flask import Blueprint, current_app, send_file
from flask_security import auth_required, roles_required, current_user
from flask_security.utils import hash_password
from sqlalchemy import func, or_

from models import (db, User, Role, StudentProfile, ExaminerProfile, Course, Examination,
                    Rubric, Slot, Booking, Evaluation, SupportTicket, ActivityLog, MonthlyReport,
                    Notification, EXAM_TYPES, grade_for)
from utils.cache import cached, invalidate, invalidate_exam_data, TTL_STATS, TTL_RUBRICS, TTL_EXAMS
from utils.helpers import (ApiError, ok, body, require, clean, validate_email, validate_password,
                           validate_phone, validate_url, parse_date, parse_time, to_int, to_float,
                           get_or_404, log_activity, notify, like)
from utils.rules import (validate_timeline, in_window, cancel_booking, check_slot_clash,
                         check_slot_in_exam_period, STATUS_LABELS)
from routes.common import apply_profile_update

admin_bp = Blueprint("admin", __name__, url_prefix="/api/admin")


@admin_bp.before_request
@auth_required("token")
@roles_required("admin")
def _guard():
    """Every /api/admin route requires a valid token of the admin role."""
    return None


def role_query(role):
    return User.query.join(User.roles).filter(Role.name == role)


# =====================================================================
# Dashboard & statistics
# =====================================================================
@admin_bp.get("/dashboard")
def dashboard():
    def produce():
        today = date.today()
        pending_eval = (Booking.query.outerjoin(Evaluation)
                        .join(Slot).filter(Booking.status == "booked", Slot.date <= today)
                        .filter(or_(Evaluation.id.is_(None), Evaluation.status != "submitted")).count())
        status_counts = dict(db.session.query(Examination.status, func.count())
                             .group_by(Examination.status).all())
        # bookings trend – last 14 days
        start = today - timedelta(days=13)
        rows = (db.session.query(func.date(Booking.booked_at), func.count())
                .filter(Booking.booked_at >= datetime.combine(start, datetime.min.time()))
                .group_by(func.date(Booking.booked_at)).all())
        trend_map = {str(d): c for d, c in rows}
        trend = [{"date": (start + timedelta(days=i)).isoformat(),
                  "count": trend_map.get((start + timedelta(days=i)).isoformat(), 0)} for i in range(14)]
        popular = (db.session.query(Examination.name, func.count(Booking.id))
                   .join(Booking, Booking.exam_id == Examination.id)
                   .filter(Booking.status != "cancelled")
                   .group_by(Examination.id).order_by(func.count(Booking.id).desc()).limit(6).all())
        workload = []
        for ex in role_query("examiner").all():
            workload.append({
                "name": ex.name,
                "slots": Slot.query.filter(Slot.examiner_id == ex.id, Slot.status != "cancelled").count(),
                "evaluations": Evaluation.query.filter_by(examiner_id=ex.id, status="submitted").count(),
            })
        upcoming = (Slot.query.filter(Slot.date >= today, Slot.status.in_(["available", "full"]))
                    .order_by(Slot.date, Slot.start_time).limit(6).all())
        return {
            "counts": {
                "courses": Course.query.count(),
                "examinations": Examination.query.count(),
                "students": role_query("student").count(),
                "examiners": role_query("examiner").count(),
                "slots": Slot.query.filter(Slot.status != "cancelled").count(),
                "bookings": Booking.query.count(),
                "active_bookings": Booking.query.filter_by(status="booked").count(),
                "pending_evaluations": pending_eval,
                "open_tickets": SupportTicket.query.filter_by(status="open").count(),
                "blocked_users": User.query.filter_by(active=False).count(),
            },
            "exam_status": {k: status_counts.get(k, 0) for k in STATUS_LABELS},
            "booking_trend": trend,
            "popular_exams": [{"name": n, "bookings": c} for n, c in popular],
            "examiner_workload": sorted(workload, key=lambda w: -w["slots"])[:8],
            "upcoming_slots": [s.to_dict() for s in upcoming],
        }
    data = cached("stats", "admin-dashboard", TTL_STATS, produce)
    recent = ActivityLog.query.order_by(ActivityLog.created_at.desc()).limit(8).all()
    data["recent_activity"] = [a.to_dict() for a in recent]
    return ok(data)


@admin_bp.get("/statistics")
def statistics():
    def produce():
        evals = Evaluation.query.filter_by(status="submitted").all()
        grades = Counter()
        per_exam = defaultdict(list)
        for e in evals:
            pct = (e.total_marks / e.exam.max_marks * 100) if e.exam and e.exam.max_marks else 0
            grades[grade_for(pct)] += 1
            per_exam[e.exam].append(e)
        exam_perf = []
        for ex, lst in per_exam.items():
            avg = sum(x.total_marks for x in lst) / len(lst)
            passed = sum(1 for x in lst if x.total_marks >= (ex.pass_marks or 0))
            exam_perf.append({"name": ex.name, "avg": round(avg, 2), "max": ex.max_marks,
                              "avg_pct": round(avg / ex.max_marks * 100, 1) if ex.max_marks else 0,
                              "pass_rate": round(passed / len(lst) * 100, 1), "count": len(lst)})
        by_type = dict(db.session.query(Examination.exam_type, func.count(Booking.id))
                       .join(Booking, Booking.exam_id == Examination.id)
                       .group_by(Examination.exam_type).all())
        booking_status = dict(db.session.query(Booking.status, func.count()).group_by(Booking.status).all())
        # registrations over last 6 months
        today = date.today()
        months = []
        for i in range(5, -1, -1):
            y, m = today.year, today.month - i
            while m <= 0:
                m += 12
                y -= 1
            months.append(f"{y:04d}-{m:02d}")
        reg_rows = dict(db.session.query(func.strftime("%Y-%m", User.created_at), func.count())
                        .join(User.roles).filter(Role.name == "student")
                        .group_by(func.strftime("%Y-%m", User.created_at)).all())
        book_rows = dict(db.session.query(func.strftime("%Y-%m", Booking.booked_at), func.count())
                         .group_by(func.strftime("%Y-%m", Booking.booked_at)).all())
        slot_util = []
        for ex in Examination.query.filter(Examination.status != "draft").all():
            cap = sum(s.capacity for s in ex.slots if s.status != "cancelled")
            used = sum(len(s.active_bookings) for s in ex.slots if s.status != "cancelled")
            if cap:
                slot_util.append({"name": ex.name, "capacity": cap, "booked": used,
                                  "pct": round(used / cap * 100, 1)})
        course_rows = (db.session.query(Course.code, func.count(Booking.id))
                       .join(Examination, Examination.course_id == Course.id)
                       .join(Booking, Booking.exam_id == Examination.id)
                       .filter(Booking.status != "cancelled").group_by(Course.id).all())
        return {
            "grades": {g: grades.get(g, 0) for g in ["S", "A", "B", "C", "D", "E", "U"]},
            "exam_performance": sorted(exam_perf, key=lambda x: -x["count"]),
            "bookings_by_type": {t: by_type.get(t, 0) for t in EXAM_TYPES},
            "booking_status": booking_status,
            "months": months,
            "registrations": [reg_rows.get(m, 0) for m in months],
            "monthly_bookings": [book_rows.get(m, 0) for m in months],
            "slot_utilisation": slot_util,
            "course_bookings": [{"code": c, "count": n} for c, n in course_rows],
            "total_evaluated": len(evals),
            "avg_percentage": round(sum((e.total_marks / e.exam.max_marks * 100) for e in evals
                                        if e.exam and e.exam.max_marks) / len(evals), 1) if evals else 0,
        }
    return ok(cached("stats", "admin-statistics", TTL_STATS, produce))


# =====================================================================
# Courses
# =====================================================================
@admin_bp.get("/courses")
def list_courses():
    from flask import request
    q = Course.query
    if request.args.get("q"):
        s = like(request.args["q"])
        q = q.filter(or_(Course.code.ilike(s), Course.name.ilike(s), Course.department.ilike(s)))
    if request.args.get("status"):
        q = q.filter(Course.status == request.args["status"])
    return ok([c.to_dict() for c in q.order_by(Course.code).all()])


def _course_from(data, course=None):
    require(data, "code", "name")
    code = clean(data["code"], 20).upper()
    dup = Course.query.filter(Course.code == code)
    if course:
        dup = dup.filter(Course.id != course.id)
    if dup.first():
        raise ApiError("Course code already exists", 409, {"code": "Duplicate"})
    course = course or Course()
    course.code = code
    course.name = clean(data["name"], 150)
    course.description = clean(data.get("description"), 5000)
    course.department = clean(data.get("department"), 100)
    course.level = clean(data.get("level"), 50)
    course.credits = to_int(data.get("credits") or 4, "credits", 0, 20)
    status = data.get("status") or "active"
    if status not in ("active", "inactive"):
        raise ApiError("Invalid status", 422, {"status": "active / inactive"})
    course.status = status
    return course


@admin_bp.post("/courses")
def create_course():
    c = _course_from(body())
    db.session.add(c)
    log_activity("course_create", f"Created course {c.code}")
    db.session.commit()
    invalidate_exam_data()
    return ok(c.to_dict(), "Course created", 201)


@admin_bp.get("/courses/<int:cid>")
def get_course(cid):
    c = get_or_404(Course, cid, "Course")
    data = c.to_dict()
    data["exams"] = [e.to_dict() for e in c.exams]
    return ok(data)


@admin_bp.put("/courses/<int:cid>")
def update_course(cid):
    c = _course_from(body(), get_or_404(Course, cid, "Course"))
    log_activity("course_update", f"Updated course {c.code}")
    db.session.commit()
    invalidate_exam_data()
    return ok(c.to_dict(), "Course updated")


@admin_bp.delete("/courses/<int:cid>")
def delete_course(cid):
    c = get_or_404(Course, cid, "Course")
    has_bookings = Booking.query.join(Examination).filter(Examination.course_id == c.id).count()
    if has_bookings:
        raise ApiError("This course has examinations with bookings. Mark it inactive instead "
                       "to keep the history.", 409)
    log_activity("course_delete", f"Deleted course {c.code}")
    db.session.delete(c)
    db.session.commit()
    invalidate_exam_data()
    return ok(message="Course deleted")


# =====================================================================
# Examinations
# =====================================================================
@admin_bp.get("/exams")
def list_exams():
    from flask import request
    a = request.args
    q = Examination.query.join(Course)
    if a.get("q"):
        s = like(a["q"])
        q = q.filter(or_(Examination.name.ilike(s), Course.code.ilike(s), Course.name.ilike(s)))
    if a.get("status"):
        q = q.filter(Examination.status == a["status"])
    if a.get("course_id"):
        q = q.filter(Examination.course_id == int(a["course_id"]))
    if a.get("exam_type"):
        q = q.filter(Examination.exam_type == a["exam_type"])
    exams = q.order_by(Examination.created_at.desc()).all()
    out = []
    for e in exams:
        d = e.to_dict()
        d["booking_count"] = Booking.query.filter(Booking.exam_id == e.id,
                                                  Booking.status != "cancelled").count()
        out.append(d)
    return ok(out)


def _exam_from(data, exam=None):
    require(data, "course_id", "name", "exam_type", "duration_minutes", "max_marks")
    course = get_or_404(Course, to_int(data["course_id"], "course_id"), "Course")
    if data["exam_type"] not in EXAM_TYPES:
        raise ApiError("Invalid examination type", 422, {"exam_type": " / ".join(EXAM_TYPES)})
    exam = exam or Examination(status="draft")
    exam.course_id = course.id
    exam.name = clean(data["name"], 150)
    exam.exam_type = data["exam_type"]
    exam.description = clean(data.get("description"), 5000)
    exam.instructions = clean(data.get("instructions"), 5000)
    exam.duration_minutes = to_int(data["duration_minutes"], "duration_minutes", 5, 600)
    max_marks = to_float(data["max_marks"], "max_marks", 1, 1000)
    if exam.id and max_marks != exam.max_marks and \
            Evaluation.query.filter_by(exam_id=exam.id, status="submitted").count():
        raise ApiError("Maximum marks cannot change after evaluations are submitted", 409)
    exam.max_marks = max_marks
    exam.pass_marks = to_float(data.get("pass_marks") or 0, "pass_marks", 0, max_marks)
    exam.requires_submission = bool(data.get("requires_submission"))
    exam.auto_publish = bool(data.get("auto_publish"))
    for f in ("slot_creation_start", "slot_creation_end", "booking_start", "booking_end",
              "exam_start", "exam_end"):
        setattr(exam, f, parse_date(data.get(f), f, required=True))
    validate_timeline(exam)
    return exam


@admin_bp.post("/exams")
def create_exam():
    data = body()
    exam = _exam_from(data)
    db.session.add(exam)
    db.session.flush()
    change = _assign_examiners(exam, data["examiner_ids"]) if data.get("examiner_ids") else None
    log_activity("exam_create", f"Created examination {exam.name}")
    db.session.commit()
    _mail_assignment(exam.id, change)
    invalidate_exam_data()
    return ok(exam.to_dict(True), "Examination created (Draft)", 201)


@admin_bp.get("/exams/<int:eid>")
def get_exam(eid):
    exam = get_or_404(Examination, eid, "Examination")
    data = exam.to_dict(True)
    bookings = Booking.query.filter_by(exam_id=exam.id).all()
    active = [b for b in bookings if b.status != "cancelled"]
    evaluated = [b for b in active if b.evaluation and b.evaluation.status == "submitted"]
    data["slots"] = [s.to_dict(False) for s in sorted(exam.slots, key=lambda s: (s.date, s.start_time))]
    data["summary"] = {
        "bookings": len(active), "cancelled": len(bookings) - len(active),
        "evaluated": len(evaluated),
        "pending_evaluation": len([b for b in active if b.status == "booked" and
                                   not (b.evaluation and b.evaluation.status == "submitted")]),
        "absent": len([b for b in active if b.status == "absent"]),
        "avg_marks": round(sum(b.evaluation.total_marks for b in evaluated) / len(evaluated), 2)
        if evaluated else None,
    }
    data["timeline_checks"] = {
        "slot_creation_today": in_window(exam.slot_creation_start, exam.slot_creation_end),
        "booking_today": in_window(exam.booking_start, exam.booking_end),
    }
    return ok(data)


@admin_bp.put("/exams/<int:eid>")
def update_exam(eid):
    exam = get_or_404(Examination, eid, "Examination")
    if exam.status == "completed" and exam.results_published:
        raise ApiError("Completed examinations with published results cannot be edited", 409)
    data = body()
    _exam_from(data, exam)
    change = _assign_examiners(exam, data["examiner_ids"]) if "examiner_ids" in data else None
    log_activity("exam_update", f"Updated examination {exam.name}")
    db.session.commit()
    _mail_assignment(exam.id, change)
    invalidate_exam_data()
    return ok(exam.to_dict(True), "Examination updated")


@admin_bp.delete("/exams/<int:eid>")
def delete_exam(eid):
    exam = get_or_404(Examination, eid, "Examination")
    if Booking.query.filter_by(exam_id=exam.id).count():
        raise ApiError("Examination has bookings – it cannot be deleted (history must be kept). "
                       "Close or complete it instead.", 409)
    log_activity("exam_delete", f"Deleted examination {exam.name}")
    db.session.delete(exam)
    db.session.commit()
    invalidate_exam_data()
    return ok(message="Examination deleted")


def _assign_examiners(exam, ids):
    examiners = []
    for i in ids or []:
        u = db.session.get(User, int(i))
        if not u or u.role != "examiner":
            raise ApiError(f"User {i} is not an examiner", 422)
        examiners.append(u)
    removed = [e for e in exam.examiners if e not in examiners]
    for r in removed:
        if Slot.query.filter(Slot.exam_id == exam.id, Slot.examiner_id == r.id,
                             Slot.status != "cancelled").count():
            raise ApiError(f"{r.name} already has slots in this exam – reassign/cancel them first", 409)
    added = [e for e in examiners if e not in exam.examiners]
    exam.examiners = examiners
    for a in added:
        notify(a.id, "New examination assigned",
               f"You have been assigned to {exam.name} ({exam.course.code}). Details sent to your e-mail.",
               "info", f"/examiner/exams/{exam.id}")
    for r in removed:
        notify(r.id, "Removed from examination", f"You were removed from {exam.name}.", "warning",
               "/examiner/exams")
    return [a.id for a in added], [r.id for r in removed]


def _mail_assignment(exam_id, change):
    """E-mail examiners who were assigned / removed (runs after the DB commit)."""
    added, removed = change or ([], [])
    if added or removed:
        from tasks.jobs import send_assignment_emails
        _defer(send_assignment_emails, exam_id, added, removed)


@admin_bp.put("/exams/<int:eid>/examiners")
def assign_examiners(eid):
    exam = get_or_404(Examination, eid, "Examination")
    change = _assign_examiners(exam, body().get("examiner_ids", []))
    log_activity("exam_assign", f"Assigned examiners for {exam.name}")
    db.session.commit()
    _mail_assignment(exam.id, change)
    invalidate_exam_data()
    return ok(exam.to_dict(True), "Examiners updated")


@admin_bp.post("/exams/<int:eid>/status")
def change_exam_status(eid):
    """Open/close slot creation & booking windows; complete; revert to draft."""
    exam = get_or_404(Examination, eid, "Examination")
    action = body().get("action")
    t = date.today()
    if action == "open_slot_creation":
        if exam.status not in ("draft", "booking_open"):
            raise ApiError("Slot creation can be opened only from Draft (or re-opened from Booking Open)", 409)
        if not exam.examiners:
            raise ApiError("Assign at least one examiner before opening slot creation", 409)
        if not exam.rubrics or abs(exam.rubric_weightage - 100) > 0.01:
            raise ApiError(f"Rubric weightage must total 100% (currently {exam.rubric_weightage}%)", 409)
        if not in_window(exam.slot_creation_start, exam.slot_creation_end, t):
            raise ApiError(f"Today ({t}) is outside the slot creation period "
                           f"{exam.slot_creation_start} → {exam.slot_creation_end}. Update the timeline first.", 409)
        if exam.status == "booking_open" and Booking.query.filter_by(exam_id=exam.id).count():
            raise ApiError("Students have already booked – slot creation cannot be re-opened", 409)
        exam.status = "slot_creation"
        for e in exam.examiners:
            notify(e.id, "Slot creation opened",
                   f"Create your slots for {exam.name} before {exam.slot_creation_end}.", "info",
                   f"/examiner/exams/{exam.id}")
    elif action == "close_slot_creation":
        if exam.status != "slot_creation":
            raise ApiError("Slot creation is not open", 409)
        exam.status = "draft"
    elif action == "open_booking":
        if exam.status not in ("slot_creation", "closed", "draft"):
            raise ApiError("Booking can be opened from Slot Creation / Closed state", 409)
        if not Slot.query.filter(Slot.exam_id == exam.id, Slot.status == "available").count():
            raise ApiError("There are no available slots – examiners must create slots first", 409)
        if not in_window(exam.booking_start, exam.booking_end, t):
            raise ApiError(f"Today ({t}) is outside the booking period "
                           f"{exam.booking_start} → {exam.booking_end}. Update the timeline first.", 409)
        exam.status = "booking_open"
        from tasks.jobs import notify_booking_open
        _defer(notify_booking_open, exam.id)
    elif action == "close_booking":
        if exam.status != "booking_open":
            raise ApiError("Booking is not open", 409)
        exam.status = "closed"
    elif action == "complete":
        if exam.status not in ("closed", "booking_open"):
            raise ApiError("Only closed examinations can be marked completed", 409)
        exam.status = "completed"
    elif action == "revert_draft":
        if Booking.query.filter_by(exam_id=exam.id).count():
            raise ApiError("Cannot revert to draft – bookings exist", 409)
        exam.status = "draft"
    else:
        raise ApiError("Unknown action", 422)
    log_activity("exam_status", f"{exam.name}: {action}")
    db.session.commit()
    invalidate_exam_data()
    return ok(exam.to_dict(True), f"Status changed to {STATUS_LABELS[exam.status]}")


def _defer(task, *args):
    """Queue a Celery task; if the broker is down run inline so the API still works."""
    try:
        task.delay(*args)
    except Exception as exc:  # pragma: no cover
        current_app.logger.warning(f"Celery unavailable ({exc}); running {task.name} inline")
        try:
            task.run(*args)
        except Exception:
            current_app.logger.exception("Inline task failed")


# ---------------- Rubrics ----------------
@admin_bp.get("/exams/<int:eid>/rubrics")
def list_rubrics(eid):
    exam = get_or_404(Examination, eid, "Examination")
    return ok(cached("rubrics", f"exam-{eid}", TTL_RUBRICS, lambda: [r.to_dict() for r in exam.rubrics]))


def _rubric_locked(exam):
    if Evaluation.query.filter_by(exam_id=exam.id).count():
        raise ApiError("Rubric is locked because evaluations have started", 409)


def _rubric_from(data, exam, rubric=None):
    require(data, "criterion", "max_marks", "weightage")
    rubric = rubric or Rubric(exam_id=exam.id)
    rubric.criterion = clean(data["criterion"], 150)
    rubric.max_marks = to_float(data["max_marks"], "max_marks", 0.5, 1000)
    rubric.weightage = to_float(data["weightage"], "weightage", 0.5, 100)
    rubric.description = clean(data.get("description"), 2000)
    rubric.order = to_int(data.get("order") or 0, "order", 0, 100)
    return rubric


@admin_bp.post("/exams/<int:eid>/rubrics")
def add_rubric(eid):
    exam = get_or_404(Examination, eid, "Examination")
    _rubric_locked(exam)
    r = _rubric_from(body(), exam)
    if exam.rubric_weightage + r.weightage > 100.001:
        raise ApiError(f"Total weightage would exceed 100% (current {exam.rubric_weightage}%)", 422,
                       {"weightage": "Too high"})
    r.order = r.order or len(exam.rubrics) + 1
    db.session.add(r)
    db.session.commit()
    invalidate_exam_data()
    return ok(r.to_dict(), "Criterion added", 201)


@admin_bp.put("/exams/<int:eid>/rubrics")
def replace_rubrics(eid):
    """Save the complete rubric in one go (used by the rubric builder)."""
    exam = get_or_404(Examination, eid, "Examination")
    _rubric_locked(exam)
    items = body().get("rubrics") or []
    if not items:
        raise ApiError("Add at least one criterion", 422)
    new = [_rubric_from(it, exam) for it in items]
    total = round(sum(r.weightage for r in new), 2)
    if abs(total - 100) > 0.01:
        raise ApiError(f"Weightages must add up to 100% (currently {total}%)", 422)
    for r in list(exam.rubrics):
        db.session.delete(r)
    db.session.flush()
    for i, r in enumerate(new, 1):
        r.order = i
        db.session.add(r)
    log_activity("rubric_save", f"Saved rubric for {exam.name}")
    db.session.commit()
    invalidate_exam_data()
    return ok([r.to_dict() for r in exam.rubrics], "Rubric saved")


@admin_bp.put("/rubrics/<int:rid>")
def update_rubric(rid):
    r = get_or_404(Rubric, rid, "Criterion")
    _rubric_locked(r.exam)
    old = r.weightage
    _rubric_from(body(), r.exam, r)
    if r.exam.rubric_weightage > 100.001:
        r.weightage = old
        raise ApiError("Total weightage would exceed 100%", 422)
    db.session.commit()
    invalidate_exam_data()
    return ok(r.to_dict(), "Criterion updated")


@admin_bp.delete("/rubrics/<int:rid>")
def delete_rubric(rid):
    r = get_or_404(Rubric, rid, "Criterion")
    _rubric_locked(r.exam)
    db.session.delete(r)
    db.session.commit()
    invalidate_exam_data()
    return ok(message="Criterion removed")


# ---------------- Results ----------------
@admin_bp.get("/exams/<int:eid>/results")
def exam_results(eid):
    exam = get_or_404(Examination, eid, "Examination")
    rows = []
    for b in Booking.query.filter(Booking.exam_id == exam.id, Booking.status != "cancelled").all():
        d = b.to_dict()
        d["evaluation"] = b.evaluation.to_dict() if b.evaluation else None
        rows.append(d)
    return ok({"exam": exam.to_dict(True), "results": rows})


@admin_bp.post("/exams/<int:eid>/publish")
def publish_results(eid):
    exam = get_or_404(Examination, eid, "Examination")
    if exam.results_published:
        raise ApiError("Results are already published", 409)
    if exam.status not in ("closed", "completed"):
        raise ApiError("Close booking before publishing results", 409)
    active = Booking.query.filter(Booking.exam_id == exam.id, Booking.status.in_(["booked", "completed"])).all()
    pending = [b for b in active if not (b.evaluation and b.evaluation.status == "submitted")]
    force = body().get("force")
    if pending and not force:
        raise ApiError(f"{len(pending)} booking(s) are not evaluated yet. Evaluate them or publish "
                       "anyway (they will be shown as pending).", 409, {"pending": len(pending)})
    exam.results_published = True
    exam.published_at = datetime.now()
    exam.status = "completed"
    for b in active:
        if b.evaluation and b.evaluation.status == "submitted" and not b.evaluation.result_notified:
            notify(b.student_id, "Result published 🎉",
                   f"Your result for {exam.name} is now available.", "success",
                   f"/student/results/{b.id}")
    log_activity("publish_results", f"Published results of {exam.name}")
    db.session.commit()
    from tasks.jobs import send_result_emails
    _defer(send_result_emails, exam.id)
    invalidate_exam_data()
    return ok(exam.to_dict(True), "Results published – students have been notified")


@admin_bp.post("/exams/<int:eid>/unpublish")
def unpublish_results(eid):
    exam = get_or_404(Examination, eid, "Examination")
    exam.results_published = False
    exam.published_at = None
    exam.status = "closed"
    log_activity("unpublish_results", f"Withdrew results of {exam.name}")
    db.session.commit()
    invalidate_exam_data()
    return ok(exam.to_dict(True), "Results withdrawn")


# =====================================================================
# Users (students & examiners)
# =====================================================================
def _user_list(role):
    from flask import request
    a = request.args
    q = role_query(role)
    if role == "student":
        q = q.outerjoin(StudentProfile, StudentProfile.user_id == User.id)
    else:
        q = q.outerjoin(ExaminerProfile, ExaminerProfile.user_id == User.id)
    if a.get("q"):
        s = like(a["q"])
        conds = [User.name.ilike(s), User.email.ilike(s), User.phone.ilike(s)]
        if role == "student":
            conds += [StudentProfile.roll_no.ilike(s), StudentProfile.program.ilike(s)]
        else:
            conds += [ExaminerProfile.employee_id.ilike(s), ExaminerProfile.department.ilike(s)]
        q = q.filter(or_(*conds))
    if a.get("status") == "active":
        q = q.filter(User.active.is_(True))
    elif a.get("status") == "blocked":
        q = q.filter(User.active.is_(False))
    users = q.order_by(User.created_at.desc()).all()
    out = []
    for u in users:
        d = u.to_dict()
        if role == "student":
            d["bookings"] = Booking.query.filter(Booking.student_id == u.id, Booking.status != "cancelled").count()
        else:
            d["assigned_exams"] = u.assigned_exams.count()
            d["slots"] = Slot.query.filter(Slot.examiner_id == u.id, Slot.status != "cancelled").count()
            d["evaluations"] = Evaluation.query.filter_by(examiner_id=u.id, status="submitted").count()
        out.append(d)
    return out


@admin_bp.get("/students")
def list_students():
    return ok(_user_list("student"))


@admin_bp.get("/examiners")
def list_examiners():
    return ok(_user_list("examiner"))


@admin_bp.post("/examiners")
def create_examiner():
    data = body()
    require(data, "name", "email", "department")
    email = validate_email(data["email"])
    ds = current_app.security.datastore
    if ds.find_user(email=email):
        raise ApiError("E-mail already registered", 409, {"email": "Already exists"})
    password = data.get("password") or ("Exam@" + secrets.token_hex(3))
    validate_password(password)
    emp_id = clean(data.get("employee_id"), 30)
    if emp_id and ExaminerProfile.query.filter_by(employee_id=emp_id.upper()).first():
        raise ApiError("Employee ID already exists", 409, {"employee_id": "Duplicate"})
    user = ds.create_user(email=email, password=hash_password(password), name=clean(data["name"], 120),
                          phone=validate_phone(data.get("phone")), roles=["examiner"])
    db.session.flush()
    db.session.add(ExaminerProfile(
        user_id=user.id, employee_id=(emp_id or f"EXM{user.id:04d}").upper(),
        department=clean(data.get("department"), 100), designation=clean(data.get("designation"), 100),
        specialization=clean(data.get("specialization"), 150), office=clean(data.get("office"), 120)))
    notify(user.id, "Welcome, Examiner 👋",
           "Your examiner account was created by the admin. Check your assigned examinations.", "success",
           "/examiner/exams")
    log_activity("examiner_create", f"Created examiner {user.email}")
    db.session.commit()
    from tasks.jobs import send_examiner_credentials
    _defer(send_examiner_credentials, user.id, password)
    invalidate("stats")
    data = user.to_dict()
    data["initial_password"] = password
    return ok(data, "Examiner created – credentials e-mailed", 201)


@admin_bp.get("/users/<int:uid>")
def user_detail(uid):
    """Full profile + statistics + activity for a student or examiner."""
    u = get_or_404(User, uid, "User")
    if u.role == "admin":
        raise ApiError("Use the profile page for admin", 400)
    data = u.to_dict()
    data["activity"] = [a.to_dict() for a in ActivityLog.query.filter_by(user_id=u.id)
                        .order_by(ActivityLog.created_at.desc()).limit(40).all()]
    if u.role == "student":
        bookings = Booking.query.filter_by(student_id=u.id).order_by(Booking.booked_at.desc()).all()
        evals = [b.evaluation for b in bookings if b.evaluation and b.evaluation.status == "submitted"]
        data["bookings"] = [b.to_dict() for b in bookings]
        data["stats"] = {
            "total_bookings": len(bookings),
            "active": len([b for b in bookings if b.status == "booked"]),
            "completed": len([b for b in bookings if b.status == "completed"]),
            "cancelled": len([b for b in bookings if b.status == "cancelled"]),
            "absent": len([b for b in bookings if b.status == "absent"]),
            "evaluated": len(evals),
            "avg_pct": round(sum(e.total_marks / e.exam.max_marks * 100 for e in evals) / len(evals), 1)
            if evals else None,
        }
        data["chart"] = [{"exam": e.exam.name, "pct": round(e.total_marks / e.exam.max_marks * 100, 1)}
                         for e in evals]
    else:
        slots = Slot.query.filter_by(examiner_id=u.id).order_by(Slot.date.desc()).all()
        evals = Evaluation.query.filter_by(examiner_id=u.id).all()
        data["assigned_exams"] = [e.to_dict() for e in u.assigned_exams.all()]
        data["slots"] = [s.to_dict() for s in slots]
        submitted = [e for e in evals if e.status == "submitted"]
        data["stats"] = {
            "assigned_exams": u.assigned_exams.count(),
            "slots": len([s for s in slots if s.status != "cancelled"]),
            "students_booked": sum(len(s.active_bookings) for s in slots),
            "evaluations": len(submitted),
            "pending": sum(1 for s in slots for b in s.active_bookings
                           if b.status == "booked" and not (b.evaluation and b.evaluation.status == "submitted")),
            "avg_given_pct": round(sum(e.total_marks / e.exam.max_marks * 100 for e in submitted) /
                                   len(submitted), 1) if submitted else None,
        }
        per_exam = Counter(e.exam.name for e in submitted)
        data["chart"] = [{"exam": k, "count": v} for k, v in per_exam.items()]
    return ok(data)


@admin_bp.put("/users/<int:uid>")
def update_user(uid):
    u = get_or_404(User, uid, "User")
    if u.role == "admin":
        raise ApiError("Admin profile cannot be edited here", 400)
    apply_profile_update(u, body(), admin=True)
    notify(u.id, "Profile updated by admin", "An administrator updated your profile details.", "info",
           "/profile")
    log_activity("user_update", f"Admin updated {u.email}")
    db.session.commit()
    return ok(u.to_dict(), "Profile updated")


@admin_bp.post("/users/<int:uid>/block")
def block_user(uid):
    u = get_or_404(User, uid, "User")
    if u.role == "admin":
        raise ApiError("Admin cannot be blocked", 400)
    data = body()
    block = bool(data.get("block", u.active))
    if block:
        u.active = False
        u.blocked_reason = clean(data.get("reason"), 255) or "Blocked by admin"
        u.fs_uniquifier = secrets.token_hex(16)  # invalidate all existing tokens
        msg = f"{u.name} has been blocked"
    else:
        u.active = True
        u.blocked_reason = None
        notify(u.id, "Account unblocked", "Your account is active again.", "success")
        msg = f"{u.name} has been unblocked"
    log_activity("user_block" if block else "user_unblock", msg)
    db.session.commit()
    invalidate("stats")
    return ok(u.to_dict(), msg)


@admin_bp.post("/users/<int:uid>/reset-password")
def reset_password(uid):
    u = get_or_404(User, uid, "User")
    if u.role == "admin":
        raise ApiError("Not allowed", 400)
    pw = body().get("password") or ("Reset@" + secrets.token_hex(3))
    validate_password(pw)
    u.password = hash_password(pw)
    u.fs_uniquifier = secrets.token_hex(16)
    log_activity("password_reset", f"Reset password of {u.email}")
    db.session.commit()
    from tasks.jobs import send_password_reset
    _defer(send_password_reset, u.id, pw)
    return ok({"password": pw}, "Password reset – new password e-mailed to the user")


@admin_bp.delete("/users/<int:uid>")
def delete_user(uid):
    u = get_or_404(User, uid, "User")
    if u.role == "admin":
        raise ApiError("Admin cannot be deleted", 400)
    if u.role == "student" and Booking.query.filter_by(student_id=u.id).count():
        raise ApiError("Student has examination history – block the account instead of deleting", 409)
    if u.role == "examiner" and (Slot.query.filter_by(examiner_id=u.id).count() or
                                 Evaluation.query.filter_by(examiner_id=u.id).count()):
        raise ApiError("Examiner has slots/evaluations – block the account instead of deleting", 409)
    log_activity("user_delete", f"Deleted {u.role} {u.email}")
    db.session.delete(u)
    db.session.commit()
    invalidate("stats")
    return ok(message="User deleted")


# =====================================================================
# Slots
# =====================================================================
@admin_bp.get("/slots")
def list_slots():
    from flask import request
    a = request.args
    q = Slot.query.join(Examination)
    if a.get("exam_id"):
        q = q.filter(Slot.exam_id == int(a["exam_id"]))
    if a.get("examiner_id"):
        q = q.filter(Slot.examiner_id == int(a["examiner_id"]))
    if a.get("status"):
        q = q.filter(Slot.status == a["status"])
    if a.get("date"):
        q = q.filter(Slot.date == parse_date(a["date"]))
    if a.get("q"):
        s = like(a["q"])
        q = q.outerjoin(User, User.id == Slot.examiner_id).filter(
            or_(Examination.name.ilike(s), User.name.ilike(s)))
    return ok([s.to_dict() for s in q.order_by(Slot.date.desc(), Slot.start_time).all()])


@admin_bp.put("/slots/<int:sid>")
def reschedule_slot(sid):
    """Admin reschedule (exceptional situations) – date/time/capacity/link."""
    slot = get_or_404(Slot, sid, "Slot")
    if slot.status in ("cancelled", "completed"):
        raise ApiError("Cancelled / completed slots cannot be changed", 409)
    data = body()
    day = parse_date(data.get("date") or slot.date.isoformat())
    start = parse_time(data.get("start_time") or slot.start_time.strftime("%H:%M"), "start_time")
    end = parse_time(data.get("end_time") or slot.end_time.strftime("%H:%M"), "end_time")
    check_slot_clash(slot.examiner_id, day, start, end, exclude_id=slot.id)
    cap = to_int(data.get("capacity") or slot.capacity, "capacity", 1, 200)
    if cap < len(slot.active_bookings):
        raise ApiError(f"Capacity cannot be lower than current bookings ({len(slot.active_bookings)})", 422)
    changed = (day, start, end) != (slot.date, slot.start_time, slot.end_time)
    slot.date, slot.start_time, slot.end_time, slot.capacity = day, start, end, cap
    if "meeting_link" in data:
        slot.meeting_link = validate_url(data.get("meeting_link"), "meeting_link")
    if "venue" in data:
        slot.venue = clean(data.get("venue"), 150)
    slot.refresh_seats()
    if changed:
        for b in slot.active_bookings:
            notify(b.student_id, "Examination rescheduled",
                   f"{slot.exam.name} moved to {day} {start.strftime('%H:%M')}–{end.strftime('%H:%M')}.",
                   "warning", "/student/bookings")
        if slot.examiner_id:
            notify(slot.examiner_id, "Slot rescheduled by admin",
                   f"{slot.exam.name} slot moved to {day} {start.strftime('%H:%M')}.", "warning",
                   "/examiner/slots")
    log_activity("slot_reschedule", f"Rescheduled slot #{slot.id} ({slot.exam.name})")
    db.session.commit()
    invalidate_exam_data()
    return ok(slot.to_dict(), "Slot updated" + (" – students notified" if changed else ""))


@admin_bp.post("/slots/<int:sid>/reassign")
def reassign_slot_examiner(sid):
    """Change the examiner assigned to a slot (exceptional situation)."""
    slot = get_or_404(Slot, sid, "Slot")
    ex = get_or_404(User, to_int(body().get("examiner_id"), "examiner_id"), "Examiner")
    if ex.role != "examiner" or not ex.active:
        raise ApiError("Select an active examiner", 422)
    if ex not in slot.exam.examiners:
        slot.exam.examiners.append(ex)  # auto-assign to the exam as well
    check_slot_clash(ex.id, slot.date, slot.start_time, slot.end_time, exclude_id=slot.id)
    if Evaluation.query.join(Booking).filter(Booking.slot_id == slot.id, Evaluation.status == "submitted").count():
        raise ApiError("Evaluations already submitted for this slot", 409)
    old = slot.examiner
    slot.examiner_id = ex.id
    for b in slot.active_bookings:
        if b.evaluation:
            b.evaluation.examiner_id = ex.id
        notify(b.student_id, "Examiner changed",
               f"Your examiner for {slot.exam.name} on {slot.date} is now {ex.name}.", "info",
               "/student/bookings")
    notify(ex.id, "Slot assigned to you",
           f"{slot.exam.name} on {slot.date} {slot.start_time.strftime('%H:%M')} was assigned to you.",
           "info", "/examiner/slots")
    if old:
        notify(old.id, "Slot reassigned", f"{slot.exam.name} on {slot.date} was reassigned to {ex.name}.",
               "warning", "/examiner/slots")
    log_activity("slot_reassign", f"Slot #{slot.id}: {old.name if old else '-'} → {ex.name}")
    db.session.commit()
    from tasks.jobs import send_user_email
    _defer(send_user_email, ex.id, f"Slot assigned to you – {slot.exam.name}", "A slot was assigned to you 📋",
           [f"<b>Examination:</b> {slot.exam.name} ({slot.exam.course.code})",
            f"<b>When:</b> {slot.date:%a, %d %b %Y}, {slot.start_time:%H:%M}–{slot.end_time:%H:%M}",
            f"<b>Students booked:</b> {len(slot.active_bookings)}",
            f"<b>Meeting link / venue:</b> {slot.meeting_link or slot.venue or '-'}"],
           "My slots", "/examiner/slots")
    invalidate_exam_data()
    return ok(slot.to_dict(), f"Examiner changed to {ex.name}")


@admin_bp.post("/slots/<int:sid>/cancel")
def cancel_slot(sid):
    slot = get_or_404(Slot, sid, "Slot")
    if slot.status in ("cancelled", "completed"):
        raise ApiError("Slot is already cancelled/completed", 409)
    reason = clean(body().get("reason"), 255) or "Cancelled by admin"
    for b in list(slot.active_bookings):
        if b.status == "booked":
            cancel_booking(b, "admin", reason)
    slot.status = "cancelled"
    slot.available_seats = 0
    log_activity("slot_cancel", f"Cancelled slot #{slot.id} ({slot.exam.name})")
    db.session.commit()
    invalidate_exam_data()
    return ok(slot.to_dict(), "Slot cancelled and affected students notified")


# =====================================================================
# Bookings
# =====================================================================
@admin_bp.get("/bookings")
def list_bookings():
    from flask import request
    a = request.args
    q = Booking.query.join(Slot).join(Examination, Examination.id == Booking.exam_id) \
        .join(User, User.id == Booking.student_id)
    if a.get("exam_id"):
        q = q.filter(Booking.exam_id == int(a["exam_id"]))
    if a.get("status"):
        q = q.filter(Booking.status == a["status"])
    if a.get("student_id"):
        q = q.filter(Booking.student_id == int(a["student_id"]))
    if a.get("q"):
        s = like(a["q"])
        q = q.outerjoin(StudentProfile, StudentProfile.user_id == User.id).filter(
            or_(User.name.ilike(s), User.email.ilike(s), Examination.name.ilike(s),
                StudentProfile.roll_no.ilike(s)))
    return ok([b.to_dict() for b in q.order_by(Booking.booked_at.desc()).all()])


@admin_bp.post("/bookings/<int:bid>/reschedule")
def reschedule_booking(bid):
    """Move a booking to another slot (possibly another examiner)."""
    b = get_or_404(Booking, bid, "Booking")
    if b.status != "booked":
        raise ApiError("Only active bookings can be rescheduled", 409)
    if b.evaluation and b.evaluation.status == "submitted":
        raise ApiError("This booking is already evaluated", 409)
    target = get_or_404(Slot, to_int(body().get("slot_id"), "slot_id"), "Slot")
    if target.id == b.slot_id:
        raise ApiError("Booking is already in this slot", 409)
    if target.exam_id != b.exam_id:
        raise ApiError("Target slot belongs to a different examination", 422)
    if target.status != "available" or target.available_seats <= 0:
        raise ApiError("Target slot has no free seat", 409)
    old = b.slot
    b.slot_id = target.id
    b.slot = target
    b.reschedule_count = (b.reschedule_count or 0) + 1
    b.admin_note = clean(body().get("note"), 300)
    if b.evaluation:
        b.evaluation.examiner_id = target.examiner_id
    db.session.flush()
    old.refresh_seats()
    target.refresh_seats()
    notify(b.student_id, "Booking rescheduled",
           f"{b.exam.name}: moved to {target.date} {target.start_time.strftime('%H:%M')} "
           f"with {target.examiner.name if target.examiner else 'TBA'}.", "warning", "/student/bookings")
    if target.examiner_id:
        notify(target.examiner_id, "New student in your slot",
               f"{b.student.name} was moved into your {b.exam.name} slot on {target.date}.", "info",
               "/examiner/students")
    log_activity("booking_reschedule", f"Booking #{b.id} moved slot {old.id} → {target.id}")
    db.session.commit()
    invalidate_exam_data()
    return ok(b.to_dict(), "Booking rescheduled – student notified")


@admin_bp.post("/bookings/<int:bid>/cancel")
def admin_cancel_booking(bid):
    b = get_or_404(Booking, bid, "Booking")
    cancel_booking(b, "admin", clean(body().get("reason"), 255))
    log_activity("booking_cancel", f"Admin cancelled booking #{b.id}")
    db.session.commit()
    invalidate_exam_data()
    return ok(b.to_dict(), "Booking cancelled")


# =====================================================================
# Global search
# =====================================================================
@admin_bp.get("/search")
def search():
    from flask import request
    term = (request.args.get("q") or "").strip()
    if len(term) < 2:
        return ok({"students": [], "examiners": [], "exams": [], "bookings": [], "courses": []})
    s = like(term)
    students = (role_query("student").outerjoin(StudentProfile, StudentProfile.user_id == User.id)
                .filter(or_(User.name.ilike(s), User.email.ilike(s), StudentProfile.roll_no.ilike(s)))
                .limit(8).all())
    examiners = (role_query("examiner").outerjoin(ExaminerProfile, ExaminerProfile.user_id == User.id)
                 .filter(or_(User.name.ilike(s), User.email.ilike(s), ExaminerProfile.department.ilike(s),
                             ExaminerProfile.employee_id.ilike(s))).limit(8).all())
    exams = (Examination.query.join(Course)
             .filter(or_(Examination.name.ilike(s), Course.code.ilike(s), Course.name.ilike(s),
                         Examination.exam_type.ilike(s))).limit(8).all())
    courses = Course.query.filter(or_(Course.code.ilike(s), Course.name.ilike(s))).limit(8).all()
    bq = (Booking.query.join(User, User.id == Booking.student_id)
          .join(Examination, Examination.id == Booking.exam_id)
          .filter(or_(User.name.ilike(s), Examination.name.ilike(s))))
    if term.isdigit():
        bq = Booking.query.filter(Booking.id == int(term))
    bookings = bq.order_by(Booking.booked_at.desc()).limit(8).all()
    return ok({"students": [u.to_dict() for u in students], "examiners": [u.to_dict() for u in examiners],
               "exams": [e.to_dict() for e in exams], "courses": [c.to_dict() for c in courses],
               "bookings": [b.to_dict() for b in bookings]})


# =====================================================================
# Support tickets
# =====================================================================
@admin_bp.get("/tickets")
def list_tickets():
    from flask import request
    q = SupportTicket.query
    if request.args.get("status"):
        q = q.filter_by(status=request.args["status"])
    return ok([t.to_dict() for t in q.order_by(SupportTicket.created_at.desc()).all()])


@admin_bp.post("/tickets/<int:tid>/reply")
def reply_ticket(tid):
    t = get_or_404(SupportTicket, tid, "Ticket")
    data = body()
    require(data, "reply")
    t.admin_reply = clean(data["reply"], 5000)
    t.replied_at = datetime.now()
    t.status = "closed" if data.get("close") else "replied"
    if t.user_id:
        notify(t.user_id, "Support replied", f"Re: {t.subject}", "info", "/support")
    log_activity("ticket_reply", f"Replied ticket #{t.id}")
    db.session.commit()
    from tasks.jobs import send_ticket_reply
    _defer(send_ticket_reply, t.id)
    return ok(t.to_dict(), "Reply sent")


@admin_bp.post("/tickets/<int:tid>/status")
def ticket_status(tid):
    t = get_or_404(SupportTicket, tid, "Ticket")
    st = body().get("status")
    if st not in ("open", "replied", "closed"):
        raise ApiError("Invalid status", 422)
    t.status = st
    db.session.commit()
    return ok(t.to_dict(), "Ticket updated")


# =====================================================================
# Reports, jobs & activity
# =====================================================================
@admin_bp.get("/activity")
def activity():
    from flask import request
    q = ActivityLog.query
    if request.args.get("user_id"):
        q = q.filter_by(user_id=int(request.args["user_id"]))
    return ok([a.to_dict() for a in q.order_by(ActivityLog.created_at.desc()).limit(200).all()])


@admin_bp.get("/reports")
def list_reports():
    return ok([r.to_dict() for r in MonthlyReport.query.order_by(MonthlyReport.created_at.desc()).all()])


@admin_bp.get("/reports/<int:rid>/html")
def report_html(rid):
    r = get_or_404(MonthlyReport, rid, "Report")
    path = os.path.join(current_app.config["REPORT_DIR"], r.filename or "")
    if not r.filename or not os.path.exists(path):
        raise ApiError("Report file missing", 404)
    with open(path, encoding="utf-8") as fh:
        return ok({"html": fh.read(), "month": r.month})


@admin_bp.post("/jobs/<string:job>")
def trigger_job(job):
    """Manually trigger scheduled jobs (useful for demo / viva)."""
    from tasks import jobs
    mapping = {"daily-reminder": jobs.daily_exam_reminder, "monthly-report": jobs.monthly_exam_report}
    if job not in mapping:
        raise ApiError("Unknown job", 404)
    month = body().get("month")
    try:
        res = mapping[job].delay(month) if job == "monthly-report" else mapping[job].delay()
        log_activity("job_trigger", f"Triggered {job}")
        db.session.commit()
        return ok({"task_id": res.id}, f"{job} queued – check MailHog in a few seconds", 202)
    except Exception as exc:
        raise ApiError(f"Could not reach Celery/Redis: {exc}", 503)


@admin_bp.get("/jobs/status/<string:task_id>")
def job_status(task_id):
    from app import celery
    res = celery.AsyncResult(task_id)
    return ok({"state": res.state, "result": res.result if res.successful() else None})
