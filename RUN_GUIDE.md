# 🚀 EMP V2 – Complete Run Guide (Windows + WSL Ubuntu)

This guide takes you from a fresh machine to a fully working Examination Management Portal.
Everything runs **inside WSL Ubuntu** (Redis & Celery need Linux). You open the site in your normal Windows browser.

> In the commands below the project lives at
> `D:\Download\Examination Management Application PROJECT\project_2xfXXXXXX`
> which inside WSL is
> `/mnt/d/Download/Examination Management Application PROJECT/project_2xfXXXXXX`
> (quotes are needed because the path has spaces).

---

## 0. What runs where – you need **6 terminals**

| # | Terminal | Command (short) | Port / URL |
|---|----------|-----------------|------------|
| 1 | Redis server | `redis-server` | 6379 |
| 2 | MailHog (fake e-mail inbox) | `~/MailHog` | SMTP 1025 · Inbox **http://localhost:8025** |
| 3 | Flask API | `python app.py` | **http://localhost:5000** |
| 4 | Celery worker (runs jobs) | `celery -A app.celery worker -l info` | – |
| 5 | Celery beat (scheduler) | `celery -A app.celery beat -l info` | – |
| 6 | Vue frontend | `npm run serve` | **http://localhost:8080** ← open this |

Tip: in *Windows Terminal* press **Ctrl+Shift+T** to open a new WSL tab for each one.

---

## 1. One-time setup

### 1.1 Install WSL (skip if you already have Ubuntu)
Open **PowerShell as Administrator**:
```powershell
wsl --install -d Ubuntu
```
Restart, open **Ubuntu** from the Start menu and create your Linux user.

### 1.2 Install system packages (inside Ubuntu)
```bash
sudo apt update
sudo apt install -y python3 python3-venv python3-pip redis-server curl wget
```

### 1.3 Install Node.js 20 LTS (for the Vue CLI)
```bash
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt install -y nodejs
node -v   # v20.x
npm -v
```

### 1.4 Install MailHog (local e-mail catcher – nothing is really sent)
```bash
cd ~
wget https://github.com/mailhog/MailHog/releases/download/v1.0.1/MailHog_linux_amd64 -O MailHog
chmod +x MailHog
```

### 1.5 Backend – Python virtual environment
```bash
cd "/mnt/d/Download/Examination Management Application PROJECT/project_2xfXXXXXX/backend"
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```
> ⚡ Faster alternative: create the venv in your Linux home (WSL is slow on `/mnt/d`):
> `python3 -m venv ~/emp-venv && source ~/emp-venv/bin/activate` – then use that path everywhere below.

### 1.6 Frontend – node modules
```bash
cd "/mnt/d/Download/Examination Management Application PROJECT/project_2xfXXXXXX/frontend"
npm install
```

---

## 2. Every time you run the project

Set a shortcut first (paste in each new terminal, or add it to `~/.bashrc`):
```bash
export EMP="/mnt/d/Download/Examination Management Application PROJECT/project_2xfXXXXXX"
```

### Terminal 1 – Redis
```bash
redis-server
```
(If it says *address already in use*, Redis is already running as a service – that's fine. Check with `redis-cli ping` → `PONG`.)

### Terminal 2 – MailHog
```bash
~/MailHog
```
Open **http://localhost:8025** in your browser to see every e-mail the app sends.

### Terminal 3 – Flask API
```bash
cd "$EMP/backend"
source .venv/bin/activate
python app.py
```
On the **first run** the SQLite database (`backend/instance/emp.sqlite3`) is created **programmatically**,
the single admin is created and demo data is seeded. You should see `Running on http://127.0.0.1:5000`.

### Terminal 4 – Celery worker
```bash
cd "$EMP/backend"
source .venv/bin/activate
celery -A app.celery worker --loglevel=info
```

### Terminal 5 – Celery beat (scheduled jobs)
```bash
cd "$EMP/backend"
source .venv/bin/activate
celery -A app.celery beat --loglevel=info
```
Default schedule (IST): daily reminder **08:00**, monthly report **1st of month 09:00**.
For a live demo run beat with fast timings instead:
```bash
CELERY_DEMO_SCHEDULE=1 celery -A app.celery beat --loglevel=info   # reminder every 2 min, report every 5 min
```
Or choose your own reminder time: `REMINDER_HOUR=18 REMINDER_MINUTE=30 celery -A app.celery beat -l info`.

### Terminal 6 – Vue frontend
```bash
cd "$EMP/frontend"
npm run serve
```
Open **http://localhost:8080** 🎉  (all `/api` calls are proxied to Flask on port 5000).

---

## 3. Demo accounts

| Role | E-mail | Password |
|------|--------|----------|
| Admin (only one, created by code) | `admin@emp.com` | `admin123` |
| Examiner | `examiner1@emp.com` … `examiner4@emp.com` | `examiner123` |
| Student | `student1@emp.com` … `student10@emp.com` | `student123` |

The login page also has **Quick demo login** buttons.

Demo data is generated relative to *today*, so you always get one exam in each state:

| Examination | State | What to demo |
|---|---|---|
| ML Foundations – End Term Assessment | Completed + results published | student results, scorecard |
| Python OPPE Practical | Closed, some evaluations pending, release = *After publish* | evaluation → "evaluated" mail; admin *Publish results* → result mail |
| MAD-II Project Viva | **Booking open**, result release = *Instant* | student booking / cancel, examiner evaluation → student gets marks + e-mail immediately |
| DBMS SQL Practical | **Slot creation open** | examiner creates slots (examiner1 / examiner2) |
| Software Engineering Project Demo | Draft | admin rubric, open slot creation |

---

## 4. Suggested demo walkthrough (viva)

1. **Home page** → features, how-it-works tabs, live stats, contact page (send a message as guest).
2. **Register** a new student → dashboard.
3. Student: **Browse exams** → *MAD-II Project Viva* → pick a slot → confirm (submission link required).
   Try booking again → *one slot per exam* error. Cancel from **My bookings**.
4. Student: **Export history** → Celery job → CSV downloads + notification + mail in MailHog.
5. Examiner (`examiner1`): **Assigned exams** → *DBMS SQL Practical* → **Create slot** (try *auto-split*).
   Try creating a slot in *MAD-II* → blocked (booking already open).
6. Examiner: **Booked students** → *Evaluate* → rubric sliders → live weighted total → submit.
7. Admin: **Examinations** → *Python OPPE Practical* → **Publish results** → student receives mail.
8. Admin: **Bookings** → reschedule a booking to another examiner's slot; **Examiner slots** → change examiner / cancel.
9. Admin: **Students** → block a student → try logging in as them (blocked message) → unblock.
10. Admin: **Reports & Jobs** → *Run now* (daily reminder) and *Generate* (monthly report) → open MailHog.
11. Admin: open *Software Engineering Project Demo* → **Examiners** tab → tick an examiner → Save → the examiner gets an e-mail (MailHog) + notification.
12. Any role: sidebar **Export My Data** → *Export everything* or a single CSV (activity log, statistics, …) → file downloads, notification + e-mail with attachment.
13. Toggle **dark mode**, resize to mobile, click **Install app** (PWA).

Show caching: `curl -i http://localhost:5000/api/public/stats` twice → header `X-Cache: MISS` then `X-Cache: HIT`.
Inspect Redis: `redis-cli -n 2 keys 'emp:*'`.

---

## 5. Reset / useful commands

```bash
# fresh database with demo data (stop Flask first)
rm "$EMP/backend/instance/emp.sqlite3"

# start with an EMPTY database (only the admin)
SEED_DEMO_DATA=0 python app.py

# clear Redis cache + queues
redis-cli flushall

# production build of the frontend
cd "$EMP/frontend" && npm run build
```

Environment variables you can set (all optional): `ADMIN_EMAIL`, `ADMIN_PASSWORD`, `MAIL_SERVER`, `MAIL_PORT`,
`CACHE_REDIS_URL`, `CELERY_BROKER_URL`, `APP_TIMEZONE` (default `Asia/Kolkata`), `REMINDER_HOUR`, `REPORT_HOUR`.

---

## 6. Troubleshooting

| Problem | Fix |
|---|---|
| `Cannot reach the server` toast in the UI | Flask (terminal 3) is not running. |
| Export spinner never finishes / *worker unavailable* | Start Redis (1) and the Celery worker (4). |
| No e-mails in MailHog | Start MailHog (2) **before** triggering jobs; check the worker log. |
| `Address already in use` on 5000/8080 | `sudo lsof -i :5000` then `kill <PID>` (or close the old terminal). |
| `redis.exceptions.ConnectionError` | `sudo service redis-server start` or run `redis-server`. |
| Hot reload not working on `/mnt/d` | Already handled by polling in `vue.config.js`; or move the project into `~/`. |
| `npm install` very slow | Move the project to `~/projects/` inside WSL (much faster file system). |
| Wrong dates/times | The backend uses IST (`APP_TIMEZONE`). Make sure your Windows clock is correct. |
| Slot creation / booking button disabled | Today must be inside the configured window **and** the admin must have opened it (see exam page warnings). |

---

## 7. Submission zip

```bash
cd "/mnt/d/Download/Examination Management Application PROJECT"
# rename to your roll number first, e.g. project_22f1000123
zip -r project_22f1000123.zip project_22f1000123 \
  -x "*/node_modules/*" "*/.venv/*" "*/__pycache__/*" "*/instance/*" "*/exports/*" "*/reports/*" "*/dist/*" "*/celerybeat-schedule*"
```
