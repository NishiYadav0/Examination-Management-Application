"""Celery configuration (Redis as broker + result backend) and Beat schedule."""
import os
from celery.schedules import crontab

broker_url = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")
result_backend = os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/1")

timezone = "Asia/Kolkata"
enable_utc = False
broker_connection_retry_on_startup = True

task_serializer = "json"
result_serializer = "json"
accept_content = ["json"]

# Chosen times (change here or with env vars)
REMINDER_HOUR = int(os.getenv("REMINDER_HOUR", "8"))
REMINDER_MINUTE = int(os.getenv("REMINDER_MINUTE", "0"))
REPORT_HOUR = int(os.getenv("REPORT_HOUR", "9"))

beat_schedule = {
    "daily-exam-reminder": {
        "task": "tasks.daily_exam_reminder",
        "schedule": crontab(hour=REMINDER_HOUR, minute=REMINDER_MINUTE),
    },
    "monthly-exam-report": {
        "task": "tasks.monthly_exam_report",
        "schedule": crontab(day_of_month="1", hour=REPORT_HOUR, minute=0),
    },
}

# Quick demo mode: run reminder every 2 minutes & report every 5 minutes
if os.getenv("CELERY_DEMO_SCHEDULE", "0") == "1":
    beat_schedule["daily-exam-reminder"]["schedule"] = crontab(minute="*/2")
    beat_schedule["monthly-exam-report"]["schedule"] = crontab(minute="*/5")
