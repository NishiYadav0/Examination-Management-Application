"""Celery tasks: scheduled jobs (daily reminder, monthly report), user triggered
CSV export, and async e-mail notifications.

Names are explicit (``tasks.<name>``) so celery_config.beat_schedule can refer
to them.
"""
import csv
import json
import os
from collections import Counter
from datetime import date, datetime, timedelta

from celery import shared_task
from flask import current_app, render_template

from models import (db, User, Role, Examination, Slot, Booking, Evaluation, ExportJob,
                    MonthlyReport, SupportTicket, Notification, grade_for)
from utils.mailer import send_mail, send_template


def _admin():
    return User.query.join(User.roles).filter(Role.name == "admin").first()


# =====================================================================
# a) Scheduled job – Daily examination reminder (e-mail via MailHog)
# =====================================================================
@shared_task(name="tasks.daily_exam_reminder")
def daily_exam_reminder():
    today = date.today()
    horizon = today + timedelta(days=2)
    # 1. students with an examination today / tomorrow / day after
    bookings = (Booking.query.join(Slot)
                .filter(Booking.status == "booked", Slot.date >= today, Slot.date <= horizon,
                        Slot.status != "cancelled").all())
    per_student = {}
    for b in bookings:
        per_student.setdefault(b.student, []).append(b)
    sent = 0
    for student, items in per_student.items():
        if not student.active:
            continue
        items.sort(key=lambda b: (b.slot.date, b.slot.start_time))
        rows = [{
            "exam": b.exam.name, "course": f"{b.exam.course.code} – {b.exam.course.name}",
            "type": b.exam.exam_type, "date": b.slot.date.strftime("%a, %d %b %Y"),
            "time": f"{b.slot.start_time.strftime('%H:%M')} – {b.slot.end_time.strftime('%H:%M')}",
            "examiner": b.slot.examiner.name if b.slot.examiner else "TBA",
            "mode": b.slot.mode, "meeting_link": b.slot.meeting_link, "venue": b.slot.venue,
            "instructions": b.exam.instructions or "Join 5 minutes early with your ID card.",
            "is_today": b.slot.date == today,
        } for b in items]
        if send_template(student.email, "⏰ Examination reminder – EMP", "reminder.html",
                         name=student.name, rows=rows, kind="upcoming"):
            sent += 1
        db.session.add(Notification(user_id=student.id, title="Upcoming examination reminder",
                                    message=f"{rows[0]['exam']} on {rows[0]['date']} at {rows[0]['time']}",
                                    type="warning", link="/student/bookings"))
    # 2. students who have not yet booked an open exam that closes soon
    open_exams = Examination.query.filter(Examination.status == "booking_open",
                                          Examination.booking_end >= today).all()
    students = User.query.join(User.roles).filter(Role.name == "student", User.active.is_(True)).all()
    nudges = 0
    for s in students:
        pending = []
        for e in open_exams:
            if not Booking.query.filter(Booking.student_id == s.id, Booking.exam_id == e.id,
                                        Booking.status != "cancelled").first():
                pending.append({"exam": e.name, "course": e.course.code, "type": e.exam_type,
                                "deadline": e.booking_end.strftime("%d %b %Y"),
                                "days_left": (e.booking_end - today).days})
        if pending:
            send_template(s.email, "📅 Book your examination slot – EMP", "reminder.html",
                          name=s.name, rows=[], pending=pending, kind="booking")
            nudges += 1
    db.session.commit()
    result = {"upcoming_reminders": sent, "booking_nudges": nudges, "run_at": datetime.now().isoformat()}
    current_app.logger.info(f"Daily reminder: {result}")
    return result


# =====================================================================
# b) Scheduled job – Monthly examination report (HTML e-mail to admin)
# =====================================================================
def _month_bounds(month_str=None):
    if month_str:
        y, m = map(int, month_str.split("-"))
    else:  # previous month (job runs on the 1st)
        first_this = date.today().replace(day=1)
        prev = first_this - timedelta(days=1)
        y, m = prev.year, prev.month
    start = date(y, m, 1)
    end = date(y + (m == 12), (m % 12) + 1, 1)
    return start, end, f"{y:04d}-{m:02d}"


@shared_task(name="tasks.monthly_exam_report")
def monthly_exam_report(month=None):
    start, end, label = _month_bounds(month)
    s_dt, e_dt = datetime.combine(start, datetime.min.time()), datetime.combine(end, datetime.min.time())
    slots = Slot.query.filter(Slot.date >= start, Slot.date < end, Slot.status != "cancelled").all()
    exam_ids = {s.exam_id for s in slots}
    bookings = Booking.query.join(Slot).filter(Slot.date >= start, Slot.date < end).all()
    evals = Evaluation.query.filter(Evaluation.status == "submitted", Evaluation.evaluated_at >= s_dt,
                                    Evaluation.evaluated_at < e_dt).all()
    pending = [b for b in bookings if b.status == "booked" and b.slot.date <= date.today()
               and not (b.evaluation and b.evaluation.status == "submitted")]
    examiner_counter = Counter(e.examiner.name for e in evals if e.examiner)
    exam_rows = []
    for eid in exam_ids:
        ex = db.session.get(Examination, eid)
        ex_b = [b for b in bookings if b.exam_id == eid]
        ex_e = [b.evaluation for b in ex_b if b.evaluation and b.evaluation.status == "submitted"]
        avg = round(sum(e.total_marks for e in ex_e) / len(ex_e), 1) if ex_e else None
        exam_rows.append({"name": ex.name, "course": ex.course.code, "type": ex.exam_type,
                          "bookings": len([b for b in ex_b if b.status != "cancelled"]),
                          "evaluated": len(ex_e), "avg": avg, "max": ex.max_marks,
                          "status": ex.status})
    grades = Counter(grade_for(e.total_marks / e.exam.max_marks * 100) for e in evals if e.exam.max_marks)
    new_students = (User.query.join(User.roles).filter(Role.name == "student", User.created_at >= s_dt,
                                                        User.created_at < e_dt).count())
    stats = {
        "exams_conducted": len(exam_ids),
        "students_evaluated": len({e.student_id for e in evals}),
        "evaluations": len(evals),
        "completed_bookings": len([b for b in bookings if b.status == "completed"]),
        "total_bookings": len(bookings),
        "cancelled_bookings": len([b for b in bookings if b.status == "cancelled"]),
        "absent": len([b for b in bookings if b.status == "absent"]),
        "pending_evaluations": len(pending),
        "slots": len(slots),
        "new_students": new_students,
        "avg_pct": round(sum(e.total_marks / e.exam.max_marks * 100 for e in evals) / len(evals), 1)
        if evals else 0,
        "active_examiners": [{"name": n, "count": c} for n, c in examiner_counter.most_common(5)],
        "grades": {g: grades.get(g, 0) for g in ["S", "A", "B", "C", "D", "E", "U"]},
    }
    month_name = start.strftime("%B %Y")
    html = render_template("emails/monthly_report.html", subject=f"Monthly Examination Report – {month_name}",
                           month=month_name, stats=stats, exams=exam_rows,
                           generated=datetime.now().strftime("%d %b %Y, %H:%M"),
                           frontend_url=current_app.config["FRONTEND_URL"])
    filename = f"monthly_report_{label}_{datetime.now().strftime('%Y%m%d%H%M%S')}.html"
    with open(os.path.join(current_app.config["REPORT_DIR"], filename), "w", encoding="utf-8") as fh:
        fh.write(html)
    admin = _admin()
    emailed = send_mail(admin.email, f"📊 Monthly Examination Report – {month_name}", html=html) if admin else False
    report = MonthlyReport(month=label, filename=filename, stats_json=json.dumps(stats), emailed=emailed)
    db.session.add(report)
    if admin:
        db.session.add(Notification(user_id=admin.id, title="Monthly report ready",
                                    message=f"Examination report for {month_name} generated.",
                                    type="success", link="/admin/reports"))
    db.session.commit()
    return {"month": label, "file": filename, "emailed": emailed}


# =====================================================================
# c) User triggered async job – "Export my data" as CSV (every role)
#    Student "examination history" is kind = exam_history.
# =====================================================================
@shared_task(name="tasks.generate_user_export")
def generate_user_export(job_id):
    from utils.exports import build_sections, kind_label
    job = db.session.get(ExportJob, job_id)
    if not job:
        return None
    user = db.session.get(User, job.user_id)
    try:
        tag = (user.student_profile.roll_no if user.student_profile else
               user.examiner_profile.employee_id if user.examiner_profile else user.role) or user.id
        filename = f"emp_{job.kind}_{tag}_{datetime.now().strftime('%Y%m%d%H%M%S')}.csv"
        path = os.path.join(current_app.config["EXPORT_DIR"], filename)
        sections = build_sections(user, job.kind)
        total = 0
        # utf-8-sig so Excel shows ₹/– characters correctly
        with open(path, "w", newline="", encoding="utf-8-sig") as fh:
            w = csv.writer(fh)
            multi = len(sections) > 1
            if multi:
                w.writerow([f"EMP – complete data export for {user.name} ({user.email})"])
                w.writerow([f"Generated on {datetime.now().strftime('%d %b %Y %H:%M')}"])
                w.writerow([])
            for title, headers, rows in sections:
                if multi:
                    w.writerow([f"### {title} ({len(rows)} rows)"])
                w.writerow(headers)
                w.writerows(rows)
                total += len(rows)
                if multi:
                    w.writerow([])
        label = kind_label(job.kind)
        job.status, job.filename, job.row_count = "done", filename, total
        job.completed_at = datetime.now()
        db.session.add(Notification(user_id=user.id, title="CSV export ready 📄",
                                    message=f"{label}: {total} row(s) exported. Download it from Export my data.",
                                    type="success", link="/export"))
        db.session.commit()
        send_mail(user.email, f"EMP – your export is ready: {label}",
                  html=render_template("emails/generic.html", subject="Export ready", name=user.name,
                                       heading="Your CSV export is ready",
                                       lines=[f"<b>Export:</b> {label}", f"<b>Rows:</b> {total}",
                                              "The CSV file is attached. You can also download it again from "
                                              "<b>Export my data</b> in the portal."],
                                       button_text="Open Export my data", button_link="/export",
                                       frontend_url=current_app.config["FRONTEND_URL"]),
                  attachments=[path])
        return {"file": filename, "rows": total, "kind": job.kind}
    except Exception as exc:
        db.session.rollback()
        job = db.session.get(ExportJob, job_id)
        job.status, job.error = "failed", str(exc)[:300]
        db.session.add(Notification(user_id=job.user_id, title="CSV export failed",
                                    message="Please try again later.", type="danger", link="/export"))
        db.session.commit()
        raise


# =====================================================================
# Async e-mail notifications
# =====================================================================
@shared_task(name="tasks.send_booking_email")
def send_booking_email(booking_id, kind):
    b = db.session.get(Booking, booking_id)
    if not b:
        return False
    s = b.slot
    lines = [f"<b>Examination:</b> {b.exam.name} ({b.exam.exam_type})",
             f"<b>Course:</b> {b.exam.course.code} – {b.exam.course.name}",
             f"<b>Date & time:</b> {s.date.strftime('%a, %d %b %Y')}, "
             f"{s.start_time.strftime('%H:%M')}–{s.end_time.strftime('%H:%M')}",
             f"<b>Examiner:</b> {s.examiner.name if s.examiner else 'TBA'}"]
    if s.meeting_link:
        lines.append(f"<b>Meeting link:</b> <a href='{s.meeting_link}'>{s.meeting_link}</a>")
    if s.venue:
        lines.append(f"<b>Venue:</b> {s.venue}")
    if kind == "booked":
        heading, subject = "Your slot is confirmed ✅", f"Booking confirmed – {b.exam.name}"
        if b.exam.instructions:
            lines.append(f"<b>Instructions:</b> {b.exam.instructions}")
    else:
        heading, subject = "Your booking was cancelled", f"Booking cancelled – {b.exam.name}"
    return send_template(b.student.email, subject, "generic.html", name=b.student.name, heading=heading,
                         lines=lines, button_text="View my bookings", button_link="/student/bookings")


@shared_task(name="tasks.send_result_emails")
def send_result_emails(exam_id):
    exam = db.session.get(Examination, exam_id)
    count = 0
    for b in Booking.query.filter(Booking.exam_id == exam_id, Booking.status == "completed").all():
        ev = b.evaluation
        if not ev or ev.status != "submitted" or ev.result_notified:
            continue  # students already informed (instant release) are not mailed twice
        _mail_result(b)
        ev.result_notified = True
        count += 1
    db.session.commit()
    return count


def _mail_result(b, updated=False):
    ev, exam = b.evaluation, b.exam
    pct = round(ev.total_marks / exam.max_marks * 100, 1)
    lines = [f"<b>Examination:</b> {exam.name} ({exam.course.code})",
             f"<b>Examiner:</b> {ev.examiner.name if ev.examiner else '-'}",
             f"<b>Marks:</b> {ev.total_marks} / {exam.max_marks} ({pct}%) – Grade {grade_for(pct)} – "
             f"{'PASS' if ev.total_marks >= (exam.pass_marks or 0) else 'FAIL'}"]
    for sc in ev.scores:
        if sc.rubric:
            lines.append(f"&nbsp;&nbsp;• {sc.rubric.criterion}: {sc.marks} / {sc.rubric.max_marks}")
    lines.append(f"<b>Examiner remarks:</b> {ev.remarks or '-'}")
    heading = "Your result was updated ✏️" if updated else "Your result is out 🎉"
    return send_template(b.student.email, f"{'Updated result' if updated else 'Result'} – {exam.name}",
                         "generic.html", name=b.student.name, heading=heading, lines=lines,
                         button_text="View scorecard", button_link=f"/student/results/{b.id}")


@shared_task(name="tasks.send_evaluation_email")
def send_evaluation_email(booking_id, updated=False):
    """Examiner submitted an evaluation -> tell the student by e-mail.
    Instant-release exams include the marks; otherwise the student is told the
    result will be visible once the admin publishes it."""
    b = db.session.get(Booking, booking_id)
    if not b or not b.evaluation or b.evaluation.status != "submitted":
        return False
    if b.exam.results_visible:
        ok = _mail_result(b, updated=updated or b.evaluation.result_notified)
        b.evaluation.result_notified = True
        db.session.commit()
        return ok
    return send_template(b.student.email, f"Evaluation completed – {b.exam.name}", "generic.html",
                         name=b.student.name, heading="Your examination has been evaluated ✅",
                         lines=[f"<b>Examination:</b> {b.exam.name} ({b.exam.course.code})",
                                f"<b>Examiner:</b> {b.evaluation.examiner.name if b.evaluation.examiner else '-'}",
                                "Your marks and feedback will be visible as soon as the admin publishes the results. "
                                "You will receive another e-mail then."],
                         button_text="View my bookings", button_link="/student/bookings")


@shared_task(name="tasks.send_user_email")
def send_user_email(user_id, subject, heading, lines, button_text=None, button_link=None):
    """Generic notification e-mail to one user."""
    u = db.session.get(User, user_id)
    if not u:
        return False
    return send_template(u.email, subject, "generic.html", name=u.name, heading=heading, lines=lines,
                         button_text=button_text, button_link=button_link)


@shared_task(name="tasks.send_assignment_emails")
def send_assignment_emails(exam_id, added_ids, removed_ids):
    """Admin assigned / removed examiners -> e-mail each of them."""
    exam = db.session.get(Examination, exam_id)
    if not exam:
        return 0
    sent = 0
    for uid in added_ids or []:
        u = db.session.get(User, uid)
        if not u:
            continue
        lines = [f"<b>Examination:</b> {exam.name}", f"<b>Course:</b> {exam.course.code} – {exam.course.name}",
                 f"<b>Type:</b> {exam.exam_type} · {exam.duration_minutes} min · {exam.max_marks} marks",
                 f"<b>Slot creation period:</b> {exam.slot_creation_start:%d %b %Y} – {exam.slot_creation_end:%d %b %Y}",
                 f"<b>Examination period:</b> {exam.exam_start:%d %b %Y} – {exam.exam_end:%d %b %Y}",
                 "Please publish your available slots once the admin opens slot creation."]
        if exam.rubrics:
            lines.append("<b>Rubric:</b> " + ", ".join(f"{r.criterion} ({r.weightage}%)" for r in exam.rubrics))
        if send_template(u.email, f"You have been assigned: {exam.name}", "generic.html", name=u.name,
                         heading="New examination assigned to you 📋", lines=lines,
                         button_text="Open examination", button_link=f"/examiner/exams/{exam.id}"):
            sent += 1
    for uid in removed_ids or []:
        u = db.session.get(User, uid)
        if u:
            send_template(u.email, f"Removed from examination: {exam.name}", "generic.html", name=u.name,
                          heading="Examination assignment removed",
                          lines=[f"The admin removed you from <b>{exam.name}</b> ({exam.course.code}).",
                                 "No action is needed from your side."],
                          button_text="My examinations", button_link="/examiner/exams")
    return sent


@shared_task(name="tasks.send_examiner_credentials")
def send_examiner_credentials(user_id, password):
    u = db.session.get(User, user_id)
    return send_template(u.email, "Your EMP examiner account", "generic.html", name=u.name,
                         heading="Welcome to the Examination Management Portal",
                         lines=["The administrator has created an examiner account for you.",
                                f"<b>Login e-mail:</b> {u.email}", f"<b>Temporary password:</b> {password}",
                                "Please change your password after the first login (Profile › Security)."],
                         button_text="Log in", button_link="/login")


@shared_task(name="tasks.send_password_reset")
def send_password_reset(user_id, password):
    u = db.session.get(User, user_id)
    return send_template(u.email, "Your EMP password was reset", "generic.html", name=u.name,
                         heading="Password reset by administrator",
                         lines=[f"<b>New password:</b> {password}", "Please change it after logging in."],
                         button_text="Log in", button_link="/login")


@shared_task(name="tasks.send_ticket_reply")
def send_ticket_reply(ticket_id):
    t = db.session.get(SupportTicket, ticket_id)
    return send_template(t.email, f"Re: {t.subject}", "generic.html", name=t.name,
                         heading="Reply from EMP support",
                         lines=[f"<i>Your message:</i> {t.message}", f"<b>Reply:</b> {t.admin_reply}"],
                         button_text="Contact us again", button_link="/contact")


@shared_task(name="tasks.notify_booking_open")
def notify_booking_open(exam_id):
    exam = db.session.get(Examination, exam_id)
    students = User.query.join(User.roles).filter(Role.name == "student", User.active.is_(True)).all()
    for s in students:
        db.session.add(Notification(user_id=s.id, title="Booking open 📢",
                                    message=f"Slots for {exam.name} ({exam.course.code}) are open until "
                                            f"{exam.booking_end}.", type="info",
                                    link=f"/student/exams/{exam.id}"))
    db.session.commit()
    return len(students)
