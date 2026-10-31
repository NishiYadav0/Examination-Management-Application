"""Programmatic database creation + single admin + (optional) realistic demo data.

Everything is relative to *today* so the demo always shows exams in every
lifecycle state (Draft, Slot Creation, Booking Open, Closed, Completed).
"""
import random
from datetime import date, datetime, time, timedelta

from flask_security.utils import hash_password

from models import (db, Role, User, StudentProfile, ExaminerProfile, Course, Examination, Rubric,
                    Slot, Booking, Evaluation, EvaluationScore, SupportTicket, Notification, ActivityLog)
from utils.rules import compute_total

ROLES = [("admin", "Portal administrator"), ("examiner", "Faculty examiner"), ("student", "Registered student")]


# Columns added after the first release. db.create_all() never alters existing
# tables, so older databases get these columns added programmatically here.
NEW_COLUMNS = {
    "examination": {"auto_publish": "BOOLEAN DEFAULT 0"},
    "evaluation": {"result_notified": "BOOLEAN DEFAULT 0"},
    "export_job": {"kind": "VARCHAR(30) DEFAULT 'exam_history'"},
}


def upgrade_schema():
    from sqlalchemy import inspect, text
    insp = inspect(db.engine)
    tables = insp.get_table_names()
    with db.engine.begin() as conn:
        for table, cols in NEW_COLUMNS.items():
            if table not in tables:
                continue
            existing = {c["name"] for c in insp.get_columns(table)}
            for name, ddl in cols.items():
                if name not in existing:
                    conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {name} {ddl}"))


def init_database(app):
    db.create_all()
    upgrade_schema()
    ds = app.security.datastore
    for name, desc in ROLES:
        ds.find_or_create_role(name=name, description=desc)
    db.session.commit()

    # ---- exactly one admin, created programmatically ----
    admin_role = Role.query.filter_by(name="admin").first()
    if not User.query.join(User.roles).filter(Role.id == admin_role.id).first():
        ds.create_user(email=app.config["ADMIN_EMAIL"], name=app.config["ADMIN_NAME"],
                       password=hash_password(app.config["ADMIN_PASSWORD"]), phone="9876543210",
                       roles=["admin"])
        db.session.commit()
        app.logger.info("Admin user created: %s", app.config["ADMIN_EMAIL"])

    if app.config.get("SEED_DEMO_DATA") and Course.query.count() == 0:
        seed_demo(ds)


def _t(h, m=0):
    return time(h, m)


def seed_demo(ds):
    random.seed(7)
    today = date.today()
    d = lambda n: today + timedelta(days=n)  # noqa: E731

    # ---------------- examiners ----------------
    ex_data = [
        ("Dr. Ananya Rao", "CSE", "Associate Professor", "Web Development & Cloud"),
        ("Prof. Rakesh Menon", "CSE", "Professor", "Databases & Systems"),
        ("Dr. Kavya Iyer", "Data Science", "Assistant Professor", "Machine Learning"),
        ("Mr. Arjun Nair", "CSE", "Teaching Fellow", "Python & Software Engineering"),
    ]
    examiners = []
    for i, (name, dept, desig, spec) in enumerate(ex_data, 1):
        u = ds.create_user(email=f"examiner{i}@emp.com", name=name, password=hash_password("examiner123"),
                           phone=f"98450000{i:02d}", roles=["examiner"])
        db.session.flush()
        db.session.add(ExaminerProfile(user_id=u.id, employee_id=f"EXM{1000 + i}", department=dept,
                                       designation=desig, specialization=spec, office=f"Block A, Room {100 + i}"))
        examiners.append(u)

    # ---------------- students ----------------
    st_names = ["Aarav Sharma", "Diya Patel", "Rohan Gupta", "Sneha Reddy", "Vikram Singh",
                "Ishita Verma", "Kabir Khan", "Meera Joshi", "Aditya Kumar", "Pooja Nair"]
    students = []
    for i, name in enumerate(st_names, 1):
        u = ds.create_user(email=f"student{i}@emp.com", name=name, password=hash_password("student123"),
                           phone=f"90000000{i:02d}", roles=["student"])
        u.created_at = datetime.now() - timedelta(days=random.randint(5, 150))
        db.session.flush()
        db.session.add(StudentProfile(user_id=u.id, roll_no=f"23F{1000000 + i}",
                                      program="BS in Data Science & Applications",
                                      department="Data Science", year=random.choice([2, 3]),
                                      gender=random.choice(["Male", "Female"]),
                                      address="Chennai, Tamil Nadu"))
        students.append(u)

    # ---------------- courses ----------------
    courses = {}
    for code, name, dept, level, desc in [
        ("BSCS2006", "Modern Application Development II", "CSE", "Diploma",
         "Build full-stack apps with Flask APIs, VueJS, Redis caching and Celery jobs."),
        ("BSCS2001", "Database Management Systems", "CSE", "Diploma",
         "Relational model, SQL, normalisation, indexing and transactions."),
        ("BSCS3001", "Machine Learning Foundations", "Data Science", "Degree",
         "Linear algebra, probability and optimisation for machine learning."),
        ("BSCS1002", "Programming in Python", "CSE", "Foundation",
         "Problem solving with Python – data types, functions, files and OOP."),
        ("BSCS3002", "Software Engineering", "CSE", "Degree",
         "Requirements, design, testing, agile process and project management."),
    ]:
        c = Course(code=code, name=name, department=dept, level=level, description=desc, credits=4)
        db.session.add(c)
        courses[code] = c
    db.session.flush()

    rubric_sets = {
        "Viva": [("Concept clarity", 30, 30), ("Code walkthrough", 40, 40), ("Q&A", 30, 30)],
        "Practical": [("Correctness", 50, 50), ("Code quality", 20, 20), ("Viva questions", 30, 30)],
        "Assessment": [("Theory", 40, 40), ("Problem solving", 60, 60)],
        "Project Demo": [("Architecture", 25, 25), ("Live demo", 40, 40), ("Documentation", 15, 15),
                         ("Q&A", 20, 20)],
    }

    def exam(course, name, etype, status, sc, bk, ep, exs, max_marks=100, instr=None, sub=False):
        e = Examination(course_id=courses[course].id, name=name, exam_type=etype, status=status,
                        description=f"{etype} for {courses[course].name}.",
                        instructions=instr or "Join 5 minutes early, keep your ID card ready and "
                                              "share your screen when asked.",
                        duration_minutes=20 if etype == "Viva" else 30, max_marks=max_marks,
                        pass_marks=round(max_marks * 0.4), requires_submission=sub,
                        slot_creation_start=d(sc[0]), slot_creation_end=d(sc[1]),
                        booking_start=d(bk[0]), booking_end=d(bk[1]), exam_start=d(ep[0]), exam_end=d(ep[1]))
        e.examiners = exs
        db.session.add(e)
        db.session.flush()
        for i, (crit, mm, w) in enumerate(rubric_sets[etype], 1):
            db.session.add(Rubric(exam_id=e.id, criterion=crit, max_marks=mm, weightage=w, order=i,
                                  description=f"Assess the student's {crit.lower()}."))
        db.session.flush()
        return e

    def slot(e, examiner, day, h, cap=2, status=None, m=0):
        dur = e.duration_minutes
        start = datetime.combine(d(day), _t(h, m))
        s = Slot(exam_id=e.id, examiner_id=examiner.id, date=d(day), start_time=start.time(),
                 end_time=(start + timedelta(minutes=dur)).time(), capacity=cap, available_seats=cap,
                 mode="online", meeting_link="https://meet.google.com/emp-demo-" + str(random.randint(100, 999)))
        db.session.add(s)
        db.session.flush()
        if status:
            s.status = status
        return s

    def book(stu, s, days_ago=3, status="booked"):
        b = Booking(student_id=stu.id, slot_id=s.id, exam_id=s.exam_id, status=status,
                    booked_at=datetime.now() - timedelta(days=days_ago, hours=random.randint(0, 10)),
                    submission_link="https://github.com/student/project" if s.exam.requires_submission else None)
        db.session.add(b)
        db.session.flush()
        s.refresh_seats()
        return b

    def evaluate(b, pct_low=45, pct_high=95, submit=True):
        ex = b.exam
        ev = Evaluation(booking_id=b.id, student_id=b.student_id, examiner_id=b.slot.examiner_id,
                        exam_id=ex.id, status="submitted" if submit else "draft",
                        remarks=random.choice(["Good understanding of concepts, well presented.",
                                               "Solid work; improve error handling and testing.",
                                               "Excellent demo and confident answers.",
                                               "Average performance – revise core fundamentals."]),
                        strengths="Clear explanation", improvements="More test cases",
                        evaluated_at=datetime.combine(b.slot.date, b.slot.end_time))
        db.session.add(ev)
        db.session.flush()
        pairs = []
        for r in ex.rubrics:
            m = round(r.max_marks * random.randint(pct_low, pct_high) / 100, 1)
            pairs.append((r, m))
            db.session.add(EvaluationScore(evaluation_id=ev.id, rubric_id=r.id, marks=m))
        ev.total_marks = compute_total(ex, pairs)
        if submit:
            b.status = "completed"
        return ev

    A, B, C, D = examiners
    S = students

    # 1) Completed + published (past)
    ml = exam("BSCS3001", "ML Foundations – End Term Assessment", "Assessment", "completed",
              (-40, -30), (-29, -22), (-21, -15), [C, B])
    ml_slots = [slot(ml, C, -20, 10), slot(ml, C, -20, 11), slot(ml, B, -18, 14), slot(ml, B, -17, 15)]
    for i, stu in enumerate(S[:7]):
        b = book(stu, ml_slots[i % 4], days_ago=25 - i)
        evaluate(b)
    for s in ml_slots:
        s.status = "completed"
    ml.results_published = True
    for ev in Evaluation.query.filter_by(exam_id=ml.id).all():
        ev.result_notified = True
    ml.published_at = datetime.now() - timedelta(days=10)

    # 2) Closed – evaluations partly done (ready to publish demo)
    py = exam("BSCS1002", "Python OPPE Practical", "Practical", "closed",
              (-20, -12), (-11, -4), (-3, 3), [D, A])
    py_slots = [slot(py, D, -2, 10, cap=3), slot(py, D, -1, 10, cap=3), slot(py, A, -1, 15, cap=2),
                slot(py, A, 2, 11, cap=2)]
    for i, stu in enumerate(S[:8]):
        s = py_slots[i % 4]
        b = book(stu, s, days_ago=8 - (i % 5))
        if s.date < today and i % 3 != 2:
            evaluate(b)

    # 3) Booking open – MAD II viva (main demo exam)
    mad = exam("BSCS2006", "MAD-II Project Viva", "Viva", "booking_open",
               (-10, -3), (-2, 7), (-2, 12), [A, D],
               instr="Keep your project running locally, share the screen and be ready to explain your code.",
               sub=True)
    mad_slots = [slot(mad, A, -1, 10), slot(mad, A, 0, 18), slot(mad, A, 2, 10), slot(mad, A, 2, 11, cap=1),
                 slot(mad, D, 3, 14), slot(mad, D, 4, 15, cap=3), slot(mad, D, 6, 10)]
    book(S[0], mad_slots[0], days_ago=2)
    mad.auto_publish = True  # demo: marks are released as soon as the examiner submits
    evaluate(Booking.query.filter_by(student_id=S[0].id, exam_id=mad.id).first()).result_notified = True
    book(S[1], mad_slots[0], days_ago=2)
    book(S[2], mad_slots[2], days_ago=1)
    book(S[3], mad_slots[3], days_ago=1)       # capacity 1 -> FULL
    book(S[4], mad_slots[4], days_ago=0)
    cb = book(S[5], mad_slots[5], days_ago=1)
    cb.status, cb.cancelled_at, cb.cancelled_by, cb.cancel_reason = "cancelled", datetime.now(), "student", "Clash"
    mad_slots[5].refresh_seats()

    # 4) Slot creation open – DBMS practical
    dbms = exam("BSCS2001", "DBMS SQL Practical", "Practical", "slot_creation",
                (-2, 5), (6, 12), (8, 20), [B, A])
    slot(dbms, B, 9, 10, cap=4)
    slot(dbms, B, 9, 11, cap=4)

    # 5) Draft – SE project demo
    exam("BSCS3002", "Software Engineering Project Demo", "Project Demo", "draft",
         (0, 7), (8, 14), (15, 25), [D, C], sub=True)

    # ---------------- misc ----------------
    db.session.add(SupportTicket(name="Rahul (guest)", email="rahul.guest@example.com",
                                 subject="How do I register as a student?", category="Account",
                                 message="Is registration open for new diploma students?"))
    db.session.add(SupportTicket(user_id=S[2].id, name=S[2].name, email=S[2].email,
                                 subject="Need to change my viva slot", category="Booking",
                                 message="I have a clash on my booked day. Can admin reschedule?"))
    for u in S + examiners:
        db.session.add(Notification(user_id=u.id, title="Welcome to EMP 👋",
                                    message="Explore your dashboard to get started.", type="info"))
        db.session.add(ActivityLog(user_id=u.id, action="register" if u in S else "account_created",
                                   details="Demo account", created_at=u.created_at))
    db.session.commit()
