"""Endpoints shared by every logged-in role: profile, password, notifications, tickets."""
import os

from flask import Blueprint, current_app, send_file
from flask_security import auth_required, current_user
from flask_security.utils import hash_password, verify_password

from models import db, Notification, SupportTicket, ActivityLog, ExportJob
from utils.helpers import (ApiError, ok, body, require, clean, validate_phone, validate_password,
                           parse_date, log_activity)

common_bp = Blueprint("common", __name__, url_prefix="/api")


def apply_profile_update(user, data, admin=False):
    """Update user + role profile from JSON (used by self-service and admin)."""
    if "name" in data:
        if not clean(data.get("name")):
            raise ApiError("Name cannot be empty", 422, {"name": "Required"})
        user.name = clean(data["name"], 120)
    if "phone" in data:
        user.phone = validate_phone(data.get("phone"))
    p = user.student_profile or user.examiner_profile
    if user.student_profile:
        for f in ("program", "department", "gender", "address", "bio"):
            if f in data:
                setattr(p, f, clean(data.get(f), 500))
        if "year" in data:
            y = data.get("year")
            p.year = int(y) if str(y or "").isdigit() else None
        if "dob" in data:
            p.dob = parse_date(data.get("dob"), "dob", required=False)
        if admin and data.get("roll_no"):
            p.roll_no = clean(data["roll_no"], 30).upper()
    elif user.examiner_profile:
        for f in ("department", "designation", "specialization", "office", "bio"):
            if f in data:
                setattr(p, f, clean(data.get(f), 500))
        if admin and data.get("employee_id"):
            p.employee_id = clean(data["employee_id"], 30).upper()
    if admin and data.get("email"):
        from utils.helpers import validate_email
        from models import User
        email = validate_email(data["email"])
        other = User.query.filter(User.email == email, User.id != user.id).first()
        if other:
            raise ApiError("E-mail already used by another account", 409, {"email": "Taken"})
        user.email = email


@common_bp.get("/profile")
@auth_required("token")
def get_profile():
    return ok(current_user.to_dict())


@common_bp.put("/profile")
@auth_required("token")
def update_profile():
    apply_profile_update(current_user, body())
    log_activity("profile_update", "Updated own profile")
    db.session.commit()
    return ok(current_user.to_dict(), "Profile updated")


@common_bp.post("/profile/change-password")
@auth_required("token")
def change_password():
    data = body()
    require(data, "current_password", "new_password")
    if not verify_password(data["current_password"], current_user.password):
        raise ApiError("Current password is incorrect", 422, {"current_password": "Incorrect"})
    validate_password(data["new_password"], "new_password")
    current_user.password = hash_password(data["new_password"])
    log_activity("password_change", "Changed password")
    db.session.commit()
    return ok(message="Password changed successfully")


@common_bp.get("/profile/activity")
@auth_required("token")
def my_activity():
    logs = (ActivityLog.query.filter_by(user_id=current_user.id)
            .order_by(ActivityLog.created_at.desc()).limit(50).all())
    return ok([l.to_dict() for l in logs])


# ---------------- Notifications ----------------
@common_bp.get("/notifications")
@auth_required("token")
def notifications():
    items = (Notification.query.filter_by(user_id=current_user.id)
             .order_by(Notification.created_at.desc()).limit(100).all())
    unread = Notification.query.filter_by(user_id=current_user.id, is_read=False).count()
    return ok({"items": [n.to_dict() for n in items], "unread": unread})


@common_bp.post("/notifications/<int:nid>/read")
@auth_required("token")
def read_notification(nid):
    n = Notification.query.filter_by(id=nid, user_id=current_user.id).first()
    if not n:
        raise ApiError("Notification not found", 404)
    n.is_read = True
    db.session.commit()
    return ok(message="Marked as read")


@common_bp.post("/notifications/read-all")
@auth_required("token")
def read_all():
    Notification.query.filter_by(user_id=current_user.id, is_read=False).update({"is_read": True})
    db.session.commit()
    return ok(message="All notifications marked as read")


@common_bp.delete("/notifications/<int:nid>")
@auth_required("token")
def delete_notification(nid):
    Notification.query.filter_by(id=nid, user_id=current_user.id).delete()
    db.session.commit()
    return ok(message="Deleted")


# ---------------- My support tickets ----------------
@common_bp.get("/my/tickets")
@auth_required("token")
def my_tickets():
    tickets = (SupportTicket.query
               .filter((SupportTicket.user_id == current_user.id) |
                       (SupportTicket.email == current_user.email))
               .order_by(SupportTicket.created_at.desc()).all())
    return ok([t.to_dict() for t in tickets])


# ---------------- "Export my data" (all roles, Celery background job) ----------------
def queue_export(kind):
    """Create an ExportJob for the current user and hand it to Celery."""
    from utils.exports import allowed, kind_label
    from tasks.jobs import generate_user_export
    if not allowed(kind, current_user.role):
        raise ApiError("This export is not available for your role", 403)
    if ExportJob.query.filter_by(user_id=current_user.id, status="pending", kind=kind).count() >= 3:
        raise ApiError("You already have exports in progress – please wait a moment", 429)
    job = ExportJob(user_id=current_user.id, status="pending", kind=kind)
    db.session.add(job)
    db.session.commit()
    try:
        res = generate_user_export.delay(job.id)
    except Exception as exc:
        job.status, job.error = "failed", "Background worker unavailable"
        db.session.commit()
        raise ApiError(f"Background worker (Celery/Redis) is not running: {exc}", 503)
    job.task_id = res.id
    log_activity("export_request", f"Requested CSV export: {kind_label(kind)}")
    db.session.commit()
    return ok(job.to_dict(), "Export started – you'll be notified when it is ready", 202)


@common_bp.get("/exports/kinds")
@auth_required("token")
def export_kinds():
    from utils.exports import kinds_for
    return ok(kinds_for(current_user.role))


@common_bp.post("/exports")
@auth_required("token")
def create_export():
    kind = (body().get("kind") or "full").strip()
    return queue_export(kind)


def _my_job(jid):
    job = ExportJob.query.filter_by(id=jid, user_id=current_user.id).first()
    if not job:
        raise ApiError("Export not found", 404)
    return job


# the same list/status/download routes are exposed under /api/exports and /api/student/exports
@common_bp.get("/exports")
@common_bp.get("/student/exports")
@auth_required("token")
def list_exports():
    jobs = (ExportJob.query.filter_by(user_id=current_user.id)
            .order_by(ExportJob.created_at.desc()).limit(30).all())
    return ok([j.to_dict() for j in jobs])


@common_bp.get("/exports/<int:jid>")
@common_bp.get("/student/exports/<int:jid>")
@auth_required("token")
def export_status(jid):
    return ok(_my_job(jid).to_dict())


@common_bp.get("/exports/<int:jid>/download")
@common_bp.get("/student/exports/<int:jid>/download")
@auth_required("token")
def download_export(jid):
    job = _my_job(jid)
    if job.status != "done":
        raise ApiError("Export is not ready", 404)
    path = os.path.join(current_app.config["EXPORT_DIR"], job.filename)
    if not os.path.exists(path):
        raise ApiError("File no longer exists – please export again", 404)
    return send_file(path, mimetype="text/csv", as_attachment=True, download_name=job.filename)
