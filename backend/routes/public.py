"""Public (no login) endpoints: landing page stats, courses, contact form."""
from datetime import date

from flask import Blueprint
from flask_security import current_user

from models import db, User, Role, Course, Examination, Booking, Evaluation, SupportTicket, Slot
from utils.cache import cached, TTL_STATS
from utils.helpers import ok, body, require, clean, validate_email, notify

public_bp = Blueprint("public", __name__, url_prefix="/api/public")


def _count_role(name):
    return User.query.join(User.roles).filter(Role.name == name).count()


@public_bp.get("/stats")
def stats():
    def produce():
        return {
            "courses": Course.query.filter_by(status="active").count(),
            "examinations": Examination.query.filter(Examination.status != "draft").count(),
            "students": _count_role("student"),
            "examiners": _count_role("examiner"),
            "bookings": Booking.query.count(),
            "evaluations": Evaluation.query.filter_by(status="submitted").count(),
        }
    return ok(cached("stats", "public", TTL_STATS, produce))


@public_bp.get("/upcoming")
def upcoming():
    """A few open / upcoming examinations to showcase on the home page."""
    def produce():
        exams = (Examination.query
                 .filter(Examination.status.in_(["slot_creation", "booking_open"]))
                 .order_by(Examination.booking_start.asc()).limit(6).all())
        return [{"id": e.id, "name": e.name, "exam_type": e.exam_type,
                 "course_code": e.course.code, "course_name": e.course.name,
                 "status": e.status, "booking_start": e.booking_start.isoformat() if e.booking_start else None,
                 "booking_end": e.booking_end.isoformat() if e.booking_end else None,
                 "duration_minutes": e.duration_minutes} for e in exams]
    return ok(cached("exams", "public-upcoming", 120, produce))


@public_bp.get("/courses")
def courses():
    def produce():
        return [c.to_dict() for c in Course.query.filter_by(status="active").order_by(Course.code).all()]
    return ok(cached("exams", "public-courses", 300, produce))


@public_bp.post("/contact")
def contact():
    """Contact form – works for guests and logged-in users."""
    data = body()
    user = current_user if current_user and current_user.is_authenticated else None
    if user:
        data.setdefault("name", user.name)
        data.setdefault("email", user.email)
    require(data, "name", "email", "subject", "message")
    ticket = SupportTicket(
        user_id=user.id if user else None,
        name=clean(data["name"], 120), email=validate_email(data["email"]),
        subject=clean(data["subject"], 200), category=clean(data.get("category"), 50) or "General",
        message=clean(data["message"], 5000))
    db.session.add(ticket)
    admin = User.query.join(User.roles).filter(Role.name == "admin").first()
    if admin:
        notify(admin.id, "New support ticket", f"{ticket.name}: {ticket.subject}", "info",
               "/admin/support")
    db.session.commit()
    return ok(ticket.to_dict(), "Thanks! Your message has been received. We'll reply soon.", 201)
