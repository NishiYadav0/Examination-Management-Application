"""Database models for the Examination Management Portal.

All tables are created programmatically with ``db.create_all()`` (see app.py).
A single unified ``User`` model is used for Admin / Examiner / Student; the
role is decided through the ``Role`` table (Flask-Security-Too RBAC).
"""
from datetime import datetime, date, time
import uuid

from flask_sqlalchemy import SQLAlchemy
from flask_security import UserMixin, RoleMixin
from sqlalchemy import Index, text

db = SQLAlchemy()

# --------------------------------------------------------------------------
# Constants
# --------------------------------------------------------------------------
EXAM_TYPES = ["Viva", "Practical", "Project Demo", "Assessment"]
EXAM_STATUSES = ["draft", "slot_creation", "booking_open", "closed", "completed"]
SLOT_STATUSES = ["available", "full", "cancelled", "completed"]
BOOKING_STATUSES = ["booked", "cancelled", "completed", "absent"]


def fmt_date(d):
    return d.isoformat() if d else None


def fmt_time(t):
    return t.strftime("%H:%M") if t else None


def fmt_dt(dt):
    return dt.strftime("%Y-%m-%dT%H:%M:%S") if dt else None


# --------------------------------------------------------------------------
# Users & roles
# --------------------------------------------------------------------------
roles_users = db.Table(
    "roles_users",
    db.Column("user_id", db.Integer, db.ForeignKey("user.id", ondelete="CASCADE")),
    db.Column("role_id", db.Integer, db.ForeignKey("role.id", ondelete="CASCADE")),
)


class Role(db.Model, RoleMixin):
    __tablename__ = "role"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    description = db.Column(db.String(255))


class User(db.Model, UserMixin):
    __tablename__ = "user"
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(150), unique=True, nullable=False, index=True)
    password = db.Column(db.String(255), nullable=False)
    name = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(20))
    active = db.Column(db.Boolean, default=True, nullable=False)  # False = blocked
    blocked_reason = db.Column(db.String(255))
    fs_uniquifier = db.Column(db.String(64), unique=True, nullable=False,
                              default=lambda: uuid.uuid4().hex)
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    last_login_at = db.Column(db.DateTime)

    roles = db.relationship("Role", secondary=roles_users,
                            backref=db.backref("users", lazy="dynamic"))
    student_profile = db.relationship("StudentProfile", uselist=False, back_populates="user",
                                      cascade="all, delete-orphan")
    examiner_profile = db.relationship("ExaminerProfile", uselist=False, back_populates="user",
                                       cascade="all, delete-orphan")

    @property
    def role(self):
        return self.roles[0].name if self.roles else None

    def to_dict(self, detailed=False):
        data = {
            "id": self.id,
            "email": self.email,
            "name": self.name,
            "phone": self.phone,
            "role": self.role,
            "active": self.active,
            "blocked_reason": self.blocked_reason,
            "created_at": fmt_dt(self.created_at),
            "last_login_at": fmt_dt(self.last_login_at),
        }
        if self.student_profile:
            data["profile"] = self.student_profile.to_dict()
        elif self.examiner_profile:
            data["profile"] = self.examiner_profile.to_dict()
        else:
            data["profile"] = {}
        return data


class StudentProfile(db.Model):
    __tablename__ = "student_profile"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id", ondelete="CASCADE"), unique=True)
    roll_no = db.Column(db.String(30), unique=True)
    program = db.Column(db.String(100))
    department = db.Column(db.String(100))
    year = db.Column(db.Integer)
    dob = db.Column(db.Date)
    gender = db.Column(db.String(20))
    address = db.Column(db.String(255))
    bio = db.Column(db.String(500))
    user = db.relationship("User", back_populates="student_profile")

    def to_dict(self):
        return {
            "roll_no": self.roll_no, "program": self.program, "department": self.department,
            "year": self.year, "dob": fmt_date(self.dob), "gender": self.gender,
            "address": self.address, "bio": self.bio,
        }


class ExaminerProfile(db.Model):
    __tablename__ = "examiner_profile"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id", ondelete="CASCADE"), unique=True)
    employee_id = db.Column(db.String(30), unique=True)
    department = db.Column(db.String(100))
    designation = db.Column(db.String(100))
    specialization = db.Column(db.String(150))
    office = db.Column(db.String(120))
    bio = db.Column(db.String(500))
    user = db.relationship("User", back_populates="examiner_profile")

    def to_dict(self):
        return {
            "employee_id": self.employee_id, "department": self.department,
            "designation": self.designation, "specialization": self.specialization,
            "office": self.office, "bio": self.bio,
        }


# --------------------------------------------------------------------------
# Academic entities
# --------------------------------------------------------------------------
class Course(db.Model):
    __tablename__ = "course"
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(20), unique=True, nullable=False)
    name = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text)
    department = db.Column(db.String(100))
    credits = db.Column(db.Integer, default=4)
    level = db.Column(db.String(50))  # Foundation / Diploma / Degree
    status = db.Column(db.String(20), default="active")  # active / inactive
    created_at = db.Column(db.DateTime, default=datetime.now)
    exams = db.relationship("Examination", back_populates="course", cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "id": self.id, "code": self.code, "name": self.name,
            "description": self.description, "department": self.department,
            "credits": self.credits, "level": self.level, "status": self.status,
            "created_at": fmt_dt(self.created_at),
            "exam_count": len(self.exams),
        }


exam_examiners = db.Table(
    "exam_examiner",
    db.Column("exam_id", db.Integer, db.ForeignKey("examination.id", ondelete="CASCADE"),
              primary_key=True),
    db.Column("examiner_id", db.Integer, db.ForeignKey("user.id", ondelete="CASCADE"),
              primary_key=True),
)


class Examination(db.Model):
    __tablename__ = "examination"
    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey("course.id", ondelete="CASCADE"), nullable=False)
    name = db.Column(db.String(150), nullable=False)
    exam_type = db.Column(db.String(30), nullable=False, default="Viva")
    description = db.Column(db.Text)
    instructions = db.Column(db.Text)
    duration_minutes = db.Column(db.Integer, nullable=False, default=30)
    max_marks = db.Column(db.Float, nullable=False, default=100)
    pass_marks = db.Column(db.Float, default=40)
    slot_creation_start = db.Column(db.Date)
    slot_creation_end = db.Column(db.Date)
    booking_start = db.Column(db.Date)
    booking_end = db.Column(db.Date)
    exam_start = db.Column(db.Date)  # first day exams may be conducted
    exam_end = db.Column(db.Date)
    status = db.Column(db.String(20), default="draft", nullable=False)
    results_published = db.Column(db.Boolean, default=False)
    published_at = db.Column(db.DateTime)
    requires_submission = db.Column(db.Boolean, default=False)  # ask project link on booking
    # Result release mode: False = student sees marks only after admin publishes (default),
    # True = marks are released to the student as soon as the examiner submits the evaluation
    auto_publish = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)

    course = db.relationship("Course", back_populates="exams")
    examiners = db.relationship("User", secondary=exam_examiners, lazy="subquery",
                                backref=db.backref("assigned_exams", lazy="dynamic"))
    rubrics = db.relationship("Rubric", back_populates="exam", cascade="all, delete-orphan",
                              order_by="Rubric.order")
    slots = db.relationship("Slot", back_populates="exam", cascade="all, delete-orphan")

    @property
    def results_visible(self):
        """Can students see their marks for this exam?"""
        return bool(self.results_published or self.auto_publish)

    @property
    def rubric_weightage(self):
        return round(sum(r.weightage or 0 for r in self.rubrics), 2)

    def to_dict(self, detailed=False):
        data = {
            "id": self.id, "course_id": self.course_id,
            "course_code": self.course.code if self.course else None,
            "course_name": self.course.name if self.course else None,
            "name": self.name, "exam_type": self.exam_type,
            "description": self.description, "instructions": self.instructions,
            "duration_minutes": self.duration_minutes, "max_marks": self.max_marks,
            "pass_marks": self.pass_marks,
            "slot_creation_start": fmt_date(self.slot_creation_start),
            "slot_creation_end": fmt_date(self.slot_creation_end),
            "booking_start": fmt_date(self.booking_start),
            "booking_end": fmt_date(self.booking_end),
            "exam_start": fmt_date(self.exam_start), "exam_end": fmt_date(self.exam_end),
            "status": self.status, "results_published": self.results_published,
            "published_at": fmt_dt(self.published_at),
            "requires_submission": self.requires_submission,
            "auto_publish": bool(self.auto_publish),
            "results_visible": self.results_visible,
            "created_at": fmt_dt(self.created_at),
            "examiners": [{"id": e.id, "name": e.name, "email": e.email,
                           "department": e.examiner_profile.department if e.examiner_profile else None}
                          for e in self.examiners],
            "rubric_count": len(self.rubrics),
            "rubric_weightage": self.rubric_weightage,
            "slot_count": len([s for s in self.slots if s.status != "cancelled"]),
            "total_seats": sum(s.capacity for s in self.slots if s.status != "cancelled"),
            "available_seats": sum(s.available_seats for s in self.slots
                                   if s.status in ("available",)),
        }
        if detailed:
            data["rubrics"] = [r.to_dict() for r in self.rubrics]
        return data


class Rubric(db.Model):
    __tablename__ = "rubric"
    id = db.Column(db.Integer, primary_key=True)
    exam_id = db.Column(db.Integer, db.ForeignKey("examination.id", ondelete="CASCADE"), nullable=False)
    criterion = db.Column(db.String(150), nullable=False)
    max_marks = db.Column(db.Float, nullable=False)
    weightage = db.Column(db.Float, nullable=False)  # percentage of exam max marks
    description = db.Column(db.Text)
    order = db.Column(db.Integer, default=0)
    exam = db.relationship("Examination", back_populates="rubrics")

    def to_dict(self):
        return {"id": self.id, "exam_id": self.exam_id, "criterion": self.criterion,
                "max_marks": self.max_marks, "weightage": self.weightage,
                "description": self.description, "order": self.order}


class Slot(db.Model):
    __tablename__ = "slot"
    id = db.Column(db.Integer, primary_key=True)
    exam_id = db.Column(db.Integer, db.ForeignKey("examination.id", ondelete="CASCADE"), nullable=False)
    examiner_id = db.Column(db.Integer, db.ForeignKey("user.id", ondelete="SET NULL"))
    date = db.Column(db.Date, nullable=False)
    start_time = db.Column(db.Time, nullable=False)
    end_time = db.Column(db.Time, nullable=False)
    capacity = db.Column(db.Integer, nullable=False, default=1)
    available_seats = db.Column(db.Integer, nullable=False, default=1)
    status = db.Column(db.String(20), default="available", nullable=False)
    mode = db.Column(db.String(20), default="online")  # online / offline
    meeting_link = db.Column(db.String(300))
    venue = db.Column(db.String(150))
    notes = db.Column(db.String(300))
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)

    exam = db.relationship("Examination", back_populates="slots")
    examiner = db.relationship("User", foreign_keys=[examiner_id])
    bookings = db.relationship("Booking", back_populates="slot", cascade="all, delete-orphan")

    @property
    def start_dt(self):
        return datetime.combine(self.date, self.start_time)

    @property
    def active_bookings(self):
        return [b for b in self.bookings if b.status != "cancelled"]

    def refresh_seats(self):
        """Recalculate available seats + auto Full / Available status."""
        booked = len(self.active_bookings)
        self.available_seats = max(self.capacity - booked, 0)
        if self.status in ("available", "full"):
            self.status = "full" if self.available_seats == 0 else "available"

    def to_dict(self, with_exam=True):
        data = {
            "id": self.id, "exam_id": self.exam_id, "examiner_id": self.examiner_id,
            "examiner_name": self.examiner.name if self.examiner else None,
            "date": fmt_date(self.date), "start_time": fmt_time(self.start_time),
            "end_time": fmt_time(self.end_time), "capacity": self.capacity,
            "available_seats": self.available_seats, "booked_count": len(self.active_bookings),
            "status": self.status, "mode": self.mode, "meeting_link": self.meeting_link,
            "venue": self.venue, "notes": self.notes,
        }
        if with_exam and self.exam:
            data.update({"exam_name": self.exam.name, "exam_type": self.exam.exam_type,
                         "exam_status": self.exam.status,
                         "course_code": self.exam.course.code if self.exam.course else None})
        return data


class Booking(db.Model):
    __tablename__ = "booking"
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey("user.id", ondelete="CASCADE"), nullable=False)
    slot_id = db.Column(db.Integer, db.ForeignKey("slot.id", ondelete="CASCADE"), nullable=False)
    exam_id = db.Column(db.Integer, db.ForeignKey("examination.id", ondelete="CASCADE"), nullable=False)
    booked_at = db.Column(db.DateTime, default=datetime.now)
    status = db.Column(db.String(20), default="booked", nullable=False)
    submission_link = db.Column(db.String(300))
    student_note = db.Column(db.String(300))
    cancelled_at = db.Column(db.DateTime)
    cancel_reason = db.Column(db.String(255))
    cancelled_by = db.Column(db.String(20))
    reschedule_count = db.Column(db.Integer, default=0)
    admin_note = db.Column(db.String(300))
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)

    student = db.relationship("User", foreign_keys=[student_id])
    slot = db.relationship("Slot", back_populates="bookings")
    exam = db.relationship("Examination")
    evaluation = db.relationship("Evaluation", uselist=False, back_populates="booking",
                                 cascade="all, delete-orphan")

    # A student can have only ONE non-cancelled booking per examination.
    __table_args__ = (
        Index("uq_active_booking_per_exam", "student_id", "exam_id", unique=True,
              sqlite_where=text("status != 'cancelled'")),
    )

    def to_dict(self, show_marks=True):
        s = self.slot
        ev = self.evaluation
        data = {
            "id": self.id, "student_id": self.student_id,
            "student_name": self.student.name if self.student else None,
            "student_email": self.student.email if self.student else None,
            "roll_no": self.student.student_profile.roll_no
            if self.student and self.student.student_profile else None,
            "slot_id": self.slot_id, "exam_id": self.exam_id,
            "exam_name": self.exam.name if self.exam else None,
            "exam_type": self.exam.exam_type if self.exam else None,
            "exam_status": self.exam.status if self.exam else None,
            "course_code": self.exam.course.code if self.exam and self.exam.course else None,
            "course_name": self.exam.course.name if self.exam and self.exam.course else None,
            "max_marks": self.exam.max_marks if self.exam else None,
            "date": fmt_date(s.date) if s else None,
            "start_time": fmt_time(s.start_time) if s else None,
            "end_time": fmt_time(s.end_time) if s else None,
            "examiner_id": s.examiner_id if s else None,
            "examiner_name": s.examiner.name if s and s.examiner else None,
            "meeting_link": s.meeting_link if s else None,
            "mode": s.mode if s else None, "venue": s.venue if s else None,
            "slot_status": s.status if s else None,
            "booked_at": fmt_dt(self.booked_at), "status": self.status,
            "submission_link": self.submission_link, "student_note": self.student_note,
            "cancelled_at": fmt_dt(self.cancelled_at), "cancel_reason": self.cancel_reason,
            "cancelled_by": self.cancelled_by,
            "reschedule_count": self.reschedule_count, "admin_note": self.admin_note,
            "evaluation_status": ev.status if ev else None,
            "results_published": self.exam.results_visible if self.exam else False,
        }
        if show_marks and ev and ev.status == "submitted":
            data["total_marks"] = ev.total_marks
            data["remarks"] = ev.remarks
        return data


class Evaluation(db.Model):
    __tablename__ = "evaluation"
    id = db.Column(db.Integer, primary_key=True)
    booking_id = db.Column(db.Integer, db.ForeignKey("booking.id", ondelete="CASCADE"),
                           unique=True, nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey("user.id", ondelete="CASCADE"), nullable=False)
    examiner_id = db.Column(db.Integer, db.ForeignKey("user.id", ondelete="SET NULL"))
    exam_id = db.Column(db.Integer, db.ForeignKey("examination.id", ondelete="CASCADE"), nullable=False)
    total_marks = db.Column(db.Float, default=0)
    remarks = db.Column(db.Text)
    strengths = db.Column(db.Text)
    improvements = db.Column(db.Text)
    status = db.Column(db.String(20), default="draft")  # draft / submitted
    result_notified = db.Column(db.Boolean, default=False)  # result mail with marks already sent
    evaluated_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)

    booking = db.relationship("Booking", back_populates="evaluation")
    student = db.relationship("User", foreign_keys=[student_id])
    examiner = db.relationship("User", foreign_keys=[examiner_id])
    exam = db.relationship("Examination")
    scores = db.relationship("EvaluationScore", back_populates="evaluation",
                             cascade="all, delete-orphan")

    def to_dict(self):
        exam = self.exam
        pct = round((self.total_marks or 0) / exam.max_marks * 100, 2) if exam and exam.max_marks else 0
        return {
            "id": self.id, "booking_id": self.booking_id, "student_id": self.student_id,
            "student_name": self.student.name if self.student else None,
            "examiner_id": self.examiner_id,
            "examiner_name": self.examiner.name if self.examiner else None,
            "exam_id": self.exam_id, "exam_name": exam.name if exam else None,
            "max_marks": exam.max_marks if exam else None,
            "pass_marks": exam.pass_marks if exam else None,
            "total_marks": self.total_marks, "percentage": pct,
            "grade": grade_for(pct),
            "passed": (self.total_marks or 0) >= (exam.pass_marks or 0) if exam else None,
            "remarks": self.remarks, "strengths": self.strengths,
            "improvements": self.improvements, "status": self.status,
            "evaluated_at": fmt_dt(self.evaluated_at),
            "scores": [sc.to_dict() for sc in self.scores],
        }


def grade_for(pct):
    if pct >= 90: return "S"
    if pct >= 80: return "A"
    if pct >= 70: return "B"
    if pct >= 60: return "C"
    if pct >= 50: return "D"
    if pct >= 40: return "E"
    return "U"


class EvaluationScore(db.Model):
    __tablename__ = "evaluation_score"
    id = db.Column(db.Integer, primary_key=True)
    evaluation_id = db.Column(db.Integer, db.ForeignKey("evaluation.id", ondelete="CASCADE"), nullable=False)
    rubric_id = db.Column(db.Integer, db.ForeignKey("rubric.id", ondelete="CASCADE"), nullable=False)
    marks = db.Column(db.Float, default=0)
    comment = db.Column(db.String(300))
    evaluation = db.relationship("Evaluation", back_populates="scores")
    rubric = db.relationship("Rubric")

    def to_dict(self):
        return {"rubric_id": self.rubric_id,
                "criterion": self.rubric.criterion if self.rubric else None,
                "max_marks": self.rubric.max_marks if self.rubric else None,
                "weightage": self.rubric.weightage if self.rubric else None,
                "marks": self.marks, "comment": self.comment}


# --------------------------------------------------------------------------
# Support, notifications, logs, jobs
# --------------------------------------------------------------------------
class SupportTicket(db.Model):
    __tablename__ = "support_ticket"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id", ondelete="SET NULL"))
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(150), nullable=False)
    subject = db.Column(db.String(200), nullable=False)
    category = db.Column(db.String(50), default="General")
    message = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(20), default="open")  # open / replied / closed
    admin_reply = db.Column(db.Text)
    replied_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.now)
    user = db.relationship("User")

    def to_dict(self):
        return {"id": self.id, "user_id": self.user_id, "name": self.name, "email": self.email,
                "role": self.user.role if self.user else "guest",
                "subject": self.subject, "category": self.category, "message": self.message,
                "status": self.status, "admin_reply": self.admin_reply,
                "replied_at": fmt_dt(self.replied_at), "created_at": fmt_dt(self.created_at)}


class Notification(db.Model):
    __tablename__ = "notification"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id", ondelete="CASCADE"), nullable=False)
    title = db.Column(db.String(150), nullable=False)
    message = db.Column(db.String(500))
    type = db.Column(db.String(30), default="info")  # info/success/warning/danger
    link = db.Column(db.String(200))
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.now)

    def to_dict(self):
        return {"id": self.id, "title": self.title, "message": self.message, "type": self.type,
                "link": self.link, "is_read": self.is_read, "created_at": fmt_dt(self.created_at)}


class ActivityLog(db.Model):
    __tablename__ = "activity_log"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id", ondelete="CASCADE"))
    action = db.Column(db.String(80), nullable=False)
    details = db.Column(db.String(500))
    created_at = db.Column(db.DateTime, default=datetime.now)
    user = db.relationship("User")

    def to_dict(self):
        return {"id": self.id, "user_id": self.user_id,
                "user_name": self.user.name if self.user else None,
                "role": self.user.role if self.user else None,
                "action": self.action, "details": self.details,
                "created_at": fmt_dt(self.created_at)}


class ExportJob(db.Model):
    __tablename__ = "export_job"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id", ondelete="CASCADE"), nullable=False)
    kind = db.Column(db.String(30), default="exam_history")  # what was exported
    task_id = db.Column(db.String(80))
    status = db.Column(db.String(20), default="pending")  # pending / done / failed
    filename = db.Column(db.String(200))
    row_count = db.Column(db.Integer, default=0)
    error = db.Column(db.String(300))
    created_at = db.Column(db.DateTime, default=datetime.now)
    completed_at = db.Column(db.DateTime)

    def to_dict(self):
        from utils.exports import kind_label
        return {"id": self.id, "kind": self.kind, "kind_label": kind_label(self.kind),
                "task_id": self.task_id, "status": self.status,
                "filename": self.filename, "row_count": self.row_count, "error": self.error,
                "created_at": fmt_dt(self.created_at), "completed_at": fmt_dt(self.completed_at)}


class MonthlyReport(db.Model):
    __tablename__ = "monthly_report"
    id = db.Column(db.Integer, primary_key=True)
    month = db.Column(db.String(7), nullable=False)  # YYYY-MM
    filename = db.Column(db.String(200))
    stats_json = db.Column(db.Text)
    emailed = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.now)

    def to_dict(self):
        import json
        return {"id": self.id, "month": self.month, "filename": self.filename,
                "stats": json.loads(self.stats_json or "{}"), "emailed": self.emailed,
                "created_at": fmt_dt(self.created_at)}
