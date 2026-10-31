"""Common helpers: JSON responses, validation, logging, notifications."""
import re
from datetime import datetime, date

from flask import request, jsonify
from flask_security import current_user

from models import db, ActivityLog, Notification

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[a-zA-Z]{2,}$")
PHONE_RE = re.compile(r"^[0-9+\-\s]{7,15}$")
URL_RE = re.compile(r"^https?://[^\s]+$")


class ApiError(Exception):
    def __init__(self, message, status=400, errors=None):
        super().__init__(message)
        self.message, self.status, self.errors = message, status, errors or {}


def ok(data=None, message=None, status=200):
    payload = {}
    if message:
        payload["message"] = message
    if data is not None:
        payload["data"] = data
    return jsonify(payload), status


def body():
    return request.get_json(silent=True) or {}


def require(data, *fields):
    missing = {f: "This field is required" for f in fields
               if data.get(f) in (None, "") or (isinstance(data.get(f), str) and not data.get(f).strip())}
    if missing:
        raise ApiError("Please fill all required fields", 422, missing)


def clean(value, max_len=None):
    if value is None:
        return None
    value = str(value).strip()
    if max_len:
        value = value[:max_len]
    return value or None


def parse_date(value, field="date", required=True):
    if not value:
        if required:
            raise ApiError(f"{field} is required", 422, {field: "Required"})
        return None
    if isinstance(value, date):
        return value
    try:
        return datetime.strptime(str(value)[:10], "%Y-%m-%d").date()
    except ValueError:
        raise ApiError(f"Invalid {field} (expected YYYY-MM-DD)", 422, {field: "Invalid date"})


def parse_time(value, field="time"):
    try:
        return datetime.strptime(str(value)[:5], "%H:%M").time()
    except (ValueError, TypeError):
        raise ApiError(f"Invalid {field} (expected HH:MM)", 422, {field: "Invalid time"})


def to_int(value, field, minimum=None, maximum=None):
    try:
        v = int(value)
    except (TypeError, ValueError):
        raise ApiError(f"{field} must be a whole number", 422, {field: "Must be a number"})
    if minimum is not None and v < minimum:
        raise ApiError(f"{field} must be at least {minimum}", 422, {field: f"Min {minimum}"})
    if maximum is not None and v > maximum:
        raise ApiError(f"{field} must be at most {maximum}", 422, {field: f"Max {maximum}"})
    return v


def to_float(value, field, minimum=None, maximum=None):
    try:
        v = float(value)
    except (TypeError, ValueError):
        raise ApiError(f"{field} must be a number", 422, {field: "Must be a number"})
    if minimum is not None and v < minimum:
        raise ApiError(f"{field} must be ≥ {minimum}", 422, {field: f"Min {minimum}"})
    if maximum is not None and v > maximum:
        raise ApiError(f"{field} must be ≤ {maximum}", 422, {field: f"Max {maximum}"})
    return v


def validate_email(email):
    if not email or not EMAIL_RE.match(email):
        raise ApiError("Please enter a valid e-mail address", 422, {"email": "Invalid e-mail"})
    return email.strip().lower()


def validate_password(pw, field="password"):
    if not pw or len(pw) < 6:
        raise ApiError("Password must be at least 6 characters", 422, {field: "Min 6 characters"})
    return pw


def validate_phone(phone):
    if phone and not PHONE_RE.match(phone):
        raise ApiError("Invalid phone number", 422, {"phone": "Invalid phone"})
    return clean(phone, 20)


def validate_url(url, field="url"):
    url = clean(url, 300)
    if url and not URL_RE.match(url):
        raise ApiError(f"{field} must start with http:// or https://", 422, {field: "Invalid URL"})
    return url


def get_or_404(model, obj_id, label="Record"):
    obj = db.session.get(model, obj_id)
    if not obj:
        raise ApiError(f"{label} not found", 404)
    return obj


def log_activity(action, details=None, user_id=None):
    uid = user_id or (current_user.id if current_user and current_user.is_authenticated else None)
    db.session.add(ActivityLog(user_id=uid, action=action, details=(details or "")[:500]))


def notify(user_id, title, message=None, type_="info", link=None):
    db.session.add(Notification(user_id=user_id, title=title, message=message,
                                type=type_, link=link))


def like(q):
    return f"%{q.strip()}%"
