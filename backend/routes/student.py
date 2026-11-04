"""Student API – browse/search exams, book & cancel slots, results, CSV export."""
import os
from collections import Counter
from datetime import date, datetime

from flask import Blueprint, request, current_app, send_file
from flask_security import auth_required, roles_required, current_user
from sqlalchemy import or_
from sqlalchemy.exc import IntegrityError

from models import db, Course, Examination, Slot, Booking, ExportJob, grade_for
from utils.cache import cached, invalidate_exam_data, TTL_EXAMS, TTL_SCHEDULE, TTL_RUBRICS
from utils.helpers import ApiError, ok, body, clean, validate_url, get_or_404, log_activity, notify, like
from utils.rules import booking_open, cancel_booking

student_bp = Blueprint("student", __name__, url_prefix="/api/student")


@student_bp.before_request
@auth_required("token")
@roles_required("student")
def _guard():
    return None


def _my_active_bookings():
    return {b.exam_id: b for b in Booking.query.filter(Booking.student_id == current_user.id,
                                                       Booking.status != "cancelled").all()}


def _visible_exams():
    """Cached list of exams visible to students (everything except Draft)."""
    def produce():
        exams = (Examination.query.join(Course).filter(Examination.status != "draft",
                                                       Course.status == "active")
                 .order_by(Examination.booking_end.asc()).all())
        return [e.to_dict() for e in exams]
    return cached("exams", "student-visible", TTL_EXAMS, produce)


# ------------------------------------------------------------------ dashboard
@student_bp.get("/dashboard")
def dashboard():
    today = date.today()
    exams = _visible_exams()
    mine = _my_active_bookings()
    bookings = Booking.query.filter_by(student_id=current_user.id).all()
    open_exams = [e for e in exams if e["status"] == "booking_open" and e["id"] not in mine]
    upcoming = sorted([b for b in bookings if b.status == "booked" and b.slot.date >= today],
                      key=lambda b: (b.slot.date, b.slot.start_time))
    results = [b for b in bookings if b.exam.results_visible and b.evaluation
               and b.evaluation.status == "submitted"]
    return ok({
        "counts": {
            "available_exams": len(open_exams),
            "available_slots": sum(e["available_seats"] for e in open_exams),
            "upcoming": len(upcoming),
            "booked": len([b for b in bookings if b.status == "booked"]),
            "completed": len([b for b in bookings if b.status == "completed"]),
            "results": len(results),
        },
        "available_exams": open_exams[:6],
        "upcoming": [b.to_dict(show_marks=False) for b in upcoming[:5]],
        "next_exam": upcoming[0].to_dict(show_marks=False) if upcoming else None,
        "results": [dict(b.to_dict(), grade=grade_for(b.evaluation.total_marks / b.exam.max_marks * 100),
                         percentage=round(b.evaluation.total_marks / b.exam.max_marks * 100, 1))
                    for b in sorted(results, key=lambda x: x.exam.published_at or x.evaluation.evaluated_at or datetime.min,
                                    reverse=True)[:5]],
        "performance": [{"exam": b.exam.name,
                         "pct": round(b.evaluation.total_marks / b.exam.max_marks * 100, 1)} for b in results],
    })


@student_bp.get("/statistics")
def statistics():
    bookings = Booking.query.filter_by(student_id=current_user.id).all()
    results = [b for b in bookings if b.exam.results_visible and b.evaluation
               and b.evaluation.status == "submitted"]
    pcts = [b.evaluation.total_marks / b.exam.max_marks * 100 for b in results]
    return ok({
        "status": dict(Counter(b.status for b in bookings)),
        "by_type": dict(Counter(b.exam.exam_type for b in bookings if b.status != "cancelled")),
        "performance": [{"exam": b.exam.name, "pct": round(p, 1), "type": b.exam.exam_type}
                        for b, p in zip(results, pcts)],
        "grades": dict(Counter(grade_for(p) for p in pcts)),
        "avg_pct": round(sum(pcts) / len(pcts), 1) if pcts else 0,
        "best": round(max(pcts), 1) if pcts else 0,
        "passed": sum(1 for b in results if b.evaluation.total_marks >= (b.exam.pass_marks or 0)),
        "total_results": len(results),
    })


# ------------------------------------------------------------------ exams
@student_bp.get("/exams")
def exams():
    a = request.args
    items = _visible_exams()
    mine = _my_active_bookings()
    if a.get("q"):
        s = a["q"].lower()
        items = [e for e in items if s in e["name"].lower() or s in (e["course_code"] or "").lower()
                 or s in (e["course_name"] or "").lower() or s in e["exam_type"].lower()]
    if a.get("exam_type"):
        items = [e for e in items if e["exam_type"] == a["exam_type"]]
    if a.get("course_id"):
        items = [e for e in items if str(e["course_id"]) == a["course_id"]]
    if a.get("status"):
        items = [e for e in items if e["status"] == a["status"]]
    out = []
    for e in items:
        b = mine.get(e["id"])
        d = dict(e)
        d["my_booking"] = {"id": b.id, "status": b.status, "date": b.slot.date.isoformat(),
                           "start_time": b.slot.start_time.strftime("%H:%M")} if b else None
        d["can_book"] = e["status"] == "booking_open" and not b and e["available_seats"] > 0
        out.append(d)
    if a.get("availability") == "bookable":
        out = [e for e in out if e["can_book"]]
    elif a.get("availability") == "booked":
        out = [e for e in out if e["my_booking"]]
    return ok(out)


@student_bp.get("/exams/<int:eid>")
def exam_detail(eid):
    exam = get_or_404(Examination, eid, "Examination")
    if exam.status == "draft":
        raise ApiError("Examination not found", 404)
    data = cached("exams", f"detail-{eid}", TTL_EXAMS, lambda: exam.to_dict())
    data = dict(data)
    data["rubrics"] = cached("rubrics", f"exam-{eid}", TTL_RUBRICS, lambda: [r.to_dict() for r in exam.rubrics])

    def schedule():
        slots = (Slot.query.filter(Slot.exam_id == eid, Slot.status.in_(["available", "full"]),
                                   Slot.date >= date.today())
                 .order_by(Slot.date, Slot.start_time).all())
        return [s.to_dict(False) for s in slots]
    now = datetime.now().strftime("%Y-%m-%dT%H:%M")
    # hide slots that already started today (cache may be up to TTL old, so filter here)
    data["slots"] = [s for s in cached("schedule", f"exam-{eid}", TTL_SCHEDULE, schedule)
                     if f"{s['date']}T{s['start_time']}" > now]
    b = _my_active_bookings().get(eid)
    data["my_booking"] = b.to_dict(show_marks=False) if b else None
    data["booking_allowed"], data["booking_message"] = booking_open(exam)
    return ok(data)


# ------------------------------------------------------------------ bookings
@student_bp.post("/bookings")
def book_slot():
    data = body()
    slot = get_or_404(Slot, int(data.get("slot_id") or 0), "Slot")
    exam = slot.exam
    allowed, msg = booking_open(exam)
    if not allowed:
        raise ApiError(msg, 409)
    if slot.status != "available":
        raise ApiError(f"This slot is {slot.status} – please pick another one", 409)
    if slot.start_dt <= datetime.now():
        raise ApiError("This slot has already started", 409)
    if Booking.query.filter(Booking.student_id == current_user.id, Booking.exam_id == exam.id,
                            Booking.status != "cancelled").first():
        raise ApiError("You already have a booking for this examination (one slot per exam)", 409)
    # personal clash – student can't be in two exams at the same time
    clash = (Booking.query.join(Slot).filter(Booking.student_id == current_user.id,
                                              Booking.status == "booked", Slot.date == slot.date,
                                              Slot.start_time < slot.end_time,
                                              Slot.end_time > slot.start_time).first())
    if clash:
        raise ApiError(f"You already have {clash.exam.name} at this time", 409)
    link = validate_url(data.get("submission_link"), "submission_link")
    if exam.requires_submission and not link:
        raise ApiError("This examination requires a project/submission link", 422,
                       {"submission_link": "Required"})
    # Atomic seat decrement – prevents overbooking even with concurrent requests
    updated = (Slot.query.filter(Slot.id == slot.id, Slot.available_seats > 0, Slot.status == "available")
               .update({Slot.available_seats: Slot.available_seats - 1}, synchronize_session=False))
    if not updated:
        db.session.rollback()
        raise ApiError("Sorry, this slot just became full", 409)
    booking = Booking(student_id=current_user.id, slot_id=slot.id, exam_id=exam.id,
                      submission_link=link, student_note=clean(data.get("note"), 300))
    db.session.add(booking)
    try:
        db.session.flush()
    except IntegrityError:
        db.session.rollback()
        raise ApiError("Duplicate booking for this examination is not allowed", 409)
    db.session.refresh(slot)
    slot.refresh_seats()  # auto-mark FULL at capacity
    notify(current_user.id, "Slot booked ✅",
           f"{exam.name} on {slot.date} at {slot.start_time.strftime('%H:%M')} with "
           f"{slot.examiner.name if slot.examiner else 'TBA'}.", "success", "/student/bookings")
    if slot.examiner_id:
        notify(slot.examiner_id, "New booking",
               f"{current_user.name} booked your {exam.name} slot on {slot.date}.", "info",
               "/examiner/students")
    log_activity("booking_create", f"Booked {exam.name} ({slot.date} {slot.start_time.strftime('%H:%M')})")
    db.session.commit()
    invalidate_exam_data()
    from tasks.jobs import send_booking_email
    try:
        send_booking_email.delay(booking.id, "booked")
    except Exception:
        current_app.logger.warning("Celery unavailable – booking e-mail skipped")
    return ok(booking.to_dict(), "Slot booked successfully", 201)


@student_bp.get("/bookings")
def my_bookings():
    q = Booking.query.filter_by(student_id=current_user.id)
    if request.args.get("status"):
        q = q.filter(Booking.status == request.args["status"])
    rows = []
    for b in q.order_by(Booking.booked_at.desc()).all():
        d = b.to_dict(show_marks=b.exam.results_visible)
        d["can_cancel"] = _can_cancel(b)[0]
        rows.append(d)
    if request.args.get("q"):
        s = request.args["q"].lower()
        rows = [r for r in rows if s in r["exam_name"].lower() or s in (r["course_code"] or "").lower()]
    return ok(rows)


def _can_cancel(b):
    if b.status != "booked":
        return False, "Only active bookings can be cancelled"
    if b.exam.booking_end and date.today() > b.exam.booking_end:
        return False, f"Booking deadline ({b.exam.booking_end}) has passed"
    if b.slot.start_dt <= datetime.now():
        return False, "The examination slot has already started"
    return True, ""


@student_bp.post("/bookings/<int:bid>/cancel")
def cancel(bid):
    b = get_or_404(Booking, bid, "Booking")
    if b.student_id != current_user.id:
        raise ApiError("Not your booking", 403)
    allowed, msg = _can_cancel(b)
    if not allowed:
        raise ApiError(msg, 409)
    cancel_booking(b, "student", clean(body().get("reason"), 255))
    notify(current_user.id, "Booking cancelled", f"You cancelled {b.exam.name} on {b.slot.date}.",
           "warning", "/student/bookings")
    if b.slot.examiner_id:
        notify(b.slot.examiner_id, "Booking cancelled",
               f"{current_user.name} cancelled the {b.exam.name} slot on {b.slot.date}.", "warning",
               "/examiner/students")
    log_activity("booking_cancel", f"Cancelled {b.exam.name}")
    db.session.commit()
    invalidate_exam_data()
    from tasks.jobs import send_booking_email
    try:
        send_booking_email.delay(b.id, "cancelled")
    except Exception:
        pass
    return ok(b.to_dict(), "Booking cancelled – the seat has been released")


@student_bp.put("/bookings/<int:bid>/submission")
def update_submission(bid):
    b = get_or_404(Booking, bid, "Booking")
    if b.student_id != current_user.id or b.status != "booked":
        raise ApiError("Cannot update this booking", 409)
    b.submission_link = validate_url(body().get("submission_link"), "submission_link")
    db.session.commit()
    return ok(b.to_dict(), "Submission link updated")


# ------------------------------------------------------------------ results
@student_bp.get("/results")
def results():
    rows = []
    for b in Booking.query.filter_by(student_id=current_user.id).all():
        if b.exam.results_visible and b.evaluation and b.evaluation.status == "submitted":
            ev = b.evaluation.to_dict()
            rows.append(dict(b.to_dict(), evaluation=ev, percentage=ev["percentage"],
                             grade=ev["grade"], passed=ev["passed"],
                             published_at=(b.exam.published_at or b.evaluation.evaluated_at).isoformat()))
    rows.sort(key=lambda r: r["published_at"] or "", reverse=True)
    return ok(rows)


@student_bp.get("/results/<int:bid>")
def result_detail(bid):
    b = get_or_404(Booking, bid, "Result")
    if b.student_id != current_user.id:
        raise ApiError("Not your result", 403)
    if not (b.exam.results_visible and b.evaluation and b.evaluation.status == "submitted"):
        raise ApiError("Result is not published yet", 404)
    return ok({"booking": b.to_dict(), "evaluation": b.evaluation.to_dict(),
               "exam": b.exam.to_dict(True), "student": current_user.to_dict()})


# ------------------------------------------------------------------ CSV export (Celery)
# Kept for backwards compatibility – the generic endpoints live in routes/common.py
@student_bp.post("/exports")
def start_export():
    from routes.common import queue_export
    return queue_export("exam_history")
