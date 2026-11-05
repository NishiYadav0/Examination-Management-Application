"""Core examination business rules shared by admin / examiner / student APIs."""
from datetime import date, datetime

from models import db, Slot, Booking
from utils.helpers import ApiError, notify

STATUS_LABELS = {
    "draft": "Draft", "slot_creation": "Slot Creation", "booking_open": "Booking Open",
    "closed": "Closed", "completed": "Completed",
}


def today():
    return date.today()


def in_window(start, end, day=None):
    day = day or today()
    return bool(start and end and start <= day <= end)


def slot_creation_open(exam):
    """Examiners may create/edit slots only when admin opened the window AND today is in it."""
    if exam.status != "slot_creation":
        return False, f"Slot creation is not open for this examination (status: {STATUS_LABELS.get(exam.status)})"
    if not in_window(exam.slot_creation_start, exam.slot_creation_end):
        return False, (f"Slot creation period is {exam.slot_creation_start} to "
                       f"{exam.slot_creation_end}; today is outside this period")
    return True, ""


def booking_open(exam):
    if exam.status != "booking_open":
        return False, f"Slot booking is not open for this examination (status: {STATUS_LABELS.get(exam.status)})"
    if not in_window(exam.booking_start, exam.booking_end):
        return False, (f"Booking period is {exam.booking_start} to {exam.booking_end}; "
                       "today is outside this period")
    return True, ""


def validate_timeline(exam):
    """Check that configured dates are in a sensible order."""
    pairs = [("slot_creation_start", "slot_creation_end", "Slot creation"),
             ("booking_start", "booking_end", "Booking"),
             ("exam_start", "exam_end", "Examination")]
    for s, e, label in pairs:
        sv, ev = getattr(exam, s), getattr(exam, e)
        if sv and ev and sv > ev:
            raise ApiError(f"{label} start date must be on/before its end date", 422, {e: "Before start"})
    if exam.slot_creation_start and exam.booking_start and exam.booking_start < exam.slot_creation_start:
        raise ApiError("Booking cannot start before slot creation starts", 422,
                       {"booking_start": "Too early"})
    if exam.booking_end and exam.exam_end and exam.exam_end < exam.booking_start:
        raise ApiError("Examination period must end after booking starts", 422, {"exam_end": "Too early"})


def check_slot_clash(examiner_id, day, start, end, exclude_id=None):
    if start >= end:
        raise ApiError("End time must be after start time", 422, {"end_time": "Must be after start"})
    q = Slot.query.filter(Slot.examiner_id == examiner_id, Slot.date == day,
                          Slot.status != "cancelled",
                          Slot.start_time < end, Slot.end_time > start)
    if exclude_id:
        q = q.filter(Slot.id != exclude_id)
    clash = q.first()
    if clash:
        raise ApiError(
            f"Time clash with another slot of this examiner ({clash.exam.name}, "
            f"{clash.start_time.strftime('%H:%M')}–{clash.end_time.strftime('%H:%M')})", 409)


def check_slot_in_exam_period(exam, day):
    if exam.exam_start and day < exam.exam_start:
        raise ApiError(f"Slot date must be on/after the exam period start ({exam.exam_start})", 422,
                       {"date": "Too early"})
    if exam.exam_end and day > exam.exam_end:
        raise ApiError(f"Slot date must be on/before the exam period end ({exam.exam_end})", 422,
                       {"date": "Too late"})


def cancel_booking(booking, by, reason=None, notify_student=True):
    if booking.status != "booked":
        raise ApiError(f"Only active bookings can be cancelled (current: {booking.status})", 409)
    booking.status = "cancelled"
    booking.cancelled_at = datetime.now()
    booking.cancelled_by = by
    booking.cancel_reason = reason
    db.session.flush()
    booking.slot.refresh_seats()
    if notify_student and by != "student":
        notify(booking.student_id, "Booking cancelled",
               f"Your booking for {booking.exam.name} on {booking.slot.date} was cancelled by {by}."
               + (f" Reason: {reason}" if reason else ""), "warning", "/student/bookings")


def compute_total(exam, scores):
    """Weighted total: Σ(marks/criterion_max × weightage%) × exam max marks."""
    total = 0.0
    for rubric, marks in scores:
        if rubric.max_marks:
            total += (marks / rubric.max_marks) * (rubric.weightage / 100.0) * exam.max_marks
    return round(total, 2)
