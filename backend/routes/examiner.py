"""Examiner API – assigned exams, slot management, booked students, rubric evaluation."""
from collections import Counter
from datetime import date, datetime, timedelta

from flask import Blueprint, request
from flask_security import auth_required, roles_required, current_user

from models import db, Examination, Slot, Booking, Evaluation, EvaluationScore, Rubric, grade_for
from utils.cache import cached, invalidate_exam_data, TTL_RUBRICS, TTL_SCHEDULE
from utils.helpers import (ApiError, ok, body, require, clean, validate_url, parse_date, parse_time,
                           to_int, to_float, get_or_404, log_activity, notify)
from utils.rules import (slot_creation_open, check_slot_clash, check_slot_in_exam_period,
                         compute_total, STATUS_LABELS)

examiner_bp = Blueprint("examiner", __name__, url_prefix="/api/examiner")


@examiner_bp.before_request
@auth_required("token")
@roles_required("examiner")
def _guard():
    return None


def my_exam(eid):
    exam = get_or_404(Examination, eid, "Examination")
    if current_user not in exam.examiners:
        raise ApiError("You are not assigned to this examination", 403)
    return exam


def my_slot(sid):
    slot = get_or_404(Slot, sid, "Slot")
    if slot.examiner_id != current_user.id:
        raise ApiError("This slot does not belong to you", 403)
    return slot


def my_booking(bid):
    b = get_or_404(Booking, bid, "Booking")
    if not b.slot or b.slot.examiner_id != current_user.id:
        raise ApiError("You can evaluate only students booked into your own slots", 403)
    return b


def _pending(bookings):
    return [b for b in bookings if b.status == "booked"
            and not (b.evaluation and b.evaluation.status == "submitted")]


# ------------------------------------------------------------------ dashboard
@examiner_bp.get("/dashboard")
def dashboard():
    today = date.today()
    exams = current_user.assigned_exams.all()
    slots = Slot.query.filter(Slot.examiner_id == current_user.id, Slot.status != "cancelled").all()
    bookings = [b for s in slots for b in s.active_bookings]
    pending = [b for b in _pending(bookings) if b.slot.date <= today]
    upcoming = sorted([s for s in slots if s.date >= today and s.status in ("available", "full")],
                      key=lambda s: (s.date, s.start_time))[:6]
    todays = [b for b in bookings if b.slot.date == today and b.status == "booked"]
    evals = Evaluation.query.filter_by(examiner_id=current_user.id, status="submitted").all()
    per_exam = Counter(e.exam.name for e in evals)
    next7 = [(today + timedelta(days=i)) for i in range(7)]
    load = [{"date": d.isoformat(), "count": sum(1 for b in bookings if b.slot.date == d)} for d in next7]
    return ok({
        "counts": {
            "assigned_exams": len(exams),
            "slots": len(slots),
            "booked_students": len([b for b in bookings if b.status in ("booked", "completed")]),
            "pending_evaluations": len(pending),
            "evaluated": len(evals),
            "today": len(todays),
        },
        "exams": [dict(e.to_dict(), can_create_slots=slot_creation_open(e)[0],
                       my_slots=len([s for s in slots if s.exam_id == e.id])) for e in exams],
        "upcoming_slots": [s.to_dict() for s in upcoming],
        "pending": [b.to_dict() for b in pending[:8]],
        "today_bookings": [b.to_dict() for b in todays],
        "evaluations_per_exam": [{"exam": k, "count": v} for k, v in per_exam.items()],
        "week_load": load,
    })


@examiner_bp.get("/statistics")
def statistics():
    evals = Evaluation.query.filter_by(examiner_id=current_user.id, status="submitted").all()
    grades = Counter()
    per_exam = {}
    for e in evals:
        pct = e.total_marks / e.exam.max_marks * 100 if e.exam.max_marks else 0
        grades[grade_for(pct)] += 1
        per_exam.setdefault(e.exam.name, []).append(pct)
    slots = Slot.query.filter_by(examiner_id=current_user.id).all()
    return ok({
        "grades": {g: grades.get(g, 0) for g in ["S", "A", "B", "C", "D", "E", "U"]},
        "avg_by_exam": [{"exam": k, "avg_pct": round(sum(v) / len(v), 1), "count": len(v)}
                        for k, v in per_exam.items()],
        "slot_status": dict(Counter(s.status for s in slots)),
        "total_evaluated": len(evals),
        "avg_pct": round(sum(sum(v) for v in per_exam.values()) / len(evals), 1) if evals else 0,
    })


# ------------------------------------------------------------------ exams
@examiner_bp.get("/exams")
def exams():
    out = []
    for e in current_user.assigned_exams.all():
        d = e.to_dict()
        mine = [s for s in e.slots if s.examiner_id == current_user.id and s.status != "cancelled"]
        d["my_slots"] = len(mine)
        d["my_bookings"] = sum(len(s.active_bookings) for s in mine)
        d["can_create_slots"], d["slot_creation_message"] = slot_creation_open(e)
        out.append(d)
    q = (request.args.get("q") or "").lower()
    if q:
        out = [x for x in out if q in x["name"].lower() or q in (x["course_code"] or "").lower()]
    if request.args.get("status"):
        out = [x for x in out if x["status"] == request.args["status"]]
    return ok(out)


@examiner_bp.get("/exams/<int:eid>")
def exam_detail(eid):
    exam = my_exam(eid)
    data = exam.to_dict()
    data["rubrics"] = cached("rubrics", f"exam-{eid}", TTL_RUBRICS, lambda: [r.to_dict() for r in exam.rubrics])
    mine = sorted([s for s in exam.slots if s.examiner_id == current_user.id],
                  key=lambda s: (s.date, s.start_time))
    data["my_slots"] = [s.to_dict(False) for s in mine]
    data["can_create_slots"], data["slot_creation_message"] = slot_creation_open(exam)
    bookings = [b for s in mine for b in s.active_bookings]
    data["summary"] = {"booked": len(bookings), "pending": len(_pending(bookings)),
                       "evaluated": len([b for b in bookings if b.evaluation and b.evaluation.status == "submitted"])}
    return ok(data)


@examiner_bp.post("/exams/<int:eid>/complete")
def complete_exam(eid):
    """Examiner marks the examination completed when every booking is evaluated."""
    exam = my_exam(eid)
    if exam.status not in ("closed", "booking_open"):
        raise ApiError("Only exams whose booking is closed can be marked completed", 409)
    if exam.status == "booking_open":
        raise ApiError("Booking is still open – ask the admin to close booking first", 409)
    active = Booking.query.filter(Booking.exam_id == exam.id, Booking.status == "booked").all()
    pending = _pending(active)
    if pending:
        raise ApiError(f"{len(pending)} student(s) still need evaluation (or mark them absent)", 409)
    exam.status = "completed"
    for s in exam.slots:
        if s.status in ("available", "full"):
            s.status = "completed"
    log_activity("exam_complete", f"Marked {exam.name} completed")
    from models import User, Role
    admin = User.query.join(User.roles).filter(Role.name == "admin").first()
    if admin:
        notify(admin.id, "Examination completed",
               f"{current_user.name} marked {exam.name} as completed – ready to publish results.",
               "success", f"/admin/exams/{exam.id}")
    db.session.commit()
    invalidate_exam_data()
    return ok(exam.to_dict(), "Examination marked as completed")


# ------------------------------------------------------------------ slots
@examiner_bp.get("/slots")
def slots():
    q = Slot.query.filter(Slot.examiner_id == current_user.id)
    if request.args.get("exam_id"):
        q = q.filter(Slot.exam_id == int(request.args["exam_id"]))
    if request.args.get("status"):
        q = q.filter(Slot.status == request.args["status"])
    if request.args.get("when") == "upcoming":
        q = q.filter(Slot.date >= date.today())
    elif request.args.get("when") == "past":
        q = q.filter(Slot.date < date.today())
    key = f"examiner-{current_user.id}-" + "-".join(f"{k}={v}" for k, v in sorted(request.args.items()))
    data = cached("schedule", key, TTL_SCHEDULE,
                  lambda: [s.to_dict() for s in q.order_by(Slot.date, Slot.start_time).all()])
    return ok(data)


def _slot_payload(data, exam):
    require(data, "date", "start_time", "end_time", "capacity")
    day = parse_date(data["date"])
    start = parse_time(data["start_time"], "start_time")
    end = parse_time(data["end_time"], "end_time")
    if start >= end:
        raise ApiError("End time must be after start time", 422, {"end_time": "After start"})
    minutes = (datetime.combine(day, end) - datetime.combine(day, start)).seconds // 60
    if minutes < exam.duration_minutes:
        raise ApiError(f"Slot must be at least the exam duration ({exam.duration_minutes} min)", 422,
                       {"end_time": "Too short"})
    if day < date.today():
        raise ApiError("Slot date cannot be in the past", 422, {"date": "Past date"})
    check_slot_in_exam_period(exam, day)
    mode = data.get("mode") or "online"
    if mode not in ("online", "offline"):
        raise ApiError("Mode must be online or offline", 422)
    link = validate_url(data.get("meeting_link"), "meeting_link")
    venue = clean(data.get("venue"), 150)
    if mode == "offline" and not venue:
        raise ApiError("Venue is required for offline slots", 422, {"venue": "Required"})
    return dict(date=day, start_time=start, end_time=end,
                capacity=to_int(data["capacity"], "capacity", 1, 200),
                mode=mode, meeting_link=link, venue=venue, notes=clean(data.get("notes"), 300))


@examiner_bp.post("/slots")
def create_slot():
    data = body()
    exam = my_exam(to_int(data.get("exam_id"), "exam_id"))
    allowed, msg = slot_creation_open(exam)
    if not allowed:
        raise ApiError(msg, 409)
    p = _slot_payload(data, exam)
    created = []
    # Optional: split a long window into back-to-back slots of exam duration
    if data.get("auto_split"):
        cur = datetime.combine(p["date"], p["start_time"])
        stop = datetime.combine(p["date"], p["end_time"])
        step = timedelta(minutes=exam.duration_minutes)
        while cur + step <= stop:
            s_start, s_end = cur.time(), (cur + step).time()
            check_slot_clash(current_user.id, p["date"], s_start, s_end)
            slot = Slot(exam_id=exam.id, examiner_id=current_user.id,
                        **dict(p, start_time=s_start, end_time=s_end, available_seats=p["capacity"]))
            db.session.add(slot)
            db.session.flush()
            created.append(slot)
            cur += step
    else:
        check_slot_clash(current_user.id, p["date"], p["start_time"], p["end_time"])
        slot = Slot(exam_id=exam.id, examiner_id=current_user.id, available_seats=p["capacity"], **p)
        db.session.add(slot)
        db.session.flush()
        created.append(slot)
    log_activity("slot_create", f"Created {len(created)} slot(s) for {exam.name}")
    db.session.commit()
    invalidate_exam_data()
    return ok([s.to_dict() for s in created], f"{len(created)} slot(s) created", 201)


@examiner_bp.put("/slots/<int:sid>")
def update_slot(sid):
    slot = my_slot(sid)
    allowed, msg = slot_creation_open(slot.exam)
    if not allowed:
        raise ApiError("Slots can be updated only before booking begins. " + msg, 409)
    if slot.active_bookings:
        raise ApiError("This slot already has bookings – contact admin to reschedule", 409)
    p = _slot_payload(body(), slot.exam)
    check_slot_clash(current_user.id, p["date"], p["start_time"], p["end_time"], exclude_id=slot.id)
    for k, v in p.items():
        setattr(slot, k, v)
    slot.available_seats = slot.capacity
    slot.status = "available"
    log_activity("slot_update", f"Updated slot #{slot.id}")
    db.session.commit()
    invalidate_exam_data()
    return ok(slot.to_dict(), "Slot updated")


@examiner_bp.delete("/slots/<int:sid>")
def delete_slot(sid):
    slot = my_slot(sid)
    allowed, msg = slot_creation_open(slot.exam)
    if not allowed:
        raise ApiError("Slots can be removed only before booking begins. " + msg, 409)
    if slot.bookings:
        raise ApiError("Slot has bookings and cannot be removed", 409)
    log_activity("slot_delete", f"Deleted slot #{slot.id} of {slot.exam.name}")
    db.session.delete(slot)
    db.session.commit()
    invalidate_exam_data()
    return ok(message="Slot removed")


@examiner_bp.post("/slots/<int:sid>/complete")
def complete_slot(sid):
    slot = my_slot(sid)
    if slot.date > date.today():
        raise ApiError("A future slot cannot be marked completed", 409)
    pending = _pending(slot.active_bookings)
    if pending:
        raise ApiError(f"Evaluate (or mark absent) {len(pending)} student(s) first", 409)
    slot.status = "completed"
    log_activity("slot_complete", f"Completed slot #{slot.id}")
    db.session.commit()
    invalidate_exam_data()
    return ok(slot.to_dict(), "Slot marked as completed")


@examiner_bp.get("/slots/<int:sid>/bookings")
def slot_bookings(sid):
    slot = my_slot(sid)
    return ok({"slot": slot.to_dict(), "bookings": [b.to_dict() for b in slot.bookings]})


# ------------------------------------------------------------------ students / evaluation
@examiner_bp.get("/students")
def booked_students():
    q = Booking.query.join(Slot).filter(Slot.examiner_id == current_user.id)
    a = request.args
    if a.get("exam_id"):
        q = q.filter(Booking.exam_id == int(a["exam_id"]))
    if a.get("status"):
        q = q.filter(Booking.status == a["status"])
    else:
        q = q.filter(Booking.status != "cancelled")
    rows = [b.to_dict() for b in q.order_by(Slot.date, Slot.start_time).all()]
    if a.get("evaluation") == "pending":
        rows = [r for r in rows if r["status"] == "booked" and r["evaluation_status"] != "submitted"]
    elif a.get("evaluation") == "done":
        rows = [r for r in rows if r["evaluation_status"] == "submitted"]
    if a.get("q"):
        s = a["q"].lower()
        rows = [r for r in rows if s in (r["student_name"] or "").lower()
                or s in (r["roll_no"] or "").lower() or s in (r["exam_name"] or "").lower()]
    return ok(rows)


@examiner_bp.get("/bookings/<int:bid>/evaluation")
def get_evaluation(bid):
    b = my_booking(bid)
    return ok({
        "booking": b.to_dict(),
        "student": b.student.to_dict(),
        "exam": b.exam.to_dict(True),
        "evaluation": b.evaluation.to_dict() if b.evaluation else None,
        "locked": bool(b.exam.results_published),
        "instant_release": bool(b.exam.auto_publish),
        "can_evaluate": b.slot.date <= date.today(),
    })


@examiner_bp.post("/bookings/<int:bid>/evaluation")
def save_evaluation(bid):
    b = my_booking(bid)
    exam = b.exam
    if b.status not in ("booked", "completed"):
        raise ApiError(f"Cannot evaluate a booking with status '{b.status}'", 409)
    if exam.results_published:
        raise ApiError("Results already published – evaluation is locked", 409)
    if b.slot.date > date.today():
        raise ApiError("You can evaluate only after the examination slot has taken place", 409)
    data = body()
    rubrics = {r.id: r for r in exam.rubrics}
    if not rubrics:
        raise ApiError("This examination has no rubric", 409)
    incoming = {int(s.get("rubric_id")): s for s in data.get("scores") or [] if s.get("rubric_id")}
    submit = bool(data.get("submit"))
    errors = {}
    pairs = []
    for rid, r in rubrics.items():
        s = incoming.get(rid)
        if s is None or s.get("marks") in (None, ""):
            if submit:
                errors[str(rid)] = f"Marks required for {r.criterion}"
            continue
        try:
            m = float(s["marks"])
        except (TypeError, ValueError):
            errors[str(rid)] = "Must be a number"
            continue
        if m < 0 or m > r.max_marks:
            errors[str(rid)] = f"{r.criterion}: 0 – {r.max_marks}"
            continue
        pairs.append((r, m, clean(s.get("comment"), 300)))
    if errors:
        raise ApiError("Please correct the rubric marks", 422, errors)
    if submit and not clean(data.get("remarks")):
        raise ApiError("Overall remarks are required to submit", 422, {"remarks": "Required"})

    ev = b.evaluation or Evaluation(booking_id=b.id, student_id=b.student_id, exam_id=exam.id)
    ev.examiner_id = current_user.id
    ev.remarks = clean(data.get("remarks"), 5000)
    ev.strengths = clean(data.get("strengths"), 2000)
    ev.improvements = clean(data.get("improvements"), 2000)
    ev.total_marks = compute_total(exam, [(r, m) for r, m, _ in pairs])
    ev.evaluated_at = datetime.now()
    if not b.evaluation:
        db.session.add(ev)
        db.session.flush()
    for sc in list(ev.scores):
        db.session.delete(sc)
    db.session.flush()
    for r, m, c in pairs:
        db.session.add(EvaluationScore(evaluation_id=ev.id, rubric_id=r.id, marks=m, comment=c))
    was_submitted = ev.status == "submitted"
    if submit:
        ev.status = "submitted"
        b.status = "completed"
        if exam.results_visible:
            # instant result release -> student sees marks right away
            pct = round(ev.total_marks / exam.max_marks * 100, 1)
            notify(b.student_id, "Result updated ✏️" if was_submitted else "Your result is out 🎉",
                   f"{exam.name}: {ev.total_marks}/{exam.max_marks} ({pct}%).", "success",
                   f"/student/results/{b.id}")
        else:
            notify(b.student_id, "Evaluation completed",
                   f"Your {exam.name} has been evaluated. Marks will be visible once the admin publishes results.",
                   "info", "/student/bookings")
    else:
        ev.status = "draft" if ev.status != "submitted" else ev.status
    log_activity("evaluation_" + ("submit" if submit else "draft"),
                 f"{exam.name} – {b.student.name}: {ev.total_marks}")
    db.session.commit()
    invalidate_exam_data()
    if submit:
        from tasks.jobs import send_evaluation_email
        try:
            send_evaluation_email.delay(b.id, was_submitted)
        except Exception:
            pass  # e-mail is best effort – the in-app notification is already stored
    return ok(ev.to_dict(), "Evaluation submitted" if submit else "Draft saved")


@examiner_bp.post("/bookings/<int:bid>/attendance")
def attendance(bid):
    """Mark a student absent / present."""
    b = my_booking(bid)
    present = bool(body().get("present"))
    if b.slot.date > date.today():
        raise ApiError("Attendance can be marked only on/after the slot date", 409)
    if b.evaluation and b.evaluation.status == "submitted":
        raise ApiError("Already evaluated", 409)
    if present:
        if b.status != "absent":
            raise ApiError("Student is not marked absent", 409)
        b.status = "booked"
    else:
        if b.status != "booked":
            raise ApiError("Only booked students can be marked absent", 409)
        b.status = "absent"
        notify(b.student_id, "Marked absent", f"You were marked absent for {b.exam.name}.", "danger",
               "/student/bookings")
    log_activity("attendance", f"{b.student.name} {'present' if present else 'absent'} ({b.exam.name})")
    db.session.commit()
    invalidate_exam_data()
    return ok(b.to_dict(), "Attendance updated")


@examiner_bp.get("/evaluations")
def evaluations():
    evs = (Evaluation.query.filter_by(examiner_id=current_user.id)
           .order_by(Evaluation.evaluated_at.desc()).all())
    out = []
    for e in evs:
        d = e.to_dict()
        d["roll_no"] = e.student.student_profile.roll_no if e.student.student_profile else None
        d["course_code"] = e.exam.course.code
        d["results_published"] = e.exam.results_published
        out.append(d)
    return ok(out)
