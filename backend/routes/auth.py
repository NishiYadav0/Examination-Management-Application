"""Authentication: student registration, login (all roles), logout, me."""
from datetime import datetime

from flask import Blueprint, current_app
from flask_security import auth_required, current_user, logout_user
from flask_security.utils import hash_password, verify_password

from models import db, User, StudentProfile
from utils.helpers import (ApiError, ok, body, require, clean, validate_email,
                           validate_password, validate_phone, log_activity, notify)

auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")


def auth_payload(user):
    return {"token": user.get_auth_token(), "user": user.to_dict()}


@auth_bp.post("/login")
def login():
    data = body()
    require(data, "email", "password")
    email = data["email"].strip().lower()
    user = current_app.security.datastore.find_user(email=email)
    if not user or not verify_password(data["password"], user.password):
        raise ApiError("Invalid e-mail or password", 401)
    if not user.active:
        reason = f" Reason: {user.blocked_reason}." if user.blocked_reason else ""
        raise ApiError(f"Your account has been blocked by the admin.{reason} "
                       "Please contact support.", 403)
    if data.get("role") and data["role"] != user.role:
        raise ApiError(f"This account is not registered as {data['role']}", 403)
    user.last_login_at = datetime.now()
    log_activity("login", "Logged in", user_id=user.id)
    db.session.commit()
    return ok(auth_payload(user), "Login successful")


@auth_bp.post("/register")
def register():
    """Only students can self-register."""
    data = body()
    require(data, "name", "email", "password", "roll_no")
    email = validate_email(data["email"])
    validate_password(data["password"])
    if data.get("confirm_password") is not None and data["confirm_password"] != data["password"]:
        raise ApiError("Passwords do not match", 422, {"confirm_password": "Does not match"})
    ds = current_app.security.datastore
    if ds.find_user(email=email):
        raise ApiError("An account with this e-mail already exists", 409, {"email": "Already registered"})
    roll_no = clean(data["roll_no"], 30).upper()
    if StudentProfile.query.filter_by(roll_no=roll_no).first():
        raise ApiError("This roll number is already registered", 409, {"roll_no": "Already registered"})
    user = ds.create_user(email=email, password=hash_password(data["password"]),
                          name=clean(data["name"], 120), phone=validate_phone(data.get("phone")),
                          roles=["student"])
    db.session.flush()
    year = data.get("year")
    db.session.add(StudentProfile(user_id=user.id, roll_no=roll_no,
                                  program=clean(data.get("program"), 100),
                                  department=clean(data.get("department"), 100),
                                  year=int(year) if str(year or "").isdigit() else None))
    notify(user.id, "Welcome to EMP 🎓",
           "Your student account is ready. Browse examinations and book your slot.", "success",
           "/student/exams")
    log_activity("register", "Student self-registered", user_id=user.id)
    db.session.commit()
    return ok(auth_payload(user), "Registration successful", 201)


@auth_bp.get("/me")
@auth_required("token")
def me():
    return ok(current_user.to_dict())


@auth_bp.post("/logout")
@auth_required("token")
def logout():
    log_activity("logout", "Logged out")
    db.session.commit()
    logout_user()
    return ok(message="Logged out")
